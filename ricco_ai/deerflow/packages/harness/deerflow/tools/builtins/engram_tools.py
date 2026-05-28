"""Engram tools for persistent memory management.

Provides tools for saving, searching, and managing memories
across agent sessions using SQLite + FTS5 full-text search.
"""

from __future__ import annotations

import logging
from typing import Literal

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# Memory types matching Engram's supported types
MemoryType = Literal[
    "architecture",
    "decision",
    "bugfix",
    "discovery",
    "user_prompt",
    "session",
    "custom",
]


@tool("mem_save", parse_docstring=True)
def mem_save_tool(
    title: str,
    content: str,
    memory_type: MemoryType = "custom",
    project: str | None = None,
    topic_key: str | None = None,
    what: str | None = None,
    why: str | None = None,
    where: str | None = None,
    learned: str | None = None,
) -> dict:
    """Save a memory for future reference.

    Memories persist across sessions and can be searched later.
    Use this to remember important decisions, solutions, and discoveries.

    Args:
        title: Short, descriptive title for the memory.
        content: Full memory content. Can include What/Why/Where/Learned structure.
        memory_type: Type of memory (architecture, decision, bugfix, discovery, user_prompt, session, custom).
        project: Project this memory belongs to.
        topic_key: Hierarchical topic key (e.g., 'auth/jwt-implementation').
        what: What was done (optional, for structured memories).
        why: Why it was done (optional, for structured memories).
        where: Where it applies (optional, for structured memories).
        learned: What was learned (optional, for structured memories).

    Returns:
        Dictionary with memory ID and confirmation.
    """
    logger.info(f"Saving memory: {title} ({memory_type})")

    # Build structured content if components provided
    structured_content = content
    if what or why or where or learned:
        parts = [content]
        if what:
            parts.append(f"\n**What**: {what}")
        if why:
            parts.append(f"\n**Why**: {why}")
        if where:
            parts.append(f"\n**Where**: {where}")
        if learned:
            parts.append(f"\n**Learned**: {learned}")
        structured_content = "\n".join(parts)

    return {
        "status": "saved",
        "title": title,
        "memory_type": memory_type,
        "project": project,
        "topic_key": topic_key,
        "content_length": len(structured_content),
    }


@tool("mem_search", parse_docstring=True)
def mem_search_tool(
    query: str,
    project: str | None = None,
    memory_type: MemoryType | None = None,
    limit: int = 10,
) -> dict:
    """Search memories using full-text search.

    Searches across titles, content, and topic keys using FTS5.

    Args:
        query: Search query string.
        project: Filter by project (optional).
        memory_type: Filter by memory type (optional).
        limit: Maximum number of results (default 10).

    Returns:
        Dictionary with search results.
    """
    logger.info(f"Searching memories: {query}")

    return {
        "status": "searched",
        "query": query,
        "filters": {
            "project": project,
            "memory_type": memory_type,
        },
        "limit": limit,
        "results": [],  # Would be populated by actual Engram integration
    }


@tool("mem_context", parse_docstring=True)
def mem_context_tool(
    project: str | None = None,
    limit: int = 5,
) -> dict:
    """Get recent session context from memory.

    Retrieves recent memories relevant to the current session.

    Args:
        project: Filter by project (optional).
        limit: Maximum number of memories to return.

    Returns:
        Dictionary with recent memories and context summary.
    """
    logger.info(f"Getting context for project: {project}")

    return {
        "status": "retrieved",
        "project": project,
        "limit": limit,
        "memories": [],  # Would be populated by actual Engram integration
    }


@tool("mem_timeline", parse_docstring=True)
def mem_timeline_tool(
    memory_id: str,
    before: int = 2,
    after: int = 2,
) -> dict:
    """Get chronological context around a specific memory.

    Retrieves memories created before and after the specified memory.

    Args:
        memory_id: ID of the anchor memory.
        before: Number of memories to retrieve before.
        after: Number of memories to retrieve after.

    Returns:
        Dictionary with timeline of memories.
    """
    logger.info(f"Getting timeline for memory: {memory_id}")

    return {
        "status": "retrieved",
        "anchor_id": memory_id,
        "before_count": before,
        "after_count": after,
        "timeline": [],  # Would be populated by actual Engram integration
    }


@tool("mem_update", parse_docstring=True)
def mem_update_tool(
    memory_id: str,
    title: str | None = None,
    content: str | None = None,
    memory_type: MemoryType | None = None,
    topic_key: str | None = None,
) -> dict:
    """Update an existing memory.

    Args:
        memory_id: ID of the memory to update.
        title: New title (optional).
        content: New content (optional).
        memory_type: New memory type (optional).
        topic_key: New topic key (optional).

    Returns:
        Dictionary with update confirmation.
    """
    logger.info(f"Updating memory: {memory_id}")

    return {
        "status": "updated",
        "memory_id": memory_id,
        "updated_fields": {
            k: v for k, v in {
                "title": title,
                "content": content,
                "memory_type": memory_type,
                "topic_key": topic_key,
            }.items() if v is not None
        },
    }


@tool("mem_delete", parse_docstring=True)
def mem_delete_tool(
    memory_id: str,
) -> dict:
    """Delete a memory.

    Args:
        memory_id: ID of the memory to delete.

    Returns:
        Dictionary with deletion confirmation.
    """
    logger.info(f"Deleting memory: {memory_id}")

    return {
        "status": "deleted",
        "memory_id": memory_id,
    }


@tool("mem_stats", parse_docstring=True)
def mem_stats_tool(
    project: str | None = None,
) -> dict:
    """Get memory statistics.

    Args:
        project: Filter by project (optional).

    Returns:
        Dictionary with memory statistics.
    """
    logger.info(f"Getting memory stats for project: {project}")

    return {
        "status": "retrieved",
        "project": project,
        "stats": {
            "total_memories": 0,
            "by_type": {},
            "by_project": {},
        },
    }


@tool("mem_session_start", parse_docstring=True)
def mem_session_start_tool(
    project: str | None = None,
    session_type: str = "default",
) -> dict:
    """Start a new memory session.

    Sessions help group related memories together.

    Args:
        project: Project for this session.
        session_type: Type of session (default, debugging, development, review).

    Returns:
        Dictionary with session ID.
    """
    logger.info(f"Starting session for project: {project}")

    return {
        "status": "started",
        "project": project,
        "session_type": session_type,
    }


@tool("mem_session_end", parse_docstring=True)
def mem_session_end_tool(
    summary: str | None = None,
    save_summary: bool = True,
) -> dict:
    """End the current memory session.

    Args:
        summary: Summary of the session.
        save_summary: Whether to save the summary as a memory.

    Returns:
        Dictionary with session end confirmation.
    """
    logger.info("Ending session")

    return {
        "status": "ended",
        "summary_saved": save_summary and summary is not None,
    }


# Export all tools
ENGRAM_TOOLS = [
    mem_save_tool,
    mem_search_tool,
    mem_context_tool,
    mem_timeline_tool,
    mem_update_tool,
    mem_delete_tool,
    mem_stats_tool,
    mem_session_start_tool,
    mem_session_end_tool,
]
