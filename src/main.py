"""
RICCO AI Service - Main Application
Based on evo-ai with RICCO customizations
"""

import os
import sys
import time
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.config.database import engine, Base
from src.config.settings import settings
from src.utils.logger import setup_logger
from src.utils.otel import init_otel

# Service providers
from src.services.service_providers import session_service
from src.services.service_providers import artifacts_service
from src.services.service_providers import memory_service

# API routes
import src.api.auth_routes
import src.api.admin_routes
import src.api.chat_routes
import src.api.session_routes
import src.api.agent_routes
import src.api.mcp_server_routes
import src.api.tool_routes
import src.api.client_routes
import src.api.a2a_routes
import src.api.nexus_routes  # NEXUS Super Agent routes

# Add root to path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

logger = setup_logger(__name__)

# ===========================================================================
# Production Validation - Fail Fast
# ===========================================================================
if settings.PRODUCTION_MODE:
    errors = settings.validate_production_secrets()
    if errors:
        error_msg = f"Production validation failed: {', '.join(errors)}"
        logger.critical(error_msg)
        raise RuntimeError(error_msg)
    logger.info("Production validation passed")

app = FastAPI(
    title=settings.API_TITLE,
    description="""
    # RICCO AI - Intelligence Layer
    
    Multi-agent orchestration platform based on **evo-ai** with **A2UI SDK** integration.
    
    ## Features
    - Multi-Agent Orchestration (LLM, A2A, Sequential, Parallel, Loop, Workflow, Task)
    - A2A Protocol for agent interoperability
    - A2UI for dynamic UI generation
    - MCP (Model Context Protocol) support
    - RICCO ID integration for unified auth
    
    ## Agent Types
    - **LLM Agent**: Language model interaction
    - **A2A Agent**: Agent-to-Agent protocol
    - **Sequential Agent**: Sequential execution
    - **Parallel Agent**: Concurrent execution
    - **Loop Agent**: Iterative execution
    - **Workflow Agent**: LangGraph workflows
    - **Task Agent**: Structured task execution
    """,
    version=settings.API_VERSION,
    redirect_slashes=False,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===========================================================================
# Rate Limiting Middleware
# ===========================================================================
rate_limiter = None
if settings.RATE_LIMIT_ENABLED:
    try:
        from src.middleware.rate_limiter import (
            setup_rate_limiting,
            RateLimitConfig,
        )
        
        # Configure route-specific rate limits
        route_configs = {
            "/api/v1/auth": RateLimitConfig(
                requests=settings.RATE_LIMIT_AUTH_REQUESTS,
                window_seconds=60,
                block_duration=300  # 5 min block after exceeding
            ),
            "/api/v1/chat": RateLimitConfig(
                requests=settings.RATE_LIMIT_CHAT_REQUESTS,
                window_seconds=60
            ),
            "/api/v1/stream": RateLimitConfig(
                requests=10,
                window_seconds=60
            ),
        }
        
        # Setup Redis URL if available
        redis_url = None
        if settings.REDIS_HOST:
            redis_url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}"
        
        rate_limiter = setup_rate_limiting(
            app=app,
            redis_url=redis_url,
            default_requests=settings.RATE_LIMIT_DEFAULT_REQUESTS,
            default_window=settings.RATE_LIMIT_DEFAULT_WINDOW,
            route_configs=route_configs,
            excluded_paths=["/health", "/docs", "/openapi.json", "/", "/metrics"]
        )
        logger.info("Rate limiting enabled")
    except ImportError as e:
        logger.warning(f"Rate limiting disabled: {e}")

