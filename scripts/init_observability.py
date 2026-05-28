#!/usr/bin/env python3
"""
RICCO AI - Observability Initialization Script

Initializes the complete observability stack:
- OpenTelemetry Tracing
- Prometheus Metrics
- Health State Machine
- Structured Logging

This implements the Resilience-Aware Architecture DNA pattern.
"""

import os
import sys
import logging
from typing import Optional

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def setup_logging(
    level: str = "INFO",
    json_format: bool = False,
    include_trace: bool = True,
) -> logging.Logger:
    """
    Setup structured logging with optional trace context
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        json_format: Use JSON format for logs
        include_trace: Include trace context in logs
        
    Returns:
        Configured logger
    """
    import json
    from datetime import datetime
    
    # Configure root logger
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    class StructuredFormatter(logging.Formatter):
        """Custom formatter that outputs JSON logs"""
        
        def format(self, record):
            log_entry = {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
            }
            
            # Add trace context if available
            if include_trace:
                try:
                    from opentelemetry import trace
                    span = trace.get_current_span()
                    if span and span.get_span_context():
                        ctx = span.get_span_context()
                        log_entry["trace_id"] = format(ctx.trace_id, '032x')
                        log_entry["span_id"] = format(ctx.span_id, '016x')
                except ImportError:
                    pass
            
            # Add extra fields
            if hasattr(record, 'extra'):
                log_entry.update(record.extra)
            
            # Add exception info if present
            if record.exc_info:
                log_entry["exception"] = self.formatException(record.exc_info)
            
            return json.dumps(log_entry) if json_format else (
                f"[{log_entry['timestamp']}] {log_entry['level']:8} "
                f"{log_entry['logger']}: {log_entry['message']}"
            )
    
    # Configure handlers
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredFormatter())
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)
    
    # Configure RICCO logger
    ricco_logger = logging.getLogger("ricco")
    ricco_logger.setLevel(log_level)
    
    return ricco_logger


def init_observability(
    app=None,
    service_name: Optional[str] = None,
    otlp_endpoint: Optional[str] = None,
    enable_tracing: bool = True,
    enable_metrics: bool = True,
    enable_health: bool = True,
    log_level: str = "INFO",
) -> dict:
    """
    Initialize the complete observability stack
    
    Args:
        app: FastAPI application instance
        service_name: Service name for tracing
        otlp_endpoint: OTLP endpoint URL
        enable_tracing: Enable distributed tracing
        enable_metrics: Enable Prometheus metrics
        enable_health: Enable health state machine
        log_level: Logging level
        
    Returns:
        Dictionary with initialized components
    """
    components = {}
    
    # Set environment variables if provided
    if service_name:
        os.environ["OTEL_SERVICE_NAME"] = service_name
    if otlp_endpoint:
        os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = otlp_endpoint
    
    # 1. Setup Logging
    print("🔧 Setting up structured logging...")
    logger = setup_logging(
        level=log_level,
        json_format=os.getenv("LOG_FORMAT", "text") == "json",
    )
    components["logger"] = logger
    logger.info("Structured logging initialized")
    
    # 2. Initialize Tracing
    if enable_tracing:
        print("🔧 Initializing OpenTelemetry tracing...")
        try:
            from src.observability.tracing import init_tracing, TracingMiddleware
            
            tracer = init_tracing(app)
            components["tracer"] = tracer
            
            if app:
                app.add_middleware(TracingMiddleware)
            
            logger.info("OpenTelemetry tracing initialized")
        except ImportError as e:
            logger.warning(f"OpenTelemetry not available: {e}")
    
    # 3. Initialize Metrics
    if enable_metrics:
        print("🔧 Setting up Prometheus metrics...")
        try:
            from src.monitoring.metrics import init_metrics, health_checker
            
            if app:
                init_metrics(app, version=os.getenv("APP_VERSION", "1.0.0"))
            
            components["health_checker"] = health_checker
            logger.info("Prometheus metrics initialized")
        except ImportError as e:
            logger.warning(f"Prometheus metrics not available: {e}")
    
    # 4. Initialize Health State Machine
    if enable_health:
        print("🔧 Setting up Health State Machine...")
        try:
            from src.observability.health_state_machine import (
                get_system_health,
                ComponentHealthMonitor,
                create_database_check,
                create_redis_check,
            )
            
            system_health = get_system_health()
            components["system_health"] = system_health
            logger.info("Health State Machine initialized")
        except ImportError as e:
            logger.warning(f"Health State Machine not available: {e}")
    
    print("✅ Observability stack initialized successfully!")
    
    return components


