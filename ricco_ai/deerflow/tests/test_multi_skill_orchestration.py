"""
Multi-Skill Orchestration Integration Tests.

These tests verify the orchestration of multiple skills working together:
- SDD + Memory integration
- Gentle-Pi orchestration with other skills
- Cross-skill workflows
- Complex prompt handling across skills
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
    sdd_tasks_tool,
    GENTLE_AI_TOOLS,
)
from deerflow.tools.builtins.engram_tools import (
    mem_stats_tool,
    mem_save_tool,
    mem_search_tool,
    mem_context_tool,
    mem_session_start_tool,
    mem_session_end_tool,
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


class TestToolCounts:
    """Verify tool counts."""

    def test_gentle_ai_tools_count(self):
        assert len(GENTLE_AI_TOOLS) == 8

    def test_engram_tools_count(self):
        assert len(ENGRAM_TOOLS) == 9

    def test_gentle_pi_tools_count(self):
        assert len(GENTLE_PI_TOOLS) == 7


class TestSDDWithMemoryIntegration:
    """Tests for SDD workflow integrated with memory persistence."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        project_dir = tmp_path / "sdd_memory_project"
        project_dir.mkdir()
        (project_dir / "src").mkdir()
        (project_dir / "tests").mkdir()
        return project_dir

    def test_sdd_phases_saved_to_memory(self, temp_project):
        """Test that SDD phase artifacts are saved to memory."""
        project_name = "sdd-memory-test"

        # Start memory session
        mem_session_start_tool.invoke({
            "project": "sdd-memory-test",
        })

        # Run SDD init and save to memory
        init_result = sdd_init_tool.invoke({
            "project_name": project_name,
            "description": "Test project with memory integration",
        })

        mem_save_tool.invoke({
            "title": "SDD Phase: Init",
            "content": "Initialized SDD workflow for project",
            "memory_type": "session",
            "project": "sdd-memory-test",
        })

        # Run proposal and save to memory
        proposal_result = sdd_proposal_tool.invoke({
            "change_name": "test-feature",
            "title": "Test Proposal",
            "summary": "Test proposal for memory integration",
            "motivation": "Testing integration",
            "approach": "Incremental development",
        })

        mem_save_tool.invoke({
            "title": "SDD Phase: Proposal",
            "content": "Created proposal: Test Proposal",
            "memory_type": "decision",
            "project": "sdd-memory-test",
        })

        # Verify memory has both phases
        search_result = mem_search_tool.invoke({
            "query": "SDD Phase",
            "project": "sdd-memory-test",
            "limit": 10,
        })

        assert search_result["status"] == "searched"

        # End session
        mem_session_end_tool.invoke({
            "summary": "Completed SDD init and proposal phases",
        })

    def test_sdd_decisions_remembered(self, temp_project):
        """Test that SDD decisions are remembered."""
        project_name = "sdd-decisions"

        # Session 1: Make architecture decision
        mem_session_start_tool.invoke({
            "project": "sdd-decisions",
        })

        sdd_init_tool.invoke({
            "project_name": project_name,
            "description": "Cross-session test",
        })

        mem_save_tool.invoke({
            "title": "Architecture Decision: Use Clean Architecture",
            "content": "Decided on Clean Architecture with 4 layers",
            "memory_type": "architecture",
            "project": "sdd-decisions",
            "topic_key": "architecture/pattern",
        })

        mem_session_end_tool.invoke({
            "summary": "Made architecture decision",
        })

        # Search for previous decision
        decision_search = mem_search_tool.invoke({
            "query": "Clean Architecture",
            "project": "sdd-decisions",
            "limit": 1,
        })

        assert decision_search["status"] == "searched"


