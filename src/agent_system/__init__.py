"""
Agent System - Configuration-Driven Agent Architecture

This module implements a fully configurable agent system that follows SOLID principles.
All domains, roles, and behaviors are loaded from JSON configuration files.

NO HARDCODED VALUES - Everything is configuration-driven.

Architecture:
- Groups: Domain-oriented agent groups
- Roles: Configurable agent roles (investigator, observer, validator, builder, assistant)
- Capital: Cognitive capital and learning system
- NEXUS: Super agent coordinator

SOLID Compliance:
- SRP: Each module has a single responsibility
- OCP: Open for extension via configuration, closed for modification
- LSP: All agents implement the same interface
- ISP: Interfaces are specific and segregated
- DIP: Dependencies injected via configuration
"""

from typing import Dict, List, Optional, Any, Literal, TypedDict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import uuid
import json
import logging

# Import configuration loader
from ..config.agent_config import get_config, ConfigLoader

logger = logging.getLogger(__name__)


# ============================================
# ENUMS AND TYPES
# ============================================

class AgentStatus(str, Enum):
    """Agent status enumeration."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    LEARNING = "learning"
    ERROR = "error"


class CapitalSyncMode(str, Enum):
    """Capital synchronization mode."""
    CENTRALIZED = "centralized"
    DECENTRALIZED = "decentralized"
    HYBRID = "hybrid"


# ============================================
# DATA CLASSES
# ============================================

@dataclass
class Engram:
    """Cognitive memory unit."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    access_count: int = 0
    importance_score: float = 0.5
    source: Literal["interaction", "observation", "reflection", "instruction"] = "interaction"
    tags: List[str] = field(default_factory=list)
    
    def access(self) -> None:
        """Increment access counter."""
        self.access_count += 1
        self.updated_at = datetime.utcnow().isoformat()


@dataclass
class CognitiveCapital:
    """
    Cognitive Capital for an agent.
    Includes engrams, metrics and synchronization configuration.
    """
    agent_id: str
    total_engrams: int = 0
    total_interactions: int = 0
    learning_score: float = 0.0
    domains: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    mcp_servers: List[str] = field(default_factory=list)
    memory_vcs_version: str = "v1.0.0"
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    capital_value: int = 0
    engrams: List[Engram] = field(default_factory=list)
    
    # Auto-improvement
    auto_improve_enabled: bool = True
    improvement_rate: float = 0.0
    last_improvement: Optional[str] = None
    
    # Synchronization
    sync_mode: CapitalSyncMode = CapitalSyncMode.HYBRID
    last_sync: Optional[str] = None
    sync_peers: List[str] = field(default_factory=list)
    
    def add_engram(self, engram: Engram) -> None:
        """Add a new engram."""
        self.engrams.append(engram)
        self.total_engrams = len(self.engrams)
        self._recalculate_capital()
        self.updated_at = datetime.utcnow().isoformat()
    
    def _recalculate_capital(self) -> None:
        """Recalculate cognitive capital value."""
        base_value = self.total_engrams * 10
        interaction_bonus = self.total_interactions * 2
        learning_bonus = int(self.learning_score * 1000)
        importance_bonus = sum(e.importance_score for e in self.engrams) * 5
        
        self.capital_value = int(base_value + interaction_bonus + learning_bonus + importance_bonus)
    
    def improve(self, improvement_delta: float) -> None:
        """Auto-improve capital."""
        if self.auto_improve_enabled:
            self.learning_score = min(1.0, self.learning_score + improvement_delta)
            self.improvement_rate = improvement_delta
            self.last_improvement = datetime.utcnow().isoformat()
            self._recalculate_capital()
    
    def get_top_engrams(self, n: int = 10) -> List[Engram]:
        """Get top n most important engrams."""
        return sorted(self.engrams, key=lambda e: e.importance_score, reverse=True)[:n]


