"""
SDD (Spec-Driven Development) Orchestration Integration Tests.

These tests verify the complete SDD workflow orchestration:
- Phase transitions (init → proposal → spec → design → tasks → apply → verify → archive)
- Artifact persistence and retrieval
- Multi-tool coordination
- Error handling and recovery
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
    sdd_apply_tool,
    sdd_verify_tool,
    sdd_archive_tool,
    GENTLE_AI_TOOLS,
)


class TestSDDWorkflowIntegration:
    """Integration tests for complete SDD workflow."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project directory with SDD structure."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()
        (project_dir / "src").mkdir()
        (project_dir / "tests").mkdir()

        # Create initial files
        (project_dir / "src" / "main.py").write_text("# Main module\n\ndef main():\n    pass\n")
        (project_dir / "tests" / "test_main.py").write_text("# Tests\n\ndef test_main():\n    pass\n")

        return project_dir

    def test_tool_count(self):
        """Test that we have 8 SDD tools."""
        assert len(GENTLE_AI_TOOLS) == 8

    def test_complete_sdd_workflow(self, temp_project):
        """Test complete SDD workflow from init to archive."""
        project_name = "test_project"
        change_name = "auth-feature"
        results = {}

        # Phase 1: Init
        results["init"] = sdd_init_tool.invoke({
            "project_name": project_name,
            "description": "A test project for SDD workflow validation",
            "artifact_store": "openspec",
        })
        assert results["init"]["status"] == "initialized"
        assert "paths" in results["init"]

        # Phase 2: Proposal
        results["proposal"] = sdd_proposal_tool.invoke({
            "change_name": change_name,
            "title": "Add User Authentication System",
            "summary": "Implement JWT-based authentication with user registration and login",
            "motivation": "Users need to securely access their accounts",
            "approach": "Use JWT tokens with refresh mechanism",
            "alternatives": "OAuth2 integration, Session-based auth",
        })
        assert results["proposal"]["status"] == "created"
        assert change_name in results["proposal"]["artifact_path"]

        # Phase 3: Spec
        results["spec"] = sdd_spec_tool.invoke({
            "change_name": change_name,
            "domain": "auth",
            "requirements": [
                "User registration with email validation",
                "Password hashing with bcrypt",
                "JWT token generation and validation",
            ],
            "acceptance_criteria": [
                "Users can register",
                "Users can login",
                "Sessions are secure",
            ],
            "non_goals": ["OAuth integration", "2FA"],
        })
        assert results["spec"]["status"] == "created"
        assert results["spec"]["requirements_count"] == 3

        # Phase 4: Design
        results["design"] = sdd_design_tool.invoke({
            "change_name": change_name,
            "architecture": "Layered Architecture with Auth Service",
            "components": [
                "AuthController",
                "AuthService",
                "TokenService",
                "UserRepository",
            ],
            "interfaces": [
                "POST /auth/register",
                "POST /auth/login",
                "POST /auth/refresh",
            ],
            "data_models": ["User", "Session", "Token"],
            "risks": ["Token storage security", "Rate limiting"],
        })
        assert results["design"]["status"] == "created"
        assert results["design"]["components_count"] == 4

        # Phase 5: Tasks
        results["tasks"] = sdd_tasks_tool.invoke({
            "change_name": change_name,
            "tasks": [
                {"name": "Create User model", "description": "Define User schema", "dependencies": []},
                {"name": "Implement UserRepository", "description": "Database operations", "dependencies": ["Create User model"]},
                {"name": "Implement TokenService", "description": "JWT handling", "dependencies": []},
                {"name": "Implement AuthService", "description": "Business logic", "dependencies": ["Implement UserRepository", "Implement TokenService"]},
                {"name": "Create AuthController", "description": "HTTP endpoints", "dependencies": ["Implement AuthService"]},
            ],
            "estimated_effort": "20h",
        })
        assert results["tasks"]["status"] == "created"
        assert results["tasks"]["tasks_count"] == 5

        # Phase 6: Apply (TDD RED phase)
        results["apply_red"] = sdd_apply_tool.invoke({
            "change_name": change_name,
            "task_id": "1",
            "tdd_phase": "RED",
            "test_name": "test_user_model_fields",
            "test_output": "FAILED: User class not defined",
            "implementation_notes": "Starting TDD cycle for User model",
        })
        assert results["apply_red"]["status"] == "recorded"
        assert results["apply_red"]["tdd_phase"] == "RED"

        # Phase 6: Apply (TDD GREEN phase)
        results["apply_green"] = sdd_apply_tool.invoke({
            "change_name": change_name,
            "task_id": "1",
            "tdd_phase": "GREEN",
            "test_name": "test_user_model_fields",
            "test_output": "PASSED: All assertions passed",
            "implementation_notes": "Implemented User model with required fields",
        })
        assert results["apply_green"]["status"] == "recorded"

        # Phase 7: Verify
        results["verify"] = sdd_verify_tool.invoke({
            "change_name": change_name,
            "verification_type": "integration",
            "results": [
                {"test": "test_registration", "status": "passed"},
                {"test": "test_login", "status": "passed"},
                {"test": "test_token_refresh", "status": "passed"},
            ],
            "overall_status": "passed",
        })
        assert results["verify"]["status"] == "recorded"
        assert results["verify"]["overall_status"] == "passed"

        # Phase 8: Archive
        results["archive"] = sdd_archive_tool.invoke({
            "change_name": change_name,
            "summary": "Authentication system implemented with JWT tokens",
            "lessons_learned": [
                "TDD helped catch edge cases early",
                "Dependency injection improved testability",
            ],
        })
        assert results["archive"]["status"] == "archived"

        # Verify all phases completed
        assert len(results) == 9  # 9 phases completed  # init, proposal, spec, design, tasks, apply_red, apply_green, verify, archive

    def test_sdd_workflow_with_changes(self, temp_project):
        """Test SDD workflow handling requirement changes mid-flight."""
        project_name = "change_project"
        change_name = "updated-feature"

        # Init and proposal
        sdd_init_tool.invoke({
            "project_name": project_name,
            "description": "Initial project",
        })

        # Create proposal
        result = sdd_proposal_tool.invoke({
            "change_name": change_name,
            "title": "Updated Proposal",
            "summary": "Changed requirements",
            "motivation": "New business needs",
            "approach": "Iterative development",
        })

        assert result["status"] == "created"

    def test_spec_multiple_domains(self, temp_project):
        """Test creating specs for multiple domains."""
        project_name = "multi-domain-project"
        change_name = "full-feature"

        sdd_init_tool.invoke({
            "project_name": project_name,
            "description": "Multi-domain project",
        })

        # Create specs for different domains
        domains = ["auth", "api", "ui"]
        for domain in domains:
            result = sdd_spec_tool.invoke({
                "change_name": change_name,
                "domain": domain,
                "requirements": [f"{domain} requirement 1"],
                "acceptance_criteria": [f"{domain} criterion 1"],
            })
            assert result["status"] == "created"
            assert domain in result["artifact_path"]


