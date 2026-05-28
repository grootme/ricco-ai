"""
Modelos de datos core del Super Asistente.
Define las estructuras de estado, mensajes y agentes.
"""

from typing import (
    Any, Dict, List, Optional, Union, Callable, 
    TypeVar, Generic, Annotated, Sequence
)
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
import operator
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage


# =============================================================================
# ENUMS Y TIPOS
# =============================================================================

class AgentRole(str, Enum):
    """Roles de agentes en el sistema."""
    LEAD = "lead"
    RESEARCHER = "researcher"
    ANALYZER = "analyzer"
    BUILDER = "builder"
    VALIDATOR = "validator"
    MEMORY_KEEPER = "memory_keeper"
    SECURITY_GUARD = "security_guard"


class TaskStatus(str, Enum):
    """Estados de una tarea."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    AWAITING_HUMAN = "awaiting_human"


class MemoryType(str, Enum):
    """Tipos de memoria soportados."""
    SESSION = "session"           # Memoria de sesión actual
    EPISODIC = "episodic"         # Eventos y experiencias
    SEMANTIC = "semantic"         # Hechos y conocimiento
    PROCEDURAL = "procedural"     # Habilidades y procedimientos
    DECLARATIVE = "declarative"   # Información explícita
    PREFERENCE = "preference"     # Preferencias del usuario


class MessageType(str, Enum):
    """Tipos de mensajes entre agentes."""
    TASK = "task"
    RESULT = "result"
    QUERY = "query"
    RESPONSE = "response"
    HANDOFF = "handoff"
    ERROR = "error"
    APPROVAL_REQUEST = "approval_request"
    APPROVAL_RESPONSE = "approval_response"


class ToolResultStatus(str, Enum):
    """Estados de resultado de herramienta."""
    SUCCESS = "success"
    FAILURE = "failure"
    PENDING_APPROVAL = "pending_approval"
    REJECTED = "rejected"


# =============================================================================
# MODELOS DE MEMORIA
# =============================================================================

class MemoryItem(BaseModel):
    """Un item de memoria individual."""
    id: Optional[str] = None
    content: str
    memory_type: MemoryType = MemoryType.SEMANTIC
    user_id: Optional[str] = None
    agent_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    score: Optional[float] = None
    hash: Optional[str] = None
    
    model_config = ConfigDict(use_enum_values=True)


class MemorySearchResult(BaseModel):
    """Resultado de búsqueda en memoria."""
    items: List[MemoryItem]
    total_count: int
    query: str
    filters: Dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# MODELOS DE TAREAS
# =============================================================================

class Task(BaseModel):
    """Representa una tarea a ejecutar."""
    id: str
    description: str
    assigned_agent: Optional[AgentRole] = None
    status: TaskStatus = TaskStatus.PENDING
    priority: int = Field(default=5, ge=1, le=10)
    
    # Dependencias
    dependencies: List[str] = Field(default_factory=list)
    
    # Resultados
    result: Optional[str] = None
    error: Optional[str] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Contexto adicional
    context: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(use_enum_values=True)


class TaskPlan(BaseModel):
    """Plan de tareas generado por el Lead Agent."""
    tasks: List[Task]
    reasoning: str
    estimated_steps: int
    parallel_tasks: List[List[str]] = Field(default_factory=list)


# =============================================================================
# MODELOS DE HERRAMIENTAS
# =============================================================================

class ToolDefinition(BaseModel):
    """Definición de una herramienta."""
    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema
    required_permissions: List[str] = Field(default_factory=list)
    requires_approval: bool = False
    category: str = "general"


class ToolCall(BaseModel):
    """Llamada a una herramienta."""
    id: str
    name: str
    arguments: Dict[str, Any]
    requested_by: AgentRole
    requires_approval: bool = False


class ToolResult(BaseModel):
    """Resultado de ejecutar una herramienta."""
    call_id: str
    status: ToolResultStatus
    output: Optional[str] = None
    error: Optional[str] = None
    execution_time_ms: Optional[int] = None
    approved_by: Optional[str] = None  # Human approver


# =============================================================================
# MODELOS DE AGENTE
# =============================================================================

class AgentIdentity(BaseModel):
    """Identidad de un agente (inspirado en CrewAI)."""
    name: str
    role: str
    goal: str
    backstory: str
    capabilities: List[str] = Field(default_factory=list)


class AgentState(BaseModel):
    """Estado interno de un agente."""
    agent_id: str
    identity: AgentIdentity
    current_task: Optional[Task] = None
    completed_tasks: List[str] = Field(default_factory=list)
    memory_ids: List[str] = Field(default_factory=list)
    tools_available: List[str] = Field(default_factory=list)
    is_active: bool = True
    last_activity: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# ESTADO COMPARTIDO (LangGraph State)
# =============================================================================

def merge_dicts(left: Dict[str, Any], right: Dict[str, Any]) -> Dict[str, Any]:
    """Función para mergear diccionarios en el estado."""
    return {**left, **right}


def append_messages(left: List[BaseMessage], right: List[BaseMessage]) -> List[BaseMessage]:
    """Función para agregar mensajes con deduplicación por ID."""
    left_ids = {msg.id for msg in left if hasattr(msg, 'id') and msg.id}
    return left + [msg for msg in right if not hasattr(msg, 'id') or msg.id not in left_ids]


class SuperAssistantState(BaseModel):
    """
    Estado principal del Super Asistente para LangGraph.
    Este es el estado que fluye entre todos los nodos del grafo.
    """
    # Mensajes de la conversación
    messages: Annotated[List[Dict[str, Any]], Field(default_factory=list)]
    
    # Usuario y sesión
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    # Tarea actual
    current_task: Optional[Dict[str, Any]] = None
    task_plan: Optional[Dict[str, Any]] = None
    
    # Resultados de subagentes
    subagent_results: Dict[str, Any] = Field(default_factory=dict)
    
    # Herramientas pendientes
    pending_tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    tool_results: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    # Memoria
    retrieved_memories: List[Dict[str, Any]] = Field(default_factory=list)
    new_memories: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Estado de control
    current_agent: Optional[str] = None
    next_agent: Optional[str] = None
    should_continue: bool = True
    awaiting_human: bool = False
    human_input_request: Optional[Dict[str, Any]] = None
    
    # Metadatos
    iteration_count: int = 0
    max_iterations: int = 20
    start_time: Optional[str] = None
    last_update: Optional[str] = None
    
    # Artefactos (outputs de agentes)
    artifacts: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(
        use_enum_values=True,
        arbitrary_types_allowed=True
    )


# =============================================================================
# EVENTOS Y SEÑALES
# =============================================================================

class AgentEvent(BaseModel):
    """Evento emitido por un agente."""
    event_type: str
    agent_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = Field(default_factory=dict)


class HandoffMessage(BaseModel):
    """Mensaje de traspaso entre agentes."""
    from_agent: AgentRole
    to_agent: AgentRole
    context: List[Dict[str, Any]]
    task: Task
    reason: str


class HumanApprovalRequest(BaseModel):
    """Solicitud de aprobación humana."""
    request_id: str
    tool_call: ToolCall
    reason: str
    options: List[str] = Field(default_factory=lambda: ["approve", "reject", "modify"])
    timeout_seconds: int = 300
    created_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# RESULTADO FINAL
# =============================================================================

class SuperAssistantResponse(BaseModel):
    """Respuesta final del Super Asistente."""
    content: str
    agent_contributions: Dict[str, str] = Field(default_factory=dict)
    tools_used: List[str] = Field(default_factory=list)
    memories_created: int = 0
    execution_time_ms: int = 0
    iterations: int = 0
    success: bool = True
    error: Optional[str] = None
    artifacts: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(use_enum_values=True)


# =============================================================================
# TIPOS GENÉRICOS
# =============================================================================

T = TypeVar('T')

class Result(BaseModel, Generic[T]):
    """Resultado genérico de una operación."""
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