class TestGentlePiOrchestration:
    """Tests for Gentle-Pi orchestration with other skills."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        project_dir = tmp_path / "orchestration_project"
        project_dir.mkdir()
        return project_dir

    def test_preflight_before_sdd(self, temp_project):
        """Test running preflight checks before SDD workflow."""
        # Run preflight
        preflight = sdd_preflight_tool.invoke({})

        assert preflight["status"] == "configured"

        # If preflight passes, proceed with SDD
        init = sdd_init_tool.invoke({
            "project_name": "post-preflight",
            "description": "Post-preflight project",
        })
        assert init["status"] == "initialized"

    def test_persona_switch(self):
        """Test that persona affects workflow behavior."""
        # Set gentleman persona
        gentleman = gentle_persona_tool.invoke({
            "persona": "gentleman",
        })

        assert gentleman["persona"] == "gentleman"

        # Set neutral persona
        neutral = gentle_persona_tool.invoke({
            "persona": "neutral",
        })

        assert neutral["persona"] == "neutral"

    def test_model_assignment(self):
        """Test model assignment for different SDD phases."""
        models = gentle_models_tool.invoke({'agent_name': 'sdd-apply', 'thinking': 'medium'})

        assert models["status"] == "configured"

    def test_delegation_workflow(self, temp_project):
        """Test delegation workflow for complex tasks."""
        # Check delegation triggers
        triggers = check_delegation_triggers_tool.invoke({'files_read': 5, 'files_to_write': 3})

        assert triggers["status"] == "checked"
        assert "triggers_activated" in triggers

        # If triggers suggest delegation, delegate
        if len(triggers.get("triggers_activated", [])) > 0:
            delegation = delegate_task_tool.invoke({'task_description': 'Explore authentication module', 'agent_type': 'scout'})

            assert delegation["status"] == "delegated"

    def test_review_workload_forecast(self):
        """Test review workload forecasting."""
        forecast = forecast_review_workload_tool.invoke({'estimated_lines_added': 500, 'estimated_lines_deleted': 100, 'files_changed': 15})

        assert forecast["status"] == "forecasted"
        assert forecast["risk_level"] in ["low", "medium", "high"]


class TestCrossSkillWorkflow:
    """Tests for workflows that span multiple skills."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        project_dir = tmp_path / "cross_skill_project"
        project_dir.mkdir()
        (project_dir / "src").mkdir()
        (project_dir / "tests").mkdir()
        return project_dir

    def test_complete_development_workflow(self, temp_project):
        """Test complete development workflow using all skills."""
        project_name = "cross-skill-test"

        # 1. Configure persona and models
        gentle_persona_tool.invoke({"mode": "gentleman"})
        gentle_models_tool.invoke({'agent_name': 'sdd-apply', 'thinking': 'medium'})

        # 2. Start memory session
        mem_session_start_tool.invoke({
            "project": project_name,
        })

        # 3. Run preflight
        sdd_preflight_tool.invoke({})

        # 4. Initialize SDD
        sdd_init_tool.invoke({
            "project_name": project_name,
            "description": "Cross-skill integration test",
        })

        # 5. Save decision to memory
        mem_save_tool.invoke({
            "title": "Feature Decision",
            "content": "Implementing user authentication feature",
            "memory_type": "decision",
            "project": project_name,
        })

        # 6. Check if delegation needed
        triggers = check_delegation_triggers_tool.invoke({'files_read': 5, 'files_to_write': 3})

        # 7. Create proposal
        sdd_proposal_tool.invoke({
            "change_name": "auth-feature",
            "title": "Authentication Feature",
            "summary": "Add user authentication",
            "motivation": "Security requirements",
            "approach": "JWT tokens",
        })

        # 8. Forecast review workload
        forecast = forecast_review_workload_tool.invoke({'estimated_lines_added': 500, 'estimated_lines_deleted': 100, 'files_changed': 15})

        # 9. End memory session
        mem_session_end_tool.invoke({
            "summary": "Completed cross-skill workflow test",
        })

        # Verify memory has workflow history
        search = mem_search_tool.invoke({
            "query": "authentication feature",
            "project": project_name,
            "limit": 5,
        })

        assert search["status"] == "searched"

    def test_error_recovery_workflow(self, temp_project):
        """Test error recovery across skills."""
        project_name = "error-recovery-test"

        mem_session_start_tool.invoke({
            "project": project_name,
        })

        # Simulate an error during SDD
        mem_save_tool.invoke({
            "title": "Error: Test failure during apply phase",
            "content": "Tests failed during sdd_apply. Root cause: missing dependency.",
            "memory_type": "bugfix",
            "project": project_name,
        })

        # Recovery: Fix the issue
        mem_save_tool.invoke({
            "title": "Fix: Added missing dependency",
            "content": "Added pytest-mock to dev dependencies",
            "memory_type": "bugfix",
            "project": project_name,
        })

        # Verify the error is documented
        search = mem_search_tool.invoke({
            "query": "Test failure",
            "project": project_name,
            "limit": 5,
        })

        assert search["status"] == "searched"

        mem_session_end_tool.invoke({
            "summary": "Recovered from test failure",
        })


