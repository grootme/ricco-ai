# Mem0 AI Memory System - Comprehensive Technical Research Report

## Executive Summary

Mem0 ("mem-zero") is a production-ready, scalable memory layer for AI agents and applications. It provides persistent, self-improving memory capabilities that enable personalized AI interactions. The system is designed to dynamically extract, consolidate, and retrieve salient information from conversations.

**Key Metrics (April 2026):**
- **LoCoMo Benchmark**: 91.6 (+20 points over previous algorithm)
- **LongMemEval**: 94.8 (+27 points, +53.6 on assistant memory recall)
- **BEAM (1M tokens)**: 64.1
- **BEAM (10M tokens)**: 48.6

---

## 1. Core Architecture

### 1.1 High-Level Architecture

Mem0 follows a **two-phase pipeline** architecture:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           MEM0 ARCHITECTURE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                   │
│  │   Messages   │───>│  Extraction  │───>│   Storage    │                   │
│  │  (Input)     │    │   Pipeline   │    │   Layer      │                   │
│  └──────────────┘    └──────────────┘    └──────────────┘                   │
│         │                   │                    │                          │
│         │                   v                    v                          │
│         │           ┌──────────────┐    ┌──────────────┐                   │
│         │           │   Entity     │    │   Vector     │                   │
│         │           │   Linking    │    │   Store      │                   │
│         │           └──────────────┘    └──────────────┘                   │
│         │                   │                    │                          │
│         │                   v                    v                          │
│         │           ┌──────────────┐    ┌──────────────┐                   │
│         │           │   Memory     │    │   Hybrid     │                   │
│         └──────────>│   Retrieval  │<───│   Search     │                   │
│                     └──────────────┘    └──────────────┘                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Core Components

1. **Extraction Pipeline**: LLM-powered fact extraction from conversations
2. **Entity Linking**: Connects related memories across sessions
3. **Vector Storage**: Pluggable vector database layer
4. **Hybrid Search**: Semantic + BM25 + Entity boosting
5. **Memory Manager**: Orchestrates add/update/delete operations

### 1.3 V3 Architecture (Current - April 2026)

The new "Token-Efficient Memory Algorithm" introduces:

| Feature | Description |
|---------|-------------|
| **Single-pass ADD-only extraction** | One LLM call, no UPDATE/DELETE operations |
| **Agent-generated facts** | First-class citizens with equal weight |
| **Entity linking** | Entities extracted, embedded, and linked across memories |
| **Multi-signal retrieval** | Semantic + BM25 keyword + entity matching in parallel |
| **Temporal Reasoning** | Time-aware retrieval for dated instances |

---

## 2. Memory Types

Mem0 supports multiple memory types inspired by cognitive science:

### 2.1 Memory Type Categories

| Type | Description | Storage | Use Case |
|------|-------------|---------|----------|
| **Episodic Memory** | Summaries of past interactions or completed tasks | Vector Store | Conversation history, task completion |
| **Semantic Memory** | Relationships between concepts for reasoning | Vector Store + Graph | Facts, preferences, entity relationships |
| **Procedural Memory** | Execution history and agent actions | SQLite | Agent workflows, step-by-step processes |
| **Working Memory** | Current session context | In-memory | Active conversation context |

### 2.2 Memory Structure

```python
# Core Memory Item Structure
class MemoryItem:
    id: str                    # UUID identifier
    memory: str                # The actual memory text
    hash: str                  # Content hash for deduplication
    created_at: datetime       # Creation timestamp
    updated_at: datetime       # Last update timestamp
    
    # Entity Context
    user_id: Optional[str]     # User identifier
    agent_id: Optional[str]    # Agent identifier  
    run_id: Optional[str]      # Session/run identifier
    
    # Additional Context
    metadata: Dict[str, Any]   # Custom metadata
    linked_memory_ids: List[str]  # Related memory IDs (for graph linking)
    entities: List[Tuple[str, str]]  # Extracted entities (type, text)
```

---

## 3. Extraction Algorithms

### 3.1 ADD-only Extraction (V3)

