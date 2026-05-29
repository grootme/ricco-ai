"""
Reactor Implementations for Hermet Agent

Reactors are automated responses to specific events or threshold breaches.
Each reactor implements a specific reaction logic.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import logging
import json


@dataclass
class ReactorResult:
    """Result of reactor execution"""
    success: bool
    action: str
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "action": self.action,
            "message": self.message,
            "data": self.data,
            "timestamp": self.timestamp,
        }


class BaseReactor(ABC):
    """Base class for all reactors"""
    
    name: str = "base_reactor"
    description: str = "Base reactor class"
    priority: int = 0  # Higher = executed first
    
    def __init__(self):
        self.logger = logging.getLogger(f"hermet.reactor.{self.name}")
        self._execution_count = 0
        self._last_execution: Optional[float] = None
        self._success_count = 0
        self._failure_count = 0
    
    @abstractmethod
    async def execute(self, data: Dict[str, Any]) -> ReactorResult:
        """Execute the reactor action"""
        pass
    
    async def run(self, data: Dict[str, Any]) -> ReactorResult:
        """Run the reactor with tracking"""
        self._execution_count += 1
        self._last_execution = time.time()
        
        try:
            result = await self.execute(data)
            if result.success:
                self._success_count += 1
            else:
                self._failure_count += 1
            return result
        except Exception as e:
            self._failure_count += 1
            self.logger.error(f"Reactor {self.name} failed: {e}")
            return ReactorResult(
                success=False,
                action=self.name,
                message=str(e),
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get reactor statistics"""
        return {
            "name": self.name,
            "execution_count": self._execution_count,
            "success_count": self._success_count,
            "failure_count": self._failure_count,
            "last_execution": self._last_execution,
        }


