"""
Lead Agent - Coordinador Central de Super-Agentes

El Lead Agent actúa como el conductor central, utilizando LangGraph para
la gestión de estados y la coordinación de sub-agentes jerárquicos.
"""

import asyncio
import uuid
from typing import Optional, Dict, Any, List, Callable, AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AgentStatus(str, Enum):
    """Estado del agente"""
    IDLE = "idle"
    PREPARING = "preparing"
    ALIGNING = "aligning"
    EXECUTING = "executing"
    WAITING = "waiting"
    COMPLETED = "completed"
    ERROR = "error"


class TaskComplexity(str, Enum):
    """Nivel de complejidad de la tarea"""
    SIMPLE = "simple"          # Una sola interacción
    MODERATE = "moderate"      # Múltiples pasos secuenciales
    COMPLEX = "complex"        # Requiere sub-agentes
    VERY_COMPLEX = "very_complex"  # Requiere orquestación avanzada


@dataclass
class AgentConfig:
    """Configuración del Lead Agent"""
    agent_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "OpenClaw Lead Agent"
    max_sub_agents: int = 5
    max_context_tokens: int = 128000
    max_iterations: int = 20
    checkpoint_enabled: bool = True
    memory_enabled: bool = True
    streaming_enabled: bool = True
    default_timeout: int = 300
    retry_attempts: int = 3
    parallel_execution: bool = True


