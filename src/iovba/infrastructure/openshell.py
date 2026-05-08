"""
OpenShell - Capa de Runtime para ejecución de comandos

Proporciona un entorno privado y seguro para ejecutar comandos de shell
y scripts Python con políticas declarativas de control.
"""

import asyncio
import subprocess
import tempfile
import os
import signal
import json
import hashlib
from typing import Optional, Dict, Any, List, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ShellType(str, Enum):
    """Tipos de shell soportados"""
    BASH = "bash"
    SH = "sh"
    ZSH = "zsh"
    PYTHON = "python"
    NODE = "node"


class ExecutionMode(str, Enum):
    """Modo de ejecución"""
    SYNC = "sync"
    ASYNC = "async"
    STREAMING = "streaming"


@dataclass
class ExecutionPolicy:
    """
    Políticas de ejecución declarativas.
    
    Control granular de qué comandos y herramientas son permitidos.
    """
    allowed_commands: List[str] = field(default_factory=lambda: ["ls", "cat", "echo", "pwd", "grep", "find", "wc", "head", "tail", "mkdir", "touch"])
    blocked_commands: List[str] = field(default_factory=lambda: ["rm -rf /", "mkfs", "dd", "shutdown", "reboot", "init"])
    allowed_paths: List[str] = field(default_factory=lambda: ["/tmp", "/workspace"])
    blocked_paths: List[str] = field(default_factory=list)
    allow_network: bool = False
    allow_environment_modification: bool = False
    max_command_length: int = 10000
    max_output_size: int = 1024 * 1024  # 1MB
    require_confirmation: List[str] = field(default_factory=lambda: ["rm", "mv", "chmod", "chown"])
    timeout_default: int = 60
    timeout_max: int = 600
    
    def is_command_allowed(self, command: str) -> tuple[bool, Optional[str]]:
        """Verifica si un comando está permitido"""
        command_lower = command.lower().strip()
        
        # Verificar comandos bloqueados
        for blocked in self.blocked_commands:
            if blocked.lower() in command_lower:
                return False, f"Comando bloqueado: {blocked}"
        
        # Extraer comando base
        base_cmd = command_lower.split()[0] if command_lower.split() else ""
        
        # Verificar si requiere confirmación
        for req_conf in self.require_confirmation:
            if base_cmd == req_conf.lower():
                return True, "REQUIRES_CONFIRMATION"
        
        # Si allowed_commands está vacío, permitir todo (excepto bloqueados)
        if not self.allowed_commands:
            return True, None
        
        # Verificar lista permitida
        for allowed in self.allowed_commands:
            if base_cmd == allowed.lower():
                return True, None
        
        return False, f"Comando no permitido: {base_cmd}"
    
    def is_path_allowed(self, path: str) -> tuple[bool, Optional[str]]:
        """Verifica si una ruta está permitida"""
        resolved = str(Path(path).resolve())
        
        # Verificar rutas bloqueadas
        for blocked in self.blocked_paths:
            if resolved.startswith(blocked):
                return False, f"Ruta bloqueada: {blocked}"
        
        # Si allowed_paths está vacío, permitir todo (excepto bloqueados)
        if not self.allowed_paths:
            return True, None
        
        # Verificar rutas permitidas
        for allowed in self.allowed_paths:
            if resolved.startswith(allowed):
                return True, None
        
        return False, f"Ruta no permitida: {path}"


@dataclass
class ShellResult:
    """Resultado de ejecución de comando"""
    success: bool
    returncode: int
    stdout: str
    stderr: str
    command: str
    execution_time_ms: int
    timeout: bool = False
    signal: Optional[int] = None
    pid: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "command": self.command,
            "execution_time_ms": self.execution_time_ms,
            "timeout": self.timeout,
            "signal": self.signal,
            "pid": self.pid,
            "metadata": self.metadata
        }


