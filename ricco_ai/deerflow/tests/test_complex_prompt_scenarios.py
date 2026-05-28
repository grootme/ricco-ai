"""
Complex Prompt Scenarios Integration Tests.

These tests simulate real-world complex prompts and verify:
- Multi-intent prompt handling
- Long context management
- Ambiguity resolution
- Sequential task orchestration
- Error recovery from complex states
"""

import json
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from deerflow.tools.builtins.gentle_ai_tools import (
    sdd_init_tool,
    sdd_proposal_tool,
    sdd_spec_tool,
    sdd_design_tool,
    sdd_tasks_tool,
)
from deerflow.tools.builtins.engram_tools import (
    mem_save_tool,
    mem_search_tool,
    mem_context_tool,
    mem_session_start_tool,
    mem_session_end_tool,
)
from deerflow.tools.builtins.gentle_pi_tools import (
    gentle_persona_tool,
    delegate_task_tool,
    check_delegation_triggers_tool,
    forecast_review_workload_tool,
)


class PromptScenario:
    """Helper class for defining test scenarios."""

    def __init__(self, name: str, prompt: str, expected_intents: list, complexity: str):
        self.name = name
        self.prompt = prompt
        self.expected_intents = expected_intents
        self.complexity = complexity


# Define test scenarios
SIMPLE_SCENARIOS = [
    PromptScenario(
        name="single_feature",
        prompt="Add a login button to the homepage",
        expected_intents=["add_feature"],
        complexity="simple",
    ),
    PromptScenario(
        name="bug_fix",
        prompt="Fix the null pointer exception in UserService",
        expected_intents=["fix_bug"],
        complexity="simple",
    ),
    PromptScenario(
        name="refactor_single",
        prompt="Rename the 'getData' method to 'fetchData'",
        expected_intents=["refactor"],
        complexity="simple",
    ),
]

MEDIUM_SCENARIOS = [
    PromptScenario(
        name="multi_file_change",
        prompt="Implement user authentication with JWT tokens and add rate limiting",
        expected_intents=["add_feature", "add_feature"],
        complexity="medium",
    ),
    PromptScenario(
        name="refactor_with_tests",
        prompt="Refactor the payment module to use Stripe and ensure all tests pass",
        expected_intents=["refactor", "test"],
        complexity="medium",
    ),
    PromptScenario(
        name="feature_with_constraints",
        prompt="Add search functionality using Elasticsearch, but keep it compatible with SQLite for development",
        expected_intents=["add_feature", "constraint"],
        complexity="medium",
    ),
]

COMPLEX_SCENARIOS = [
    PromptScenario(
        name="architectural_change",
        prompt="Migrate the monolithic application to microservices, starting with user and payment services",
        expected_intents=["architecture", "migration", "compatibility"],
        complexity="complex",
    ),
    PromptScenario(
        name="full_stack_feature",
        prompt="Build a real-time notification system with WebSocket, React frontend, Python backend, and Redis pub/sub",
        expected_intents=["frontend", "backend", "infrastructure", "testing"],
        complexity="complex",
    ),
    PromptScenario(
        name="performance_optimization",
        prompt="Optimize for 10x more users with caching, query optimization, and horizontal scaling",
        expected_intents=["optimization", "infrastructure", "documentation"],
        complexity="complex",
    ),
]


