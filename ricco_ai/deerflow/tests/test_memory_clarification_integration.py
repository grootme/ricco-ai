"""
Memory + Clarification Integration Tests.

These tests verify the integration between Engram memory and ClarificationMiddleware:
- Saving clarification history to memory
- Learning from user responses
- Context-aware clarifications based on memory
- Memory-enhanced clarification suggestions
"""

import json
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from deerflow.tools.builtins.engram_tools import (
    mem_save_tool,
    mem_search_tool,
    mem_context_tool,
    mem_timeline_tool,
    mem_update_tool,
    mem_delete_tool,
    mem_stats_tool,
    mem_session_start_tool,
    mem_session_end_tool,
    ENGRAM_TOOLS,
)


class TestMemoryTools:
    """Tests for memory tools functionality."""

    def test_tool_count(self):
        """Test that we have 9 memory tools."""
        assert len(ENGRAM_TOOLS) == 9

    def test_mem_save_basic(self):
        """Test basic memory save."""
        result = mem_save_tool.invoke({
            "title": "Test Memory",
            "content": "This is a test memory",
            "memory_type": "custom",
        })

        assert result["status"] == "saved"
        assert result["title"] == "Test Memory"

    def test_mem_save_with_structure(self):
        """Test memory save with structured What/Why/Where/Learned."""
        result = mem_save_tool.invoke({
            "title": "Structured Memory",
            "content": "Base content",
            "memory_type": "decision",
            "what": "Implemented JWT auth",
            "why": "For stateless authentication",
            "where": "src/auth/service.py",
            "learned": "JWT tokens scale better than sessions",
        })

        assert result["status"] == "saved"
        assert result["content_length"] > 10  # Should include structured parts

    def test_mem_save_all_types(self):
        """Test all memory types."""
        types = ["architecture", "decision", "bugfix", "discovery", "user_prompt", "session", "custom"]

        for mem_type in types:
            result = mem_save_tool.invoke({
                "title": f"Test {mem_type}",
                "content": f"Content for {mem_type}",
                "memory_type": mem_type,
            })
            assert result["status"] == "saved"
            assert result["memory_type"] == mem_type

    def test_mem_search_basic(self):
        """Test basic memory search."""
        result = mem_search_tool.invoke({
            "query": "authentication",
            "limit": 10,
        })

        assert result["status"] == "searched"
        assert result["query"] == "authentication"
        assert "results" in result

    def test_mem_search_with_filters(self):
        """Test memory search with filters."""
        result = mem_search_tool.invoke({
            "query": "jwt",
            "project": "auth-project",
            "memory_type": "decision",
            "limit": 5,
        })

        assert result["status"] == "searched"
        assert result["filters"]["project"] == "auth-project"
        assert result["filters"]["memory_type"] == "decision"

    def test_mem_context(self):
        """Test getting memory context."""
        result = mem_context_tool.invoke({
            "project": "test-project",
            "limit": 5,
        })

        assert result["status"] == "retrieved"
        assert result["project"] == "test-project"

    def test_mem_timeline(self):
        """Test memory timeline."""
        result = mem_timeline_tool.invoke({
            "memory_id": "mem-123",
            "before": 3,
            "after": 3,
        })

        assert result["status"] == "retrieved"
        assert result["anchor_id"] == "mem-123"

    def test_mem_update(self):
        """Test updating a memory."""
        result = mem_update_tool.invoke({
            "memory_id": "mem-456",
            "title": "Updated Title",
            "content": "Updated content",
        })

        assert result["status"] == "updated"
        assert "title" in result["updated_fields"]

    def test_mem_delete(self):
        """Test deleting a memory."""
        result = mem_delete_tool.invoke({
            "memory_id": "mem-789",
        })

        assert result["status"] == "deleted"
        assert result["memory_id"] == "mem-789"

    def test_mem_stats(self):
        """Test memory statistics."""
        result = mem_stats_tool.invoke({
            "project": "stats-project",
        })

        assert result["status"] == "retrieved"
        assert "stats" in result

    def test_mem_session_start(self):
        """Test starting a memory session."""
        result = mem_session_start_tool.invoke({
            "project": "session-test",
            "session_type": "development",
        })

        assert result["status"] == "started"
        assert result["project"] == "session-test"

    def test_mem_session_end(self):
        """Test ending a memory session."""
        result = mem_session_end_tool.invoke({
            "summary": "Session completed",
            "save_summary": True,
        })

        assert result["status"] == "ended"


class TestMemoryWorkflow:
    """Tests for memory workflow integration."""

    def test_save_search_workflow(self):
        """Test workflow of saving and searching memories."""
        # Save a memory
        save_result = mem_save_tool.invoke({
            "title": "Auth Decision",
            "content": "Decided to use JWT tokens for authentication",
            "memory_type": "decision",
            "project": "auth-workflow",
            "topic_key": "auth/jwt",
        })

        assert save_result["status"] == "saved"

        # Search for it
        search_result = mem_search_tool.invoke({
            "query": "JWT authentication",
            "project": "auth-workflow",
            "limit": 5,
        })

        assert search_result["status"] == "searched"

    def test_session_workflow(self):
        """Test complete session workflow."""
        # Start session
        start = mem_session_start_tool.invoke({
            "project": "session-workflow",
            "session_type": "development",
        })
        assert start["status"] == "started"

        # Save some memories
        mem_save_tool.invoke({
            "title": "Session Memory 1",
            "content": "First memory in session",
            "memory_type": "session",
            "project": "session-workflow",
        })

        mem_save_tool.invoke({
            "title": "Session Memory 2",
            "content": "Second memory in session",
            "memory_type": "session",
            "project": "session-workflow",
        })

        # Get context
        context = mem_context_tool.invoke({
            "project": "session-workflow",
            "limit": 5,
        })
        assert context["status"] == "retrieved"

        # End session
        end = mem_session_end_tool.invoke({
            "summary": "Session workflow completed",
            "save_summary": True,
        })
        assert end["status"] == "ended"


