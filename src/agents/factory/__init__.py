"""
Agent Factory Module for RICCO AI.

Provides dynamic agent creation with MCP injection and mixin support.
"""

from typing import Any, Dict, List, Optional, Type, Union
from enum import Enum
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    """Types of agents that can be created."""
    SUPPORT = "support"
    SALES = "sales"
    ADVISOR = "advisor"
    COMMERCE = "commerce"
    HEALTH = "health"
    FINANCE = "finance"
    LOGISTICS = "logistics"


class MixinType(str, Enum):
    """Types of mixins that can be applied to agents."""
    FRUSTRATION_HANDLER = "frustration_handler"
    RESPONSE_FORMATTER = "response_formatter"
    CONTEXT_AWARE = "context_aware"


class MCPServerConfig(BaseModel):
    """MCP server configuration for agent injection."""
    name: str
    endpoint: str
    capabilities: List[str] = Field(default_factory=list)
    timeout: int = 30
    retry_count: int = 3
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentConfig(BaseModel):
    """Configuration for creating an agent."""
    agent_type: AgentType
    name: str
    description: str = ""
    mcp_servers: List[MCPServerConfig] = Field(default_factory=list)
    mixins: List[MixinType] = Field(default_factory=list)
    system_prompt: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SwarmAgent:
    """Base class for swarm agents."""
    
    def __init__(
        self,
        name: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        **kwargs,
    ):
        self.name = name
        self.system_prompt = system_prompt
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._mcps: List[Dict[str, Any]] = []
        self._mixins: List[Any] = []
    
    def inject_mcps(self, mcp_list: List[Dict[str, Any]]) -> None:
        """Inject MCP servers into the agent."""
        self._mcps.extend(mcp_list)
        logger.debug(f"Injected {len(mcp_list)} MCP servers into {self.name}")
    
    def add_mixin(self, mixin: Any) -> None:
        """Add a mixin to the agent."""
        self._mixins.append(mixin)
        logger.debug(f"Added mixin to {self.name}")
    
    def get_mixin(self, mixin_class: Type) -> Optional[Any]:
        """Get a mixin by class type."""
        for mixin in self._mixins:
            if isinstance(mixin, mixin_class):
                return mixin
        return None
    
    async def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request (to be overridden)."""
        return {
            "agent": self.name,
            "response": "Processing complete",
        }


# Default configurations for agent types
DEFAULT_CONFIGS: Dict[AgentType, Dict[str, Any]] = {
    AgentType.SUPPORT: {
        "description": "Customer support agent",
        "mixins": [MixinType.FRUSTRATION_HANDLER, MixinType.CONTEXT_AWARE],
        "system_prompt": "You are a helpful customer support agent.",
    },
    AgentType.SALES: {
        "description": "Sales agent",
        "mixins": [MixinType.RESPONSE_FORMATTER, MixinType.CONTEXT_AWARE],
        "system_prompt": "You are a helpful sales agent.",
    },
    AgentType.ADVISOR: {
        "description": "Advisory agent",
        "mixins": [MixinType.RESPONSE_FORMATTER, MixinType.CONTEXT_AWARE],
        "system_prompt": "You are a helpful advisor.",
    },
    AgentType.COMMERCE: {
        "description": "E-commerce agent",
        "mixins": [MixinType.RESPONSE_FORMATTER, MixinType.CONTEXT_AWARE],
        "system_prompt": "You are an e-commerce assistant.",
    },
    AgentType.HEALTH: {
        "description": "Health consultation agent",
        "mixins": [MixinType.RESPONSE_FORMATTER, MixinType.CONTEXT_AWARE],
        "system_prompt": "You are a health consultation assistant.",
    },
    AgentType.FINANCE: {
        "description": "Financial advisory agent",
        "mixins": [MixinType.RESPONSE_FORMATTER, MixinType.CONTEXT_AWARE],
        "system_prompt": "You are a financial advisory assistant.",
    },
    AgentType.LOGISTICS: {
        "description": "Logistics agent",
        "mixins": [MixinType.CONTEXT_AWARE],
        "system_prompt": "You are a logistics assistant.",
    },
}


def get_default_config(agent_type: AgentType) -> Dict[str, Any]:
    """Get default configuration for an agent type."""
    return DEFAULT_CONFIGS.get(agent_type, {})


class AgentFactoryError(Exception):
    """Exception raised for agent factory errors."""
    pass


class AgentFactory:
    """
    Factory class for creating and configuring agents.
    
    Provides methods to create agents based on type, inject MCP servers,
    and apply mixins dynamically.
    """
    
    def __init__(
        self,
        custom_agents: Optional[Dict[str, Type[SwarmAgent]]] = None,
        custom_mixins: Optional[Dict[str, Type]] = None,
    ):
        self._agent_registry: Dict[AgentType, Type[SwarmAgent]] = {
            AgentType.SUPPORT: SwarmAgent,
            AgentType.SALES: SwarmAgent,
            AgentType.ADVISOR: SwarmAgent,
            AgentType.COMMERCE: SwarmAgent,
            AgentType.HEALTH: SwarmAgent,
            AgentType.FINANCE: SwarmAgent,
            AgentType.LOGISTICS: SwarmAgent,
        }
        self._mixin_registry: Dict[MixinType, Type] = {}
        self._agent_instances: Dict[str, SwarmAgent] = {}
        
        # Register custom agents and mixins
        if custom_agents:
            for agent_type, agent_class in custom_agents.items():
                self.register_agent_type(agent_type, agent_class)
        
        if custom_mixins:
            for mixin_type, mixin_class in custom_mixins.items():
                self.register_mixin_type(mixin_type, mixin_class)
    
    def create_agent(
        self,
        config: AgentConfig,
        instance_id: Optional[str] = None,
    ) -> SwarmAgent:
        """
        Create an agent based on the provided configuration.
        
        Args:
            config: Agent configuration.
            instance_id: Optional instance identifier for tracking.
            
        Returns:
            Configured agent instance.
        """
        # Get base agent class
        base_class = self._agent_registry.get(config.agent_type)
        
        if base_class is None:
            raise AgentFactoryError(
                f"Unknown agent type: {config.agent_type}. "
                f"Available types: {[t.value for t in self._agent_registry.keys()]}"
            )
        
        # Merge with default configuration
        default_config = get_default_config(config.agent_type)
        merged_config = self._merge_configs(config, default_config)
        
        # Create the agent instance
        agent = base_class(
            name=merged_config.name,
            system_prompt=merged_config.system_prompt,
            max_tokens=merged_config.max_tokens,
            temperature=merged_config.temperature,
            **merged_config.metadata,
        )
        
        # Inject MCP servers
        if merged_config.mcp_servers:
            agent = self._inject_mcps(agent, merged_config.mcp_servers)
        
        # Store instance if ID provided
        if instance_id:
            self._agent_instances[instance_id] = agent
        
        logger.info(f"Created agent: {merged_config.name} ({merged_config.agent_type.value})")
        return agent
    
    def create_agent_from_type(
        self,
        agent_type: Union[AgentType, str],
        name: Optional[str] = None,
        mcp_servers: Optional[List[MCPServerConfig]] = None,
        mixins: Optional[List[Union[MixinType, str]]] = None,
        **kwargs,
    ) -> SwarmAgent:
        """
        Create an agent with a simplified interface.
        """
        # Convert string to AgentType if necessary
        if isinstance(agent_type, str):
            agent_type = AgentType(agent_type.lower())
        
        config = AgentConfig(
            agent_type=agent_type,
            name=name or f"{agent_type.value.title()}Agent",
            mcp_servers=mcp_servers or [],
            **kwargs,
        )
        
        return self.create_agent(config)
    
    def _inject_mcps(
        self,
        agent: SwarmAgent,
        mcp_servers: List[MCPServerConfig],
    ) -> SwarmAgent:
        """Inject MCP servers into the agent."""
        mcp_list = [
            {
                "name": mcp.name,
                "endpoint": mcp.endpoint,
                "capabilities": mcp.capabilities,
                "timeout": mcp.timeout,
                "retry_count": mcp.retry_count,
                "metadata": mcp.metadata,
            }
            for mcp in mcp_servers
        ]
        
        agent.inject_mcps(mcp_list)
        return agent
    
    def _merge_configs(
        self,
        config: AgentConfig,
        default: Dict[str, Any],
    ) -> AgentConfig:
        """Merge configuration with defaults."""
        return AgentConfig(
            agent_type=config.agent_type,
            name=config.name,
            description=config.description or default.get("description", ""),
            mcp_servers=config.mcp_servers[:],
            mixins=config.mixins[:],
            system_prompt=config.system_prompt or default.get("system_prompt"),
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            metadata=config.metadata.copy(),
        )
    
    def register_agent_type(
        self,
        agent_type: Union[AgentType, str],
        agent_class: Type[SwarmAgent],
    ) -> None:
        """Register a custom agent type."""
        if isinstance(agent_type, str):
            agent_type = AgentType(agent_type.lower())
        
        self._agent_registry[agent_type] = agent_class
    
    def register_mixin_type(
        self,
        mixin_type: Union[MixinType, str],
        mixin_class: Type,
    ) -> None:
        """Register a custom mixin type."""
        if isinstance(mixin_type, str):
            mixin_type = MixinType(mixin_type.lower())
        
        self._mixin_registry[mixin_type] = mixin_class
    
    def get_agent_instance(self, instance_id: str) -> Optional[SwarmAgent]:
        """Get a stored agent instance by ID."""
        return self._agent_instances.get(instance_id)
    
    def remove_agent_instance(self, instance_id: str) -> bool:
        """Remove a stored agent instance."""
        if instance_id in self._agent_instances:
            del self._agent_instances[instance_id]
            return True
        return False
    
    def list_registered_types(self) -> Dict[str, List[str]]:
        """List all registered agent and mixin types."""
        return {
            "agents": [t.value for t in self._agent_registry.keys()],
            "mixins": [t.value for t in self._mixin_registry.keys()],
        }


# Default factory instance
default_factory = AgentFactory()


def create_agent(
    agent_type: Union[AgentType, str],
    name: Optional[str] = None,
    **kwargs,
) -> SwarmAgent:
    """
    Convenience function to create an agent using the default factory.
    """
    return default_factory.create_agent_from_type(
        agent_type=agent_type,
        name=name,
        **kwargs,
    )
