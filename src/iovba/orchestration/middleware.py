"""
Middleware Chain para Lead Agent

Implementa los 9 middlewares de deer-flow para procesar cada turno
de la conversación de forma modular y extensible.
"""

import asyncio
from typing import Optional, Dict, Any, List, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class MiddlewareContext:
    """Contexto pasado entre middlewares"""
    session_id: str
    thread_id: str
    messages: List[Dict[str, Any]] = field(default_factory=list)
    state: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    skipped_middlewares: List[str] = field(default_factory=list)


class MiddlewareBase(ABC):
    """Clase base para todos los middlewares"""
    
    name: str = "base_middleware"
    priority: int = 100  # Menor número = mayor prioridad
    
    @abstractmethod
    async def process(
        self,
        context: MiddlewareContext,
        next_middleware: Callable
    ) -> MiddlewareContext:
        """
        Procesa el contexto y pasa al siguiente middleware.
        
        Args:
            context: Contexto actual
            next_middleware: Función para llamar al siguiente middleware
        
        Returns:
            Contexto modificado
        """
        pass
    
    async def should_skip(self, context: MiddlewareContext) -> bool:
        """Determina si este middleware debe saltarse"""
        return False


class MiddlewareChain:
    """
    Cadena de middlewares para procesar solicitudes.
    
    Ejecuta los middlewares en orden de prioridad, permitiendo
    que cada uno modifique el contexto antes de pasar al siguiente.
    
    Usage:
        chain = MiddlewareChain()
        chain.add(ThreadDataMiddleware())
        chain.add(SandboxAcquisitionMiddleware())
        
        result = await chain.execute(context)
    """
    
    def __init__(self):
        self._middlewares: List[MiddlewareBase] = []
        self._on_middleware_error: Optional[Callable] = None
    
    def add(self, middleware: MiddlewareBase) -> "MiddlewareChain":
        """Añade un middleware a la cadena"""
        self._middlewares.append(middleware)
        self._middlewares.sort(key=lambda m: m.priority)
        return self
    
    def remove(self, name: str) -> bool:
        """Remueve un middleware por nombre"""
        for i, m in enumerate(self._middlewares):
            if m.name == name:
                self._middlewares.pop(i)
                return True
        return False
    
    async def execute(
        self,
        context: MiddlewareContext
    ) -> MiddlewareContext:
        """
        Ejecuta la cadena completa de middlewares.
        
        Args:
            context: Contexto inicial
        
        Returns:
            Contexto después de procesar todos los middlewares
        """
        if not self._middlewares:
            return context
        
        async def run_middlewares(index: int, ctx: MiddlewareContext) -> MiddlewareContext:
            if index >= len(self._middlewares):
                return ctx
            
            middleware = self._middlewares[index]
            
            # Verificar si debe saltarse
            if await middleware.should_skip(ctx):
                ctx.skipped_middlewares.append(middleware.name)
                return await run_middlewares(index + 1, ctx)
            
            try:
                logger.debug(f"Ejecutando middleware: {middleware.name}")
                
                return await middleware.process(
                    ctx,
                    lambda c: run_middlewares(index + 1, c)
                )
                
            except Exception as e:
                ctx.errors.append(f"{middleware.name}: {str(e)}")
                
                if self._on_middleware_error:
                    await self._on_middleware_error(middleware.name, e, ctx)
                
                # Continuar con el siguiente middleware
                return await run_middlewares(index + 1, ctx)
        
        return await run_middlewares(0, context)
    
    def get_middlewares(self) -> List[str]:
        """Obtiene lista de middlewares registrados"""
        return [m.name for m in self._middlewares]
    
    def on_error(self, callback: Callable) -> None:
        """Registra callback para errores de middleware"""
        self._on_middleware_error = callback


# =============================================================================
# MIDDLEWARES ESPECÍFICOS
# =============================================================================

