# Pattern Analysis and Refactoring Plan

## Executive Summary

This document provides a comprehensive analysis of the current architecture patterns and a detailed refactoring plan based on SOLID principles to achieve a solid, testable, and maintainable integration layer.

---

## 1. Current Architecture Analysis

### 1.1 Pattern Identification

#### Frontend Patterns (Next.js 16 + React 19)

| Pattern | Location | Status | Issues |
|---------|----------|--------|--------|
| **State Management** | Zustand stores (`/stores/index.ts`) | ✅ Good | Well-structured with devtools |
| **API Client** | `@/lib/api/client` | ⚠️ Needs Work | Missing error handling, retry logic |
| **Component Architecture** | shadcn/ui components | ✅ Good | Atomic design approach |
| **Type System** | TypeScript types (`/types/index.ts`) | ✅ Good | Comprehensive type definitions |
| **Data Fetching** | Custom hooks + stores | ⚠️ Needs Work | No caching, no optimistic updates |

#### Backend Patterns (FastAPI + Python)

| Pattern | Location | Status | Issues |
|---------|----------|--------|--------|
| **Dependency Injection** | Service providers | ✅ Good | Container pattern implemented |
| **Repository Pattern** | Not implemented | ❌ Missing | Direct DB access in services |
| **Factory Pattern** | Agent factory | ✅ Good | Profile-based agent creation |
| **Middleware** | ORIGINS middleware | ✅ Good | CORS, streaming, sanitization |
| **Event-Driven** | Queue system | ⚠️ Partial | Redis queues present but underutilized |

### 1.2 Integration Patterns

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         CURRENT INTEGRATION FLOW                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   Frontend (Next.js)           Backend (FastAPI)          External      │
│   ─────────────────           ──────────────────          ────────      │
│                                                                          │
│   ┌──────────────┐            ┌──────────────┐           ┌───────────┐ │
│   │   Zustand    │──HTTP─────▶│   FastAPI    │──HTTP────▶│ OpenRouter│ │
│   │   Stores     │            │   Routes     │           │   LLM     │ │
│   └──────────────┘            └──────────────┘           └───────────┘ │
│         │                            │                                   │
│         │                            ▼                                   │
│         │                    ┌──────────────┐                           │
│         │                    │   Services   │                           │
│         │                    └──────────────┘                           │
│         │                            │                                   │
│         │              ┌─────────────┼─────────────┐                    │
│         │              ▼             ▼             ▼                    │
│         │       ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│         │       │  NEXUS   │  │  IOVBA   │  │   MCP    │               │
│         │       │  Agent   │  │  Groups  │  │  Servers │               │
│         │       └──────────┘  └──────────┘  └──────────┘               │
│         │                                                            │
│         │              ┌─────────────┴─────────────┐                  │
│         │              ▼                           ▼                  │
│         │       ┌──────────────┐          ┌──────────────┐           │
│         │       │   Cognitive  │          │    Memory    │           │
│         │       │   Capital    │          │     VCS      │           │
│         │       └──────────────┘          └──────────────┘           │
│         │                                                            │
└─────────┼────────────────────────────────────────────────────────────┘
          │
          ▼
   MISSING: Repository Layer
   MISSING: Domain Events
   MISSING: CQRS Pattern
   MISSING: Circuit Breaker
```

---

## 2. SOLID Principle Analysis

### 2.1 Single Responsibility Principle (SRP)

**Current Issues:**
- `AgentService` handles creation, retrieval, updates, deletion, AND cognitive capital
- `NEXUSRoutes` mixes routing logic with business logic
- Frontend stores handle both state AND API calls

**Proposed Changes:**
```python
# BEFORE (SRP Violation)
class AgentService:
    def create_agent(self): ...
    def get_agent(self): ...
    def update_capital(self): ...  # Different responsibility
    def record_interaction(self): ...  # Different responsibility

# AFTER (SRP Compliant)
class AgentRepository:
    def create(self): ...
    def get(self): ...
    def update(self): ...
    def delete(self): ...

class CognitiveCapitalService:
    def update_capital(self): ...
    def record_interaction(self): ...

class AgentOrchestrator:
    def coordinate_agents(self): ...
```

### 2.2 Open/Closed Principle (OCP)

**Current Issues:**
- Adding new domains requires modifying `DomainConfig`
- Adding new roles requires code changes
- Skill extension requires modifying core files

**Proposed Changes:**
```python
# BEFORE (OCP Violation)
class DomainRouter:
    def route(self, domain: str):
        if domain == "swe": ...
        elif domain == "salud": ...
        # Adding new domain requires modifying this method

