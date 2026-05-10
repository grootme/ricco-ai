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
    from ricco_ai.mcp import ServerRegistry, TokenAwareProxy
    
    # Register servers
    registry = ServerRegistry()
    await registry.register(server_config)
    
    # Execute through proxy
    proxy = TokenAwareProxy(registry=registry)
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
    TokenAwareProxy,
    TokenContext,
    LoadBalancer,
    LoadBalancingStrategy,
    ServerStats,
    CircuitBreaker,
    CircuitState,
    CircuitStats,
)

# Alias for backwards compatibility
MCPProxy = TokenAwareProxy

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
    "TokenAwareProxy",
    "TokenContext",
    "LoadBalancer",
    "LoadBalancingStrategy",
    "ServerStats",
    "CircuitBreaker",
    "CircuitState",
    "CircuitStats",
    # Backwards compatibility
    "MCPProxy",
]
