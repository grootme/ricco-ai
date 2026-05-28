"""
RICCO AI - Plataforma de Agentes Cognitivos

Integración de los tres pilares del sistema de agentes:

1. DeerFlow - Motor de Workflows
   - Orquestación de flujos de trabajo
   - Nodos de acción, decisión, paralelismo
   - Integración con agentes

2. Gentle-AI - Sistema de Comportamiento
   - Personalidades adaptables
   - Comportamiento ético
   - Adaptación contextual

3. Engram - Sistema de Memoria
   - Memoria persistente con versionado
   - Búsqueda semántica (FTS5)
   - Grafo de conocimiento

Uso integrado:
    from ricco_ai import DeerFlow, GentleAI, Engram
    
    # Crear workflow
    workflow = DeerFlow.Workflow(name="daily_report")
    
    # Configurar personalidad
    persona = GentleAI.Persona(GentleAI.PersonaConfig(
        persona_type=GentleAI.PersonaType.ASSISTANT
    ))
    
    # Almacenar en memoria
    memory = Engram.MemoryVCS()
    memory.upsert("project:status", "Active development")
"""

__version__ = "0.1.0"
__author__ = "RICCO AI Team"

# Importar submódulos
from . import deerflow
from . import gentle_ai
from . import engram

# Exportar clases principales
from .deerflow import (
    WorkflowEngine,
    Workflow,
    Node,
    Edge,
    ActionNode,
    DecisionNode,
    ParallelNode,
    AgentNode,
    ExecutionContext,
    ExecutionResult,
)

from .gentle_ai import (
    Persona,
    PersonaConfig,
    PersonaType,
    CommunicationStyle,
    ToneLevel,
    BehaviorEngine,
    EthicsPolicy,
    ResponseAdapter,
    AdaptiveContext,
)

from .engram import (
    MemoryVCS,
    MemoryEntry,
    MemoryVersion,
    DisclosureLevel,
    EngramStore,
    EngramQuery,
    MemoryIndex,
    IndexConfig,
)

__all__ = [
    # DeerFlow
    "DeerFlow",
    "WorkflowEngine",
    "Workflow",
    "Node",
    "Edge",
    "ActionNode",
    "DecisionNode",
    "ParallelNode",
    "AgentNode",
    "ExecutionContext",
    "ExecutionResult",
    
    # Gentle-AI
    "GentleAI",
    "Persona",
    "PersonaConfig",
    "PersonaType",
    "CommunicationStyle",
    "ToneLevel",
    "BehaviorEngine",
    "EthicsPolicy",
    "ResponseAdapter",
    "AdaptiveContext",
    
    # Engram
    "Engram",
    "MemoryVCS",
    "MemoryEntry",
    "MemoryVersion",
    "DisclosureLevel",
    "EngramStore",
    "EngramQuery",
    "MemoryIndex",
    "IndexConfig",
]

# Namespace aliases para acceso conveniente
class DeerFlow:
    """Namespace para DeerFlow - Motor de Workflows"""
    WorkflowEngine = WorkflowEngine
    Workflow = Workflow
    Node = Node
    Edge = Edge
    ActionNode = ActionNode
    DecisionNode = DecisionNode
    ParallelNode = ParallelNode
    AgentNode = AgentNode


class GentleAI:
    """Namespace para Gentle-AI - Sistema de Comportamiento"""
    Persona = Persona
    PersonaConfig = PersonaConfig
    PersonaType = PersonaType
    CommunicationStyle = CommunicationStyle
    ToneLevel = ToneLevel
    BehaviorEngine = BehaviorEngine
    EthicsPolicy = EthicsPolicy
    ResponseAdapter = ResponseAdapter
    AdaptiveContext = AdaptiveContext


class Engram:
    """Namespace para Engram - Sistema de Memoria"""
    MemoryVCS = MemoryVCS
    MemoryEntry = MemoryEntry
    MemoryVersion = MemoryVersion
    DisclosureLevel = DisclosureLevel
    EngramStore = EngramStore
    EngramQuery = EngramQuery
    MemoryIndex = MemoryIndex
    IndexConfig = IndexConfig
