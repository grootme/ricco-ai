"""
Tests for MCP Proxy, Registry, and Circuit Breaker

Comprehensive test suite for:
- TokenAwareProxy
- LoadBalancer
- CircuitBreaker
- ServerRegistry
- ToolRegistry
- SkillRegistry
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add project paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))


# ============== CIRCUIT BREAKER TESTS ==============

class TestCircuitBreaker:
    """Tests for Circuit Breaker pattern implementation."""
    
    @pytest.fixture
    def circuit_breaker(self):
        """Create a circuit breaker instance for testing."""
        from mcp.proxy.circuit_breaker import CircuitBreaker, CircuitState
        
        return CircuitBreaker(
            failure_threshold=3,
            recovery_timeout=30,
            half_open_max_calls=2
        )
    
    def test_circuit_breaker_initial_state(self, circuit_breaker):
        """Test that circuit breaker starts in CLOSED state."""
        from mcp.proxy.circuit_breaker import CircuitState
        
        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.failure_count == 0
        assert circuit_breaker.is_available() is True
    
    def test_circuit_breaker_opens_after_threshold(self, circuit_breaker):
        """Test that circuit breaker opens after failure threshold."""
        from mcp.proxy.circuit_breaker import CircuitState
        
        # Record failures up to threshold
        for _ in range(3):
            circuit_breaker.record_failure()
        
        assert circuit_breaker.state == CircuitState.OPEN
        assert circuit_breaker.is_available() is False
    
    def test_circuit_breaker_closes_on_success(self, circuit_breaker):
        """Test that circuit breaker resets on success."""
        from mcp.proxy.circuit_breaker import CircuitState
        
        # Record some failures
        circuit_breaker.record_failure()
        circuit_breaker.record_failure()
        
        # Record success
        circuit_breaker.record_success()
        
        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.failure_count == 0
    
    @pytest.mark.asyncio
    async def test_circuit_breaker_protected_decorator(self, circuit_breaker):
        """Test the circuit breaker protected decorator."""
        from mcp.proxy.circuit_breaker import circuit_breaker_protected, CircuitState
        
        call_count = 0
        
        @circuit_breaker_protected(circuit_breaker)
        async def protected_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Simulated failure")
            return "success"
        
        # First two calls should fail and open circuit
        with pytest.raises(Exception):
            await protected_function()
        with pytest.raises(Exception):
            await protected_function()
        
        # Circuit should be open now
        assert circuit_breaker.state == CircuitState.OPEN


# ============== LOAD BALANCER TESTS ==============

class TestLoadBalancer:
    """Tests for Load Balancer implementation."""
    
    @pytest.fixture
    def load_balancer(self):
        """Create a load balancer instance for testing."""
        from mcp.proxy.load_balancer import LoadBalancer, LoadBalancingStrategy
        
        lb = LoadBalancer(strategy=LoadBalancingStrategy.ROUND_ROBIN)
        
        # Add some mock servers
        for i in range(3):
            server = MagicMock()
            server.server_id = f"server-{i}"
            server.weight = 1
            server.health_score = 1.0
            server.is_available = MagicMock(return_value=True)
            lb.add_server(server)
        
        return lb
    
    def test_round_robin_selection(self, load_balancer):
        """Test round-robin server selection."""
        # Select servers in sequence
        selected = [load_balancer.select_server().server_id for _ in range(6)]
        
        # Should cycle through servers
        assert selected == ["server-0", "server-1", "server-2", "server-0", "server-1", "server-2"]
    
    def test_weighted_selection(self, load_balancer):
        """Test weighted round-robin selection."""
        from mcp.proxy.load_balancer import LoadBalancingStrategy
        
        load_balancer.strategy = LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN
        
        # Set different weights
        load_balancer.servers[0].weight = 3
        load_balancer.servers[1].weight = 2
        load_balancer.servers[2].weight = 1
        
        # Select many times and count
        selections = {}
        for _ in range(60):
            server = load_balancer.select_server()
            if server:
                selections[server.server_id] = selections.get(server.server_id, 0) + 1
        
        # Higher weight servers should get more selections
        assert selections.get("server-0", 0) >= selections.get("server-2", 0)
    
    def test_least_connections_selection(self, load_balancer):
        """Test least connections selection strategy."""
        from mcp.proxy.load_balancer import LoadBalancingStrategy
        
        load_balancer.strategy = LoadBalancingStrategy.LEAST_CONNECTIONS
        
        # Set different connection counts
        load_balancer.servers[0].active_connections = 10
        load_balancer.servers[1].active_connections = 2
        load_balancer.servers[2].active_connections = 5
        
        # Should select server with least connections
        selected = load_balancer.select_server()
        assert selected.server_id == "server-1"
    
    def test_health_filtering(self, load_balancer):
        """Test that unhealthy servers are filtered out."""
        # Mark one server as unhealthy
        load_balancer.servers[0].health_score = 0.0
        
        # Select multiple times
        for _ in range(10):
            selected = load_balancer.select_server()
            assert selected.server_id != "server-0"


# ============== TOKEN AWARE PROXY TESTS ==============

class TestTokenAwareProxy:
    """Tests for Token Aware Proxy implementation."""
    
    @pytest.fixture
    def proxy(self):
        """Create a proxy instance for testing."""
        from mcp.proxy.token_aware_proxy import TokenAwareProxy
        
        return TokenAwareProxy(
            servers=[],
            timeout_seconds=30,
            max_retries=3
        )
    
    def test_proxy_initialization(self, proxy):
        """Test proxy initializes correctly."""
        assert proxy.timeout_seconds == 30
        assert proxy.max_retries == 3
        assert proxy.load_balancer is not None
        assert proxy.circuit_breakers == {}
    
    @pytest.mark.asyncio
    async def test_proxy_execute_no_servers(self, proxy):
        """Test proxy behavior when no servers are available."""
        result = await proxy.execute("test_tool", {"arg": "value"})
        
        assert result["success"] is False
        assert "error" in result or "No servers" in str(result)
    
    @pytest.mark.asyncio
    async def test_proxy_with_mock_server(self, proxy):
        """Test proxy execution with a mock server."""
        mock_server = MagicMock()
        mock_server.server_id = "mock-server"
        mock_server.is_available = MagicMock(return_value=True)
        mock_server.execute_tool = AsyncMock(return_value={"success": True, "result": "ok"})
        
        proxy.add_server(mock_server)
        
        result = await proxy.execute("test_tool", {"arg": "value"})
        
        assert result is not None


# ============== SERVER REGISTRY TESTS ==============

class TestServerRegistry:
    """Tests for MCP Server Registry."""
    
    @pytest.fixture
    def registry(self):
        """Create a server registry instance."""
        from mcp.registry.server_registry import ServerRegistry, MCPServerConfig, TransportType
        
        return ServerRegistry()
    
    def test_register_server(self, registry):
        """Test registering an MCP server."""
        from mcp.registry.server_registry import MCPServerConfig, TransportType
        
        config = MCPServerConfig(
            server_id="test-server",
            name="Test Server",
            description="A test server",
            transport=TransportType.STDIO,
            command="python",
            args=["-m", "test_server"]
        )
        
        registry.register(config)
        
        assert registry.get("test-server") is not None
        assert registry.get("test-server").name == "Test Server"
    
    def test_unregister_server(self, registry):
        """Test unregistering an MCP server."""
        from mcp.registry.server_registry import MCPServerConfig, TransportType
        
        config = MCPServerConfig(
            server_id="temp-server",
            name="Temp Server",
            transport=TransportType.STDIO
        )
        
        registry.register(config)
        assert registry.get("temp-server") is not None
        
        registry.unregister("temp-server")
        assert registry.get("temp-server") is None
    
    def test_find_by_tool(self, registry):
        """Test finding servers by tool name."""
        from mcp.registry.server_registry import MCPServerConfig, TransportType
        
        config = MCPServerConfig(
            server_id="tool-server",
            name="Tool Server",
            transport=TransportType.STDIO,
            tools=["tool_a", "tool_b", "tool_c"]
        )
        
        registry.register(config)
        
        servers = registry.find_by_tool("tool_b")
        assert len(servers) == 1
        assert servers[0].server_id == "tool-server"
    
    def test_list_all_servers(self, registry):
        """Test listing all registered servers."""
        from mcp.registry.server_registry import MCPServerConfig, TransportType
        
        for i in range(3):
            config = MCPServerConfig(
                server_id=f"server-{i}",
                name=f"Server {i}",
                transport=TransportType.STDIO
            )
            registry.register(config)
        
        all_servers = registry.list_all()
        assert len(all_servers) >= 3


# ============== TOOL REGISTRY TESTS ==============

class TestToolRegistry:
    """Tests for MCP Tool Registry."""
    
    @pytest.fixture
    def registry(self):
        """Create a tool registry instance."""
        from mcp.registry.tool_registry import ToolRegistry
        
        return ToolRegistry()
    
    def test_register_tool(self, registry):
        """Test registering a tool."""
        from mcp.registry.server_registry import MCPToolDefinition
        
        tool = MCPToolDefinition(
            tool_id="test-tool",
            name="Test Tool",
            description="A test tool",
            input_schema={"type": "object", "properties": {}}
        )
        
        registry.register(tool)
        
        assert registry.get("test-tool") is not None
        assert registry.get("test-tool").name == "Test Tool"
    
    def test_find_tools_by_category(self, registry):
        """Test finding tools by category."""
        from mcp.registry.server_registry import MCPToolDefinition
        
        for i in range(3):
            tool = MCPToolDefinition(
                tool_id=f"tool-{i}",
                name=f"Tool {i}",
                description=f"Tool {i}",
                input_schema={},
                category="test-category"
            )
            registry.register(tool)
        
        tools = registry.find_by_category("test-category")
        assert len(tools) == 3
    
    def test_find_tools_by_server(self, registry):
        """Test finding tools by server."""
        from mcp.registry.server_registry import MCPToolDefinition
        
        for i in range(2):
            tool = MCPToolDefinition(
                tool_id=f"server-tool-{i}",
                name=f"Server Tool {i}",
                description="",
                input_schema={},
                server_id="test-server"
            )
            registry.register(tool)
        
        tools = registry.find_by_server("test-server")
        assert len(tools) == 2


# ============== SKILL REGISTRY TESTS ==============

class TestSkillRegistry:
    """Tests for Skill Registry."""
    
    @pytest.fixture
    def registry(self):
        """Create a skill registry instance."""
        from mcp.registry.skill_registry import SkillRegistry
        
        return SkillRegistry()
    
    def test_register_skill(self, registry):
        """Test registering a skill."""
        skill_data = {
            "id": "test-skill",
            "name": "Test Skill",
            "description": "A test skill",
            "category": "test",
            "tools": ["tool_a", "tool_b"]
        }
        
        registry.register(skill_data)
        
        assert registry.get("test-skill") is not None
    
    def test_find_skill_by_tool(self, registry):
        """Test finding a skill by its tool."""
        skill_data = {
            "id": "tool-skill",
            "name": "Tool Skill",
            "description": "",
            "category": "test",
            "tools": ["unique_tool"]
        }
        
        registry.register(skill_data)
        
        skills = registry.find_by_tool("unique_tool")
        assert len(skills) == 1
        assert skills[0]["id"] == "tool-skill"
    
    def test_list_by_category(self, registry):
        """Test listing skills by category."""
        for i in range(3):
            skill_data = {
                "id": f"category-skill-{i}",
                "name": f"Category Skill {i}",
                "description": "",
                "category": "special-category"
            }
            registry.register(skill_data)
        
        skills = registry.list_by_category("special-category")
        assert len(skills) == 3


# ============== INTEGRATION TESTS ==============

class TestMCPIntegration:
    """Integration tests for MCP components."""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete MCP workflow from registration to execution."""
        from mcp.registry.server_registry import ServerRegistry, MCPServerConfig, TransportType
        from mcp.registry.tool_registry import ToolRegistry
        from mcp.proxy.token_aware_proxy import TokenAwareProxy
        
        # Setup registries
        server_registry = ServerRegistry()
        tool_registry = ToolRegistry()
        proxy = TokenAwareProxy(servers=[])
        
        # Register a server
        server_config = MCPServerConfig(
            server_id="integration-server",
            name="Integration Server",
            transport=TransportType.STDIO,
            tools=["int_tool"]
        )
        server_registry.register(server_config)
        
        # Verify registration
        assert server_registry.get("integration-server") is not None
        
        # Find server by tool
        servers = server_registry.find_by_tool("int_tool")
        assert len(servers) == 1


# ============== FIXTURES AND SETUP ==============

@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