@dataclass
class AgentState:
    """
    Estado del agente en un momento dado.
    
    Compatible con LangGraph para gestión de estados.
    """
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    thread_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    status: AgentStatus = AgentStatus.IDLE
    
    # Contexto actual
    current_task: Optional[str] = None
    task_complexity: TaskComplexity = TaskComplexity.SIMPLE
    obviousness_context: Optional[Dict[str, Any]] = None
    system_prompt: Optional[str] = None
    
    # Mensajes y razonamiento
    messages: List[Dict[str, Any]] = field(default_factory=list)
    reasoning_trace: List[Dict[str, Any]] = field(default_factory=list)
    
    # Sub-agentes
    active_sub_agents: List[str] = field(default_factory=list)
    sub_agent_results: Dict[str, Any] = field(default_factory=dict)
    
    # Ejecución
    current_step: int = 0
    total_steps: Optional[int] = None
    execution_plan: List[Dict[str, Any]] = field(default_factory=list)
    checkpoints: List[Dict[str, Any]] = field(default_factory=list)
    
    # Memoria
    relevant_memories: List[Dict[str, Any]] = field(default_factory=list)
    new_memories: List[Dict[str, Any]] = field(default_factory=list)
    
    # Herramientas
    available_tools: List[str] = field(default_factory=list)
    used_tools: List[str] = field(default_factory=list)
    pending_tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    
    # Resultado
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    
    # Metadatos
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    token_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el estado a diccionario para LangGraph"""
        return {
            "session_id": self.session_id,
            "thread_id": self.thread_id,
            "status": self.status.value,
            "current_task": self.current_task,
            "task_complexity": self.task_complexity.value,
            "obviousness_context": self.obviousness_context,
            "system_prompt": self.system_prompt,
            "messages": self.messages,
            "reasoning_trace": self.reasoning_trace,
            "active_sub_agents": self.active_sub_agents,
            "sub_agent_results": self.sub_agent_results,
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "execution_plan": self.execution_plan,
            "checkpoints": self.checkpoints,
            "relevant_memories": self.relevant_memories,
            "new_memories": self.new_memories,
            "available_tools": self.available_tools,
            "used_tools": self.used_tools,
            "pending_tool_calls": self.pending_tool_calls,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "token_count": self.token_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentState":
        """Crea estado desde diccionario"""
        state = cls(
            session_id=data.get("session_id", str(uuid.uuid4())),
            thread_id=data.get("thread_id", str(uuid.uuid4())[:8]),
        )
        
        for key, value in data.items():
            if hasattr(state, key):
                if key in ["status", "task_complexity"]:
                    setattr(state, key, {
                        "status": AgentStatus,
                        "task_complexity": TaskComplexity
                    }[key](value))
                elif key in ["created_at", "updated_at"]:
                    setattr(state, key, datetime.fromisoformat(value) if isinstance(value, str) else value)
                else:
                    setattr(state, key, value)
        
        return state


class LeadAgent:
    """
    Lead Agent - Coordinador Central de Super-Agentes.
    
    Actúa como el conductor central, utilizando una cadena de 9 middlewares
    para procesar cada turno de la conversación. Coordina sub-agentes
    jerárquicos que operan en paralelo en contextos aislados.
    
    Usage:
        agent = LeadAgent(AgentConfig())
        
        # Iniciar tarea compleja
        result = await agent.process({
            "objective": "Analizar mercado de semiconductores",
            "domain": "finance"
        })
        
        # Con streaming
        async for chunk in agent.process_stream(request):
            print(chunk)
    """
    
    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        middleware_chain: Optional[Any] = None
    ):
        """
        Inicializa el Lead Agent.
        
        Args:
            config: Configuración del agente
            middleware_chain: Cadena de middlewares (se crea si no se especifica)
        """
        self.config = config or AgentConfig()
        self.state = AgentState()
        self.middleware_chain = middleware_chain
        
        # Callbacks
        self._on_status_change: Optional[Callable] = None
        self._on_step_complete: Optional[Callable] = None
        self._on_error: Optional[Callable] = None
        
        # Sub-agentes
        self._sub_agents: Dict[str, Any] = {}
        
        # Métricas
        self._metrics = {
            "tasks_completed": 0,
            "tasks_failed": 0,
            "total_tokens": 0,
            "avg_execution_time_ms": 0
        }
    
    async def process(
        self,
        request: Dict[str, Any],
        obviousness_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Procesa una solicitud completa.
        
        Args:
            request: Solicitud con objetivo y parámetros
            obviousness_context: Contexto de obviedad pre-configurado
        
        Returns:
            Resultado de la ejecución
        """
        # Reset state
        self.state = AgentState()
        self.state.status = AgentStatus.PREPARING
        self.state.obviousness_context = obviousness_context
        self.state.current_task = request.get("objective")
        
        start_time = datetime.utcnow()
        
        try:
            # Fase 1: Preparación
            await self._update_status(AgentStatus.PREPARING)
            await self._prepare(request)
            
            # Fase 2: Alineación
            await self._update_status(AgentStatus.ALIGNING)
            alignment = await self._align()
            
            if not alignment.get("confirmed"):
                return {
                    "success": False,
                    "error": "Alineación fallida",
                    "alignment": alignment
                }
            
            # Fase 3: Análisis de complejidad
            complexity = await self._analyze_complexity()
            self.state.task_complexity = complexity
            
            # Fase 4: Planificación
            plan = await self._plan()
            self.state.execution_plan = plan
            self.state.total_steps = len(plan)
            
            # Fase 5: Ejecución
            await self._update_status(AgentStatus.EXECUTING)
            result = await self._execute_plan()
            
            # Fase 6: Finalización
            await self._update_status(AgentStatus.COMPLETED)
            self.state.result = result
            
            # Actualizar métricas
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            self._metrics["tasks_completed"] += 1
            self._metrics["avg_execution_time_ms"] = (
                (self._metrics["avg_execution_time_ms"] * (self._metrics["tasks_completed"] - 1) + execution_time)
                / self._metrics["tasks_completed"]
            )
            
            return {
                "success": True,
                "result": result,
                "execution_time_ms": execution_time,
                "steps": self.state.current_step,
                "complexity": complexity.value,
                "session_id": self.state.session_id
            }
            
        except Exception as e:
            await self._update_status(AgentStatus.ERROR)
            self.state.error = str(e)
            self._metrics["tasks_failed"] += 1
            
            if self._on_error:
                await self._on_error(e, self.state)
            
            return {
                "success": False,
                "error": str(e),
                "state": self.state.to_dict()
            }
    
    async def process_stream(
        self,
        request: Dict[str, Any],
        obviousness_context: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Procesa una solicitud con streaming de progreso.
        
        Yields chunks con el estado y progreso actual.
        """
        self.state = AgentState()
        self.state.obviousness_context = obviousness_context
        self.state.current_task = request.get("objective")
        
        try:
            # Yield inicial
            yield {
                "type": "status",
                "status": "preparing",
                "message": "Preparando contexto..."
            }
            
            # Preparación
            await self._prepare(request)
            yield {
                "type": "prepared",
                "system_prompt": self.state.system_prompt
            }
            
            # Alineación
            yield {
                "type": "status",
                "status": "aligning",
                "message": "Confirmando entendimiento..."
            }
            
            alignment = await self._align()
            yield {
                "type": "alignment",
                "confirmed": alignment.get("confirmed"),
                "understanding": alignment.get("understanding")
            }
            
            if not alignment.get("confirmed"):
                yield {
                    "type": "error",
                    "message": "Alineación no confirmada"
                }
                return
            
            # Análisis y planificación
            complexity = await self._analyze_complexity()
            plan = await self._plan()
            
            yield {
                "type": "plan",
                "complexity": complexity.value,
                "steps": len(plan),
                "plan": plan
            }
            
            # Ejecución paso a paso
            for i, step in enumerate(plan):
                self.state.current_step = i + 1
                
                yield {
                    "type": "step_start",
                    "step": i + 1,
                    "total": len(plan),
                    "description": step.get("description")
                }
                
                # Ejecutar paso
                step_result = await self._execute_step(step)
                
                yield {
                    "type": "step_complete",
                    "step": i + 1,
                    "result": step_result
                }
                
                # Agregar al razonamiento
                self.state.reasoning_trace.append({
                    "step": i + 1,
                    "action": step.get("action"),
                    "result": step_result,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            # Resultado final
            yield {
                "type": "complete",
                "result": self.state.result,
                "session_id": self.state.session_id
            }
            
        except Exception as e:
            yield {
                "type": "error",
                "message": str(e),
                "state": self.state.to_dict()
            }
    
    async def _prepare(self, request: Dict[str, Any]) -> None:
        """Fase de preparación"""
        self.state.updated_at = datetime.utcnow()
        
        # Construir system prompt si hay contexto
        if self.state.obviousness_context:
            from ...core.obviousness import ObviousnessContext
            context = ObviousnessContext(**self.state.obviousness_context)
            self.state.system_prompt = context.to_system_prompt()
        
        # Cargar herramientas disponibles
        self.state.available_tools = request.get("tools", [])
        
        # Cargar memorias relevantes
        if self.config.memory_enabled:
            await self._load_relevant_memories()
    
    async def _align(self) -> Dict[str, Any]:
        """Fase de alineación"""
        # En una implementación real, esto invocaría al LLM para confirmar
        # entendimiento. Por ahora, simulamos confirmación automática.
        
        return {
            "confirmed": True,
            "understanding": f"Entendido: {self.state.current_task}",
            "ambiguities": [],
            "improvements": []
        }
    
    async def _analyze_complexity(self) -> TaskComplexity:
        """Analiza la complejidad de la tarea"""
        task = self.state.current_task or ""
        
        # Heurística simple de complejidad
        complexity_indicators = {
            "research": 2,
            "analyze": 2,
            "generate": 1,
            "report": 2,
            "optimize": 3,
            "deploy": 3,
            "integrate": 3,
            "coordinate": 4
        }
        
        score = 0
        for indicator, points in complexity_indicators.items():
            if indicator in task.lower():
                score += points
        
        if score >= 8:
            return TaskComplexity.VERY_COMPLEX
        elif score >= 5:
            return TaskComplexity.COMPLEX
        elif score >= 3:
            return TaskComplexity.MODERATE
        else:
            return TaskComplexity.SIMPLE
    
    async def _plan(self) -> List[Dict[str, Any]]:
        """Genera plan de ejecución"""
        complexity = self.state.task_complexity
        
        if complexity == TaskComplexity.SIMPLE:
            return [
                {"step": 1, "action": "execute_direct", "description": "Ejecutar tarea directamente"}
            ]
        
        elif complexity == TaskComplexity.MODERATE:
            return [
                {"step": 1, "action": "gather_info", "description": "Recopilar información"},
                {"step": 2, "action": "process", "description": "Procesar datos"},
                {"step": 3, "action": "generate_output", "description": "Generar resultado"}
            ]
        
        elif complexity == TaskComplexity.COMPLEX:
            return [
                {"step": 1, "action": "decompose", "description": "Descomponer en subtareas"},
                {"step": 2, "action": "spawn_subagents", "description": "Crear sub-agentes"},
                {"step": 3, "action": "parallel_execute", "description": "Ejecutar en paralelo"},
                {"step": 4, "action": "synthesize", "description": "Sintetizar resultados"},
                {"step": 5, "action": "validate", "description": "Validar resultado final"}
            ]
        
        else:  # VERY_COMPLEX
            return [
                {"step": 1, "action": "analyze_requirements", "description": "Analizar requerimientos"},
                {"step": 2, "action": "create_plan", "description": "Crear plan detallado"},
                {"step": 3, "action": "spawn_specialized_agents", "description": "Crear agentes especializados"},
                {"step": 4, "action": "coordinate_execution", "description": "Coordinar ejecución"},
                {"step": 5, "action": "monitor_progress", "description": "Monitorear progreso"},
                {"step": 6, "action": "handle_errors", "description": "Manejar errores"},
                {"step": 7, "action": "synthesize_results", "description": "Sintetizar resultados"},
                {"step": 8, "action": "final_validation", "description": "Validación final"}
            ]
    
    async def _execute_plan(self) -> Dict[str, Any]:
        """Ejecuta el plan completo"""
        results = []
        
        for step in self.state.execution_plan:
            self.state.current_step += 1
            step_result = await self._execute_step(step)
            results.append(step_result)
            
            # Crear checkpoint si está habilitado
            if self.config.checkpoint_enabled:
                self.state.checkpoints.append({
                    "step": self.state.current_step,
                    "state": self.state.to_dict(),
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            if self._on_step_complete:
                await self._on_step_complete(self.state.current_step, step_result)
        
        return {
            "steps_completed": self.state.current_step,
            "results": results,
            "final_result": results[-1] if results else None
        }
    
    async def _execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta un paso individual"""
        action = step.get("action", "unknown")
        
        # Simulación de ejecución
        # En una implementación real, esto invocaría las herramientas y sub-agentes
        
        return {
            "action": action,
            "status": "completed",
            "output": f"Ejecutado: {action}",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _load_relevant_memories(self) -> None:
        """Carga memorias relevantes del Memory VCS"""
        # Placeholder - en implementación real, consultaría Memory VCS
        pass
    
    async def _update_status(self, status: AgentStatus) -> None:
        """Actualiza el estado del agente"""
        old_status = self.state.status
        self.state.status = status
        self.state.updated_at = datetime.utcnow()
        
        if self._on_status_change:
            await self._on_status_change(old_status, status, self.state)
    
    async def spawn_sub_agent(
        self,
        task: str,
        config: Optional[Dict[str, Any]] = None
    ) -> str:
        """Crea un sub-agente para una subtarea"""
        if len(self._sub_agents) >= self.config.max_sub_agents:
            raise RuntimeError(f"Máximo de sub-agentes alcanzado: {self.config.max_sub_agents}")
        
        sub_agent_id = str(uuid.uuid4())[:8]
        self._sub_agents[sub_agent_id] = {
            "task": task,
            "config": config,
            "status": "created"
        }
        
        self.state.active_sub_agents.append(sub_agent_id)
        
        return sub_agent_id
    
    async def get_sub_agent_result(self, sub_agent_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene resultado de un sub-agente"""
        return self.state.sub_agent_results.get(sub_agent_id)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas del agente"""
        return self._metrics.copy()
    
    def on_status_change(self, callback: Callable) -> None:
        """Registra callback para cambios de estado"""
        self._on_status_change = callback
    
    def on_step_complete(self, callback: Callable) -> None:
        """Registra callback para pasos completados"""
        self._on_step_complete = callback
    
    def on_error(self, callback: Callable) -> None:
        """Registra callback para errores"""
        self._on_error = callback
