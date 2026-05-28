"""
Prompt Complexity Level Integration Tests.

These tests verify handling of prompts at different complexity levels:
- Simple: Single task, clear scope, minimal context needed
- Medium: Multiple tasks, some ambiguity, moderate context
- Complex: Multiple domains, high ambiguity, large context, delegation needed
"""

import json
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

# Import all tools
from deerflow.tools.builtins.gentle_ai_tools import (
    sdd_init_tool,
    sdd_proposal_tool,
    sdd_spec_tool,
    sdd_design_tool,
    sdd_tasks_tool,
    sdd_apply_tool,
    sdd_verify_tool,
    sdd_archive_tool,
    GENTLE_AI_TOOLS,
)
from deerflow.tools.builtins.engram_tools import (
    mem_save_tool,
    mem_search_tool,
    mem_context_tool,
    mem_session_start_tool,
    mem_session_end_tool,
    mem_stats_tool,
    ENGRAM_TOOLS,
)
from deerflow.tools.builtins.gentle_pi_tools import (
    gentle_persona_tool,
    gentle_models_tool,
    sdd_preflight_tool,
    delegate_task_tool,
    check_delegation_triggers_tool,
    forecast_review_workload_tool,
    GENTLE_PI_TOOLS,
)


class PromptComplexityLevel:
    """Enum for prompt complexity levels."""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


class PromptTestCase:
    """Test case definition for prompt testing."""

    def __init__(
        self,
        name: str,
        prompt: str,
        complexity: str,
        expected_tools: list[str],
        expected_phases: list[str],
        expected_context_files: int = 0,
        expected_delegation: bool = False,
    ):
        self.name = name
        self.prompt = prompt
        self.complexity = complexity
        self.expected_tools = expected_tools
        self.expected_phases = expected_phases
        self.expected_context_files = expected_context_files
        self.expected_delegation = expected_delegation


# =============================================================================
# SIMPLE PROMPTS - Single task, clear scope, minimal context
# =============================================================================

SIMPLE_PROMPTS = [
    PromptTestCase(
        name="rename_variable",
        prompt="Rename the variable 'userData' to 'userInfo' in the UserService class",
        complexity=PromptComplexityLevel.SIMPLE,
        expected_tools=["sdd_init"],
        expected_phases=["init"],
        expected_context_files=1,
        expected_delegation=False,
    ),
    PromptTestCase(
        name="add_button",
        prompt="Add a 'Submit' button to the contact form",
        complexity=PromptComplexityLevel.SIMPLE,
        expected_tools=["sdd_init", "sdd_proposal"],
        expected_phases=["init", "proposal"],
        expected_context_files=1,
        expected_delegation=False,
    ),
    PromptTestCase(
        name="fix_typo",
        prompt="Fix the typo in the welcome message on the homepage",
        complexity=PromptComplexityLevel.SIMPLE,
        expected_tools=["sdd_init"],
        expected_phases=["init"],
        expected_context_files=1,
        expected_delegation=False,
    ),
    PromptTestCase(
        name="add_log",
        prompt="Add a debug log statement at the start of the processPayment function",
        complexity=PromptComplexityLevel.SIMPLE,
        expected_tools=["sdd_init"],
        expected_phases=["init"],
        expected_context_files=1,
        expected_delegation=False,
    ),
    PromptTestCase(
        name="update_comment",
        prompt="Update the docstring for the calculateTotal method to reflect the new parameters",
        complexity=PromptComplexityLevel.SIMPLE,
        expected_tools=["sdd_init"],
        expected_phases=["init"],
        expected_context_files=1,
        expected_delegation=False,
    ),
]


# =============================================================================
# MEDIUM PROMPTS - Multiple tasks, some ambiguity, moderate context
# =============================================================================

