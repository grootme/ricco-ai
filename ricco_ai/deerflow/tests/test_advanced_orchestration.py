"""
Advanced Orchestration Integration Tests.

These tests verify complex orchestration scenarios including:
- Multi-tool coordination across skills
- Agent persona switching and model assignment
- Delegation workflows with scout agents
- Review workload forecasting
- Cross-session memory integration
- Complex prompt decomposition
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
    mem_timeline_tool,
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


class TestMultiSkillOrchestration:
    """Tests for orchestrating multiple skills together."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        """Create a temporary project directory."""
        project_dir = tmp_path / "multi_skill_project"
        project_dir.mkdir()
        (project_dir / "src").mkdir()
        (project_dir / "tests").mkdir()
        return project_dir

    def test_full_stack_feature_development(self, temp_project):
        """Test full-stack feature development using all three skills."""
        project_name = "fullstack-feature"
        change_name = "user-dashboard"

        # === PHASE 1: Configuration (Gentle-Pi) ===
        # Set persona for collaborative development
        persona = gentle_persona_tool.invoke({"persona": "gentleman"})
        assert persona["persona"] == "gentleman"

        # Configure model for SDD work
        models = gentle_models_tool.invoke({
            "agent_name": "sdd-apply",
            "thinking": "high",
        })
        assert models["status"] == "configured"

        # Run preflight checks
        preflight = sdd_preflight_tool.invoke({})
        assert preflight["status"] == "configured"

        # === PHASE 2: Memory Setup (Engram) ===
        # Start memory session
        session = mem_session_start_tool.invoke({"project": project_name})
        assert session["status"] == "started"

        # Save initial context
        mem_save_tool.invoke({
            "title": "Project Requirements",
            "content": "Build a user dashboard with real-time analytics",
            "memory_type": "user_prompt",
            "project": project_name,
        })

        # === PHASE 3: SDD Workflow (Gentle-AI) ===
        # Initialize SDD
        sdd_init_tool.invoke({
            "project_name": project_name,
            "description": "User dashboard with real-time analytics and role-based access",
        })

        # Create proposal
        proposal = sdd_proposal_tool.invoke({
            "change_name": change_name,
            "title": "User Dashboard Feature",
            "summary": "Interactive dashboard with analytics widgets",
            "motivation": "Users need visibility into their data",
            "approach": "Component-based frontend with WebSocket updates",
        })

        # === PHASE 4: Multi-domain Specs ===
        domains = [
            ("frontend", ["React components", "Chart visualizations", "WebSocket client"]),
            ("backend", ["REST API endpoints", "WebSocket server", "Data aggregation"]),
            ("auth", ["Role-based access control", "Permission checks"]),
        ]

        for domain, requirements in domains:
            spec = sdd_spec_tool.invoke({
                "change_name": change_name,
                "domain": domain,
                "requirements": requirements,
                "acceptance_criteria": [f"{domain} criterion"],
            })
            assert spec["status"] == "created"

            # Save each spec decision to memory
            mem_save_tool.invoke({
                "title": f"Spec Decision: {domain}",
                "content": json.dumps(requirements),
                "memory_type": "decision",
                "project": project_name,
            })

        # === PHASE 5: Architecture Design ===
        design = sdd_design_tool.invoke({
            "change_name": change_name,
            "architecture": "Three-tier with real-time layer",
            "components": [
                "DashboardWidget", "AnalyticsService", "WebSocketGateway",
                "PermissionGuard", "DataProvider", "ChartRenderer",
            ],
            "interfaces": [
                "GET /api/dashboard/widgets",
                "WebSocket /ws/analytics",
                "POST /api/dashboard/configure",
            ],
            "data_models": ["DashboardConfig", "Widget", "AnalyticsData"],
            "risks": ["WebSocket scaling", "Real-time data consistency"],
        })

        assert design["components_count"] == 6

        # === PHASE 6: Task Breakdown ===
        tasks = [
            {"name": "Create DashboardLayout", "description": "Main layout component", "dependencies": []},
            {"name": "Implement Widget components", "description": "Reusable widgets", "dependencies": ["Create DashboardLayout"]},
            {"name": "Build AnalyticsService", "description": "Backend service", "dependencies": []},
            {"name": "Implement WebSocket server", "description": "Real-time updates", "dependencies": ["Build AnalyticsService"]},
            {"name": "Add permission checks", "description": "RBAC implementation", "dependencies": []},
            {"name": "Integration tests", "description": "E2E testing", "dependencies": ["Implement Widget components", "Implement WebSocket server"]},
        ]

        task_result = sdd_tasks_tool.invoke({
            "change_name": change_name,
            "tasks": tasks,
            "estimated_effort": "40h",
        })

        assert task_result["tasks_count"] == 6

        # === PHASE 7: Workload Forecasting (Gentle-Pi) ===
        forecast = forecast_review_workload_tool.invoke({
            "estimated_lines_added": 1500,
            "estimated_lines_deleted": 200,
            "files_changed": 20,
        })

        # Save forecast to memory
        mem_save_tool.invoke({
            "title": "Review Forecast",
            "content": json.dumps(forecast),
            "memory_type": "session",
            "project": project_name,
        })

        # === PHASE 8: End Session ===
        mem_session_end_tool.invoke({
            "summary": "Completed full-stack feature planning",
        })

        # Verify context is available
        context = mem_context_tool.invoke({
            "project": project_name,
            "limit": 10,
        })
        assert context["status"] == "retrieved"


class TestDelegationWorkflows:
    """Tests for delegation workflows with subagents."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        return tmp_path / "delegation_project"

    def test_scout_delegation_flow(self, temp_project):
        """Test scout agent delegation for codebase exploration."""
        project_name = "scout-test"

        mem_session_start_tool.invoke({"project": project_name})

        # Check triggers - should recommend delegation for large scope
        triggers = check_delegation_triggers_tool.invoke({
            "files_read": 15,
            "files_to_write": 10,
            "session_length": "long",
            "recent_commits": 8,
        })

        # Should have triggers for scout delegation
        assert len(triggers.get("triggers_activated", [])) >= 1

        # Delegate to scout for exploration
        scout_delegation = delegate_task_tool.invoke({
            "task_description": "Explore authentication module and identify integration points",
            "agent_type": "scout",
        })
        assert scout_delegation["status"] == "delegated"

        # Simulate scout returning results
        mem_save_tool.invoke({
            "title": "Scout Report: Auth Module",
            "content": json.dumps({
                "files_analyzed": 15,
                "integration_points": ["UserService", "AuthController", "TokenManager"],
                "recommendations": ["Extract interface", "Add dependency injection"],
            }),
            "memory_type": "session",
            "project": project_name,
        })

        # Proceed with SDD based on scout findings
        sdd_init_tool.invoke({
            "project_name": project_name,
            "description": "Refactor auth based on scout analysis",
        })

        mem_session_end_tool.invoke({"summary": "Scout delegation completed"})

    def test_multi_agent_delegation(self, temp_project):
        """Test delegating to multiple agent types."""
        project_name = "multi-delegation"

        mem_session_start_tool.invoke({"project": project_name})

        # Delegate to different agents (only valid agent types)
        delegations = [
            ("scout", "Explore existing code patterns"),
            ("worker", "Implement authentication service"),
            ("reviewer", "Review security implementation"),
        ]

        for agent_type, task in delegations:
            result = delegate_task_tool.invoke({
                "task_description": task,
                "agent_type": agent_type,
            })
            assert result["status"] == "delegated"

            mem_save_tool.invoke({
                "title": f"Delegation: {agent_type}",
                "content": task,
                "memory_type": "session",
                "project": project_name,
            })

        mem_session_end_tool.invoke({"summary": "Multi-agent delegation completed"})


