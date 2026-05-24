# RAG Blueprint Skill

## Overview
NVIDIA RAG (Retrieval-Augmented Generation) Blueprint integration for building intelligent document retrieval and question-answering systems with vector search, hybrid retrieval, and citation support.

## Description
This skill provides tools for implementing production-ready RAG systems with multiple retrieval strategies, document processing pipelines, and answer generation with source attribution. It supports:

- **Dense Retrieval**: Vector similarity search using embeddings
- **Sparse Retrieval**: Keyword-based BM25 search
- **Hybrid Search**: Combining dense and sparse methods
- **Reranking**: Post-retrieval relevance improvement
- **Multi-hop RAG**: Iterative retrieval for complex queries

## Tools (15)

### rag_init
Initialize a RAG system with configuration.

**Parameters:**
- `system_name` (required): Name for the RAG system
- `vector_store` (required): 'milvus', 'qdrant', 'pinecone', or 'chroma'
- `embedding_model` (optional): Embedding model to use (default: nvidia/nv-embed)
- `llm_model` (optional): LLM for generation (default: openrouter/free)

### rag_ingest_documents
Ingest documents into the RAG system.

**Parameters:**
- `documents` (required): List of document paths or content
- `chunk_size` (optional): Chunk size in tokens (default: 512)
- `chunk_overlap` (optional): Overlap between chunks (default: 50)
- `metadata` (optional): Additional metadata for all documents

### rag_ingest_url
Ingest content from URL.

**Parameters:**
- `url` (required): URL to scrape and ingest
- `selector` (optional): CSS selector for content extraction
- `chunk_size` (optional): Chunk size for processing
- `metadata` (optional): Additional metadata

### rag_ingest_pdf
Ingest PDF documents with OCR support.

**Parameters:**
- `pdf_path` (required): Path to PDF file
- `ocr_enabled` (optional): Enable OCR for scanned documents
- `extract_images` (optional): Extract and describe images
- `extract_tables` (optional): Extract and format tables

### rag_create_collection
Create a new collection/index.

**Parameters:**
- `collection_name` (required): Name for the collection
- `description` (optional): Collection description
- `schema` (optional): Custom schema for metadata fields
- `replication_factor` (optional): Replication factor for distributed stores

### rag_search
Perform retrieval search.

**Parameters:**
- `query` (required): Search query
- `collection` (optional): Collection to search (default: all)
- `top_k` (optional): Number of results (default: 10)
- `search_type` (optional): 'dense', 'sparse', or 'hybrid'
- `filters` (optional): Metadata filters
- `rerank` (optional): Enable reranking (default: true)

### rag_hybrid_search
Perform hybrid search combining dense and sparse.

**Parameters:**
- `query` (required): Search query
- `dense_weight` (optional): Weight for dense results (default: 0.7)
- `sparse_weight` (optional): Weight for sparse results (default: 0.3)
- `top_k` (optional): Number of results
- `filters` (optional): Metadata filters

### rag_multi_hop_search
Perform multi-hop iterative retrieval.

**Parameters:**
- `query` (required): Initial query
- `max_hops` (optional): Maximum iterations (default: 3)
- `top_k_per_hop` (optional): Results per hop (default: 5)
- `relevance_threshold` (optional): Minimum relevance score

### rag_generate_answer
Generate answer from retrieved context.

**Parameters:**
- `query` (required): User question
- `context` (required): Retrieved context chunks
- `citation_style` (optional): 'inline', 'footnote', or 'endnote'
- `max_tokens` (optional): Maximum answer length
- `include_confidence` (optional): Include confidence score

### rag_query
End-to-end RAG query (retrieve + generate).

**Parameters:**
- `query` (required): User question
- `collection` (optional): Collection to query
- `top_k` (optional): Number of context chunks
- `search_type` (optional): 'dense', 'sparse', or 'hybrid'
- `filters` (optional): Metadata filters
- `citation_style` (optional): Citation format
- `stream` (optional): Stream response (default: false)

