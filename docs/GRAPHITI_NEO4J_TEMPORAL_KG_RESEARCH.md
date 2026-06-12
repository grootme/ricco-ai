# Graphiti & Neo4j Temporal Knowledge Graph Research Report

## Executive Summary

This research report provides a comprehensive technical analysis of **Graphiti** (by Zep AI) and **Neo4j** for implementing temporal knowledge graphs in AI agent memory systems. The findings are directly applicable to **Phase 2 implementation** of adding temporal knowledge graph capabilities.

---

## 1. Graphiti Architecture

### 1.1 Overview

Graphiti is an open-source framework for building **temporal context graphs** specifically designed for AI agents. Unlike static knowledge graphs, Graphiti's context graphs track how facts change over time, maintain provenance to source data, and support both prescribed and learned ontology.

**Key Repository**: `getzep/graphiti` on GitHub (27.3k stars, 2.7k forks)

### 1.2 Hierarchical Graph Structure

Graphiti implements a **three-tier hierarchical knowledge graph**:

```
𝒢 = (𝒩, ℰ, φ)
```

Where:
- **𝒩** = Nodes (entities, episodes, communities)
- **ℰ** = Edges (relationships, provenance links)
- **φ** = Incidence function mapping edges to node pairs

#### Tier 1: Episode Subgraph (𝒢ₑ)
- **Episodes**: Raw input data (messages, text, JSON)
- Serve as **non-lossy data store** from which semantic entities are extracted
- Each episode includes:
  - Reference timestamp (`t_ref`) indicating when the message was sent
  - Content (text or structured data)
  - Actor information

#### Tier 2: Semantic Entity Subgraph (𝒢ₛ)
- **Entity Nodes**: People, products, policies, concepts with evolving summaries
- **Semantic Edges**: Relationships between entities with temporal validity windows
- Each edge contains:
  - The fact/relationship
  - `t_valid`: When the fact became true
  - `t_invalid`: When the fact was superseded (if applicable)

#### Tier 3: Community Subgraph (𝒢꜀)
- **Community Nodes**: Clusters of strongly connected entities
- High-level summarizations representing interconnected views
- Built using **Label Propagation algorithm** (vs. Leiden in GraphRAG)
- Enables efficient retrieval of related entity groups

### 1.3 Bi-Temporal Model

Graphiti implements a **novel bi-temporal tracking system**:

| Timeline | Purpose |
|----------|---------|
| **T** (Event Timeline) | Chronological ordering of when events actually occurred |
| **T'** (Transaction Timeline) | When data was ingested into the system |

**Four Key Timestamps per Edge**:
- `t_valid`: When the fact became true
- `t_invalid`: When the fact was invalidated
- `t'_created`: When the fact was created in the system
- `t'_expired`: When the fact was invalidated in the system

### 1.4 Data Flow Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                    EPISODE INGESTION                            │
├─────────────────────────────────────────────────────────────────┤
│  1. Episode Input (Message/Text/JSON)                          │
│     └── Reference timestamp t_ref                               │
│                                                                 │
│  2. Entity Extraction (LLM-powered)                            │
│     ├── Named Entity Recognition                               │
│     ├── Reflection technique for hallucination reduction       │
│     └── Entity summary generation                              │
│                                                                 │
│  3. Entity Resolution                                           │
│     ├── Embedding-based similarity search (1024-dim)           │
│     ├── Full-text search on names/summaries                    │
│     └── LLM-based deduplication                                │
│                                                                 │
│  4. Fact Extraction                                             │
│     ├── Relationship extraction between entities               │
│     ├── Temporal information extraction                        │
│     └── Edge deduplication                                     │
│                                                                 │
│  5. Temporal Processing                                         │
│     ├── Absolute/relative timestamp parsing                    │
│     ├── Conflict detection with existing edges                 │
│     └── Edge invalidation (set t_invalid)                      │
│                                                                 │
│  6. Community Update                                            │
│     ├── Dynamic label propagation                              │
│     └── Community summary refresh                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Neo4j Integration

### 2.1 Why Neo4j for Agent Memory

Neo4j provides the ideal backend for temporal knowledge graphs because:

1. **Native Graph Structure**: Direct mapping to entity-relationship model
2. **Vector + BM25 Indexes**: Neo4j 5.26+ supports both index types natively
3. **Cypher Query Language**: Expressive temporal and graph traversal queries
4. **ACID Transactions**: Ensures consistency for memory updates
5. **Scalability**: Handles enterprise-scale knowledge graphs

### 2.2 Graphiti Neo4j Driver Setup

