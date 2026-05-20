"""
Dynamic Agent Registry

Fully configuration-driven agent system that follows OCP (Open/Closed Principle).
To add a new agent, simply add an entry to agents.json - NO CODE CHANGES REQUIRED.

Architecture:
- AgentRegistry: Discovers and loads agents from configuration
- AgentFactory: Creates agent instances dynamically
- CapabilityResolver: Resolves skills, tools, MCP servers from config
- BehaviorProfile: Loads behavior from config, not hardcoded classes

NO HARDCODED:
- Agent types
- Agent classes
- Agent behaviors
- Agent capabilities
- File system structure for agents
"""

from typing import Dict, List, Optional, Any, Callable, TypeVar, Generic, Protocol
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
import json
import uuid
import logging
import asyncio
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# Configuration paths
CONFIG_DIR = Path(__file__).parent.parent / "config"
AGENTS_CONFIG_FILE = CONFIG_DIR / "agents.json"
DOMAINS_CONFIG_FILE = CONFIG_DIR / "domains.json"
ROLES_CONFIG_FILE = CONFIG_DIR / "roles.json"
PLATFORM_CONFIG_FILE = CONFIG_DIR / "platform.json"


# ============================================
# PROTOCOLS (Interfaces for dependency injection)
# ============================================

class AgentCapability(Protocol):
    """Protocol for agent capabilities - implemented dynamically."""
    def execute(self, context: Dict[str, Any]) -> Any:
        ...


class AgentBehavior(Protocol):
    """Protocol for agent behavior - loaded from config."""
    def apply(self, content: str) -> str:
        ...


# ============================================
# DATA CLASSES (Loaded from configuration)
# ============================================

@dataclass
class CapabilityConfig:
    """Agent capabilities loaded from configuration."""
    skills: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    mcp_servers: List[str] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CapabilityConfig':
        return cls(
            skills=data.get("skills", []),
            tools=data.get("tools", []),
            mcp_servers=data.get("mcp_servers", []),
        )


@dataclass
class BehaviorConfig:
    """Agent behavior loaded from configuration."""
    tone: str = "professional"
    style: str = "balanced"
    response_format: str = "default"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BehaviorConfig':
        return cls(
            tone=data.get("tone", "professional"),
            style=data.get("style", "balanced"),
            response_format=data.get("response_format", "default"),
        )


@dataclass
class PromptConfig:
    """Agent prompts loaded from configuration."""
    system: str = ""
    task_template: str = ""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PromptConfig':
        return cls(
            system=data.get("system", ""),
            task_template=data.get("task_template", ""),
        )


@dataclass
class LimitsConfig:
    """Agent limits loaded from configuration."""
    max_tokens: int = 4096
    timeout_seconds: int = 60
    max_retries: int = 3
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LimitsConfig':
        return cls(
            max_tokens=data.get("max_tokens", 4096),
            timeout_seconds=data.get("timeout_seconds", 60),
            max_retries=data.get("max_retries", 3),
        )


@dataclass
class AgentDefinition:
    """
    Complete agent definition loaded from configuration.
    
    This is the single source of truth for what an agent is.
    NO CODE REQUIRED to define an agent - just configuration.
    """
    id: str
    name: str
    description: str
    domain: str
    role: str
    capabilities: CapabilityConfig
    behavior: BehaviorConfig
    prompts: PromptConfig
    limits: LimitsConfig
    enabled: bool = True
    is_coordinator: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentDefinition':
        return cls(
            id=data["id"],
            name=data.get("name", data["id"]),
            description=data.get("description", ""),
            domain=data.get("domain", "custom"),
            role=data.get("role", "assistant"),
            capabilities=CapabilityConfig.from_dict(data.get("capabilities", {})),
            behavior=BehaviorConfig.from_dict(data.get("behavior", {})),
            prompts=PromptConfig.from_dict(data.get("prompts", {})),
            limits=LimitsConfig.from_dict(data.get("limits", {})),
            enabled=data.get("enabled", True),
            is_coordinator=data.get("is_coordinator", False),
            metadata=data.get("metadata", {}),
        )


