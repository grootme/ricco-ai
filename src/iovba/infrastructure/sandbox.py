"""
Sandbox Manager - Aislamiento seguro de ejecución

Implementa contenedores Docker/K8s Pods para aislamiento total de procesos
y sistema de archivos. Basado en la arquitectura deer-flow de ByteDance.
"""

import asyncio
import uuid
import json
import os
import subprocess
import tempfile
import shutil
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class IsolationLevel(str, Enum):
    """Niveles de aislamiento del sandbox"""
    NONE = "none"              # Sin aislamiento (solo desarrollo)
    PROCESS = "process"        # Aislamiento a nivel proceso
    CONTAINER = "container"    # Aislamiento con Docker
    KUBERNETES = "kubernetes"  # Aislamiento con K8s Pods


class SandboxStatus(str, Enum):
    """Estado del sandbox"""
    CREATING = "creating"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    TERMINATED = "terminated"


@dataclass
class SandboxConfig:
    """Configuración del sandbox"""
    sandbox_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    isolation_level: IsolationLevel = IsolationLevel.CONTAINER
    timeout_seconds: int = 300
    max_memory_mb: int = 512
    max_cpu_percent: int = 50
    max_file_size_mb: int = 100
    network_enabled: bool = False
    allowed_domains: List[str] = field(default_factory=list)
    allowed_tools: List[str] = field(default_factory=list)
    restricted_tools: List[str] = field(default_factory=list)
    environment_vars: Dict[str, str] = field(default_factory=dict)
    working_directory: Optional[str] = None
    auto_cleanup: bool = True
    persistent_storage: bool = False
    storage_path: Optional[str] = None


@dataclass
class SandboxIsolation:
    """Configuración de aislamiento específica"""
    pid_namespace: bool = True
    network_namespace: bool = True
    mount_namespace: bool = True
    user_namespace: bool = False
    cgroup_limits: bool = True
    seccomp_profile: Optional[str] = None
    apparmor_profile: Optional[str] = None
    read_only_root: bool = True


@dataclass
class SandboxInfo:
    """Información del sandbox en runtime"""
    sandbox_id: str
    status: SandboxStatus
    created_at: datetime
    config: SandboxConfig
    container_id: Optional[str] = None
    pid: Optional[int] = None
    workspace_path: Optional[str] = None
    resource_usage: Dict[str, Any] = field(default_factory=dict)
    execution_count: int = 0
    last_activity: Optional[datetime] = None
    errors: List[str] = field(default_factory=list)