```python
from graphiti_core import Graphiti
from graphiti_core.driver.neo4j_driver import Neo4jDriver

# Standard connection
graphiti = Graphiti(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="password"
)

# Custom database name
driver = Neo4jDriver(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="password",
    database="my_custom_database"  # Custom database name
)

graphiti = Graphiti(graph_driver=driver)
```

### 2.3 Neo4j Schema for Temporal KG

Graphiti creates the following node/relationship types in Neo4j:

```cypher
// Node Labels
(:Entity {
    uuid: STRING,
    name: STRING,
    summary: STRING,
    created_at: DATETIME,
    embedding: LIST<FLOAT>
})

(:Episode {
    uuid: STRING,
    content: STRING,
    source_description: STRING,
    timestamp: DATETIME,
    valid_at: DATETIME
})

(:Community {
    uuid: STRING,
    name: STRING,
    summary: STRING,
    embedding: LIST<FLOAT>
})

// Relationship Types
[:MENTIONS {             // Episode -> Entity
    created_at: DATETIME
}]

[:RELATES_TO {          // Entity -> Entity
    uuid: STRING,
    fact: STRING,
    valid_at: DATETIME,
    invalid_at: DATETIME,  // NULL if still valid
    created_at: DATETIME,
    expired_at: DATETIME,  // Transaction timeline
    embedding: LIST<FLOAT>
}]

[:MEMBER_OF {           // Entity -> Community
    created_at: DATETIME
}]
```

### 2.4 Index Creation

```cypher
// Vector index for semantic search
CREATE VECTOR INDEX entity_embedding_index
FOR (e:Entity) ON e.embedding
OPTIONS {indexConfig: {
    `vector.dimensions`: 1024,
    `vector.similarity_function`: 'cosine'
}}

CREATE VECTOR INDEX edge_embedding_index
FOR ()-[r:RELATES_TO]-() ON r.embedding
OPTIONS {indexConfig: {
    `vector.dimensions`: 1024,
    `vector.similarity_function`: 'cosine'
}}

// Full-text index for BM25 search
CREATE FULLTEXT INDEX entity_name_fulltext
FOR (e:Entity) ON EACH [e.name, e.summary]

CREATE FULLTEXT INDEX edge_fact_fulltext
FOR ()-[r:RELATES_TO]-() ON r.fact
```

---

## 3. Temporal Graph Features

### 3.1 Time-Based Relationships

Graphiti's temporal model enables powerful time-aware queries:

#### Validity Window Tracking
Every edge has a validity window (`t_valid`, `t_invalid`):
- **Current facts**: `t_invalid IS NULL`
- **Historical facts**: `t_invalid IS NOT NULL`
- **Time-travel queries**: Query state at any point in time

#### Automatic Fact Invalidation
When new information contradicts existing facts:
1. LLM compares new edge against semantically related existing edges
2. If contradiction found with temporal overlap:
   - Set `t_invalid` of old edge to `t_valid` of new edge
3. Old edge is **invalidated, not deleted** (preserves history)

### 3.2 Temporal Query Examples

```cypher
// Get all currently valid relationships for an entity
MATCH (e:Entity {name: $entity_name})-[r:RELATES_TO]-(related)
WHERE r.invalid_at IS NULL
RETURN e.name, r.fact, related.name, r.valid_at

// Get entity state at a specific point in time
MATCH (e:Entity {name: $entity_name})-[r:RELATES_TO]-(related)
WHERE r.valid_at <= $query_time AND 
      (r.invalid_at IS NULL OR r.invalid_at > $query_time)
RETURN e.name, r.fact, related.name

// Find all facts that changed in a time range
MATCH ()-[r:RELATES_TO]->()
WHERE r.valid_at >= $start_time AND r.valid_at <= $end_time
RETURN r.fact, r.valid_at, r.invalid_at
ORDER BY r.valid_at

// Track entity evolution over time
MATCH (e:Entity {name: $entity_name})
MATCH (e)-[r:RELATES_TO]-(related)
RETURN r.fact, r.valid_at, r.invalid_at
ORDER BY r.valid_at
```

### 3.3 Versioning & Evolution

| Feature | Implementation |
|---------|----------------|
| **Entity Evolution** | Entity summaries are updated as new information arrives |
| **Fact Versioning** | Old facts invalidated with `t_invalid`, new facts created |
| **Full History** | All edges preserved, enabling historical queries |
| **Provenance** | Every fact traces back to source episodes |

---

## 4. Entity-Relationship Modeling