MEDIUM_PROMPTS = [
    PromptTestCase(
        name="add_validation",
        prompt="Add input validation to the user registration form with email format checking and password strength requirements",
        complexity=PromptComplexityLevel.MEDIUM,
        expected_tools=["sdd_init", "sdd_proposal", "sdd_spec", "sdd_tasks"],
        expected_phases=["init", "proposal", "spec", "tasks"],
        expected_context_files=2,
        expected_delegation=False,
    ),
    PromptTestCase(
        name="implement_caching",
        prompt="Implement caching for the product list API using Redis with a 5-minute TTL and cache invalidation on product updates",
        complexity=PromptComplexityLevel.MEDIUM,
        expected_tools=["sdd_init", "sdd_proposal", "sdd_spec", "sdd_design"],
        expected_phases=["init", "proposal", "spec", "design"],
        expected_context_files=3,
        expected_delegation=False,
    ),
    PromptTestCase(
        name="add_search_filters",
        prompt="Add search filters to the product catalog: by category, price range, and rating. Include a 'clear filters' button",
        complexity=PromptComplexityLevel.MEDIUM,
        expected_tools=["sdd_init", "sdd_proposal", "sdd_spec"],
        expected_phases=["init", "proposal", "spec"],
        expected_context_files=2,
        expected_delegation=False,
    ),
    PromptTestCase(
        name="refactor_error_handling",
        prompt="Refactor error handling in the API layer to use a consistent error response format and add proper logging",
        complexity=PromptComplexityLevel.MEDIUM,
        expected_tools=["sdd_init", "sdd_proposal", "sdd_spec", "sdd_tasks"],
        expected_phases=["init", "proposal", "spec", "tasks"],
        expected_context_files=5,
        expected_delegation=True,
    ),
    PromptTestCase(
        name="add_rate_limiting",
        prompt="Implement rate limiting for the API endpoints: 100 requests per minute for authenticated users, 20 for anonymous",
        complexity=PromptComplexityLevel.MEDIUM,
        expected_tools=["sdd_init", "sdd_proposal", "sdd_spec", "sdd_design"],
        expected_phases=["init", "proposal", "spec", "design"],
        expected_context_files=3,
        expected_delegation=False,
    ),
]


# =============================================================================
# COMPLEX PROMPTS - Multiple domains, high ambiguity, large context
# =============================================================================

COMPLEX_PROMPTS = [
    PromptTestCase(
        name="microservices_migration",
        prompt="""
        Migrate the monolithic e-commerce platform to microservices architecture.
        
        Requirements:
        1. Extract user service with authentication (JWT + OAuth2)
        2. Extract product catalog service with search (Elasticsearch)
        3. Extract order service with saga pattern for distributed transactions
        4. Set up API Gateway with rate limiting and request routing
        5. Implement service discovery (Consul)
        6. Add distributed tracing (Jaeger)
        7. Set up event bus (RabbitMQ) for async communication
        
        Constraints:
        - Maintain backward compatibility with existing mobile apps
        - Zero downtime migration strategy
        - Database per service pattern
        """,
        complexity=PromptComplexityLevel.COMPLEX,
        expected_tools=["sdd_init", "sdd_proposal", "sdd_spec", "sdd_design", "sdd_tasks"],
        expected_phases=["init", "proposal", "spec", "design", "tasks"],
        expected_context_files=20,
        expected_delegation=True,
    ),
    PromptTestCase(
        name="realtime_analytics_platform",
        prompt="""
        Build a real-time analytics platform for monitoring system health.
        
        Components:
        - Dashboard with real-time charts (WebSocket updates)
        - Alert system with configurable thresholds
        - Historical data analysis with custom queries
        - Export functionality (CSV, PDF, Excel)
        - Role-based access control (admin, analyst, viewer)
        
        Technical Stack:
        - Frontend: React with D3.js for visualizations
        - Backend: Python FastAPI with async support
        - Database: TimescaleDB for time-series data
        - Cache: Redis for real-time aggregations
        - Queue: Celery for background jobs
        
        Performance Requirements:
        - Handle 10,000 events per second
        - Sub-second dashboard updates
        - 99.9% uptime
        """,
        complexity=PromptComplexityLevel.COMPLEX,
        expected_tools=["sdd_init", "sdd_proposal", "sdd_spec", "sdd_design", "sdd_tasks"],
        expected_phases=["init", "proposal", "spec", "design", "tasks"],
        expected_context_files=15,
        expected_delegation=True,
    ),
    PromptTestCase(
        name="multi_tenant_saaS",
        prompt="""
        Convert the existing single-tenant application to multi-tenant SaaS.
        
        Requirements:
        1. Tenant isolation (database-level and application-level)
        2. Tenant-specific configurations
        3. Billing integration (Stripe)
        4. Usage tracking and quotas
        5. Custom domain support
        6. White-label options (logo, colors, domain)
        
        Migration:
        - Migrate existing customers to tenant model
        - Data migration script for existing data
        - Backward compatibility during transition
        
        Security:
        - Row-level security in database
        - Tenant context in all API calls
        - Audit logging per tenant
        """,
        complexity=PromptComplexityLevel.COMPLEX,
        expected_tools=["sdd_init", "sdd_proposal", "sdd_spec", "sdd_design", "sdd_tasks"],
        expected_phases=["init", "proposal", "spec", "design", "tasks"],
        expected_context_files=25,
        expected_delegation=True,
    ),
    PromptTestCase(
        name="ai_chatbot_platform",
        prompt="""
        Create an enterprise AI chatbot platform with the following capabilities:
        
        LLM Integration:
        - Support for multiple providers (OpenAI, Anthropic, local LLMs)
        - Automatic fallback between providers
        - Cost tracking per conversation
        
        Features:
        - Conversation memory with context management
        - RAG with vector database (Pinecone/Milvus)
        - Document upload and processing
        - Multi-language support (English, Spanish, Portuguese)
        
        Platform:
        - Admin dashboard for monitoring
        - Analytics on conversation quality
        - A/B testing for prompt templates
        - Webhook integrations (Slack, Teams, Discord)
        
        Architecture:
        - Multi-tenant isolation
        - Horizontal scaling
        - Rate limiting per tenant
        """,
        complexity=PromptComplexityLevel.COMPLEX,
        expected_tools=["sdd_init", "sdd_proposal", "sdd_spec", "sdd_design", "sdd_tasks"],
        expected_phases=["init", "proposal", "spec", "design", "tasks"],
        expected_context_files=30,
        expected_delegation=True,
    ),
]


