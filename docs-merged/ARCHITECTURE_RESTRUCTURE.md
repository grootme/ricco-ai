# RICCO Ecosystem - Architectural Restructure Plan

## Executive Summary

This document outlines the comprehensive architectural restructure of the RICCO ecosystem, following microservices best practices and domain-driven design principles.

---

## 1. Current Architecture Analysis

### 1.1 Problems Identified

#### 1.1.1 Misplaced Modules in services/genui

The `genui` service is designed exclusively for **Generative UI using AI**. However, it currently contains:

| Module | Current Location | Should Be | Priority |
|--------|------------------|-----------|----------|
| `payments/` | services/genui/payments/ | services/payment-service/ | HIGH |
| `notifications/` | services/genui/notifications/ | services/notification-service/ | MEDIUM |
| `location/` | services/genui/location/ | services/location-service/ | MEDIUM |
| `legal/` | services/genui/legal/ | services/legal-service/ | LOW |
| `mcp_registry/` | services/genui/mcp_registry/ | services/ricco-ai/mcp/ | HIGH |
| `mcp_proxy/` | services/genui/mcp_proxy/ | services/ricco-ai/mcp/ | HIGH |
| `agent_swarm/` | services/genui/agent_swarm/ | services/ricco-ai/agents/ | HIGH |
| `agent_factory/` | services/genui/agent_factory/ | services/ricco-ai/agents/ | HIGH |
| `agent_graphs/` | services/genui/agent_graphs/ | services/ricco-ai/agents/ | HIGH |
| `context_engine/` | services/genui/context_engine/ | services/ricco-ai/context/ | HIGH |
| `context_bundles/` | services/genui/context_bundles/ | services/ricco-ai/context/ | HIGH |
| `event_sourcing/` | services/genui/event_sourcing/ | services/shared/event_sourcing/ | MEDIUM |
| `cdc/` | services/genui/cdc/ | services/shared/cdc/ | MEDIUM |
| `langgraph_dag/` | services/genui/langgraph_dag/ | services/ricco-ai/dag/ | HIGH |
| `ai_services/` | services/genui/ai_services/ | services/ricco-ai/ai/ | HIGH |

#### 1.1.2 Duplicated Web Structures

| Path | Type | Action |
|------|------|--------|
| `web/mall/` | Backend + Storefront | Consolidate into `web/commerce/` |
| `web/mall-storefront/` | Duplicate Storefront | Merge with `web/commerce/storefronts/mall/` |
| `web/commerce/wholesale/` | Duplicate | Merge with `web/commerce/storefronts/wholesale/` |

---

## 2. Target Architecture

### 2.1 Services Architecture

```
services/
├── ricco-ai/                      # AI Orchestration Service
│   ├── src/
│   │   ├── agents/               # Agent management (from genui)
│   │   │   ├── agent_swarm/
│   │   │   ├── agent_factory/
│   │   │   └── agent_graphs/
│   │   ├── context/              # Context engineering (from genui)
│   │   │   ├── context_engine/
│   │   │   └── context_bundles/
│   │   ├── mcp/                  # MCP Registry & Proxy (from genui)
│   │   │   ├── registry/
│   │   │   └── proxy/
│   │   ├── dag/                  # DAG execution (from genui)
│   │   │   └── langgraph_dag/
│   │   ├── ai/                   # AI providers (from genui)
│   │   │   └── ai_services/
│   │   ├── a2ui/                 # A2UI Module (from genui)
│   │   │   ├── service/
│   │   │   ├── streaming/
│   │   │   └── registry/
│   │   ├── schemas/              # DB-managed configs
│   │   ├── seeds/                # Initial seeds
│   │   └── services/
│   ├── migrations/
│   └── tests/
│
├── payment-service/              # Payment Gateway Service
│   ├── src/
│   │   ├── gateways/
│   │   │   ├── mmg/             # Mobile Money Guyana
│   │   │   ├── binance/
│   │   │   ├── bybit/
│   │   │   ├── coinex/
│   │   │   ├── stripe/
│   │   │   └── paypal/
│   │   ├── models/
│   │   ├── routes/
│   │   └── webhooks/
│   └── tests/
│
├── notification-service/         # Notification Service
│   ├── src/
│   │   ├── providers/
│   │   │   ├── firebase/
│   │   │   ├── email/
│   │   │   └── sms/
│   │   ├── templates/
│   │   └── routes/
│   └── tests/
│
├── location-service/             # Location & Currency Service
│   ├── src/
│   │   ├── countries/
│   │   ├── currencies/
│   │   ├── languages/
│   │   └── exchange/
│   └── tests/
│
├── ricco-id/                     # Identity Service (existing)
│   └── ...
│
├── shared/                       # Shared Infrastructure
│   ├── event_sourcing/
│   ├── cdc/
│   └── utils/
│
└── genui/                        # DEPRECATED - Will be removed
    └── (only a2ui components remain, moved to ricco-ai)
```