class SandboxManager:
    """
    Gestor de Sandboxes para ejecución aislada.
    
    Proporciona entornos de ejecución seguros con aislamiento de recursos y red,
    permitiendo que los agentes ejecuten comandos de shell y scripts Python
    de forma segura.
    
    Usage:
        manager = SandboxManager()
        
        # Crear sandbox
        sandbox = await manager.create_sandbox(SandboxConfig(
            isolation_level=IsolationLevel.CONTAINER,
            timeout_seconds=600
        ))
        
        # Ejecutar comando
        result = await manager.execute(sandbox.sandbox_id, "ls -la")
        
        # Limpiar
        await manager.terminate_sandbox(sandbox.sandbox_id)
    """
    
    def __init__(
        self,
        default_config: Optional[SandboxConfig] = None,
        max_sandboxes: int = 10,
        docker_image: str = "openclaw/sandbox:latest"
    ):
        """
        Inicializa el gestor de sandboxes.
        
        Args:
            default_config: Configuración por defecto para nuevos sandboxes
            max_sandboxes: Máximo número de sandboxes concurrentes
            docker_image: Imagen Docker base para sandboxes
        """
        self.default_config = default_config or SandboxConfig()
        self.max_sandboxes = max_sandboxes
        self.docker_image = docker_image
        self._sandboxes: Dict[str, SandboxInfo] = {}
        self._lock = asyncio.Lock()
        self._on_sandbox_created: Optional[Callable] = None
        self._on_sandbox_terminated: Optional[Callable] = None
        
        # Verificar Docker disponible
        self._docker_available = self._check_docker()
    
    def _check_docker(self) -> bool:
        """Verifica si Docker está disponible"""
        try:
            result = subprocess.run(
                ["docker", "version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False
    
    async def create_sandbox(
        self,
        config: Optional[SandboxConfig] = None,
        isolation: Optional[SandboxIsolation] = None
    ) -> SandboxInfo:
        """
        Crea un nuevo sandbox aislado.
        
        Args:
            config: Configuración del sandbox (usa default si no se especifica)
            isolation: Configuración de aislamiento específica
        
        Returns:
            SandboxInfo con información del sandbox creado
        """
        async with self._lock:
            if len(self._sandboxes) >= self.max_sandboxes:
                raise RuntimeError(f"Máximo número de sandboxes alcanzado: {self.max_sandboxes}")
            
            sandbox_config = config or self.default_config
            sandbox_id = sandbox_config.sandbox_id
            
            if sandbox_id in self._sandboxes:
                raise ValueError(f"Sandbox {sandbox_id} ya existe")
            
            sandbox_info = SandboxInfo(
                sandbox_id=sandbox_id,
                status=SandboxStatus.CREATING,
                created_at=datetime.utcnow(),
                config=sandbox_config
            )
            
            self._sandboxes[sandbox_id] = sandbox_info
            
            try:
                # Crear según nivel de aislamiento
                if sandbox_config.isolation_level == IsolationLevel.CONTAINER:
                    await self._create_container_sandbox(sandbox_info, isolation)
                elif sandbox_config.isolation_level == IsolationLevel.KUBERNETES:
                    await self._create_k8s_sandbox(sandbox_info, isolation)
                elif sandbox_config.isolation_level == IsolationLevel.PROCESS:
                    await self._create_process_sandbox(sandbox_info, isolation)
                else:
                    await self._create_no_isolation_sandbox(sandbox_info)
                
                sandbox_info.status = SandboxStatus.READY
                sandbox_info.last_activity = datetime.utcnow()
                
                if self._on_sandbox_created:
                    await self._on_sandbox_created(sandbox_info)
                
                logger.info(f"Sandbox {sandbox_id} creado con nivel {sandbox_config.isolation_level}")
                
            except Exception as e:
                sandbox_info.status = SandboxStatus.ERROR
                sandbox_info.errors.append(str(e))
                logger.error(f"Error creando sandbox {sandbox_id}: {e}")
                raise
            
            return sandbox_info
    
    async def _create_container_sandbox(
        self,
        sandbox_info: SandboxInfo,
        isolation: Optional[SandboxIsolation]
    ) -> None:
        """Crea sandbox usando Docker"""
        if not self._docker_available:
            # Fallback a proceso si Docker no está disponible
            logger.warning("Docker no disponible, usando aislamiento de proceso")
            await self._create_process_sandbox(sandbox_info, isolation)
            return
        
        config = sandbox_info.config
        
        # Crear directorio de trabajo
        workspace = tempfile.mkdtemp(prefix=f"sandbox_{sandbox_info.sandbox_id}_")
        sandbox_info.workspace_path = workspace
        
        # Construir comando docker run
        docker_cmd = [
            "docker", "run", "-d",
            "--name", f"openclaw-{sandbox_info.sandbox_id}",
            "--memory", f"{config.max_memory_mb}m",
            "--cpus", f"0.{config.max_cpu_percent // 10}",
            "--network", "none" if not config.network_enabled else "bridge",
            "-v", f"{workspace}:/workspace",
            "-w", "/workspace",
            "-e", "SANDBOX_ID=" + sandbox_info.sandbox_id,
        ]
        
        # Añadir variables de entorno
        for key, value in config.environment_vars.items():
            docker_cmd.extend(["-e", f"{key}={value}"])
        
        # Límites de recursos
        docker_cmd.extend([
            "--pids-limit", "100",
            "--ulimit", f"fsize={config.max_file_size_mb * 1024 * 1024}",
        ])
        
        # Políticas de seguridad
        if isolation:
            if isolation.read_only_root:
                docker_cmd.append("--read-only")
            if isolation.seccomp_profile:
                docker_cmd.extend(["--security-opt", f"seccomp={isolation.seccomp_profile}"])
            if isolation.apparmor_profile:
                docker_cmd.extend(["--security-opt", f"apparmor={isolation.apparmor_profile}"])
        
        docker_cmd.append(self.docker_image)
        docker_cmd.extend(["tail", "-f", "/dev/null"])  # Mantener contenedor corriendo
        
        try:
            result = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                sandbox_info.container_id = result.stdout.strip()
            else:
                raise RuntimeError(f"Error iniciando contenedor: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            raise RuntimeError("Timeout creando contenedor Docker")
    
    async def _create_k8s_sandbox(
        self,
        sandbox_info: SandboxInfo,
        isolation: Optional[SandboxIsolation]
    ) -> None:
        """Crea sandbox usando Kubernetes (placeholder)"""
        # TODO: Implementar con cliente K8s
        logger.warning("K8s sandbox no implementado, usando contenedor")
        await self._create_container_sandbox(sandbox_info, isolation)
    
    async def _create_process_sandbox(
        self,
        sandbox_info: SandboxInfo,
        isolation: Optional[SandboxIsolation]
    ) -> None:
        """Crea sandbox con aislamiento a nivel proceso"""
        workspace = tempfile.mkdtemp(prefix=f"sandbox_{sandbox_info.sandbox_id}_")
        sandbox_info.workspace_path = workspace
        sandbox_info.pid = os.getpid()
    
    async def _create_no_isolation_sandbox(self, sandbox_info: SandboxInfo) -> None:
        """Crea sandbox sin aislamiento (solo para desarrollo)"""
        workspace = tempfile.mkdtemp(prefix=f"sandbox_{sandbox_info.sandbox_id}_")
        sandbox_info.workspace_path = workspace
        logger.warning(f"Sandbox {sandbox_info.sandbox_id} creado SIN aislamiento - solo desarrollo")
    
    async def execute(
        self,
        sandbox_id: str,
        command: str,
        timeout: Optional[int] = None,
        capture_output: bool = True,
        env: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta un comando en el sandbox.
        
        Args:
            sandbox_id: ID del sandbox
            command: Comando a ejecutar
            timeout: Timeout en segundos
            capture_output: Si capturar stdout/stderr
            env: Variables de entorno adicionales
        
        Returns:
            Dict con resultado de la ejecución
        """
        if sandbox_id not in self._sandboxes:
            raise ValueError(f"Sandbox {sandbox_id} no encontrado")
        
        sandbox_info = self._sandboxes[sandbox_id]
        
        if sandbox_info.status not in [SandboxStatus.READY, SandboxStatus.BUSY]:
            raise RuntimeError(f"Sandbox {sandbox_id} no está disponible: {sandbox_info.status}")
        
        sandbox_info.status = SandboxStatus.BUSY
        timeout = timeout or sandbox_info.config.timeout_seconds
        
        try:
            if sandbox_info.container_id:
                result = await self._execute_in_container(
                    sandbox_info, command, timeout, capture_output, env
                )
            else:
                result = await self._execute_in_workspace(
                    sandbox_info, command, timeout, capture_output, env
                )
            
            sandbox_info.execution_count += 1
            sandbox_info.last_activity = datetime.utcnow()
            
            return result
            
        except Exception as e:
            sandbox_info.errors.append(str(e))
            raise
        finally:
            sandbox_info.status = SandboxStatus.READY
    
    async def _execute_in_container(
        self,
        sandbox_info: SandboxInfo,
        command: str,
        timeout: int,
        capture_output: bool,
        env: Optional[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Ejecuta comando en contenedor Docker"""
        docker_cmd = ["docker", "exec"]
        
        if env:
            for key, value in env.items():
                docker_cmd.extend(["-e", f"{key}={value}"])
        
        docker_cmd.extend([
            sandbox_info.container_id,
            "sh", "-c", command
        ])
        
        try:
            result = subprocess.run(
                docker_cmd,
                capture_output=capture_output,
                text=True,
                timeout=timeout
            )
            
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout if capture_output else "",
                "stderr": result.stderr if capture_output else "",
                "command": command,
                "timeout": timeout
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": f"Timeout después de {timeout} segundos",
                "command": command,
                "timeout": True
            }
    
    async def _execute_in_workspace(
        self,
        sandbox_info: SandboxInfo,
        command: str,
        timeout: int,
        capture_output: bool,
        env: Optional[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Ejecuta comando en workspace local"""
        workspace = sandbox_info.workspace_path or tempfile.gettempdir()
        
        execution_env = os.environ.copy()
        execution_env.update(sandbox_info.config.environment_vars)
        if env:
            execution_env.update(env)
        
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=capture_output,
                text=True,
                timeout=timeout,
                cwd=workspace,
                env=execution_env
            )
            
            return {
                "success": result.returncode == 0,
                "returncode": result.returncode,
                "stdout": result.stdout if capture_output else "",
                "stderr": result.stderr if capture_output else "",
                "command": command,
                "timeout": timeout
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "returncode": -1,
                "stdout": "",
                "stderr": f"Timeout después de {timeout} segundos",
                "command": command,
                "timeout": True
            }
    
    async def write_file(
        self,
        sandbox_id: str,
        file_path: str,
        content: str
    ) -> Dict[str, Any]:
        """Escribe un archivo en el sandbox"""
        if sandbox_id not in self._sandboxes:
            raise ValueError(f"Sandbox {sandbox_id} no encontrado")
        
        sandbox_info = self._sandboxes[sandbox_id]
        workspace = sandbox_info.workspace_path
        
        if not workspace:
            raise RuntimeError(f"Sandbox {sandbox_id} no tiene workspace")
        
        # Construir ruta completa
        full_path = Path(workspace) / file_path.lstrip("/")
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Verificar tamaño
        max_size = sandbox_info.config.max_file_size_mb * 1024 * 1024
        if len(content) > max_size:
            raise ValueError(f"Archivo excede tamaño máximo: {len(content)} > {max_size}")
        
        full_path.write_text(content)
        
        return {
            "success": True,
            "path": str(full_path),
            "size": len(content)
        }
    
    async def read_file(
        self,
        sandbox_id: str,
        file_path: str
    ) -> Dict[str, Any]:
        """Lee un archivo del sandbox"""
        if sandbox_id not in self._sandboxes:
            raise ValueError(f"Sandbox {sandbox_id} no encontrado")
        
        sandbox_info = self._sandboxes[sandbox_id]
        workspace = sandbox_info.workspace_path
        
        if not workspace:
            raise RuntimeError(f"Sandbox {sandbox_id} no tiene workspace")
        
        full_path = Path(workspace) / file_path.lstrip("/")
        
        if not full_path.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
        
        content = full_path.read_text()
        
        return {
            "success": True,
            "path": str(full_path),
            "content": content,
            "size": len(content)
        }
    
    async def terminate_sandbox(self, sandbox_id: str) -> bool:
        """Termina y limpia un sandbox"""
        async with self._lock:
            if sandbox_id not in self._sandboxes:
                return False
            
            sandbox_info = self._sandboxes[sandbox_id]
            
            try:
                # Detener contenedor si existe
                if sandbox_info.container_id:
                    subprocess.run(
                        ["docker", "rm", "-f", sandbox_info.container_id],
                        capture_output=True,
                        timeout=10
                    )
                
                # Limpiar workspace
                if sandbox_info.workspace_path and sandbox_info.config.auto_cleanup:
                    if os.path.exists(sandbox_info.workspace_path):
                        shutil.rmtree(sandbox_info.workspace_path)
                
                sandbox_info.status = SandboxStatus.TERMINATED
                
                if self._on_sandbox_terminated:
                    await self._on_sandbox_terminated(sandbox_info)
                
                del self._sandboxes[sandbox_id]
                
                logger.info(f"Sandbox {sandbox_id} terminado")
                return True
                
            except Exception as e:
                logger.error(f"Error terminando sandbox {sandbox_id}: {e}")
                return False
    
    async def get_sandbox_info(self, sandbox_id: str) -> Optional[SandboxInfo]:
        """Obtiene información de un sandbox"""
        return self._sandboxes.get(sandbox_id)
    
    async def list_sandboxes(self) -> List[SandboxInfo]:
        """Lista todos los sandboxes activos"""
        return list(self._sandboxes.values())
    
    async def cleanup_all(self) -> int:
        """Limpia todos los sandboxes"""
        count = 0
        for sandbox_id in list(self._sandboxes.keys()):
            if await self.terminate_sandbox(sandbox_id):
                count += 1
        return count
    
    def on_sandbox_created(self, callback: Callable) -> None:
        """Registra callback para creación de sandbox"""
        self._on_sandbox_created = callback
    
    def on_sandbox_terminated(self, callback: Callable) -> None:
        """Registra callback para terminación de sandbox"""
        self._on_sandbox_terminated = callback


# Alias for backward compatibility
SandboxEnvironment = SandboxManager