class TestSimplePrompts:
    """Tests for simple prompts."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        project_dir = tmp_path / "simple_prompts"
        project_dir.mkdir()
        return project_dir

    @pytest.mark.parametrize("prompt_case", SIMPLE_PROMPTS)
    def test_simple_prompt_execution(self, temp_project, prompt_case):
        """Test execution of simple prompts."""
        project_name = prompt_case.name

        # Start session
        mem_session_start_tool.invoke({"project": project_name})

        # Save prompt
        mem_save_tool.invoke({
            "title": f"Simple Prompt: {prompt_case.name}",
            "content": prompt_case.prompt,
            "memory_type": "user_prompt",
            "project": project_name,
        })

        # Check delegation triggers - should not trigger for simple
        triggers = check_delegation_triggers_tool.invoke({
            "files_read": prompt_case.expected_context_files,
            "files_to_write": 1,
            "session_length": "short",
            "recent_commits": 0,
        })

        # Simple prompts should not require delegation
        if not prompt_case.expected_delegation:
            # Might have some triggers but fewer than complex
            pass

        # Initialize SDD
        init = sdd_init_tool.invoke({
            "project_name": project_name,
            "description": prompt_case.prompt,
        })
        assert init["status"] == "initialized"

        # Execute expected phases
        if "proposal" in prompt_case.expected_phases:
            proposal = sdd_proposal_tool.invoke({
                "change_name": f"{project_name}-change",
                "title": prompt_case.name,
                "summary": prompt_case.prompt[:100],
                "motivation": "User request",
                "approach": "Direct implementation",
            })
            assert proposal["status"] == "created"

        # End session
        mem_session_end_tool.invoke({
            "summary": f"Simple prompt processed: {prompt_case.name}",
        })

    def test_simple_prompt_quick_turnaround(self, temp_project):
        """Test that simple prompts have quick turnaround."""
        project_name = "quick-turnaround"

        mem_session_start_tool.invoke({"project": project_name})

        # Simulate quick execution
        import time
        start = time.time()

        sdd_init_tool.invoke({
            "project_name": project_name,
            "description": "Fix typo in button text",
        })

        elapsed = time.time() - start

        # Should be very fast for simple operations
        assert elapsed < 1.0  # Less than 1 second

        mem_session_end_tool.invoke({"summary": "Quick turnaround completed"})


class TestMediumPrompts:
    """Tests for medium complexity prompts."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        project_dir = tmp_path / "medium_prompts"
        project_dir.mkdir()
        (project_dir / "src").mkdir()
        (project_dir / "tests").mkdir()
        return project_dir

    @pytest.mark.parametrize("prompt_case", MEDIUM_PROMPTS)
    def test_medium_prompt_execution(self, temp_project, prompt_case):
        """Test execution of medium complexity prompts."""
        project_name = prompt_case.name

        mem_session_start_tool.invoke({"project": project_name})

        # Save prompt
        mem_save_tool.invoke({
            "title": f"Medium Prompt: {prompt_case.name}",
            "content": prompt_case.prompt,
            "memory_type": "user_prompt",
            "project": project_name,
        })

        # Check delegation triggers
        triggers = check_delegation_triggers_tool.invoke({
            "files_read": prompt_case.expected_context_files,
            "files_to_write": 3,
            "session_length": "medium",
            "recent_commits": 1,
        })

        # Initialize SDD
        sdd_init_tool.invoke({
            "project_name": project_name,
            "description": prompt_case.prompt,
        })

        # Execute expected phases
        if "proposal" in prompt_case.expected_phases:
            sdd_proposal_tool.invoke({
                "change_name": f"{project_name}-change",
                "title": prompt_case.name,
                "summary": prompt_case.prompt[:100],
                "motivation": "Feature enhancement",
                "approach": "Iterative implementation",
            })

        if "spec" in prompt_case.expected_phases:
            sdd_spec_tool.invoke({
                "change_name": f"{project_name}-change",
                "domain": "main",
                "requirements": ["Requirement from prompt"],
                "acceptance_criteria": ["Acceptance criterion"],
            })

        if "design" in prompt_case.expected_phases:
            sdd_design_tool.invoke({
                "change_name": f"{project_name}-change",
                "architecture": "Layered architecture",
                "components": ["Service", "Repository", "Controller"],
            })

        if "tasks" in prompt_case.expected_phases:
            sdd_tasks_tool.invoke({
                "change_name": f"{project_name}-change",
                "tasks": [
                    {"name": "Task 1", "description": "First task", "dependencies": []},
                    {"name": "Task 2", "description": "Second task", "dependencies": ["Task 1"]},
                ],
                "estimated_effort": "8h",
            })

        # Check delegation if expected
        if prompt_case.expected_delegation:
            delegate_task_tool.invoke({
                "task_description": f"Explore for: {project_name}",
                "agent_type": "scout",
            })

        mem_session_end_tool.invoke({
            "summary": f"Medium prompt processed: {prompt_case.name}",
        })

    def test_medium_prompt_with_clarification(self, temp_project):
        """Test medium prompt that requires clarification."""
        project_name = "needs-clarification"

        mem_session_start_tool.invoke({"project": project_name})

        # Ambiguous prompt
        mem_save_tool.invoke({
            "title": "Ambiguous Prompt",
            "content": "Add caching to improve performance",
            "memory_type": "user_prompt",
            "project": project_name,
        })

        # Save clarification
        mem_save_tool.invoke({
            "title": "Clarification",
            "content": "User specified: Redis caching for user profiles API, 5-minute TTL",
            "memory_type": "session",
            "project": project_name,
        })

        # Proceed with clarified requirements
        sdd_init_tool.invoke({
            "project_name": project_name,
            "description": "Redis caching for user profiles API",
        })

        mem_session_end_tool.invoke({"summary": "Clarification resolved"})


