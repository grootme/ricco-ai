# Super Asistente con Capital Cognitivo - Extended Version
# Incluye: RAG Ontológico, Capital Cognitivo, MCP, Patrones GOF, Agentes SWE

from typing import Any, Dict, List, Optional

# Version
__version__ = "2.0.0"
__author__ = "Super Assistant Team"

# =============================================================================
# CORE MODULES (Previous)
# =============================================================================

from .config.settings import (
    Settings, get_settings, LLMConfig, MemoryConfig,
    GuardrailsConfig, HITLConfig, OrchestrationConfig, SubagentConfig
)

from .core.models import (
    AgentRole, TaskStatus, MemoryType, Task, TaskPlan,
    ToolDefinition, ToolCall, ToolResult, AgentIdentity,
    SuperAssistantState, SuperAssistantResponse
)

from .memory.memory_system import (
    MemoryStore, InMemoryStore, MultiTypeMemorySystem,
    MemoryManager, create_memory_system
)

from .orchestration.graph import (
    SuperAssistantOrchestrator, create_orchestrator
)

from .agents.base import (
    BaseAgent, LeadAgent, ResearcherAgent, AnalyzerAgent,
    BuilderAgent, ValidatorAgent, create_agent, create_agent_team
)

from .security.guardrails import (
    GuardrailsManager, create_default_guardrails,
    JailbreakDetectionRail, ContentSafetyRail, SensitiveDataMaskingRail
)

from .skills.registry import (
    BaseSkill, SkillRegistry, SkillResult, create_skill_registry_with_defaults
)

from .hitl.hitl_system import (
    HITLManager, create_hitl_manager, ApprovalRequest, ApprovalResponse
)

# =============================================================================
# KNOWLEDGE GRAPH - RAG Ontológico
# =============================================================================

from .knowledge_graph.ontological_rag import (
    # Enums
    EntityType, RelationType,
    # Models
    Entity, Relationship, Community, Triple, NodeProperty,
    # Patterns
    EntityFactory, ExtractionStrategy, LLMExtractionStrategy,
    NLPExtractionStrategy, HybridExtractionStrategy,
    GraphEventType, GraphEvent, GraphObserver, LoggingObserver,
    GraphCommand, AddEntityCommand, AddRelationshipCommand, BatchCommand,
    GraphQueryBuilder,
    # Main Classes
    KnowledgeGraph, CognitiveKnowledgeBase, GlobalKnowledgeBase
)

# =============================================================================
# COGNITIVE CAPITAL
# =============================================================================

from .cognitive_capital.manager import (
    # Enums
    CognitiveAssetType,
    # Models
    CognitiveValue, CognitiveAsset,
    # Patterns
    CognitiveAssetPrototype,
    CognitiveIterator, ByTypeIterator, ByValueIterator,
    CognitiveVisitor, ExportVisitor, DecayVisitor,
    AssetDecorator, EmbeddingDecorator, ProvenanceDecorator,
    LearningHandler, KnowledgeExtractionHandler, SkillExtractionHandler,
    # Main Classes
    CognitiveCapitalStore, CognitiveCapitalManager
)

# =============================================================================
# MCP INTEGRATION
# =============================================================================

from .mcp.integration import (
    # Enums
    MCPTransportType, MCPToolAnnotation,
    # Models
    MCPToolSchema, MCPToolResult, MCPServerConfig,
    # Adapters
    MCPTransportAdapter, StdioTransportAdapter, HTTPTransportAdapter,
    # Patterns
    MCPProxy, MCPClientFacade, MCPSkillBridge,
    # Built-in Skills
    BuiltinMCPSkills
)

# =============================================================================
# GOF PATTERNS
# =============================================================================

