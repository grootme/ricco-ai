"""
Agent Modules for RICCO AI.

This package provides agent-related functionality including:
- Agent Swarm: Multi-agent orchestration with specialized agents
- Agent Factory: Dynamic agent creation with MCP injection
- Agent Graphs: LangGraph-based DAG execution

Example:
--------
    from ricco_ai.agents import AgentFactory, AgentConfig, AgentType
    
    factory = AgentFactory()
    config = AgentConfig(
        agent_type=AgentType.COMMERCE,
        name="MyCommerceBot",
    )
    agent = factory.create_agent(config)
"""

from .swarm import (
    OrchestratorAgent,
    AgentType,
    AgentStatus,
    AgentCapability,
    AgentConfig as SwarmAgentConfig,
    AgentMessage,
    SwarmTask,
    SwarmState,
)
from .factory import (
    AgentFactory,
    AgentFactoryError,
    AgentConfig,
    AgentType as FactoryAgentType,
    create_agent,
    default_factory,
)
from .graphs import (
    GraphEngine,
    ExecutionConfig,
    ExecutionResult,
    CommerceGraph,
    FinanceGraph,
    HealthGraph,
    LogisticsGraph,
)

__version__ = "1.0.0"

__all__ = [
    # Swarm
    "OrchestratorAgent",
    "AgentType",
    "AgentStatus",
    "AgentCapability",
    "SwarmAgentConfig",
    "AgentMessage",
    "SwarmTask",
    "SwarmState",
    # Factory
    "AgentFactory",
    "AgentFactoryError",
    "AgentConfig",
    "FactoryAgentType",
    "create_agent",
    "default_factory",
    # Graphs
    "GraphEngine",
    "ExecutionConfig",
    "ExecutionResult",
    "CommerceGraph",
    "FinanceGraph",
    "HealthGraph",
    "LogisticsGraph",
]
