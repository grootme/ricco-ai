"""
Database Seeds for RICCO AI.

This package provides seed data for database-managed configuration.
"""

from .mcp_servers import MCP_SERVER_SEEDS
from .agents import AGENT_SEEDS
from .context_providers import CONTEXT_PROVIDER_SEEDS
from .a2ui_components import A2UI_COMPONENT_SEEDS

__all__ = [
    "MCP_SERVER_SEEDS",
    "AGENT_SEEDS",
    "CONTEXT_PROVIDER_SEEDS",
    "A2UI_COMPONENT_SEEDS",
]
