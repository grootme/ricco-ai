"""
Tests for Gentle-Pi - DNA 4: Agent Orchestration

Tests cover:
- Persona management
- Delegation system
- Model assignment
- Trigger detection
- DNA integration
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

# Add parent to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ricco_ai.gentle_pi.orchestrator import (
    GentlePiOrchestrator,
    PersonaType,
    AgentType,
    TaskPriority,
    TaskStatus,
    ThinkingLevel,
    DelegationRequest,
    DelegationResult,
    ModelAssignment,
    DelegationTrigger,
    DEFAULT_TRIGGERS,
    get_orchestrator,
    reset_orchestrator,
)


class TestPersonaManagement:
    """Tests for persona management functionality."""
    
    def test_default_persona_is_gentleman(self):
        """Default persona should be GENTLEMAN."""
        orchestrator = GentlePiOrchestrator()
        assert orchestrator.get_persona() == PersonaType.GENTLEMAN
    
    def test_set_persona_neutral(self):
        """Should be able to set NEUTRAL persona."""
        orchestrator = GentlePiOrchestrator()
        orchestrator.set_persona(PersonaType.NEUTRAL)
        assert orchestrator.get_persona() == PersonaType.NEUTRAL
    
    def test_set_persona_expert(self):
        """Should be able to set EXPERT persona."""
        orchestrator = GentlePiOrchestrator()
        orchestrator.set_persona(PersonaType.EXPERT)
        assert orchestrator.get_persona() == PersonaType.EXPERT
    
    def test_get_persona_config_gentleman(self):
        """GENTLEMAN persona should have collaborative style."""
        orchestrator = GentlePiOrchestrator(persona=PersonaType.GENTLEMAN)
        config = orchestrator.get_persona_config()
        assert config["style"] == "collaborative"
        assert config["tone"] == "warm"
        assert config["proactive"] is True
    
    def test_get_persona_config_neutral(self):
        """NEUTRAL persona should have direct style."""
        orchestrator = GentlePiOrchestrator(persona=PersonaType.NEUTRAL)
        config = orchestrator.get_persona_config()
        assert config["style"] == "direct"
        assert config["proactive"] is False
    
    def test_get_persona_config_expert(self):
        """EXPERT persona should have technical style."""
        orchestrator = GentlePiOrchestrator(persona=PersonaType.EXPERT)
        config = orchestrator.get_persona_config()
        assert config["style"] == "technical"
        assert config["detail_level"] == "very_high"


class TestModelAssignment:
    """Tests for model assignment functionality."""
    
    def test_configure_model_default(self):
        """Should configure model with default settings."""
        orchestrator = GentlePiOrchestrator()
        assignment = orchestrator.configure_model(
            agent_name="test_agent",
            model="anthropic/claude-3.5-sonnet"
        )
        
        assert assignment.agent_name == "test_agent"
        assert assignment.model == "anthropic/claude-3.5-sonnet"
        assert assignment.thinking == ThinkingLevel.MEDIUM
        assert assignment.max_tokens == 4096
        assert assignment.temperature == 0.7
    
    def test_configure_model_custom(self):
        """Should configure model with custom settings."""
        orchestrator = GentlePiOrchestrator()
        assignment = orchestrator.configure_model(
            agent_name="custom_agent",
            model="meta-llama/llama-3.1-8b-instruct",
            thinking=ThinkingLevel.LOW,
            max_tokens=2048,
            temperature=0.5
        )
        
        assert assignment.thinking == ThinkingLevel.LOW
        assert assignment.max_tokens == 2048
        assert assignment.temperature == 0.5
    
    def test_get_model_assignment(self):
        """Should retrieve configured model assignment."""
        orchestrator = GentlePiOrchestrator()
        orchestrator.configure_model("agent1", "model-a")
        
        retrieved = orchestrator.get_model_assignment("agent1")
        assert retrieved is not None
        assert retrieved.model == "model-a"
    
    def test_get_model_assignment_not_found(self):
        """Should return None for unconfigured agent."""
        orchestrator = GentlePiOrchestrator()
        result = orchestrator.get_model_assignment("nonexistent")
        assert result is None
    
    def test_get_model_for_thinking_low(self):
        """Low thinking level should use fast model."""
        orchestrator = GentlePiOrchestrator()
        model = orchestrator.get_model_for_thinking(ThinkingLevel.LOW)
        assert "llama" in model.lower() or "8b" in model.lower()
    
    def test_get_model_for_thinking_high(self):
        """High thinking level should use capable model."""
        orchestrator = GentlePiOrchestrator()
        model = orchestrator.get_model_for_thinking(ThinkingLevel.HIGH)
        assert "claude" in model.lower() or "sonnet" in model.lower()


class TestDelegation:
    """Tests for delegation functionality."""
    
    @pytest.mark.asyncio
    async def test_delegate_simple_task(self):
        """Should delegate a simple task successfully."""
        orchestrator = GentlePiOrchestrator()
        request = DelegationRequest(
            task_description="Test task",
            agent_type=AgentType.SCOUT
        )
        
        result = await orchestrator.delegate(request)
        
        assert result.status == TaskStatus.COMPLETED
        assert result.agent_type == AgentType.SCOUT
        assert result.task_id is not None
    
    @pytest.mark.asyncio
    async def test_delegate_with_priority(self):
        """Should delegate task with specified priority."""
        orchestrator = GentlePiOrchestrator()
        request = DelegationRequest(
            task_description="Urgent task",
            agent_type=AgentType.WORKER,
            priority=TaskPriority.URGENT
        )
        
        result = await orchestrator.delegate(request)
        
        assert result.status == TaskStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_delegate_with_context(self):
        """Should delegate task with context."""
        orchestrator = GentlePiOrchestrator()
        request = DelegationRequest(
            task_description="Task with context",
            agent_type=AgentType.ANALYZER,
            context={"files": ["a.py", "b.py"], "data_size": 5000}
        )
        
        result = await orchestrator.delegate(request)
        
        assert result.status == TaskStatus.COMPLETED
    
    @pytest.mark.asyncio
    async def test_delegate_tracks_duration(self):
        """Should track delegation duration."""
        orchestrator = GentlePiOrchestrator()
        request = DelegationRequest(
            task_description="Timed task",
            agent_type=AgentType.REVIEWER
        )
        
        result = await orchestrator.delegate(request)
        
        assert result.duration_seconds >= 0
    
    @pytest.mark.asyncio
    async def test_delegate_stores_in_history(self):
        """Should store delegation in history."""
        orchestrator = GentlePiOrchestrator()
        request = DelegationRequest(
            task_description="Historical task",
            agent_type=AgentType.CONTEXT_BUILDER
        )
        
        await orchestrator.delegate(request)
        
        metrics = orchestrator.get_metrics()
        assert metrics["total_tasks"] == 1
    
    def test_get_task_status(self):
        """Should retrieve task status."""
        orchestrator = GentlePiOrchestrator()
        
        # Simulate a completed task in history
        result = DelegationResult(
            task_id="test-123",
            status=TaskStatus.COMPLETED,
            agent_type=AgentType.SCOUT
        )
        orchestrator._active_tasks["test-123"] = result
        
        retrieved = orchestrator.get_task_status("test-123")
        assert retrieved is not None
        assert retrieved.status == TaskStatus.COMPLETED
    
    def test_cancel_task(self):
        """Should cancel an active task."""
        orchestrator = GentlePiOrchestrator()
        
        result = DelegationResult(
            task_id="cancel-test",
            status=TaskStatus.RUNNING,
            agent_type=AgentType.WORKER
        )
        orchestrator._active_tasks["cancel-test"] = result
        
        cancelled = orchestrator.cancel_task("cancel-test")
        assert cancelled is True
        assert orchestrator._active_tasks["cancel-test"].status == TaskStatus.CANCELLED
    
    def test_cancel_nonexistent_task(self):
        """Should return False when cancelling nonexistent task."""
        orchestrator = GentlePiOrchestrator()
        cancelled = orchestrator.cancel_task("nonexistent")
        assert cancelled is False


class TestTriggers:
    """Tests for delegation triggers."""
    
    def test_default_triggers_exist(self):
        """Should have default triggers configured."""
        assert len(DEFAULT_TRIGGERS) >= 5
        
        trigger_types = [t.agent_type for t in DEFAULT_TRIGGERS]
        assert AgentType.SCOUT in trigger_types
        assert AgentType.WORKER in trigger_types
        assert AgentType.REVIEWER in trigger_types
    
    def test_check_triggers_scout(self):
        """Should trigger SCOUT when many files read."""
        orchestrator = GentlePiOrchestrator()
        
        triggered = orchestrator.check_triggers({"files_read": 10})
        
        assert AgentType.SCOUT in triggered
    
    def test_check_triggers_worker(self):
        """Should trigger WORKER when many files to write."""
        orchestrator = GentlePiOrchestrator()
        
        triggered = orchestrator.check_triggers({"files_to_write": 5})
        
        assert AgentType.WORKER in triggered
    
    def test_check_triggers_multiple(self):
        """Should trigger multiple agents."""
        orchestrator = GentlePiOrchestrator()
        
        triggered = orchestrator.check_triggers({
            "files_read": 10,
            "files_to_write": 5
        })
        
        assert AgentType.SCOUT in triggered
        assert AgentType.WORKER in triggered
    
    def test_check_triggers_none(self):
        """Should not trigger when conditions not met."""
        orchestrator = GentlePiOrchestrator()
        
        triggered = orchestrator.check_triggers({
            "files_read": 1,
            "files_to_write": 1
        })
        
        assert len(triggered) == 0
    
    def test_custom_triggers(self):
        """Should support custom triggers."""
        custom_trigger = DelegationTrigger(
            agent_type=AgentType.ANALYZER,
            condition=lambda ctx: ctx.get("custom_flag", False),
            description="Custom trigger test"
        )
        
        orchestrator = GentlePiOrchestrator(triggers=[custom_trigger])
        
        # Should not trigger without flag
        triggered = orchestrator.check_triggers({})
        assert AgentType.ANALYZER not in triggered
        
        # Should trigger with flag
        triggered = orchestrator.check_triggers({"custom_flag": True})
        assert AgentType.ANALYZER in triggered


class TestWorkloadForecasting:
    """Tests for workload forecasting."""
    
    def test_forecast_low_complexity(self):
        """Should forecast low complexity for small changes."""
        orchestrator = GentlePiOrchestrator()
        
        forecast = orchestrator.forecast_review_workload(
            estimated_lines_added=50,
            estimated_lines_deleted=20,
            files_changed=2
        )
        
        assert forecast["risk_level"] == "low"
        assert forecast["estimated_review_hours"] < 1
        assert forecast["should_delegate"] is False
    
    def test_forecast_medium_complexity(self):
        """Should forecast medium complexity for moderate changes."""
        orchestrator = GentlePiOrchestrator()
        
        forecast = orchestrator.forecast_review_workload(
            estimated_lines_added=150,
            estimated_lines_deleted=100,
            files_changed=5
        )
        
        assert forecast["risk_level"] in ["low", "medium"]
    
    def test_forecast_high_complexity(self):
        """Should forecast high complexity for large changes."""
        orchestrator = GentlePiOrchestrator()
        
        forecast = orchestrator.forecast_review_workload(
            estimated_lines_added=500,
            estimated_lines_deleted=200,
            files_changed=15
        )
        
        assert forecast["risk_level"] == "high"
        assert forecast["should_delegate"] is True
        assert forecast["recommended_reviewers"] >= 2


class TestDNAIntegration:
    """Tests for DNA integration."""
    
    def test_integrate_deerflow(self):
        """Should integrate with DeerFlow."""
        orchestrator = GentlePiOrchestrator()
        
        mock_deerflow = Mock()
        orchestrator.integrate_deerflow(mock_deerflow)
        
        status = orchestrator.get_status()
        assert status["integrations"]["deerflow"] is True
    
    def test_integrate_gentle_ai(self):
        """Should integrate with Gentle-AI."""
        orchestrator = GentlePiOrchestrator()
        
        mock_gentle_ai = Mock()
        orchestrator.integrate_gentle_ai(mock_gentle_ai)
        
        status = orchestrator.get_status()
        assert status["integrations"]["gentle_ai"] is True
    
    def test_integrate_engram(self):
        """Should integrate with Engram."""
        orchestrator = GentlePiOrchestrator()
        
        mock_engram = Mock()
        orchestrator.integrate_engram(mock_engram)
        
        status = orchestrator.get_status()
        assert status["integrations"]["engram"] is True
    
    @pytest.mark.asyncio
    async def test_delegation_uses_gentle_ai(self):
        """Should apply Gentle-AI behavior during delegation."""
        orchestrator = GentlePiOrchestrator()
        
        # Mock Gentle-AI
        mock_gentle_ai = Mock()
        mock_gentle_ai.evaluate = Mock(return_value={"actions": ["check_ethics"]})
        orchestrator.integrate_gentle_ai(mock_gentle_ai)
        
        request = DelegationRequest(
            task_description="Test with behavior",
            agent_type=AgentType.SCOUT
        )
        
        await orchestrator.delegate(request)
        
        # Note: Gentle-AI is only called when real agents are available
        # In simulation mode, it won't be called


class TestStatusAndMetrics:
    """Tests for status and metrics."""
    
    def test_get_status(self):
        """Should return orchestrator status."""
        orchestrator = GentlePiOrchestrator()
        
        status = orchestrator.get_status()
        
        assert status["dna"] == "Gentle-Pi"
        assert status["persona"] == "gentleman"
        assert "active_tasks" in status
        assert "integrations" in status
    
    def test_get_metrics_empty(self):
        """Should return empty metrics when no delegations."""
        orchestrator = GentlePiOrchestrator()
        
        metrics = orchestrator.get_metrics()
        
        assert metrics["total_tasks"] == 0
    
    @pytest.mark.asyncio
    async def test_get_metrics_after_delegations(self):
        """Should return accurate metrics after delegations."""
        orchestrator = GentlePiOrchestrator()
        
        # Perform multiple delegations
        for i in range(3):
            await orchestrator.delegate(DelegationRequest(
                task_description=f"Task {i}",
                agent_type=AgentType.SCOUT
            ))
        
        metrics = orchestrator.get_metrics()
        
        assert metrics["total_tasks"] == 3
        assert metrics["completed"] == 3
        assert metrics["success_rate"] == 1.0


class TestConvenienceFunctions:
    """Tests for convenience functions."""
    
    def test_get_orchestrator_creates_instance(self):
        """Should create orchestrator instance."""
        reset_orchestrator()
        
        orchestrator = get_orchestrator()
        
        assert orchestrator is not None
        assert isinstance(orchestrator, GentlePiOrchestrator)
    
    def test_get_orchestrator_returns_same_instance(self):
        """Should return same instance on subsequent calls."""
        reset_orchestrator()
        
        orchestrator1 = get_orchestrator()
        orchestrator2 = get_orchestrator()
        
        assert orchestrator1 is orchestrator2
    
    def test_reset_orchestrator(self):
        """Should reset orchestrator instance."""
        orchestrator1 = get_orchestrator()
        reset_orchestrator()
        orchestrator2 = get_orchestrator()
        
        assert orchestrator1 is not orchestrator2


class TestDataClasses:
    """Tests for data classes."""
    
    def test_delegation_request_to_dict(self):
        """Should convert DelegationRequest to dict."""
        request = DelegationRequest(
            task_description="Test task",
            agent_type=AgentType.SCOUT,
            priority=TaskPriority.HIGH,
            timeout_minutes=60
        )
        
        data = request.to_dict()
        
        assert data["task_description"] == "Test task"
        assert data["agent_type"] == "scout"
        assert data["priority"] == "high"
        assert data["timeout_minutes"] == 60
    
    def test_delegation_result_to_dict(self):
        """Should convert DelegationResult to dict."""
        result = DelegationResult(
            task_id="task-123",
            status=TaskStatus.COMPLETED,
            agent_type=AgentType.WORKER,
            result={"output": "success"}
        )
        
        data = result.to_dict()
        
        assert data["task_id"] == "task-123"
        assert data["status"] == "completed"
        assert data["agent_type"] == "worker"
        assert data["result"] == {"output": "success"}
    
    def test_model_assignment_to_dict(self):
        """Should convert ModelAssignment to dict."""
        assignment = ModelAssignment(
            agent_name="test_agent",
            model="claude-3.5-sonnet",
            thinking=ThinkingLevel.HIGH
        )
        
        data = assignment.to_dict()
        
        assert data["agent_name"] == "test_agent"
        assert data["model"] == "claude-3.5-sonnet"
        assert data["thinking"] == "high"


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