@dataclass
class AgentProfile:
    """Agent profile - fully configurable."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    domain: str = "custom"
    role: Optional[str] = None
    skills: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    mcp_servers: List[str] = field(default_factory=list)
    prompt_template: str = ""
    status: AgentStatus = AgentStatus.ACTIVE
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    cognitive_capital: Optional[CognitiveCapital] = None
    
    # Metrics
    total_interactions: int = 0
    success_rate: float = 0.0
    avg_response_time: float = 0.0
    capital_growth: float = 0.0
    last_interaction: Optional[str] = None
    
    def __post_init__(self):
        if self.cognitive_capital is None:
            self.cognitive_capital = CognitiveCapital(agent_id=self.id)


# ============================================
# AGENT GROUP - Configuration-Driven
# ============================================

@dataclass
class AgentGroup:
    """
    Agent Group - Domain-oriented group of agents.
    
    Roles are loaded from configuration, not hardcoded.
    Each group creates agents based on configured roles.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    elegant_name: str = ""
    domain: str = "custom"
    description: str = ""
    status: AgentStatus = AgentStatus.ACTIVE
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # Agents (dynamic based on configuration)
    agents: Dict[str, AgentProfile] = field(default_factory=dict)
    
    # Shared capital
    shared_capital: Optional[CognitiveCapital] = None
    
    # Metrics
    total_tasks: int = 0
    success_rate: float = 0.0
    avg_completion_time: float = 0.0
    domain_expertise: float = 0.0
    
    # Synchronization
    sync_mode: CapitalSyncMode = CapitalSyncMode.HYBRID
    centralized_capital: Optional[CognitiveCapital] = None
    
    def __post_init__(self):
        if self.shared_capital is None:
            self.shared_capital = CognitiveCapital(agent_id=self.id)
        if self.centralized_capital is None:
            self.centralized_capital = CognitiveCapital(agent_id=f"{self.id}_central")
        
        # Load domain branding from configuration
        config = get_config()
        domain_config = config.get_domain(self.domain)
        if domain_config:
            if not self.elegant_name:
                self.elegant_name = domain_config.get("elegant_name", "")
        
        # Create agents based on configured roles
        self._create_agents_from_config()
    
    def _create_agents_from_config(self) -> None:
        """Create agents based on roles configuration."""
        config = get_config()
        roles = config.get_roles()
        domain_config = config.get_domain(self.domain)
        
        for role_id, role_config in roles.items():
            agent = self._create_role_agent(role_id, role_config, domain_config)
            self.agents[role_id] = agent
    
    def _create_role_agent(
        self,
        role_id: str,
        role_config: Dict[str, Any],
        domain_config: Optional[Dict[str, Any]]
    ) -> AgentProfile:
        """Create an agent for a specific role."""
        domain_name = domain_config.get("name", "Custom") if domain_config else "Custom"
        elegant_name = domain_config.get("elegant_name", "CUSTOM") if domain_config else "CUSTOM"
        
        role_elegant_name = role_config.get("elegant_name", role_id.upper())
        role_description = role_config.get("description", "")
        
        return AgentProfile(
            name=f"{role_elegant_name} {elegant_name}",
            description=f"{role_description} en {domain_name}",
            domain=self.domain,
            role=role_id,
            skills=role_config.get("skills", []),
            tools=role_config.get("tools", []),
        )
    
    def get_all_agents(self) -> Dict[str, AgentProfile]:
        """Get all agents in the group."""
        return self.agents
    
    async def sync_capital(self, mode: Optional[CapitalSyncMode] = None) -> Dict[str, Any]:
        """Synchronize cognitive capital between agents."""
        sync_mode = mode or self.sync_mode
        sync_result = {
            "mode": sync_mode.value,
            "timestamp": datetime.utcnow().isoformat(),
            "synced_agents": [],
            "total_engrams_synced": 0,
        }
        
        agents = self.get_all_agents()
        
        if sync_mode == CapitalSyncMode.CENTRALIZED:
            for role_id, agent in agents.items():
                if agent and agent.cognitive_capital:
                    self.centralized_capital.engrams.extend(agent.cognitive_capital.engrams)
                    sync_result["synced_agents"].append(role_id)
                    sync_result["total_engrams_synced"] += len(agent.cognitive_capital.engrams)
            
            for role_id, agent in agents.items():
                if agent and agent.cognitive_capital:
                    agent.cognitive_capital.learning_score = self.centralized_capital.learning_score
                    agent.cognitive_capital.last_sync = datetime.utcnow().isoformat()
        
        elif sync_mode == CapitalSyncMode.DECENTRALIZED:
            agent_list = [a for a in agents.values() if a and a.cognitive_capital]
            for i, agent1 in enumerate(agent_list):
                for agent2 in agent_list[i+1:]:
                    top_engrams_1 = agent1.cognitive_capital.get_top_engrams(5)
                    top_engrams_2 = agent2.cognitive_capital.get_top_engrams(5)
                    
                    for e in top_engrams_1:
                        if e not in agent2.cognitive_capital.engrams:
                            agent2.cognitive_capital.add_engram(e)
                            sync_result["total_engrams_synced"] += 1
                    
                    for e in top_engrams_2:
                        if e not in agent1.cognitive_capital.engrams:
                            agent1.cognitive_capital.add_engram(e)
                            sync_result["total_engrams_synced"] += 1
        
        elif sync_mode == CapitalSyncMode.HYBRID:
            await self.sync_capital(CapitalSyncMode.DECENTRALIZED)
            await self.sync_capital(CapitalSyncMode.CENTRALIZED)
        
        self.shared_capital.last_sync = datetime.utcnow().isoformat()
        
        return sync_result
    
    async def auto_improve(self) -> Dict[str, Any]:
        """Auto-improve the group."""
        improvement_result = {
            "timestamp": datetime.utcnow().isoformat(),
            "improvements": [],
            "new_engrams": 0,
            "capital_delta": 0,
        }
        
        for role_id, agent in self.get_all_agents().items():
            if agent and agent.cognitive_capital:
                improvement_delta = agent.success_rate * 0.1
                agent.cognitive_capital.improve(improvement_delta)
                
                improvement_result["improvements"].append({
                    "agent": role_id,
                    "delta": improvement_delta,
                    "new_score": agent.cognitive_capital.learning_score,
                })
        
        await self.sync_capital()
        
        return improvement_result