class TestPersonaAndModelManagement:
    """Tests for persona and model configuration."""

    def test_persona_switching(self):
        """Test switching between different personas."""
        # Only valid personas
        personas = ["gentleman", "neutral"]

        for persona_name in personas:
            result = gentle_persona_tool.invoke({"persona": persona_name})
            # Tool should accept any persona
            assert result["status"] in ["configured", "set", "switched"]

    def test_model_assignment_for_phases(self):
        """Test model assignment for different SDD phases."""
        phases = [
            ("sdd-init", "low"),
            ("sdd-proposal", "medium"),
            ("sdd-design", "high"),
            ("sdd-apply", "high"),
            ("sdd-verify", "medium"),
        ]

        for phase, thinking in phases:
            result = gentle_models_tool.invoke({
                "agent_name": phase,
                "thinking": thinking,
            })
            assert result["status"] == "configured"


class TestReviewWorkloadForecasting:
    """Tests for review workload forecasting."""

    @pytest.mark.parametrize("complexity,expected_risk", [
        ({"lines_added": 100, "lines_deleted": 10, "files": 2}, "low"),
        ({"lines_added": 400, "lines_deleted": 50, "files": 8}, "medium"),
        ({"lines_added": 2000, "lines_deleted": 500, "files": 30}, "high"),
        ({"lines_added": 5000, "lines_deleted": 1000, "files": 50}, "high"),
    ])
    def test_workload_risk_levels(self, complexity, expected_risk):
        """Test that workload forecasting correctly identifies risk levels."""
        result = forecast_review_workload_tool.invoke({
            "estimated_lines_added": complexity["lines_added"],
            "estimated_lines_deleted": complexity["lines_deleted"],
            "files_changed": complexity["files"],
        })

        assert result["status"] == "forecasted"
        assert result["risk_level"] == expected_risk

    def test_workload_with_delegation_recommendation(self):
        """Test that high workload triggers delegation recommendation."""
        high_workload = forecast_review_workload_tool.invoke({
            "estimated_lines_added": 3000,
            "estimated_lines_deleted": 800,
            "files_changed": 40,
        })

        # High risk should be identified
        assert high_workload["risk_level"] == "high"

        # Check delegation triggers
        triggers = check_delegation_triggers_tool.invoke({
            "files_read": 20,
            "files_to_write": 15,
            "session_length": "long",
        })

        # Should recommend some delegation
        assert len(triggers.get("triggers_activated", [])) >= 1


