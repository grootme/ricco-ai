"""
Agent Cache Service - Configuration-Driven Agent Loading and Caching

This service provides:
- Loading agents from database into memory cache
- Fast access to agent configurations
- Automatic cache invalidation on updates
- Direct component loading (skills, tools, MCP, memory, prompt)

An agent is defined by its components:
- SKILLS: What it knows how to do
- TOOLS: What it has available
- MCP: Where resources come from
- MEMORY: What it knows (Cognitive Capital)
- PROMPT: How it acts

@author: NEXUS - Neural Execution Unified System
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass, field
import logging
import asyncio
import json
from uuid import UUID

logger = logging.getLogger(__name__)


@dataclass
class CachedAgent:
    """
    Cached agent configuration.
    
    This is the runtime representation of an agent loaded from database.
    An agent is defined by its components, not by a "type".
    """
    id: str
    name: str
    description: Optional[str] = None
    
    # COMPONENTS - The agent's fundamental building blocks
    # SKILLS: What the agent knows how to do
    skills: List[Dict[str, Any]] = field(default_factory=list)
    
    # TOOLS: What the agent has available
    tools: List[Dict[str, Any]] = field(default_factory=list)
    
    # MCP: Where resources come from
    mcp_servers: List[Dict[str, Any]] = field(default_factory=list)
    
    # MEMORY: Cognitive Capital configuration
    memory_config: Dict[str, Any] = field(default_factory=dict)
    
    # PROMPT: How the agent acts
    prompt_config: Dict[str, Any] = field(default_factory=dict)
    
    # Sub-agents for hierarchical patterns
    sub_agent_ids: List[str] = field(default_factory=list)
    
    # Additional configuration
    config: Dict[str, Any] = field(default_factory=dict)
    extra_config: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    # Legacy fields (for backward compatibility)
    type: Optional[str] = None  # Deprecated
    role: Optional[str] = None  # Deprecated
    goal: Optional[str] = None
    instruction: Optional[str] = None
    model: Optional[str] = None
    
    # Runtime state
    status: str = "active"
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0
    
    def get_skill_ids(self) -> List[str]:
        """Get IDs of all enabled skills"""
        return [s.get("skill_id") for s in self.skills if s.get("enabled", True)]
    
    def get_tool_names(self) -> List[str]:
        """Get names of all enabled tools"""
        return [t.get("tool_name") for t in self.tools if t.get("enabled", True)]
    
    def get_mcp_tools(self) -> Dict[str, List[str]]:
        """Get tools grouped by MCP server"""
        result = {}
        for m in self.mcp_servers:
            if m.get("enabled", True):
                result[m.get("mcp_name")] = m.get("tools", [])
        return result
    
    def has_skill(self, skill_name: str) -> bool:
        """Check if agent has a specific skill"""
        return any(
            s.get("skill_name") == skill_name and s.get("enabled", True)
            for s in self.skills
        )
    
    def has_tool(self, tool_name: str) -> bool:
        """Check if agent has access to a specific tool"""
        return any(
            t.get("tool_name") == tool_name and t.get("enabled", True)
            for t in self.tools
        )
    
    def get_capabilities_summary(self) -> Dict[str, Any]:
        """Get a summary of the agent's capabilities"""
        return {
            "skills_count": len([s for s in self.skills if s.get("enabled", True)]),
            "tools_count": len([t for t in self.tools if t.get("enabled", True)]),
            "mcps_count": len([m for m in self.mcp_servers if m.get("enabled", True)]),
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "skills": self.skills,
            "tools": self.tools,
            "mcp_servers": self.mcp_servers,
            "memory_config": self.memory_config,
            "prompt_config": self.prompt_config,
            "sub_agent_ids": self.sub_agent_ids,
            "config": self.config,
            "extra_config": self.extra_config,
            "tags": self.tags,
            "type": self.type,
            "role": self.role,
            "goal": self.goal,
            "instruction": self.instruction,
            "model": self.model,
            "status": self.status,
            "capabilities": self.get_capabilities_summary(),
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count,
        }