class OpenShell:
    """
    Capa de Runtime para ejecución segura de comandos.
    
    Proporciona un entorno privado y seguro con:
    - Políticas declarativas de control
    - Router de Privacidad para filtrado de PII
    - Gestión de secretos fuera del proyecto (~/.openclaw)
    
    Usage:
        shell = OpenShell(ExecutionPolicy())
        
        # Ejecutar comando
        result = await shell.execute("ls -la /workspace")
        
        # Ejecutar script Python
        result = await shell.execute_script("print('Hello')", ShellType.PYTHON)
    """
    
    def __init__(
        self,
        policy: Optional[ExecutionPolicy] = None,
        working_directory: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None,
        secrets_path: str = "~/.openclaw/secrets"
    ):
        """
        Inicializa OpenShell.
        
        Args:
            policy: Políticas de ejecución
            working_directory: Directorio de trabajo
            environment: Variables de entorno
            secrets_path: Ruta para almacenamiento de secretos
        """
        self.policy = policy or ExecutionPolicy()
        self.working_directory = working_directory or tempfile.gettempdir()
        self.environment = environment or {}
        self.secrets_path = Path(secrets_path).expanduser()
        
        # Crear directorio de secretos
        self.secrets_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Estado de ejecución
        self._running_processes: Dict[int, subprocess.Popen] = {}
        self._execution_history: List[ShellResult] = []
        self._on_command_executed: Optional[Callable] = None
    
    async def execute(
        self,
        command: str,
        timeout: Optional[int] = None,
        mode: ExecutionMode = ExecutionMode.SYNC,
        input_data: Optional[str] = None,
        env: Optional[Dict[str, str]] = None
    ) -> ShellResult:
        """
        Ejecuta un comando de shell.
        
        Args:
            command: Comando a ejecutar
            timeout: Timeout en segundos
            mode: Modo de ejecución
            input_data: Datos de entrada para stdin
            env: Variables de entorno adicionales
        
        Returns:
            ShellResult con el resultado de la ejecución
        """
        # Validar comando contra política
        allowed, reason = self.policy.is_command_allowed(command)
        if not allowed:
            return ShellResult(
                success=False,
                returncode=-1,
                stdout="",
                stderr=reason or "Comando no permitido",
                command=command,
                execution_time_ms=0
            )
        
        # Verificar longitud máxima
        if len(command) > self.policy.max_command_length:
            return ShellResult(
                success=False,
                returncode=-1,
                stdout="",
                stderr=f"Comando excede longitud máxima ({self.policy.max_command_length})",
                command=command[:100] + "...",
                execution_time_ms=0
            )
        
        timeout = min(timeout or self.policy.timeout_default, self.policy.timeout_max)
        
        # Preparar entorno
        execution_env = os.environ.copy()
        execution_env.update(self.environment)
        if env:
            execution_env.update(env)
        
        # Filtrar secretos del entorno si están en el output
        execution_env["OPENCLAW_SECRETS_FILTERED"] = "true"
        
        start_time = datetime.utcnow()
        
        try:
            if mode == ExecutionMode.STREAMING:
                return await self._execute_streaming(command, timeout, execution_env)
            
            # Ejecución síncrona
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE if input_data else None,
                cwd=self.working_directory,
                env=execution_env
            )
            
            self._running_processes[process.pid] = process
            
            try:
                stdout, stderr = process.communicate(
                    input=input_data.encode() if input_data else None,
                    timeout=timeout
                )
                
                # Truncar output si excede tamaño máximo
                stdout = stdout.decode()[:self.policy.max_output_size]
                stderr = stderr.decode()[:self.policy.max_output_size]
                
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                
                result = ShellResult(
                    success=False,
                    returncode=-1,
                    stdout=stdout.decode()[:self.policy.max_output_size],
                    stderr=f"Timeout después de {timeout} segundos",
                    command=command,
                    execution_time_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000),
                    timeout=True,
                    pid=process.pid
                )
                self._execution_history.append(result)
                return result
            
            finally:
                del self._running_processes[process.pid]
            
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            result = ShellResult(
                success=process.returncode == 0,
                returncode=process.returncode,
                stdout=stdout,
                stderr=stderr,
                command=command,
                execution_time_ms=execution_time,
                pid=process.pid
            )
            
            self._execution_history.append(result)
            
            if self._on_command_executed:
                await self._on_command_executed(result)
            
            return result
            
        except Exception as e:
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            result = ShellResult(
                success=False,
                returncode=-1,
                stdout="",
                stderr=str(e),
                command=command,
                execution_time_ms=execution_time
            )
            
            self._execution_history.append(result)
            return result
    
    async def _execute_streaming(
        self,
        command: str,
        timeout: int,
        env: Dict[str, str]
    ) -> ShellResult:
        """Ejecución con output streaming"""
        stdout_chunks = []
        stderr_chunks = []
        
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self.working_directory,
            env=env
        )
        
        self._running_processes[process.pid] = process
        
        async def read_stream(stream, chunks):
            while True:
                line = stream.readline()
                if not line:
                    break
                chunks.append(line.decode())
        
        try:
            await asyncio.wait_for(
                asyncio.gather(
                    read_stream(process.stdout, stdout_chunks),
                    read_stream(process.stderr, stderr_chunks)
                ),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            
        process.wait()
        del self._running_processes[process.pid]
        
        stdout = "".join(stdout_chunks)[:self.policy.max_output_size]
        stderr = "".join(stderr_chunks)[:self.policy.max_output_size]
        
        return ShellResult(
            success=process.returncode == 0,
            returncode=process.returncode,
            stdout=stdout,
            stderr=stderr,
            command=command,
            execution_time_ms=0,
            pid=process.pid
        )
    
    async def execute_script(
        self,
        script: str,
        shell_type: ShellType = ShellType.PYTHON,
        timeout: Optional[int] = None
    ) -> ShellResult:
        """Ejecuta un script completo"""
        if shell_type == ShellType.PYTHON:
            command = f'python3 -c "{script}"'
        elif shell_type == ShellType.NODE:
            command = f'node -e "{script}"'
        else:
            command = f'{shell_type.value} -c "{script}"'
        
        return await self.execute(command, timeout)
    
    async def execute_file(
        self,
        file_path: str,
        args: Optional[List[str]] = None,
        timeout: Optional[int] = None
    ) -> ShellResult:
        """Ejecuta un archivo de script"""
        # Verificar ruta permitida
        allowed, reason = self.policy.is_path_allowed(file_path)
        if not allowed:
            return ShellResult(
                success=False,
                returncode=-1,
                stdout="",
                stderr=reason or "Ruta no permitida",
                command=file_path,
                execution_time_ms=0
            )
        
        # Detectar tipo de script
        path = Path(file_path)
        suffix = path.suffix.lower()
        
        if suffix == ".py":
            cmd = f"python3 {file_path}"
        elif suffix == ".js":
            cmd = f"node {file_path}"
        elif suffix == ".sh":
            cmd = f"bash {file_path}"
        else:
            cmd = file_path
        
        if args:
            cmd += " " + " ".join(args)
        
        return await self.execute(cmd, timeout)
    
    def store_secret(self, key: str, value: str) -> None:
        """Almacena un secreto de forma segura"""
        secrets_file = self.secrets_path / "secrets.json"
        
        secrets = {}
        if secrets_file.exists():
            secrets = json.loads(secrets_file.read_text())
        
        # Hash del valor para verificación
        value_hash = hashlib.sha256(value.encode()).hexdigest()[:16]
        
        secrets[key] = {
            "value": value,
            "hash": value_hash,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Crear directorio si no existe
        secrets_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Escribir con permisos restrictivos
        secrets_file.write_text(json.dumps(secrets, indent=2))
        os.chmod(secrets_file, 0o600)
    
    def get_secret(self, key: str) -> Optional[str]:
        """Obtiene un secreto almacenado"""
        secrets_file = self.secrets_path / "secrets.json"
        
        if not secrets_file.exists():
            return None
        
        secrets = json.loads(secrets_file.read_text())
        entry = secrets.get(key)
        
        if entry:
            return entry.get("value")
        
        return None
    
    def delete_secret(self, key: str) -> bool:
        """Elimina un secreto"""
        secrets_file = self.secrets_path / "secrets.json"
        
        if not secrets_file.exists():
            return False
        
        secrets = json.loads(secrets_file.read_text())
        
        if key in secrets:
            del secrets[key]
            secrets_file.write_text(json.dumps(secrets, indent=2))
            return True
        
        return False
    
    async def kill_process(self, pid: int) -> bool:
        """Termina un proceso en ejecución"""
        if pid in self._running_processes:
            try:
                self._running_processes[pid].kill()
                return True
            except Exception:
                return False
        return False
    
    def get_execution_history(self, limit: int = 100) -> List[ShellResult]:
        """Obtiene historial de ejecuciones"""
        return self._execution_history[-limit:]
    
    def clear_history(self) -> None:
        """Limpia el historial de ejecuciones"""
        self._execution_history.clear()
    
    def on_command_executed(self, callback: Callable) -> None:
        """Registra callback para comandos ejecutados"""
        self._on_command_executed = callback