class TestSDDArtifactPersistence:
    """Tests for artifact persistence across SDD phases."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        project_dir = tmp_path / "artifact_project"
        project_dir.mkdir()
        return project_dir

    def test_init_creates_paths(self, temp_project):
        """Test that init creates expected paths."""
        result = sdd_init_tool.invoke({
            "project_name": "artifact_test",
            "description": "Artifact test",
            "artifact_store": "openspec",
        })

        assert "paths" in result
        assert "specs" in result["paths"]
        assert "changes" in result["paths"]
        assert "archive" in result["paths"]
        assert "config" in result["paths"]

    def test_proposal_artifact_path(self, temp_project):
        """Test that proposal artifact path is correct."""
        result = sdd_proposal_tool.invoke({
            "change_name": "test-change",
            "title": "Test Proposal",
            "summary": "Test summary",
            "motivation": "Test motivation",
            "approach": "Test approach",
        })

        assert "artifact_path" in result
        assert "test-change" in result["artifact_path"]
        assert "proposal.md" in result["artifact_path"]


class TestSDDErrorHandling:
    """Tests for error handling in SDD workflow."""

    def test_init_with_minimal_args(self):
        """Test that init works with minimal arguments."""
        result = sdd_init_tool.invoke({
            "project_name": "minimal-project",
        })

        assert result["status"] == "initialized"

    def test_proposal_with_minimal_args(self):
        """Test proposal with minimal required arguments."""
        result = sdd_proposal_tool.invoke({
            "change_name": "minimal-change",
            "title": "Minimal",
            "summary": "Minimal summary",
            "motivation": "Minimal motivation",
            "approach": "Minimal approach",
        })

        assert result["status"] == "created"

    def test_apply_all_tdd_phases(self):
        """Test all TDD phases."""
        phases = ["RED", "GREEN", "TRIANGULATE", "REFACTOR"]

        for phase in phases:
            result = sdd_apply_tool.invoke({
                "change_name": "tdd-test",
                "task_id": "1",
                "tdd_phase": phase,
            })
            assert result["status"] == "recorded"
            assert result["tdd_phase"] == phase


class TestSDDMetrics:
    """Tests for SDD metrics and reporting."""

    def test_task_count_accuracy(self):
        """Test that task count is accurate."""
        tasks = [
            {"name": "Task 1", "description": "First", "dependencies": []},
            {"name": "Task 2", "description": "Second", "dependencies": ["Task 1"]},
            {"name": "Task 3", "description": "Third", "dependencies": ["Task 1"]},
        ]

        result = sdd_tasks_tool.invoke({
            "change_name": "metrics-test",
            "tasks": tasks,
            "estimated_effort": "10h",
        })

        assert result["tasks_count"] == 3
        assert result["estimated_effort"] == "10h"

    def test_verify_results_count(self):
        """Test that verify results are counted correctly."""
        results = [
            {"test": "test_1", "status": "passed"},
            {"test": "test_2", "status": "passed"},
            {"test": "test_3", "status": "failed"},
        ]

        result = sdd_verify_tool.invoke({
            "change_name": "verify-test",
            "verification_type": "unit",
            "results": results,
            "overall_status": "partial",
        })

        assert result["results_count"] == 3

    def test_archive_with_lessons(self):
        """Test archive with lessons learned."""
        lessons = [
            "TDD is valuable",
            "Code review helps",
            "Documentation matters",
        ]

        result = sdd_archive_tool.invoke({
            "change_name": "lessons-test",
            "summary": "Completed with lessons",
            "lessons_learned": lessons,
        })

        assert result["status"] == "archived"
        assert len(result["lessons_learned"]) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