# AFTER (OCP Compliant)
class DomainRouter:
    def __init__(self, domain_handlers: Dict[str, DomainHandler]):
        self._handlers = domain_handlers
    
    def route(self, domain: str):
        handler = self._handlers.get(domain, self._default_handler)
        return handler.handle()

# New domains can be added without modifying the class
domain_handlers = {
    "swe": SWEDomainHandler(),
    "salud": SaludDomainHandler(),
    # Add new domains here
}
```

### 2.3 Liskov Substitution Principle (LSP)

**Current Issues:**
- Agent subclasses may not be substitutable due to missing method implementations
- Provider implementations have inconsistent interfaces

**Proposed Changes:**
```python
# Define clear contracts with ABC
class BaseAgent(ABC):
    @abstractmethod
    async def process(self, input: AgentInput) -> AgentOutput:
        """All agents must implement this method"""
        pass
    
    @abstractmethod
    async def get_capabilities(self) -> List[Capability]:
        """All agents must return their capabilities"""
        pass

# Now any agent can be substituted
class NEXUSAgent(BaseAgent):
    async def process(self, input: AgentInput) -> AgentOutput: ...
    async def get_capabilities(self) -> List[Capability]: ...

class DomainAgent(BaseAgent):
    async def process(self, input: AgentInput) -> AgentOutput: ...
    async def get_capabilities(self) -> List[Capability]: ...
```

### 2.4 Interface Segregation Principle (ISP)

**Current Issues:**
- `AgentProfile` interface includes fields not needed by all consumers
- API clients have methods that throw "not implemented"

**Proposed Changes:**
```typescript
// BEFORE (ISP Violation)
interface AgentProfile {
  id: string;
  name: string;
  // ... basic fields
  cognitive_capital: CognitiveCapital;  // Not needed for listing
  metrics: AgentMetrics;  // Not needed for creation
  prompt_template: string;  // Not needed for display
}

// AFTER (ISP Compliant)
interface AgentBase {
  id: string;
  name: string;
  description: string;
  domain: string;
  status: AgentStatus;
}

interface AgentWithCapital extends AgentBase {
  cognitive_capital: CognitiveCapital;
}

interface AgentWithMetrics extends AgentBase {
  metrics: AgentMetrics;
}

interface AgentFull extends AgentWithCapital, AgentWithMetrics {
  prompt_template: string;
  skills: string[];
  tools: string[];
}
```

### 2.5 Dependency Inversion Principle (DIP)

**Current Issues:**
- High-level modules depend directly on low-level implementations
- Services instantiate their own dependencies

**Proposed Changes:**
```python
# BEFORE (DIP Violation)
class NEXUSAgent:
    def __init__(self):
        self.llm = OpenRouterProvider()  # Direct dependency
        self.memory = MemoryVCS()  # Direct dependency

# AFTER (DIP Compliant)
class NEXUSAgent:
    def __init__(
        self,
        llm_provider: ILLMProvider,  # Abstraction
        memory_store: IMemoryStore,  # Abstraction
        capital_engine: ICapitalEngine  # Abstraction
    ):
        self._llm = llm_provider
        self._memory = memory_store
        self._capital = capital_engine

# Dependencies injected from container
container.register(ILLMProvider, OpenRouterProvider)
container.register(IMemoryStore, MemoryVCS)
container.register(ICapitalEngine, CognitiveCapitalEngine)
```

---

## 3. Refactoring Plan

### Phase 1: Repository Layer (Week 1)

```python
# src/repositories/base.py
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional

T = TypeVar('T')

class IRepository(ABC, Generic[T]):
    """Repository contract following DIP"""
    
    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[T]:
        pass
    
    @abstractmethod
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        pass
    
    @abstractmethod
    async def create(self, entity: T) -> T:
        pass
    
    @abstractmethod
    async def update(self, entity: T) -> T:
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        pass


# src/repositories/agent_repository.py
class AgentRepository(IRepository[AgentProfile]):
    def __init__(self, db: Session):
        self._db = db
    
    async def get_by_id(self, id: str) -> Optional[AgentProfile]:
        return self._db.query(AgentModel).filter(AgentModel.id == id).first()
    
    async def get_by_domain(self, domain: str) -> List[AgentProfile]:
        return self._db.query(AgentModel).filter(AgentModel.domain == domain).all()
    
    async def get_active_agents(self) -> List[AgentProfile]:
        return self._db.query(AgentModel).filter(AgentModel.status == 'active').all()