class TestPromptDecomposition:
    """Tests for decomposing complex prompts into manageable tasks."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        return tmp_path / "decomposition_project"

    def test_architectural_prompt_decomposition(self, temp_project):
        """Test decomposing an architectural change prompt."""
        project_name = "arch-decomp"
        complex_prompt = """
        Migrate from monolith to microservices:
        1. Extract user service with authentication
        2. Extract product catalog service
        3. Extract order management service
        4. Set up API gateway
        5. Implement service discovery
        """

        mem_session_start_tool.invoke({"project": project_name})

        # Parse and save prompt components
        components = [
            "user-service",
            "product-catalog-service",
            "order-service",
            "api-gateway",
            "service-discovery",
        ]

        # Save overall architecture decision
        mem_save_tool.invoke({
            "title": "Architecture Decision: Microservices",
            "content": json.dumps({"components": components}),
            "memory_type": "architecture",
            "project": project_name,
        })

        # Initialize SDD for main migration
        sdd_init_tool.invoke({
            "project_name": project_name,
            "description": "Monolith to microservices migration",
        })

        # Create design for each service
        for component in components:
            sdd_spec_tool.invoke({
                "change_name": f"{component}-spec",
                "domain": component,
                "requirements": [f"Requirements for {component}"],
                "acceptance_criteria": [f"{component} is extracted and tested"],
            })

        # Create phased task breakdown
        phases = [
            {"name": "Phase 1: Core Infrastructure", "description": "API Gateway + Service Discovery", "dependencies": []},
            {"name": "Phase 2: User Service", "description": "Extract user service", "dependencies": ["Phase 1: Core Infrastructure"]},
            {"name": "Phase 3: Product Service", "description": "Extract product service", "dependencies": ["Phase 1: Core Infrastructure"]},
            {"name": "Phase 4: Order Service", "description": "Extract order service", "dependencies": ["Phase 2: User Service", "Phase 3: Product Service"]},
            {"name": "Phase 5: Integration Testing", "description": "E2E tests", "dependencies": ["Phase 4: Order Service"]},
        ]

        tasks = sdd_tasks_tool.invoke({
            "change_name": "microservices-migration",
            "tasks": phases,
            "estimated_effort": "160h",
        })

        assert tasks["tasks_count"] == 5

        mem_session_end_tool.invoke({"summary": "Architectural decomposition complete"})

    def test_feature_with_constraints_decomposition(self, temp_project):
        """Test decomposing a feature request with constraints."""
        project_name = "feature-constraints"
        prompt = """
        Add search functionality:
        - Use Elasticsearch for production
        - Use SQLite FTS5 for development
        - Must handle 1000 queries per second
        - Results must be sorted by relevance
        """

        mem_session_start_tool.invoke({"project": project_name})

        # Save constraints
        constraints = [
            ("technology", "Elasticsearch (prod) / SQLite FTS5 (dev)"),
            ("performance", "1000 qps"),
            ("sorting", "relevance"),
        ]

        for constraint_type, value in constraints:
            mem_save_tool.invoke({
                "title": f"Constraint: {constraint_type}",
                "content": value,
                "memory_type": "session",
                "project": project_name,
            })

        # Initialize with constraints
        sdd_init_tool.invoke({
            "project_name": project_name,
            "description": "Search with dual backend support",
        })

        # Create specs with constraints
        sdd_spec_tool.invoke({
            "change_name": "search-feature",
            "domain": "search",
            "requirements": [
                "Elasticsearch client for production",
                "SQLite FTS5 for development",
                "Query optimization for 1000 qps",
            ],
            "acceptance_criteria": [
                "Search works in both environments",
                "Performance target met",
            ],
            "non_goals": ["Semantic search", "AI-powered ranking"],
        })

        mem_session_end_tool.invoke({"summary": "Feature with constraints decomposed"})


class TestCrossSessionWorkflows:
    """Tests for workflows that span multiple sessions."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        return tmp_path / "cross_session"

    def test_continue_previous_work(self, temp_project):
        """Test continuing work from a previous session."""
        project_name = "continue-work"

        # Session 1: Start feature
        mem_session_start_tool.invoke({"project": project_name})

        mem_save_tool.invoke({
            "title": "Feature Started: Authentication",
            "content": "Started implementing JWT authentication",
            "memory_type": "session",
            "project": project_name,
        })

        sdd_init_tool.invoke({
            "project_name": project_name,
            "description": "JWT authentication",
        })

        mem_session_end_tool.invoke({"summary": "Session 1: Authentication started"})

        # Session 2: Continue work
        mem_session_start_tool.invoke({"project": project_name})

        # Retrieve previous context
        context = mem_context_tool.invoke({
            "project": project_name,
            "limit": 10,
        })

        assert context["status"] == "retrieved"

        # Continue from where we left off
        search = mem_search_tool.invoke({
            "query": "Authentication",
            "project": project_name,
            "limit": 5,
        })

        # Continue SDD
        proposal = sdd_proposal_tool.invoke({
            "change_name": "jwt-auth",
            "title": "JWT Authentication",
            "summary": "Continuing from previous session",
            "motivation": "Security requirements",
            "approach": "JWT with refresh tokens",
        })

        mem_session_end_tool.invoke({"summary": "Session 2: Authentication continued"})

    def test_session_handoff(self, temp_project):
        """Test handing off work between sessions."""
        project_name = "session-handoff"

        # Session 1: Developer A starts work
        mem_session_start_tool.invoke({"project": project_name})

        mem_save_tool.invoke({
            "title": "Handoff: Work in Progress",
            "content": json.dumps({
                "completed": ["API design", "Database schema"],
                "in_progress": ["User service implementation"],
                "blocked": ["Waiting for OAuth credentials"],
                "next_steps": ["Complete user service", "Start integration tests"],
            }),
            "memory_type": "session",
            "project": project_name,
        })

        mem_session_end_tool.invoke({"summary": "Handoff created"})

        # Session 2: Developer B continues
        mem_session_start_tool.invoke({"project": project_name})

        # Find handoff
        handoff_search = mem_search_tool.invoke({
            "query": "Handoff",
            "project": project_name,
            "limit": 1,
        })

        assert handoff_search["status"] == "searched"

        # Continue from handoff
        sdd_init_tool.invoke({
            "project_name": project_name,
            "description": "Continuing from developer handoff",
        })

        mem_session_end_tool.invoke({"summary": "Continued from handoff"})