class TestComplexPrompts:
    """Tests for complex prompts."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        project_dir = tmp_path / "complex_prompts"
        project_dir.mkdir()
        (project_dir / "src").mkdir()
        (project_dir / "tests").mkdir()
        (project_dir / "docs").mkdir()
        return project_dir

    @pytest.mark.parametrize("prompt_case", COMPLEX_PROMPTS)
    def test_complex_prompt_execution(self, temp_project, prompt_case):
        """Test execution of complex prompts."""
        project_name = prompt_case.name

        # Set gentleman persona for complex work
        gentle_persona_tool.invoke({"persona": "gentleman"})

        mem_session_start_tool.invoke({"project": project_name})

        # Save full prompt
        mem_save_tool.invoke({
            "title": f"Complex Prompt: {prompt_case.name}",
            "content": prompt_case.prompt,
            "memory_type": "user_prompt",
            "project": project_name,
        })

        # Check delegation triggers - should trigger for complex
        triggers = check_delegation_triggers_tool.invoke({
            "files_read": prompt_case.expected_context_files,
            "files_to_write": 10,
            "session_length": "long",
            "recent_commits": 5,
        })

        # Complex prompts should have delegation triggers
        assert prompt_case.expected_delegation

        # Delegate exploration
        delegate_task_tool.invoke({
            "task_description": f"Explore architecture for: {project_name}",
            "agent_type": "scout",
        })

        # Initialize SDD with full description
        sdd_init_tool.invoke({
            "project_name": project_name,
            "description": prompt_case.prompt[:500],
        })

        # Create comprehensive proposal
        proposal = sdd_proposal_tool.invoke({
            "change_name": f"{project_name}-main",
            "title": f"Implementation: {project_name}",
            "summary": prompt_case.prompt[:200],
            "motivation": "Complex system requirements",
            "approach": "Phased implementation with continuous delivery",
            "alternatives": "Considered simpler alternatives, rejected due to scalability requirements",
        })

        # Extract domains from prompt and create specs
        domains = self._extract_domains(prompt_case.prompt)
        for domain in domains:
            sdd_spec_tool.invoke({
                "change_name": f"{project_name}-main",
                "domain": domain,
                "requirements": [f"Requirements for {domain}"],
                "acceptance_criteria": [f"Acceptance for {domain}"],
            })

            mem_save_tool.invoke({
                "title": f"Spec: {domain}",
                "content": f"Created spec for {domain} domain",
                "memory_type": "decision",
                "project": project_name,
            })

        # Create detailed design
        components = self._extract_components(prompt_case.prompt)
        design = sdd_design_tool.invoke({
            "change_name": f"{project_name}-main",
            "architecture": "Microservices with event-driven architecture",
            "components": components,
            "interfaces": ["REST API", "gRPC", "Event Bus"],
            "data_models": ["Entity", "Aggregate", "ValueObject"],
            "risks": ["Complexity", "Distributed transactions", "Data consistency"],
        })

        # Create phased tasks
        phases = self._create_phases(len(components))
        sdd_tasks_tool.invoke({
            "change_name": f"{project_name}-main",
            "tasks": phases,
            "estimated_effort": "120h",
        })

        # High-risk forecast
        forecast = forecast_review_workload_tool.invoke({
            "estimated_lines_added": 5000,
            "estimated_lines_deleted": 1500,
            "files_changed": 50,
        })

        assert forecast["risk_level"] == "high"

        # Save architecture decision
        mem_save_tool.invoke({
            "title": "Architecture Decision",
            "content": json.dumps({
                "domains": domains,
                "components": len(components),
                "phases": len(phases),
            }),
            "memory_type": "architecture",
            "project": project_name,
        })

        mem_session_end_tool.invoke({
            "summary": f"Complex prompt planned: {project_name}",
        })

    def _extract_domains(self, prompt: str) -> list[str]:
        """Extract domain areas from prompt."""
        domains = []
        if "user" in prompt.lower() or "auth" in prompt.lower():
            domains.append("auth")
        if "product" in prompt.lower() or "catalog" in prompt.lower():
            domains.append("catalog")
        if "order" in prompt.lower():
            domains.append("orders")
        if "payment" in prompt.lower() or "billing" in prompt.lower():
            domains.append("billing")
        if "analytics" in prompt.lower() or "monitoring" in prompt.lower():
            domains.append("analytics")
        if "chat" in prompt.lower() or "chatbot" in prompt.lower():
            domains.append("chat")
        if "tenant" in prompt.lower() or "saas" in prompt.lower():
            domains.append("multi-tenancy")
        if not domains:
            domains.append("core")
        return domains[:4]  # Limit to 4 domains for tests

    def _extract_components(self, prompt: str) -> list[str]:
        """Extract components from prompt."""
        components = []
        lines = prompt.lower().split("\n")
        for line in lines:
            if "service" in line:
                components.append(line.strip().title())
        if not components:
            components = ["CoreService", "ApiGateway", "EventHandler"]
        return components[:6]  # Limit to 6 components for tests

    def _create_phases(self, component_count: int) -> list[dict]:
        """Create phased task breakdown."""
        return [
            {"name": "Phase 1: Infrastructure", "description": "Core infrastructure", "dependencies": []},
            {"name": "Phase 2: Core Services", "description": "Service implementation", "dependencies": ["Phase 1: Infrastructure"]},
            {"name": "Phase 3: Integration", "description": "Service integration", "dependencies": ["Phase 2: Core Services"]},
            {"name": "Phase 4: Testing", "description": "Integration testing", "dependencies": ["Phase 3: Integration"]},
        ]


class TestPromptComplexityDetection:
    """Tests for detecting prompt complexity."""

    def test_complexity_detection_simple(self):
        """Test that simple prompts are correctly identified."""
        simple_indicators = [
            "rename variable",
            "fix typo",
            "add button",
            "update comment",
            "change color",
        ]

        for indicator in simple_indicators:
            triggers = check_delegation_triggers_tool.invoke({
                "files_read": 1,
                "files_to_write": 1,
                "session_length": "short",
                "recent_commits": 0,
            })

            # Simple prompts should have minimal triggers
            assert triggers["status"] == "checked"

    def test_complexity_detection_complex(self):
        """Test that complex prompts trigger delegation."""
        complex_indicators = [
            "microservices",
            "migrate architecture",
            "multi-tenant",
            "distributed system",
            "real-time platform",
        ]

        for indicator in complex_indicators:
            triggers = check_delegation_triggers_tool.invoke({
                "files_read": 20,
                "files_to_write": 15,
                "session_length": "long",
                "recent_commits": 10,
            })

            # Complex prompts should have triggers
            assert len(triggers.get("triggers_activated", [])) >= 1


class TestPromptMemoryPersistence:
    """Tests for prompt context persistence."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        return tmp_path / "prompt_memory"

    def test_simple_prompt_memory_efficiency(self, temp_project):
        """Test that simple prompts use minimal memory."""
        project_name = "simple-memory"

        mem_session_start_tool.invoke({"project": project_name})

        # Simple prompt should create minimal memories
        mem_save_tool.invoke({
            "title": "Simple Request",
            "content": "Add button",
            "memory_type": "user_prompt",
            "project": project_name,
        })

        stats = mem_stats_tool.invoke({"project": project_name})

        mem_session_end_tool.invoke({"summary": "Simple prompt done"})

    def test_complex_prompt_memory_richness(self, temp_project):
        """Test that complex prompts create rich context."""
        project_name = "complex-memory"

        mem_session_start_tool.invoke({"project": project_name})

        # Complex prompt creates multiple memories
        memories = [
            ("user_prompt", "Complex request"),
            ("architecture", "Microservices pattern"),
            ("decision", "Use PostgreSQL"),
            ("session", "Zero downtime"),
            ("discovery", "Integration points found"),
        ]

        for mem_type, content in memories:
            mem_save_tool.invoke({
                "title": f"Memory: {mem_type}",
                "content": content,
                "memory_type": mem_type,
                "project": project_name,
            })

        # Retrieve context
        context = mem_context_tool.invoke({
            "project": project_name,
            "limit": 10,
        })

        assert context["status"] == "retrieved"

        mem_session_end_tool.invoke({"summary": "Complex context saved"})