### 2.2 Web Architecture

```
web/
├── commerce/
│   ├── backend/                  # MedusaJS Backend
│   │   ├── src/
│   │   │   ├── modules/
│   │   │   ├── api/
│   │   │   └── workflows/
│   │   └── ...
│   │
│   ├── storefronts/
│   │   ├── mall/                # B2C Storefront (UNIFIED)
│   │   │   ├── src/
│   │   │   └── ...
│   │   │
│   │   └── wholesale/           # B2B Storefront (UNIFIED)
│   │       ├── src/
│   │       └── ...
│   │
│   ├── pos/                      # Point of Sale
│   │   └── ...
│   │
│   └── food/                     # Food Delivery
│       └── ...
│
├── health/                       # Health App
│   └── ...
│
├── booking/                      # Booking App
│   └── ...
│
├── logistics/                    # Logistics App
│   └── ...
│
├── finance/                      # Finance App
│   └── ...
│
└── connect/                      # Jobs App
    └── ...

```

---

## 3. Database-Managed Configuration

### 3.1 Schema for Dynamic Configuration

All configurations must be stored in the database and loaded as seeds, eliminating hardcoded values.

```sql
-- MCP Servers Configuration
CREATE TABLE mcp_servers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    category VARCHAR(100) NOT NULL,
    transport_type VARCHAR(50) NOT NULL, -- 'stdio', 'http', 'websocket'
    command TEXT,
    args JSONB,
    env JSONB,
    url TEXT,
    headers JSONB,
    enabled BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 5,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- MCP Tools Configuration
CREATE TABLE mcp_tools (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    server_id UUID REFERENCES mcp_servers(id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    input_schema JSONB,
    output_schema JSONB,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Agent Configurations
CREATE TABLE agent_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    type VARCHAR(100) NOT NULL, -- 'support', 'sales', 'advisor', 'specialist'
    system_prompt TEXT,
    model VARCHAR(100) DEFAULT 'gemini-2.0-flash',
    temperature DECIMAL(3,2) DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 4096,
    tools JSONB, -- Array of tool names
    mcp_servers JSONB, -- Array of MCP server names
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Context Providers Configuration
CREATE TABLE context_providers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    type VARCHAR(100) NOT NULL, -- 'personal', 'temporal', 'spatial', 'device', etc.
    priority INTEGER DEFAULT 5,
    cache_ttl INTEGER DEFAULT 300,
    config JSONB,
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- A2UI Component Registry
CREATE TABLE a2ui_components (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    category VARCHAR(100) NOT NULL,
    schema JSONB NOT NULL,
    default_props JSONB,
    platforms JSONB, -- ['react', 'flutter', 'lit']
    version VARCHAR(50) DEFAULT '1.0.0',
    enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Themes Configuration
CREATE TABLE themes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    type VARCHAR(50) DEFAULT 'light', -- 'light', 'dark', 'custom'
    colors JSONB NOT NULL,
    typography JSONB,
    spacing JSONB,
    components JSONB,
    is_default BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 3.2 Seed Data Structure

```typescript
// services/ricco-ai/seeds/mcp_servers.seed.ts
export const mcpServersSeed = [
  {
    name: 'filesystem',
    category: 'filesystem',
    transport_type: 'stdio',
    command: 'npx',
    args: ['-y', '@modelcontextprotocol/server-filesystem', '/data'],
    env: {},
    priority: 1,
    enabled: true
  },
  {
    name: 'postgres',
    category: 'database',
    transport_type: 'stdio',
    command: 'npx',
    args: ['-y', '@modelcontextprotocol/server-postgres'],
    env: { DATABASE_URL: process.env.DATABASE_URL },
    priority: 2,
    enabled: true
  },
  // ... more servers
];