class TestSimplePromptScenarios:
    """Tests for simple prompt scenarios."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        project_dir = tmp_path / "simple_scenarios"
        project_dir.mkdir()
        (project_dir / "src").mkdir()
        return project_dir

    @pytest.fixture
    def session_id(self):
        return "simple-scenario-session"

    @pytest.mark.parametrize("scenario", SIMPLE_SCENARIOS)
    def test_simple_scenario_execution(self, temp_project, session_id, scenario):
        """Test execution of simple prompt scenarios."""
        project_name = scenario.name

        # Start session
        mem_session_start_tool.invoke({
            "project": scenario.name,
        })

        # Save prompt for context
        mem_save_tool.invoke({
            "title": f"User Prompt: {scenario.name}",
            "content": scenario.prompt,
            "memory_type": "user_prompt",
            "project": scenario.name,
        })

        # For simple scenarios, direct execution is expected
        triggers = check_delegation_triggers_tool.invoke({
            "files_read": 1,
            "files_to_modify": 1,
            "session_length": "short",
            "recent_commits": 0,
        })

        # Execute directly
        if "feature" in str(scenario.expected_intents):
            sdd_init_tool.invoke({
                "project_name": project_name,
                "description": scenario.prompt,
            })

        mem_session_end_tool.invoke({
            "summary": f"Completed simple scenario: {scenario.name}",
        })


class TestMediumPromptScenarios:
    """Tests for medium complexity prompt scenarios."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        project_dir = tmp_path / "medium_scenarios"
        project_dir.mkdir()
        (project_dir / "src").mkdir()
        (project_dir / "tests").mkdir()
        return project_dir

    @pytest.fixture
    def session_id(self):
        return "medium-scenario-session"

    @pytest.mark.parametrize("scenario", MEDIUM_SCENARIOS)
    def test_medium_scenario_execution(self, temp_project, session_id, scenario):
        """Test execution of medium complexity prompt scenarios."""
        project_name = scenario.name

        mem_session_start_tool.invoke({
            "project": scenario.name,
        })

        # Save prompt
        mem_save_tool.invoke({
            "title": f"User Prompt: {scenario.name}",
            "content": scenario.prompt,
            "memory_type": "user_prompt",
            "project": scenario.name,
        })

        # Check delegation triggers
        triggers = check_delegation_triggers_tool.invoke({
            "files_read": 2,
            "files_to_modify": 3,
            "session_length": "medium",
            "recent_commits": 1,
        })

        # Initialize SDD for structured approach
        sdd_init_tool.invoke({
            "project_name": project_name,
            "description": scenario.prompt,
        })

        # For multi-intent, create multiple memories
        if len(scenario.expected_intents) > 1:
            for i, intent in enumerate(scenario.expected_intents):
                mem_save_tool.invoke({
                    "title": f"Intent {i+1}: {intent}",
                    "content": f"Processing intent: {intent}",
                    "memory_type": "session",
                    "project": scenario.name,
                })

        # Forecast review workload
        forecast = forecast_review_workload_tool.invoke({'estimated_lines_added': 200, 'estimated_lines_deleted': 50, 'files_changed': 3})

        mem_session_end_tool.invoke({
            "summary": f"Completed medium scenario: {scenario.name}",
        })


