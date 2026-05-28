---
name: gentle-pi
description: "Turn Pi into a controlled development harness: el Gentleman persona, SDD/OpenSpec workflows, subagent orchestration, strict TDD, and review protection."
version: "1.0.0"
author: "Gentleman Programming"
tags: [pi, sdd, workflow, orchestration, testing]
---

# Gentle-Pi - Pi Development Harness

Turn Pi from a powerful coding agent into a controlled development harness with senior-architect discipline.

## What It Adds

| Capability | Description |
|------------|-------------|
| **el Gentleman persona** | Senior architect and teacher behavior |
| **Work routing discipline** | Small tasks inline, large changes through SDD |
| **SDD/OpenSpec assets** | Phase agents for init, explore, proposal, spec, design, tasks, apply, verify, archive |
| **Subagent orchestration** | Parent session responsible, child agents focused |
| **Strict TDD support** | RED → GREEN → TRIANGULATE → REFACTOR evidence |
| **Reviewer protection** | Surfaces review workload risk before oversized PRs |

## Work Routing

```text
small + known context      → inline direct
unknown / context-heavy    → simple delegation
large / ambiguous / risky  → SDD/OpenSpec flow
```

## SDD/OpenSpec Flow

```text
init
  ↓
explore → proposal → spec ─┬→ design ─┐
                            └─────────┴→ tasks → apply → verify → sync → archive
```

## Delegation Triggers

| Trigger | Expected behavior |
|---------|-------------------|
| Reading 4+ files to understand a flow | Launch scout or context-builder |
| Touching 2+ non-trivial code files | Use one worker or require fresh review |
| Commit, push, or PR after code changes | Run fresh reviewer (unless trivial) |
| Wrong cwd, worktree accident, merge recovery | Run fresh audit reviewer |
| Long monolithic session | Pause and delegate |

## Tools

- `sdd_init`: Initialize SDD workflow for a project
- `sdd_preflight`: Run preflight checks before SDD
- `gentle_models`: Configure model assignments for agents
- `gentle_persona`: Switch persona mode
- `skill_registry_refresh`: Refresh the skill registry
- `delegate_task`: Delegate work to subagents
- `check_delegation_triggers`: Evaluate delegation rules
- `forecast_review_workload`: Predict review effort

## Model Assignment

| Agent kind | Recommended model | Recommended effort |
|------------|-------------------|-------------------|
| Explore, proposal, archive | Fast and cheap | `off` to `low` |
| Spec, design, tasks | Strong reasoning | `medium` to `high` |
| Apply | Strong coding/tool-use | `medium` to `high` |
| Verify/review | Strong fresh-context | `high` |

## Principles

- Human control over agent momentum
- Concepts before code
- Artifacts over floating chat context
- SDD when risk justifies it
- Strict TDD when tests exist
- One parent orchestrator, focused subagents
- Reviewable changes over giant diffs