class ReactorRegistry:
    """Registry for managing reactors"""
    
    def __init__(self):
        self._reactors: Dict[str, BaseReactor] = {}
        self.logger = logging.getLogger("hermet.reactor_registry")
    
    def register(self, name: str, reactor: BaseReactor):
        """Register a reactor"""
        self._reactors[name] = reactor
        self.logger.info(f"Registered reactor: {name}")
    
    def unregister(self, name: str):
        """Unregister a reactor"""
        if name in self._reactors:
            del self._reactors[name]
    
    def get(self, name: str) -> Optional[BaseReactor]:
        """Get a reactor by name"""
        return self._reactors.get(name)
    
    def list_reactors(self) -> List[str]:
        """List all registered reactors"""
        return list(self._reactors.keys())
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all reactors"""
        return {
            name: reactor.get_stats()
            for name, reactor in self._reactors.items()
        }


# ============================================================================
# System Reactors
# ============================================================================

class HighCPUReactor(BaseReactor):
    """React to high CPU usage"""
    
    name = "high_cpu"
    description = "Handles high CPU usage by scaling or notifying"
    priority = 10
    
    async def execute(self, data: Dict[str, Any]) -> ReactorResult:
        cpu_value = data.get("value", 0)
        threshold = data.get("threshold", 80)
        
        self.logger.warning(f"High CPU detected: {cpu_value}% (threshold: {threshold}%)")
        
        actions_taken = []
        
        # Check if we can scale horizontally
        if cpu_value > 90:
            actions_taken.append("alert_ops_team")
            actions_taken.append("suggest_scaling")
        
        # Log to event system
        actions_taken.append("logged_event")
        
        return ReactorResult(
            success=True,
            action=self.name,
            message=f"CPU at {cpu_value}% exceeds threshold {threshold}%",
            data={
                "cpu_percent": cpu_value,
                "threshold": threshold,
                "actions_taken": actions_taken,
            }
        )


class HighMemoryReactor(BaseReactor):
    """React to high memory usage"""
    
    name = "high_memory"
    description = "Handles high memory usage by clearing caches or scaling"
    priority = 10
    
    async def execute(self, data: Dict[str, Any]) -> ReactorResult:
        memory_value = data.get("value", 0)
        threshold = data.get("threshold", 85)
        
        self.logger.warning(f"High memory detected: {memory_value}% (threshold: {threshold}%)")
        
        actions_taken = []
        
        # Suggest cache clearing
        if memory_value > 90:
            actions_taken.append("suggest_cache_clear")
            actions_taken.append("alert_ops_team")
        else:
            actions_taken.append("log_warning")
        
        return ReactorResult(
            success=True,
            action=self.name,
            message=f"Memory at {memory_value}% exceeds threshold {threshold}%",
            data={
                "memory_percent": memory_value,
                "threshold": threshold,
                "actions_taken": actions_taken,
            }
        )


class HighErrorRateReactor(BaseReactor):
    """React to high error rates"""
    
    name = "high_error_rate"
    description = "Handles high error rates by investigating root cause"
    priority = 20
    
    async def execute(self, data: Dict[str, Any]) -> ReactorResult:
        error_rate = data.get("value", 0)
        threshold = data.get("threshold", 5)
        
        self.logger.error(f"High error rate detected: {error_rate}% (threshold: {threshold}%)")
        
        actions_taken = [
            "check_recent_deployments",
            "analyze_error_logs",
            "alert_dev_team",
        ]
        
        if error_rate > 10:
            actions_taken.append("enable_circuit_breaker")
        
        return ReactorResult(
            success=True,
            action=self.name,
            message=f"Error rate at {error_rate}% exceeds threshold {threshold}%",
            data={
                "error_rate": error_rate,
                "threshold": threshold,
                "actions_taken": actions_taken,
            }
        )


class HighLatencyReactor(BaseReactor):
    """React to high latency"""
    
    name = "high_latency"
    description = "Handles high latency by investigating bottlenecks"
    priority = 15
    
    async def execute(self, data: Dict[str, Any]) -> ReactorResult:
        latency = data.get("value", 0)
        threshold = data.get("threshold", 2000)
        
        self.logger.warning(f"High latency detected: {latency}ms (threshold: {threshold}ms)")
        
        actions_taken = [
            "check_database_connections",
            "analyze_slow_queries",
            "check_external_api_latency",
        ]
        
        if latency > 5000:
            actions_taken.append("enable_degraded_mode")
        
        return ReactorResult(
            success=True,
            action=self.name,
            message=f"Latency at {latency}ms exceeds threshold {threshold}ms",
            data={
                "latency_ms": latency,
                "threshold_ms": threshold,
                "actions_taken": actions_taken,
            }
        )


# ============================================================================
# MCP Reactors
# ============================================================================

class MCPHealthReactor(BaseReactor):
    """React to MCP server health issues"""
    
    name = "mcp_health"
    description = "Handles MCP server health issues"
    priority = 25
    
    async def execute(self, data: Dict[str, Any]) -> ReactorResult:
        server_id = data.get("server_id", "unknown")
        healthy = data.get("healthy", True)
        
        self.logger.warning(f"MCP server {server_id} health check: {healthy}")
        
        actions_taken = []
        
        if not healthy:
            actions_taken = [
                "attempt_reconnect",
                "failover_to_backup",
                "alert_ops_team",
            ]
        
        return ReactorResult(
            success=True,
            action=self.name,
            message=f"MCP server {server_id} health: {healthy}",
            data={
                "server_id": server_id,
                "healthy": healthy,
                "actions_taken": actions_taken,
            }
        )


# ============================================================================
# Agent Reactors
# ============================================================================

class AgentHealthReactor(BaseReactor):
    """React to agent health issues"""
    
    name = "agent_health"
    description = "Handles agent health issues"
    priority = 20
    
    async def execute(self, data: Dict[str, Any]) -> ReactorResult:
        agent_type = data.get("agent_type", "unknown")
        error_rate = data.get("error_rate", 0)
        
        self.logger.warning(f"Agent {agent_type} health issue: {error_rate}% error rate")
        
        actions_taken = []
        
        if error_rate > 0.5:
            actions_taken = [
                "restart_agent",
                "clear_agent_cache",
                "log_diagnostics",
            ]
        
        return ReactorResult(
            success=True,
            action=self.name,
            message=f"Agent {agent_type} error rate: {error_rate}%",
            data={
                "agent_type": agent_type,
                "error_rate": error_rate,
                "actions_taken": actions_taken,
            }
        )


# ============================================================================
# Custom Reactors
# ============================================================================

class LLMRateLimitReactor(BaseReactor):
    """React to LLM rate limiting"""
    
    name = "llm_rate_limit"
    description = "Handles LLM rate limiting by switching providers"
    priority = 15
    
    async def execute(self, data: Dict[str, Any]) -> ReactorResult:
        provider = data.get("provider", "unknown")
        model = data.get("model", "unknown")
        
        self.logger.warning(f"LLM rate limit hit: {provider}/{model}")
        
        actions_taken = [
            "switch_to_backup_provider",
            "enable_request_queueing",
            "notify_users_of_delay",
        ]
        
        return ReactorResult(
            success=True,
            action=self.name,
            message=f"Rate limit hit for {provider}/{model}",
            data={
                "provider": provider,
                "model": model,
                "actions_taken": actions_taken,
            }
        )


class DatabaseSlowQueryReactor(BaseReactor):
    """React to slow database queries"""
    
    name = "db_slow_query"
    description = "Handles slow database queries"
    priority = 10
    
    async def execute(self, data: Dict[str, Any]) -> ReactorResult:
        query_time = data.get("query_time", 0)
        query_pattern = data.get("query_pattern", "unknown")
        
        self.logger.warning(f"Slow query detected: {query_time}ms - {query_pattern}")
        
        actions_taken = [
            "log_query_for_analysis",
            "suggest_index_optimization",
            "check_query_plan",
        ]
        
        return ReactorResult(
            success=True,
            action=self.name,
            message=f"Slow query: {query_time}ms",
            data={
                "query_time_ms": query_time,
                "query_pattern": query_pattern,
                "actions_taken": actions_taken,
            }
        )


class QueueOverflowReactor(BaseReactor):
    """React to queue overflow"""
    
    name = "queue_overflow"
    description = "Handles queue overflow by scaling consumers"
    priority = 15
    
    async def execute(self, data: Dict[str, Any]) -> ReactorResult:
        queue_name = data.get("queue_name", "unknown")
        queue_size = data.get("queue_size", 0)
        max_size = data.get("max_size", 10000)
        
        self.logger.warning(f"Queue overflow: {queue_name} at {queue_size}/{max_size}")
        
        actions_taken = [
            "scale_consumers",
            "enable_priority_processing",
            "alert_ops_team",
        ]
        
        return ReactorResult(
            success=True,
            action=self.name,
            message=f"Queue {queue_name} overflow: {queue_size}/{max_size}",
            data={
                "queue_name": queue_name,
                "queue_size": queue_size,
                "max_size": max_size,
                "actions_taken": actions_taken,
            }
        )


# Export all reactors
__all__ = [
    "BaseReactor",
    "ReactorResult",
    "ReactorRegistry",
    "HighCPUReactor",
    "HighMemoryReactor",
    "HighErrorRateReactor",
    "HighLatencyReactor",
    "MCPHealthReactor",
    "AgentHealthReactor",
    "LLMRateLimitReactor",
    "DatabaseSlowQueryReactor",
    "QueueOverflowReactor",
]