### rag_add_feedback
Add relevance feedback for improvement.

**Parameters:**
- `query` (required): Original query
- `document_id` (required): Document ID
- `rating` (required): Relevance rating (1-5)
- `feedback_type` (optional): 'explicit' or 'implicit'

### rag_get_stats
Get RAG system statistics.

**Parameters:**
- `collection` (optional): Specific collection or 'all'
- `include_usage` (optional): Include usage statistics
- `include_performance` (optional): Include performance metrics

### rag_optimize
Optimize the RAG system.

**Parameters:**
- `collection` (optional): Collection to optimize
- `optimization_type` (optional): 'index', 'embeddings', or 'full'
- `reindex` (optional): Force reindexing

### rag_delete_documents
Delete documents from the system.

**Parameters:**
- `document_ids` (optional): List of document IDs to delete
- `collection` (optional): Collection name
- `filter` (optional): Filter for bulk deletion

### rag_export_collection
Export collection data.

**Parameters:**
- `collection` (required): Collection to export
- `format` (optional): 'json', 'csv', or 'parquet'
- `include_embeddings` (optional): Include embeddings in export

## Retrieval Strategies

### Dense Retrieval
Uses vector embeddings for semantic similarity:
```
Query → Embed → Vector Search → Top-K Results
```

### Sparse Retrieval (BM25)
Uses keyword matching with TF-IDF weighting:
```
Query → Tokenize → BM25 Search → Top-K Results
```

### Hybrid Retrieval
Combines both methods with configurable weights:
```
Query → [Dense Search] → Merge → Rerank → Top-K
      → [Sparse Search] →
```

### Multi-Hop Retrieval
Iterative retrieval for complex queries:
```
Query → Search → Results → Generate Follow-up → Search → ...
```

## Usage Examples

### Basic RAG Pipeline
```
1. rag_init(system_name="docs", vector_store="qdrant", embedding_model="nvidia/nv-embed")
2. rag_ingest_documents(documents=["/path/to/doc1.pdf", "/path/to/doc2.pdf"])
3. rag_query(query="What is the main topic?", top_k=5)
```

### Hybrid Search with Filters
```
1. rag_search(
     query="machine learning algorithms",
     search_type="hybrid",
     top_k=10,
     filters={"category": "technical", "year": "2024"},
     rerank=true
   )
```

### Multi-Hop for Complex Queries
```
1. rag_multi_hop_search(
     query="What are the implications of the new AI regulations on healthcare?",
     max_hops=3,
     relevance_threshold=0.7
   )
```

## Vector Store Configuration

### Milvus
```python
MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_USER=root
MILVUS_PASSWORD=Milvus
```

### Qdrant
```python
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_API_KEY=your-api-key
```

### Pinecone
```python
PINECONE_API_KEY=your-api-key
PINECONE_ENVIRONMENT=us-east-1
```

## Embedding Models

### NVIDIA NV-Embed
- Model: `nvidia/nv-embedqa-e5-v5`
- Dimension: 1024
- Optimized for RAG applications

### OpenAI Embeddings
- Model: `text-embedding-3-small` or `text-embedding-3-large`
- Dimension: 1536 or 3072

### Local Models
- Model: `sentence-transformers/all-MiniLM-L6-v2`
- Dimension: 384
- Runs locally without API calls

## Integration with NVIDIA NIM

This skill integrates with NVIDIA NIM microservices:

- **NeMo Retriever**: Advanced retrieval service
- **NVIDIA RAG**: Production RAG pipeline
- **NV-Embed**: High-quality embeddings

## References

- [NVIDIA RAG Blueprint](https://developer.nvidia.com/blueprints)
- [NeMo Retriever Documentation](https://docs.nvidia.com/nemo-retriever)
- [Vector Store Comparison](./references/vector_stores.md)
- [Embedding Models Guide](./references/embeddings.md)
