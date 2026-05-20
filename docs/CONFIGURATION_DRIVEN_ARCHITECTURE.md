# Configuration-Driven Agent Architecture

## Overview

This system implements a **truly configuration-driven agent architecture** that fully complies with SOLID principles, especially OCP (Open/Closed Principle).

**Key Principle: To add a new agent, you ONLY modify configuration files. NO CODE CHANGES.**

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     CONFIGURATION (JSON)                        │
├─────────────────────────────────────────────────────────────────┤
│  domains.json    │  14 domains (swe, salud, finanzas, etc.)    │
│  roles.json      │  5 roles (investigator, observer, etc.)     │
│  platform.json   │  Platform branding and defaults             │
│  agents.json     │  66 agents (auto-generated)                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     REGISTRY (Dynamic Discovery)                │
├─────────────────────────────────────────────────────────────────┤
│  AgentRegistry   │  Discovers agents from configuration        │
│  AgentFactory    │  Creates agents dynamically                 │
│  DynamicAgent    │  Thin wrapper around configuration          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        APPLICATION                              │
├─────────────────────────────────────────────────────────────────┤
│  get_agent(id)   │  Get agent by ID                            │
│  get_agents_for_domain(domain)  │  Get all agents for domain   │
│  get_coordinator()  │  Get the NEXUS coordinator               │
└─────────────────────────────────────────────────────────────────┘
```

## How to Add a New Agent

### Option 1: Add a New Domain
Edit `src/config/domains.json`:
```json
{
  "new_domain": {
    "id": "new_domain",
    "name": "New Domain",
    "elegant_name": "NEWDOM",
    "keywords": ["keyword1", "keyword2"],
    "mcp_servers": ["server1"]
  }
}
```
Then run: `python scripts/generate_agents.py`
This creates 5 new agents automatically!

### Option 2: Add a New Role
Edit `src/config/roles.json`:
```json
{
  "new_role": {
    "id": "new_role",
    "name": "new_role",
    "elegant_name": "NEW_ROLE",
    "skills": ["skill1", "skill2"],
    "tools": ["tool1"]
  }
}
```
Then run: `python scripts/generate_agents.py`
This creates 13 new agents (one per domain)!

### Option 3: Add a Custom Agent
Edit `src/config/agents.json` directly:
```json
{
  "my_custom_agent": {
    "id": "my_custom_agent",
    "name": "My Custom Agent",
    "domain": "custom",
    "role": "custom",
    "capabilities": {...},
    "behavior": {...},
    "prompts": {...}
  }
}
```

## Anti-Patterns Eliminated

### ❌ BEFORE (Hardcoded)
```python
# Directory structure hardcoded
src/
  iovba/
    action/
    behavior/
    validation/

# Agent types hardcoded
class InvestigatorAgent:
    ...

class ObserverAgent:
    ...

# If-else chains
if domain == "swe":
    agent = InvestigatorAgent()
elif domain == "salud":
    agent = MedicalInvestigator()
```

### ✅ AFTER (Configuration-Driven)
```python
# No hardcoded directories for agents
# No hardcoded agent classes
# No if-else chains

# Everything comes from configuration
agent = get_agent("investigator_swe")  # Any agent, dynamically created
```

## SOLID Compliance

| Principle | Implementation |
|-----------|---------------|
| **SRP** | Each component has single responsibility |
| **OCP** | Open for extension via config, closed for modification |
| **LSP** | All agents implement same DynamicAgent interface |
| **ISP** | Protocols define minimal interfaces |
| **DIP** | Dependencies injected via configuration |

## File Structure

```
src/
├── config/
│   ├── domains.json      # Domain definitions
│   ├── roles.json        # Role definitions
│   ├── platform.json     # Platform config
│   └── agents.json       # Agent definitions (generated)
│
├── registry/
│   └── __init__.py       # AgentRegistry, AgentFactory, DynamicAgent
│
└── scripts/
    └── generate_agents.py  # Auto-generate agents from config
```

## Usage Examples

```python
from src.registry import get_agent, get_agents_for_domain, get_coordinator

# Get specific agent
agent = get_agent("investigator_swe")
print(agent.name)  # "CODEX INVESTIGATOR"

# Get all agents for a domain
agents = get_agents_for_domain("finanzas")
# Returns: [investigator_finanzas, observer_finanzas, ...]

# Get coordinator
nexus = get_coordinator()
print(nexus.name)  # "NEXUS"

# Execute with agent
result = await agent.execute(
    query="Analyze this code",
    llm_provider=my_llm_provider
)
```

## Statistics

- **66 agents** generated automatically
- **13 domain teams**
- **5 role types**
- **0 hardcoded agent classes**
- **0 if-else chains for agent selection**
- **0 hardcoded directory structure for agents**

## Comparison with Previous Architecture

| Aspect | Before | After |
|--------|--------|-------|
| Add new domain | Create new files | Edit domains.json |
| Add new role | Create new classes | Edit roles.json |
| Add new agent | Write code | Edit agents.json |
| Agent discovery | Hardcoded imports | Dynamic from config |
| File structure | Hardcoded directories | Configuration-based |
| OCP Compliance | ❌ Violates | ✅ Complies |
