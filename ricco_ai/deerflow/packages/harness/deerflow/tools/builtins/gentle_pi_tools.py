"""Gentle-Pi tools for persona and orchestration.

Provides tools for managing the Gentleman persona, model assignments,
and development harness configuration in Pi.
"""

from __future__ import annotations

import logging
from typing import Literal

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

PersonaMode = Literal["gentleman", "neutral"]
ExecutionMode = Literal["interactive", "auto"]
PrStrategy = Literal["auto-forecast", "ask-always", "single-pr-default", "force-chained"]
ThinkingEffort = Literal["off", "low", "medium", "high", "inherit"]


@tool("gentle_persona", parse_docstring=True)
def gentle_persona_tool(
    persona: PersonaMode = "gentleman",
) -> dict:
    """Switch between Gentleman and neutral persona modes.

    The persona affects how the agent communicates and approaches problems.

    Args:
        persona: Persona mode - 'gentleman' for senior architect/teacher style,
                 'neutral' for professional but less opinionated style.

    Returns:
        Dictionary with persona confirmation and description.
    """
    logger.info(f"Switching persona to: {persona}")

    descriptions = {
        "gentleman": "Senior architect and teacher. Uses Rioplatense Spanish/voseo when responding in Spanish. Direct technical feedback.",
        "neutral": "Professional, warmer language. Same discipline but less regional expression.",
    }

    return {
        "status": "switched",
        "persona": persona,
        "description": descriptions.get(persona, ""),
    }


@tool("gentle_models", parse_docstring=True)
def gentle_models_tool(
    agent_name: str,
    model: str | None = None,
    thinking: ThinkingEffort = "medium",
) -> dict:
    """Configure model assignment for a specific agent type.

    Allows assigning different models and thinking effort levels
    to different agent types in the SDD workflow.

    Args:
        agent_name: Name of the agent (e.g., 'sdd-explore', 'sdd-apply', 'sdd-verify').
        model: Model identifier (e.g., 'anthropic/claude-sonnet-4', 'openai/gpt-4').
        thinking: Thinking effort level - 'off', 'low', 'medium', 'high', or 'inherit'.

    Returns:
        Dictionary with model assignment confirmation.
    """
    logger.info(f"Setting model for {agent_name}: {model} (thinking: {thinking})")

    return {
        "status": "configured",
        "agent_name": agent_name,
        "model": model,
        "thinking": thinking,
    }


@tool("sdd_preflight", parse_docstring=True)
def sdd_preflight_tool(
    execution_mode: ExecutionMode = "interactive",
    artifact_store: Literal["openspec", "engram", "both"] = "openspec",
    pr_strategy: PrStrategy = "auto-forecast",
    review_budget_lines: int | None = None,
) -> dict:
    """Run SDD preflight configuration.

    Sets up the SDD workflow preferences for the current session.
    Run this before starting any SDD workflow.

    Args:
        execution_mode: 'interactive' for manual approval, 'auto' for automatic execution.
        artifact_store: Where to store artifacts - 'openspec', 'engram', or 'both'.
        pr_strategy: PR chaining strategy - 'auto-forecast', 'ask-always', 'single-pr-default', 'force-chained'.
        review_budget_lines: Maximum lines before warning about review workload.

    Returns:
        Dictionary with preflight status and configuration.
    """
    logger.info("Running SDD preflight")

    return {
        "status": "configured",
        "execution_mode": execution_mode,
        "artifact_store": artifact_store,
        "pr_strategy": pr_strategy,
        "review_budget_lines": review_budget_lines,
        "ready": True,
    }


@tool("skill_registry_refresh", parse_docstring=True)
def skill_registry_refresh_tool(
    scan_user_skills: bool = True,
    scan_project_skills: bool = True,
) -> dict:
    """Refresh the skill registry.

    Scans project and user skill directories to update the registry
    of available skills.

    Args:
        scan_user_skills: Whether to scan user-level skills.
        scan_project_skills: Whether to scan project-level skills.

    Returns:
        Dictionary with registry refresh status and skill count.
    """
    logger.info("Refreshing skill registry")

    skill_roots = []
    if scan_project_skills:
        skill_roots.extend([
            "./skills",
            ".opencode/skills",
            ".claude/skills",
            ".cursor/skills",
        ])
    if scan_user_skills:
        skill_roots.extend([
            "~/.pi/agent/skills",
            "~/.config/agents/skills",
            "~/.claude/skills",
        ])

    return {
        "status": "refreshed",
        "registry_path": ".atl/skill-registry.md",
        "skill_roots_scanned": skill_roots,
        "skills_found": 0,  # Would be populated by actual scan
    }


