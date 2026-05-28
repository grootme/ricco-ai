"""
Milvus Vector Store Integration for OpenClaw Agent SaaS.

Milvus is the vector database used in NVIDIA Blueprints for:
- GPU-accelerated vector search (cuVS integration)
- Billion-scale vector storage
- Multi-tenancy with 4 isolation strategies

@author: OpenClaw Agent SaaS
"""

from typing import Any, Dict, List, Optional, Union
from uuid import UUID
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

try:
    from pymilvus import (
        connections,
        Collection,
        CollectionSchema,
        FieldSchema,
        DataType,
        utility,
    )
    MILVUS_AVAILABLE = True
except ImportError:
    MILVUS_AVAILABLE = False
    connections = None
    Collection = None  # type: ignore


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class MilvusConfig:
    """Configuration for Milvus connection."""
    host: str = "localhost"
    port: int = 19530
    user: str = ""
    password: str = ""
    db_name: str = "default"
    
    # Collection defaults
    default_vector_size: int = 1536
    default_index_type: str = "GPU_CAGRA"  # GPU-accelerated
    default_metric_type: str = "COSINE"
    
    # Multi-tenancy strategy
    # Options: "database", "collection", "partition", "partition_key"
    multi_tenant_strategy: str = "partition_key"
    
    # GPU settings (for cuVS)
    use_gpu: bool = True
    gpu_id: int = 0


# ============================================================================
# COLLECTION DEFINITIONS
# ============================================================================

class MilvusCollectionType(str):
    """Pre-defined collections for OpenClaw (matching Qdrant)."""
    AGENT_PROFILES = "agent_profiles"
    SKILLS = "skills"
    DOCUMENTS = "documents"
    MEMORY_ENTRIES = "memory_entries"
    CONVERSATIONS = "conversations"
    COGNITIVE_CAPITAL = "cognitive_capital"


# ============================================================================
# MILVUS VECTOR STORE
# ============================================================================