class ThreadDataMiddleware(MiddlewareBase):
    """
    Middleware para gestión de datos por hilo.
    
    Mantiene el estado de la conversación agrupado por thread_id,
    permitiendo conversaciones paralelas independientes.
    """
    
    name = "thread_data"
    priority = 10
    
    def __init__(self, max_threads: int = 100, thread_ttl: int = 3600):
        self.max_threads = max_threads
        self.thread_ttl = thread_ttl
        self._threads: Dict[str, Dict[str, Any]] = {}
    
    async def process(
        self,
        context: MiddlewareContext,
        next_middleware: Callable
    ) -> MiddlewareContext:
        thread_id = context.thread_id
        
        # Crear o recuperar thread
        if thread_id not in self._threads:
            self._threads[thread_id] = {
                "created_at": datetime.utcnow(),
                "messages": [],
                "state": {}
            }
        
        # Cargar datos del thread
        thread_data = self._threads[thread_id]
        context.metadata["thread_data"] = thread_data
        
        # Ejecutar siguiente
        result = await next_middleware(context)
        
        # Guardar cambios
        self._threads[thread_id] = result.metadata.get("thread_data", thread_data)
        
        return result


class SandboxAcquisitionMiddleware(MiddlewareBase):
    """
    Middleware para adquisición de sandboxes.
    
    Gestiona el ciclo de vida de sandboxes para cada sesión,
    reutilizando cuando es posible y limpiando cuando es necesario.
    """
    
    name = "sandbox_acquisition"
    priority = 20
    
    def __init__(self, sandbox_manager: Optional[Any] = None):
        self._sandbox_manager = sandbox_manager
        self._session_sandboxes: Dict[str, str] = {}
    
    async def process(
        self,
        context: MiddlewareContext,
        next_middleware: Callable
    ) -> MiddlewareContext:
        session_id = context.session_id
        
        # Verificar sandbox existente
        if session_id in self._session_sandboxes:
            sandbox_id = self._session_sandboxes[session_id]
            context.metadata["sandbox_id"] = sandbox_id
        else:
            # Crear nuevo sandbox si el manager está disponible
            if self._sandbox_manager:
                from ..infrastructure.sandbox import SandboxConfig
                sandbox = await self._sandbox_manager.create_sandbox(
                    SandboxConfig(sandbox_id=f"{session_id[:8]}")
                )
                self._session_sandboxes[session_id] = sandbox.sandbox_id
                context.metadata["sandbox_id"] = sandbox.sandbox_id
        
        return await next_middleware(context)
    
    async def release_sandbox(self, session_id: str) -> bool:
        """Libera el sandbox de una sesión"""
        if session_id in self._session_sandboxes and self._sandbox_manager:
            sandbox_id = self._session_sandboxes[session_id]
            result = await self._sandbox_manager.terminate_sandbox(sandbox_id)
            if result:
                del self._session_sandboxes[session_id]
            return result
        return False


class ContextSummarizationMiddleware(MiddlewareBase):
    """
    Middleware para sumarización de contexto.
    
    Previene el desbordamiento de tokens sumarizando el contexto
    cuando excede el límite configurado.
    """
    
    name = "context_summarization"
    priority = 30
    
    def __init__(
        self,
        max_tokens: int = 100000,
        summarization_threshold: float = 0.8
    ):
        self.max_tokens = max_tokens
        self.summarization_threshold = summarization_threshold
    
    async def process(
        self,
        context: MiddlewareContext,
        next_middleware: Callable
    ) -> MiddlewareContext:
        messages = context.messages
        
        # Estimar tokens (aproximación: 4 caracteres = 1 token)
        total_chars = sum(len(m.get("content", "")) for m in messages)
        estimated_tokens = total_chars // 4
        
        if estimated_tokens > self.max_tokens * self.summarization_threshold:
            # Sumarizar mensajes antiguos
            summarized = await self._summarize_messages(messages[:-10])
            
            context.messages = messages[-10:]
            context.metadata["summarized_context"] = summarized
            context.metadata["tokens_saved"] = estimated_tokens - len(summarized) // 4
        
        return await next_middleware(context)
    
    async def _summarize_messages(self, messages: List[Dict[str, Any]]) -> str:
        """Sumariza una lista de mensajes"""
        # Placeholder - en implementación real usaría LLM
        return f"Sumarizado: {len(messages)} mensajes"