### 4.1 Custom Entity Types (Ontology)

Graphiti supports **prescribed ontology** via Pydantic models:

```python
from pydantic import BaseModel, Field

class Customer(BaseModel):
    """A customer of the service"""
    name: str | None = Field(..., description="Customer name")
    email: str | None = Field(..., description="Email address")
    subscription_tier: str | None = Field(..., description="Subscription level")

class Product(BaseModel):
    """A product in the catalog"""
    name: str | None = Field(..., description="Product name")
    category: str | None = Field(..., description="Product category")
    price: float | None = Field(..., description="Price in USD")

class Order(BaseModel):
    """A customer order"""
    order_id: str | None = Field(..., description="Order ID")
    status: str | None = Field(..., description="Order status")
    total: float | None = Field(..., description="Order total")
```

### 4.2 Entity Resolution Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                 ENTITY RESOLUTION FLOW                       │
├─────────────────────────────────────────────────────────────┤
│  1. Extract entities from episode using LLM                 │
│                                                             │
│  2. Generate 1024-dim embedding for entity name            │
│                                                             │
│  3. Hybrid search for candidate matches:                   │
│     ├── Vector similarity search (cosine)                  │
│     └── Full-text search (BM25) on name + summary          │
│                                                             │
│  4. LLM-based deduplication decision:                      │
│     ├── If duplicate: Update existing entity               │
│     └── If new: Create new entity                          │
│                                                             │
│  5. Update entity summary with new context                 │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 Relationship Extraction

Relationships are extracted as triplets with temporal metadata:

```
(Entity_A) --[RELATES_TO {fact: "...", valid_at: T, invalid_at: NULL}]--> (Entity_B)
```

**Key extraction steps**:
1. LLM identifies relationships between extracted entities
2. Temporal context from episode used for `valid_at` extraction
3. Supports **hyper-edges** (same fact between multiple entity pairs)
4. Edge deduplication constrained to same entity pair

---

## 5. Query Capabilities

### 5.1 Hybrid Search Architecture

Graphiti implements **three complementary search methods**:

| Method | Function | Use Case |
|--------|----------|----------|
| **Semantic Search** (φ_cos) | Vector similarity on embeddings | Conceptual similarity |
| **Full-Text Search** (φ_bm25) | BM25 keyword matching | Exact term matching |
| **Graph Traversal** (φ_bfs) | Breadth-first search | Contextual proximity |

### 5.2 Search Implementation

```python
# The search function: φ: S → ℰₛⁿ × 𝒩ₛⁿ × 𝒩꜀ⁿ
# Returns: (edges, entities, communities)

async def search(query: str, limit: int = 10):
    results = await graphiti.search(query, num_results=limit)
    
    return {
        'edges': results.edges,      # Facts with temporal info
        'nodes': results.nodes,      # Entity summaries
        'communities': results.communities  # Community summaries
    }
```

### 5.3 Reranking Strategies

```python
# 1. Reciprocal Rank Fusion (RRF)
# Combines rankings from multiple search methods

# 2. Maximal Marginal Relevance (MMR)
# Balances relevance with diversity

# 3. Episode Mentions Reranker
# Prioritizes frequently mentioned entities/facts

# 4. Node Distance Reranker
# Reorders based on graph distance from centroid

# 5. Cross-Encoder Reranker (most sophisticated)
# LLM-based relevance scoring
```

### 5.4 Cypher Query Patterns for Memory Retrieval

```cypher
// 1. Semantic search for entities
CALL db.index.vector.queryNodes('entity_embedding_index', $limit, $query_embedding)
YIELD node, score
MATCH (node)-[r:RELATES_TO]-(related)
WHERE r.invalid_at IS NULL
RETURN node.name, node.summary, r.fact, related.name, score
ORDER BY score DESC

// 2. Full-text search for facts
CALL db.index.fulltext.queryRelationships('edge_fact_fulltext', $query)
YIELD relationship, score
WHERE relationship.invalid_at IS NULL
RETURN relationship.fact, relationship.valid_at, score

// 3. Graph traversal from seed entities
MATCH (seed:Entity) WHERE seed.uuid IN $seed_uuids
MATCH (seed)-[r:RELATES_TO*1..3]-(related)
WHERE ALL(e IN r WHERE e.invalid_at IS NULL)
RETURN DISTINCT related.name, related.summary

// 4. Community-based retrieval
MATCH (c:Community)
CALL db.index.vector.queryNodes('community_embedding_index', 5, $query_embedding)
YIELD node, score
WHERE node = c
MATCH (c)<-[:MEMBER_OF]-(e:Entity)
RETURN c.summary as community_summary, collect(e.name) as members
```

