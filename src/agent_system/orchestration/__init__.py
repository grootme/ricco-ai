"""
Orchestration Layer - Configuration-Driven Agent Orchestration

This module provides orchestration capabilities for coordinating multiple agents.
All orchestration is configurable and follows SOLID principles.
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import uuid
import logging

from ...config.agent_config import get_config
from .. import AgentGroup, AgentProfile, AgentStatus

logger = logging.getLogger(__name__)


class OrchestrationStatus(str, Enum):
    """Orchestration task status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class OrchestrationTask:
    """Orchestration task definition."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    assigned_roles: List[str] = field(default_factory=list)
    status: OrchestrationStatus = OrchestrationStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class SubAgentCoordinator:
    """
    Sub-Agent Coordinator - Coordinates sub-agents for tasks.
    
    Uses configuration to determine which roles to use.
    """
    
    def __init__(self):
        self.config = get_config()
        self._tasks: Dict[str, OrchestrationTask] = {}
    
    def create_task(
        self,
        name: str,
        description: str,
        assigned_roles: Optional[List[str]] = None,
    ) -> OrchestrationTask:
        """Create a new orchestration task."""
        if not assigned_roles:
            # Use configuration to determine roles
            assigned_roles = list(self.config.get_roles().keys())
        
        task = OrchestrationTask(
            name=name,
            description=description,
            assigned_roles=assigned_roles,
        )
        
        self._tasks[task.id] = task
        return task
    
    async def execute_task(
        self,
        task: OrchestrationTask,
        executor: Callable[[str, Dict[str, Any]], Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a task across assigned roles."""
        task.status = OrchestrationStatus.RUNNING
        task.started_at = datetime.utcnow().isoformat()
        
        results = {}
        context = context or {}
        
        try:
            for role_id in task.assigned_roles:
                role_config = self.config.get_role(role_id)
                if role_config:
                    result = await executor(role_id, context)
                    results[role_id] = result
            
            task.status = OrchestrationStatus.COMPLETED
            task.completed_at = datetime.utcnow().isoformat()
            task.result = results
            
        except Exception as e:
            task.status = OrchestrationStatus.FAILED
            task.error = str(e)
            logger.error(f"Task {task.id} failed: {e}")
        
        return {
            "task_id": task.id,
            "status": task.status.value,
            "results": results,
        }
    
    def get_task(self, task_id: str) -> Optional[OrchestrationTask]:
        """Get a task by ID."""
        return self._tasks.get(task_id)


class LeadAgentOrchestrator:
    """
    Lead Agent Orchestrator - Coordinates the lead agent and sub-agents.
    
    Configuration-driven orchestration without hardcoded values.
    """
    
    def __init__(self):
        self.config = get_config()
        self.sub_coordinator = SubAgentCoordinator()
        self._middleware: List[Callable] = []
    
    def add_middleware(self, middleware: Callable) -> None:
        """Add middleware to the orchestration pipeline."""
        self._middleware.append(middleware)
    
    async def orchestrate(
        self,
        query: str,
        domain: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Orchestrate a query across agents.
        
        1. Detect domain (if not specified)
        2. Determine roles to use
        3. Execute across roles
        4. Aggregate results
        """
        context = context or {}
        
        # Detect domain
        if not domain:
            domain, confidence = self.config.detect_domain(query)
        else:
            confidence = 0.8
        
        # Determine roles
        roles = self.config.detect_roles(query)
        
        # Create orchestration task
        task = self.sub_coordinator.create_task(
            name=f"Query: {query[:50]}",
            description=query,
            assigned_roles=roles,
        )
        
        # Execute through middleware
        for middleware in self._middleware:
            query, context = await middleware(query, context)
        
        # Execute task
        async def role_executor(role_id: str, ctx: Dict[str, Any]) -> Dict[str, Any]:
            role_config = self.config.get_role(role_id)
            return {
                "role": role_id,
                "config": role_config,
                "domain": domain,
            }
        
        result = await self.sub_coordinator.execute_task(
            task=task,
            executor=role_executor,
            context=context,
        )
        
        return {
            "domain": domain,
            "confidence": confidence,
            "roles": roles,
            "task_result": result,
        }


class OrchestrationMiddleware:
    """
    Middleware for orchestration pipeline.
    
    Allows configurable processing steps.
    """
    
    def __init__(self):
        self._processors: List[Callable] = []
    
    def add_processor(self, processor: Callable) -> None:
        """Add a processor to the middleware chain."""
        self._processors.append(processor)
    
    async def process(
        self,
        query: str,
        context: Dict[str, Any],
    ) -> tuple:
        """Process query and context through all processors."""
        for processor in self._processors:
            query, context = await processor(query, context)
        return query, context


__all__ = [
    "OrchestrationStatus",
    "OrchestrationTask",
    "SubAgentCoordinator",
    "LeadAgentOrchestrator",
    "OrchestrationMiddleware",
]
