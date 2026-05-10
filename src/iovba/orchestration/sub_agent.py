"""
Sub-Agent - Agentes Especializados para Tareas Específicas

Cada sub-agente tiene su propia terminal, sistema de archivos y
herramientas específicas, reportando resultados estructurados
al agente líder para su síntesis final.
"""

import asyncio
import uuid
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SubAgentStatus(str, Enum):
    """Estado del sub-agente"""
    CREATED = "created"
    INITIALIZING = "initializing"
    READY = "ready"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    TERMINATED = "terminated"


class SubAgentRole(str, Enum):
    """Roles especializados de sub-agentes"""
    RESEARCHER = "researcher"
    CODER = "coder"
    ANALYZER = "analyzer"
    WRITER = "writer"
    VALIDATOR = "validator"
    COORDINATOR = "coordinator"
    SPECIALIST = "specialist"


@dataclass
class SubAgentConfig:
    """Configuración de un sub-agente"""
    agent_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "Sub-Agent"
    role: SubAgentRole = SubAgentRole.SPECIALIST
    parent_agent_id: Optional[str] = None
    
    # Recursos
    sandbox_id: Optional[str] = None
    workspace_path: Optional[str] = None
    
    # Capacidades
    allowed_tools: List[str] = field(default_factory=list)
    restricted_tools: List[str] = field(default_factory=list)
    max_execution_time: int = 300
    
    # Comunicación
    report_interval: int = 30
    checkpoint_enabled: bool = True
    
    # Especialización
    domain: Optional[str] = None
    custom_instructions: Optional[str] = None


@dataclass
class SubAgentResult:
    """Resultado de ejecución de un sub-agente"""
    agent_id: str
    success: bool
    status: SubAgentStatus
    
    # Resultado
    output: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    
    # Métricas
    execution_time_ms: int = 0
    tokens_used: int = 0
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    
    # Errores
    error: Optional[str] = None
    error_trace: Optional[str] = None
    
    # Metadatos
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    checkpoints: List[Dict[str, Any]] = field(default_factory=list)


