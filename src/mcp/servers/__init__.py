"""MCP Servers for NVIDIA Blueprint integration.

This package provides MCP servers for various blueprints:
- Multi-Agent Blueprint Server
- RAG Blueprint Server
- Digital Human Blueprint Server
- Healthcare Blueprint Server
- Industrial Blueprint Server
"""

from .base_server import (
    BaseMCPServer,
    MCPServerConfig,
    MCPToolDefinition,
    ServerStatus,
    TransportType,
)
from .multi_agent_server import MultiAgentMCPServer, multi_agent_server

# Import other servers when they are created
# from .rag_server import RAGMCPServer, rag_server
# from .digital_human_server import DigitalHumanMCPServer, digital_human_server
# from .healthcare_server import HealthcareMCPServer, healthcare_server
# from .industrial_server import IndustrialMCPServer, industrial_server

__all__ = [
    # Base classes
    "BaseMCPServer",
    "MCPServerConfig",
    "MCPToolDefinition",
    "ServerStatus",
    "TransportType",
    # Multi-Agent Server
    "MultiAgentMCPServer",
    "multi_agent_server",
]