### 5.5 Context Construction

The final step transforms retrieved nodes/edges into LLM context:

```
FACTS and ENTITIES represent relevant context to the current conversation.

FACTS:
- FACT (Date range: valid_at - invalid_at)
- Kendra loves Adidas shoes (as of March 2026)

ENTITIES:
- ENTITY_NAME: entity summary
- Kendra: A customer interested in athletic footwear
```

---

## 6. Integration Patterns with LLM Agents

### 6.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI AGENT ARCHITECTURE                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐     ┌─────────────────────────────────────┐   │
│  │   LLM       │────▶│           ZEP / GRAPHITI            │   │
│  │  (GPT-4o)   │     │  ┌─────────────────────────────┐   │   │
│  └─────────────┘     │  │     Neo4j Graph Database    │   │   │
│        │             │  │  ┌───────────────────────┐  │   │   │
│        │             │  │  │   Episode Subgraph    │  │   │   │
│        ▼             │  │  ├───────────────────────┤  │   │   │
│  ┌─────────────┐     │  │  │   Entity Subgraph     │  │   │   │
│  │   Agent     │◀────│  │  ├───────────────────────┤  │   │   │
│  │   Memory    │     │  │  │   Community Subgraph  │  │   │   │
│  └─────────────┘     │  │  └───────────────────────┘  │   │   │
│                      │  └─────────────────────────────┘   │   │
│                      └─────────────────────────────────────┘   │
│                                    │                            │
│                                    ▼                            │
│                      ┌─────────────────────────────────────┐   │
│                      │         HYBRID SEARCH               │   │
│                      │  ┌─────────┬─────────┬─────────┐   │   │
│                      │  │ Vector  │  BM25   │  BFS    │   │   │
│                      │  └─────────┴─────────┴─────────┘   │   │
│                      │              │                     │   │
│                      │              ▼                     │   │
│                      │        RERANKER                    │   │
│                      └─────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 LangChain/LangGraph Integration

```python
from langchain_core.tools import tool
from graphiti_core import Graphiti

# Initialize Graphiti
graphiti = Graphiti(uri="bolt://localhost:7687", user="neo4j", password="password")

@tool
async def search_memory(query: str) -> str:
    """Search the agent's temporal knowledge graph for relevant context."""
    results = await graphiti.search(query, num_results=20)
    
    context_parts = []
    
    # Add facts with temporal info
    for edge in results.edges:
        time_info = f"({edge.valid_at} - {edge.invalid_at or 'present'})"
        context_parts.append(f"FACT: {edge.fact} {time_info}")
    
    # Add entity summaries
    for node in results.nodes:
        context_parts.append(f"ENTITY {node.name}: {node.summary}")
    
    return "\n".join(context_parts)

@tool
async def add_memory(content: str, timestamp: datetime = None) -> str:
    """Add a new episode to the agent's memory."""
    await graphiti.add_episode(
        name=f"memory_{datetime.now().isoformat()}",
        content=content,
        source_description="User interaction",
        reference_time=timestamp or datetime.now()
    )
    return "Memory added successfully"

# Use in LangGraph agent
from langgraph.prebuilt import create_react_agent

agent = create_react_agent(
    model="gpt-4o-mini",
    tools=[search_memory, add_memory]
)
```

### 6.3 MCP Server Integration

Graphiti provides an **MCP (Model Context Protocol) server** for direct integration with AI assistants:

```python
# MCP Server enables Claude, Cursor, and other MCP clients
# to interact with Graphiti's context graph capabilities

# Key MCP capabilities:
# - Episode management (add, retrieve, delete)
# - Entity management and relationship handling
# - Semantic and hybrid search capabilities
# - Group management for organizing related data
# - Graph maintenance operations
```

### 6.4 REST API Service

Graphiti includes a **FastAPI-based REST service**:

```python
# server/ directory contains the API service
# Endpoints include:
# - POST /episodes - Add new episodes
# - GET /search - Hybrid search
# - GET /entities - Entity management
# - GET /edges - Relationship queries
# - POST /communities - Community operations
```

---

## 7. Performance Benchmarks

### 7.1 Deep Memory Retrieval (DMR)

| Memory Model | Model | Score |
|--------------|-------|-------|
| Recursive Summarization | gpt-4-turbo | 35.3% |
| Conversation Summaries | gpt-4-turbo | 78.6% |
| MemGPT | gpt-4-turbo | 93.4% |
| Full-conversation | gpt-4-turbo | 94.4% |
| **Zep (Graphiti)** | gpt-4-turbo | **94.8%** |
| **Zep (Graphiti)** | gpt-4o-mini | **98.2%** |

