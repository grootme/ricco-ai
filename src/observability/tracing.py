"""
OpenTelemetry Distributed Tracing for RICCO AI

Provides distributed tracing with OpenTelemetry protocol (OTLP)
for integration with Grafana Tempo, Jaeger, and other tracing backends.

Implements:
- Automatic span creation for FastAPI endpoints
- Database query tracing
- LLM API call tracing
- MCP tool invocation tracing
- Cross-service context propagation
"""

import os
import time
import functools
from typing import Optional, Dict, Any, Callable
from contextlib import contextmanager

# OpenTelemetry imports
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator
from opentelemetry.trace import Status, StatusCode, SpanKind
from opentelemetry.util.types import AttributeValue

# OTLP Exporter for Tempo/Jaeger
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter as OTLPGrpcExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as OTLPHttpExporter

# Console exporter for development
from opentelemetry.sdk.trace.export import ConsoleSpanExporter

propagator = TraceContextTextMapPropagator()

# ============================================================================
# Configuration
# ============================================================================

TRACING_CONFIG = {
    "service_name": os.getenv("OTEL_SERVICE_NAME", "ricco-ai"),
    "service_version": os.getenv("OTEL_SERVICE_VERSION", "1.0.0"),
    "otlp_endpoint": os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
    "otlp_protocol": os.getenv("OTEL_EXPORTER_OTLP_PROTOCOL", "grpc"),  # grpc or http
    "enabled": os.getenv("OTEL_TRACES_ENABLED", "true").lower() == "true",
    "sample_rate": float(os.getenv("OTEL_TRACES_SAMPLE_RATE", "1.0")),
    "console_export": os.getenv("OTEL_CONSOLE_EXPORT", "false").lower() == "true",
}


# ============================================================================
# Tracer Provider Setup
# ============================================================================

def create_tracer_provider() -> TracerProvider:
    """Create and configure the tracer provider"""
    
    # Create resource with service info
    resource = Resource.create({
        SERVICE_NAME: TRACING_CONFIG["service_name"],
        SERVICE_VERSION: TRACING_CONFIG["service_version"],
        "deployment.environment": os.getenv("ENVIRONMENT", "development"),
        "service.instance.id": os.getenv("HOSTNAME", "local"),
    })
    
    # Create tracer provider
    provider = TracerProvider(resource=resource)
    
    if TRACING_CONFIG["enabled"]:
        # Add OTLP exporter
        if TRACING_CONFIG["otlp_protocol"] == "grpc":
            otlp_exporter = OTLPGrpcExporter(
                endpoint=TRACING_CONFIG["otlp_endpoint"],
                timeout=10,
            )
        else:
            otlp_exporter = OTLPHttpExporter(
                endpoint=f"{TRACING_CONFIG['otlp_endpoint']}/v1/traces",
                timeout=10,
            )
        
        # Use batch processor for production
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
        
        # Add console exporter for development
        if TRACING_CONFIG["console_export"]:
            provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
    
    return provider


def init_tracing(app=None) -> trace.Tracer:
    """
    Initialize OpenTelemetry tracing
    
    Args:
        app: FastAPI application instance (optional)
        
    Returns:
        Configured tracer instance
    """
    provider = create_tracer_provider()
    trace.set_tracer_provider(provider)
    
    tracer = trace.get_tracer(
        TRACING_CONFIG["service_name"],
        TRACING_CONFIG["service_version"],
    )
    
    if app:
        # Add FastAPI instrumentation if available
        try:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
            FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
        except ImportError:
            pass
    
    return tracer


# Global tracer instance
_tracer: Optional[trace.Tracer] = None


def get_tracer() -> trace.Tracer:
    """Get or create the global tracer"""
    global _tracer
    if _tracer is None:
        _tracer = init_tracing()
    return _tracer


# ============================================================================
# Span Helpers
# ============================================================================

@contextmanager
def span(
    name: str,
    attributes: Optional[Dict[str, AttributeValue]] = None,
    kind: SpanKind = SpanKind.INTERNAL,
):
    """
    Context manager for creating a span
    
    Usage:
        with span("database.query", {"db.table": "users"}):
            # ... code ...
    """
    tracer = get_tracer()
    with tracer.start_as_current_span(name, kind=kind) as s:
        if attributes:
            s.set_attributes(attributes)
        try:
            yield s
        except Exception as e:
            s.set_status(Status(StatusCode.ERROR, str(e)))
            s.record_exception(e)
            raise


def start_span(
    name: str,
    attributes: Optional[Dict[str, AttributeValue]] = None,
    kind: SpanKind = SpanKind.INTERNAL,
) -> trace.Span:
    """
    Start a new span (manual lifecycle management)
    
    Usage:
        span = start_span("llm.request", {"provider": "openai"})
        try:
            # ... code ...
        finally:
            span.end()
    """
    tracer = get_tracer()
    s = tracer.start_span(name, kind=kind)
    if attributes:
        s.set_attributes(attributes)
    return s


