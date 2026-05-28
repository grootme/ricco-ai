"""Unit tests for Engram tools (persistent memory)."""

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


class TestEngramTools:
    """Tests for Engram memory tools."""

    def test_tool_count(self):
        """Verify we have 9 Engram tools."""
        assert len(ENGRAM_TOOLS) == 9

    def test_mem_save_basic(self):
        """Test basic memory save."""
        result = mem_save_tool.invoke({
            "title": "Test Memory",
            "content": "This is a test memory",
            "memory_type": "discovery"
        })

        assert result["status"] == "saved"
        assert result["title"] == "Test Memory"
        assert result["memory_type"] == "discovery"

    def test_mem_save_with_structure(self):
        """Test memory save with What/Why/Where/Learned structure."""
        result = mem_save_tool.invoke({
            "title": "Architecture Decision",
            "content": "Use microservices",
            "memory_type": "architecture",
            "project": "my-project",
            "topic_key": "architecture/microservices",
            "what": "Decided to use microservices",
            "why": "Scalability requirements",
            "where": "Backend architecture",
            "learned": "Need API gateway"
        })

        assert result["status"] == "saved"
        assert result["project"] == "my-project"
        assert result["topic_key"] == "architecture/microservices"

    def test_mem_save_all_types(self):
        """Test saving memories of all types."""
        memory_types = [
            "architecture", "decision", "bugfix",
            "discovery", "user_prompt", "session", "custom"
        ]

        for mem_type in memory_types:
            result = mem_save_tool.invoke({
                "title": f"Test {mem_type}",
                "content": f"Content for {mem_type}",
                "memory_type": mem_type
            })
            assert result["status"] == "saved"
            assert result["memory_type"] == mem_type

    def test_mem_search(self):
        """Test memory search."""
        result = mem_search_tool.invoke({
            "query": "microservices",
            "limit": 5
        })

        assert result["status"] == "searched"
        assert result["query"] == "microservices"
        assert result["limit"] == 5

    def test_mem_search_with_filters(self):
        """Test memory search with filters."""
        result = mem_search_tool.invoke({
            "query": "auth",
            "project": "my-project",
            "memory_type": "architecture",
            "limit": 10
        })

        assert result["status"] == "searched"
        assert result["filters"]["project"] == "my-project"
        assert result["filters"]["memory_type"] == "architecture"

    def test_mem_context(self):
        """Test getting session context."""
        result = mem_context_tool.invoke({
            "project": "my-project",
            "limit": 5
        })

        assert result["status"] == "retrieved"
        assert result["project"] == "my-project"
        assert result["limit"] == 5

    def test_mem_timeline(self):
        """Test memory timeline."""
        result = mem_timeline_tool.invoke({
            "memory_id": "mem-123",
            "before": 3,
            "after": 3
        })

        assert result["status"] == "retrieved"
        assert result["anchor_id"] == "mem-123"
        assert result["before_count"] == 3
        assert result["after_count"] == 3

    def test_mem_update(self):
        """Test memory update."""
        result = mem_update_tool.invoke({
            "memory_id": "mem-123",
            "title": "Updated Title",
            "content": "Updated content"
        })

        assert result["status"] == "updated"
        assert result["memory_id"] == "mem-123"
        assert "title" in result["updated_fields"]
        assert "content" in result["updated_fields"]

    def test_mem_delete(self):
        """Test memory deletion."""
        result = mem_delete_tool.invoke({
            "memory_id": "mem-123"
        })

        assert result["status"] == "deleted"
        assert result["memory_id"] == "mem-123"

    def test_mem_stats(self):
        """Test memory statistics."""
        result = mem_stats_tool.invoke({
            "project": "my-project"
        })

        assert result["status"] == "retrieved"
        assert result["project"] == "my-project"
        assert "total_memories" in result["stats"]
        assert "by_type" in result["stats"]

    def test_mem_session_start(self):
        """Test session start."""
        result = mem_session_start_tool.invoke({
            "project": "my-project",
            "session_type": "development"
        })

        assert result["status"] == "started"
        assert result["project"] == "my-project"
        assert result["session_type"] == "development"

    def test_mem_session_end(self):
        """Test session end."""
        result = mem_session_end_tool.invoke({
            "summary": "Completed feature implementation",
            "save_summary": True
        })

        assert result["status"] == "ended"
        assert result["summary_saved"] is True

    def test_tool_names(self):
        """Verify all tool names are correct."""
        expected_names = [
            "mem_save", "mem_search", "mem_context", "mem_timeline",
            "mem_update", "mem_delete", "mem_stats", "mem_session_start",
            "mem_session_end"
        ]
        actual_names = [t.name for t in ENGRAM_TOOLS]
        assert actual_names == expected_names


class TestMemoryWorkflow:
    """Integration tests for memory workflow."""

    def test_save_search_workflow(self):
        """Test save and search workflow."""
        # Save a memory
        save_result = mem_save_tool.invoke({
            "title": "Important Decision",
            "content": "Use PostgreSQL for main database",
            "memory_type": "decision",
            "project": "test-project",
            "topic_key": "database/postgres"
        })
        assert save_result["status"] == "saved"

        # Search for it
        search_result = mem_search_tool.invoke({
            "query": "database",
            "project": "test-project"
        })
        assert search_result["status"] == "searched"

        # Get context
        context_result = mem_context_tool.invoke({
            "project": "test-project"
        })
        assert context_result["status"] == "retrieved"

    def test_session_workflow(self):
        """Test session lifecycle."""
        # Start session
        start_result = mem_session_start_tool.invoke({
            "project": "test-project",
            "session_type": "debugging"
        })
        assert start_result["status"] == "started"

        # Save some memories
        mem_save_tool.invoke({
            "title": "Bug Found",
            "content": "Null pointer in auth flow",
            "memory_type": "bugfix",
            "project": "test-project"
        })

        # End session
        end_result = mem_session_end_tool.invoke({
            "summary": "Fixed auth bug",
            "save_summary": True
        })
        assert end_result["status"] == "ended"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
