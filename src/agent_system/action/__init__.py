"""
Action Layer - Configuration-Driven Action Execution

This module provides action execution capabilities for agents.
All actions and skills are loaded from configuration.
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import uuid
import logging

from ...config.agent_config import get_config

logger = logging.getLogger(__name__)


@dataclass
class ActionResult:
    """Result of an action execution."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    action_name: str = ""
    success: bool = False
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class SkillsRegistry:
    """
    Skills Registry - Configuration-driven skills management.
    
    Skills are loaded from configuration, not hardcoded.
    """
    
    def __init__(self):
        self.config = get_config()
        self._skills: Dict[str, Dict[str, Any]] = {}
        self._load_skills()
    
    def _load_skills(self) -> None:
        """Load skills from configuration."""
        # Skills are derived from role configurations
        roles = self.config.get_roles()
        
        for role_id, role_config in roles.items():
            skills = role_config.get("skills", [])
            for skill in skills:
                if skill not in self._skills:
                    self._skills[skill] = {
                        "name": skill,
                        "role": role_id,
                        "category": role_config.get("elegant_name", role_id.upper()),
                    }
        
        logger.info(f"Loaded {len(self._skills)} skills from configuration")
    
    def get_skill(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """Get a skill by name."""
        return self._skills.get(skill_name)
    
    def get_all_skills(self) -> Dict[str, Dict[str, Any]]:
        """Get all skills."""
        return self._skills
    
    def get_skills_for_role(self, role_id: str) -> List[str]:
        """Get all skills for a specific role."""
        role_config = self.config.get_role(role_id)
        if role_config:
            return role_config.get("skills", [])
        return []


class MCPRegistry:
    """
    MCP Registry - Configuration-driven MCP server management.
    
    MCP servers are loaded from configuration based on domains.
    """
    
    def __init__(self):
        self.config = get_config()
        self._servers: Dict[str, Dict[str, Any]] = {}
        self._load_servers()
    
    def _load_servers(self) -> None:
        """Load MCP servers from configuration."""
        domains = self.config.get_domains()
        
        for domain_id, domain_config in domains.items():
            servers = domain_config.get("mcp_servers", [])
            for server in servers:
                if server not in self._servers:
                    self._servers[server] = {
                        "name": server,
                        "domain": domain_id,
                        "domain_name": domain_config.get("name", ""),
                    }
        
        logger.info(f"Loaded {len(self._servers)} MCP servers from configuration")
    
    def get_server(self, server_name: str) -> Optional[Dict[str, Any]]:
        """Get an MCP server by name."""
        return self._servers.get(server_name)
    
    def get_all_servers(self) -> Dict[str, Dict[str, Any]]:
        """Get all MCP servers."""
        return self._servers
    
    def get_servers_for_domain(self, domain_id: str) -> List[str]:
        """Get all MCP servers for a specific domain."""
        domain_config = self.config.get_domain(domain_id)
        if domain_config:
            return domain_config.get("mcp_servers", [])
        return []


class ActionExecutor:
    """
    Action Executor - Executes actions for agents.
    
    Uses SkillsRegistry and MCPRegistry for configuration-driven execution.
    """
    
    def __init__(
        self,
        skills_registry: Optional[SkillsRegistry] = None,
        mcp_registry: Optional[MCPRegistry] = None,
    ):
        self.skills_registry = skills_registry or SkillsRegistry()
        self.mcp_registry = mcp_registry or MCPRegistry()
        self._action_handlers: Dict[str, Callable] = {}
    
    def register_handler(self, action_name: str, handler: Callable) -> None:
        """Register a handler for an action."""
        self._action_handlers[action_name] = handler
    
    async def execute(
        self,
        action_name: str,
        params: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> ActionResult:
        """Execute an action."""
        start_time = datetime.utcnow()
        params = params or {}
        
        try:
            # Check if there's a registered handler
            if action_name in self._action_handlers:
                result = await self._action_handlers[action_name](params, context)
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                
                return ActionResult(
                    action_name=action_name,
                    success=True,
                    result=result,
                    execution_time=execution_time,
                )
            
            # Check if it's a skill
            skill = self.skills_registry.get_skill(action_name)
            if skill:
                # Execute skill (placeholder for actual implementation)
                result = {"skill": action_name, "executed": True, "params": params}
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                
                return ActionResult(
                    action_name=action_name,
                    success=True,
                    result=result,
                    execution_time=execution_time,
                )
            
            # Action not found
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            return ActionResult(
                action_name=action_name,
                success=False,
                error=f"Action '{action_name}' not found",
                execution_time=execution_time,
            )
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"Error executing action {action_name}: {e}")
            return ActionResult(
                action_name=action_name,
                success=False,
                error=str(e),
                execution_time=execution_time,
            )


__all__ = [
    "ActionResult",
    "SkillsRegistry",
    "MCPRegistry",
    "ActionExecutor",
]