class TestComplexPromptScenarios:
    """Tests for complex prompt scenarios."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        project_dir = tmp_path / "complex_scenarios"
        project_dir.mkdir()
        (project_dir / "src").mkdir()
        (project_dir / "tests").mkdir()
        (project_dir / "docs").mkdir()
        return project_dir

    @pytest.fixture
    def session_id(self):
        return "complex-scenario-session"

    @pytest.mark.parametrize("scenario", COMPLEX_SCENARIOS)
    def test_complex_scenario_execution(self, temp_project, session_id, scenario):
        """Test execution of complex prompt scenarios."""
        project_name = scenario.name

        mem_session_start_tool.invoke({
            "project": scenario.name,
        })

        # Save prompt
        mem_save_tool.invoke({
            "title": f"Complex Prompt: {scenario.name}",
            "content": scenario.prompt,
            "memory_type": "user_prompt",
            "project": scenario.name,
        })

        # Complex scenarios require delegation
        triggers = check_delegation_triggers_tool.invoke({
            "files_read": 5,
            "files_to_modify": 8,
            "session_length": "long",
            "recent_commits": 3,
        })

        # Set gentleman persona for complex work
        gentle_persona_tool.invoke({"persona": "gentleman"})

        # Delegate scouting phase
        scout = delegate_task_tool.invoke({
            "task_description": f"Explore codebase for: {scenario.name}",
            "agent_type": "scout",
        })

        mem_save_tool.invoke({
            "title": "Scout Results",
            "content": f"Exploration complete for {scenario.name}",
            "memory_type": "discovery",
            "project": scenario.name,
        })

        # Initialize full SDD workflow
        sdd_init_tool.invoke({
            "project_name": project_name,
            "description": scenario.prompt,
        })

        # Create detailed proposal
        proposal = sdd_proposal_tool.invoke({
            "change_name": f"{scenario.name}-change",
            "title": f"Proposal: {scenario.name}",
            "summary": scenario.prompt[:100],
            "motivation": "Business requirements",
            "approach": "Iterative development",
        })

        # Create specs for each intent
        for intent in scenario.expected_intents:
            sdd_spec_tool.invoke({
                "change_name": f"{scenario.name}-change",
                "domain": intent,
                "requirements": [f"Requirements for {intent}"],
                "acceptance_criteria": [f"Criteria for {intent}"],
            })

        # Forecast large review
        forecast = forecast_review_workload_tool.invoke({'estimated_lines_added': 1000, 'estimated_lines_deleted': 200, 'files_changed': 15})

        assert forecast["risk_level"] == "high"

        mem_session_end_tool.invoke({
            "summary": f"Complex scenario planned: {scenario.name}",
        })


class TestAmbiguityResolution:
    """Tests for handling ambiguous prompts."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        project_dir = tmp_path / "ambiguity_test"
        project_dir.mkdir()
        return project_dir

    @pytest.fixture
    def session_id(self):
        return "ambiguity-session"

    def test_ambiguous_scope(self, temp_project, session_id):
        """Test handling ambiguous scope in prompt."""
        project_name = "ambiguity-scope"

        mem_session_start_tool.invoke({
            "project": project_name,
        })

        # Document the ambiguity
        mem_save_tool.invoke({
            "title": "Ambiguity Detected: Scope",
            "content": "PROMPT: 'Improve performance' - ambiguous scope and metrics",
            "memory_type": "session",
            "project": project_name,
        })

        # Assume clarification: "API response time for /users endpoint"
        mem_save_tool.invoke({
            "title": "Clarification Received",
            "content": "User clarified: Reduce /users endpoint response time from 500ms to <100ms",
            "memory_type": "decision",
            "project": project_name,
        })

        # Now proceed with specific goal
        sdd_init_tool.invoke({
            "project_name": project_name,
            "description": "Optimize /users endpoint: 500ms -> <100ms",
        })

        mem_session_end_tool.invoke({
            "session_id": session_id,
            "summary": "Resolved ambiguity, proceeding with API optimization",
        })

    def test_ambiguous_technology(self, temp_project, session_id):
        """Test handling ambiguous technology choice."""
        project_name = "ambiguity-tech"

        mem_session_start_tool.invoke({
            "project": project_name,
        })

        mem_save_tool.invoke({
            "title": "Ambiguity Detected: Technology",
            "content": "PROMPT: 'Add search' - technology choice unclear",
            "memory_type": "session",
            "project": project_name,
        })

        # Assume clarification with constraint
        mem_save_tool.invoke({
            "title": "Clarification Received",
            "content": "User chose: Elasticsearch for production, SQLite FTS5 for development",
            "memory_type": "decision",
            "project": project_name,
        })

        mem_session_end_tool.invoke({
            "summary": "Resolved technology choice",
        })