The V3 algorithm uses **single-pass, append-only extraction**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     ADD-ONLY EXTRACTION FLOW                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  INPUT:                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ • New Messages (user/assistant conversation)                        │    │
│  │ • Summary (narrative of user profile from prior conversations)      │    │
│  │ • Recently Extracted Memories (up to 20, for deduplication)          │    │
│  │ • Existing Memories (relevant memories from vector store)            │    │
│  │ • Last k Messages (up to 20, for reference resolution)               │    │
│  │ • Observation Date (temporal anchor for relative references)         │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  PROCESSING:                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ 1. Parse all messages (user AND assistant)                          │    │
│  │ 2. Extract facts, preferences, plans, relationships                  │    │
│  │ 3. Resolve temporal references (yesterday → specific date)          │    │
│  │ 4. Deduplicate against Recent/Existing Memories                      │    │
│  │ 5. Link to related existing memories                                 │    │
│  │ 6. Generate contextually rich, self-contained memories              │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│  OUTPUT:                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ {"memory": [                                                         │    │
│  │   {"id": "0", "text": "...", "attributed_to": "user",               │    │
│  │    "linked_memory_ids": ["uuid-of-related-memory"]},                │    │
│  │   {"id": "1", "text": "...", "attributed_to": "assistant"}          │    │
│  │ ]}                                                                   │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Extraction Prompt Structure

The `ADDITIVE_EXTRACTION_PROMPT` is the core extraction system prompt:

**Key Extraction Guidelines:**

1. **What to Extract from User Messages:**
   - Personal details, preferences, plans, relationships
   - Health/wellness, opinions, hobbies, emotional states
   - Entity attributes (breed, model, color, make, size)
   - Implicit preferences revealed through requests
   - Shared content and reference material
   - Firsts and milestones
   - Specific foods, meals, and who was present

2. **What to Extract from Assistant Messages:**
   - Specific recommendations given
   - Plans or schedules created for the user
   - Information researched or provided
   - Agreements reached during conversation

3. **Memory Quality Standards:**
   - **Contextually Rich**: "User has a dog named Poppy and their morning walks together are the highlight of their day"
   - **Self-Contained**: Replace pronouns with specific names
   - **Temporally Grounded**: Convert relative → absolute dates
   - **Numerically Precise**: Preserve exact quantities
   - **Proper Nouns Preserved**: Keep titles, names, brands exact

### 3.3 Entity Extraction

Mem0 extracts four types of entities using spaCy NLP:

| Entity Type | Description | Example |
|-------------|-------------|---------|
| **PROPER** | Capitalized multi-word sequences | "John Smith", "San Francisco" |
| **QUOTED** | Text in single or double quotes | "The Last Dance", "Inception" |
| **COMPOUND** | Multi-word noun phrases | "machine learning", "senior engineer" |
| **NOUN** | Single nouns from compound patterns | Specific technical terms |

```python
# Entity Extraction Process
def extract_entities(text: str) -> List[Tuple[str, str]]:
    """
    Extract named entities, quoted text, and noun compounds.
    Returns: List of (entity_type, entity_text) tuples
    """
    # Uses spaCy for NER
    # Filters generic heads and circumstantial modifiers
    # Strips generic endings from compounds
```

### 3.4 Memory Linking

When extracting new memories, the system links them to related existing memories:

**Linking Conditions:**
- Same entity/topic
- Updated preference
- Continuation of narrative
- Contradiction

```json
{
  "memory": [
    {
      "id": "0",
      "text": "User's dog Poppy had a vet checkup around March 14, 2025",
      "linked_memory_ids": ["a1b2c3d4-5678-9abc-def0-111111111111"]
    }
  ]
}
```

---

## 4. Consolidation Process

### 4.1 V2 Consolidation (Legacy - UPDATE/DELETE)

The older V2 system used a four-operation model:

| Operation | Description | When Used |
|-----------|-------------|-----------|
| **ADD** | Add new memory element | New information not in memory |
| **UPDATE** | Update existing element | Information changed/evolved |
| **DELETE** | Delete existing element | Contradictory information |
| **NONE** | No change | Already present or irrelevant |

### 4.2 V3 ADD-Only Model (Current)

The V3 algorithm **eliminates consolidation entirely**:

