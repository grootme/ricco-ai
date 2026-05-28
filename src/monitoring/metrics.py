"""
Prometheus Metrics for RICCO AI
Comprehensive metrics collection for monitoring and observability
"""

import time
from typing import Dict, Any, Optional, Callable
from functools import wraps
from contextlib import contextmanager

from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    Info,
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST,
    REGISTRY,
)
from prometheus_client.middleware import PrometheusMiddleware


# Create a custom registry for RICCO AI metrics
RICCO_REGISTRY = CollectorRegistry()

# ============================================================================
# HTTP Metrics
# ============================================================================

HTTP_REQUESTS_TOTAL = Counter(
    "ricco_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
    registry=RICCO_REGISTRY,
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "ricco_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=RICCO_REGISTRY,
)

HTTP_REQUESTS_IN_PROGRESS = Gauge(
    "ricco_http_requests_in_progress",
    "Number of HTTP requests currently being processed",
    ["method", "endpoint"],
    registry=RICCO_REGISTRY,
)

# ============================================================================
# Agent Metrics
# ============================================================================

AGENT_REQUESTS_TOTAL = Counter(
    "ricco_agent_requests_total",
    "Total agent requests",
    ["agent_type", "agent_id", "status"],
    registry=RICCO_REGISTRY,
)

AGENT_EXECUTION_DURATION_SECONDS = Histogram(
    "ricco_agent_execution_duration_seconds",
    "Agent execution duration in seconds",
    ["agent_type", "agent_id"],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
    registry=RICCO_REGISTRY,
)

AGENT_ACTIVE_SESSIONS = Gauge(
    "ricco_agent_active_sessions",
    "Number of active agent sessions",
    ["agent_type"],
    registry=RICCO_REGISTRY,
)

AGENT_MEMORY_USAGE_BYTES = Gauge(
    "ricco_agent_memory_usage_bytes",
    "Memory usage by agent in bytes",
    ["agent_id"],
    registry=RICCO_REGISTRY,
)

# ============================================================================
# MCP Metrics
# ============================================================================

MCP_TOOL_INVOCATIONS_TOTAL = Counter(
    "ricco_mcp_tool_invocations_total",
    "Total MCP tool invocations",
    ["tool_name", "server_id", "status"],
    registry=RICCO_REGISTRY,
)

MCP_TOOL_DURATION_SECONDS = Histogram(
    "ricco_mcp_tool_duration_seconds",
    "MCP tool execution duration in seconds",
    ["tool_name", "server_id"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=RICCO_REGISTRY,
)

MCP_SERVER_CONNECTIONS = Gauge(
    "ricco_mcp_server_connections",
    "Number of active MCP server connections",
    ["server_id", "server_type"],
    registry=RICCO_REGISTRY,
)

MCP_SERVER_HEALTH = Gauge(
    "ricco_mcp_server_health",
    "MCP server health status (1=healthy, 0=unhealthy)",
    ["server_id"],
    registry=RICCO_REGISTRY,
)

# ============================================================================
# Rate Limiting Metrics
# ============================================================================

RATE_LIMIT_TOTAL = Counter(
    "ricco_rate_limit_total",
    "Total rate limit checks",
    ["route", "result"],  # result: allowed, blocked, exceeded
    registry=RICCO_REGISTRY,
)

RATE_LIMIT_ACTIVE_BLOCKS = Gauge(
    "ricco_rate_limit_active_blocks",
    "Number of currently blocked clients",
    ["route"],
    registry=RICCO_REGISTRY,
)

# ============================================================================
# LLM/AI Provider Metrics
# ============================================================================

LLM_REQUESTS_TOTAL = Counter(
    "ricco_llm_requests_total",
    "Total LLM API requests",
    ["provider", "model", "status"],
    registry=RICCO_REGISTRY,
)

LLM_TOKENS_USED = Counter(
    "ricco_llm_tokens_used_total",
    "Total tokens used",
    ["provider", "model", "type"],  # type: input, output
    registry=RICCO_REGISTRY,
)

LLM_REQUEST_DURATION_SECONDS = Histogram(
    "ricco_llm_request_duration_seconds",
    "LLM API request duration in seconds",
    ["provider", "model"],
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0],
    registry=RICCO_REGISTRY,
)

LLM_COST_TOTAL = Counter(
    "ricco_llm_cost_total_dollars",
    "Total cost in dollars",
    ["provider", "model"],
    registry=RICCO_REGISTRY,
)

# ============================================================================
# Vector Store Metrics
# ============================================================================

