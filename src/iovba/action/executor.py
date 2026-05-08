"""
Action Executor - Ejecutor de Acciones del Agente

Coordina la ejecución de acciones a través de MCP y Skills,
manejando timeouts, retries y logging.
"""

import asyncio
import uuid
from typing import Optional, Dict, Any, List, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ExecutionStatus(str, Enum):
    """Estado de la ejecución"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class ExecutionResult:
    """Resultado de una ejecución"""
    execution_id: str
    action_type: str
    status: ExecutionStatus
    output: Any = None
    error: Optional[str] = None
    execution_time_ms: int = 0
    retries: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionContext:
    """Contexto para la ejecución"""
    session_id: str
    user_id: str
    sandbox_id: Optional[str] = None
    timeout: int = 60
    max_retries: int = 2
    metadata: Dict[str, Any] = field(default_factory=dict)


class ActionExecutor:
    """
    Ejecutor central de acciones del agente.
    
    Coordina la ejecución de herramientas MCP, Skills y comandos directos,
    manejando timeouts, retries y logging exhaustivo.
    
    Usage:
        executor = ActionExecutor(
            mcp_registry=mcp_registry,
            skills_registry=skills_registry
        )
        
        # Ejecutar herramienta MCP
        result = await executor.execute_tool(
            "web_search",
            {"query": "AI news"},
            context
        )
        
        # Ejecutar Skill
        result = await executor.execute_skill(
            "data_analysis",
            {"data": [...]},
            context
        )
    """
    
    def __init__(
        self,
        mcp_registry: Optional[Any] = None,
        skills_registry: Optional[Any] = None,
        sandbox_manager: Optional[Any] = None
    ):
        """
        Inicializa el ejecutor.
        
        Args:
            mcp_registry: Registro MCP para herramientas externas
            skills_registry: Registro de habilidades
            sandbox_manager: Gestor de sandboxes para comandos
        """
        self._mcp_registry = mcp_registry
        self._skills_registry = skills_registry
        self._sandbox_manager = sandbox_manager
        
        self._executions: Dict[str, ExecutionResult] = {}
        self._on_execution_complete: Optional[Callable] = None
    
    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        context: ExecutionContext
    ) -> ExecutionResult:
        """
        Ejecuta una herramienta MCP.
        
        Args:
            tool_name: Nombre de la herramienta
            arguments: Argumentos para la herramienta
            context: Contexto de ejecución
        
        Returns:
            ExecutionResult con el resultado
        """
        execution_id = str(uuid.uuid4())[:8]
        start_time = datetime.utcnow()
        
        result = ExecutionResult(
            execution_id=execution_id,
            action_type=f"tool:{tool_name}",
            status=ExecutionStatus.RUNNING
        )
        
        self._executions[execution_id] = result
        
        try:
            if not self._mcp_registry:
                raise ValueError("MCP Registry no configurado")
            
            # Ejecutar con timeout y retries
            mcp_result = await self._execute_with_retry(
                lambda: self._mcp_registry.execute_tool(tool_name, arguments),
                context.max_retries,
                context.timeout
            )
            
            result.status = ExecutionStatus.COMPLETED if mcp_result.success else ExecutionStatus.FAILED
            result.output = mcp_result.output
            result.error = mcp_result.error
            result.retries = context.max_retries
            
        except asyncio.TimeoutError:
            result.status = ExecutionStatus.TIMEOUT
            result.error = f"Timeout después de {context.timeout}s"
            
        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error = str(e)
        
        result.execution_time_ms = int(
            (datetime.utcnow() - start_time).total_seconds() * 1000
        )
        
        if self._on_execution_complete:
            await self._on_execution_complete(result)
        
        return result
    
    async def execute_skill(
        self,
        skill_id: str,
        parameters: Dict[str, Any],
        context: ExecutionContext
    ) -> ExecutionResult:
        """
        Ejecuta una habilidad.
        
        Args:
            skill_id: ID de la habilidad
            parameters: Parámetros para la habilidad
            context: Contexto de ejecución
        
        Returns:
            ExecutionResult con el resultado
        """
        execution_id = str(uuid.uuid4())[:8]
        start_time = datetime.utcnow()
        
        result = ExecutionResult(
            execution_id=execution_id,
            action_type=f"skill:{skill_id}",
            status=ExecutionStatus.RUNNING
        )
        
        self._executions[execution_id] = result
        
        try:
            if not self._skills_registry:
                raise ValueError("Skills Registry no configurado")
            
            skill = self._skills_registry.get(skill_id) or self._skills_registry.get_by_name(skill_id)
            
            if not skill:
                raise ValueError(f"Skill no encontrada: {skill_id}")
            
            # Verificar herramientas requeridas
            if skill.metadata.required_tools:
                missing_tools = []
                for tool in skill.metadata.required_tools:
                    if self._mcp_registry:
                        mcp_tool = self._mcp_registry.get_tool(tool)
                        if not mcp_tool:
                            missing_tools.append(tool)
                
                if missing_tools:
                    raise ValueError(f"Herramientas requeridas no disponibles: {missing_tools}")
            
            # Ejecutar habilidad (simulado - en producción usaría LLM con las instrucciones)
            skill_result = await self._execute_skill_implementation(
                skill, parameters, context
            )
            
            result.status = ExecutionStatus.COMPLETED
            result.output = skill_result
            
            # Registrar uso
            self._skills_registry.record_usage(
                skill.id,
                success=True,
                execution_time_ms=result.execution_time_ms
            )
            
        except asyncio.TimeoutError:
            result.status = ExecutionStatus.TIMEOUT
            result.error = f"Timeout después de {context.timeout}s"
            
            if self._skills_registry:
                self._skills_registry.record_usage(skill_id, False, 0)
            
        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error = str(e)
            
            if self._skills_registry:
                self._skills_registry.record_usage(skill_id, False, 0)
        
        result.execution_time_ms = int(
            (datetime.utcnow() - start_time).total_seconds() * 1000
        )
        
        if self._on_execution_complete:
            await self._on_execution_complete(result)
        
        return result
    
    async def execute_command(
        self,
        command: str,
        context: ExecutionContext
    ) -> ExecutionResult:
        """
        Ejecuta un comando de shell en sandbox.
        
        Args:
            command: Comando a ejecutar
            context: Contexto de ejecución
        
        Returns:
            ExecutionResult con el resultado
        """
        execution_id = str(uuid.uuid4())[:8]
        start_time = datetime.utcnow()
        
        result = ExecutionResult(
            execution_id=execution_id,
            action_type="command",
            status=ExecutionStatus.RUNNING
        )
        
        self._executions[execution_id] = result
        
        try:
            if not self._sandbox_manager:
                raise ValueError("Sandbox Manager no configurado")
            
            # Verificar sandbox
            sandbox_id = context.sandbox_id
            if not sandbox_id:
                raise ValueError("Sandbox ID requerido para ejecución de comandos")
            
            # Ejecutar comando
            sandbox_result = await self._sandbox_manager.execute(
                sandbox_id,
                command,
                timeout=context.timeout
            )
            
            result.status = ExecutionStatus.COMPLETED if sandbox_result.get("success") else ExecutionStatus.FAILED
            result.output = sandbox_result.get("stdout")
            result.error = sandbox_result.get("stderr")
            
        except asyncio.TimeoutError:
            result.status = ExecutionStatus.TIMEOUT
            result.error = f"Timeout después de {context.timeout}s"
            
        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error = str(e)
        
        result.execution_time_ms = int(
            (datetime.utcnow() - start_time).total_seconds() * 1000
        )
        
        if self._on_execution_complete:
            await self._on_execution_complete(result)
        
        return result
    
    async def _execute_with_retry(
        self,
        action: Callable,
        max_retries: int,
        timeout: int
    ) -> Any:
        """Ejecuta una acción con reintentos y timeout"""
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                return await asyncio.wait_for(
                    action(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                raise
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    await asyncio.sleep(1 * (attempt + 1))  # Backoff exponencial simple
        
        raise last_error
    
    async def _execute_skill_implementation(
        self,
        skill: Any,
        parameters: Dict[str, Any],
        context: ExecutionContext
    ) -> Any:
        """
        Ejecuta la implementación de una skill.
        
        En una implementación completa, esto invocaría un LLM
        con las instrucciones de la skill.
        """
        # Placeholder - simula ejecución
        await asyncio.sleep(0.1)  # Simular trabajo
        
        return {
            "skill": skill.metadata.name,
            "parameters": parameters,
            "result": f"Ejecutado según instrucciones: {skill.instructions[:100]}..."
        }
    
    async def cancel(self, execution_id: str) -> bool:
        """Cancela una ejecución en progreso"""
        if execution_id not in self._executions:
            return False
        
        result = self._executions[execution_id]
        
        if result.status == ExecutionStatus.RUNNING:
            result.status = ExecutionStatus.CANCELLED
            return True
        
        return False
    
    def get_execution(self, execution_id: str) -> Optional[ExecutionResult]:
        """Obtiene información de una ejecución"""
        return self._executions.get(execution_id)
    
    def get_active_executions(self) -> List[ExecutionResult]:
        """Obtiene ejecuciones activas"""
        return [
            r for r in self._executions.values()
            if r.status in [ExecutionStatus.PENDING, ExecutionStatus.RUNNING]
        ]
    
    def get_execution_history(self, limit: int = 100) -> List[ExecutionResult]:
        """Obtiene historial de ejecuciones"""
        return list(self._executions.values())[-limit:]
    
    def clear_history(self) -> None:
        """Limpia el historial de ejecuciones"""
        # Mantener solo ejecuciones activas
        self._executions = {
            k: v for k, v in self._executions.items()
            if v.status in [ExecutionStatus.PENDING, ExecutionStatus.RUNNING]
        }
    
    def on_execution_complete(self, callback: Callable) -> None:
        """Registra callback para completación de ejecuciones"""
        self._on_execution_complete = callback
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del ejecutor"""
        total = len(self._executions)
        
        by_status = {}
        for result in self._executions.values():
            status = result.status.value
            by_status[status] = by_status.get(status, 0) + 1
        
        total_time = sum(r.execution_time_ms for r in self._executions.values())
        avg_time = total_time / total if total > 0 else 0
        
        return {
            "total_executions": total,
            "by_status": by_status,
            "average_execution_time_ms": avg_time,
            "active_executions": len(self.get_active_executions())
        }