// services/ricco-ai/seeds/agents.seed.ts
export const agentsSeed = [
  {
    name: 'support_agent',
    type: 'support',
    system_prompt: 'You are a helpful support assistant...',
    model: 'gemini-2.0-flash',
    temperature: 0.7,
    tools: ['search', 'create_ticket', 'get_order'],
    mcp_servers: ['filesystem', 'postgres']
  },
  // ... more agents
];
```

---

## 4. MCP Proxy Implementation

### 4.1 Token Optimization Strategy

The MCP Proxy implements caching, load balancing, and circuit breaking to optimize token consumption.

```
┌─────────────────────────────────────────────────────────────────┐
│                        MCP Proxy Layer                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐       │
│  │   Request    │──▶│   Router     │──▶│   Load       │       │
│  │   Handler    │   │   (by tool)  │   │   Balancer   │       │
│  └──────────────┘   └──────────────┘   └──────────────┘       │
│                                                │                │
│                                                ▼                │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐       │
│  │   Response   │◀──│   Cache      │◀──│   Circuit    │       │
│  │   Handler    │   │   (Redis)    │   │   Breaker    │       │
│  └──────────────┘   └──────────────┘   └──────────────┘       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Implementation

```python
# services/ricco-ai/mcp/proxy/token_aware_proxy.py

class TokenAwareMCPProxy:
    """
    MCP Proxy that optimizes token consumption through:
    1. Response caching (deduplicate identical requests)
    2. Request batching (combine multiple tool calls)
    3. Circuit breaking (prevent cascading failures)
    4. Load balancing (distribute across server pool)
    """
    
    def __init__(self, redis_client, config):
        self.redis = redis_client
        self.cache_ttl = config.get('cache_ttl', 300)
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60
        )
        self.load_balancer = LoadBalancer(strategy='round_robin')
        
    async def execute_tool(self, tool_name: str, params: dict) -> dict:
        # 1. Check cache first
        cache_key = self._generate_cache_key(tool_name, params)
        cached = await self.redis.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # 2. Route to appropriate MCP server
        server = self.load_balancer.get_server(tool_name)
        
        # 3. Execute with circuit breaker
        try:
            result = await self.circuit_breaker.execute(
                lambda: server.call_tool(tool_name, params)
            )
        except CircuitBreakerOpen:
            # Fallback to cached data or error
            return await self._handle_failure(tool_name, params)
        
        # 4. Cache successful response
        await self.redis.setex(
            cache_key,
            self.cache_ttl,
            json.dumps(result)
        )
        
        return result
    
    def _generate_cache_key(self, tool_name: str, params: dict) -> str:
        """Generate deterministic cache key"""
        params_hash = hashlib.sha256(
            json.dumps(params, sort_keys=True).encode()
        ).hexdigest()[:16]
        return f"mcp:cache:{tool_name}:{params_hash}"
```

---

## 5. Google A2UI Integration

### 5.1 Integration Strategy

Use Google's A2UI library directly instead of reimplementing. The integration follows these principles:

1. **Direct Dependency**: Add `@google/a2ui` as a dependency
2. **Extend, Don't Replace**: Extend Google's components, don't reimplement
3. **Configuration over Code**: Use database-stored schemas for component definitions

```typescript
// services/ricco-ai/src/a2ui/google_adapter.ts

import { A2UI } from '@google/a2ui';
import { ComponentRegistry } from './registry/component_registry';
import { ThemeManager } from './registry/theme_manager';

export class GoogleA2UIAdapter {
    private a2ui: A2UI;
    private registry: ComponentRegistry;
    private themes: ThemeManager;
    
    constructor(config: A2UIConfig) {
        // Initialize Google's A2UI
        this.a2ui = new A2UI({
            apiKey: config.googleApiKey,
            model: config.model || 'gemini-2.0-flash',
        });
        
        // Load components from database
        this.registry = new ComponentRegistry(config.db);
        this.themes = new ThemeManager(config.db);
    }
    
    async generateUI(prompt: string, context: ContextBundle): Promise<A2UIResponse> {
        // Get registered components
        const components = await this.registry.getEnabled();
        
        // Get theme
        const theme = await this.themes.getActive();
        
        // Generate using Google's A2UI
        const response = await this.a2ui.generate({
            prompt,
            components: components.map(c => c.schema),
            theme: theme.config,
            context: context.toPrompt(),
        });
        
        return {
            component: response.component,
            props: response.props,
            platform: context.platform || 'react',
        };
    }
    
    async streamUI(prompt: string, context: ContextBundle): AsyncGenerator<StreamEvent> {
        // Stream using Google's A2UI
        for await (const event of this.a2ui.stream({
            prompt,
            components: await this.registry.getEnabled(),
            theme: await this.themes.getActive(),
            context: context.toPrompt(),
        })) {
            yield this._transformEvent(event);
        }
    }
}
```

