"""
RICCO AI Observability Module

Provides comprehensive observability capabilities:
- Distributed Tracing (OpenTelemetry)
- Health State Machine
- Metrics (Prometheus)
- Logging (Structured)

Part of the Resilience-Aware Architecture DNA.
"""

from .tracing import (
    get_tracer,
    init_tracing,
    span,
    start_span,
    traced,
    TracingMiddleware,
    LLMSpan,
    MCPSpan,
    DBSpan,
    VectorSpan,
    AgentSpan,
    inject_trace_context,
    extract_trace_context,
)

from .health_state_machine import (
    HealthState,
    AlertSeverity,
    HealthCheckResult,
    HealthAlert,
    ComponentHealthMonitor,
    SystemHealthStateMachine,
    get_system_health,
    create_database_check,
    create_redis_check,
    create_http_check,
    create_vector_store_check,
)

__all__ = [
    # Tracing
    "get_tracer",
    "init_tracing",
    "span",
    "start_span",
    "traced",
    "TracingMiddleware",
    "LLMSpan",
    "MCPSpan",
    "DBSpan",
    "VectorSpan",
    "AgentSpan",
    "inject_trace_context",
    "extract_trace_context",
    # Health State Machine
    "HealthState",
    "AlertSeverity",
    "HealthCheckResult",
    "HealthAlert",
    "ComponentHealthMonitor",
    "SystemHealthStateMachine",
    "get_system_health",
    "create_database_check",
    "create_redis_check",
    "create_http_check",
    "create_vector_store_check",
]