class TestLongContextHandling:
    """Tests for handling long context in prompts."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        project_dir = tmp_path / "long_context"
        project_dir.mkdir()
        return project_dir

    @pytest.fixture
    def session_id(self):
        return "long-context-session"

    def test_large_codebase_context(self, temp_project, session_id):
        """Test handling requests involving large codebase context."""
        project_name = "large-context"

        mem_session_start_tool.invoke({
            "project": project_name,
        })

        # Simulate reading many files
        files_context = []
        for i in range(10):
            files_context.append({
                "file": f"src/module_{i}.py",
                "lines": 100,
            })

        # Check if delegation needed for context gathering
        triggers = check_delegation_triggers_tool.invoke({
            "files_read": 10,
            "files_to_write": 3,
        })

        # Should trigger scout delegation
        assert len(triggers.get("triggers_activated", [])) >= 1

        # Delegate context building
        scout = delegate_task_tool.invoke({"task_description": "Build context from 10 source files", "agent_type": "scout"})

        # Save consolidated context
        mem_save_tool.invoke({
            "title": "Context Summary: 10 Modules",
            "content": json.dumps(files_context, indent=2),
            "memory_type": "discovery",
            "project": project_name,
        })

        mem_session_end_tool.invoke({
            "summary": "Handled large context with delegation",
        })

    def test_historical_context_integration(self, temp_project, session_id):
        """Test integrating historical context from memory."""
        project_name = "historical-context"

        mem_session_start_tool.invoke({
            "project": project_name,
        })

        # Simulate previous session decisions
        previous_decisions = [
            {"topic": "architecture", "decision": "Use microservices"},
            {"topic": "database", "decision": "PostgreSQL for primary data"},
            {"topic": "cache", "decision": "Redis for caching"},
        ]

        for decision in previous_decisions:
            mem_save_tool.invoke({
                "title": f"Previous Decision: {decision['topic']}",
                "content": decision["decision"],
                "memory_type": "decision",
                "project": project_name,
            })

        # Get context for current task
        context = mem_context_tool.invoke({
            "project": project_name,
            "limit": 10,
        })

        # Use context to inform new task
        sdd_init_tool.invoke({
            "project_name": project_name,
            "description": "Add new microservice (consistent with architecture decision)",
        })

        mem_session_end_tool.invoke({
            "summary": "Integrated historical context for new feature",
        })


class TestSequentialTaskOrchestration:
    """Tests for sequential task orchestration."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        project_dir = tmp_path / "sequential_tasks"
        project_dir.mkdir()
        (project_dir / "src").mkdir()
        (project_dir / "tests").mkdir()
        return project_dir

    @pytest.fixture
    def session_id(self):
        return "sequential-session"

    def test_dependent_task_chain(self, temp_project, session_id):
        """Test a chain of dependent tasks."""
        project_name = "dependent-tasks"

        mem_session_start_tool.invoke({
            "project": project_name,
        })

        # Task chain: Model -> Repository -> Service -> Controller -> Tests
        task_chain = [
            {"name": "Create User model", "description": "Define schema", "dependencies": []},
            {"name": "Create UserRepository", "description": "Database ops", "dependencies": ["Create User model"]},
            {"name": "Create UserService", "description": "Business logic", "dependencies": ["Create UserRepository"]},
            {"name": "Create UserController", "description": "HTTP endpoints", "dependencies": ["Create UserService"]},
            {"name": "Create integration tests", "description": "E2E tests", "dependencies": ["Create UserController"]},
        ]

        # Create task breakdown
        tasks_result = sdd_tasks_tool.invoke({
            "change_name": "user-feature",
            "tasks": task_chain,
            "estimated_effort": "16h",
        })

        assert tasks_result["tasks_count"] == 5

        # Execute tasks in order
        for task in task_chain:
            mem_save_tool.invoke({
                "title": f"Task Started: {task['name']}",
                "content": f"Dependencies: {task['dependencies']}",
                "memory_type": "session",
                "project": project_name,
            })

        mem_session_end_tool.invoke({
            "summary": "Executed dependent task chain",
        })

    def test_parallel_task_groups(self, temp_project, session_id):
        """Test parallel execution of independent task groups."""
        project_name = "parallel-tasks"

        mem_session_start_tool.invoke({
            "project": project_name,
        })

        # Parallel groups
        sdd_tasks_tool.invoke({
            "change_name": "parallel-feature",
            "tasks": [
                # Group A - Auth
                {"name": "Auth model", "description": "Auth schema", "dependencies": []},
                {"name": "Auth service", "description": "Auth logic", "dependencies": ["Auth model"]},
                # Group B - Payment
                {"name": "Payment model", "description": "Payment schema", "dependencies": []},
                {"name": "Payment service", "description": "Payment logic", "dependencies": ["Payment model"]},
                # Integration
                {"name": "Integration tests", "description": "E2E", "dependencies": ["Auth service", "Payment service"]},
            ],
            "estimated_effort": "14h",
        })

        mem_session_end_tool.invoke({
            "summary": "Parallel task groups identified",
        })


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