class TestErrorRecoveryWorkflows:
    """Tests for error recovery in orchestration workflows."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        return tmp_path / "error_recovery"

    def test_recovery_from_failed_verification(self, temp_project):
        """Test recovery from failed verification phase."""
        project_name = "failed-verify"
        change_name = "failing-feature"

        mem_session_start_tool.invoke({"project": project_name})

        # Setup SDD
        sdd_init_tool.invoke({
            "project_name": project_name,
            "description": "Feature that fails verification initially",
        })

        # Record failed verification
        failed_verify = sdd_verify_tool.invoke({
            "change_name": change_name,
            "verification_type": "integration",
            "results": [
                {"test": "test_user_creation", "status": "passed"},
                {"test": "test_user_authentication", "status": "failed", "error": "Timeout"},
                {"test": "test_user_deletion", "status": "passed"},
            ],
            "overall_status": "failed",
        })

        assert failed_verify["overall_status"] == "failed"

        # Save error for analysis
        mem_save_tool.invoke({
            "title": "Error: Authentication Test Timeout",
            "content": "test_user_authentication failed with timeout error",
            "memory_type": "bugfix",
            "project": project_name,
        })

        # Apply fix
        fix_apply = sdd_apply_tool.invoke({
            "change_name": change_name,
            "task_id": "fix-1",
            "tdd_phase": "GREEN",
            "test_name": "test_user_authentication",
            "test_output": "PASSED: Added timeout handling",
            "implementation_notes": "Increased timeout and added retry logic",
        })

        # Re-verify
        success_verify = sdd_verify_tool.invoke({
            "change_name": change_name,
            "verification_type": "integration",
            "results": [
                {"test": "test_user_creation", "status": "passed"},
                {"test": "test_user_authentication", "status": "passed"},
                {"test": "test_user_deletion", "status": "passed"},
            ],
            "overall_status": "passed",
        })

        assert success_verify["overall_status"] == "passed"

        # Archive with lessons learned
        sdd_archive_tool.invoke({
            "change_name": change_name,
            "summary": "Feature completed after fixing timeout issues",
            "lessons_learned": [
                "Add timeout handling for authentication tests",
                "Use retry logic for flaky operations",
                "Monitor test execution time",
            ],
        })

        mem_session_end_tool.invoke({"summary": "Recovered from verification failure"})

    def test_recovery_from_spec_change(self, temp_project):
        """Test recovery when requirements change mid-workflow."""
        project_name = "spec-change"

        mem_session_start_tool.invoke({"project": project_name})

        # Initial setup
        sdd_init_tool.invoke({
            "project_name": project_name,
            "description": "Original: Basic search",
        })

        # Original spec
        original_spec = sdd_spec_tool.invoke({
            "change_name": "search",
            "domain": "search",
            "requirements": ["Basic text search"],
            "acceptance_criteria": ["Users can search"],
        })

        # Requirement change arrives
        mem_save_tool.invoke({
            "title": "Requirement Change",
            "content": "Search must now support filters and facets",
            "memory_type": "decision",
            "project": project_name,
        })

        # Update spec
        updated_spec = sdd_spec_tool.invoke({
            "change_name": "search",
            "domain": "search",
            "requirements": [
                "Text search",
                "Filter support",
                "Facet navigation",
            ],
            "acceptance_criteria": [
                "Users can search",
                "Users can filter results",
                "Users can navigate by facets",
            ],
            "non_goals": ["AI-powered search"],
        })

        assert updated_spec["requirements_count"] == 3

        mem_session_end_tool.invoke({"summary": "Adapted to requirement change"})


class TestWorkflowMetrics:
    """Tests for tracking workflow metrics."""

    @pytest.fixture
    def temp_project(self, tmp_path):
        return tmp_path / "metrics"

    def test_workflow_efficiency_tracking(self, temp_project):
        """Test tracking efficiency metrics across a workflow."""
        project_name = "efficiency-metrics"

        mem_session_start_tool.invoke({"project": project_name})

        # Track time in each phase
        phase_times = {
            "init": 0.25,
            "proposal": 0.5,
            "spec": 1.0,
            "design": 1.5,
            "tasks": 0.25,
            "apply": 4.0,
            "verify": 1.0,
        }

        total_time = 0
        for phase, hours in phase_times.items():
            mem_save_tool.invoke({
                "title": f"Phase Time: {phase}",
                "content": json.dumps({"hours": hours, "phase": phase}),
                "memory_type": "session",
                "project": project_name,
            })
            total_time += hours

        # Save total
        mem_save_tool.invoke({
            "title": "Total Workflow Time",
            "content": json.dumps({"total_hours": total_time}),
            "memory_type": "session",
            "project": project_name,
        })

        # Get stats
        stats = mem_stats_tool.invoke({"project": project_name})
        assert stats["status"] == "retrieved"

        mem_session_end_tool.invoke({"summary": f"Workflow completed in {total_time} hours"})


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
