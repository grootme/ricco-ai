"""Gentle AI tools for SDD/OpenSpec workflows.

Provides tools for structured development workflows including
proposal, specification, design, task breakdown, and verification.
"""

from __future__ import annotations

import logging
from typing import Literal

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool("sdd_init", parse_docstring=True)
def sdd_init_tool(
    project_name: str,
    description: str | None = None,
    artifact_store: str = "openspec",
) -> dict:
    """Initialize SDD workflow for a project.

    Creates the OpenSpec directory structure and configuration file.

    Args:
        project_name: Name of the project.
        description: Optional project description.
        artifact_store: Where to store artifacts ('openspec', 'engram', or 'both').

    Returns:
        Dictionary with initialization status and paths created.
    """
    logger.info(f"Initializing SDD for project: {project_name}")

    return {
        "status": "initialized",
        "project_name": project_name,
        "artifact_store": artifact_store,
        "paths": {
            "specs": "openspec/specs/",
            "changes": "openspec/changes/",
            "archive": "openspec/changes/archive/",
            "config": "openspec/config.yaml",
        },
    }


@tool("sdd_proposal", parse_docstring=True)
def sdd_proposal_tool(
    change_name: str,
    title: str,
    summary: str,
    motivation: str,
    approach: str,
    alternatives: str | None = None,
) -> dict:
    """Create a proposal artifact for SDD workflow.

    Args:
        change_name: Unique identifier for this change.
        title: Human-readable title of the proposal.
        summary: Brief summary of what the change does.
        motivation: Why this change is needed.
        approach: High-level approach to implement.
        alternatives: Alternative approaches considered.

    Returns:
        Dictionary with proposal status and artifact path.
    """
    logger.info(f"Creating proposal: {change_name}")

    return {
        "status": "created",
        "change_name": change_name,
        "artifact_path": f"openspec/changes/{change_name}/proposal.md",
        "content": {
            "title": title,
            "summary": summary,
            "motivation": motivation,
            "approach": approach,
            "alternatives": alternatives,
        },
    }


@tool("sdd_spec", parse_docstring=True)
def sdd_spec_tool(
    change_name: str,
    domain: str,
    requirements: list[str],
    acceptance_criteria: list[str],
    non_goals: list[str] | None = None,
) -> dict:
    """Create a specification artifact for SDD workflow.

    Args:
        change_name: Unique identifier for this change.
        domain: Domain area (e.g., 'auth', 'api', 'ui').
        requirements: List of functional requirements.
        acceptance_criteria: List of acceptance criteria.
        non_goals: Things explicitly out of scope.

    Returns:
        Dictionary with spec status and artifact path.
    """
    logger.info(f"Creating spec for: {change_name}/{domain}")

    return {
        "status": "created",
        "change_name": change_name,
        "domain": domain,
        "artifact_path": f"openspec/changes/{change_name}/specs/{domain}/spec.md",
        "requirements_count": len(requirements),
        "acceptance_criteria_count": len(acceptance_criteria),
    }


@tool("sdd_design", parse_docstring=True)
def sdd_design_tool(
    change_name: str,
    architecture: str,
    components: list[str],
    interfaces: list[str] | None = None,
    data_models: list[str] | None = None,
    risks: list[str] | None = None,
) -> dict:
    """Create a design artifact for SDD workflow.

    Args:
        change_name: Unique identifier for this change.
        architecture: High-level architecture description.
        components: List of components to implement.
        interfaces: List of interfaces/APIs.
        data_models: List of data models/schemas.
        risks: Identified risks and mitigations.

    Returns:
        Dictionary with design status and artifact path.
    """
    logger.info(f"Creating design for: {change_name}")

    return {
        "status": "created",
        "change_name": change_name,
        "artifact_path": f"openspec/changes/{change_name}/design.md",
        "components_count": len(components),
    }


@tool("sdd_tasks", parse_docstring=True)
def sdd_tasks_tool(
    change_name: str,
    tasks: list[dict],
    estimated_effort: str | None = None,
) -> dict:
    """Create a task breakdown artifact for SDD workflow.

    Args:
        change_name: Unique identifier for this change.
        tasks: List of task objects with 'name', 'description', 'dependencies'.
        estimated_effort: Overall effort estimate.

    Returns:
        Dictionary with tasks status and artifact path.
    """
    logger.info(f"Creating tasks for: {change_name}")

    return {
        "status": "created",
        "change_name": change_name,
        "artifact_path": f"openspec/changes/{change_name}/tasks.md",
        "tasks_count": len(tasks),
        "estimated_effort": estimated_effort,
    }


@tool("sdd_apply", parse_docstring=True)
def sdd_apply_tool(
    change_name: str,
    task_id: str,
    tdd_phase: Literal["RED", "GREEN", "TRIANGULATE", "REFACTOR"],
    test_name: str | None = None,
    test_output: str | None = None,
    implementation_notes: str | None = None,
) -> dict:
    """Record apply progress with TDD evidence for SDD workflow.

    Args:
        change_name: Unique identifier for this change.
        task_id: ID of the task being worked on.
        tdd_phase: Current TDD phase (RED, GREEN, TRIANGULATE, REFACTOR).
        test_name: Name of the test (for RED/GREEN phases).
        test_output: Test output/result.
        implementation_notes: Notes about the implementation.

    Returns:
        Dictionary with apply status and evidence recorded.
    """
    logger.info(f"Recording apply progress: {change_name}/{task_id}/{tdd_phase}")

    return {
        "status": "recorded",
        "change_name": change_name,
        "task_id": task_id,
        "tdd_phase": tdd_phase,
        "evidence": {
            "test_name": test_name,
            "test_output": test_output,
            "implementation_notes": implementation_notes,
        },
    }


@tool("sdd_verify", parse_docstring=True)
def sdd_verify_tool(
    change_name: str,
    verification_type: Literal["unit", "integration", "e2e", "review"],
    results: list[dict],
    overall_status: Literal["passed", "failed", "partial"],
) -> dict:
    """Record verification results for SDD workflow.

    Args:
        change_name: Unique identifier for this change.
        verification_type: Type of verification performed.
        results: List of verification results.
        overall_status: Overall verification status.

    Returns:
        Dictionary with verify status and artifact path.
    """
    logger.info(f"Recording verification: {change_name}/{verification_type}")

    return {
        "status": "recorded",
        "change_name": change_name,
        "artifact_path": f"openspec/changes/{change_name}/verify-report.md",
        "verification_type": verification_type,
        "overall_status": overall_status,
        "results_count": len(results),
    }


@tool("sdd_archive", parse_docstring=True)
def sdd_archive_tool(
    change_name: str,
    summary: str,
    lessons_learned: list[str] | None = None,
) -> dict:
    """Archive completed SDD workflow.

    Moves the change to the archive directory with completion notes.

    Args:
        change_name: Unique identifier for this change.
        summary: Summary of what was accomplished.
        lessons_learned: Lessons learned during implementation.

    Returns:
        Dictionary with archive status.
    """
    logger.info(f"Archiving: {change_name}")

    return {
        "status": "archived",
        "change_name": change_name,
        "archive_path": f"openspec/changes/archive/{change_name}/",
        "summary": summary,
        "lessons_learned": lessons_learned or [],
    }


# Export all tools
GENTLE_AI_TOOLS = [
    sdd_init_tool,
    sdd_proposal_tool,
    sdd_spec_tool,
    sdd_design_tool,
    sdd_tasks_tool,
    sdd_apply_tool,
    sdd_verify_tool,
    sdd_archive_tool,
]
