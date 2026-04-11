# RICCO AI Service

> Multi-agent orchestration platform based on [evo-ai](https://github.com/EvolutionAPI/evo-ai) with [A2UI SDK](https://github.com/google/A2UI) integration.

## Overview

RICCO AI is the intelligence layer of the RICCO ecosystem, providing:

- **Multi-Agent Orchestration**: LLM, A2A, Sequential, Parallel, Loop, Workflow, and Task agents
- **A2A Protocol**: Agent-to-Agent interoperability
- **A2UI Integration**: Dynamic UI generation via Google A2UI SDK
- **MCP Support**: 50+ Model Context Protocol tools
- **RICCO ID Integration**: Unified authentication across the ecosystem

## Architecture

```
┌───────────────────────────────────────────────────────────────────────────────┐
│                           AI/ML INTELLIGENCE LAYER                            │
│                                                                               │
│  ┌──────────────────────────────┐  ┌──────────────────────────────────────┐  │
│  │      GENERATIVE AI           │  │        TRADITIONAL AI/ML             │  │
│  │                              │  │                                      │  │
│  │ ┌──────────┐ ┌───────────┐  │  │ ┌──────────┐ ┌──────────┐ ┌────────┐ │  │
│  │ │OpenRouter│ │  Gemini   │  │  │ │TensorFlow│ │  PyTorch │ │ Scikit │ │  │
│  │ │(Multi-  │ │   Pro     │  │  │ │(Images)  │ │ (Custom) │ │ Learn  │ │  │
│  │ │  LLM)   │ │           │  │  │ └──────────┘ └──────────┘ └────────┘ │  │
│  │ └──────────┘ └───────────┘  │  │                                      │  │
│  └──────────────────────────────┘  └──────────────────────────────────────┘  │
│                                                                               │
│  ┌──────────────────────────────┐  ┌──────────────────────────────────────┐  │
│  │      A2UI (Google SDK)       │  │        CONTEXT ENGINEERING           │  │
│  │                              │  │                                      │  │
│  │ • Dynamic Surface Gen        │  │ • Personal Context                   │  │
│  │ • Component Catalog          │  │ • Spatial Context                    │  │
│  │ • Theme Management           │  │ • Temporal Context                   │  │
│  └──────────────────────────────┘  └──────────────────────────────────────┘  │
│                                                                               │
│  ┌─────────────────────────────────────────────────────────────────────────┐  │
│  │                         MCP ARSENAL (50+ Tools)                          │  │
│  │  Filesystem │ Database │ Web │ AI │ Finance │ RICCO │ DevOps │ Docs    │  │
│  └─────────────────────────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────────────────────┘
```

## Agent Types

| Type | Description |
|------|-------------|
| **LLM Agent** | Language model interaction with tools and MCP servers |
| **A2A Agent** | Agent-to-Agent protocol for interoperability |
| **Sequential Agent** | Executes sub-agents in sequence |
| **Parallel Agent** | Executes sub-agents concurrently |
| **Loop Agent** | Iterative execution with max iterations |
| **Workflow Agent** | Custom graph-based workflows (LangGraph) |
| **Task Agent** | Structured task execution |

## Quick Start

```bash
# Clone the ecosystem
git clone https://github.com/grootme/ecosystem
cd ecosystem/services/ricco-ai

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install A2UI SDK
pip install -e ../../external/A2UI/agent_sdks/python/

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run database migrations
alembic upgrade head

# Start the service
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

## API Documentation

Once running, access:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Integration with RICCO ID

RICCO AI integrates with RICCO ID for:
- JWT token verification
- User profile retrieval
- Trust score validation
- KYC status checking

```python
from src.services.ricco_id_client import RiccoIDClient

client = RiccoIDClient(
    base_url="https://id.ricco.com",
    shared_secret="your-shared-secret"
)

# Verify user token
user_data = await client.verify_token(token)

# Get trust score
trust = await client.get_trust_score(user_id)
```

## A2UI Integration

Uses Google's A2UI SDK for dynamic UI generation:

```python
from src.services.a2ui_service import get_a2ui_service

a2ui = get_a2ui_service()

# Create chat interface
surface = a2ui.create_chat_ui("chat-1", "User Name")

# Create KYC form
kyc_form = a2ui.create_kyc_form("kyc-1", "individual")
```

## MCP Arsenal

50+ MCP tools available:

| Category | Tools |
|----------|-------|
| Filesystem | S3, GDrive, Local |
| Database | PostgreSQL, MongoDB, Redis |
| Web | Fetch, Search, Puppeteer |
| AI | OpenAI, OpenRouter, Ollama |
| Finance | Stripe, QvaPay, Binance |
| RICCO | ID, Commerce, Energy, Logistics |
| DevOps | GitHub, GitLab, Docker, Kubernetes |
| Documents | PDF, DOCX, XLSX |

## Project Structure

```
services/ricco-ai/
├── src/
│   ├── main.py              # FastAPI application
│   ├── config/              # Configuration
│   │   ├── settings.py      # RICCO settings
│   │   ├── database.py      # PostgreSQL
│   │   └── redis.py         # Redis cache
│   ├── api/                 # API routes (from evo-ai)
│   ├── services/
│   │   ├── adk/            # Agent Development Kit
│   │   ├── ricco_id_client.py  # RICCO ID integration
│   │   ├── a2ui_service.py     # A2UI SDK integration
│   │   ├── context_engine.py   # Context engineering
│   │   └── mcp_arsenal.py      # MCP tools
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic schemas
│   └── utils/               # Utilities
├── migrations/              # Alembic migrations
├── requirements.txt
├── .env.example
└── README.md
```

## Based On

- [evo-ai](https://github.com/EvolutionAPI/evo-ai) - Multi-agent orchestration
- [A2UI](https://github.com/google/A2UI) - Agent-to-User Interface SDK

## License

Apache License 2.0
