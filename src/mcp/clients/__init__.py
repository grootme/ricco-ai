"""
MCP Clients Module

Provides clients for external services including NVIDIA NIM APIs.
"""

from .nim_client import (
    NIMClient,
    NIMConfig,
    NIMEndpoint,
    NIMError,
    NIMAuthenticationError,
    NIMRateLimitError,
    NIMServerError,
    NIMValidationError,
    CircuitBreakerState,
    get_nim_client,
    close_nim_client,
)

__all__ = [
    "NIMClient",
    "NIMConfig",
    "NIMEndpoint",
    "NIMError",
    "NIMAuthenticationError",
    "NIMRateLimitError",
    "NIMServerError",
    "NIMValidationError",
    "CircuitBreakerState",
    "get_nim_client",
    "close_nim_client",
]