```

### Phase 2: Service Layer Refactoring (Week 2)

```python
# src/services/agents/agent_service.py
class AgentService:
    """High-level agent coordination (SRP compliant)"""
    
    def __init__(
        self,
        repository: IAgentRepository,
        capital_service: ICognitiveCapitalService,
        event_publisher: IEventPublisher
    ):
        self._repository = repository
        self._capital = capital_service
        self._events = event_publisher
    
    async def create_agent(self, config: AgentConfig) -> AgentProfile:
        agent = await self._repository.create(config)
        await self._capital.initialize(agent.id)
        await self._events.publish(AgentCreatedEvent(agent.id))
        return agent


# src/services/agents/cognitive_capital_service.py
class CognitiveCapitalService:
    """Single responsibility: cognitive capital management"""
    
    def __init__(
        self,
        engram_repository: IEngramRepository,
        memory_vcs: IMemoryVCS,
        embedding_service: IEmbeddingService
    ):
        self._engrams = engram_repository
        self._memory = memory_vcs
        self._embeddings = embedding_service
    
    async def record_interaction(
        self, 
        agent_id: str, 
        interaction: Interaction
    ) -> Engram:
        embedding = await self._embeddings.create(interaction.content)
        engram = Engram(
            agent_id=agent_id,
            content=interaction.content,
            embedding=embedding,
            source='interaction'
        )
        await self._engrams.create(engram)
        await self._memory.commit(agent_id, engram)
        return engram
```

### Phase 3: Event-Driven Architecture (Week 3)

```python
# src/events/base.py
from dataclasses import dataclass
from datetime import datetime
from typing import Any

@dataclass
class DomainEvent:
    id: str
    timestamp: datetime
    payload: Any

@dataclass
class AgentCreatedEvent(DomainEvent):
    agent_id: str
    domain: str

@dataclass
class InteractionRecordedEvent(DomainEvent):
    agent_id: str
    user_id: str
    interaction_type: str


# src/events/handlers.py
class EventHandler(ABC):
    @abstractmethod
    async def handle(self, event: DomainEvent) -> None:
        pass

class CognitiveCapitalEventHandler(EventHandler):
    async def handle(self, event: DomainEvent) -> None:
        if isinstance(event, InteractionRecordedEvent):
            await self._update_capital(event.agent_id)

class MemoryVCSEventHandler(EventHandler):
    async def handle(self, event: DomainEvent) -> None:
        if isinstance(event, InteractionRecordedEvent):
            await self._commit_to_memory(event)
```

### Phase 4: Frontend Integration Layer (Week 4)

```typescript
// lib/api/repository.ts
interface IApiRepository<T> {
  getAll(params?: QueryParams): Promise<PaginatedResponse<T>>;
  getById(id: string): Promise<T>;
  create(data: Partial<T>): Promise<T>;
  update(id: string, data: Partial<T>): Promise<T>;
  delete(id: string): Promise<void>;
}

// lib/api/repositories/agent.repository.ts
class AgentRepository implements IApiRepository<AgentProfile> {
  private client: ApiClient;
  
  constructor(client: ApiClient) {
    this.client = client;
  }
  
  async getAll(params?: QueryParams): Promise<PaginatedResponse<AgentProfile>> {
    return this.client.get('/agents', { params });
  }
  
  async getById(id: string): Promise<AgentProfile> {
    return this.client.get(`/agents/${id}`);
  }
  
  async getByDomain(domain: string): Promise<AgentProfile[]> {
    return this.client.get(`/agents/domain/${domain}`);
  }
  
  async getActive(): Promise<AgentProfile[]> {
    return this.client.get('/agents/active');
  }
}

// lib/api/client.ts
class ApiClient {
  private baseURL: string;
  private cache: Map<string, CacheEntry>;
  private retryPolicy: RetryPolicy;
  
  constructor(config: ApiClientConfig) {
    this.baseURL = config.baseURL;
    this.cache = new Map();
    this.retryPolicy = config.retryPolicy || new ExponentialBackoffRetry();
  }
  
  async get<T>(path: string, options?: RequestOptions): Promise<T> {
    const cacheKey = this.getCacheKey(path, options);
    
    if (options?.cache && this.cache.has(cacheKey)) {
      return this.cache.get(cacheKey)!.data;
    }
    
    return this.withRetry(async () => {
      const response = await fetch(`${this.baseURL}${path}`, {
        method: 'GET',
        headers: this.getHeaders(),
      });
      
      if (!response.ok) {
        throw new ApiError(response.status, await response.text());
      }
      
      const data = await response.json();
      
      if (options?.cache) {
        this.cache.set(cacheKey, { data, timestamp: Date.now() });
      }
      
      return data;
    });
  }
  
