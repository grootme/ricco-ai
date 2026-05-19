# Refactoring Gaps and Implementation Plan

## Summary

This document identifies the gaps and necessary changes to eliminate "IOVBA" from the codebase and implement a fully configuration-driven agent system.

---

## Completed Changes

### 1. Configuration System (COMPLETED)
- Created `src/config/agent_config/domains.json` - All domains are now configurable
- Created `src/config/agent_config/roles.json` - All roles are now configurable
- Created `src/config/agent_config/platform.json` - Platform branding is configurable
- Created `src/config/agent_config/__init__.py` - ConfigLoader with dynamic loading

### 2. New Agent System (COMPLETED)
- Created `src/agent_system/__init__.py` - Main module with AgentGroup, AgentProfile, CognitiveCapital
- Created `src/agent_system/nexus.py` - NEXUS Super Agent refactored (no hardcoded values)
- Created `src/agent_system/action/__init__.py` - ActionExecutor, SkillsRegistry, MCPRegistry
- Created `src/agent_system/behavior/__init__.py` - PersonaManager, EthicsEngine
- Created `src/agent_system/validation/__init__.py` - GuardrailEngine, PolicyEngine
- Created `src/agent_system/orchestration/__init__.py` - LeadAgentOrchestrator, SubAgentCoordinator
- Created `src/agent_system/infrastructure/__init__.py` - SandboxEnvironment, OpenShellConnector

### 3. Frontend Types (COMPLETED)
- Updated `frontend/src/types/index.ts` - Removed all IOVBA references
- Added new types: DomainConfig, RoleConfig, PlatformConfig, NEXUSConfig

### 4. Frontend Stores (COMPLETED)
- Updated `frontend/src/stores/index.ts` - Renamed IOVBAGroupsStore to AgentGroupsStore
- Added new stores: PlatformStore

---

## Pending Changes

### 1. Remove Old IOVBA Directory
**Priority: HIGH**

The old `src/iovba/` directory needs to be removed after all imports are updated.

Files to remove:
```
src/iovba/__init__.py
src/iovba/groups.py
src/iovba/nexus_super_agent.py
src/iovba/lead_assistant.py
src/iovba/langgraph_integration.py
src/iovba/testing.py
src/iovba/action/*
src/iovba/behavior/*
src/iovba/validation/*
src/iovba/orchestration/*
src/iovba/infrastructure/*
```

### 2. Update All Imports
**Priority: HIGH**

All files that import from `src.iovba` need to be updated:

```python
# OLD
from src.iovba import IOVBAGroup, IOVBAGroupManager, NEXUSSuperAgent

# NEW
from src.agent_system import AgentGroup, AgentGroupManager
from src.agent_system.nexus import NEXUSSuperAgent
```

Files requiring import updates:
- `src/api/nexus_routes.py`
- `src/api/agent_routes.py`
- `src/core/agent_profile.py`
- `src/queue/*` (multiple files)
- `src/services/agent_service.py`
- `scripts/*` (multiple files)
- `tests/*` (multiple test files)

### 3. Update API Routes
**Priority: HIGH**

API routes need to use the new agent system:

- `src/api/nexus_routes.py` - Update to use `agent_system.nexus`
- `src/api/agent_routes.py` - Update endpoints to serve domain/role configs

### 4. Database Schema Updates
**Priority: MEDIUM**

The Prisma schema may need updates to remove any IOVBA-specific tables:

- Review `frontend/prisma/schema.prisma`
- Ensure no tables have hardcoded "iovba" names
- Use generic names like "agent_groups", "agent_profiles"

### 5. Frontend Components
**Priority: MEDIUM**

Components that reference IOVBA need updates:

- `frontend/src/app/page.tsx`
- `frontend/src/app/chat/page.tsx`
- `frontend/src/app/domains/page.tsx`
- `frontend/src/app/agents/page.tsx`
- `frontend/src/components/agent-management/agent-dashboard.tsx`

### 6. Test Files
**Priority: MEDIUM**

Test files need updates:

- `tests/test_iovba_*.py` - Rename and update
- Update all test imports

---

## Gaps Identified

### Gap 1: LangGraph Integration
**Status: NEEDS UPDATE**

The LangGraph integration in `src/iovba/langgraph_integration.py` needs to be refactored:
- Move to `src/agent_system/langgraph_integration.py`
- Update to use configuration instead of hardcoded values

### Gap 2: Lead Assistant
**Status: NEEDS UPDATE**

The Lead Assistant in `src/iovba/lead_assistant.py` needs:
- Refactor to `src/agent_system/lead_assistant.py`
- Update HITL (Human In The Loop) to be configuration-driven

### Gap 3: Testing Module
**Status: NEEDS UPDATE**

The testing module in `src/iovba/testing.py` needs:
- Refactor to `src/agent_system/testing.py`
- Update to use new configuration system

### Gap 4: API Client Frontend
**Status: NEEDS UPDATE**

The frontend API client needs new methods:
- `getDomains()` - Fetch domain configurations
- `getRoles()` - Fetch role configurations
- `getPlatformConfig()` - Fetch platform configuration
- `getNEXUSConfig()` - Fetch NEXUS status

### Gap 5: Migration Scripts
**Status: NEEDS CREATION**

