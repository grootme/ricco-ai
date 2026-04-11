"""
MCP Registry & Proxy Module for RICCO AI.

This module provides the MCP (Model Context Protocol) infrastructure for RICCO AI,
including server registration, discovery, and request routing.

Components:
-----------
- Registry: Server and tool registration with health monitoring
- Proxy: Token-aware routing with load balancing and circuit breaking

Example:
--------
    from ricco_ai.mcp import ServerRegistry, MCPProxy
    
    # Register servers
    registry = ServerRegistry()
    await registry.register(server_config)
    
    # Execute through proxy
    proxy = MCPProxy(registry=registry)
    response = await proxy.execute(request)
"""

from .registry import (
    ServerRegistry,
    ToolsRegistry,
    MCPServer,
    MCPServerCreate,
    MCPServerUpdate,
    MCPServerSummary,
    MCPCategory,
    TransportType,
    HealthStatus,
    ServerCapability,
    ServerMetadata,
    MCPTool,
    MCPToolCreate,
    MCPToolSummary,
    ToolParameter,
    ToolRiskLevel,
)
from .proxy import (
    MCPProxy,
    LoadBalancer,
    LoadBalancingStrategy,
    CircuitBreaker,
    CircuitState,
    TokenAwareProxy,
)

__version__ = "1.0.0"

__all__ = [
    # Registry
    "ServerRegistry",
    "ToolsRegistry",
    "MCPServer",
    "MCPServerCreate",
    "MCPServerUpdate",
    "MCPServerSummary",
    "MCPCategory",
    "TransportType",
    "HealthStatus",
    "ServerCapability",
    "ServerMetadata",
    "MCPTool",
    "MCPToolCreate",
    "MCPToolSummary",
    "ToolParameter",
    "ToolRiskLevel",
    # Proxy
    "MCPProxy",
    "LoadBalancer",
    "LoadBalancingStrategy",
    "CircuitBreaker",
    "CircuitState",
    "TokenAwareProxy",
]