# ============================================
# AGENT GROUP MANAGER
# ============================================

class AgentGroupManager:
    """
    Agent Group Manager - Configuration-driven.
    
    Creates and manages groups based on configuration files.
    NO hardcoded domains or roles.
    """
    
    def __init__(self):
        self.groups: Dict[str, AgentGroup] = {}
        self.config = get_config()
        self._load_templates()
    
    def _load_templates(self) -> None:
        """Load templates from configuration."""
        self.domain_templates = {}
        domains = self.config.get_domains()
        
        for domain_id, domain_config in domains.items():
            self.domain_templates[domain_id] = {
                "name": domain_config.get("name", ""),
                "elegant_name": domain_config.get("elegant_name", ""),
                "tagline": domain_config.get("tagline", ""),
                "description": domain_config.get("description", ""),
                "mcp_servers": domain_config.get("mcp_servers", []),
            }
    
    def create_group(
        self,
        name: str,
        domain: str,
        description: str = "",
        sync_mode: CapitalSyncMode = CapitalSyncMode.HYBRID,
    ) -> AgentGroup:
        """Create a new agent group."""
        template = self.domain_templates.get(domain, {})
        domain_config = self.config.get_domain(domain)
        
        group = AgentGroup(
            name=name or f"{template.get('elegant_name', 'Custom')} Unit",
            elegant_name=template.get("elegant_name", ""),
            domain=domain,
            description=description or template.get("description", ""),
            sync_mode=sync_mode,
        )
        
        # Configure MCP servers from template
        mcp_servers = template.get("mcp_servers", [])
        for role_id, agent in group.get_all_agents().items():
            if agent:
                agent.mcp_servers = mcp_servers
        
        self.groups[group.id] = group
        return group
    
    def get_group(self, group_id: str) -> Optional[AgentGroup]:
        """Get a group by ID."""
        return self.groups.get(group_id)
    
    def list_groups(self) -> List[AgentGroup]:
        """List all groups."""
        return list(self.groups.values())
    
    async def sync_all_groups(self) -> Dict[str, Any]:
        """Synchronize all groups."""
        results = {}
        for group_id, group in self.groups.items():
            results[group_id] = await group.sync_capital()
        return results
    
    async def auto_improve_all(self) -> Dict[str, Any]:
        """Auto-improve all groups."""
        results = {}
        for group_id, group in self.groups.items():
            results[group_id] = await group.auto_improve()
        return results
    
    def get_domain_branding(self, domain: str) -> Dict[str, Any]:
        """Get branding for a domain."""
        return self.config.get_domain(domain) or {}
    
    def get_all_domain_brands(self) -> Dict[str, Dict[str, Any]]:
        """Get all domain branding."""
        return self.config.get_domains()


# ============================================
# EXPORTS
# ============================================

__all__ = [
    # Enums
    "AgentStatus",
    "CapitalSyncMode",
    
    # Data Classes
    "Engram",
    "CognitiveCapital",
    "AgentProfile",
    "AgentGroup",
    
    # Managers
    "AgentGroupManager",
]