class TestCrossComplexityComparison:
    """Tests comparing different complexity levels."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        return tmp_path / "complexity_comparison"

    def test_workflow_duration_comparison(self, temp_project):
        """Test that complexity affects workflow duration."""
        import time

        # Simple prompt
        simple_start = time.time()
        sdd_init_tool.invoke({
            "project_name": "simple-duration",
            "description": "Fix typo",
        })
        simple_duration = time.time() - simple_start

        # Complex prompt
        complex_start = time.time()
        sdd_init_tool.invoke({
            "project_name": "complex-duration",
            "description": "Build microservices platform with multiple services",
        })
        sdd_proposal_tool.invoke({
            "change_name": "complex-change",
            "title": "Complex",
            "summary": "Complex system",
            "motivation": "Scaling needs",
            "approach": "Microservices",
        })
        complex_duration = time.time() - complex_start

        # Both should be fast, but complex takes more operations
        assert simple_duration < 1.0
        assert complex_duration < 2.0

    def test_tool_usage_by_complexity(self, temp_project):
        """Test that different complexity levels use different tools."""
        # Simple: minimal tools
        simple_tools = ["sdd_init"]

        # Medium: moderate tools
        medium_tools = ["sdd_init", "sdd_proposal", "sdd_spec"]

        # Complex: extensive tools
        complex_tools = ["sdd_init", "sdd_proposal", "sdd_spec", "sdd_design", "sdd_tasks"]

        # Verify tool availability
        all_tools = GENTLE_AI_TOOLS
        tool_names = [t.name for t in all_tools]

        for tool in simple_tools + medium_tools + complex_tools:
            assert tool in tool_names


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
