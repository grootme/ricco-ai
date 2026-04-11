"""
Load Balancer for MCP Servers.

This module implements various load balancing strategies for distributing
MCP requests across multiple server instances.

Adapted from genui for RICCO AI integration.
"""

import hashlib
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class LoadBalancingStrategy(str, Enum):
    """Available load balancing strategies."""
    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_CONNECTIONS = "least_connections"
    WEIGHTED_LEAST_CONNECTIONS = "weighted_least_connections"
    LEAST_RESPONSE_TIME = "least_response_time"
    RANDOM = "random"
    CONSISTENT_HASH = "consistent_hash"
    PRIORITY = "priority"
    ADAPTIVE = "adaptive"


@dataclass
class ServerStats:
    """Statistics for a server in the load balancer."""
    server_id: str
    weight: int = 100
    current_weight: int = 0
    connections: int = 0
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_latency_ms: float = 0.0
    last_selected: Optional[datetime] = None
    registration_time: datetime = field(default_factory=datetime.utcnow)
    
    # Slow start tracking
    slow_start_progress: float = 0.0
    slow_start_start_time: Optional[datetime] = None
    
    def get_effective_weight(self) -> int:
        """Get effective weight considering slow start."""
        if self.slow_start_progress < 1.0:
            return int(self.weight * self.slow_start_progress)
        return self.weight
    
    def get_avg_latency(self) -> float:
        """Get average latency in ms."""
        if self.total_requests == 0:
            return 0.0
        return self.total_latency_ms / self.total_requests
    
    def get_success_rate(self) -> float:
        """Get success rate (0-100)."""
        if self.total_requests == 0:
            return 100.0
        return (self.successful_requests / self.total_requests) * 100
    
    def get_score(self) -> float:
        """Calculate a score for adaptive load balancing."""
        if self.total_requests == 0:
            return 100.0
        
        latency_score = max(0, 100 - (self.get_avg_latency() / 10))
        success_score = self.get_success_rate()
        
        return (latency_score * 0.4 + success_score * 0.6)


class LoadBalancingAlgorithm(ABC):
    """Abstract base class for load balancing algorithms."""
    
    @abstractmethod
    def select(
        self,
        servers: List[Any],
        stats: Dict[str, ServerStats],
        **kwargs,
    ) -> Optional[Any]:
        """Select a server from the candidates."""
        pass
    
    @abstractmethod
    def update_after_request(
        self,
        server_id: str,
        stats: Dict[str, ServerStats],
        success: bool,
        latency_ms: float,
    ) -> None:
        """Update stats after a request completes."""
        pass


class RoundRobinAlgorithm(LoadBalancingAlgorithm):
    """Round-robin load balancing."""
    
    def __init__(self):
        self._current_index = 0
    
    def select(
        self,
        servers: List[Any],
        stats: Dict[str, ServerStats],
        **kwargs,
    ) -> Optional[Any]:
        if not servers:
            return None
        
        selected = servers[self._current_index % len(servers)]
        self._current_index += 1
        return selected
    
    def update_after_request(
        self,
        server_id: str,
        stats: Dict[str, ServerStats],
        success: bool,
        latency_ms: float,
    ) -> None:
        stat = stats.get(server_id)
        if stat:
            stat.total_requests += 1
            stat.total_latency_ms += latency_ms
            if success:
                stat.successful_requests += 1
            else:
                stat.failed_requests += 1
            stat.last_selected = datetime.utcnow()


class WeightedRoundRobinAlgorithm(LoadBalancingAlgorithm):
    """Weighted round-robin load balancing."""
    
    def select(
        self,
        servers: List[Any],
        stats: Dict[str, ServerStats],
        **kwargs,
    ) -> Optional[Any]:
        if not servers:
            return None
        
        best_server = None
        best_weight = -1
        
        for server in servers:
            server_id = getattr(server, 'server_id', str(id(server)))
            stat = stats.get(server_id)
            if stat:
                effective_weight = stat.get_effective_weight()
                stat.current_weight += effective_weight
                
                if best_server is None or stat.current_weight > best_weight:
                    best_weight = stat.current_weight
                    best_server = server
        
        if best_server:
            best_id = getattr(best_server, 'server_id', str(id(best_server)))
            best_stat = stats.get(best_id)
            if best_stat:
                total_weight = sum(
                    stats.get(
                        getattr(s, 'server_id', str(id(s))),
                        ServerStats(server_id=getattr(s, 'server_id', str(id(s))))
                    ).get_effective_weight()
                    for s in servers
                )
                best_stat.current_weight -= total_weight
        
        return best_server
    
    def update_after_request(
        self,
        server_id: str,
        stats: Dict[str, ServerStats],
        success: bool,
        latency_ms: float,
    ) -> None:
        stat = stats.get(server_id)
        if stat:
            stat.total_requests += 1
            stat.total_latency_ms += latency_ms
            if success:
                stat.successful_requests += 1
            else:
                stat.failed_requests += 1
            stat.last_selected = datetime.utcnow()