class TaskListMiddleware(MiddlewareBase):
    """
    Middleware para gestión de listas de tareas dinámicas.
    
    Mantiene una lista de tareas pendientes que puede ser
    modificada durante la ejecución.
    """
    
    name = "task_list"
    priority = 40
    
    async def process(
        self,
        context: MiddlewareContext,
        next_middleware: Callable
    ) -> MiddlewareContext:
        # Inicializar lista de tareas si no existe
        if "tasks" not in context.state:
            context.state["tasks"] = {
                "pending": [],
                "in_progress": None,
                "completed": [],
                "failed": []
            }
        
        return await next_middleware(context)
    
    def add_task(self, context: MiddlewareContext, task: Dict[str, Any]) -> None:
        """Añade una tarea pendiente"""
        context.state["tasks"]["pending"].append(task)
    
    def start_task(self, context: MiddlewareContext) -> Optional[Dict[str, Any]]:
        """Inicia la siguiente tarea pendiente"""
        if context.state["tasks"]["pending"]:
            task = context.state["tasks"]["pending"].pop(0)
            context.state["tasks"]["in_progress"] = task
            return task
        return None
    
    def complete_task(self, context: MiddlewareContext, result: Any) -> None:
        """Marca la tarea actual como completada"""
        if context.state["tasks"]["in_progress"]:
            task = context.state["tasks"]["in_progress"]
            task["result"] = result
            context.state["tasks"]["completed"].append(task)
            context.state["tasks"]["in_progress"] = None
    
    def fail_task(self, context: MiddlewareContext, error: str) -> None:
        """Marca la tarea actual como fallida"""
        if context.state["tasks"]["in_progress"]:
            task = context.state["tasks"]["in_progress"]
            task["error"] = error
            context.state["tasks"]["failed"].append(task)
            context.state["tasks"]["in_progress"] = None


class MemoryMiddleware(MiddlewareBase):
    """
    Middleware para gestión de memoria del agente.
    
    Carga memorias relevantes al inicio y guarda nuevas memorias
    al final de cada interacción exitosa.
    """
    
    name = "memory"
    priority = 50
    
    def __init__(self, memory_vcs: Optional[Any] = None):
        self._memory_vcs = memory_vcs
    
    async def process(
        self,
        context: MiddlewareContext,
        next_middleware: Callable
    ) -> MiddlewareContext:
        # Cargar memorias relevantes
        if self._memory_vcs:
            relevant = await self._load_relevant_memories(context)
            context.metadata["relevant_memories"] = relevant
        
        # Ejecutar siguiente
        result = await next_middleware(context)
        
        # Guardar nuevas memorias si la ejecución fue exitosa
        if not result.errors and self._memory_vcs:
            await self._save_new_memories(result)
        
        return result
    
    async def _load_relevant_memories(self, context: MiddlewareContext) -> List[Dict[str, Any]]:
        """Carga memorias relevantes para el contexto actual"""
        # Placeholder
        return []
    
    async def _save_new_memories(self, context: MiddlewareContext) -> None:
        """Guarda nuevas memorias del contexto"""
        # Placeholder
        pass


