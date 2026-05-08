"""
RICCO AI Core Module

This module provides core functionality:
- Protocols (type-safe interfaces)
- Dependency Injection Container
- Exception handling
- Service bootstrap
- PPCC Cycle (Proper Prompt Chat Cycle)
- Obviousness Context (SMART+R+T Semantic Contract)
"""

from .exceptions import (
    BaseAPIException,
    AgentNotFoundError,
    InvalidParameterError,
    InvalidRequestError,
    InternalServerError,
    RICCOError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
)
from .protocols import (
    # Provider protocols
    AIProviderProtocol,
    AIProviderType,
    EmbeddingProviderProtocol,
    # Agent protocols
    AgentProtocol,
    AgentType,
    MCPAwareAgentProtocol,
    # Service protocols
    MemoryServiceProtocol,
    SessionServiceProtocol,
    # UI protocols
    A2UIProviderProtocol,
    ContextAwareUIProtocol,
    UIContextMode,
    # Context protocols
    ContextProviderProtocol,
    ContextBundleProtocol,
    # Storage protocols
    VectorStoreProtocol,
    CacheProtocol,
    # MCP protocols
    MCPServerProtocol,
    MCPRegistryProtocol,
    # Event protocols
    EventPublisherProtocol,
    EventSubscriberProtocol,
    # DDD protocols
    RepositoryProtocol,
    FactoryProtocol,
)
from .container import (
    Container,
    ServiceLifetime,
    get_container,
    set_container,
    reset_container,
    inject,
    async_inject,
    ServiceProvider,
)
from .obviousness import (
    ObviousnessContext,
    ObviousnessContextBuilder,
    ObviousnessDimension,
    OrganizationalImpact,
    TaskPriority,
)
from .ppcc import (
    PPCCCycle,
    PPCCPhase,
    PPCCState,
    PPCCError,
    AlignmentRequiredError,
    ExecutionBlockedError,
)

__all__ = [
    # Exceptions
    'BaseAPIException',
    'AgentNotFoundError',
    'InvalidParameterError',
    'InvalidRequestError',
    'InternalServerError',
    'RICCOError',
    'ValidationError',
    'AuthenticationError',
    'AuthorizationError',
    # Protocols
    'AIProviderProtocol',
    'AIProviderType',
    'EmbeddingProviderProtocol',
    'AgentProtocol',
    'AgentType',
    'MCPAwareAgentProtocol',
    'MemoryServiceProtocol',
    'SessionServiceProtocol',
    'A2UIProviderProtocol',
    'ContextAwareUIProtocol',
    'UIContextMode',
    'ContextProviderProtocol',
    'ContextBundleProtocol',
    'VectorStoreProtocol',
    'CacheProtocol',
    'MCPServerProtocol',
    'MCPRegistryProtocol',
    'EventPublisherProtocol',
    'EventSubscriberProtocol',
    'RepositoryProtocol',
    'FactoryProtocol',
    # Container
    'Container',
    'ServiceLifetime',
    'get_container',
    'set_container',
    'reset_container',
    'inject',
    'async_inject',
    'ServiceProvider',
    # Obviousness
    'ObviousnessContext',
    'ObviousnessContextBuilder',
    'ObviousnessDimension',
    'OrganizationalImpact',
    'TaskPriority',
    # PPCC
    'PPCCCycle',
    'PPCCPhase',
    'PPCCState',
    'PPCCError',
    'AlignmentRequiredError',
    'ExecutionBlockedError',
]