class LeastConnectionsAlgorithm(LoadBalancingAlgorithm):
    """Least connections load balancing."""
    
    def select(
        self,
        servers: List[Any],
        stats: Dict[str, ServerStats],
        **kwargs,
    ) -> Optional[Any]:
        if not servers:
            return None
        
        best_server = None
        least_connections = float('inf')
        
        for server in servers:
            server_id = getattr(server, 'server_id', str(id(server)))
            stat = stats.get(server_id)
            connections = stat.connections if stat else 0
            if connections < least_connections:
                least_connections = connections
                best_server = server
        
        if best_server:
            best_id = getattr(best_server, 'server_id', str(id(best_server)))
            best_stat = stats.get(best_id)
            if best_stat:
                best_stat.connections += 1
        
        return best_server
    
    def update_after_request(
        self,
        server_id: str,
        stats: Dict[str, ServerStats],
        success: bool,
        latency_ms: float,
    ) -> None:
        stat = stats.get(server_id)
        if stat:
            stat.connections = max(0, stat.connections - 1)
            stat.total_requests += 1
            stat.total_latency_ms += latency_ms
            if success:
                stat.successful_requests += 1
            else:
                stat.failed_requests += 1
            stat.last_selected = datetime.utcnow()


class AdaptiveAlgorithm(LoadBalancingAlgorithm):
    """Adaptive load balancing that considers multiple factors."""
    
    def __init__(
        self,
        latency_weight: float = 0.3,
        success_weight: float = 0.3,
        connection_weight: float = 0.2,
        health_weight: float = 0.2,
    ):
        self.latency_weight = latency_weight
        self.success_weight = success_weight
        self.connection_weight = connection_weight
        self.health_weight = health_weight
    
    def select(
        self,
        servers: List[Any],
        stats: Dict[str, ServerStats],
        **kwargs,
    ) -> Optional[Any]:
        if not servers:
            return None
        
        best_server = None
        best_score = float('inf')
        
        for server in servers:
            server_id = getattr(server, 'server_id', str(id(server)))
            stat = stats.get(server_id, ServerStats(server_id=server_id))
            health_score = getattr(server, 'get_health_score', lambda: 100)()
            
            latency_factor = stat.get_avg_latency() / 1000.0
            success_factor = 1.0 - (stat.get_success_rate() / 100.0)
            connection_factor = stat.connections / 100.0
            health_factor = 1.0 - (health_score / 100.0)
            
            score = (
                latency_factor * self.latency_weight +
                success_factor * self.success_weight +
                connection_factor * self.connection_weight +
                health_factor * self.health_weight
            )
            
            if score < best_score:
                best_score = score
                best_server = server
        
        return best_server
    
    def update_after_request(
        self,
        server_id: str,
        stats: Dict[str, ServerStats],
        success: bool,
        latency_ms: float,
    ) -> None:
        stat = stats.get(server_id)
        if stat:
            stat.total_requests += 1
            stat.total_latency_ms += latency_ms
            if success:
                stat.successful_requests += 1
            else:
                stat.failed_requests += 1
            stat.last_selected = datetime.utcnow()


