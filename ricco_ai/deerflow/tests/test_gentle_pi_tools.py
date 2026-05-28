"""Unit tests for Gentle-Pi tools (persona and orchestration)."""

import pytest
from deerflow.tools.builtins.gentle_pi_tools import (
    gentle_persona_tool,
    gentle_models_tool,
    sdd_preflight_tool,
    skill_registry_refresh_tool,
    delegate_task_tool,
    check_delegation_triggers_tool,
    forecast_review_workload_tool,
    GENTLE_PI_TOOLS,
)


class TestGentlePiTools:
    """Tests for Gentle-Pi tools."""

    def test_tool_count(self):
        """Verify we have 7 Gentle-Pi tools."""
        assert len(GENTLE_PI_TOOLS) == 7

    def test_gentle_persona_gentleman(self):
        """Test setting gentleman persona."""
        result = gentle_persona_tool.invoke({
            "persona": "gentleman"
        })

        assert result["status"] == "switched"
        assert result["persona"] == "gentleman"
        assert "Senior architect" in result["description"]

    def test_gentle_persona_neutral(self):
        """Test setting neutral persona."""
        result = gentle_persona_tool.invoke({
            "persona": "neutral"
        })

        assert result["status"] == "switched"
        assert result["persona"] == "neutral"
        assert "Professional" in result["description"]

    def test_gentle_models(self):
        """Test model configuration."""
        result = gentle_models_tool.invoke({
            "agent_name": "sdd-verify",
            "model": "anthropic/claude-sonnet-4",
            "thinking": "high"
        })

        assert result["status"] == "configured"
        assert result["agent_name"] == "sdd-verify"
        assert result["model"] == "anthropic/claude-sonnet-4"
        assert result["thinking"] == "high"

    def test_gentle_models_all_thinking_levels(self):
        """Test all thinking effort levels."""
        levels = ["off", "low", "medium", "high", "inherit"]

        for level in levels:
            result = gentle_models_tool.invoke({
                "agent_name": f"agent-{level}",
                "thinking": level
            })
            assert result["status"] == "configured"
            assert result["thinking"] == level

    def test_sdd_preflight(self):
        """Test SDD preflight configuration."""
        result = sdd_preflight_tool.invoke({
            "execution_mode": "interactive",
            "artifact_store": "openspec",
            "pr_strategy": "auto-forecast",
            "review_budget_lines": 500
        })

        assert result["status"] == "configured"
        assert result["execution_mode"] == "interactive"
        assert result["artifact_store"] == "openspec"
        assert result["pr_strategy"] == "auto-forecast"
        assert result["review_budget_lines"] == 500
        assert result["ready"] is True

    def test_sdd_preflight_all_stores(self):
        """Test all artifact store options."""
        stores = ["openspec", "engram", "both"]

        for store in stores:
            result = sdd_preflight_tool.invoke({
                "artifact_store": store
            })
            assert result["artifact_store"] == store

    def test_sdd_preflight_all_pr_strategies(self):
        """Test all PR strategy options."""
        strategies = ["auto-forecast", "ask-always", "single-pr-default", "force-chained"]

        for strategy in strategies:
            result = sdd_preflight_tool.invoke({
                "pr_strategy": strategy
            })
            assert result["pr_strategy"] == strategy

    def test_skill_registry_refresh(self):
        """Test skill registry refresh."""
        result = skill_registry_refresh_tool.invoke({
            "scan_user_skills": True,
            "scan_project_skills": True
        })

        assert result["status"] == "refreshed"
        assert result["registry_path"] == ".atl/skill-registry.md"
        assert len(result["skill_roots_scanned"]) > 0

    def test_delegate_task(self):
        """Test task delegation."""
        result = delegate_task_tool.invoke({
            "task_description": "Analyze authentication flow",
            "agent_type": "scout",
            "context_files": ["src/auth/login.ts", "src/auth/middleware.ts"],
            "fresh_context": True
        })

        assert result["status"] == "delegated"
        assert result["agent_type"] == "scout"
        assert len(result["context_files"]) == 2

    def test_delegate_task_all_types(self):
        """Test delegation to all agent types."""
        agent_types = ["scout", "worker", "reviewer", "context-builder"]

        for agent_type in agent_types:
            result = delegate_task_tool.invoke({
                "task_description": f"Task for {agent_type}",
                "agent_type": agent_type
            })
            assert result["status"] == "delegated"
            assert result["agent_type"] == agent_type

    def test_check_delegation_triggers_no_triggers(self):
        """Test delegation check with no triggers."""
        result = check_delegation_triggers_tool.invoke({
            "files_read": 2,
            "files_to_write": 1,
            "tool_calls": 5,
            "exploratory_reads": 2,
            "non_mechanical_edits": 1
        })

        assert result["status"] == "checked"
        assert len(result["triggers_activated"]) == 0

    def test_check_delegation_triggers_four_file_rule(self):
        """Test four file rule trigger."""
        result = check_delegation_triggers_tool.invoke({
            "files_read": 5,
            "files_to_write": 0,
            "tool_calls": 10,
            "exploratory_reads": 0,
            "non_mechanical_edits": 0
        })

        assert "four_file_rule" in result["triggers_activated"]
        assert len(result["recommendations"]) > 0

    def test_check_delegation_triggers_multiple(self):
        """Test multiple triggers activated."""
        result = check_delegation_triggers_tool.invoke({
            "files_read": 5,
            "files_to_write": 3,
            "tool_calls": 25,
            "exploratory_reads": 6,
            "non_mechanical_edits": 3
        })

        assert len(result["triggers_activated"]) >= 3
        assert len(result["recommendations"]) >= 3

    def test_forecast_review_workload_low(self):
        """Test low risk workload forecast."""
        result = forecast_review_workload_tool.invoke({
            "estimated_lines_added": 50,
            "estimated_lines_deleted": 10,
            "files_changed": 3,
            "areas_touched": ["auth"]
        })

        assert result["status"] == "forecasted"
        assert result["total_lines"] == 60
        assert result["risk_level"] == "low"

    def test_forecast_review_workload_medium(self):
        """Test medium risk workload forecast."""
        result = forecast_review_workload_tool.invoke({
            "estimated_lines_added": 150,
            "estimated_lines_deleted": 100,
            "files_changed": 5,
            "areas_touched": ["auth", "api"]
        })

        assert result["risk_level"] == "medium"
        assert result["total_lines"] == 250

    def test_forecast_review_workload_high(self):
        """Test high risk workload forecast."""
        result = forecast_review_workload_tool.invoke({
            "estimated_lines_added": 400,
            "estimated_lines_deleted": 200,
            "files_changed": 15,
            "areas_touched": ["auth", "api", "ui", "db"]
        })

        assert result["risk_level"] == "high"
        assert result["total_lines"] == 600
        assert len(result["recommendations"]) > 0

    def test_tool_names(self):
        """Verify all tool names are correct."""
        expected_names = [
            "gentle_persona", "gentle_models", "sdd_preflight",
            "skill_registry_refresh", "delegate_task",
            "check_delegation_triggers", "forecast_review_workload"
        ]
        actual_names = [t.name for t in GENTLE_PI_TOOLS]
        assert actual_names == expected_names


class TestOrchestrationWorkflow:
    """Integration tests for orchestration workflow."""

    def test_full_delegation_workflow(self):
        """Test complete delegation decision workflow."""
        # 1. Check triggers
        trigger_result = check_delegation_triggers_tool.invoke({
            "files_read": 5,
            "files_to_write": 2,
            "tool_calls": 15
        })

        # 2. If triggers, delegate
        if trigger_result["triggers_activated"]:
            delegate_result = delegate_task_tool.invoke({
                "task_description": "Complex implementation task",
                "agent_type": "worker",
                "fresh_context": True
            })
            assert delegate_result["status"] == "delegated"

    def test_review_forecast_workflow(self):
        """Test review workload forecasting."""
        # Forecast before making changes
        forecast = forecast_review_workload_tool.invoke({
            "estimated_lines_added": 200,
            "estimated_lines_deleted": 50,
            "files_changed": 8,
            "areas_touched": ["auth", "api", "ui"]
        })

        # If high risk, consider splitting
        if forecast["risk_level"] == "high":
            assert len(forecast["recommendations"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