def register_health_checks(components: dict, config: dict):
    """
    Register health checks for system components
    
    Args:
        components: Dictionary of system components
        config: Configuration dictionary
    """
    from src.observability.health_state_machine import (
        ComponentHealthMonitor,
        create_database_check,
        create_redis_check,
        create_http_check,
        get_system_health,
    )
    
    system_health = get_system_health()
    
    # Database health check
    if "database" in components:
        db_monitor = ComponentHealthMonitor(
            name="database",
            check_func=create_database_check(components["database"]),
            check_interval=30.0,
            failure_threshold=3,
        )
        system_health.register_component(db_monitor)
        print("  ✓ Database health check registered")
    
    # Redis health check
    if "redis" in components:
        redis_monitor = ComponentHealthMonitor(
            name="redis",
            check_func=create_redis_check(components["redis"]),
            check_interval=15.0,
            failure_threshold=3,
        )
        system_health.register_component(redis_monitor)
        print("  ✓ Redis health check registered")
    
    # Vector store health check
    if "vector_store" in components:
        from src.observability.health_state_machine import create_vector_store_check
        vector_monitor = ComponentHealthMonitor(
            name="vector_store",
            check_func=create_vector_store_check(
                components["vector_store"],
                config.get("vector_collection", "default")
            ),
            check_interval=60.0,
        )
        system_health.register_component(vector_monitor)
        print("  ✓ Vector store health check registered")
    
    # External API health checks
    external_apis = config.get("external_apis", {})
    for name, url in external_apis.items():
        api_monitor = ComponentHealthMonitor(
            name=f"api_{name}",
            check_func=create_http_check(url),
            check_interval=60.0,
            failure_threshold=2,
        )
        system_health.register_component(api_monitor)
        print(f"  ✓ {name} API health check registered")


async def start_health_monitoring():
    """Start all health monitors"""
    from src.observability.health_state_machine import get_system_health
    
    system_health = get_system_health()
    await system_health.start_all()
    print("✅ Health monitoring started")


async def stop_health_monitoring():
    """Stop all health monitors"""
    from src.observability.health_state_machine import get_system_health
    
    system_health = get_system_health()
    await system_health.stop_all()
    print("✅ Health monitoring stopped")


# CLI entry point
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize RICCO AI Observability")
    parser.add_argument("--service-name", default="ricco-ai", help="Service name")
    parser.add_argument("--otlp-endpoint", default="http://localhost:4317", help="OTLP endpoint")
    parser.add_argument("--log-level", default="INFO", help="Log level")
    parser.add_argument("--disable-tracing", action="store_true", help="Disable tracing")
    parser.add_argument("--disable-metrics", action="store_true", help="Disable metrics")
    parser.add_argument("--disable-health", action="store_true", help="Disable health checks")
    
    args = parser.parse_args()
    
    components = init_observability(
        service_name=args.service_name,
        otlp_endpoint=args.otlp_endpoint,
        enable_tracing=not args.disable_tracing,
        enable_metrics=not args.disable_metrics,
        enable_health=not args.disable_health,
        log_level=args.log_level,
    )
    
    print("\n📊 Observability Components:")
    for name, component in components.items():
        print(f"  - {name}: {type(component).__name__}")