### 7.2 LongMemEval (LME)

Zep achieves:
- **Up to 18.5% accuracy improvement** over baselines
- **90% reduction in response latency**
- Average context: 115,000 tokens

### 7.3 Query Performance

- **P95 latency: 300ms** for retrieval
- Near-constant time access via vector + BM25 indexes
- Sub-second latency suitable for real-time interactions

---

## 8. Phase 2 Implementation Recommendations

### 8.1 Recommended Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│              PHASE 2: TEMPORAL KG IMPLEMENTATION                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Database Layer                                              │
│     ├── Neo4j 5.26+ (primary graph store)                      │
│     ├── Vector indexes (1024-dim, cosine similarity)           │
│     └── Full-text indexes (BM25)                               │
│                                                                 │
│  2. Graphiti Core Layer                                         │
│     ├── Episode ingestion pipeline                             │
│     ├── Entity extraction & resolution                         │
│     ├── Temporal fact management                               │
│     └── Community detection                                    │
│                                                                 │
│  3. LLM Integration                                             │
│     ├── OpenAI GPT-4o-mini (extraction)                        │
│     ├── BGE-m3 embeddings (1024-dim)                           │
│     └── Cross-encoder reranking                                │
│                                                                 │
│  4. API Layer                                                   │
│     ├── FastAPI endpoints                                      │
│     ├── MCP server for agent integration                       │
│     └── WebSocket for real-time updates                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 8.2 Key Implementation Steps

1. **Install Dependencies**
   ```bash
   pip install graphiti-core
   # Or with FalkorDB alternative:
   pip install graphiti-core[falkordb]
   ```

2. **Initialize Graph Schema**
   ```python
   await graphiti.build_indices_and_constraints()
   ```

3. **Define Custom Entity Types**
   ```python
   class UserEntity(BaseModel):
       name: str
       preferences: dict
       interaction_history: list
   ```

4. **Implement Episode Ingestion**
   ```python
   await graphiti.add_episode(
       name="conversation_123",
       content=message_content,
       source_description="User conversation",
       reference_time=datetime.now()
   )
   ```

5. **Implement Hybrid Search**
   ```python
   results = await graphiti.search(
       query=user_query,
       num_results=20,
       search_type="hybrid"
   )
   ```

### 8.3 Migration from Current System

| Current Component | Temporal KG Replacement |
|-------------------|------------------------|
| Vector DB only | Neo4j with vector + graph |
| Static embeddings | Dynamic entity embeddings |
| No relationships | Explicit relationship edges |
| No time tracking | Bi-temporal model |
| No provenance | Episode-to-entity traceability |

---

## 9. Alternative Backends

Graphiti supports multiple graph backends:

| Backend | Status | Use Case |
|---------|--------|----------|
| **Neo4j** | ✅ Recommended | Production, enterprise |
| **FalkorDB** | ✅ Supported | Redis-based, simpler setup |
| **Amazon Neptune** | ✅ Supported | AWS native, serverless |
| **Kuzu** | ⚠️ Deprecated | Embedded (no longer maintained) |

---

## 10. Key Takeaways

1. **Temporal Knowledge Graphs** are essential for AI agents that need to track evolving information
2. **Graphiti's bi-temporal model** enables both current state queries and historical analysis
3. **Neo4j provides the ideal backend** with native vector + full-text indexes
4. **Hybrid search** (semantic + keyword + graph traversal) achieves optimal retrieval
5. **MCP integration** enables seamless agent connectivity
6. **Sub-300ms latency** makes it suitable for real-time applications

---

## References

1. [Graphiti GitHub Repository](https://github.com/getzep/graphiti)
2. [Zep: A Temporal Knowledge Graph Architecture for Agent Memory (arXiv:2501.13956)](https://arxiv.org/html/2501.13956v1)
3. [Neo4j Developer Blog: Graphiti Knowledge Graph Memory](https://neo4j.com/blog/developer/graphiti-knowledge-graph-memory)
4. [Zep Blog: Graphiti Knowledge Graphs for Agents](https://blog.getzep.com/graphiti-knowledge-graphs-for-agents)
5. [Neo4j Labs: agent-memory](https://github.com/neo4j-labs/agent-memory)

---

*Report generated: 2025*
*Focus: Phase 2 Implementation - Temporal Knowledge Graphs via Neo4j (Graphiti style)*
