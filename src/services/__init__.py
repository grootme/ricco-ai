"""
RICCO AI Services Module

This module provides all services for the RICCO AI platform.
"""

# A2UI Service (consolidated) - Always available
from .a2ui import (
    A2UIService,
    get_a2ui_service,
    ComponentType,
    A2UIComponent,
    A2UIResponse,
    ContextBundle,
    UIContextMode,
)

# Google ADK - Optional dependency
try:
    from .adk.agent_runner import run_agent
    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False
    run_agent = None  # type: ignore

__all__ = [
    # A2UI
    'A2UIService',
    'get_a2ui_service',
    'ComponentType',
    'A2UIComponent',
    'A2UIResponse',
    'ContextBundle',
    'UIContextMode',
    # ADK (optional)
    'run_agent',
    'ADK_AVAILABLE',
]
