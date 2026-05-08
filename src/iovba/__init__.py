"""
IOVBA - Infrastructure, Orchestration, Validation, Behavior, Action

IOVBA Groups: Grupos de agentes orientados a dominio
- Investigador: Investiga y analiza información
- Observador: Monitorea y detecta patrones
- Validador: Valida y verifica calidad
- Builder: Construye e implementa
- Asistente: Coordina y asiste

Capital Cognitivo: Sistema de memoria y aprendizaje automejorado
- Centralizado: Sincronización con servidor central
- Descentralizado: P2P entre agentes
- Híbrido: Combinación de ambos

HITL: Human In The Loop para aprobaciones
"""

from .groups import (
    IOVBAGroup,
    IOVBAGroupManager,
    IOVBARole,
    IOVBADomain,
    CapitalSyncMode,
    AgentProfile,
    CognitiveCapital,
    Engram,
    AgentStatus,
)

from .lead_assistant import (
    LeadAssistant,
    LeadAssistantConfig,
    HITLProposal,
    ProposalType,
    ApprovalStatus,
)

from .action.executor import ActionExecutor
from .action.skills_registry import SkillsRegistry
from .action.mcp_registry import MCPRegistry

from .behavior.persona import PersonaManager
from .behavior.ethics import EthicsEngine

from .validation.guardrail import GuardrailEngine
from .validation.policy_engine import PolicyEngine

from .orchestration.lead_agent import LeadAgentOrchestrator
from .orchestration.sub_agent import SubAgentCoordinator
from .orchestration.middleware import OrchestrationMiddleware

from .infrastructure.sandbox import SandboxEnvironment
from .infrastructure.openshell import OpenShellConnector

# Try to import LangGraph integration if available
try:
    from .langgraph_integration import (
        LangGraphIOVBA,
        LangGraphLeadAssistant,
        LangGraphConfig,
        AgentState,
        IOVBAState,
    )
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False

__all__ = [
    # Groups
    "IOVBAGroup",
    "IOVBAGroupManager",
    "IOVBARole",
    "IOVBADomain",
    "CapitalSyncMode",
    "AgentProfile",
    "CognitiveCapital",
    "Engram",
    "AgentStatus",
    
    # Lead Assistant
    "LeadAssistant",
    "LeadAssistantConfig",
    "HITLProposal",
    "ProposalType",
    "ApprovalStatus",
    
    # Action Layer
    "ActionExecutor",
    "SkillsRegistry",
    "MCPRegistry",
    
    # Behavior Layer
    "PersonaManager",
    "EthicsEngine",
    
    # Validation Layer
    "GuardrailEngine",
    "PolicyEngine",
    
    # Orchestration Layer
    "LeadAgentOrchestrator",
    "SubAgentCoordinator",
    "OrchestrationMiddleware",
    
    # Infrastructure Layer
    "SandboxEnvironment",
    "OpenShellConnector",
    
    # LangGraph (conditional)
    "LANGGRAPH_AVAILABLE",
]

if LANGGRAPH_AVAILABLE:
    __all__.extend([
        "LangGraphIOVBA",
        "LangGraphLeadAssistant",
        "LangGraphConfig",
        "AgentState",
        "IOVBAState",
    ])