class ToolAuthorizationMiddleware(MiddlewareBase):
    """
    Middleware para autorización de herramientas en tiempo real.
    
    Verifica permisos antes de cada llamada a herramienta.
    """
    
    name = "tool_authorization"
    priority = 60
    
    def __init__(self, policy_engine: Optional[Any] = None):
        self._policy_engine = policy_engine
    
    async def process(
        self,
        context: MiddlewareContext,
        next_middleware: Callable
    ) -> MiddlewareContext:
        # Inicializar registro de autorizaciones
        if "tool_authorizations" not in context.metadata:
            context.metadata["tool_authorizations"] = {
                "allowed": [],
                "denied": [],
                "pending": []
            }
        
        return await next_middleware(context)
    
    async def authorize_tool(
        self,
        context: MiddlewareContext,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> bool:
        """Autoriza el uso de una herramienta"""
        if self._policy_engine:
            result = await self._policy_engine.check_permission(
                context.session_id,
                "tool",
                tool_name,
                arguments
            )
            return result.allowed
        
        # Sin motor de políticas, permitir por defecto
        return True


class ProgressReportingMiddleware(MiddlewareBase):
    """
    Middleware para reporte de progreso.
    
    Emite eventos de progreso que pueden ser capturados por
    callbacks registrados.
    """
    
    name = "progress_reporting"
    priority = 70
    
    def __init__(self):
        self._progress_callbacks: List[Callable] = []
    
    async def process(
        self,
        context: MiddlewareContext,
        next_middleware: Callable
    ) -> MiddlewareContext:
        # Inicializar tracking de progreso
        context.metadata["progress"] = {
            "started_at": datetime.utcnow().isoformat(),
            "current_step": 0,
            "total_steps": 0,
            "percentage": 0.0
        }
        
        await self._emit_progress(context, "started")
        
        result = await next_middleware(context)
        
        result.metadata["progress"]["completed_at"] = datetime.utcnow().isoformat()
        result.metadata["progress"]["percentage"] = 100.0
        
        await self._emit_progress(result, "completed")
        
        return result
    
    def add_callback(self, callback: Callable) -> None:
        """Añade callback para eventos de progreso"""
        self._progress_callbacks.append(callback)
    
    async def _emit_progress(self, context: MiddlewareContext, event: str) -> None:
        """Emite evento de progreso"""
        for callback in self._progress_callbacks:
            try:
                await callback(event, context.metadata.get("progress", {}), context)
            except Exception as e:
                logger.error(f"Error en callback de progreso: {e}")


class ErrorRecoveryMiddleware(MiddlewareBase):
    """
    Middleware para recuperación de errores.
    
    Captura errores y aplica estrategias de recuperación
    configuradas.
    """
    
    name = "error_recovery"
    priority = 80
    
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self._error_handlers: Dict[str, Callable] = {}
    
    async def process(
        self,
        context: MiddlewareContext,
        next_middleware: Callable
    ) -> MiddlewareContext:
        # Inicializar registro de errores
        if "error_recovery" not in context.metadata:
            context.metadata["error_recovery"] = {
                "attempts": 0,
                "recovered": False,
                "errors": []
            }
        
        try:
            return await next_middleware(context)
        except Exception as e:
            return await self._handle_error(context, e)
    
    async def _handle_error(
        self,
        context: MiddlewareContext,
        error: Exception
    ) -> MiddlewareContext:
        """Maneja un error con estrategia de recuperación"""
        error_type = type(error).__name__
        
        context.metadata["error_recovery"]["errors"].append({
            "type": error_type,
            "message": str(error),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Buscar handler específico
        if error_type in self._error_handlers:
            try:
                await self._error_handlers[error_type](context, error)
                context.metadata["error_recovery"]["recovered"] = True
            except Exception as handler_error:
                context.errors.append(f"Error recovery failed: {handler_error}")
        
        return context
    
    def register_handler(self, error_type: str, handler: Callable) -> None:
        """Registra un handler para un tipo de error específico"""
        self._error_handlers[error_type] = handler


class CheckpointMiddleware(MiddlewareBase):
    """
    Middleware para checkpoints y persistencia de estado.
    
    Guarda checkpoints periódicos que permiten reanudar
    desde un punto conocido en caso de fallo.
    """
    
    name = "checkpoint"
    priority = 90
    
    def __init__(
        self,
        checkpoint_interval: int = 5,
        checkpoint_storage: Optional[Any] = None
    ):
        self.checkpoint_interval = checkpoint_interval
        self._storage = checkpoint_storage
        self._checkpoints: Dict[str, List[Dict[str, Any]]] = {}
    
    async def process(
        self,
        context: MiddlewareContext,
        next_middleware: Callable
    ) -> MiddlewareContext:
        session_id = context.session_id
        
        # Crear checkpoint inicial
        await self._save_checkpoint(session_id, context, "start")
        
        # Ejecutar siguiente
        result = await next_middleware(context)
        
        # Crear checkpoint final
        await self._save_checkpoint(session_id, result, "end")
        
        return result
    
    async def _save_checkpoint(
        self,
        session_id: str,
        context: MiddlewareContext,
        phase: str
    ) -> None:
        """Guarda un checkpoint"""
        checkpoint = {
            "phase": phase,
            "timestamp": datetime.utcnow().isoformat(),
            "state": context.state.copy(),
            "messages_count": len(context.messages)
        }
        
        if session_id not in self._checkpoints:
            self._checkpoints[session_id] = []
        
        self._checkpoints[session_id].append(checkpoint)
        
        # Persistir si hay storage
        if self._storage:
            await self._storage.save(f"checkpoint_{session_id}_{phase}", checkpoint)
    
    async def restore_checkpoint(
        self,
        session_id: str,
        phase: str = "start"
    ) -> Optional[MiddlewareContext]:
        """Restaura desde un checkpoint"""
        checkpoints = self._checkpoints.get(session_id, [])
        
        for checkpoint in reversed(checkpoints):
            if checkpoint["phase"] == phase:
                context = MiddlewareContext(
                    session_id=session_id,
                    thread_id="",
                    state=checkpoint["state"]
                )
                return context
        
        return None
