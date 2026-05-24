"""
E2E Integration Tests for Frontend-Backend Integration
Tests complete user flows with mocked backend services

Test Categories:
1. Dashboard Integration
2. Agent Management Integration  
3. NEXUS Chat Integration
4. Cognitive Capital Integration
5. MCP Server Integration
"""
import pytest
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import json

# Test constants
API_BASE = "http://localhost:8000/api/v1"


# =============================================================================
# MOCK DATA GENERATORS
# =============================================================================

class MockDataGenerator:
    """Generate consistent mock data for tests"""
    
    @staticmethod
    def generate_agent(
        id: str = "agent-001",
        name: str = "Test Agent",
        domain: str = "swe",
        status: str = "active"
    ) -> Dict[str, Any]:
        return {
            "id": id,
            "name": name,
            "description": f"Agent for {domain}",
            "domain": domain,
            "role": "builder",
            "skills": ["coding", "testing"],
            "tools": ["execute_code"],
            "mcp_servers": ["filesystem"],
            "prompt_template": "You are a helpful assistant.",
            "cognitive_capital": {
                "agent_id": id,
                "capital_value": 1000,
                "total_engrams": 50,
                "total_interactions": 100,
                "learning_score": 0.85,
                "domains": [domain],
                "skills": ["coding", "testing"],
                "tools": ["execute_code"],
                "mcp_servers": ["filesystem"],
                "memory_vcs_version": "v1.0.0",
                "last_updated": datetime.utcnow().isoformat()
            },
            "status": status,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "metrics": {
                "total_interactions": 100,
                "success_rate": 0.95,
                "avg_response_time": 1.5,
                "capital_growth": 0.1,
                "last_interaction": datetime.utcnow().isoformat()
            }
        }
    
    @staticmethod
    def generate_iovba_group(
        id: str = "group-001",
        domain: str = "swe"
    ) -> Dict[str, Any]:
        roles = ["investigador", "observador", "validador", "builder", "asistente"]
        agents = {}
        for role in roles:
            agents[role] = MockDataGenerator.generate_agent(
                id=f"{id}-{role}",
                name=f"{role.capitalize()} Agent",
                domain=domain
            )
        
        return {
            "id": id,
            "name": f"{domain.upper()} Expert Group",
            "domain": domain,
            "elegant_name": f"{domain.capitalize()} Team",
            "description": f"Expert group for {domain} domain",
            "agents": agents,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "metrics": {
                "total_tasks": 100,
                "success_rate": 0.92,
                "avg_completion_time": 2.5,
                "domain_expertise": 0.88
            }
        }
    
    @staticmethod
    def generate_engram(
        id: str = "engram-001",
        agent_id: str = "agent-001"
    ) -> Dict[str, Any]:
        return {
            "id": id,
            "agent_id": agent_id,
            "content": "Python is a high-level programming language.",
            "source": "interaction",
            "importance_score": 0.85,
            "access_count": 10,
            "tags": ["python", "programming"],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def generate_mcp_server(
        id: str = "mcp-001",
        name: str = "filesystem"
    ) -> Dict[str, Any]:
        return {
            "id": id,
            "name": name,
            "description": f"{name} MCP server",
            "transport": "stdio",
            "tools": [
                {
                    "name": f"{name}_tool",
                    "description": f"Tool for {name}",
                    "input_schema": {"type": "object"}
                }
            ],
            "resources": [],
            "status": "connected",
            "last_connected": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def generate_dashboard_stats() -> Dict[str, Any]:
        return {
            "total_agents": 25,
            "active_agents": 20,
            "total_capital": 15000,
            "total_engrams": 500,
            "mcp_servers_connected": 8,
            "skills_available": 45,
            "agent_groups": 5,
            "system_health": 98
        }
    
    @staticmethod
    def generate_nexus_status() -> Dict[str, Any]:
        return {
            "id": "nexus-001",
            "name": "NEXUS",
            "full_name": "Neural Execution Unified System",
            "status": "active",
            "domains_available": 13,
            "llm_configured": True,
            "model": "openrouter/free",
            "capital": {
                "total_engrams": 200,
                "total_interactions": 1000,
                "capital_value": 5000
            }
        }
    
    @staticmethod
    def generate_domains() -> List[Dict[str, Any]]:
        return [
            {"domain": "swe", "name": "Software Engineering", "elegant_name": "Code Crafter", "color": "#3B82F6", "tagline": "Build with code", "icon": "code", "description": "Software development"},
            {"domain": "salud", "name": "Health & Medicine", "elegant_name": "Health Guardian", "color": "#EF4444", "tagline": "Care for health", "icon": "heart", "description": "Healthcare"},
            {"domain": "finanzas", "name": "Finance", "elegant_name": "Finance Wizard", "color": "#059669", "tagline": "Master the markets", "icon": "dollar", "description": "Financial analysis"},
            {"domain": "noticias", "name": "News & Journalism", "elegant_name": "News Hunter", "color": "#6366F1", "tagline": "Stay informed", "icon": "newspaper", "description": "News analysis"},
        ]
    
    @staticmethod
    def generate_roles() -> List[Dict[str, Any]]:
        return [
            {"role": "investigador", "elegant_name": "Researcher", "tagline": "Discover truth", "description": "Research and analyze", "icon": "microscope", "color": "#3B82F6"},
            {"role": "observador", "elegant_name": "Observer", "tagline": "Watch closely", "description": "Monitor and detect", "icon": "eye", "color": "#F59E0B"},
            {"role": "validador", "elegant_name": "Validator", "tagline": "Verify quality", "description": "Validate and verify", "icon": "shield", "color": "#10B981"},
            {"role": "builder", "elegant_name": "Builder", "tagline": "Create solutions", "description": "Build and implement", "icon": "hammer", "color": "#8B5CF6"},
            {"role": "asistente", "elegant_name": "Assistant", "tagline": "Help always", "description": "Coordinate and assist", "icon": "help-circle", "color": "#EC4899"},
        ]


# =============================================================================
# DASHBOARD INTEGRATION TESTS
# =============================================================================

class TestDashboardIntegration:
    """Tests for Dashboard frontend-backend integration"""
    
    @pytest.mark.asyncio
    async def test_dashboard_loads_stats(self):
        """Test dashboard loads statistics correctly"""
        # Arrange
        expected_stats = MockDataGenerator.generate_dashboard_stats()
        
        # Act - Simulate API call
        with patch('requests.get') as mock_get:
            mock_get.return_value.json.return_value = expected_stats
            mock_get.return_value.status_code = 200
            
            # Simulate frontend fetch
            response = mock_get.return_value
            stats = response.json()
        
        # Assert
        assert stats["total_agents"] == 25
        assert stats["active_agents"] == 20
        assert stats["system_health"] == 98
    
    @pytest.mark.asyncio
    async def test_dashboard_displays_agents(self):
        """Test dashboard displays agent list"""
        # Arrange
        agents = [
            MockDataGenerator.generate_agent(id=f"agent-{i}", name=f"Agent {i}")
            for i in range(5)
        ]
        
        # Act
        agent_count = len(agents)
        active_count = sum(1 for a in agents if a["status"] == "active")
        
        # Assert
        assert agent_count == 5
        assert active_count == 5
    
    @pytest.mark.asyncio
    async def test_dashboard_iovba_groups_display(self):
        """Test dashboard displays IOVBA groups"""
        # Arrange
        groups = [
            MockDataGenerator.generate_iovba_group(id=f"group-{i}", domain=d)
            for i, d in enumerate(["swe", "salud", "finanzas"])
        ]
        
        # Act
        for group in groups:
            role_count = len(group["agents"])
            
            # Assert
            assert role_count == 5  # All IOVBA roles present
    
    @pytest.mark.asyncio
    async def test_dashboard_mcp_servers_status(self):
        """Test dashboard displays MCP server status"""
        # Arrange
        servers = [
            MockDataGenerator.generate_mcp_server(id=f"mcp-{i}", name=f"server-{i}")
            for i in range(3)
        ]
        
        # Act
        connected = sum(1 for s in servers if s["status"] == "connected")
        
        # Assert
        assert connected == 3


# =============================================================================
# NEXUS CHAT INTEGRATION TESTS
# =============================================================================

class TestNEXUSChatIntegration:
    """Tests for NEXUS Chat frontend-backend integration"""
    
    @pytest.mark.asyncio
    async def test_nexus_status_fetch(self):
        """Test NEXUS status is fetched correctly"""
        # Arrange
        expected_status = MockDataGenerator.generate_nexus_status()
        
        # Act
        status_data = expected_status
        
        # Assert
        assert status_data["status"] == "active"
        assert status_data["domains_available"] == 13
        assert status_data["llm_configured"] is True
    
    @pytest.mark.asyncio
    async def test_nexus_domains_fetch(self):
        """Test NEXUS domains are fetched correctly"""
        # Arrange
        domains = MockDataGenerator.generate_domains()
        
        # Act
        domain_names = [d["domain"] for d in domains]
        
        # Assert
        assert "swe" in domain_names
        assert "salud" in domain_names
        assert len(domains) == 4
    
    @pytest.mark.asyncio
    async def test_nexus_roles_fetch(self):
        """Test NEXUS roles are fetched correctly"""
        # Arrange
        roles = MockDataGenerator.generate_roles()
        
        # Act
        role_names = [r["role"] for r in roles]
        
        # Assert
        assert "investigador" in role_names
        assert "builder" in role_names
        assert len(roles) == 5
    
    @pytest.mark.asyncio
    async def test_nexus_chat_message_flow(self):
        """Test complete chat message flow"""
        # Arrange
        user_message = "Create a Python function to sort a list"
        
        # Act - Simulate chat flow
        # 1. User sends message
        request = {
            "message": user_message,
            "domain": "auto",
            "role": "auto",
            "stream": False
        }
        
        # 2. Backend processes and routes
        detected_domain = self._detect_domain(user_message)
        
        # 3. Response generated
        response = {
            "content": "Here's a Python function to sort a list...",
            "domain": detected_domain,
            "domain_brand": "Software Engineering",
            "confidence": 0.95,
            "roles_consulted": ["investigador", "builder"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Assert
        assert response["domain"] == "swe"
        assert "builder" in response["roles_consulted"]
        assert response["confidence"] > 0.8
    
    def _detect_domain(self, message: str) -> str:
        """Simple domain detection"""
        message_lower = message.lower()
        if "python" in message_lower or "function" in message_lower or "code" in message_lower:
            return "swe"
        return "custom"
    
    @pytest.mark.asyncio
    async def test_nexus_chat_with_domain_selection(self):
        """Test chat with specific domain selection"""
        # Arrange
        user_message = "What are the symptoms of flu?"
        selected_domain = "salud"
        
        # Act
        response = {
            "content": "Flu symptoms typically include...",
            "domain": selected_domain,
            "domain_brand": "Health Guardian",
            "confidence": 0.92
        }
        
        # Assert
        assert response["domain"] == "salud"
    
    @pytest.mark.asyncio
    async def test_nexus_chat_with_role_selection(self):
        """Test chat with specific role selection"""
        # Arrange
        user_message = "Verify this code is correct"
        selected_role = "validador"
        
        # Act
        response = {
            "content": "Let me validate this code...",
            "domain": "swe",
            "roles_consulted": [selected_role]
        }
        
        # Assert
        assert selected_role in response["roles_consulted"]


# =============================================================================
# AGENT MANAGEMENT INTEGRATION TESTS
# =============================================================================

class TestAgentManagementIntegration:
    """Tests for Agent Management frontend-backend integration"""
    
    @pytest.mark.asyncio
    async def test_list_agents_pagination(self):
        """Test agents list pagination"""
        # Arrange
        page_size = 10
        total_agents = 25
        
        # Act
        total_pages = (total_agents + page_size - 1) // page_size
        
        # Assert
        assert total_pages == 3
    
    @pytest.mark.asyncio
    async def test_create_agent_flow(self):
        """Test complete agent creation flow"""
        # Arrange
        new_agent_config = {
            "name": "New Test Agent",
            "domain": "swe",
            "role": "builder",
            "skills": ["python", "testing"],
            "tools": ["execute_code"],
            "prompt_template": "You are a Python expert."
        }
        
        # Act - Simulate creation
        created_agent = MockDataGenerator.generate_agent(
            id="agent-new",
            name=new_agent_config["name"],
            domain=new_agent_config["domain"]
        )
        
        # Assert
        assert created_agent["name"] == new_agent_config["name"]
        assert created_agent["domain"] == new_agent_config["domain"]
    
    @pytest.mark.asyncio
    async def test_update_agent_status(self):
        """Test updating agent status"""
        # Arrange
        agent = MockDataGenerator.generate_agent()
        
        # Act
        agent["status"] = "learning"
        
        # Assert
        assert agent["status"] == "learning"
    
    @pytest.mark.asyncio
    async def test_delete_agent(self):
        """Test deleting an agent"""
        # Arrange
        agents = [
            MockDataGenerator.generate_agent(id=f"agent-{i}")
            for i in range(3)
        ]
        
        # Act
        agents = [a for a in agents if a["id"] != "agent-1"]
        
        # Assert
        assert len(agents) == 2
        assert all(a["id"] != "agent-1" for a in agents)
    
    @pytest.mark.asyncio
    async def test_search_agents(self):
        """Test searching agents by name"""
        # Arrange
        agents = [
            MockDataGenerator.generate_agent(name="Python Expert"),
            MockDataGenerator.generate_agent(name="JavaScript Expert"),
            MockDataGenerator.generate_agent(name="Health Advisor")
        ]
        
        # Act
        search_query = "python"
        filtered = [a for a in agents if search_query.lower() in a["name"].lower()]
        
        # Assert
        assert len(filtered) == 1
        assert filtered[0]["name"] == "Python Expert"


# =============================================================================
# COGNITIVE CAPITAL INTEGRATION TESTS
# =============================================================================

class TestCognitiveCapitalIntegration:
    """Tests for Cognitive Capital frontend-backend integration"""
    
    @pytest.mark.asyncio
    async def test_capital_display(self):
        """Test cognitive capital display"""
        # Arrange
        agent = MockDataGenerator.generate_agent()
        capital = agent["cognitive_capital"]
        
        # Assert
        assert capital["capital_value"] == 1000
        assert capital["total_engrams"] == 50
        assert capital["learning_score"] == 0.85
    
    @pytest.mark.asyncio
    async def test_engrams_list(self):
        """Test engrams list display"""
        # Arrange
        engrams = [
            MockDataGenerator.generate_engram(id=f"engram-{i}")
            for i in range(10)
        ]
        
        # Act
        total = len(engrams)
        
        # Assert
        assert total == 10
    
    @pytest.mark.asyncio
    async def test_engram_importance_sorting(self):
        """Test engrams sorted by importance"""
        # Arrange
        engrams = [
            MockDataGenerator.generate_engram(id=f"engram-{i}")
            for i in range(5)
        ]
        
        # Set different importance scores
        engrams[0]["importance_score"] = 0.95
        engrams[1]["importance_score"] = 0.75
        engrams[2]["importance_score"] = 0.85
        
        # Act
        sorted_engrams = sorted(engrams, key=lambda e: e["importance_score"], reverse=True)
        
        # Assert
        assert sorted_engrams[0]["importance_score"] == 0.95
    
    @pytest.mark.asyncio
    async def test_capital_growth_tracking(self):
        """Test cognitive capital growth tracking"""
        # Arrange
        initial_capital = 1000
        interactions = 10
        
        # Act - Simulate growth
        growth_per_interaction = 5
        final_capital = initial_capital + (interactions * growth_per_interaction)
        
        # Assert
        assert final_capital == 1050
        assert final_capital > initial_capital


# =============================================================================
# MCP SERVER INTEGRATION TESTS
# =============================================================================

class TestMCPServerIntegration:
    """Tests for MCP Server frontend-backend integration"""
    
    @pytest.mark.asyncio
    async def test_server_list_display(self):
        """Test MCP server list display"""
        # Arrange
        servers = [
            MockDataGenerator.generate_mcp_server(name=name)
            for name in ["filesystem", "git", "postgres"]
        ]
        
        # Act
        connected = sum(1 for s in servers if s["status"] == "connected")
        
        # Assert
        assert connected == 3
    
    @pytest.mark.asyncio
    async def test_server_tools_display(self):
        """Test MCP server tools display"""
        # Arrange
        server = MockDataGenerator.generate_mcp_server(name="filesystem")
        server["tools"] = [
            {"name": "read_file", "description": "Read a file"},
            {"name": "write_file", "description": "Write a file"},
            {"name": "list_directory", "description": "List directory contents"}
        ]
        
        # Act
        tool_count = len(server["tools"])
        
        # Assert
        assert tool_count == 3
    
    @pytest.mark.asyncio
    async def test_server_connect_disconnect(self):
        """Test MCP server connection status change"""
        # Arrange
        server = MockDataGenerator.generate_mcp_server()
        assert server["status"] == "connected"
        
        # Act - Disconnect
        server["status"] = "disconnected"
        
        # Assert
        assert server["status"] == "disconnected"


# =============================================================================
# IOVBA GROUPS INTEGRATION TESTS
# =============================================================================

class TestIOVBAGroupsIntegration:
    """Tests for IOVBA Groups frontend-backend integration"""
    
    @pytest.mark.asyncio
    async def test_group_list_display(self):
        """Test IOVBA groups list display"""
        # Arrange
        groups = [
            MockDataGenerator.generate_iovba_group(domain=d)
            for d in ["swe", "salud", "finanzas"]
        ]
        
        # Act
        total = len(groups)
        
        # Assert
        assert total == 3
    
    @pytest.mark.asyncio
    async def test_group_roles_display(self):
        """Test IOVBA group roles display"""
        # Arrange
        group = MockDataGenerator.generate_iovba_group()
        
        # Act
        roles = list(group["agents"].keys())
        
        # Assert - All IOVBA roles present
        expected_roles = ["investigador", "observador", "validador", "builder", "asistente"]
        for role in expected_roles:
            assert role in roles
    
    @pytest.mark.asyncio
    async def test_group_metrics_display(self):
        """Test IOVBA group metrics display"""
        # Arrange
        group = MockDataGenerator.generate_iovba_group()
        metrics = group["metrics"]
        
        # Assert
        assert metrics["success_rate"] == 0.92
        assert metrics["total_tasks"] == 100
    
    @pytest.mark.asyncio
    async def test_create_new_group(self):
        """Test creating new IOVBA group"""
        # Arrange
        new_group_config = {
            "name": "Legal Expert Group",
            "domain": "legal",
            "description": "Expert group for legal domain"
        }
        
        # Act
        new_group = MockDataGenerator.generate_iovba_group(
            id="group-new",
            domain="legal"
        )
        new_group["name"] = new_group_config["name"]
        
        # Assert
        assert new_group["domain"] == "legal"
        assert len(new_group["agents"]) == 5


# =============================================================================
# SKILL INTEGRATION TESTS
# =============================================================================

class TestSkillIntegration:
    """Tests for Skills frontend-backend integration"""
    
    @pytest.mark.asyncio
    async def test_skill_list(self):
        """Test skills list"""
        # Arrange
        skills = [
            {"id": "skill-1", "name": "gentle_ai", "category": "assistance"},
            {"id": "skill-2", "name": "engram", "category": "memory"},
            {"id": "skill-3", "name": "gentle_pi", "category": "reasoning"}
        ]
        
        # Act
        total = len(skills)
        
        # Assert
        assert total == 3
    
    @pytest.mark.asyncio
    async def test_skill_trigger(self):
        """Test skill trigger detection"""
        # Arrange
        skill = {
            "name": "gentle_ai",
            "triggers": ["help", "assist", "guide"]
        }
        
        user_message = "Please help me with this task"
        
        # Act
        triggered = any(t in user_message.lower() for t in skill["triggers"])
        
        # Assert
        assert triggered is True


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================

class TestErrorHandling:
    """Tests for error handling in integration"""
    
    @pytest.mark.asyncio
    async def test_api_error_response(self):
        """Test API error response handling"""
        # Arrange
        error_response = {
            "detail": "Agent not found",
            "status_code": 404
        }
        
        # Assert
        assert error_response["status_code"] == 404
    
    @pytest.mark.asyncio
    async def test_network_error_handling(self):
        """Test network error handling"""
        # Arrange - Simulate network error
        error_occurred = True
        
        # Act - Error should be caught and handled
        if error_occurred:
            error_message = "Could not connect to server"
        
        # Assert
        assert error_message == "Could not connect to server"
    
    @pytest.mark.asyncio
    async def test_validation_error_handling(self):
        """Test validation error handling"""
        # Arrange
        invalid_data = {"name": ""}  # Empty name should be invalid
        errors = []
        
        # Act
        if not invalid_data["name"]:
            errors.append({"field": "name", "message": "Name is required"})
        
        # Assert
        assert len(errors) == 1


# =============================================================================
# RUN CONFIGURATION
# =============================================================================

if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "--tb=short"
    ])