class MilvusVectorStore:
    """
    Milvus-based vector store for OpenClaw Agent SaaS.
    
    Features:
    - GPU acceleration via cuVS (CAGRA algorithm)
    - 4 multi-tenancy strategies
    - Billion-scale vector support
    - Compatible with NVIDIA Blueprints
    """
    
    def __init__(self, config: Optional[MilvusConfig] = None):
        if not MILVUS_AVAILABLE:
            raise ImportError(
                "Milvus client not installed. Run: pip install pymilvus"
            )
        
        self.config = config or MilvusConfig()
        self._connected = False
        self._collections: Dict[str, Collection] = {}
    
    def connect(self) -> bool:
        """Connect to Milvus server."""
        try:
            connections.connect(
                alias="default",
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                db_name=self.config.db_name,
            )
            self._connected = True
            logger.info(f"Connected to Milvus at {self.config.host}:{self.config.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from Milvus."""
        try:
            connections.disconnect("default")
            self._connected = False
        except Exception as e:
            logger.error(f"Failed to disconnect: {e}")
    
    @property
    def is_connected(self) -> bool:
        return self._connected
    
    # ========================================================================
    # COLLECTION MANAGEMENT
    # ========================================================================
    
    def create_collection(
        self,
        collection_name: str,
        vector_size: Optional[int] = None,
        description: str = "",
        enable_partition_key: bool = True,
    ) -> bool:
        """
        Create a collection with schema.
        
        Schema includes:
        - id (VARCHAR, primary key)
        - vector (FLOAT_VECTOR)
        - tenant_id (VARCHAR, partition key for multi-tenancy)
        - payload (JSON)
        """
        vector_size = vector_size or self.config.default_vector_size
        
        fields = [
            FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=256, is_primary=True),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=vector_size),
            FieldSchema(name="tenant_id", dtype=DataType.VARCHAR, max_length=256, 
                       is_partition_key=enable_partition_key),
            FieldSchema(name="payload", dtype=DataType.JSON),
        ]
        
        schema = CollectionSchema(
            fields=fields,
            description=description or f"OpenClaw {collection_name} collection",
        )
        
        try:
            if utility.has_collection(collection_name):
                logger.info(f"Collection {collection_name} already exists")
                self._collections[collection_name] = Collection(collection_name)
                return True
            
            collection = Collection(
                name=collection_name,
                schema=schema,
            )
            
            # Create GPU-accelerated index
            index_params = {
                "metric_type": self.config.default_metric_type,
                "index_type": self.config.default_index_type,
                "params": {
                    "intermediate_graph_degree": 128,
                    "graph_degree": 64,
                    "build_algo": "IVF_PQ",
                } if self.config.use_gpu else {},
            }
            
            collection.create_index(
                field_name="vector",
                index_params=index_params,
            )
            
            self._collections[collection_name] = collection
            logger.info(f"Created Milvus collection: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {e}")
            return False
    
    def ensure_collections(self) -> Dict[str, bool]:
        """Ensure all required collections exist."""
        results = {}
        for collection in [
            MilvusCollectionType.AGENT_PROFILES,
            MilvusCollectionType.SKILLS,
            MilvusCollectionType.DOCUMENTS,
            MilvusCollectionType.MEMORY_ENTRIES,
            MilvusCollectionType.COGNITIVE_CAPITAL,
        ]:
            results[collection] = self.create_collection(collection)
        return results
    
    # ========================================================================
    # CRUD OPERATIONS
    # ========================================================================
    
    def upsert(
        self,
        collection_name: str,
        point_id: str,
        vector: List[float],
        payload: Dict[str, Any],
        tenant_id: str = "default",
    ) -> bool:
        """Insert or update a point."""
        collection = self._get_collection(collection_name)
        if not collection:
            return False
        
        data = [
            [str(point_id)],
            [vector],
            [tenant_id],
            [payload],
        ]
        
        try:
            collection.upsert(data)
            return True
        except Exception as e:
            logger.error(f"Failed to upsert in Milvus: {e}")
            return False
    
    def batch_upsert(
        self,
        collection_name: str,
        points: List[Dict[str, Any]],
        tenant_id: str = "default",
    ) -> int:
        """Batch insert/update points."""
        collection = self._get_collection(collection_name)
        if not collection:
            return 0
        
        ids = [str(p["id"]) for p in points]
        vectors = [p["vector"] for p in points]
        payloads = [p.get("payload", {}) for p in points]
        tenants = [p.get("tenant_id", tenant_id) for p in points]
        
        data = [ids, vectors, tenants, payloads]
        
        try:
            collection.upsert(data)
            return len(points)
        except Exception as e:
            logger.error(f"Batch upsert failed in Milvus: {e}")
            return 0
    
    def delete(
        self,
        collection_name: str,
        point_id: str,
        tenant_id: str = "default",
    ) -> bool:
        """Delete a point."""
        collection = self._get_collection(collection_name)
        if not collection:
            return False
        
        try:
            collection.delete(
                expr=f'id == "{point_id}" and tenant_id == "{tenant_id}"'
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete from Milvus: {e}")
            return False
    
    # ========================================================================
    # SEARCH OPERATIONS
    # ========================================================================
    
    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        tenant_id: str = "default",
        filter_expr: Optional[str] = None,
        output_fields: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Semantic search with tenant isolation.
        
        Uses GPU-accelerated CAGRA index for fast search.
        """
        collection = self._get_collection(collection_name)
        if not collection:
            return []
        
        # Build filter expression
        expr = f'tenant_id == "{tenant_id}"'
        if filter_expr:
            expr = f'{expr} and ({filter_expr})'
        
        output_fields = output_fields or ["id", "payload", "tenant_id"]
        
        search_params = {
            "metric_type": self.config.default_metric_type,
            "params": {"nprobe": 10},
        }
        
        try:
            results = collection.search(
                data=[query_vector],
                anns_field="vector",
                param=search_params,
                limit=limit,
                expr=expr,
                output_fields=output_fields,
            )
            
            hits = results[0]
            return [
                {
                    "id": hit.id,
                    "score": hit.distance,
                    "payload": hit.entity.get("payload", {}),
                }
                for hit in hits
            ]
        except Exception as e:
            logger.error(f"Milvus search failed: {e}")
            return []
    
    def hybrid_search(
        self,
        collection_name: str,
        query_vector: List[float],
        scalar_filters: Dict[str, Any],
        limit: int = 10,
        tenant_id: str = "default",
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining vector similarity with scalar filtering.
        
        Example:
            hybrid_search(
                collection_name="agent_profiles",
                query_vector=embedding,
                scalar_filters={"domain": "commerce", "orchestration_role": "lead"},
            )
        """
        filter_parts = [f'tenant_id == "{tenant_id}"']
        
        for key, value in scalar_filters.items():
            if isinstance(value, str):
                filter_parts.append(f'{key} == "{value}"')
            elif isinstance(value, (int, float)):
                filter_parts.append(f'{key} == {value}')
            elif isinstance(value, list):
                values_str = ", ".join(f'"{v}"' for v in value)
                filter_parts.append(f'{key} in [{values_str}]')
        
        filter_expr = " and ".join(filter_parts)
        
        return self.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            tenant_id=tenant_id,
            filter_expr=filter_expr,
        )
    
    # ========================================================================
    # HELPER METHODS
    # ========================================================================
    
    def _get_collection(self, collection_name: str) -> Optional[Collection]:
        """Get or load a collection."""
        if collection_name in self._collections:
            return self._collections[collection_name]
        
        try:
            if utility.has_collection(collection_name):
                collection = Collection(collection_name)
                collection.load()
                self._collections[collection_name] = collection
                return collection
        except Exception as e:
            logger.error(f"Failed to get collection {collection_name}: {e}")
        
        return None
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get collection statistics."""
        collection = self._get_collection(collection_name)
        if not collection:
            return {}
        
        return {
            "name": collection_name,
            "num_entities": collection.num_entities,
            "description": collection.description,
        }


# ============================================================================
# COGNITIVE CAPITAL INDEXER (Milvus-specific)
# ============================================================================

class CognitiveCapitalIndexer:
    """
    Indexes Cognitive Capital entries in Milvus.
    
    Cognitive Capital = Knowledge + Experience + Patterns + Skills
    stored in vector form for semantic retrieval.
    """
    
    def __init__(self, vector_store: MilvusVectorStore, embedding_fn: Optional[callable] = None):
        self.vector_store = vector_store
        self._embedding_fn = embedding_fn
    
    async def index_capital(
        self,
        agent_id: str,
        capital_entry: Dict[str, Any],
        tenant_id: str = "default",
    ) -> bool:
        """
        Index a cognitive capital entry.
        
        Entry structure:
        {
            "type": "knowledge" | "experience" | "pattern" | "skill",
            "domain": "commerce" | "health" | ...,
            "content": "The actual knowledge content",
            "context": {"key": "value"},  # Metadata
            "value": 0.8,  # Cognitive value score
        }
        """
        if not self._embedding_fn:
            return False
        
        # Create text for embedding
        text_parts = [
            f"Type: {capital_entry.get('type', 'knowledge')}",
            f"Domain: {capital_entry.get('domain', 'general')}",
            f"Content: {capital_entry.get('content', '')}",
        ]
        
        context = capital_entry.get("context", {})
        if context:
            text_parts.append(f"Context: {context}")
        
        text = " | ".join(text_parts)
        
        try:
            vector = await self._embedding_fn(text)
        except Exception as e:
            logger.error(f"Failed to embed capital: {e}")
            return False
        
        payload = {
            "agent_id": agent_id,
            "type": capital_entry.get("type", "knowledge"),
            "domain": capital_entry.get("domain", "general"),
            "content": capital_entry.get("content", ""),
            "context": context,
            "cognitive_value": capital_entry.get("value", 0.5),
            "created_at": capital_entry.get("created_at"),
        }
        
        entry_id = f"{agent_id}_{capital_entry.get('id', '')}"
        
        return self.vector_store.upsert(
            collection_name=MilvusCollectionType.COGNITIVE_CAPITAL,
            point_id=entry_id,
            vector=vector,
            payload=payload,
            tenant_id=tenant_id,
        )
    
    async def find_relevant_capital(
        self,
        query: str,
        agent_id: Optional[str] = None,
        domain: Optional[str] = None,
        capital_type: Optional[str] = None,
        tenant_id: str = "default",
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Find relevant cognitive capital for a query."""
        if not self._embedding_fn:
            return []
        
        try:
            vector = await self._embedding_fn(query)
        except Exception as e:
            logger.error(f"Failed to embed query: {e}")
            return []
        
        filters = {}
        if agent_id:
            filters["agent_id"] = agent_id
        if domain:
            filters["domain"] = domain
        if capital_type:
            filters["type"] = capital_type
        
        if filters:
            return self.vector_store.hybrid_search(
                collection_name=MilvusCollectionType.COGNITIVE_CAPITAL,
                query_vector=vector,
                scalar_filters=filters,
                limit=limit,
                tenant_id=tenant_id,
            )
        
        return self.vector_store.search(
            collection_name=MilvusCollectionType.COGNITIVE_CAPITAL,
            query_vector=vector,
            limit=limit,
            tenant_id=tenant_id,
        )


# ============================================================================
# FACTORY
# ============================================================================

def create_milvus_store(
    host: str = "localhost",
    port: int = 19530,
    use_gpu: bool = True,
) -> MilvusVectorStore:
    """Create a configured Milvus vector store."""
    config = MilvusConfig(
        host=host,
        port=port,
        use_gpu=use_gpu,
    )
    return MilvusVectorStore(config)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "MilvusConfig",
    "MilvusVectorStore",
    "MilvusCollectionType",
    "CognitiveCapitalIndexer",
    "create_milvus_store",
    "MILVUS_AVAILABLE",
]
