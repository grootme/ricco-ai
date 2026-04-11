# RICCO AI Service v2.0 - Integration Guide

## Overview

RICCO AI v2.0 is the centralized AI platform for the RICCO ecosystem (14 solutions).
It routes all LLM calls, RAG pipelines, and agent orchestration through four primary integrations:

| Integration | Role | Priority |
|-------------|------|----------|
| **OpenRouter** | Primary LLM gateway (Claude, GPT-4, Gemini, Llama, vision) | Primary |
| **Flowise** | RAG pipelines, document ingestion, visual workflows | Primary |
| **Evo-AI** | ADK agent platform, A2A protocol, agent orchestration | Primary |
| **OpenClaw** | Open-source agent framework, tool use, multi-agent | Secondary |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    RICCO AI Service v2.0                      │
├──────────────────────────────────────────────────────────────┤
│  ┌────────────┐ ┌────────────┐ ┌──────────┐ ┌────────────┐ │
│  │ OpenRouter │ │  Evo-AI    │ │ Flowise  │ │ OpenClaw   │ │
│  │ (LLMs/     │ │ (A2A/ADK   │ │ (RAG/    │ │ (Agents/   │ │
│  │  Vision)   │ │  Agents)   │ │  Workflows)│ │  Tools)    │ │
│  └─────┬──────┘ └─────┬──────┘ └────┬─────┘ └─────┬──────┘ │
│        └──────────────┬┴─────────────┴────────────┘        │
│               ┌───────┴────────┐                           │
│               │  Integration   │                           │
│               │  Hub (FastAPI) │                           │
│               └───────┬────────┘                           │
├───────────────────────┼────────────────────────────────────┤
│  ┌────────────────────┴───────────────────────────────────┐ │
│  │              14 RICCO Solutions                        │ │
│  ├────────┬────────┬────────┬────────┬────────┬───────────┤ │
│  │Commerce│ Health │Logistics│Funding │ Legal  │ Social    │ │
│  ├────────┼────────┼────────┼────────┼────────┼───────────┤ │
│  │Connect │  ID    │ Assets  │Booking │  Gym   │ POS      │ │
│  ├────────┼────────┼────────┼────────┼────────┼───────────┤ │
│  │ Cargo  │ Travel │ Energy  │        │        │           │ │
│  └────────┴────────┴────────┴────────┴────────┴───────────┘ │
│                                                              │
│  ┌──────────────────────────────────────────────────────────┐│
│  │              MCP Servers Arsenal (50+)                   ││
│  │  Filesystem | Database | Web | AI | Finance | RICCO     ││
│  └──────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────┘
```

---

## Quick Start

### Environment Variables

```bash
# Core
DEBUG=false
SECRET_KEY=your-secret-key

# OpenRouter (Primary LLM Gateway)
OPENROUTER_API_KEY=sk-or-xxx
OPENROUTER_DEFAULT_MODEL=anthropic/claude-3-haiku

# OpenAI (Embeddings only)
OPENAI_API_KEY=sk-xxx

# Vector Store
VECTOR_STORE_PROVIDER=chromadb
CHROMADB_HOST=localhost
CHROMADB_PORT=8000

# Evo-AI (ADK Agents / A2A Protocol)
EVOAI_BASE_URL=http://localhost:8001
EVOAI_API_KEY=xxx
A2A_PROTOCOL_ENABLED=true

# Flowise (RAG Pipelines)
FLOWISE_BASE_URL=http://localhost:3000
FLOWISE_API_KEY=xxx

# OpenClaw
OPENCLAW_BASE_URL=http://localhost:8003
OPENCLAW_API_KEY=xxx

# Feature Flags
ENABLE_STREAMING=true
ENABLE_A2A=true

