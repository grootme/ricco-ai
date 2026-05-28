"""
Gentle-Pi - Agent Orchestration DNA

El 4to DNA del sistema RICCO AI, responsable de:
- Gestión de personas del agente
- Delegación de tareas entre agentes
- Coordinación de workflows
- Asignación de modelos

Gentle-Pi actúa como el orquestador que conecta los otros 3 DNA:
- DeerFlow: Ejecuta los workflows delegados
- Gentle-AI: Aplica comportamiento ético a las delegaciones
- Engram: Almacena y recupera contexto de tareas
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import logging
import asyncio

logger = logging.getLogger(__name__)


# ============================================
# ENUMS AND TYPES
# ============================================

class PersonaType(str, Enum):
    """Tipos de persona del orquestador"""
    GENTLEMAN = "gentleman"  # Colaborativo, empático, detallado
    NEUTRAL = "neutral"      # Directo, eficiente, conciso
    EXPERT = "expert"        # Técnico, profundo, especializado


class AgentType(str, Enum):
    """Tipos de agentes disponibles para delegación"""
    SCOUT = "scout"                    # Exploración y recopilación
    WORKER = "worker"                  # Implementación y ejecución
    REVIEWER = "reviewer"              # Revisión y validación
    CONTEXT_BUILDER = "context_builder"  # Construcción de contexto
    ANALYZER = "analyzer"              # Análisis y procesamiento


class TaskPriority(str, Enum):
    """Prioridad de tareas"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(str, Enum):
    """Estado de tareas delegadas"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ThinkingLevel(str, Enum):
    """Nivel de razonamiento del modelo"""
    LOW = "low"        # Respuestas rápidas
    MEDIUM = "medium"  # Balance velocidad/calidad
    HIGH = "high"      # Máxima calidad, más lento


# ============================================
# DATA CLASSES
# ============================================

@dataclass
class DelegationRequest:
    """Solicitud de delegación de tarea"""
    task_description: str
    agent_type: AgentType
    priority: TaskPriority = TaskPriority.NORMAL
    timeout_minutes: int = 30
    context: Optional[Dict[str, Any]] = None
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_description": self.task_description,
            "agent_type": self.agent_type.value,
            "priority": self.priority.value,
            "timeout_minutes": self.timeout_minutes,
            "context": self.context,
            "dependencies": self.dependencies,
            "metadata": self.metadata
        }


@dataclass
class DelegationResult:
    """Resultado de una delegación"""
    task_id: str
    status: TaskStatus
    agent_type: AgentType
    result: Optional[Any] = None
    error: Optional[str] = None
    duration_seconds: float = 0.0
    tokens_used: int = 0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "agent_type": self.agent_type.value,
            "result": self.result,
            "error": self.error,
            "duration_seconds": self.duration_seconds,
            "tokens_used": self.tokens_used,
            "timestamp": self.timestamp
        }


@dataclass
class ModelAssignment:
    """Asignación de modelo para un agente"""
    agent_name: str
    model: str
    thinking: ThinkingLevel = ThinkingLevel.MEDIUM
    max_tokens: int = 4096
    temperature: float = 0.7
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "model": self.model,
            "thinking": self.thinking.value,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature
        }


@dataclass
class DelegationTrigger:
    """Trigger de delegación automática"""
    agent_type: AgentType
    condition: Callable[[Dict[str, Any]], bool]
    priority: TaskPriority = TaskPriority.NORMAL
    description: str = ""


# ============================================
# DEFAULT TRIGGERS
# ============================================

DEFAULT_TRIGGERS: List[DelegationTrigger] = [
    DelegationTrigger(
        agent_type=AgentType.SCOUT,
        condition=lambda ctx: ctx.get("files_read", 0) > 5,
        priority=TaskPriority.NORMAL,
        description="Más de 5 archivos para leer"
    ),
    DelegationTrigger(
        agent_type=AgentType.WORKER,
        condition=lambda ctx: ctx.get("files_to_write", 0) > 3,
        priority=TaskPriority.HIGH,
        description="Más de 3 archivos para modificar"
    ),
    DelegationTrigger(
        agent_type=AgentType.REVIEWER,
        condition=lambda ctx: (
            ctx.get("session_length") == "long" and 
            ctx.get("recent_commits", 0) > 3
        ),
        priority=TaskPriority.HIGH,
        description="Sesión larga con varios commits"
    ),
    DelegationTrigger(
        agent_type=AgentType.CONTEXT_BUILDER,
        condition=lambda ctx: ctx.get("context_missing", False),
        priority=TaskPriority.NORMAL,
        description="Falta contexto para la tarea"
    ),
    DelegationTrigger(
        agent_type=AgentType.ANALYZER,
        condition=lambda ctx: ctx.get("data_size", 0) > 10000,
        priority=TaskPriority.NORMAL,
        description="Grandes volúmenes de datos a analizar"
    ),
]


# ============================================
# GENTLE-PI ORCHESTRATOR
# ============================================

class GentlePiOrchestrator:
    """
    Orquestador de agentes Gentle-Pi.
    
    Implementa el 4to DNA para coordinación de agentes.
    
    Capacidades:
    - Gestión de personas (gentleman/neutral/expert)
    - Delegación inteligente de tareas
    - Asignación de modelos
    - Detección de triggers automáticos
    - Coordinación con otros DNA
    
    Example:
        orchestrator = GentlePiOrchestrator()
        
        # Configurar persona
        orchestrator.set_persona(PersonaType.GENTLEMAN)
        
        # Delegar tarea
        result = await orchestrator.delegate(DelegationRequest(
            task_description="Analizar el módulo de autenticación",
            agent_type=AgentType.SCOUT
        ))
        
        # Verificar triggers
        triggers = orchestrator.check_triggers({
            "files_read": 10,
            "files_to_write": 5
        })
    """
    
    def __init__(
        self,
        persona: PersonaType = PersonaType.GENTLEMAN,
        triggers: Optional[List[DelegationTrigger]] = None
    ):
        self._persona = persona
        self._triggers = triggers or DEFAULT_TRIGGERS
        self._model_assignments: Dict[str, ModelAssignment] = {}
        self._active_tasks: Dict[str, DelegationResult] = {}
        self._task_history: List[DelegationResult] = []
        
        # Agentes disponibles (inicialmente vacío)
        self._agents: Dict[AgentType, List[Any]] = {t: [] for t in AgentType}
        
        # Integraciones con otros DNA (opcional)
        self._deerflow = None  # Workflow engine
        self._gentle_ai = None  # Behavior engine
        self._engram = None  # Memory store
        
        logger.info(f"Gentle-Pi Orchestrator initialized with persona: {persona.value}")
    
    # ============================================
    # PERSONA MANAGEMENT
    # ============================================
    
    def set_persona(self, persona: PersonaType) -> None:
        """Establece la persona del orquestador"""
        self._persona = persona
        logger.info(f"Persona changed to: {persona.value}")
    
    def get_persona(self) -> PersonaType:
        """Obtiene la persona actual"""
        return self._persona
    
    def get_persona_config(self) -> Dict[str, Any]:
        """Obtiene la configuración de la persona actual"""
        configs = {
            PersonaType.GENTLEMAN: {
                "style": "collaborative",
                "tone": "warm",
                "detail_level": "high",
                "proactive": True,
                "explanation_style": "thorough",
                "greeting": "¡Hola! Estoy aquí para ayudarte de la mejor manera posible."
            },
            PersonaType.NEUTRAL: {
                "style": "direct",
                "tone": "professional",
                "detail_level": "medium",
                "proactive": False,
                "explanation_style": "concise",
                "greeting": "¿En qué puedo ayudarte?"
            },
            PersonaType.EXPERT: {
                "style": "technical",
                "tone": "precise",
                "detail_level": "very_high",
                "proactive": True,
                "explanation_style": "detailed",
                "greeting": "Estoy listo para asistirte con tareas técnicas complejas."
            }
        }
        return configs.get(self._persona, configs[PersonaType.GENTLEMAN])
    
    # ============================================
    # MODEL ASSIGNMENT
    # ============================================
    
    def configure_model(
        self,
        agent_name: str,
        model: str,
        thinking: ThinkingLevel = ThinkingLevel.MEDIUM,
        **kwargs
    ) -> ModelAssignment:
        """Configura el modelo para un agente específico"""
        assignment = ModelAssignment(
            agent_name=agent_name,
            model=model,
            thinking=thinking,
            max_tokens=kwargs.get("max_tokens", 4096),
            temperature=kwargs.get("temperature", 0.7)
        )
        self._model_assignments[agent_name] = assignment
        logger.info(f"Model configured for {agent_name}: {model} (thinking: {thinking.value})")
        return assignment
    
    def get_model_assignment(self, agent_name: str) -> Optional[ModelAssignment]:
        """Obtiene la asignación de modelo para un agente"""
        return self._model_assignments.get(agent_name)
    
    def get_model_for_thinking(self, thinking: ThinkingLevel) -> str:
        """Obtiene el modelo recomendado para un nivel de razonamiento"""
        model_map = {
            ThinkingLevel.LOW: "meta-llama/llama-3.1-8b-instruct",
            ThinkingLevel.MEDIUM: "anthropic/claude-3.5-sonnet",
            ThinkingLevel.HIGH: "anthropic/claude-3.5-sonnet"
        }
        return model_map.get(thinking, model_map[ThinkingLevel.MEDIUM])
    
    # ============================================
    # DELEGATION
    # ============================================
    
    async def delegate(self, request: DelegationRequest) -> DelegationResult:
        """
        Delega una tarea al agente apropiado.
        
        El proceso de delegación:
        1. Validar la solicitud
        2. Seleccionar agente disponible
        3. Aplicar comportamiento (Gentle-AI)
        4. Ejecutar tarea (DeerFlow)
        5. Almacenar resultado (Engram)
        
        Args:
            request: Solicitud de delegación
        
        Returns:
            Resultado de la delegación
        """
        task_id = str(uuid.uuid4())[:8]
        start_time = datetime.utcnow()
        
        logger.info(f"Delegating task {task_id} to {request.agent_type.value}")
        
        # Verificar agentes disponibles
        agents = self._agents.get(request.agent_type, [])
        if not agents:
            # Crear resultado simulado si no hay agentes reales
            result = DelegationResult(
                task_id=task_id,
                status=TaskStatus.COMPLETED,
                agent_type=request.agent_type,
                result={
                    "message": f"Task '{request.task_description[:50]}...' acknowledged",
                    "note": "No real agent available - simulation mode"
                }
            )
        else:
            # Ejecutar con agente real
            try:
                agent = agents[0]  # Seleccionar primer agente disponible
                
                # Aplicar comportamiento si está disponible
                if self._gentle_ai:
                    behavior_result = self._gentle_ai.evaluate({
                        "content": request.task_description,
                        "agent_type": request.agent_type.value
                    })
                    if behavior_result.get("actions"):
                        logger.info(f"Behavior applied: {behavior_result['actions']}")
                
                # Ejecutar tarea
                agent_result = await agent.execute(request.to_dict())
                
                result = DelegationResult(
                    task_id=task_id,
                    status=TaskStatus.COMPLETED,
                    agent_type=request.agent_type,
                    result=agent_result
                )
                
            except Exception as e:
                result = DelegationResult(
                    task_id=task_id,
                    status=TaskStatus.FAILED,
                    agent_type=request.agent_type,
                    error=str(e)
                )
        
        # Calcular duración
        result.duration_seconds = (datetime.utcnow() - start_time).total_seconds()
        
        # Almacenar en historial
        self._active_tasks[task_id] = result
        self._task_history.append(result)
        
        # Almacenar en memoria si está disponible
        if self._engram:
            try:
                self._engram.store_interaction(
                    agent_id="gentle-pi",
                    interaction_type="delegation",
                    content=f"Task: {request.task_description[:100]}... Result: {result.status.value}"
                )
            except Exception as e:
                logger.warning(f"Could not store in engram: {e}")
        
        return result
    
    def check_triggers(self, context: Dict[str, Any]) -> List[AgentType]:
        """
        Verifica qué triggers de delegación se activan.
        
        Args:
            context: Contexto actual con métricas
        
        Returns:
            Lista de tipos de agentes recomendados
        """
        triggered = []
        
        for trigger in self._triggers:
            try:
                if trigger.condition(context):
                    triggered.append(trigger.agent_type)
                    logger.info(
                        f"Trigger activated: {trigger.agent_type.value} - {trigger.description}"
                    )
            except Exception as e:
                logger.warning(f"Trigger evaluation failed: {e}")
        
        return triggered
    
    def get_task_status(self, task_id: str) -> Optional[DelegationResult]:
        """Obtiene el estado de una tarea"""
        return self._active_tasks.get(task_id)
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancela una tarea activa"""
        if task_id in self._active_tasks:
            self._active_tasks[task_id].status = TaskStatus.CANCELLED
            return True
        return False
    
    # ============================================
    # WORKLOAD FORECASTING
    # ============================================
    
    def forecast_review_workload(
        self,
        estimated_lines_added: int,
        estimated_lines_deleted: int,
        files_changed: int
    ) -> Dict[str, Any]:
        """
        Predice la carga de trabajo de revisión.
        
        Args:
            estimated_lines_added: Líneas a añadir
            estimated_lines_deleted: Líneas a eliminar
            files_changed: Archivos afectados
        
        Returns:
            Predicción de complejidad y tiempo
        """
        complexity_score = (
            estimated_lines_added * 1.0 +
            estimated_lines_deleted * 0.5 +
            files_changed * 10
        )
        
        if complexity_score < 200:
            risk_level = "low"
            estimated_hours = 0.5
        elif complexity_score < 500:
            risk_level = "medium"
            estimated_hours = 1.5
        else:
            risk_level = "high"
            estimated_hours = 3.0 + (complexity_score - 500) * 0.005
        
        return {
            "complexity_score": complexity_score,
            "risk_level": risk_level,
            "estimated_review_hours": estimated_hours,
            "recommended_reviewers": 1 if risk_level == "low" else 2,
            "should_delegate": complexity_score > 300
        }
    
    # ============================================
    # DNA INTEGRATION
    # ============================================
    
    def integrate_deerflow(self, deerflow_engine: Any) -> None:
        """Integra con DeerFlow para ejecución de workflows"""
        self._deerflow = deerflow_engine
        logger.info("DeerFlow integration enabled")
    
    def integrate_gentle_ai(self, behavior_engine: Any) -> None:
        """Integra con Gentle-AI para comportamiento ético"""
        self._gentle_ai = behavior_engine
        logger.info("Gentle-AI integration enabled")
    
    def integrate_engram(self, memory_store: Any) -> None:
        """Integra con Engram para persistencia"""
        self._engram = memory_store
        logger.info("Engram integration enabled")
    
    # ============================================
    # STATUS AND METRICS
    # ============================================
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado del orquestador"""
        return {
            "dna": "Gentle-Pi",
            "version": "1.0.0",
            "persona": self._persona.value,
            "active_tasks": len(self._active_tasks),
            "total_delegations": len(self._task_history),
            "integrations": {
                "deerflow": self._deerflow is not None,
                "gentle_ai": self._gentle_ai is not None,
                "engram": self._engram is not None
            },
            "agents_registered": sum(len(agents) for agents in self._agents.values())
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas de delegación"""
        if not self._task_history:
            return {"total_tasks": 0}
        
        completed = [t for t in self._task_history if t.status == TaskStatus.COMPLETED]
        failed = [t for t in self._task_history if t.status == TaskStatus.FAILED]
        
        avg_duration = (
            sum(t.duration_seconds for t in completed) / len(completed)
            if completed else 0
        )
        
        return {
            "total_tasks": len(self._task_history),
            "completed": len(completed),
            "failed": len(failed),
            "success_rate": len(completed) / len(self._task_history) if self._task_history else 0,
            "average_duration_seconds": avg_duration,
            "by_agent_type": {
                agent.value: len([t for t in self._task_history if t.agent_type == agent])
                for agent in AgentType
            }
        }


# ============================================
# CONVENIENCE FUNCTIONS
# ============================================

_orchestrator_instance: Optional[GentlePiOrchestrator] = None


def get_orchestrator(persona: PersonaType = PersonaType.GENTLEMAN) -> GentlePiOrchestrator:
    """Obtiene o crea la instancia del orquestador"""
    global _orchestrator_instance
    
    if _orchestrator_instance is None:
        _orchestrator_instance = GentlePiOrchestrator(persona=persona)
    
    return _orchestrator_instance


def reset_orchestrator() -> None:
    """Reinicia el orquestador"""
    global _orchestrator_instance
    _orchestrator_instance = None
