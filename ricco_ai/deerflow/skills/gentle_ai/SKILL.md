---
name: gentle-ai
description: "Gentle AI harness discipline: clarify first, preserve artifacts, use strict TDD, delegate through subagents, and protect review workload."
version: "1.0.0"
author: "Gentleman Programming"
tags: [workflow, sdd, testing, orchestration]
---

# Gentle AI - Agent Harness Discipline

Use this skill when work is non-trivial, risky, multi-step, or benefits from structured development workflows.

## Core Principles

1. **Clarity First**: Understand scope, constraints, acceptance criteria, and non-goals before implementation.
2. **Artifact Preservation**: Maintain OpenSpec-style artifacts (proposal, specs, design, tasks, apply progress, verify report, archive notes).
3. **Strict TDD**: When tests exist, follow RED → GREEN → TRIANGULATE → REFACTOR with evidence.
4. **Controlled Delegation**: Parent session orchestrates; child subagents receive concrete phase work.
5. **Review Protection**: Forecast review workload before large changes.

## Work Routing Decision Tree

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

| Trigger | Action |
|---------|--------|
| 4+ files for understanding | Launch scout/context-builder |
| 2+ non-trivial files to write | Use one worker or require fresh review |
| Commit/PR after code changes | Run fresh reviewer (unless trivial docs/text) |
| Tooling/worktree incidents | Run fresh audit reviewer |
| Long session with complexity | Pause and delegate or justify |

## Tools

- `sdd_init`: Initialize SDD workflow
- `sdd_proposal`: Create proposal artifact
- `sdd_spec`: Create specification
- `sdd_design`: Create design document
- `sdd_tasks`: Generate task breakdown
- `sdd_apply`: Apply changes with TDD evidence
- `sdd_verify`: Verify implementation
- `sdd_archive`: Archive completed work
