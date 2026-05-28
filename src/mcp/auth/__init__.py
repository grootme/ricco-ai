"""
MCP Authentication Package

Provides authentication and authorization for MCP servers.
"""

from .jwt_auth import (
    MCPAuthenticator,
    MCPAuthConfig,
    AuthToken,
    AuthMethod,
    AuthError,
    TokenRequest,
    TokenResponse,
    create_auth_middleware,
    get_authenticator,
)

# Alias for backward compatibility
JWTAuth = MCPAuthenticator

__all__ = [
    "MCPAuthenticator",
    "JWTAuth",  # Alias
    "MCPAuthConfig",
    "AuthToken",
    "AuthMethod",
    "AuthError",
    "TokenRequest",
    "TokenResponse",
    "create_auth_middleware",
    "get_authenticator",
]