from .patterns.gof_patterns import (
    # Creational
    AgentComponentFactory, ResearcherAgentFactory, BuilderAgentFactory,
    AgentBuilder, AgentCreator, AgentPrototype, AgentRegistry,
    # Structural
    ToolAdapter, LangChainToolAdapter, MCPToolAdapter,
    LLMInterface, OpenAIImplementation, AnthropicImplementation,
    TaskComponent, SimpleTask, CompositeTask,
    AgentDecorator, LoggingDecorator, CachingDecorator, RetryDecorator,
    AgentOrchestratorFacade,
    # Behavioral
    RequestHandler, SecurityHandler, ValidationHandler, ProcessingHandler,
    Command, CreateAgentCommand, CommandInvoker,
    Observer, Subject, Event, LoggingObserver as PatternLoggingObserver,
    ExecutionStrategy, SequentialStrategy, ParallelStrategy, PriorityStrategy,
    AgentTemplate,
    AgentState, IdleState, ProcessingState, WaitingForInputState,
    # Additional
    NullAgent, Specification, AndSpecification, OrSpecification
)

# =============================================================================
# SWE AGENTS with CoT
# =============================================================================

from .swe_agents.cot_agents import (
    # CoT
    ThoughtType, Thought, ThoughtChain,
    # ToT
    ThoughtNode, TreeOfThought,
    # Self-Refine
    RefinementIteration, SelfRefine,
    # ReAct
    ActionType, ReActStep, ReActExecutor,
    # Agents
    SWEAgentRole, CodeContext, SWEAgentOutput, BaseSWEAgent,
    CodeAnalyzerAgent, CodePlannerAgent, CodeBuilderAgent, CodeTesterAgent,
    SWEAgentTeam
)

# =============================================================================
# SUPER ASSISTANT EXTENDED
# =============================================================================

class SuperAssistantV2:
    """
    Super Asistente versión 2.0 con:
    - RAG Ontológico con Knowledge Graph
    - Capital Cognitivo acumulativo
    - Integración MCP
    - Agentes SWE con CoT
    - Patrones GOF
    """
    
    def __init__(
        self,
        enable_knowledge_graph: bool = True,
        enable_cognitive_capital: bool = True,
        enable_mcp: bool = True,
        enable_swe_agents: bool = True
    ):
        # Knowledge Graph
        if enable_knowledge_graph:
            self.knowledge_graph = CognitiveKnowledgeBase()
        else:
            self.knowledge_graph = None
        
        # Cognitive Capital
        if enable_cognitive_capital:
            self.cognitive_capital = CognitiveCapitalManager()
        else:
            self.cognitive_capital = None
        
        # MCP Client
        if enable_mcp:
            self.mcp_client = MCPClientFacade()
        else:
            self.mcp_client = None
        
        # SWE Agents
        if enable_swe_agents:
            self.swe_team = SWEAgentTeam()
        else:
            self.swe_team = None
        
        # Core orchestrator
        from .orchestration.graph import create_orchestrator
        self._orchestrator = create_orchestrator()
    
    async def chat(
        self,
        message: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> SuperAssistantResponse:
        """Procesa un mensaje con todas las capacidades."""
        
        # 1. Recuperar contexto del Knowledge Graph
        kg_context = {}
        if self.knowledge_graph:
            kg_context = await self.knowledge_graph.get_context_for_agent(
                task=message,
                agent_role="lead"
            )
        
        # 2. Recuperar Capital Cognitivo relevante
        capital_context = {}
        if self.cognitive_capital:
            capital_context = await self.cognitive_capital.get_context_for_task(
                task=message
            )
        
        # 3. Procesar con orquestador
        result = await self._orchestrator.process(
            message=message,
            user_id=user_id,
            session_id=session_id
        )
        
        # 4. Aprender de la interacción
        messages = result.get("messages", [])
        last_message = messages[-1] if messages else {}
        response_content = last_message.get("content", "")
        
        if self.cognitive_capital:
            await self.cognitive_capital.learn_from_interaction(
                user_input=message,
                agent_response=response_content,
                context={"user_id": user_id, "session_id": session_id}
            )
        
        if self.knowledge_graph:
            await self.knowledge_graph.learn(
                text=f"{message}\n{response_content}",
                source=session_id
            )
        
        return SuperAssistantResponse(
            content=response_content,
            agent_contributions=result.get("subagent_results", {}),
            iterations=result.get("iteration_count", 0),
            success=True
        )
    
    async def solve_code_problem(
        self,
        problem: str,
        code: Optional[str] = None
    ) -> Dict[str, Any]:
        """Resuelve un problema de código usando agentes SWE."""
        if not self.swe_team:
            return {"error": "SWE agents not enabled"}
        
        result = await self.swe_team.solve(problem, code)
        
        # Aprender de la solución
        if self.cognitive_capital:
            reasoning = self.swe_team.get_full_reasoning()
            await self.cognitive_capital.store.learn(reasoning, {"type": "swe_solution"})
        
        return result
    
    async def learn_knowledge(
        self,
        text: str,
        source: Optional[str] = None
    ) -> Dict[str, Any]:
        """Aprende nuevo conocimiento."""
        results = {}
        
        if self.knowledge_graph:
            kg_result = await self.knowledge_graph.learn(text, source)
            results["knowledge_graph"] = kg_result
        
        if self.cognitive_capital:
            cc_result = await self.cognitive_capital.learn_from_interaction(
                user_input="LEARN",
                agent_response=text,
                context={"source": source, "type": "explicit_learning"}
            )
            results["cognitive_capital"] = cc_result
        
        return results
    
    async def query_knowledge(
        self,
        query: str
    ) -> Dict[str, Any]:
        """Consulta el conocimiento acumulado."""
        results = {}
        
        if self.knowledge_graph:
            kg_result = await self.knowledge_graph.query(query)
            results["knowledge_graph"] = kg_result
        
        if self.cognitive_capital:
            cc_result = await self.cognitive_capital.get_context_for_task(query)
            results["cognitive_capital"] = cc_result
        
        return results
    
    def get_cognitive_report(self) -> Dict[str, Any]:
        """Obtiene reporte del estado cognitivo."""
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "components": {}
        }
        
        if self.cognitive_capital:
            report["components"]["cognitive_capital"] = (
                self.cognitive_capital.get_capital_report()
            )
        
        if self.knowledge_graph:
            # Basic stats from knowledge graph
            kg = self.knowledge_graph.graph
            report["components"]["knowledge_graph"] = {
                "entities": len(kg._entities),
                "relationships": len(kg._relationships),
                "communities": len(kg._communities)
            }
        
        return report
    
    async def register_mcp_server(
        self,
        name: str,
        config: MCPServerConfig
    ) -> bool:
        """Registra un servidor MCP."""
        if not self.mcp_client:
            return False
        
        return await self.mcp_client.register_server(name, config)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_assistant_v2(**kwargs) -> SuperAssistantV2:
    """Factory para crear SuperAssistantV2."""
    return SuperAssistantV2(**kwargs)


