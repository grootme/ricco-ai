"""
Unit tests for Core Protocols

Tests the protocol definitions and their runtime behavior.
"""

import sys
import pytest
from typing import Dict, Any, List, Optional, AsyncIterator
from datetime import datetime

sys.path.insert(0, '.')

from src.core.protocols import (
    AIProviderProtocol,
    AIProviderType,
    AgentProtocol,
    AgentType,
    MemoryServiceProtocol,
    SessionServiceProtocol,
    A2UIProviderProtocol,
    ContextProviderProtocol,
    VectorStoreProtocol,
    CacheProtocol,
    MCPServerProtocol,
    MCPRegistryProtocol,
    EventSubscriberProtocol,
    EventPublisherProtocol,
    RepositoryProtocol,
    FactoryProtocol,
    UIContextMode,
)


# =============================================================================
# Mock Implementations for Testing
# =============================================================================

class MockAIProvider:
    """Mock implementation of AIProviderProtocol"""
    
    def __init__(self):
        self._initialized = False
        self._provider_type = AIProviderType.OPENAI
    
    @property
    def provider_type(self) -> AIProviderType:
        return self._provider_type
    
    @property
    def is_initialized(self) -> bool:
        return self._initialized
    
    async def initialize(self) -> None:
        self._initialized = True
    
    async def generate_response(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        return {"response": f"Mock response to: {prompt}"}
    
    async def generate_stream(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[str]:
        yield "Mock "
        yield "streaming "
        yield "response"
    
    async def get_embedding(self, text: str) -> List[float]:
        return [0.1, 0.2, 0.3]
    
    async def health_check(self) -> bool:
        return self._initialized


class MockAgent:
    """Mock implementation of AgentProtocol"""
    
    def __init__(self, agent_id: str, name: str = "TestAgent"):
        self._agent_id = agent_id
        self._name = name
        self._agent_type = AgentType.LLM
    
    @property
    def agent_id(self) -> str:
        return self._agent_id
    
    @property
    def agent_type(self) -> AgentType:
        return self._agent_type
    
    @property
    def name(self) -> str:
        return self._name
    
    async def process(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        return {"result": f"Processed by {self._name}"}
    
    async def initialize(self) -> None:
        pass
    
    async def shutdown(self) -> None:
        pass


class MockMemoryService:
    """Mock implementation of MemoryServiceProtocol"""
    
    def __init__(self):
        self._store: Dict[str, Any] = {}
    
    async def store(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        self._store[key] = value
    
    async def retrieve(self, key: str) -> Optional[Any]:
        return self._store.get(key)
    
    async def delete(self, key: str) -> bool:
        if key in self._store:
            del self._store[key]
            return True
        return False
    
    async def exists(self, key: str) -> bool:
        return key in self._store


class MockSessionService:
    """Mock implementation of SessionServiceProtocol"""
    
    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}
    
    async def create_session(
        self,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        import uuid
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = {
            "user_id": user_id,
            "metadata": metadata or {}
        }
        return {"session_id": session_id, "user_id": user_id}
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self._sessions.get(session_id)
    
    async def update_session(
        self,
        session_id: str,
        data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        if session_id in self._sessions:
            self._sessions[session_id].update(data)
            return self._sessions[session_id]
        return None
    
    async def delete_session(self, session_id: str) -> bool:
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False


class MockA2UIProvider:
    """Mock implementation of A2UIProviderProtocol"""
    
    async def create_surface(
        self,
        surface_id: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        return {"surface_id": surface_id, "created": True}
    
    async def update_components(
        self,
        surface_id: str,
        components: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        return {"surface_id": surface_id, "updated": len(components)}
    
    async def delete_surface(self, surface_id: str) -> Dict[str, Any]:
        return {"surface_id": surface_id, "deleted": True}
    
    def get_agent_extension(self, version: str = "0.9") -> Dict[str, Any]:
        return {"uri": f"https://a2ui.org/a2a-extension/v{version}"}


class MockContextProvider:
    """Mock implementation of ContextProviderProtocol"""
    
    @property
    def provider_name(self) -> str:
        return "mock_context"
    
    async def get_context(
        self,
        user_id: str,
        session_id: str
    ) -> Dict[str, Any]:
        return {"user_id": user_id, "session_id": session_id}
    
    async def update_context(
        self,
        user_id: str,
        session_id: str,
        data: Dict[str, Any]
    ) -> None:
        pass


class MockVectorStore:
    """Mock implementation of VectorStoreProtocol"""
    
    def __init__(self):
        self._vectors: Dict[str, tuple] = {}
    
    async def upsert(
        self,
        id: str,
        vector: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        self._vectors[id] = (vector, metadata)
    
    async def search(
        self,
        query_vector: List[float],
        k: int = 5,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        return [{"id": "test", "score": 0.95}]
    
    async def delete(self, id: str) -> bool:
        if id in self._vectors:
            del self._vectors[id]
            return True
        return False


class MockCache:
    """Mock implementation of CacheProtocol"""
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
    
    async def get(self, key: str) -> Optional[Any]:
        return self._cache.get(key)
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> None:
        self._cache[key] = value
    
    async def invalidate(self, key: str) -> bool:
        if key in self._cache:
            del self._cache[key]
            return True
        return False


class MockMCPServer:
    """Mock implementation of MCPServerProtocol"""
    
    @property
    def server_name(self) -> str:
        return "mock_server"
    
    @property
    def capabilities(self) -> List[str]:
        return ["tools", "resources"]
    
    async def connect(self) -> None:
        pass
    
    async def disconnect(self) -> None:
        pass
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        return [{"name": "test_tool"}]
    
    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {"result": f"Executed {tool_name}"}


class MockEventSubscriber:
    """Mock implementation of EventSubscriberProtocol"""
    
    def __init__(self):
        self.events: List[tuple] = []
    
    async def handle_event(
        self,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> None:
        self.events.append((event_type, event_data))


class MockEventPublisher:
    """Mock implementation of EventPublisherProtocol"""
    
    def __init__(self):
        self._subscribers: Dict[str, List[EventSubscriberProtocol]] = {}
    
    def subscribe(
        self,
        event_type: str,
        subscriber: EventSubscriberProtocol
    ) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(subscriber)
    
    def unsubscribe(
        self,
        event_type: str,
        subscriber: EventSubscriberProtocol
    ) -> None:
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(subscriber)
    
    async def publish(
        self,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> None:
        for sub in self._subscribers.get(event_type, []):
            await sub.handle_event(event_type, event_data)


class MockRepository:
    """Mock implementation of RepositoryProtocol"""
    
    def __init__(self, entity_type: type):
        self._entity_type = entity_type
        self._entities: Dict[str, Any] = {}
    
    async def get_by_id(self, id: str) -> Optional[Any]:
        return self._entities.get(id)
    
    async def get_all(self) -> List[Any]:
        return list(self._entities.values())
    
    async def save(self, entity: Any) -> Any:
        if hasattr(entity, 'id'):
            self._entities[entity.id] = entity
        return entity
    
    async def delete(self, id: str) -> bool:
        if id in self._entities:
            del self._entities[id]
            return True
        return False


class MockFactory:
    """Mock implementation of FactoryProtocol"""
    
    def __init__(self):
        self._creators: Dict[str, callable] = {}
    
    def create(self, **kwargs) -> Any:
        key = kwargs.get('type', 'default')
        if key in self._creators:
            return self._creators[key](**kwargs)
        return None
    
    def register(self, key: str, creator: callable) -> None:
        self._creators[key] = creator
    
    def get_registered_types(self) -> List[str]:
        return list(self._creators.keys())


# =============================================================================
# Tests
# =============================================================================

class TestProtocols:
    """Tests for protocol definitions"""
    
    def test_ai_provider_type_enum(self):
        """Test AIProviderType enum values"""
        assert AIProviderType.OPENAI.value == "openai"
        assert AIProviderType.ANTHROPIC.value == "anthropic"
        assert AIProviderType.GOOGLE.value == "google"
        assert AIProviderType.LOCAL.value == "local"
        assert AIProviderType.OPENROUTER.value == "openrouter"
    
    def test_agent_type_enum(self):
        """Test AgentType enum values"""
        assert AgentType.LLM.value == "llm"
        assert AgentType.A2A.value == "a2a"
        assert AgentType.SEQUENTIAL.value == "sequential"
        assert AgentType.PARALLEL.value == "parallel"
        assert AgentType.WORKFLOW.value == "workflow"
    
    def test_ui_context_mode_enum(self):
        """Test UIContextMode enum values"""
        assert UIContextMode.MINIMAL.value == "minimal"
        assert UIContextMode.STANDARD.value == "standard"
        assert UIContextMode.DETAILED.value == "detailed"
        assert UIContextMode.ACCESSIBILITY.value == "accessibility"
    
    def test_ai_provider_protocol_implementation(self):
        """Test that MockAIProvider implements AIProviderProtocol"""
        provider = MockAIProvider()
        assert isinstance(provider, AIProviderProtocol)
        assert provider.provider_type == AIProviderType.OPENAI
        assert provider.is_initialized == False
    
    @pytest.mark.asyncio
    async def test_ai_provider_methods(self):
        """Test AI provider async methods"""
        provider = MockAIProvider()
        
        # Initialize
        await provider.initialize()
        assert provider.is_initialized == True
        
        # Generate response
        response = await provider.generate_response("Hello")
        assert "response" in response
        
        # Get embedding
        embedding = await provider.get_embedding("test")
        assert len(embedding) == 3
        
        # Health check
        assert await provider.health_check() == True
    
    def test_agent_protocol_implementation(self):
        """Test that MockAgent implements AgentProtocol"""
        agent = MockAgent("agent-001", "TestBot")
        assert isinstance(agent, AgentProtocol)
        assert agent.agent_id == "agent-001"
        assert agent.name == "TestBot"
        assert agent.agent_type == AgentType.LLM
    
    @pytest.mark.asyncio
    async def test_agent_process(self):
        """Test agent process method"""
        agent = MockAgent("agent-001")
        result = await agent.process({"input": "test"})
        assert "result" in result
    
    @pytest.mark.asyncio
    async def test_memory_service(self):
        """Test memory service protocol"""
        memory = MockMemoryService()
        
        # Store
        await memory.store("key1", "value1")
        assert await memory.exists("key1") == True
        
        # Retrieve
        value = await memory.retrieve("key1")
        assert value == "value1"
        
        # Delete
        assert await memory.delete("key1") == True
        assert await memory.exists("key1") == False
    
    @pytest.mark.asyncio
    async def test_session_service(self):
        """Test session service protocol"""
        service = MockSessionService()
        
        # Create
        session = await service.create_session("user-001")
        assert "session_id" in session
        assert session["user_id"] == "user-001"
        
        # Get
        retrieved = await service.get_session(session["session_id"])
        assert retrieved is not None
        
        # Delete
        assert await service.delete_session(session["session_id"]) == True
    
    @pytest.mark.asyncio
    async def test_a2ui_provider(self):
        """Test A2UI provider protocol"""
        provider = MockA2UIProvider()
        
        # Create surface
        result = await provider.create_surface("surface-001")
        assert result["created"] == True
        
        # Update components
        result = await provider.update_components("surface-001", [{"id": "comp1"}])
        assert result["updated"] == 1
        
        # Delete surface
        result = await provider.delete_surface("surface-001")
        assert result["deleted"] == True
        
        # Get extension
        ext = provider.get_agent_extension()
        assert "uri" in ext
    
    @pytest.mark.asyncio
    async def test_vector_store(self):
        """Test vector store protocol"""
        store = MockVectorStore()
        
        # Upsert
        await store.upsert("vec1", [0.1, 0.2, 0.3], {"label": "test"})
        
        # Search
        results = await store.search([0.1, 0.2, 0.3])
        assert len(results) > 0
        
        # Delete
        assert await store.delete("vec1") == True
    
    @pytest.mark.asyncio
    async def test_cache(self):
        """Test cache protocol"""
        cache = MockCache()
        
        # Set
        await cache.set("key1", "value1")
        
        # Get
        value = await cache.get("key1")
        assert value == "value1"
        
        # Invalidate
        assert await cache.invalidate("key1") == True
        assert await cache.get("key1") is None
    
    @pytest.mark.asyncio
    async def test_event_publisher_subscriber(self):
        """Test event publisher and subscriber protocols"""
        publisher = MockEventPublisher()
        subscriber = MockEventSubscriber()
        
        # Subscribe
        publisher.subscribe("test_event", subscriber)
        
        # Publish
        await publisher.publish("test_event", {"data": "test"})
        
        # Verify
        assert len(subscriber.events) == 1
        assert subscriber.events[0][0] == "test_event"
        
        # Unsubscribe
        publisher.unsubscribe("test_event", subscriber)
        await publisher.publish("test_event", {"data": "test2"})
        assert len(subscriber.events) == 1  # No new events
    
    def test_factory_protocol(self):
        """Test factory protocol"""
        factory = MockFactory()
        
        # Register creators
        factory.register("type_a", lambda **kw: {"type": "A", **{k: v for k, v in kw.items() if k != 'type'}})
        factory.register("type_b", lambda **kw: {"type": "B", **{k: v for k, v in kw.items() if k != 'type'}})
        
        # Get registered types
        types = factory.get_registered_types()
        assert "type_a" in types
        assert "type_b" in types
        
        # Create
        result = factory.create(type="type_a", name="test")
        assert result["type"] == "A"
        assert result["name"] == "test"


# =============================================================================
# Run tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