@tool("delegate_task", parse_docstring=True)
def delegate_task_tool(
    task_description: str,
    agent_type: Literal["scout", "worker", "reviewer", "context-builder"],
    context_files: list[str] | None = None,
    fresh_context: bool = True,
) -> dict:
    """Delegate a task to a subagent.

    Creates a focused subagent to handle specific work while
    the parent session maintains orchestration responsibility.

    Args:
        task_description: Clear description of the task to delegate.
        agent_type: Type of subagent - 'scout' (exploration), 'worker' (implementation),
                    'reviewer' (adversarial review), 'context-builder' (context compression).
        context_files: Specific files to include in subagent context.
        fresh_context: Whether to start with fresh context (recommended for reviewers).

    Returns:
        Dictionary with delegation status.
    """
    logger.info(f"Delegating to {agent_type}: {task_description[:50]}...")

    return {
        "status": "delegated",
        "agent_type": agent_type,
        "task_description": task_description,
        "context_files": context_files or [],
        "fresh_context": fresh_context,
    }


@tool("check_delegation_triggers", parse_docstring=True)
def check_delegation_triggers_tool(
    files_read: int = 0,
    files_to_write: int = 0,
    tool_calls: int = 0,
    exploratory_reads: int = 0,
    non_mechanical_edits: int = 0,
) -> dict:
    """Check if any delegation triggers are activated.

    Evaluates the current session state against delegation rules
    to determine if work should be delegated.

    Args:
        files_read: Number of files read to understand the task.
        files_to_write: Number of non-trivial files being modified.
        tool_calls: Total number of tool calls in the session.
        exploratory_reads: Number of exploratory file reads.
        non_mechanical_edits: Number of non-mechanical code edits.

    Returns:
        Dictionary with triggered rules and recommendations.
    """
    logger.info("Checking delegation triggers")

    triggers = []
    recommendations = []

    if files_read >= 4:
        triggers.append("four_file_rule")
        recommendations.append("Consider delegating exploration to scout or context-builder")

    if files_to_write >= 2:
        triggers.append("multi_file_write")
        recommendations.append("Use a single worker or require fresh review before completion")

    if tool_calls >= 20:
        triggers.append("long_session")
        recommendations.append("Consider pausing to delegate or justify not doing so")

    if exploratory_reads >= 5:
        triggers.append("exploration_heavy")
        recommendations.append("Consider delegating context-heavy exploration")

    if non_mechanical_edits >= 2:
        triggers.append("complex_edits")
        recommendations.append("Fresh review recommended before completion")

    return {
        "status": "checked",
        "triggers_activated": triggers,
        "recommendations": recommendations,
        "metrics": {
            "files_read": files_read,
            "files_to_write": files_to_write,
            "tool_calls": tool_calls,
            "exploratory_reads": exploratory_reads,
            "non_mechanical_edits": non_mechanical_edits,
        },
    }


@tool("forecast_review_workload", parse_docstring=True)
def forecast_review_workload_tool(
    estimated_lines_added: int,
    estimated_lines_deleted: int,
    files_changed: int,
    areas_touched: list[str] | None = None,
) -> dict:
    """Forecast review workload before making changes.

    Helps prevent oversized or multi-area diffs that are hard to review.

    Args:
        estimated_lines_added: Estimated lines to add.
        estimated_lines_deleted: Estimated lines to delete.
        files_changed: Number of files to change.
        areas_touched: List of code areas being touched.

    Returns:
        Dictionary with workload assessment and recommendations.
    """
    logger.info("Forecasting review workload")

    total_lines = estimated_lines_added + estimated_lines_deleted
    risk_level = "low"
    recommendations = []

    if total_lines > 500:
        risk_level = "high"
        recommendations.append("Consider splitting into multiple PRs")
    elif total_lines > 200:
        risk_level = "medium"
        recommendations.append("Ensure clear commit messages and good description")

    if files_changed > 10:
        if risk_level != "high":
            risk_level = "medium"
        recommendations.append("Many files changed - consider if change scope is appropriate")

    if areas_touched and len(areas_touched) > 3:
        recommendations.append("Multi-area change - consider separate PRs for each area")

    return {
        "status": "forecasted",
        "total_lines": total_lines,
        "files_changed": files_changed,
        "areas_touched": areas_touched or [],
        "risk_level": risk_level,
        "recommendations": recommendations,
    }


# Export all tools
GENTLE_PI_TOOLS = [
    gentle_persona_tool,
    gentle_models_tool,
    sdd_preflight_tool,
    skill_registry_refresh_tool,
    delegate_task_tool,
    check_delegation_triggers_tool,
    forecast_review_workload_tool,
]