class AgentCacheService:
    """
    Service for caching agents from database.
    
    This service provides:
    - In-memory cache for fast agent access
    - Automatic loading from database
    - Cache invalidation on updates
    - Component-based agent loading
    
    Usage:
        cache = AgentCacheService(db_session)
        await cache.initialize()
        
        # Get agent by ID (from cache or database)
        agent = await cache.get_agent(agent_id)
        
        # Invalidate cache when agent is updated
        await cache.invalidate(agent_id)
    """
    
    _instance: Optional['AgentCacheService'] = None
    
    def __new__(cls, *args, **kwargs) -> 'AgentCacheService':
        """Singleton pattern for global cache access"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, db_session=None, redis_client=None):
        if self._initialized:
            return
            
        self.db = db_session
        self.redis = redis_client
        
        # In-memory cache
        self._cache: Dict[str, CachedAgent] = {}
        
        # Cache statistics
        self._stats = {
            "hits": 0,
            "misses": 0,
            "total_loads": 0,
        }
        
        self._initialized = True
        logger.info("AgentCacheService initialized")
    
    async def initialize(self) -> None:
        """Initialize the cache"""
        logger.info("Agent cache initialized")
    
    async def get_agent(self, agent_id: str) -> Optional[CachedAgent]:
        """
        Get an agent by ID from cache or database.
        
        Args:
            agent_id: The agent's UUID as string
            
        Returns:
            CachedAgent if found, None otherwise
        """
        # Check memory cache first
        if agent_id in self._cache:
            self._stats["hits"] += 1
            agent = self._cache[agent_id]
            agent.last_accessed = datetime.utcnow()
            agent.access_count += 1
            return agent
        
        # Check Redis cache if available
        if self.redis:
            try:
                cached_data = await self.redis.get(f"agent:{agent_id}")
                if cached_data:
                    self._stats["hits"] += 1
                    data = json.loads(cached_data)
                    agent = CachedAgent(**data)
                    self._cache[agent_id] = agent
                    return agent
            except Exception as e:
                logger.warning(f"Redis cache error: {e}")
        
        # Load from database
        self._stats["misses"] += 1
        return await self._load_agent_from_db(agent_id)
    
    async def _load_agent_from_db(self, agent_id: str) -> Optional[CachedAgent]:
        """Load an agent from database and cache it"""
        if not self.db:
            return None
            
        try:
            from src.models.models import Agent
            
            # Convert to UUID if string
            if isinstance(agent_id, str):
                try:
                    agent_uuid = UUID(agent_id)
                except ValueError:
                    logger.warning(f"Invalid agent ID: {agent_id}")
                    return None
            else:
                agent_uuid = agent_id
            
            agent = self.db.query(Agent).filter(Agent.id == agent_uuid).first()
            if not agent:
                return None
            
            # Build cached agent with all components
            cached = CachedAgent(
                id=str(agent.id),
                name=agent.name,
                description=agent.description,
                
                # Components
                skills=agent.skills or [],
                tools=agent.tools or [],
                mcp_servers=agent.mcp_servers or [],
                memory_config=agent.memory_config or {},
                prompt_config=agent.prompt_config or {},
                sub_agent_ids=agent.sub_agent_ids or [],
                
                # Additional config
                config=agent.config or {},
                extra_config=agent.extra_config or {},
                tags=agent.tags or [],
                
                # Legacy fields
                type=agent.type,
                role=agent.role,
                goal=agent.goal,
                instruction=agent.instruction,
                model=agent.model,
            )
            
            # Store in cache
            self._cache[agent_id] = cached
            self._stats["total_loads"] += 1
            
            # Store in Redis if available
            if self.redis:
                try:
                    await self.redis.setex(
                        f"agent:{agent_id}",
                        3600,  # 1 hour TTL
                        json.dumps(cached.to_dict())
                    )
                except Exception as e:
                    logger.warning(f"Redis cache set error: {e}")
            
            return cached
            
        except Exception as e:
            logger.error(f"Error loading agent {agent_id}: {e}")
            return None
    
    async def invalidate(self, agent_id: str) -> bool:
        """
        Invalidate cache for an agent.
        
        Call this when an agent is updated in the database.
        """
        # Remove from memory cache
        if agent_id in self._cache:
            del self._cache[agent_id]
        
        # Remove from Redis cache
        if self.redis:
            try:
                await self.redis.delete(f"agent:{agent_id}")
            except Exception as e:
                logger.warning(f"Redis cache delete error: {e}")
        
        logger.info(f"Invalidated cache for agent {agent_id}")
        return True
    
    async def invalidate_all(self) -> bool:
        """Invalidate all cached agents"""
        self._cache.clear()
        
        if self.redis:
            try:
                keys = await self.redis.keys("agent:*")
                if keys:
                    await self.redis.delete(*keys)
            except Exception as e:
                logger.warning(f"Redis cache clear error: {e}")
        
        logger.info("Invalidated all agent cache")
        return True
    
    async def refresh_configurations(self) -> None:
        """Refresh all cached agents from database"""
        # Clear and reload all cached agents
        agent_ids = list(self._cache.keys())
        self._cache.clear()
        
        for agent_id in agent_ids:
            await self._load_agent_from_db(agent_id)
        
        logger.info("Refreshed all agent configurations")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total if total > 0 else 0
        
        return {
            "memory_cache_size": len(self._cache),
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "hit_rate": hit_rate,
            "total_loads": self._stats["total_loads"],
        }
    
    def set_db_session(self, db_session) -> None:
        """Set database session for queries"""
        self.db = db_session
    
    def set_redis_client(self, redis_client) -> None:
        """Set Redis client for distributed caching"""
        self.redis = redis_client
    
    # ========================================================================
    # DEPRECATED METHODS - Kept for backward compatibility
    # ========================================================================
    
    def get_type(self, type_name: str) -> Optional[Dict[str, Any]]:
        """
        DEPRECATED: Types are no longer stored separately.
        Agent configuration is now component-based.
        """
        logger.warning("get_type() is deprecated. Use agent components instead.")
        return None
    
    def get_role(self, role_name: str) -> Optional[Dict[str, Any]]:
        """
        DEPRECATED: Roles are no longer stored separately.
        Agent configuration is now component-based.
        """
        logger.warning("get_role() is deprecated. Use agent components instead.")
        return None
    
    def get_domain(self, domain_name: str) -> Optional[Dict[str, Any]]:
        """
        DEPRECATED: Domains are no longer stored separately.
        Agent configuration is now component-based.
        """
        logger.warning("get_domain() is deprecated. Use agent components instead.")
        return None
    
    def list_types(self) -> List[Dict[str, Any]]:
        """DEPRECATED: Types are no longer stored separately."""
        logger.warning("list_types() is deprecated.")
        return []
    
    def list_roles(self) -> List[Dict[str, Any]]:
        """DEPRECATED: Roles are no longer stored separately."""
        logger.warning("list_roles() is deprecated.")
        return []
    
    def list_domains(self) -> List[Dict[str, Any]]:
        """DEPRECATED: Domains are no longer stored separately."""
        logger.warning("list_domains() is deprecated.")
        return []


# Global singleton instance
_agent_cache: Optional[AgentCacheService] = None


def get_agent_cache() -> AgentCacheService:
    """Get the global agent cache instance"""
    global _agent_cache
    if _agent_cache is None:
        _agent_cache = AgentCacheService()
    return _agent_cache


def init_agent_cache(db_session=None, redis_client=None) -> AgentCacheService:
    """Initialize the global agent cache"""
    global _agent_cache
    _agent_cache = AgentCacheService(db_session, redis_client)
    return _agent_cache