# ===========================================================================
# Prometheus Metrics
# ===========================================================================
if settings.PROMETHEUS_ENABLED:
    try:
        from src.monitoring.metrics import init_metrics, health_checker
        
        # Initialize metrics collection
        init_metrics(app, version=settings.API_VERSION)
        
        # Register health checks with real dependency verification
        async def check_database():
            """Real PostgreSQL health check."""
            try:
                from sqlalchemy import text
                with engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                return {"status": "healthy", "type": "postgresql"}
            except Exception as e:
                logger.error(f"Database health check failed: {e}")
                return {"status": "unhealthy", "error": str(e), "type": "postgresql"}
        
        async def check_redis():
            """Real Redis health check."""
            try:
                import redis
                r = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    password=settings.REDIS_PASSWORD,
                    ssl=settings.REDIS_SSL,
                    socket_timeout=5
                )
                r.ping()
                return {"status": "healthy", "type": "redis"}
            except Exception as e:
                logger.error(f"Redis health check failed: {e}")
                return {"status": "unhealthy", "error": str(e), "type": "redis"}
        
        health_checker.register_check("database", check_database)
        health_checker.register_check("redis", check_redis)
        
        logger.info("Prometheus metrics enabled at /metrics")
    except ImportError as e:
        logger.warning(f"Prometheus metrics disabled: {e}")

# Static files
static_dir = Path("static")
if not static_dir.exists():
    static_dir.mkdir(parents=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Database
Base.metadata.create_all(bind=engine)

API_PREFIX = "/api/v1"

# Routers
app.include_router(src.api.auth_routes.router, prefix=API_PREFIX)
app.include_router(src.api.admin_routes.router, prefix=API_PREFIX)
app.include_router(src.api.mcp_server_routes.router, prefix=API_PREFIX)
app.include_router(src.api.tool_routes.router, prefix=API_PREFIX)
app.include_router(src.api.client_routes.router, prefix=API_PREFIX)
app.include_router(src.api.chat_routes.router, prefix=API_PREFIX)
app.include_router(src.api.session_routes.router, prefix=API_PREFIX)
app.include_router(src.api.agent_routes.router, prefix=API_PREFIX)
app.include_router(src.api.a2a_routes.router, prefix=API_PREFIX)
app.include_router(src.api.nexus_routes.router, prefix=API_PREFIX)  # NEXUS Super Agent

# OpenTelemetry
init_otel()


@app.get("/")
def read_root():
    return {
        "service": "RICCO AI",
        "version": settings.API_VERSION,
        "based_on": {
            "evo_ai": "https://github.com/EvolutionAPI/evo-ai",
            "a2ui": "https://github.com/google/A2UI"
        },
        "docs": "/docs",
        "integrations": {
            "ricco_id": settings.RICCO_ID_URL,
            "openrouter": "configured" if settings.OPENROUTER_API_KEY else "not configured"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint with detailed status"""
    from src.monitoring.metrics import health_checker
    
    health_status = await health_checker.check_health()
    
    # Get 4 DNA status
    dna_status = {
        "deerflow": "available",
        "gentle_ai": "available",
        "engram": "available",
        "gentle_pi": "available"
    }
    
    try:
        from ricco_ai.deerflow.core import WorkflowEngine
        dna_status["deerflow"] = "operational"
    except ImportError:
        dna_status["deerflow"] = "unavailable"
    
    try:
        from ricco_ai.gentle_ai.behavior import BehaviorEngine
        dna_status["gentle_ai"] = "operational"
    except ImportError:
        dna_status["gentle_ai"] = "unavailable"
    
    try:
        from ricco_ai.engram.store import EngramStore
        dna_status["engram"] = "operational"
    except ImportError:
        dna_status["engram"] = "unavailable"
    
    try:
        from ricco_ai.gentle_pi.orchestrator import GentlePiOrchestrator
        dna_status["gentle_pi"] = "operational"
    except ImportError:
        dna_status["gentle_pi"] = "unavailable"
    
    return {
        "status": health_status["status"],
        "service": settings.API_TITLE,
        "version": settings.API_VERSION,
        "ai_engine": settings.AI_ENGINE,
        "checks": health_status["checks"],
        "dna_status": dna_status,
        "rate_limiting": "enabled" if settings.RATE_LIMIT_ENABLED else "disabled",
        "monitoring": "enabled" if settings.MONITORING_ENABLED else "disabled",
        "production_mode": settings.PRODUCTION_MODE
    }