Migration scripts needed:
- Script to convert existing IOVBA groups to AgentGroups
- Script to backfill configuration from database

---

## Anti-Patterns Eliminated

### 1. Hardcoded Domain Detection
**BEFORE:**
```python
DOMAIN_KEYWORDS: Dict[IOVBADomain, List[str]] = {
    "swe": ["código", "programming", ...],
    ...
}
```

**AFTER:**
```python
# Keywords loaded from domains.json configuration
domain, confidence = config.detect_domain(query)
```

### 2. Hardcoded Roles
**BEFORE:**
```python
IOVBARole = Literal["investigador", "observador", "validador", "builder", "asistente"]
```

**AFTER:**
```python
# Roles loaded from roles.json configuration
roles = config.get_roles()
```

### 3. Hardcoded Branding
**BEFORE:**
```python
DOMAIN_BRANDING: Dict[IOVBADomain, IOVBADomainBrand] = {
    "swe": IOVBADomainBrand(domain="swe", name="Software Engineering", ...),
}
```

**AFTER:**
```python
# Branding loaded from configuration
domain_config = config.get_domain("swe")
elegant_name = domain_config.get("elegant_name")
```

### 4. Switch/If-Else Chains (OCP Violations)
**BEFORE:**
```python
if domain == "swe":
    mcp_servers = ["github", "docker"]
elif domain == "salud":
    mcp_servers = ["medical-db", "hl7-fhir"]
# ... more elif chains
```

**AFTER:**
```python
# Configuration-driven - no if/else chains
mcp_servers = config.get_mcp_servers_for_domain(domain)
```

---

## SOLID Compliance Achieved

### SRP (Single Responsibility Principle)
- Each module has a single responsibility
- ConfigLoader: Load configuration
- AgentGroupManager: Manage agent groups
- NEXUSSuperAgent: Coordinate agents

### OCP (Open/Closed Principle)
- System is open for extension via configuration
- Closed for modification - no need to change code to add new domains/roles
- Simply add to JSON configuration files

### LSP (Liskov Substitution Principle)
- All agents implement the same AgentProfile interface
- Any agent can be substituted for another

### ISP (Interface Segregation Principle)
- Interfaces are specific and segregated
- SkillsRegistry for skills
- MCPRegistry for MCP servers
- PersonaManager for personas

### DIP (Dependency Inversion Principle)
- High-level modules depend on abstractions
- Configuration is injected via ConfigLoader
- No hardcoded dependencies

---

## Next Steps

1. **Update all imports** - Run a search-replace for `from src.iovba` to `from src.agent_system`
2. **Remove old iovba directory** - After imports are updated
3. **Update API routes** - Ensure endpoints serve configuration
4. **Update frontend components** - Remove IOVBA references
5. **Run tests** - Ensure all tests pass
6. **Deploy** - Push changes to repository

---

## Configuration Extension

To add a new domain, simply add to `domains.json`:

```json
{
  "new_domain": {
    "id": "new_domain",
    "name": "New Domain",
    "elegant_name": "NEWDOM",
    "tagline": "New Domain Tagline",
    "icon": "Star",
    "color": "#FF5733",
    "description": "Description of new domain",
    "keywords": ["keyword1", "keyword2"],
    "mcp_servers": ["server1", "server2"]
  }
}
```

To add a new role, add to `roles.json`:

```json
{
  "new_role": {
    "id": "new_role",
    "name": "new_role",
    "elegant_name": "NEW_ROLE",
    "tagline": "New Role Tagline",
    "description": "Description of new role",
    "icon": "Star",
    "color": "#FF5733",
    "gradient": "from-red-500 to-orange-500",
    "skills": ["skill1", "skill2"],
    "tools": ["tool1", "tool2"],
    "keywords": ["keyword1"]
  }
}
```

No code changes required!

---

## File Changes Summary

### New Files Created
- `src/config/agent_config/domains.json`
- `src/config/agent_config/roles.json`
- `src/config/agent_config/platform.json`
- `src/config/agent_config/__init__.py`
- `src/agent_system/__init__.py`
- `src/agent_system/nexus.py`
- `src/agent_system/action/__init__.py`
- `src/agent_system/behavior/__init__.py`
- `src/agent_system/validation/__init__.py`
- `src/agent_system/orchestration/__init__.py`
- `src/agent_system/infrastructure/__init__.py`

### Files Updated
- `frontend/src/types/index.ts`
- `frontend/src/stores/index.ts`

### Files to Remove
- `src/iovba/*` (entire directory)

### Files Needing Import Updates
- `src/api/*.py`
- `src/core/*.py`
- `src/queue/*.py`
- `src/services/*.py`
- `scripts/*.py`
- `tests/*.py`
- `frontend/src/app/*.tsx`
- `frontend/src/components/**/*.tsx`

---

## Verification Checklist

- [ ] All imports updated from `src.iovba` to `src.agent_system`
- [ ] No hardcoded "IOVBA" references in code
- [ ] No hardcoded domain/role names
- [ ] Configuration files loaded correctly
- [ ] Domain detection works from configuration
- [ ] Role detection works from configuration
- [ ] API endpoints return configuration data
- [ ] Frontend displays configuration-driven data
- [ ] Tests pass
- [ ] Build succeeds