VECTOR_STORE_OPERATIONS_TOTAL = Counter(
    "ricco_vector_store_operations_total",
    "Total vector store operations",
    ["store_type", "operation", "status"],
    registry=RICCO_REGISTRY,
)

VECTOR_STORE_OPERATION_DURATION_SECONDS = Histogram(
    "ricco_vector_store_operation_duration_seconds",
    "Vector store operation duration in seconds",
    ["store_type", "operation"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
    registry=RICCO_REGISTRY,
)

VECTOR_STORE_DOCUMENTS = Gauge(
    "ricco_vector_store_documents_total",
    "Total documents in vector store",
    ["store_type", "collection"],
    registry=RICCO_REGISTRY,
)

# ============================================================================
# Queue/Event Metrics
# ============================================================================

QUEUE_MESSAGES_TOTAL = Counter(
    "ricco_queue_messages_total",
    "Total queue messages processed",
    ["queue_name", "status"],
    registry=RICCO_REGISTRY,
)

QUEUE_SIZE = Gauge(
    "ricco_queue_size",
    "Current queue size",
    ["queue_name"],
    registry=RICCO_REGISTRY,
)

QUEUE_PROCESSING_TIME_SECONDS = Histogram(
    "ricco_queue_processing_time_seconds",
    "Queue message processing time in seconds",
    ["queue_name"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
    registry=RICCO_REGISTRY,
)

# ============================================================================
# Database Metrics
# ============================================================================

DB_CONNECTIONS_ACTIVE = Gauge(
    "ricco_db_connections_active",
    "Number of active database connections",
    ["database"],
    registry=RICCO_REGISTRY,
)

DB_QUERY_DURATION_SECONDS = Histogram(
    "ricco_db_query_duration_seconds",
    "Database query duration in seconds",
    ["database", "operation"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
    registry=RICCO_REGISTRY,
)

DB_ERRORS_TOTAL = Counter(
    "ricco_db_errors_total",
    "Total database errors",
    ["database", "error_type"],
    registry=RICCO_REGISTRY,
)

# ============================================================================
# System Metrics
# ============================================================================

SYSTEM_INFO = Info(
    "ricco_system",
    "RICCO AI system information",
    registry=RICCO_REGISTRY,
)

SYSTEM_START_TIME = Gauge(
    "ricco_system_start_time_seconds",
    "System start time in unix timestamp",
    registry=RICCO_REGISTRY,
)

SYSTEM_UPTIME_SECONDS = Gauge(
    "ricco_system_uptime_seconds",
    "System uptime in seconds",
    registry=RICCO_REGISTRY,
)


# ============================================================================
# Helper Functions and Decorators
# ============================================================================

def track_http_request(method: str, endpoint: str, status_code: int, duration: float):
    """Track HTTP request metrics"""
    HTTP_REQUESTS_TOTAL.labels(
        method=method,
        endpoint=endpoint,
        status_code=str(status_code)
    ).inc()
    
    HTTP_REQUEST_DURATION_SECONDS.labels(
        method=method,
        endpoint=endpoint
    ).observe(duration)


def track_agent_execution(agent_type: str, agent_id: str):
    """Decorator to track agent execution metrics"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                AGENT_REQUESTS_TOTAL.labels(
                    agent_type=agent_type,
                    agent_id=agent_id,
                    status=status
                ).inc()
                AGENT_EXECUTION_DURATION_SECONDS.labels(
                    agent_type=agent_type,
                    agent_id=agent_id
                ).observe(duration)
        return wrapper
    return decorator


def track_mcp_tool(tool_name: str, server_id: str):
    """Decorator to track MCP tool execution"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                MCP_TOOL_INVOCATIONS_TOTAL.labels(
                    tool_name=tool_name,
                    server_id=server_id,
                    status=status
                ).inc()
                MCP_TOOL_DURATION_SECONDS.labels(
                    tool_name=tool_name,
                    server_id=server_id
                ).observe(duration)
        return wrapper
    return decorator


def track_llm_request(provider: str, model: str):
    """Context manager for tracking LLM requests"""
    @contextmanager
    def context():
        start_time = time.time()
        status = "success"
        try:
            yield
        except Exception:
            status = "error"
            raise
        finally:
            duration = time.time() - start_time
            LLM_REQUESTS_TOTAL.labels(
                provider=provider,
                model=model,
                status=status
            ).inc()
            LLM_REQUEST_DURATION_SECONDS.labels(
                provider=provider,
                model=model
            ).observe(duration)
    return context()


def record_llm_tokens(provider: str, model: str, input_tokens: int, output_tokens: int):
    """Record LLM token usage"""
    LLM_TOKENS_USED.labels(provider=provider, model=model, type="input").inc(input_tokens)
    LLM_TOKENS_USED.labels(provider=provider, model=model, type="output").inc(output_tokens)


def record_llm_cost(provider: str, model: str, cost: float):
    """Record LLM cost"""
    LLM_COST_TOTAL.labels(provider=provider, model=model).inc(cost)


def track_vector_store_operation(store_type: str, operation: str):
    """Decorator to track vector store operations"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                VECTOR_STORE_OPERATIONS_TOTAL.labels(
                    store_type=store_type,
                    operation=operation,
                    status=status
                ).inc()
                VECTOR_STORE_OPERATION_DURATION_SECONDS.labels(
                    store_type=store_type,
                    operation=operation
                ).observe(duration)
        return wrapper
    return decorator


def track_db_query(database: str, operation: str):
    """Decorator to track database queries"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                DB_QUERY_DURATION_SECONDS.labels(
                    database=database,
                    operation=operation
                ).observe(duration)
        return wrapper
    return decorator


# ============================================================================
# Metrics Endpoint
# ============================================================================

from fastapi import Response
from fastapi.routing import APIRoute


class MetricsRoute(APIRoute):
    """Custom route class that tracks metrics for all endpoints"""
    
    def get_route_handler(self):
        original_route_handler = super().get_route_handler()
        
        async def custom_route_handler(request):
            # Track in-progress requests
            endpoint = request.url.path
            method = request.method
            
            HTTP_REQUESTS_IN_PROGRESS.labels(
                method=method,
                endpoint=endpoint
            ).inc()
            
            start_time = time.time()
            status_code = 200
            
            try:
                response = await original_route_handler(request)
                status_code = response.status_code
                return response
            except Exception as e:
                status_code = 500
                raise
            finally:
                duration = time.time() - start_time
                
                HTTP_REQUESTS_IN_PROGRESS.labels(
                    method=method,
                    endpoint=endpoint
                ).dec()
                
                track_http_request(method, endpoint, status_code, duration)
        
        return custom_route_handler


async def metrics_endpoint():
    """FastAPI endpoint to expose Prometheus metrics"""
    from fastapi import Response
    
    # Update uptime
    SYSTEM_UPTIME_SECONDS.set(time.time() - SYSTEM_START_TIME._value._value if SYSTEM_START_TIME._value._value else 0)
    
    return Response(
        content=generate_latest(RICCO_REGISTRY),
        media_type=CONTENT_TYPE_LATEST,
    )


def init_metrics(app, version: str = "1.0.0"):
    """
    Initialize metrics collection for a FastAPI application
    
    Args:
        app: FastAPI application instance
        version: Application version
    """
    import os
    import platform
    
    # Set system info
    SYSTEM_INFO.info({
        "version": version,
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "hostname": platform.node(),
    })
    
    # Set start time
    SYSTEM_START_TIME.set(time.time())
    
    # Add metrics endpoint
    from fastapi import Response
    
    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint"""
        SYSTEM_UPTIME_SECONDS.set(time.time() - SYSTEM_START_TIME._value._value)
        return Response(
            content=generate_latest(RICCO_REGISTRY),
            media_type=CONTENT_TYPE_LATEST,
        )
    
    return app


# ============================================================================
# Health Check with Metrics
# ============================================================================

class HealthChecker:
    """Health checker with metrics integration"""
    
    def __init__(self):
        self._checks: Dict[str, Callable] = {}
    
    def register_check(self, name: str, check_func: Callable):
        """Register a health check function"""
        self._checks[name] = check_func
    
    async def check_health(self) -> Dict[str, Any]:
        """Run all health checks"""
        results = {
            "status": "healthy",
            "checks": {},
            "timestamp": time.time()
        }
        
        for name, check_func in self._checks.items():
            try:
                check_result = await check_func() if asyncio.iscoroutinefunction(check_func) else check_func()
                results["checks"][name] = {
                    "status": "healthy" if check_result else "unhealthy",
                    "details": check_result if isinstance(check_result, dict) else None
                }
                
                # Update MCP server health gauge if applicable
                if name.startswith("mcp_"):
                    MCP_SERVER_HEALTH.labels(server_id=name).set(1 if check_result else 0)
                    
            except Exception as e:
                results["checks"][name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
                results["status"] = "unhealthy"
                
                if name.startswith("mcp_"):
                    MCP_SERVER_HEALTH.labels(server_id=name).set(0)
        
        return results


# Global health checker instance
health_checker = HealthChecker()


import asyncio