def traced(
    name: Optional[str] = None,
    attributes: Optional[Dict[str, AttributeValue]] = None,
    kind: SpanKind = SpanKind.INTERNAL,
):
    """
    Decorator for tracing functions
    
    Usage:
        @traced("agent.execute", {"agent.type": "swe"})
        async def execute_agent():
            ...
    """
    def decorator(func: Callable):
        span_name = name or f"{func.__module__}.{func.__name__}"
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            with span(span_name, attributes, kind):
                return await func(*args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            with span(span_name, attributes, kind):
                return func(*args, **kwargs)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


# ============================================================================
# Domain-Specific Tracing Helpers
# ============================================================================

class LLMSpan:
    """Tracing helpers for LLM operations"""
    
    @staticmethod
    def start_request(
        provider: str,
        model: str,
        operation: str = "chat.completion",
    ) -> trace.Span:
        """Start a span for an LLM API request"""
        return start_span(
            f"llm.{operation}",
            {
                "llm.provider": provider,
                "llm.model": model,
                "llm.operation": operation,
            },
            SpanKind.CLIENT,
        )
    
    @staticmethod
    def record_tokens(
        span: trace.Span,
        input_tokens: int,
        output_tokens: int,
        total_tokens: int,
    ):
        """Record token usage in a span"""
        span.set_attributes({
            "llm.tokens.input": input_tokens,
            "llm.tokens.output": output_tokens,
            "llm.tokens.total": total_tokens,
        })
    
    @staticmethod
    def record_cost(span: trace.Span, cost: float):
        """Record cost in a span"""
        span.set_attribute("llm.cost.usd", cost)


class MCPSpan:
    """Tracing helpers for MCP tool operations"""
    
    @staticmethod
    def start_invocation(
        tool_name: str,
        server_id: str,
    ) -> trace.Span:
        """Start a span for an MCP tool invocation"""
        return start_span(
            f"mcp.tool.{tool_name}",
            {
                "mcp.tool.name": tool_name,
                "mcp.server.id": server_id,
            },
            SpanKind.CLIENT,
        )


class DBSpan:
    """Tracing helpers for database operations"""
    
    @staticmethod
    def start_query(
        database: str,
        operation: str,
        table: Optional[str] = None,
    ) -> trace.Span:
        """Start a span for a database query"""
        attrs = {
            "db.system": database,
            "db.operation": operation,
        }
        if table:
            attrs["db.table"] = table
        return start_span(f"db.{operation}", attrs, SpanKind.CLIENT)


class VectorSpan:
    """Tracing helpers for vector store operations"""
    
    @staticmethod
    def start_operation(
        store_type: str,
        operation: str,
        collection: Optional[str] = None,
    ) -> trace.Span:
        """Start a span for a vector store operation"""
        attrs = {
            "vector.store.type": store_type,
            "vector.operation": operation,
        }
        if collection:
            attrs["vector.collection"] = collection
        return start_span(f"vector.{operation}", attrs)


class AgentSpan:
    """Tracing helpers for agent operations"""
    
    @staticmethod
    def start_execution(
        agent_type: str,
        agent_id: str,
        operation: str = "execute",
    ) -> trace.Span:
        """Start a span for an agent execution"""
        return start_span(
            f"agent.{operation}",
            {
                "agent.type": agent_type,
                "agent.id": agent_id,
            },
        )


# ============================================================================
# Context Propagation
# ============================================================================

def inject_trace_context(headers: Dict[str, str]) -> Dict[str, str]:
    """
    Inject trace context into headers for propagation
    
    Usage:
        headers = inject_trace_context({})
        response = await http_client.get(url, headers=headers)
    """
    propagator.inject(headers)
    return headers


def extract_trace_context(headers: Dict[str, str]) -> Optional[trace.SpanContext]:
    """
    Extract trace context from headers
    
    Usage:
        context = extract_trace_context(request.headers)
        with trace.use_span(context, end_on_exit=False):
            # Process request within the received trace context
    """
    ctx = propagator.extract(headers)
    return ctx


# ============================================================================
# FastAPI Middleware
# ============================================================================

class TracingMiddleware:
    """
    FastAPI middleware for automatic request tracing
    
    Creates a span for each incoming request with:
    - HTTP method and path
    - Status code
    - Request duration
    - Error information if applicable
    """
    
    def __init__(self, app):
        self.app = app
        self.tracer = get_tracer()
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        method = scope["method"]
        path = scope["path"]
        
        # Extract trace context from headers if present
        headers = dict(scope.get("headers", []))
        ctx = propagator.extract({k.decode(): v.decode() for k, v in headers.items()})
        
        with self.tracer.start_as_current_span(
            f"HTTP {method} {path}",
            kind=SpanKind.SERVER,
            context=ctx,
        ) as span:
            span.set_attributes({
                "http.method": method,
                "http.route": path,
                "http.scheme": scope.get("scheme", "http"),
                "http.host": scope.get("server", ["localhost", 80])[0],
            })
            
            # Wrap send to capture status code
            status_code = [200]  # Default
            
            async def wrapped_send(message):
                if message["type"] == "http.response.start":
                    status_code[0] = message["status"]
                    span.set_attribute("http.status_code", status_code[0])
                    if status_code[0] >= 400:
                        span.set_status(Status(StatusCode.ERROR))
                    else:
                        span.set_status(Status(StatusCode.OK))
                await send(message)
            
            try:
                await self.app(scope, receive, wrapped_send)
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise


# ============================================================================
# Initialize on import
# ============================================================================

# Auto-initialize tracer on module import
_tracer = init_tracing()