class LoadBalancer:
    """
    Main load balancer class.
    
    Provides load balancing across MCP server instances with multiple
    algorithms and statistics tracking.
    """
    
    _algorithms: Dict[LoadBalancingStrategy, type] = {
        LoadBalancingStrategy.ROUND_ROBIN: RoundRobinAlgorithm,
        LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN: WeightedRoundRobinAlgorithm,
        LoadBalancingStrategy.LEAST_CONNECTIONS: LeastConnectionsAlgorithm,
        LoadBalancingStrategy.ADAPTIVE: AdaptiveAlgorithm,
    }
    
    def __init__(
        self,
        strategy: LoadBalancingStrategy = LoadBalancingStrategy.ROUND_ROBIN,
        health_score_threshold: float = 50.0,
        slow_start_duration_seconds: int = 60,
    ):
        self.strategy = strategy
        self.health_score_threshold = health_score_threshold
        self.slow_start_duration_seconds = slow_start_duration_seconds
        self._algorithm = self._create_algorithm(strategy)
        self._stats: Dict[str, ServerStats] = {}
        self._servers: Dict[str, Any] = {}
    
    def _create_algorithm(self, strategy: LoadBalancingStrategy) -> LoadBalancingAlgorithm:
        """Create a load balancing algorithm instance."""
        algorithm_class = self._algorithms.get(strategy)
        if not algorithm_class:
            logger.warning(f"Unknown strategy {strategy}, defaulting to round_robin")
            return RoundRobinAlgorithm()
        return algorithm_class()
    
    def set_strategy(self, strategy: LoadBalancingStrategy) -> None:
        """Change the load balancing strategy."""
        self.strategy = strategy
        self._algorithm = self._create_algorithm(strategy)
    
    def add_server(self, server: Any) -> None:
        """Add a server to the load balancer pool."""
        server_id = getattr(server, 'server_id', str(id(server)))
        self._servers[server_id] = server
        if server_id not in self._stats:
            metadata = getattr(server, 'metadata', None)
            weight = getattr(metadata, 'weight', 100) if metadata else 100
            self._stats[server_id] = ServerStats(
                server_id=server_id,
                weight=weight,
                slow_start_start_time=datetime.utcnow(),
            )
        logger.debug(f"Added server {server_id} to load balancer")
    
    def remove_server(self, server_id: str) -> None:
        """Remove a server from the load balancer pool."""
        self._servers.pop(server_id, None)
        logger.debug(f"Removed server {server_id} from load balancer")
    
    def select_server(
        self,
        servers: Optional[List[Any]] = None,
        tool_name: Optional[str] = None,
        request: Optional[Any] = None,
    ) -> Optional[Any]:
        """
        Select a server for the next request.
        
        Args:
            servers: Optional list of candidate servers
            tool_name: Tool being requested
            request: Full request object
            
        Returns:
            Selected server or None if no servers available
        """
        candidate_servers = servers or list(self._servers.values())
        
        if not candidate_servers:
            return None
        
        # Filter out unhealthy servers
        healthy_servers = [
            s for s in candidate_servers
            if getattr(s, 'get_health_score', lambda: 100)() >= self.health_score_threshold
        ]
        
        if not healthy_servers:
            logger.warning("No healthy servers available, falling back to all servers")
            healthy_servers = candidate_servers
        
        # Update slow start progress
        self._update_slow_start(healthy_servers)
        
        selected = self._algorithm.select(
            healthy_servers,
            self._stats,
            tool_name=tool_name,
            request=request,
        )
        
        if selected:
            server_id = getattr(selected, 'server_id', str(id(selected)))
            logger.debug(f"Selected server {server_id} using {self.strategy}")
        
        return selected
    
    def _update_slow_start(self, servers: List[Any]) -> None:
        """Update slow start progress for new servers."""
        now = datetime.utcnow()
        duration = self.slow_start_duration_seconds
        
        for server in servers:
            server_id = getattr(server, 'server_id', str(id(server)))
            stat = self._stats.get(server_id)
            if stat and stat.slow_start_start_time and stat.slow_start_progress < 1.0:
                elapsed = (now - stat.slow_start_start_time).total_seconds()
                stat.slow_start_progress = min(1.0, elapsed / duration)
    
    def record_request(
        self,
        server_id: str,
        success: bool,
        latency_ms: float,
    ) -> None:
        """Record the result of a request for statistics."""
        self._algorithm.update_after_request(
            server_id,
            self._stats,
            success,
            latency_ms,
        )
    
    def get_server_stats(self, server_id: str) -> Optional[ServerStats]:
        """Get statistics for a specific server."""
        return self._stats.get(server_id)
    
    def get_all_stats(self) -> Dict[str, ServerStats]:
        """Get statistics for all servers."""
        return self._stats.copy()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of load balancer state."""
        return {
            "strategy": self.strategy.value,
            "total_servers": len(self._servers),
            "server_stats": {
                server_id: {
                    "total_requests": stat.total_requests,
                    "success_rate": stat.get_success_rate(),
                    "avg_latency_ms": stat.get_avg_latency(),
                    "connections": stat.connections,
                    "effective_weight": stat.get_effective_weight(),
                }
                for server_id, stat in self._stats.items()
            },
        }