# Need to import datetime
from datetime import datetime


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Version
    "__version__",
    
    # Main Class
    "SuperAssistantV2",
    "create_assistant_v2",
    
    # Knowledge Graph
    "EntityType", "RelationType",
    "Entity", "Relationship", "Community", "Triple",
    "EntityFactory", "KnowledgeGraph", "CognitiveKnowledgeBase",
    
    # Cognitive Capital
    "CognitiveAssetType", "CognitiveAsset", "CognitiveValue",
    "CognitiveCapitalStore", "CognitiveCapitalManager",
    
    # MCP
    "MCPTransportType", "MCPToolSchema", "MCPToolResult",
    "MCPServerConfig", "MCPClientFacade", "MCPProxy", "MCPSkillBridge",
    
    # GOF Patterns
    "AgentBuilder", "AgentRegistry", "AgentPrototype",
    "AgentDecorator", "LoggingDecorator", "CachingDecorator", "RetryDecorator",
    "TaskComponent", "SimpleTask", "CompositeTask",
    "RequestHandler", "SecurityHandler", "ProcessingHandler",
    "Command", "CommandInvoker",
    "Observer", "Subject", "Event",
    "ExecutionStrategy", "SequentialStrategy", "ParallelStrategy",
    
    # SWE Agents
    "ThoughtType", "Thought", "ThoughtChain",
    "TreeOfThought", "SelfRefine", "ReActExecutor",
    "SWEAgentRole", "BaseSWEAgent",
    "CodeAnalyzerAgent", "CodePlannerAgent", 
    "CodeBuilderAgent", "CodeTesterAgent",
    "SWEAgentTeam",
]