  private async withRetry<T>(fn: () => Promise<T>): Promise<T> {
    let lastError: Error;
    
    for (let i = 0; i < this.retryPolicy.maxRetries; i++) {
      try {
        return await fn();
      } catch (error) {
        lastError = error;
        if (!this.retryPolicy.shouldRetry(error, i)) {
          throw error;
        }
        await this.retryPolicy.wait(i);
      }
    }
    
    throw lastError;
  }
}
```

---

## 4. Integration Test Strategy

### 4.1 Test Pyramid

```
                    ┌───────────┐
                   │    E2E    │  (Few, Slow, Expensive)
                  │   Tests   │
                 └───────────┘
                ┌─────────────────┐
               │   Integration   │  (Some, Medium speed)
              │     Tests       │
             └─────────────────┘
            ┌───────────────────────┐
           │      Unit Tests       │  (Many, Fast, Cheap)
          │                       │
         └───────────────────────┘
```

### 4.2 Test Categories

| Category | Scope | Tools | Coverage Target |
|----------|-------|-------|-----------------|
| **Unit** | Individual functions/classes | pytest, jest | 80% |
| **Integration** | API endpoints, DB interactions | pytest-asyncio, testcontainers | 70% |
| **Contract** | API contracts, schemas | schemathesis | 100% endpoints |
| **E2E** | Full user flows | playwright | Critical paths |

### 4.3 Test Structure

```python
# tests/integration/test_nexus_integration.py
"""
Integration tests for NEXUS Super Agent

Tests the complete flow:
1. User sends message
2. NEXUS processes and routes
3. Domain agents respond
4. Cognitive capital updated
5. Memory VCS committed
"""
import pytest
from httpx import AsyncClient
from src.main import app

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def mock_llm_provider():
    """Mock LLM for deterministic testing"""
    return MockLLMProvider(responses={
        "What is AI?": "Artificial Intelligence is...",
    })

class TestNEXUSIntegration:
    """Integration tests for NEXUS Super Agent"""
    
    @pytest.mark.asyncio
    async def test_chat_flow_updates_cognitive_capital(
        self, 
        client: AsyncClient,
        mock_llm_provider
    ):
        # 1. Get initial capital
        initial = await client.get("/api/v1/nexus/capital")
        initial_capital = initial.json()["capital_value"]
        
        # 2. Send message
        response = await client.post(
            "/api/v1/nexus/chat",
            json={"message": "What is AI?"}
        )
        assert response.status_code == 200
        
        # 3. Verify capital increased
        final = await client.get("/api/v1/nexus/capital")
        assert final.json()["capital_value"] > initial_capital
    
    @pytest.mark.asyncio
    async def test_domain_routing_accuracy(self, client: AsyncClient):
        """Test that NEXUS correctly routes to domains"""
        test_cases = [
            ("Create a Python function", "swe"),
            ("What are the symptoms of flu?", "salud"),
            ("Analyze AAPL stock", "finanzas"),
        ]
        
        for message, expected_domain in test_cases:
            response = await client.post(
                "/api/v1/nexus/chat",
                json={"message": message}
            )
            assert response.json()["domain"] == expected_domain
```

---

## 5. Implementation Checklist

### Phase 1: Repository Layer
- [ ] Create `IRepository` interface
- [ ] Implement `AgentRepository`
- [ ] Implement `EngramRepository`
- [ ] Implement `MemoryRepository`
- [ ] Add repository unit tests

### Phase 2: Service Refactoring
- [ ] Extract `CognitiveCapitalService` from `AgentService`
- [ ] Create `DomainRouter` with OCP compliance
- [ ] Implement `EventHandler` pattern
- [ ] Add service integration tests

### Phase 3: Frontend Integration
- [ ] Create `ApiClient` with retry logic
- [ ] Implement `AgentRepository` (frontend)
- [ ] Add optimistic updates to stores
- [ ] Add frontend integration tests

### Phase 4: E2E Testing
- [ ] Set up Playwright
- [ ] Test NEXUS chat flow
- [ ] Test agent management flow
- [ ] Test cognitive capital visualization

---

## 6. Success Metrics

| Metric | Current | Target | Measurement |
|--------|---------|--------|-------------|
| Test Coverage | ~40% | 80% | pytest-cov |
| API Response Time | 200ms | 100ms | OpenTelemetry |
| Error Rate | 5% | 0.5% | Logging |
| Code Duplication | High | Low | SonarQube |
| SOLID Violations | 12 | 0 | Architecture tests |
