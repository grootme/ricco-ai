"""
Core Protocols and Interfaces for RICCO AI
Implements Protocol Pattern (Structural Typing) for loose coupling

This module defines the contracts that services must implement,
enabling dependency injection and easy testing/mocking.

Consolidated: Enums moved to src/shared/enums.py for OCP compliance.
"""

from typing import Protocol, Dict, Any, List, Optional, AsyncIterator, runtime_checkable
from abc import abstractmethod
from datetime import datetime

# Import consolidated enums from single source of truth
try:
    from src.shared.enums import (
        AIProviderType,
        AgentType,
        UIContextMode,
    )
except ImportError:
    # Fallback for direct imports
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from shared.enums import (
        AIProviderType,
        AgentType,
        UIContextMode,
    )


@runtime_checkable
class AIProviderProtocol(Protocol):
    """Protocol for AI providers - enables Strategy Pattern"""
    
    @property
    def provider_type(self) -> AIProviderType:
        """Return the provider type"""
        ...
    
    @property
    def is_initialized(self) -> bool:
        """Check if provider is initialized"""
        ...
    
    async def initialize(self) -> None:
        """Initialize the provider"""
        ...
    
    async def generate_response(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate a response from the AI"""
        ...
    
    async def generate_stream(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[str]:
        """Generate a streaming response"""
        ...
    
    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding vector for text"""
        ...
    
    async def health_check(self) -> bool:
        """Check provider health"""
        ...


@runtime_checkable
class EmbeddingProviderProtocol(Protocol):
    """Protocol for embedding providers"""
    
    async def embed(self, text: str) -> List[float]:
        """Generate embedding for single text"""
        ...
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        ...
    
    def get_dimension(self) -> int:
        """Get embedding dimension"""
        ...


# =============================================================================
# Agent Protocols
# =============================================================================

# AgentType imported from src.shared.enums


@runtime_checkable
class AgentProtocol(Protocol):
    """Protocol for all agents - enables polymorphism"""
    
    @property
    def agent_id(self) -> str:
        """Unique agent identifier"""
        ...
    
    @property
    def agent_type(self) -> AgentType:
        """Agent type"""
        ...
    
    @property
    def name(self) -> str:
        """Agent name"""
        ...
    
    async def process(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process input and return result"""
        ...
    
    async def initialize(self) -> None:
        """Initialize agent resources"""
        ...
    
    async def shutdown(self) -> None:
        """Cleanup agent resources"""
        ...


@runtime_checkable
class MCPAwareAgentProtocol(AgentProtocol, Protocol):
    """Protocol for agents that support MCP tools"""
    
    def inject_mcp(self, mcp_config: Dict[str, Any]) -> None:
        """Inject MCP server configuration"""
        ...
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available MCP tools"""
        ...


# =============================================================================
# Memory Protocols
# =============================================================================

@runtime_checkable
class MemoryServiceProtocol(Protocol):
    """Protocol for memory services"""
    
    async def store(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> None:
        """Store value with optional TTL"""
        ...
    
    async def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve value by key"""
        ...
    
    async def delete(self, key: str) -> bool:
        """Delete value by key"""
        ...
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        ...


@runtime_checkable
class SessionServiceProtocol(Protocol):
    """Protocol for session management"""
    
    async def create_session(
        self,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create new session"""
        ...
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID"""
        ...
    
    async def update_session(
        self,
        session_id: str,
        data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Update session data"""
        ...
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        ...


# =============================================================================
# UI/A2UI Protocols
# =============================================================================

# UIContextMode imported from src.shared.enums


@runtime_checkable
class A2UIProviderProtocol(Protocol):
    """Protocol for A2UI service - enables Strategy Pattern for UI generation"""
    
    async def create_surface(
        self,
        surface_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a new UI surface"""
        ...
    
    async def update_components(
        self,
        surface_id: str,
        components: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Update components on a surface"""
        ...
    
    async def delete_surface(self, surface_id: str) -> Dict[str, Any]:
        """Delete a surface"""
        ...
    
    def get_agent_extension(
        self,
        version: str = "0.9"
    ) -> Dict[str, Any]:
        """Get A2UI extension for A2A protocol"""
        ...


@runtime_checkable
class ContextAwareUIProtocol(A2UIProviderProtocol, Protocol):
    """Protocol for context-aware UI generation"""
    
    async def build_context_aware_ui(
        self,
        user_id: str,
        session_id: str,
        intent: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Generate UI based on context"""
        ...


# =============================================================================
# Context Protocols
# =============================================================================

@runtime_checkable
class ContextProviderProtocol(Protocol):
    """Protocol for context providers"""
    
    @property
    def provider_name(self) -> str:
        """Provider identifier"""
        ...
    
    async def get_context(
        self,
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        """Get context data"""
        ...
    
    async def update_context(
        self,
        user_id: str,
        session_id: str,
        data: Dict[str, Any]
    ) -> None:
        """Update context data"""
        ...


@runtime_checkable
class ContextBundleProtocol(Protocol):
    """Protocol for context bundles"""
    
    @property
    def session_id(self) -> str:
        """Session identifier"""
        ...
    
    @property
    def user_id(self) -> str:
        """User identifier"""
        ...
    
    def get_temporal_context(self) -> Dict[str, Any]:
        """Get temporal context"""
        ...
    
    def get_spatial_context(self) -> Optional[Dict[str, Any]]:
        """Get spatial context"""
        ...
    
    def get_device_context(self) -> Optional[Dict[str, Any]]:
        """Get device context"""
        ...
    
    def to_prompt(self, format: str = "openai") -> str:
        """Convert to prompt format"""
        ...


# =============================================================================
# Storage Protocols
# =============================================================================

@runtime_checkable
class VectorStoreProtocol(Protocol):
    """Protocol for vector stores"""
    
    async def upsert(
        self,
        id: str,
        vector: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Insert or update vector"""
        ...
    
    async def search(
        self,
        query_vector: List[float],
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search similar vectors"""
        ...
    
    async def delete(self, id: str) -> bool:
        """Delete vector by ID"""
        ...


@runtime_checkable
class CacheProtocol(Protocol):
    """Protocol for caching"""
    
    async def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        ...
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> None:
        """Set cached value"""
        ...
    
    async def invalidate(self, key: str) -> bool:
        """Invalidate cached value"""
        ...


# =============================================================================
# MCP Protocols
# =============================================================================

@runtime_checkable
class MCPServerProtocol(Protocol):
    """Protocol for MCP servers"""
    
    @property
    def server_name(self) -> str:
        """Server identifier"""
        ...
    
    @property
    def capabilities(self) -> List[str]:
        """Server capabilities"""
        ...
    
    async def connect(self) -> None:
        """Connect to MCP server"""
        ...
    
    async def disconnect(self) -> None:
        """Disconnect from MCP server"""
        ...
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools"""
        ...
    
    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a tool"""
        ...


@runtime_checkable
class MCPRegistryProtocol(Protocol):
    """Protocol for MCP registry"""
    
    def register_server(self, server: MCPServerProtocol) -> None:
        """Register MCP server"""
        ...
    
    def get_server(self, name: str) -> Optional[MCPServerProtocol]:
        """Get server by name"""
        ...
    
    def list_servers(self) -> List[str]:
        """List all registered servers"""
        ...


# =============================================================================
# Event/Observer Protocols
# =============================================================================

@runtime_checkable
class EventSubscriberProtocol(Protocol):
    """Protocol for event subscribers - Observer Pattern"""
    
    async def handle_event(
        self,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> None:
        """Handle received event"""
        ...


@runtime_checkable
class EventPublisherProtocol(Protocol):
    """Protocol for event publishers - Observer Pattern"""
    
    def subscribe(
        self,
        event_type: str,
        subscriber: EventSubscriberProtocol
    ) -> None:
        """Subscribe to events"""
        ...
    
    def unsubscribe(
        self,
        event_type: str,
        subscriber: EventSubscriberProtocol
    ) -> None:
        """Unsubscribe from events"""
        ...
    
    async def publish(
        self,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> None:
        """Publish event to subscribers"""
        ...


# =============================================================================
# Repository Protocols (DDD)
# =============================================================================

from typing import TypeVar, Generic

T = TypeVar('T')


@runtime_checkable
class RepositoryProtocol(Protocol, Generic[T]):
    """Protocol for repositories - Repository Pattern (DDD)"""
    
    async def get_by_id(self, id: str) -> Optional[T]:
        """Get entity by ID"""
        ...
    
    async def get_all(self) -> List[T]:
        """Get all entities"""
        ...
    
    async def save(self, entity: T) -> T:
        """Save entity"""
        ...
    
    async def delete(self, id: str) -> bool:
        """Delete entity"""
        ...


# =============================================================================
# Factory Protocol
# =============================================================================

@runtime_checkable
class FactoryProtocol(Protocol, Generic[T]):
    """Protocol for factories - Factory Pattern"""
    
    def create(self, **kwargs) -> T:
        """Create instance"""
        ...
    
    def register(self, key: str, creator: callable) -> None:
        """Register creator"""
        ...
    
    def get_registered_types(self) -> List[str]:
        """Get registered types"""
        ...


# =============================================================================
# ALIASES FOR BACKWARD COMPATIBILITY
# =============================================================================

# Alias for backward compatibility - generic service protocol
ServiceProtocol = AIProviderProtocol

__all__ = [
    "AIProviderType",
    "AIProviderProtocol",
    "ServiceProtocol",  # Alias
    "EmbeddingProviderProtocol",
    "AgentType",
    "AgentProtocol",
    "MCPAwareAgentProtocol",
    "MemoryServiceProtocol",
    "SessionServiceProtocol",
    "UIContextMode",
    "A2UIProviderProtocol",
    "ContextAwareUIProtocol",
    "ContextProviderProtocol",
    "ContextBundleProtocol",
    "VectorStoreProtocol",
    "CacheProtocol",
    "MCPServerProtocol",
    "MCPRegistryProtocol",
    "EventSubscriberProtocol",
    "EventPublisherProtocol",
    "RepositoryProtocol",
    "FactoryProtocol",
]