class SubAgent:
    """
    Sub-Agente Especializado.
    
    Opera en un contexto aislado con sus propias herramientas y recursos,
    reportando resultados estructurados al agente líder.
    
    Usage:
        config = SubAgentConfig(
            role=SubAgentRole.RESEARCHER,
            domain="finance"
        )
        
        sub_agent = SubAgent(config)
        result = await sub_agent.execute({
            "task": "Analizar tendencias del mercado",
            "context": {...}
        })
    """
    
    def __init__(
        self,
        config: SubAgentConfig,
        sandbox_manager: Optional[Any] = None,
        tool_registry: Optional[Any] = None
    ):
        """
        Inicializa el sub-agente.
        
        Args:
            config: Configuración del sub-agente
            sandbox_manager: Gestor de sandboxes
            tool_registry: Registro de herramientas disponibles
        """
        self.config = config
        self.status = SubAgentStatus.CREATED
        self._sandbox_manager = sandbox_manager
        self._tool_registry = tool_registry
        
        # Estado interno
        self._workspace: Optional[str] = None
        self._current_task: Optional[str] = None
        self._execution_log: List[Dict[str, Any]] = []
        
        # Callbacks
        self._on_progress: Optional[Callable] = None
        self._on_tool_call: Optional[Callable] = None
    
    async def initialize(self) -> bool:
        """Inicializa el sub-agente"""
        self.status = SubAgentStatus.INITIALIZING
        
        try:
            # Crear sandbox si no existe
            if self._sandbox_manager and not self.config.sandbox_id:
                from ..infrastructure.sandbox import SandboxConfig
                sandbox = await self._sandbox_manager.create_sandbox(
                    SandboxConfig(sandbox_id=f"sub_{self.config.agent_id}")
                )
                self.config.sandbox_id = sandbox.sandbox_id
                self._workspace = sandbox.workspace_path
            
            self.status = SubAgentStatus.READY
            return True
            
        except Exception as e:
            self.status = SubAgentStatus.FAILED
            logger.error(f"Error inicializando sub-agente {self.config.agent_id}: {e}")
            return False
    
    async def execute(
        self,
        task: Dict[str, Any]
    ) -> SubAgentResult:
        """
        Ejecuta una tarea asignada.
        
        Args:
            task: Tarea con descripción y contexto
        
        Returns:
            SubAgentResult con el resultado de la ejecución
        """
        if self.status != SubAgentStatus.READY:
            # Intentar inicializar si no está listo
            if not await self.initialize():
                return SubAgentResult(
                    agent_id=self.config.agent_id,
                    success=False,
                    status=self.status,
                    error="Sub-agente no pudo inicializarse"
                )
        
        self.status = SubAgentStatus.EXECUTING
        self._current_task = task.get("description")
        
        result = SubAgentResult(
            agent_id=self.config.agent_id,
            success=False,
            status=SubAgentStatus.EXECUTING,
            started_at=datetime.utcnow()
        )
        
        start_time = datetime.utcnow()
        
        try:
            # Ejecutar según rol
            if self.config.role == SubAgentRole.RESEARCHER:
                output = await self._execute_research(task)
            elif self.config.role == SubAgentRole.CODER:
                output = await self._execute_coding(task)
            elif self.config.role == SubAgentRole.ANALYZER:
                output = await self._execute_analysis(task)
            elif self.config.role == SubAgentRole.WRITER:
                output = await self._execute_writing(task)
            elif self.config.role == SubAgentRole.VALIDATOR:
                output = await self._execute_validation(task)
            else:
                output = await self._execute_generic(task)
            
            result.success = True
            result.output = output.get("output")
            result.data = output.get("data")
            result.artifacts = output.get("artifacts", [])
            result.tool_calls = output.get("tool_calls", [])
            result.status = SubAgentStatus.COMPLETED
            
        except Exception as e:
            result.status = SubAgentStatus.FAILED
            result.error = str(e)
            self.status = SubAgentStatus.FAILED
        
        result.completed_at = datetime.utcnow()
        result.execution_time_ms = int(
            (result.completed_at - start_time).total_seconds() * 1000
        )
        
        return result
    
    async def _execute_research(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta tarea de investigación"""
        # Placeholder - en implementación real usaría herramientas de búsqueda
        return {
            "output": f"Investigación completada: {task.get('description')}",
            "data": {"findings": []},
            "tool_calls": [{"tool": "search", "query": task.get("description")}]
        }
    
    async def _execute_coding(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta tarea de codificación"""
        # Placeholder - en implementación real usaría herramientas de código
        return {
            "output": f"Código generado para: {task.get('description')}",
            "data": {"code": "# Generated code"},
            "artifacts": [{"type": "file", "path": "output.py"}]
        }
    
    async def _execute_analysis(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta tarea de análisis"""
        return {
            "output": f"Análisis completado: {task.get('description')}",
            "data": {"insights": []}
        }
    
    async def _execute_writing(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta tarea de escritura"""
        return {
            "output": f"Contenido generado: {task.get('description')}",
            "data": {"content": ""}
        }
    
    async def _execute_validation(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta tarea de validación"""
        return {
            "output": f"Validación completada: {task.get('description')}",
            "data": {"valid": True, "issues": []}
        }
    
    async def _execute_generic(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta tarea genérica"""
        return {
            "output": f"Tarea completada: {task.get('description')}",
            "data": {}
        }
    
    async def terminate(self) -> bool:
        """Termina el sub-agente y limpia recursos"""
        try:
            if self._sandbox_manager and self.config.sandbox_id:
                await self._sandbox_manager.terminate_sandbox(self.config.sandbox_id)
            
            self.status = SubAgentStatus.TERMINATED
            return True
            
        except Exception as e:
            logger.error(f"Error terminando sub-agente {self.config.agent_id}: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado actual del sub-agente"""
        return {
            "agent_id": self.config.agent_id,
            "name": self.config.name,
            "role": self.config.role.value,
            "status": self.status.value,
            "current_task": self._current_task,
            "sandbox_id": self.config.sandbox_id
        }
    
    def on_progress(self, callback: Callable) -> None:
        """Registra callback para reportes de progreso"""
        self._on_progress = callback
    
    def on_tool_call(self, callback: Callable) -> None:
        """Registra callback para llamadas a herramientas"""
        self._on_tool_call = callback


# Alias for backward compatibility
SubAgentCoordinator = SubAgent