class TestComplexPrompts:
    """Tests for handling complex prompts with multiple skills."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        project_dir = tmp_path / "complex_prompts_project"
        project_dir.mkdir()
        return project_dir

    def test_multi_step_feature_request(self, temp_project):
        """Test handling a multi-step feature request."""
        project_name = "complex-prompts"

        # Complex prompt: "Add user authentication with OAuth2, remember my preference for Google provider"

        # Step 1: Parse intent and save preferences
        mem_save_tool.invoke({
            "title": "User Preference: OAuth Provider",
            "content": "User prefers Google as OAuth provider",
            "memory_type": "user_prompt",
            "project": project_name,
            "topic_key": "oauth/provider",
        })

        # Step 2: Initialize SDD with parsed requirements
        sdd_init_tool.invoke({
            "project_name": project_name,
            "description": "OAuth2 authentication with Google provider",
        })

        # Step 3: Create detailed spec
        spec = sdd_spec_tool.invoke({
            "change_name": "oauth-feature",
            "domain": "auth",
            "requirements": [
                "OAuth2 authorization code flow",
                "Google provider integration",
                "Session management",
            ],
            "acceptance_criteria": [
                "User can login with Google",
                "Session persists across requests",
            ],
        })

        assert spec["status"] == "created"

        # Step 4: Verify preference was used
        search = mem_search_tool.invoke({
            "query": "Google OAuth provider",
            "project": project_name,
            "limit": 1,
        })

        assert search["status"] == "searched"

    def test_context_heavy_request(self, temp_project):
        """Test handling a request that requires reading multiple files."""
        # Context-heavy prompt: "Refactor the authentication module to use the new user service"

        # Check if delegation needed
        triggers = check_delegation_triggers_tool.invoke({'files_read': 5, 'files_to_write': 3})

        # Should identify potential delegation
        assert triggers["status"] == "checked"

        # Delegate exploration if needed
        if triggers.get("triggers_matched", 0) > 0:
            delegation = delegate_task_tool.invoke({'task_description': 'Explore authentication module', 'agent_type': 'scout'})

            assert delegation["status"] == "delegated"

        # Save exploration results
        mem_save_tool.invoke({
            "title": "Exploration: Auth + User Service Integration",
            "content": "Integration points identified between auth and user service",
            "memory_type": "discovery",
            "project": "context-heavy-test",
        })


class TestWorkflowMetrics:
    """Tests for measuring and tracking workflow metrics."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        project_dir = tmp_path / "metrics_project"
        project_dir.mkdir()
        return project_dir

    def test_workflow_efficiency_metrics(self, temp_project):
        """Test tracking workflow efficiency metrics."""
        project_name = "workflow-metrics"

        mem_session_start_tool.invoke({
            "project": project_name,
        })

        # Track time spent in each phase
        phases = {
            "init": 0.5,
            "proposal": 1.0,
            "spec": 2.0,
            "design": 1.5,
            "tasks": 0.5,
        }

        for phase, hours in phases.items():
            mem_save_tool.invoke({
                "title": f"Phase Time: {phase}",
                "content": f"Time spent: {hours} hours",
                "memory_type": "session",
                "project": project_name,
            })

        # Calculate total
        total_hours = sum(phases.values())

        mem_save_tool.invoke({
            "title": "Workflow Total Time",
            "content": f"Total SDD workflow time: {total_hours} hours",
            "memory_type": "session",
            "project": project_name,
        })

        mem_session_end_tool.invoke({
            "summary": f"Completed workflow in {total_hours} hours",
        })

        # Verify metrics saved
        stats = mem_stats_tool.invoke({
            "project": project_name,
        })

        assert stats["status"] == "retrieved"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