@dataclass
class AgentGroupDefinition:
    """Agent group definition loaded from configuration."""
    id: str
    name: str
    domain: str
    agent_ids: List[str]
    coordinator: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentGroupDefinition':
        return cls(
            id=data["id"],
            name=data.get("name", data["id"]),
            domain=data.get("domain", "custom"),
            agent_ids=data.get("agent_ids", []),
            coordinator=data.get("coordinator"),
        )


# ============================================
# AGENT REGISTRY (Dynamic discovery)
# ============================================

class AgentRegistry:
    """
    Dynamic Agent Registry - Discovers agents from configuration.
    
    NO HARDCODED AGENT TYPES.
    To add an agent, just add to agents.json.
    
    Implements:
    - Registry Pattern: Central discovery point
    - Singleton: Single source of truth
    - Lazy Loading: Load on demand
    """
    
    _instance: Optional['AgentRegistry'] = None
    
    def __new__(cls) -> 'AgentRegistry':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._agents: Dict[str, AgentDefinition] = {}
        self._groups: Dict[str, AgentGroupDefinition] = {}
        self._domains: Dict[str, Dict[str, Any]] = {}
        self._roles: Dict[str, Dict[str, Any]] = {}
        self._loaded = False
        self._initialized = True
    
    def load(self, config_path: Optional[Path] = None) -> None:
        """Load all configurations."""
        if self._loaded:
            return
        
        self._load_domains()
        self._load_roles()
        self._load_agents(config_path)
        self._load_groups()
        self._loaded = True
        
        logger.info(f"Registry loaded: {len(self._agents)} agents, {len(self._groups)} groups")
    
    def _load_domains(self) -> None:
        """Load domain configurations."""
        try:
            with open(DOMAINS_CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._domains = data.get("domains", {})
        except FileNotFoundError:
            logger.warning(f"Domains config not found: {DOMAINS_CONFIG_FILE}")
            self._domains = {}
    
    def _load_roles(self) -> None:
        """Load role configurations."""
        try:
            with open(ROLES_CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._roles = data.get("roles", {})
        except FileNotFoundError:
            logger.warning(f"Roles config not found: {ROLES_CONFIG_FILE}")
            self._roles = {}
    
    def _load_agents(self, config_path: Optional[Path] = None) -> None:
        """Load agent definitions from configuration."""
        path = config_path or AGENTS_CONFIG_FILE
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                agents_data = data.get("agents", {})
                
                for agent_id, agent_config in agents_data.items():
                    agent_config["id"] = agent_id
                    self._agents[agent_id] = AgentDefinition.from_dict(agent_config)
                    
            logger.info(f"Loaded {len(self._agents)} agents from {path}")
        except FileNotFoundError:
            logger.warning(f"Agents config not found: {path}")
            self._agents = {}
    
    def _load_groups(self) -> None:
        """Load agent group definitions."""
        try:
            with open(AGENTS_CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                groups_data = data.get("agent_groups", {})
                
                for group_id, group_config in groups_data.items():
                    group_config["id"] = group_id
                    self._groups[group_id] = AgentGroupDefinition.from_dict(group_config)
                    
        except FileNotFoundError:
            self._groups = {}
    
    def reload(self) -> None:
        """Reload all configurations."""
        self._loaded = False
        self._agents.clear()
        self._groups.clear()
        self.load()
    
    # ============================================
    # AGENT DISCOVERY (Dynamic)
    # ============================================
    
    def get_agent(self, agent_id: str) -> Optional[AgentDefinition]:
        """Get an agent definition by ID."""
        if not self._loaded:
            self.load()
        return self._agents.get(agent_id)
    
    def get_all_agents(self) -> Dict[str, AgentDefinition]:
        """Get all agent definitions."""
        if not self._loaded:
            self.load()
        return self._agents.copy()
    
    def get_agents_by_domain(self, domain: str) -> List[AgentDefinition]:
        """Get all agents for a domain."""
        if not self._loaded:
            self.load()
        return [a for a in self._agents.values() if a.domain == domain]
    
    def get_agents_by_role(self, role: str) -> List[AgentDefinition]:
        """Get all agents with a specific role."""
        if not self._loaded:
            self.load()
        return [a for a in self._agents.values() if a.role == role]
    
    def get_enabled_agents(self) -> List[AgentDefinition]:
        """Get all enabled agents."""
        if not self._loaded:
            self.load()
        return [a for a in self._agents.values() if a.enabled]
    
    def get_coordinator(self) -> Optional[AgentDefinition]:
        """Get the coordinator agent."""
        if not self._loaded:
            self.load()
        for agent in self._agents.values():
            if agent.is_coordinator:
                return agent
        return None
    
    # ============================================
    # GROUP DISCOVERY
    # ============================================
    
    def get_group(self, group_id: str) -> Optional[AgentGroupDefinition]:
        """Get a group definition by ID."""
        if not self._loaded:
            self.load()
        return self._groups.get(group_id)
    
    def get_all_groups(self) -> Dict[str, AgentGroupDefinition]:
        """Get all group definitions."""
        if not self._loaded:
            self.load()
        return self._groups.copy()
    
    def get_group_for_domain(self, domain: str) -> Optional[AgentGroupDefinition]:
        """Get the group for a specific domain."""
        if not self._loaded:
            self.load()
        for group in self._groups.values():
            if group.domain == domain:
                return group
        return None
    
    # ============================================
    # DOMAIN & ROLE LOOKUP
    # ============================================
    
    def get_domain_config(self, domain: str) -> Optional[Dict[str, Any]]:
        """Get domain configuration."""
        if not self._loaded:
            self.load()
        return self._domains.get(domain)
    
    def get_role_config(self, role: str) -> Optional[Dict[str, Any]]:
        """Get role configuration."""
        if not self._loaded:
            self.load()
        return self._roles.get(role)
    
    def detect_domain(self, query: str) -> tuple:
        """Detect domain from query using configuration."""
        if not self._loaded:
            self.load()
        
        query_lower = query.lower()
        scores: Dict[str, int] = {}
        
        for domain_id, domain_config in self._domains.items():
            keywords = domain_config.get("keywords", [])
            score = sum(1 for kw in keywords if kw in query_lower)
            if score > 0:
                scores[domain_id] = score
        
        if not scores:
            return "custom", 0.3
        
        best_domain = max(scores, key=scores.get)
        total_matches = scores[best_domain]
        max_possible = len(self._domains.get(best_domain, {}).get("keywords", []))
        
        confidence = min(0.95, 0.4 + (total_matches / max(max_possible, 1)) * 0.5)
        
        return best_domain, confidence
    
    # ============================================
    # DYNAMIC REGISTRATION (Runtime)
    # ============================================
    
    def register_agent(self, agent_config: Dict[str, Any]) -> AgentDefinition:
        """
        Register a new agent at runtime.
        
        This allows dynamic agent creation without code changes.
        The agent is added to the registry but not persisted.
        """
        if not self._loaded:
            self.load()
        
        agent = AgentDefinition.from_dict(agent_config)
        self._agents[agent.id] = agent
        
        logger.info(f"Registered agent: {agent.id}")
        return agent
    
    def unregister_agent(self, agent_id: str) -> bool:
        """Remove an agent from the registry."""
        if agent_id in self._agents:
            del self._agents[agent_id]
            logger.info(f"Unregistered agent: {agent_id}")
            return True
        return False


# ============================================
# AGENT FACTORY (Dynamic instantiation)
# ============================================

class AgentFactory:
    """
    Dynamic Agent Factory - Creates agents from configuration.
    
    NO HARDCODED AGENT CLASSES.
    All agent behavior is derived from configuration.
    
    Implements:
    - Factory Pattern: Creates instances
    - Strategy Pattern: Behavior from config
    - Template Method: Prompt templates
    """
    
    def __init__(self, registry: Optional[AgentRegistry] = None):
        self.registry = registry or AgentRegistry()
        self._capability_resolvers: Dict[str, Callable] = {}
        self._behavior_modifiers: Dict[str, Callable] = {}
    
    def register_capability_resolver(self, capability_type: str, resolver: Callable) -> None:
        """Register a custom capability resolver."""
        self._capability_resolvers[capability_type] = resolver
    
    def register_behavior_modifier(self, behavior_type: str, modifier: Callable) -> None:
        """Register a custom behavior modifier."""
        self._behavior_modifiers[behavior_type] = modifier
    
    def create_agent(self, agent_id: str) -> Optional['DynamicAgent']:
        """
        Create an agent instance from configuration.
        
        The agent is fully configured from the registry,
        no hardcoded classes or behaviors.
        """
        definition = self.registry.get_agent(agent_id)
        if not definition:
            logger.error(f"Agent not found: {agent_id}")
            return None
        
        if not definition.enabled:
            logger.warning(f"Agent is disabled: {agent_id}")
            return None
        
        return DynamicAgent(
            definition=definition,
            factory=self,
        )
    
    def create_agents_for_domain(self, domain: str) -> List['DynamicAgent']:
        """Create all agents for a domain."""
        agents = []
        for agent_def in self.registry.get_agents_by_domain(domain):
            agent = self.create_agent(agent_def.id)
            if agent:
                agents.append(agent)
        return agents
    
    def create_coordinator(self) -> Optional['DynamicAgent']:
        """Create the coordinator agent."""
        coordinator_def = self.registry.get_coordinator()
        if coordinator_def:
            return self.create_agent(coordinator_def.id)
        return None
    
    def resolve_capabilities(self, definition: AgentDefinition) -> Dict[str, Any]:
        """Resolve agent capabilities from configuration."""
        capabilities = {
            "skills": definition.capabilities.skills.copy(),
            "tools": definition.capabilities.tools.copy(),
            "mcp_servers": definition.capabilities.mcp_servers.copy(),
        }
        
        # Apply custom resolvers
        for skill in capabilities["skills"]:
            if skill in self._capability_resolvers:
                resolver = self._capability_resolvers[skill]
                capabilities[f"skill_{skill}"] = resolver()
        
        return capabilities
    
    def resolve_behavior(self, definition: AgentDefinition) -> Dict[str, Any]:
        """Resolve agent behavior from configuration."""
        behavior = {
            "tone": definition.behavior.tone,
            "style": definition.behavior.style,
            "response_format": definition.behavior.response_format,
        }
        
        # Apply custom modifiers
        for key, value in behavior.items():
            if value in self._behavior_modifiers:
                modifier = self._behavior_modifiers[value]
                behavior[key] = modifier(value)
        
        return behavior
    
    def build_system_prompt(self, definition: AgentDefinition, context: Optional[Dict[str, Any]] = None) -> str:
        """Build system prompt from configuration."""
        context = context or {}
        
        domain_config = self.registry.get_domain_config(definition.domain)
        role_config = self.registry.get_role_config(definition.role)
        
        context.update({
            "domain": domain_config.get("name", definition.domain) if domain_config else definition.domain,
            "role": role_config.get("name", definition.role) if role_config else definition.role,
            "role_description": role_config.get("description", "") if role_config else "",
            "agent_name": definition.name,
            "agent_description": definition.description,
        })
        
        return definition.prompts.system.format(**context)


# ============================================
# DYNAMIC AGENT (Configuration-driven)
# ============================================

@dataclass
class AgentExecutionContext:
    """Context for agent execution."""
    query: str
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = "anonymous"
    domain: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentExecutionResult:
    """Result of agent execution."""
    agent_id: str
    success: bool
    content: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class DynamicAgent:
    """
    Dynamic Agent - Fully configured from definition.
    
    NO HARDCODED BEHAVIOR.
    All behavior comes from the AgentDefinition.
    
    This class is a thin wrapper around configuration.
    """
    
    def __init__(
        self,
        definition: AgentDefinition,
        factory: AgentFactory,
    ):
        self.definition = definition
        self.factory = factory
        self._capabilities = factory.resolve_capabilities(definition)
        self._behavior = factory.resolve_behavior(definition)
    
    @property
    def id(self) -> str:
        return self.definition.id
    
    @property
    def name(self) -> str:
        return self.definition.name
    
    @property
    def domain(self) -> str:
        return self.definition.domain
    
    @property
    def role(self) -> str:
        return self.definition.role
    
    @property
    def capabilities(self) -> Dict[str, Any]:
        return self._capabilities
    
    @property
    def behavior(self) -> Dict[str, Any]:
        return self._behavior
    
    def get_system_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Get the system prompt for this agent."""
        return self.factory.build_system_prompt(self.definition, context)
    
    def get_task_prompt(self, query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Get the task prompt for a specific query."""
        context = context or {}
        context["query"] = query
        
        if self.definition.prompts.task_template:
            return self.definition.prompts.task_template.format(**context)
        return query
    
    async def execute(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        llm_provider: Optional[Any] = None,
    ) -> AgentExecutionResult:
        """
        Execute a query using this agent.
        
        The execution is fully driven by the agent definition.
        """
        import time
        start_time = time.time()
        
        context = context or {}
        execution_context = AgentExecutionContext(
            query=query,
            domain=self.domain,
            metadata=context,
        )
        
        try:
            # Build prompts from configuration
            system_prompt = self.get_system_prompt(context)
            task_prompt = self.get_task_prompt(query, context)
            
            # Execute with LLM if provided
            if llm_provider:
                result = await self._execute_with_llm(
                    llm_provider=llm_provider,
                    system_prompt=system_prompt,
                    task_prompt=task_prompt,
                )
            else:
                result = self._generate_fallback_response(query)
            
            execution_time = time.time() - start_time
            
            return AgentExecutionResult(
                agent_id=self.id,
                success=True,
                content=result,
                metadata={
                    "domain": self.domain,
                    "role": self.role,
                    "execution_context": execution_context.metadata,
                },
                execution_time=execution_time,
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Agent {self.id} execution failed: {e}")
            
            return AgentExecutionResult(
                agent_id=self.id,
                success=False,
                content=str(e),
                execution_time=execution_time,
            )
    
    async def _execute_with_llm(
        self,
        llm_provider: Any,
        system_prompt: str,
        task_prompt: str,
    ) -> str:
        """Execute with LLM provider."""
        try:
            result = await llm_provider.chat_completion(
                messages=[{"role": "user", "content": task_prompt}],
                system_prompt=system_prompt,
                max_tokens=self.definition.limits.max_tokens,
            )
            return result.get("content", "")
        except Exception as e:
            logger.error(f"LLM execution failed: {e}")
            raise
    
    def _generate_fallback_response(self, query: str) -> str:
        """Generate fallback response when no LLM is available."""
        return f"""# {self.name}

I received your query: "{query[:100]}..."

**Agent:** {self.name}
**Domain:** {self.domain}
**Role:** {self.role}

**Capabilities:**
- Skills: {', '.join(self.capabilities.get('skills', []))}
- Tools: {', '.join(self.capabilities.get('tools', []))}

⚠️ **Note:** LLM provider not configured. Configure an LLM provider for full responses.
"""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert agent to dictionary representation."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.definition.description,
            "domain": self.domain,
            "role": self.role,
            "capabilities": self.capabilities,
            "behavior": self.behavior,
            "enabled": self.definition.enabled,
            "is_coordinator": self.definition.is_coordinator,
        }


# ============================================
# CONVENIENCE FUNCTIONS
# ============================================

# Global registry instance
_registry: Optional[AgentRegistry] = None


def get_registry() -> AgentRegistry:
    """Get the global agent registry."""
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
        _registry.load()
    return _registry


def get_factory() -> AgentFactory:
    """Get an agent factory with the global registry."""
    return AgentFactory(get_registry())


def get_agent(agent_id: str) -> Optional[DynamicAgent]:
    """Get an agent by ID."""
    return get_factory().create_agent(agent_id)


def get_agents_for_domain(domain: str) -> List[DynamicAgent]:
    """Get all agents for a domain."""
    return get_factory().create_agents_for_domain(domain)


def get_coordinator() -> Optional[DynamicAgent]:
    """Get the coordinator agent."""
    return get_factory().create_coordinator()


__all__ = [
    # Configuration classes
    "CapabilityConfig",
    "BehaviorConfig",
    "PromptConfig",
    "LimitsConfig",
    "AgentDefinition",
    "AgentGroupDefinition",
    
    # Core classes
    "AgentRegistry",
    "AgentFactory",
    "DynamicAgent",
    
    # Context classes
    "AgentExecutionContext",
    "AgentExecutionResult",
    
    # Convenience functions
    "get_registry",
    "get_factory",
    "get_agent",
    "get_agents_for_domain",
    "get_coordinator",
]