# Database & Cache
DATABASE_URL=postgresql://ricco:password@localhost:5432/ricco_ai
REDIS_URL=redis://localhost:6379/0
```

### Install & Run

```bash
cd services/ricco-ai
poetry install && uvicorn app.main:app --reload
```

---

## Docker Compose

```yaml
version: "3.8"
services:
  ricco-ai:
    build: .
    ports: ["8000:8000"]
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - EVOAI_BASE_URL=http://evoai:8001
      - FLOWISE_BASE_URL=http://flowise:3000
      - A2A_PROTOCOL_ENABLED=true
    depends_on: [postgres, redis, chromadb, evoai]
    volumes: [./models:/app/models]
  evoai:
    image: evolutionapi/evo-ai:latest
    ports: ["8001:8001"]
    environment:
      - DATABASE_URL=postgresql://ricco:password@postgres:5432/evoai
  postgres:
    image: postgres:16-alpine
    environment: [POSTGRES_USER=ricco, POSTGRES_PASSWORD=password]
  redis:
    image: redis:7-alpine
  chromadb:
    image: chromadb/chroma:latest
    ports: ["8002:8000"]
  flowise:
    image: flowiseai/flowise:latest
    ports: ["3000:3000"]
    profiles: [flowise]
volumes:
  postgres_data:
  redis_data:
  chromadb_data:
  evoai_data:
```

---

## Integration Usage

### OpenRouter (Primary LLM Gateway)

All LLM calls route through OpenRouter, including chat completions and vision (image analysis).

```python
from app.services.openrouter_service import get_openrouter_service
router = get_openrouter_service()

# Chat completion
response = await router.chat(
    model="anthropic/claude-3-haiku",
    messages=[
        {"role": "system", "content": "You are a RICCO Commerce assistant."},
        {"role": "user", "content": "Recommend laptops under $1000"}
    ]
)

# Vision (image analysis via OpenRouter)
response = await router.chat(model="google/gemini-pro-vision", messages=[
    {"role": "user", "content": [
        {"type": "text", "text": "Classify this product image"},
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
    ]}
])
```

### Flowise (RAG & Workflows)

Document ingestion, retrieval, and visual workflow execution.

```python
from app.services.flowise_service import get_flowise_service
flowise = get_flowise_service()

# Ingest documents into RAG pipeline
await flowise.ingest(flow_id="commerce-faq",
    documents=[{"text": "FAQ content...", "metadata": {"source": "faq"}}])

# Query RAG pipeline
result = await flowise.query(flow_id="commerce-faq", question="What is the return policy?")

# Execute a visual workflow (e.g., order processing)
result = await flowise.execute_flow(flow_id="order-processing", input_data={"order_id": "ORD-12345"})
```

### Evo-AI (ADK Agents & A2A Protocol)

Create, execute, and discover agents with full A2A interoperability.

```python
from app.services.evoai_service import get_evoai_service

evoai = get_evoai_service()

# Create an agent for a solution
agent = await evoai.create_ricco_assistant_agent(
    solution="commerce",
    capabilities=["product_search", "recommendations", "support"]
)

# Execute agent
result = await evoai.execute_agent(
    agent_id=agent["id"],
    input_text="Find gaming laptops under $1200",
)

# Register for A2A interoperability
await evoai.register_a2a_agent({
    "agent_id": "commerce-agent-001",
    "endpoint_url": "https://ai.ricco.cu/api/v1/a2a",
    "capabilities": ["product_search", "order_management", "support"]
})

# Discover agents across solutions
agents = await evoai.discover_a2a_agents(capabilities=["shipping", "tracking"])

# Send A2A message to another solution's agent
response = await evoai.send_a2a_message(
    target_agent_id="logistics-agent",
    message={"type": "tracking_request", "order_id": "ORD-12345"}
)
```

### Integration Hub

Central request router for all 14 solutions.

```python
from app.services.ricco_integration import get_integration_hub

hub = get_integration_hub()