---

## 6. Migration Execution Plan

### Phase 1: Create New Service Structure (Week 1)

1. Create `services/payment-service/` structure
2. Create `services/notification-service/` structure  
3. Create `services/location-service/` structure
4. Move payment gateways from genui to payment-service
5. Move notification providers from genui to notification-service
6. Move location data from genui to location-service

### Phase 2: Integrate genui into ricco-ai (Week 2)

1. Move MCP Registry & Proxy to `services/ricco-ai/mcp/`
2. Move Agent modules to `services/ricco-ai/agents/`
3. Move Context modules to `services/ricco-ai/context/`
4. Move A2UI modules to `services/ricco-ai/a2ui/`
5. Implement database-managed configuration
6. Create seed scripts

### Phase 3: Unify Web Structure (Week 3)

1. Consolidate `web/mall/` into `web/commerce/`
2. Merge `web/mall-storefront/` into `web/commerce/storefronts/mall/`
3. Merge `web/commerce/wholesale/` into `web/commerce/storefronts/wholesale/`
4. Update all imports and references

### Phase 4: Testing & Documentation (Week 4)

1. Write integration tests
2. Update API documentation
3. Update deployment configurations
4. Create migration guide for developers

---

## 7. Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Service Coupling | High | Low | Dependency analysis |
| Token Consumption | Baseline | -30% | MCP Proxy metrics |
| Deployment Independence | 2 services | 5+ services | Independent deployments |
| Code Duplication | ~40% | <5% | Code analysis |
| Configuration Flexibility | Hardcoded | DB-managed | Config change time |

---

## 8. Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Breaking existing integrations | High | Maintain backward compatibility layer |
| Data migration failures | High | Backup before migration, rollback scripts |
| Performance degradation | Medium | Load testing before deployment |
| Developer confusion | Medium | Comprehensive documentation and training |

---

## Appendix A: File Migration Map

### Payment Service Migration

```
services/genui/payments/ → services/payment-service/

payments/
├── mmg_gateway.py      → gateways/mmg/gateway.py
├── mmg_crypto.py       → gateways/mmg/crypto.py
├── mmg_models.py       → gateways/mmg/models.py
├── mmg_routes.py       → gateways/mmg/routes.py
├── binance_gateway.py  → gateways/binance/gateway.py
├── bybit_gateway.py    → gateways/bybit/gateway.py
├── coinex_gateway.py   → gateways/coinex/gateway.py
├── payment_service.py  → service.py
├── gateway_factory.py  → factory.py
├── models.py           → models/payment.py
└── base.py             → base.py
```

### ricco-ai Integration Map

```
services/genui/mcp_registry/    → services/ricco-ai/src/mcp/registry/
services/genui/mcp_proxy/       → services/ricco-ai/src/mcp/proxy/
services/genui/agent_swarm/     → services/ricco-ai/src/agents/swarm/
services/genui/agent_factory/   → services/ricco-ai/src/agents/factory/
services/genui/agent_graphs/    → services/ricco-ai/src/agents/graphs/
services/genui/context_engine/  → services/ricco-ai/src/context/engine/
services/genui/context_bundles/ → services/ricco-ai/src/context/bundles/
services/genui/ai_services/     → services/ricco-ai/src/ai/providers/
services/genui/langgraph_dag/   → services/ricco-ai/src/dag/
services/genui/a2ui_service/    → services/ricco-ai/src/a2ui/service/
services/genui/a2ui_streaming/  → services/ricco-ai/src/a2ui/streaming/
services/genui/a2ui/            → services/ricco-ai/src/a2ui/registry/
```

---

**Document Version**: 1.0  
**Last Updated**: 2026-04-03  
**Author**: RICCO Architecture Team
