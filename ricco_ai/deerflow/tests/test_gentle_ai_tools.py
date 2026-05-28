"""Unit tests for Gentle AI tools (SDD/OpenSpec workflows)."""

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


class TestGentleAITools:
    """Tests for Gentle AI tools."""

    def test_tool_count(self):
        """Verify we have 8 Gentle AI tools."""
        assert len(GENTLE_AI_TOOLS) == 8

    def test_sdd_init(self):
        """Test SDD initialization."""
        result = sdd_init_tool.invoke({
            "project_name": "test-project",
            "description": "Test project description",
            "artifact_store": "openspec"
        })

        assert result["status"] == "initialized"
        assert result["project_name"] == "test-project"
        assert result["artifact_store"] == "openspec"
        assert "specs" in result["paths"]
        assert "changes" in result["paths"]

    def test_sdd_proposal(self):
        """Test SDD proposal creation."""
        result = sdd_proposal_tool.invoke({
            "change_name": "add-auth",
            "title": "Add Authentication",
            "summary": "Implement JWT authentication",
            "motivation": "Security requirements",
            "approach": "Use JWT tokens with refresh"
        })

        assert result["status"] == "created"
        assert result["change_name"] == "add-auth"
        assert "proposal.md" in result["artifact_path"]

    def test_sdd_spec(self):
        """Test SDD specification creation."""
        result = sdd_spec_tool.invoke({
            "change_name": "add-auth",
            "domain": "auth",
            "requirements": ["User can login", "User can logout", "Token refresh"],
            "acceptance_criteria": ["Login works", "Logout clears token"]
        })

        assert result["status"] == "created"
        assert result["domain"] == "auth"
        assert result["requirements_count"] == 3
        assert result["acceptance_criteria_count"] == 2

    def test_sdd_design(self):
        """Test SDD design creation."""
        result = sdd_design_tool.invoke({
            "change_name": "add-auth",
            "architecture": "Microservices with API Gateway",
            "components": ["AuthService", "TokenManager", "UserRepository"],
            "interfaces": ["IAuthService", "ITokenManager"],
            "risks": ["Token expiration handling"]
        })

        assert result["status"] == "created"
        assert result["components_count"] == 3

    def test_sdd_tasks(self):
        """Test SDD tasks creation."""
        result = sdd_tasks_tool.invoke({
            "change_name": "add-auth",
            "tasks": [
                {"name": "Create AuthService", "description": "Implement service"},
                {"name": "Add JWT support", "description": "Add token handling"}
            ],
            "estimated_effort": "2 weeks"
        })

        assert result["status"] == "created"
        assert result["tasks_count"] == 2
        assert result["estimated_effort"] == "2 weeks"

    def test_sdd_apply(self):
        """Test SDD apply with TDD evidence."""
        result = sdd_apply_tool.invoke({
            "change_name": "add-auth",
            "task_id": "task-1",
            "tdd_phase": "RED",
            "test_name": "test_login",
            "test_output": "FAILED: Not implemented",
            "implementation_notes": "Starting TDD cycle"
        })

        assert result["status"] == "recorded"
        assert result["tdd_phase"] == "RED"
        assert result["evidence"]["test_name"] == "test_login"

    def test_sdd_verify(self):
        """Test SDD verification."""
        result = sdd_verify_tool.invoke({
            "change_name": "add-auth",
            "verification_type": "unit",
            "results": [{"test": "test_login", "status": "passed"}],
            "overall_status": "passed"
        })

        assert result["status"] == "recorded"
        assert result["verification_type"] == "unit"
        assert result["overall_status"] == "passed"

    def test_sdd_archive(self):
        """Test SDD archive."""
        result = sdd_archive_tool.invoke({
            "change_name": "add-auth",
            "summary": "Authentication implemented successfully",
            "lessons_learned": ["JWT needs refresh tokens"]
        })

        assert result["status"] == "archived"
        assert len(result["lessons_learned"]) == 1

    def test_tool_names(self):
        """Verify all tool names are correct."""
        expected_names = [
            "sdd_init", "sdd_proposal", "sdd_spec", "sdd_design",
            "sdd_tasks", "sdd_apply", "sdd_verify", "sdd_archive"
        ]
        actual_names = [t.name for t in GENTLE_AI_TOOLS]
        assert actual_names == expected_names


class TestSDDWorkflowIntegration:
    """Integration tests for complete SDD workflow."""

    def test_complete_workflow(self):
        """Test a complete SDD workflow from init to archive."""
        # 1. Initialize
        init_result = sdd_init_tool.invoke({
            "project_name": "workflow-test",
            "artifact_store": "openspec"
        })
        assert init_result["status"] == "initialized"

        # 2. Create proposal
        proposal_result = sdd_proposal_tool.invoke({
            "change_name": "feature-x",
            "title": "Feature X",
            "summary": "New feature",
            "motivation": "User request",
            "approach": "Standard implementation"
        })
        assert proposal_result["status"] == "created"

        # 3. Create spec
        spec_result = sdd_spec_tool.invoke({
            "change_name": "feature-x",
            "domain": "features",
            "requirements": ["Requirement 1"],
            "acceptance_criteria": ["Criteria 1"]
        })
        assert spec_result["status"] == "created"

        # 4. Create design
        design_result = sdd_design_tool.invoke({
            "change_name": "feature-x",
            "architecture": "Simple",
            "components": ["Component1"]
        })
        assert design_result["status"] == "created"

        # 5. Create tasks
        tasks_result = sdd_tasks_tool.invoke({
            "change_name": "feature-x",
            "tasks": [{"name": "Task 1"}]
        })
        assert tasks_result["status"] == "created"

        # 6. Apply (TDD cycle)
        for phase in ["RED", "GREEN", "REFACTOR"]:
            apply_result = sdd_apply_tool.invoke({
                "change_name": "feature-x",
                "task_id": "task-1",
                "tdd_phase": phase
            })
            assert apply_result["status"] == "recorded"

        # 7. Verify
        verify_result = sdd_verify_tool.invoke({
            "change_name": "feature-x",
            "verification_type": "unit",
            "results": [],
            "overall_status": "passed"
        })
        assert verify_result["status"] == "recorded"

        # 8. Archive
        archive_result = sdd_archive_tool.invoke({
            "change_name": "feature-x",
            "summary": "Completed"
        })
        assert archive_result["status"] == "archived"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