```
┌─────────────────────────────────────────────────────────────────┐
│                    V3 ADD-ONLY MODEL                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  OLD (V2):                    NEW (V3):                         │
│  ┌─────────────────┐          ┌─────────────────┐               │
│  │ Extract Facts   │          │ Extract Facts   │               │
│  │       ↓         │          │       ↓         │               │
│  │ Compare to      │          │ Add to Store    │               │
│  │ Existing        │          │       ↓         │               │
│  │       ↓         │          │ Entity Linking  │               │
│  │ ADD/UPDATE/     │          │       ↓         │               │
│  │ DELETE/NONE     │          │ Done            │               │
│  │       ↓         │          │                 │               │
│  │ Re-consolidate  │          │                 │               │
│  └─────────────────┘          └─────────────────┘               │
│                                                                 │
│  Benefits:                                                      │
│  • ~50% faster (single LLM call)                               │
│  • Full history preserved                                       │
│  • Retrieval handles relevance ranking                          │
│  • No information loss from consolidation errors               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 Storage Schema

**SQLite History Table:**
```sql
CREATE TABLE history (
    id           TEXT PRIMARY KEY,
    memory_id    TEXT,
    old_memory   TEXT,
    new_memory   TEXT,
    event        TEXT,           -- ADD, UPDATE, DELETE
    created_at   DATETIME,
    updated_at   DATETIME,
    is_deleted   INTEGER,
    actor_id     TEXT,
    role         TEXT
);
```

**SQLite Messages Table:**
```sql
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    session_scope TEXT,
    role TEXT,
    content TEXT,
    name TEXT,
    created_at DATETIME
);
```

---

## 5. Integration APIs

### 5.1 Python SDK

```python
from mem0 import Memory

# Initialize memory
memory = Memory()

# Add memories from conversation
messages = [
    {"role": "user", "content": "I'm John, a software engineer at Google"},
    {"role": "assistant", "content": "Nice to meet you, John!"}
]
result = memory.add(messages, user_id="john_123")

# Search memories
results = memory.search(
    query="What does John do?",
    filters={"user_id": "john_123"},
    top_k=3
)

# Get all memories
all_memories = memory.get_all(filters={"user_id": "john_123"})

# Update memory
memory.update(memory_id="abc123", data="Updated content")

# Delete memory
memory.delete(memory_id="abc123")
```

### 5.2 Node.js SDK

```javascript
import { Memory } from 'mem0ai';

const memory = new Memory();

// Add memories
const result = await memory.add(
    [{ role: 'user', content: 'I love hiking on weekends' }],
    { userId: 'user_123' }
);

// Search memories
const results = await memory.search(
    'What does user like to do?',
    { filters: { user_id: 'user_123' }, top_k: 5 }
);
```

### 5.3 REST API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/memories` | Create new memories |
| `GET` | `/memories` | Get all memories (with optional filters) |
| `GET` | `/memories/{id}` | Get specific memory |
| `PUT` | `/memories/{id}` | Update memory |
| `DELETE` | `/memories/{id}` | Delete memory |
| `DELETE` | `/memories` | Delete all memories (admin) |
| `POST` | `/search` | Search memories |
| `GET` | `/memories/{id}/history` | Get memory history |

### 5.4 REST API Examples

**Create Memory:**
```bash
curl -X POST http://localhost:3000/memories \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "I prefer dark mode in all my apps"}
    ],
    "user_id": "user_123"
  }'
```

**Search Memories:**
```bash
curl -X POST http://localhost:3000/search \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are user preferences?",
    "filters": {"user_id": "user_123"},
    "top_k": 5
  }'
```

### 5.5 CLI

```bash
# Install CLI
npm install -g @mem0/cli

# Initialize
mem0 init

# Add memory
mem0 add "Prefers dark mode and vim keybindings" --user-id alice

# Search
mem0 search "What does Alice prefer?" --user-id alice
```

---

## 6. Vector Database Support

### 6.1 Supported Vector Stores

| Provider | Class | Best For |
|----------|-------|----------|
| **Qdrant** | `mem0.vector_stores.qdrant.Qdrant` | Open-source, high-performance |
| **Pinecone** | `mem0.vector_stores.pinecone.PineconeDB` | Managed, enterprise |
| **Chroma** | `mem0.vector_stores.chroma.ChromaDB` | Local development |
| **PGVector** | `mem0.vector_stores.pgvector.PGVector` | PostgreSQL integration |
| **Milvus** | `mem0.vector_stores.milvus.MilvusDB` | Large-scale production |
| **Weaviate** | `mem0.vector_stores.weaviate.Weaviate` | GraphQL-based |
| **Redis** | `mem0.vector_stores.redis.RedisDB` | Caching + vector search |
| **MongoDB** | `mem0.vector_stores.mongodb.MongoDB` | Document store integration |
| **Azure AI Search** | `mem0.vector_stores.azure_ai_search.AzureAISearch` | Azure ecosystem |
| **OpenSearch** | `mem0.vector_stores.opensearch.OpenSearchDB` | AWS ecosystem |
| **FAISS** | `mem0.vector_stores.faiss.FAISS` | Local, no external dependencies |
| **Supabase** | `mem0.vector_stores.supabase.Supabase` | BaaS platform |
| **Upstash Vector** | `mem0.vector_stores.upstash_vector.UpstashVector` | Serverless |
| **Elasticsearch** | `mem0.vector_stores.elasticsearch.ElasticsearchDB` | Search platform |
| **Vertex AI** | `mem0.vector_stores.vertex_ai_vector_search.GoogleMatchingEngine` | GCP ecosystem |

