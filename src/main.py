"""
RICCO AI Service - Main Application
Based on evo-ai with RICCO customizations
"""

import os
import sys
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
def health_check():
    return {
        "status": "healthy",
        "service": settings.API_TITLE,
        "version": settings.API_VERSION,
        "ai_engine": settings.AI_ENGINE
    }
