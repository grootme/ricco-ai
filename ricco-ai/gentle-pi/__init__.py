"""
Gentle-Pi - Agent Orchestration DNA

El 4to DNA del sistema RICCO AI.

Gentle-Pi es responsable de:
- Gestión de personas del agente (gentleman, neutral, expert)
- Delegación de tareas entre agentes especializados
- Coordinación de workflows multi-agente
- Asignación inteligente de modelos
- Detección de triggers de delegación automática
"""

from .orchestrator import (
    # Core
    GentlePiOrchestrator,
    get_orchestrator,
    reset_orchestrator,
    
    # Enums
    PersonaType,
    AgentType,
    TaskPriority,
    TaskStatus,
    ThinkingLevel,
    
    # Data Classes
    DelegationRequest,
    DelegationResult,
    ModelAssignment,
    DelegationTrigger,
    
    # Constants
    DEFAULT_TRIGGERS,
)

__all__ = [
    # Core
    "GentlePiOrchestrator",
    "get_orchestrator",
    "reset_orchestrator",
    
    # Enums
    "PersonaType",
    "AgentType",
    "TaskPriority",
    "TaskStatus",
    "ThinkingLevel",
    
    # Data Classes
    "DelegationRequest",
    "DelegationResult",
    "ModelAssignment",
    "DelegationTrigger",
    
    # Constants
    "DEFAULT_TRIGGERS",
]

__version__ = "1.0.0"