### 6.2 Qdrant Configuration Example

```python
from mem0 import Memory

config = {
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "host": "localhost",
            "port": 6333,
            "collection_name": "memories"
        }
    },
    "embedder": {
        "provider": "openai",
        "config": {"model": "text-embedding-3-small"}
    },
    "llm": {
        "provider": "openai",
        "config": {"model": "gpt-4o-mini"}
    }
}

memory = Memory.from_config(config)
```

### 6.3 Supported Embedders

| Provider | Best For |
|----------|----------|
| **OpenAI** | Default, text-embedding-3-small |
| **HuggingFace** | Open-source models |
| **Ollama** | Local inference |
| **Azure OpenAI** | Enterprise Azure |
| **Gemini** | Google Cloud |
| **VertexAI** | GCP ecosystem |
| **AWS Bedrock** | AWS ecosystem |
| **FastEmbed** | Lightweight, fast |

**Recommended for Hybrid Search:**
- Qwen 600M or comparable embedding model
- Minimum: text-embedding-3-small

### 6.4 Supported LLMs

| Provider | Models |
|----------|--------|
| **OpenAI** | GPT-4o, GPT-4o-mini (default), GPT-5-mini |
| **Anthropic** | Claude models |
| **Azure OpenAI** | Azure-hosted OpenAI models |
| **Gemini** | Google Gemini models |
| **Groq** | Fast inference |
| **Ollama** | Local models |
| **DeepSeek** | Cost-effective |
| **Together** | Open-source models |
| **AWS Bedrock** | AWS-hosted models |
| **LiteLLM** | Universal LLM proxy |

---

## 7. Key Features

### 7.1 Hybrid Search

Mem0 combines multiple search signals:

```
Combined Score = (Semantic + BM25 + Entity_Boost) / Max_Possible

Where:
- Semantic: Vector similarity score
- BM25: Keyword matching score (normalized to [0,1])
- Entity_Boost: Entity linking boost (weight: 0.5)
- Max_Possible: 1.0 (semantic) + 1.0 (BM25) + 0.5 (entity)
```

**BM25 Normalization:**
```python
def normalize_bm25(raw_score: float, midpoint: float, steepness: float) -> float:
    """Normalize BM25 score to [0, 1] using logistic sigmoid."""
    return 1.0 / (1.0 + math.exp(-steepness * (raw_score - midpoint)))

# Query-length-adaptive parameters
if num_terms <= 3:
    midpoint, steepness = 5.0, 0.7
elif num_terms <= 6:
    midpoint, steepness = 7.0, 0.6
elif num_terms <= 9:
    midpoint, steepness = 9.0, 0.5
```

### 7.2 Temporal Reasoning

**Time Reference Resolution:**
- "yesterday" → day before Observation Date
- "last week" → week preceding Observation Date
- "next month" → month following Observation Date
- "recently" → shortly before Observation Date

**Key Principle:** Always ground relative references to specific dates for meaningful long-term retrieval.

### 7.3 Entity Resolution

```python
# Entity linking workflow
def link_entities(new_memory, existing_memories):
    """
    1. Extract entities from new memory using spaCy
    2. Embed entities using same embedder
    3. Search for matching entities in existing memories
    4. Add matched memory IDs to linked_memory_ids
    """
    entities = extract_entities(new_memory.text)
    entity_embeddings = embed_entities(entities)
    matches = search_entities(entity_embeddings, existing_memories)
    new_memory.linked_memory_ids = [m.id for m in matches]
```

### 7.4 Memory Importance & Deduplication

**Deduplication Process:**
1. **Recent Memory Check**: Compare against last 20 extracted memories
2. **Existing Memory Check**: Vector search for semantically similar memories
3. **Skip if Equivalent**: If new fact matches existing (semantic equivalence), skip extraction
4. **Link if Related**: If same entity/topic but different event, extract and link

### 7.5 Memory Expiration

Mem0 does not implement automatic memory expiration. Instead:
- All memories are preserved (ADD-only model)
- Relevance is determined at retrieval time
- Temporal reasoning helps surface current/relevant memories

---

## 8. Self-Hosted Deployment

