"""
Circuit Breaker Pattern for MCP Servers.

This module implements the circuit breaker pattern to prevent cascade failures
and provide resilience when calling MCP servers.

Adapted from genui for RICCO AI integration.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
import logging
from functools import wraps

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"        # Normal operation, requests pass through
    OPEN = "open"           # Failing, requests are rejected
    HALF_OPEN = "half_open" # Testing if service recovered


@dataclass
class CircuitStats:
    """Statistics for a circuit breaker."""
    server_id: str
    
    # State
    state: CircuitState = CircuitState.CLOSED
    state_changed_at: datetime = field(default_factory=datetime.utcnow)
    
    # Failure tracking
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    total_failures: int = 0
    total_successes: int = 0
    total_requests: int = 0
    
    # Time window tracking
    failures_in_window: int = 0
    requests_in_window: int = 0
    window_start: datetime = field(default_factory=datetime.utcnow)
    
    # Half-open state
    half_open_requests: int = 0
    half_open_successes: int = 0
    
    # Timing
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    last_request_time: Optional[datetime] = None
    
    # Metrics
    total_time_open_seconds: float = 0.0
    total_state_changes: int = 0
    
    def get_failure_rate(self) -> float:
        """Calculate failure rate in current window."""
        if self.requests_in_window == 0:
            return 0.0
        return (self.failures_in_window / self.requests_in_window) * 100
    
    def reset_window(self) -> None:
        """Reset the sliding window counters."""
        self.failures_in_window = 0
        self.requests_in_window = 0
        self.window_start = datetime.utcnow()


class CircuitBreaker:
    """
    Circuit breaker for protecting MCP server calls.
    
    Implements the circuit breaker pattern with:
    - Configurable failure thresholds
    - Automatic recovery (half-open state)
    - Per-server circuit tracking
    - Metrics and monitoring
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 3,
        timeout_seconds: int = 60,
        half_open_max_requests: int = 5,
        failure_rate_threshold: float = 50.0,
        minimum_requests: int = 10,
    ):
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout_seconds = timeout_seconds
        self.half_open_max_requests = half_open_max_requests
        self.failure_rate_threshold = failure_rate_threshold
        self.minimum_requests = minimum_requests
        
        self._circuits: Dict[str, CircuitStats] = {}
        self._lock = asyncio.Lock()
        
        # Callbacks
        self._on_state_change_callbacks: List[Callable] = []
        self._on_open_callbacks: List[Callable] = []
        self._on_close_callbacks: List[Callable] = []
        self._on_half_open_callbacks: List[Callable] = []
    
    def register_server(self, server_id: str) -> None:
        """Register a server with the circuit breaker."""
        if server_id not in self._circuits:
            self._circuits[server_id] = CircuitStats(server_id=server_id)
            logger.debug(f"Registered circuit breaker for server {server_id}")
    
    def unregister_server(self, server_id: str) -> None:
        """Unregister a server from the circuit breaker."""
        self._circuits.pop(server_id, None)
        logger.debug(f"Unregistered circuit breaker for server {server_id}")
    
    def get_state(self, server_id: str) -> CircuitState:
        """Get the current circuit state for a server."""
        circuit = self._circuits.get(server_id)
        return circuit.state if circuit else CircuitState.CLOSED
    
    def get_stats(self, server_id: str) -> Optional[CircuitStats]:
        """Get circuit breaker statistics for a server."""
        return self._circuits.get(server_id)
    
    def is_call_allowed(self, server_id: str) -> bool:
        """
        Check if a call is allowed for the given server.
        
        Returns True if the call should proceed, False if it should be rejected.
        """
        circuit = self._circuits.get(server_id)
        if not circuit:
            return True
        
        self._update_state(server_id, circuit)
        
        if circuit.state == CircuitState.CLOSED:
            return True
        elif circuit.state == CircuitState.OPEN:
            return False
        elif circuit.state == CircuitState.HALF_OPEN:
            return circuit.half_open_requests < self.half_open_max_requests
        
        return True
    
    def record_success(self, server_id: str) -> None:
        """Record a successful call."""
        circuit = self._circuits.get(server_id)
        if not circuit:
            return
        
        circuit.total_successes += 1
        circuit.total_requests += 1
        circuit.consecutive_successes += 1
        circuit.consecutive_failures = 0
        circuit.requests_in_window += 1
        circuit.last_success_time = datetime.utcnow()
        circuit.last_request_time = datetime.utcnow()
        
        if circuit.state == CircuitState.HALF_OPEN:
            circuit.half_open_successes += 1
            
            if circuit.half_open_successes >= self.success_threshold:
                self._transition_to_closed(server_id, circuit)
        
        logger.debug(f"Circuit breaker success for {server_id}: state={circuit.state.value}")
    
    def record_failure(self, server_id: str) -> None:
        """Record a failed call."""
        circuit = self._circuits.get(server_id)
        if not circuit:
            return
        
        circuit.total_failures += 1
        circuit.total_requests += 1
        circuit.consecutive_failures += 1
        circuit.consecutive_successes = 0
        circuit.failures_in_window += 1
        circuit.requests_in_window += 1
        circuit.last_failure_time = datetime.utcnow()
        circuit.last_request_time = datetime.utcnow()
        
        if circuit.state == CircuitState.HALF_OPEN:
            self._transition_to_open(server_id, circuit)
        elif circuit.state == CircuitState.CLOSED:
            if self._should_open_circuit(circuit):
                self._transition_to_open(server_id, circuit)
        
        logger.warning(
            f"Circuit breaker failure for {server_id}: "
            f"consecutive={circuit.consecutive_failures}, "
            f"rate={circuit.get_failure_rate():.1f}%, "
            f"state={circuit.state.value}"
        )
    
    def _should_open_circuit(self, circuit: CircuitStats) -> bool:
        """Determine if the circuit should open."""
        if circuit.consecutive_failures >= self.failure_threshold:
            return True
        
        if (circuit.requests_in_window >= self.minimum_requests and
            circuit.get_failure_rate() >= self.failure_rate_threshold):
            return True
        
        return False
    
    def _update_state(self, server_id: str, circuit: CircuitStats) -> None:
        """Update circuit state based on time."""
        now = datetime.utcnow()
        
        if circuit.state == CircuitState.OPEN:
            time_since_open = (now - circuit.state_changed_at).total_seconds()
            if time_since_open >= self.timeout_seconds:
                self._transition_to_half_open(server_id, circuit)
        
        if circuit.state == CircuitState.CLOSED:
            window_duration = timedelta(seconds=self.timeout_seconds)
            if now - circuit.window_start > window_duration:
                circuit.reset_window()
    
    def _transition_to_open(self, server_id: str, circuit: CircuitStats) -> None:
        """Transition circuit to OPEN state."""
        old_state = circuit.state
        circuit.state = CircuitState.OPEN
        circuit.state_changed_at = datetime.utcnow()
        circuit.half_open_requests = 0
        circuit.half_open_successes = 0
        circuit.total_state_changes += 1
        
        logger.warning(f"Circuit OPENED for server {server_id}")
        self._execute_callbacks(self._on_open_callbacks, server_id, circuit)
        self._execute_callbacks(self._on_state_change_callbacks, server_id, old_state, CircuitState.OPEN)
    
    def _transition_to_closed(self, server_id: str, circuit: CircuitStats) -> None:
        """Transition circuit to CLOSED state."""
        old_state = circuit.state
        circuit.state = CircuitState.CLOSED
        circuit.state_changed_at = datetime.utcnow()
        circuit.consecutive_failures = 0
        circuit.half_open_requests = 0
        circuit.half_open_successes = 0
        circuit.total_state_changes += 1
        circuit.reset_window()
        
        logger.info(f"Circuit CLOSED for server {server_id}")
        self._execute_callbacks(self._on_close_callbacks, server_id, circuit)
        self._execute_callbacks(self._on_state_change_callbacks, server_id, old_state, CircuitState.CLOSED)
    
    def _transition_to_half_open(self, server_id: str, circuit: CircuitStats) -> None:
        """Transition circuit to HALF_OPEN state."""
        old_state = circuit.state
        circuit.state = CircuitState.HALF_OPEN
        circuit.state_changed_at = datetime.utcnow()
        circuit.half_open_requests = 0
        circuit.half_open_successes = 0
        circuit.total_state_changes += 1
        
        logger.info(f"Circuit HALF-OPEN for server {server_id}")
        self._execute_callbacks(self._on_half_open_callbacks, server_id, circuit)
        self._execute_callbacks(self._on_state_change_callbacks, server_id, old_state, CircuitState.HALF_OPEN)
    
    def force_open(self, server_id: str) -> None:
        """Force the circuit open (manual override)."""
        circuit = self._circuits.get(server_id)
        if circuit and circuit.state != CircuitState.OPEN:
            self._transition_to_open(server_id, circuit)
    
    def force_close(self, server_id: str) -> None:
        """Force the circuit closed (manual reset)."""
        circuit = self._circuits.get(server_id)
        if circuit and circuit.state != CircuitState.CLOSED:
            self._transition_to_closed(server_id, circuit)
    
    def reset(self, server_id: str) -> None:
        """Reset circuit breaker state for a server."""
        if server_id in self._circuits:
            self._circuits[server_id] = CircuitStats(server_id=server_id)
            logger.info(f"Circuit breaker reset for server {server_id}")
    
    def reset_all(self) -> None:
        """Reset all circuit breakers."""
        for server_id in self._circuits:
            self._circuits[server_id] = CircuitStats(server_id=server_id)
        logger.info("All circuit breakers reset")
    
    def on_state_change(self, callback: Callable) -> None:
        """Register a callback for state changes."""
        self._on_state_change_callbacks.append(callback)
    
    def on_open(self, callback: Callable) -> None:
        """Register a callback for circuit opening."""
        self._on_open_callbacks.append(callback)
    
    def on_close(self, callback: Callable) -> None:
        """Register a callback for circuit closing."""
        self._on_close_callbacks.append(callback)
    
    def on_half_open(self, callback: Callable) -> None:
        """Register a callback for circuit half-open transition."""
        self._on_half_open_callbacks.append(callback)
    
    def _execute_callbacks(self, callbacks: List[Callable], *args) -> None:
        """Execute registered callbacks."""
        for callback in callbacks:
            try:
                callback(*args)
            except Exception as e:
                logger.exception(f"Callback error: {e}")
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all circuit breaker states."""
        return {
            "servers": {
                server_id: {
                    "state": circuit.state.value,
                    "consecutive_failures": circuit.consecutive_failures,
                    "consecutive_successes": circuit.consecutive_successes,
                    "total_requests": circuit.total_requests,
                    "failure_rate": circuit.get_failure_rate(),
                    "state_changed_at": circuit.state_changed_at.isoformat(),
                    "last_failure": circuit.last_failure_time.isoformat() if circuit.last_failure_time else None,
                    "last_success": circuit.last_success_time.isoformat() if circuit.last_success_time else None,
                }
                for server_id, circuit in self._circuits.items()
            },
            "config": {
                "failure_threshold": self.failure_threshold,
                "success_threshold": self.success_threshold,
                "timeout_seconds": self.timeout_seconds,
                "failure_rate_threshold": self.failure_rate_threshold,
            },
        }


class CircuitOpenError(Exception):
    """Exception raised when circuit is open."""
    pass


def circuit_breaker_protected(
    circuit_breaker: CircuitBreaker,
    server_id_param: str = "server_id",
):
    """
    Decorator to protect a function with a circuit breaker.
    
    Usage:
        @circuit_breaker_protected(circuit_breaker, server_id_param="server_id")
        async def call_server(server_id: str, ...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            server_id = kwargs.get(server_id_param)
            if not server_id:
                raise ValueError(f"Missing {server_id_param} parameter")
            
            if not circuit_breaker.is_call_allowed(server_id):
                raise CircuitOpenError(
                    f"Circuit breaker is open for server {server_id}"
                )
            
            try:
                result = await func(*args, **kwargs)
                circuit_breaker.record_success(server_id)
                return result
            except Exception as e:
                circuit_breaker.record_failure(server_id)
                raise
        
        return wrapper
    return decorator