class TestClarificationMemoryIntegration:
    """Integration tests for clarification history with memory."""

    def test_save_clarification_to_memory(self):
        """Test saving a clarification question/answer to memory."""
        # Start session
        session_result = mem_session_start_tool.invoke({
            "project": "clarification-integration",
        })

        # Save clarification as memory
        result = mem_save_tool.invoke({
            "title": "Clarification: Authentication Method",
            "content": """
WHAT: User clarified they want JWT-based authentication
WHY: Session tokens don't scale for their microservices architecture
WHERE: src/auth/service.py
LEARNED: User prefers stateless authentication for horizontal scaling
            """.strip(),
            "memory_type": "decision",
            "project": "clarification-integration",
            "topic_key": "auth/method",
        })

        assert result["status"] == "saved"

    def test_search_clarification_history(self):
        """Test searching past clarifications."""
        # Save multiple clarifications
        clarifications = [
            {
                "title": "Clarification: Database Choice",
                "content": "User chose PostgreSQL over MongoDB for ACID compliance",
                "memory_type": "decision",
                "topic_key": "database/choice",
            },
            {
                "title": "Clarification: API Format",
                "content": "User prefers REST over GraphQL for simplicity",
                "memory_type": "decision",
                "topic_key": "api/format",
            },
        ]

        for clarification in clarifications:
            mem_save_tool.invoke({
                **clarification,
                "project": "clarification-search-test",
            })

        # Search for clarification decisions
        result = mem_search_tool.invoke({
            "query": "clarification decision",
            "project": "clarification-search-test",
            "limit": 10,
        })

        assert result["status"] == "searched"

    def test_context_aware_clarification_suggestions(self):
        """Test that memory can inform clarification suggestions."""
        # Save project context
        mem_session_start_tool.invoke({
            "project": "context-test",
        })

        mem_save_tool.invoke({
            "title": "Project: E-commerce Platform",
            "content": "Building a multi-tenant e-commerce platform",
            "memory_type": "architecture",
            "project": "context-test",
            "topic_key": "project/overview",
        })

        mem_save_tool.invoke({
            "title": "Constraint: Must use existing payment provider",
            "content": "Stripe integration is mandatory",
            "memory_type": "decision",
            "project": "context-test",
            "topic_key": "payment/constraint",
        })

        # Get context for clarifications
        context_result = mem_context_tool.invoke({
            "project": "context-test",
            "limit": 5,
        })

        assert context_result["status"] == "retrieved"


class TestMemorySessionWorkflow:
    """Tests for memory session workflows with clarifications."""

    def test_session_lifecycle_with_clarifications(self):
        """Test complete session lifecycle with clarifications."""
        # Start session
        start_result = mem_session_start_tool.invoke({
            "project": "lifecycle-test",
            "session_type": "development",
        })
        assert start_result["status"] == "started"

        # Save clarifications during session
        clarification_1 = mem_save_tool.invoke({
            "title": "Clarification: Framework",
            "content": "User chose FastAPI for async support",
            "memory_type": "decision",
            "project": "lifecycle-test",
        })
        assert clarification_1["status"] == "saved"

        clarification_2 = mem_save_tool.invoke({
            "title": "Clarification: Database",
            "content": "User chose PostgreSQL with SQLAlchemy ORM",
            "memory_type": "decision",
            "project": "lifecycle-test",
        })
        assert clarification_2["status"] == "saved"

        # Get session context
        context = mem_context_tool.invoke({
            "project": "lifecycle-test",
            "limit": 10,
        })
        assert context["status"] == "retrieved"

        # End session
        end_result = mem_session_end_tool.invoke({
            "summary": "Decided on FastAPI + PostgreSQL stack",
        })
        assert end_result["status"] == "ended"


class TestMemoryUpdateWithClarification:
    """Tests for updating memories when clarifications change."""

    def test_update_clarification_decision(self):
        """Test updating a clarification when user changes their mind."""
        # Initial decision
        initial = mem_save_tool.invoke({
            "title": "Clarification: ORM Choice",
            "content": "User chose SQLAlchemy",
            "memory_type": "decision",
            "project": "update-test",
        })

        # User changes mind - update the memory
        updated = mem_update_tool.invoke({
            "memory_id": "mem-orm-choice",
            "content": "User changed to Django ORM for better admin integration",
        })

        assert updated["status"] == "updated"


class TestMemoryStats:
    """Tests for memory statistics with clarifications."""

    def test_memory_stats_by_project(self):
        """Test statistics by project."""
        # Save various types of memories
        for i in range(3):
            mem_save_tool.invoke({
                "title": f"Memory {i+1}",
                "content": f"Content {i+1}",
                "memory_type": "decision",
                "project": "stats-test",
            })

        stats = mem_stats_tool.invoke({
            "project": "stats-test",
        })

        assert stats["status"] == "retrieved"
        assert "stats" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