# Route request to any solution
result = await hub.process_request({
    "solution": "ricco-commerce",
    "action": "recommend_products",
    "data": {
        "user_id": "user_123",
        "user_profile": {"interests": ["electronics", "gaming"]},
        "limit": 10
    }
})
```

---

## MCP Servers

50+ Model Context Protocol servers organized by category:

| Category | Servers | Purpose |
|----------|---------|---------|
| **Filesystem** | filesystem, S3, Google Drive | File management |
| **Database** | PostgreSQL, MongoDB, Redis, NebulaGraph | Data access |
| **Web** | Fetch, Brave Search, Puppeteer | Scraping & search |
| **AI** | OpenRouter, OpenAI, Ollama, HuggingFace | LLM access |
| **Productivity** | Google Maps, Calendar, Email, Slack | Daily tools |
| **Finance** | Stripe, QvaPay, Crypto, Binance | Payments |
| **RICCO** | ID, Energy, Commerce, Logistics, Health | Solution APIs |
| **DevOps** | GitHub, GitLab, Docker, Kubernetes | CI/CD |
| **Monitoring** | Prometheus, Grafana, Langfuse | Observability |
| **Documents** | PDF, DOCX, XLSX | Document processing |

```python
from app.seeds.mcp_servers import get_mcp_servers_for_solution

# Get recommended MCP servers for a solution
mcps = get_mcp_servers_for_solution("ricco-commerce")
# Returns: postgres, redis, commerce, stripe, qvapay, + AI MCPs
```

## Agent Seeds (27 Agents)

Pre-configured agent templates for all solutions:

| Solution | Agents |
|----------|--------|
| Commerce | assistant, recommender |
| Health | assistant, document-analyst |
| Logistics | assistant, route-optimizer |
| Funding | assistant, analyst |
| Legal | assistant, document-analyst |
| Social | assistant, moderator |
| Connect | assistant, recruiter |
| ID | assistant, kyc-processor |
| Assets | assistant, signature-processor |
| Booking | assistant, pricing-agent |
| Gym | assistant, trainer-agent |
| POS | assistant, analytics-agent |
| Cargo | assistant, customs-agent |
| Travel | assistant, planner-agent |

```python
from app.seeds.agent_seeds import get_agent_seeds_by_solution

agents = get_agent_seeds_by_solution("ricco-commerce")
# Access: agent.system_prompt, agent.capabilities, agent.tools, agent.mcp_servers
```

---

## API Endpoints

### Chat & Completions
- `POST /api/v1/chat/completions` — Chat completions via OpenRouter
- `POST /api/v1/chat/assistant` — RICCO Assistant with solution context

### RAG (via Flowise)
- `POST /api/v1/rag/ingest` — Ingest documents
- `POST /api/v1/rag/query` — Query knowledge base
- `POST /api/v1/rag/rerank` — Rerank results

### Agents (via Evo-AI)
- `GET  /api/v1/agents` — List agents
- `POST /api/v1/agents` — Create agent
- `GET  /api/v1/agents/{id}` — Get agent details
- `POST /api/v1/agents/{id}/execute` — Execute agent

### A2A Protocol
- `GET  /api/v1/a2a/agents` — Discover A2A agents
- `POST /api/v1/a2a/agents` — Register A2A agent
- `POST /api/v1/a2a/agents/{id}/message` — Send A2A message

### Integration Hub
- `GET  /api/v1/solutions` — List registered solutions
- `POST /api/v1/integrate` — Route request to a solution

### Vision (via OpenRouter)
- `POST /api/v1/vision/analyze` — Analyze image content
- `POST /api/v1/vision/classify` — Classify product/document images

---

## Dependencies

| Component | Technology | Version |
|-----------|------------|---------|
| Web Framework | FastAPI | 0.109+ |
| LLM Gateway | OpenRouter | API v1 |
| Agent Platform | Evo-AI | Latest |
| RAG & Workflows | Flowise | Latest |
| Vector Store | ChromaDB | 0.4+ |
| Embeddings | OpenAI | text-embedding-3-small |
| Database | PostgreSQL | 16 |
| Cache | Redis | 7 |

---

## See Also

- [A2UI Integration Guide](./A2UI_INTEGRATION_GUIDE.md) — Context Engineering, Flutter GenUI SDK, React Renderer
