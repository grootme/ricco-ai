"""
RICCO AI Services Module

This module provides all services for the RICCO AI platform.
"""

from .adk.agent_runner import run_agent

# A2UI Service (consolidated)
from .a2ui import (
    A2UIService,
    get_a2ui_service,
    ComponentType,
    A2UIComponent,
    A2UIResponse,
    ContextBundle,
    UIContextMode,
)

__all__ = [
    # ADK
    'run_agent',
    # A2UI
    'A2UIService',
    'get_a2ui_service',
    'ComponentType',
    'A2UIComponent',
    'A2UIResponse',
    'ContextBundle',
    'UIContextMode',
]
