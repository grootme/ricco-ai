---
name: engram
description: "Persistent memory for AI agents: save, search, and retrieve memories across sessions with SQLite + FTS5 full-text search."
version: "1.0.0"
author: "Gentleman Programming"
tags: [memory, persistence, sqlite, mcp]
---

# Engram - Persistent Agent Memory

Give your AI coding agent a brain. Engram provides persistent memory with SQLite + FTS5 full-text search.

## Memory Types

| Type | Description |
|------|-------------|
| `architecture` | Architecture decisions and patterns |
| `decision` | Important decisions made |
| `bugfix` | Bug fixes and solutions |
| `discovery` | Discoveries and insights |
| `user_prompt` | Saved user prompts |
| `session` | Session summaries |

## Tools

| Tool | Description |
|------|-------------|
| `mem_save` | Save a memory with title, type, What/Why/Where/Learned |
| `mem_search` | Full-text search across memories |
| `mem_context` | Get recent session context |
| `mem_timeline` | Chronological context around a memory |
| `mem_update` | Update an existing memory |
| `mem_delete` | Delete a memory |
| `mem_stats` | Get memory statistics |

## Usage

### Save a memory
```
mem_save(
    title="Use Clean Architecture",
    content="Layers: entities, use cases, adapters. Domain layer has no dependencies.",
    type="architecture",
    project="my-project"
)
```

### Search memories
```
mem_search(query="architecture", limit=5)
```

### Get context
```
mem_context(project="my-project")
```

## Best Practices

1. **Save significant work**: Bug fixes, architecture decisions, discoveries
2. **Use topic keys**: Organize memories hierarchically
3. **Search before asking**: Check if similar problems were solved before
4. **Session summaries**: Save session summaries for future context