### 8.1 Docker Compose

```bash
# Quick start with bootstrap
cd server && make bootstrap

# Manual setup
cd server && docker compose up -d
# Access at http://localhost:3000
```

### 8.2 Configuration

```python
DEFAULT_CONFIG = {
    "version": "v1.1",
    "vector_store": {
        "provider": "pgvector",
        "config": {
            "host": "localhost",
            "port": 5432,
            "dbname": "memories",
            "user": "postgres",
            "password": "password",
            "collection_name": "memories"
        }
    },
    "llm": {
        "provider": "openai",
        "config": {
            "api_key": "sk-...",
            "temperature": 0.2,
            "model": "gpt-4o-mini"
        }
    },
    "embedder": {
        "provider": "openai",
        "config": {
            "api_key": "sk-...",
            "model": "text-embedding-3-small"
        }
    },
    "history_db_path": "/app/history/history.db"
}
```

### 8.3 Authentication

```bash
# Environment variables
ADMIN_API_KEY=<long-random-value>  # Admin key
JWT_SECRET=$(openssl rand -base64 48)  # JWT secret
AUTH_DISABLED=true  # For local development only
```

---

## 9. Code Examples

### 9.1 Full Integration Example

```python
from openai import OpenAI
from mem0 import Memory

openai_client = OpenAI()
memory = Memory()

def chat_with_memories(message: str, user_id: str = "default_user") -> str:
    # 1. Retrieve relevant memories
    relevant_memories = memory.search(
        query=message,
        filters={"user_id": user_id},
        top_k=3
    )
    memories_str = "\n".join(
        f"- {entry['memory']}" 
        for entry in relevant_memories["results"]
    )

    # 2. Generate response with memory context
    system_prompt = f"""You are a helpful AI. Answer based on query and memories.
    
User Memories:
{memories_str}"""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message}
    ]
    
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages
    )
    assistant_response = response.choices[0].message.content

    # 3. Create new memories from conversation
    messages.append({"role": "assistant", "content": assistant_response})
    memory.add(messages, user_id=user_id)

    return assistant_response
```

### 9.2 Hybrid Search with Explain

```python
results = memory.search(
    query="What restaurants does user like?",
    filters={"user_id": "user_123"},
    top_k=5,
    threshold=0.7,
    explain=True  # Returns score breakdown
)

# Result with explain:
# {
#   "results": [{
#     "id": "abc123",
#     "memory": "User enjoys Italian cuisine at Osteria Francescana",
#     "score": 0.85,
#     "score_details": {
#       "semantic_score": 0.78,
#       "bm25_score": 0.65,
#       "entity_boost": 0.42,
#       "raw_score": 1.85,
#       "max_possible_score": 2.5,
#       "final_score": 0.85
#     }
#   }]
# }
```

### 9.3 Custom Instructions for Extraction

```python
memory.add(
    messages=[{"role": "user", "content": "..."}],
    user_id="user_123",
    custom_instructions="""Focus on extracting:
1. Dietary restrictions and food allergies
2. Restaurant preferences
3. Cooking habits and kitchen equipment"""
)
```

---

## 10. Key Takeaways for Implementation

### Phase 1: Extraction & Consolidation

1. **Use ADD-only extraction** - Single LLM call, no UPDATE/DELETE
2. **Extract from both user and assistant messages**
3. **Implement contextually rich extraction** - Not atomic facts
4. **Ground temporal references** - Convert relative to absolute dates
5. **Preserve proper nouns exactly** - Critical for recall

### Phase 2: Storage & Retrieval

1. **Use hybrid search** - Semantic + BM25 + Entity boosting
2. **Implement entity extraction** - spaCy for NER
3. **Store entity embeddings separately** - For linking
4. **Track memory history** - SQLite for audit trail

### Phase 3: Production Considerations

1. **Choose vector DB based on scale** - Qdrant for open-source, Pinecone for managed
2. **Configure appropriate embedder** - text-embedding-3-small minimum
3. **Set up authentication** - JWT + API keys
4. **Implement rate limiting** - Protect extraction endpoints

---

## References

- **Official Documentation**: https://docs.mem0.ai
- **GitHub Repository**: https://github.com/mem0ai/mem0
- **Research Paper**: arXiv:2504.19413 - "Mem0: Building Production-Ready AI Agents with Scalable Long-Term Memory"
- **Benchmark Results**: https://mem0.ai/research
- **Migration Guide**: https://docs.mem0.ai/migration/oss-v2-to-v3
