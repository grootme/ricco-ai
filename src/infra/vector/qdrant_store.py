"""
Qdrant Vector Store Integration for OpenClaw Agent SaaS.

Provides semantic search capabilities for:
- Agent profiles (find agents by capability)
- Skills (semantic skill matching)
- Documents (RAG knowledge retrieval)
- Memory entries (semantic memory search)

Alternative to Milvus with better multi-tenancy for SaaS.

@author: OpenClaw Agent SaaS
"""

from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4
from dataclasses import dataclass, field
from datetime import datetime
import json
import asyncio
import os
import logging

logger = logging.getLogger(__name__)

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    from qdrant_client.http.models import Distance, VectorParams, PointStruct
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False
    QdrantClient = None


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class QdrantConfig:
    """Configuration for Qdrant connection."""
    host: str = "localhost"
    port: int = 6333
    grpc_port: int = 6334
    api_key: Optional[str] = None
    prefer_grpc: bool = True
    timeout: int = 30
    
    # Collection defaults
    default_vector_size: int = 1536  # OpenAI embeddings
    default_distance: str = "Cosine"
    
    # Multi-tenancy
    tenant_field: str = "tenant_id"
    default_tenant: str = "default"


# ============================================================================
# COLLECTION DEFINITIONS
# ============================================================================

class CollectionType(str):
    """Pre-defined collections for OpenClaw."""
    AGENT_PROFILES = "agent_profiles"
    SKILLS = "skills"
    DOCUMENTS = "documents"
    MEMORY_ENTRIES = "memory_entries"
    CONVERSATIONS = "conversations"


# ============================================================================
# VECTOR STORE
# ============================================================================

class QdrantVectorStore:
    """
    Qdrant-based vector store for OpenClaw Agent SaaS.
    
    Features:
    - Multi-tenant isolation via payload filtering
    - Semantic search for agents, skills, documents
    - Hybrid filtering (metadata + vector)
    - Batch operations
    """
    
    def __init__(self, config: Optional[QdrantConfig] = None):
        if not QDRANT_AVAILABLE:
            raise ImportError(
                "Qdrant client not installed. Run: pip install qdrant-client"
            )
        
        self.config = config or QdrantConfig()
        self._client: Optional[QdrantClient] = None
        self._collections_cache: Dict[str, bool] = {}
    
    @property
    def client(self) -> QdrantClient:
        """Lazy client initialization."""
        if self._client is None:
            self._client = QdrantClient(
                host=self.config.host,
                port=self.config.port,
                grpc_port=self.config.grpc_port,
                api_key=self.config.api_key,
                prefer_grpc=self.config.prefer_grpc,
                timeout=self.config.timeout,
            )
        return self._client
    
    # ========================================================================
    # COLLECTION MANAGEMENT
    # ========================================================================
    
    async def create_collection(
        self,
        collection_name: str,
        vector_size: Optional[int] = None,
        distance: Optional[str] = None,
    ) -> bool:
        """Create a collection if it doesn't exist."""
        vector_size = vector_size or self.config.default_vector_size
        distance = distance or self.config.default_distance
        
        distance_map = {
            "Cosine": Distance.COSINE,
            "Euclidean": Distance.EUCLID,
            "Dot": Distance.DOT,
        }
        
        try:
            # Check if exists
            collections = self.client.get_collections().collections
            exists = any(c.name == collection_name for c in collections)
            
            if exists:
                logger.info(f"Collection {collection_name} already exists")
                return True
            
            # Create
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=distance_map.get(distance, Distance.COSINE),
                ),
            )
            
            self._collections_cache[collection_name] = True
            logger.info(f"Created collection: {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create collection {collection_name}: {e}")
            return False
    
    async def ensure_collections(self) -> Dict[str, bool]:
        """Ensure all required collections exist."""
        results = {}
        for collection in [
            CollectionType.AGENT_PROFILES,
            CollectionType.SKILLS,
            CollectionType.DOCUMENTS,
            CollectionType.MEMORY_ENTRIES,
        ]:
            results[collection] = await self.create_collection(collection)
        return results
    
    # ========================================================================
    # POINT OPERATIONS
    # ========================================================================
    
    async def upsert(
        self,
        collection_name: str,
        point_id: Union[str, UUID],
        vector: List[float],
        payload: Dict[str, Any],
        tenant_id: Optional[str] = None,
    ) -> bool:
        """
        Insert or update a point.
        
        Args:
            collection_name: Target collection
            point_id: Unique identifier
            vector: Embedding vector
            payload: Metadata (includes tenant_id for multi-tenancy)
            tenant_id: Optional tenant isolation
        """
        # Add tenant to payload
        if tenant_id:
            payload[self.config.tenant_field] = tenant_id
        
        point = PointStruct(
            id=str(point_id),
            vector=vector,
            payload=payload,
        )
        
        try:
            self.client.upsert(
                collection_name=collection_name,
                points=[point],
            )
            return True
        except Exception as e:
            logger.error(f"Failed to upsert point: {e}")
            return False
    
    async def batch_upsert(
        self,
        collection_name: str,
        points: List[Dict[str, Any]],
        tenant_id: Optional[str] = None,
    ) -> int:
        """
        Batch insert/update points.
        
        Args:
            points: List of {id, vector, payload}
        
        Returns:
            Number of successfully upserted points
        """
        qdrant_points = []
        for p in points:
            payload = p.get("payload", {})
            if tenant_id:
                payload[self.config.tenant_field] = tenant_id
            
            qdrant_points.append(PointStruct(
                id=str(p["id"]),
                vector=p["vector"],
                payload=payload,
            ))
        
        try:
            self.client.upsert(
                collection_name=collection_name,
                points=qdrant_points,
            )
            return len(qdrant_points)
        except Exception as e:
            logger.error(f"Batch upsert failed: {e}")
            return 0
    
    # ========================================================================
    # SEARCH OPERATIONS
    # ========================================================================
    
    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        score_threshold: Optional[float] = None,
        tenant_id: Optional[str] = None,
        filter_conditions: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Semantic search with optional filtering.
        
        Args:
            collection_name: Collection to search
            query_vector: Query embedding
            limit: Max results
            score_threshold: Minimum similarity score
            tenant_id: Tenant isolation
            filter_conditions: Additional metadata filters
        
        Returns:
            List of {id, score, payload}
        """
        # Build filter
        must_conditions = []
        
        if tenant_id:
            must_conditions.append(
                models.FieldCondition(
                    key=self.config.tenant_field,
                    match=models.MatchValue(value=tenant_id),
                )
            )
        
        if filter_conditions:
            for key, value in filter_conditions.items():
                must_conditions.append(
                    models.FieldCondition(
                        key=key,
                        match=models.MatchValue(value=value),
                    )
                )
        
        query_filter = models.Filter(must=must_conditions) if must_conditions else None
        
        try:
            results = self.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                query_filter=query_filter,
                limit=limit,
                score_threshold=score_threshold,
            )
            
            return [
                {
                    "id": str(hit.id),
                    "score": hit.score,
                    "payload": hit.payload,
                }
                for hit in results
            ]
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    async def search_by_domain(
        self,
        collection_name: str,
        query_vector: List[float],
        domain: str,
        limit: int = 10,
        tenant_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search within a specific domain."""
        return await self.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            tenant_id=tenant_id,
            filter_conditions={"domain": domain},
        )
    
    async def find_similar_agents(
        self,
        query_vector: List[float],
        required_skills: Optional[List[str]] = None,
        domain: Optional[str] = None,
        tenant_id: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Find agents with similar capabilities.
        
        Used by orchestrator to route tasks to capable agents.
        """
        filter_conditions = {}
        
        if domain:
            filter_conditions["domain"] = domain
        
        return await self.search(
            collection_name=CollectionType.AGENT_PROFILES,
            query_vector=query_vector,
            limit=limit,
            tenant_id=tenant_id,
            filter_conditions=filter_conditions if filter_conditions else None,
        )


# ============================================================================
# AGENT PROFILE INDEXER
# ============================================================================

class AgentProfileIndexer:
    """
    Indexes AgentProfiles into Qdrant for semantic search.
    
    Enables finding agents by capability description.
    """
    
    def __init__(
        self,
        vector_store: QdrantVectorStore,
        embedding_fn: Optional[callable] = None,
    ):
        self.vector_store = vector_store
        self._embedding_fn = embedding_fn
    
    def set_embedding_fn(self, fn: callable):
        """Set the embedding function (e.g., OpenAI embeddings)."""
        self._embedding_fn = fn
    
    async def index_profile(
        self,
        profile,  # AgentProfile from agents.profile
        tenant_id: Optional[str] = None,
    ) -> bool:
        """
        Index an agent profile.
        
        Creates a searchable representation including:
        - Name and description
        - Domain and skills
        - Capabilities summary
        """
        if not self._embedding_fn:
            logger.warning("No embedding function set")
            return False
        
        # Create text representation for embedding
        text_parts = [
            f"Agent: {profile.name}",
            f"Domain: {profile.domain}",
            f"Description: {profile.description}",
        ]
        
        if profile.skills:
            skills_text = ", ".join(s.skill_name for s in profile.skills)
            text_parts.append(f"Skills: {skills_text}")
        
        if profile.prompt_context and profile.prompt_context.role_description:
            text_parts.append(f"Role: {profile.prompt_context.role_description}")
        
        text_for_embedding = " | ".join(text_parts)
        
        # Generate embedding
        try:
            vector = await self._embedding_fn(text_for_embedding)
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            return False
        
        # Create payload
        payload = {
            "name": profile.name,
            "domain": profile.domain,
            "description": profile.description,
            "skills": [s.skill_name for s in profile.skills],
            "tools": [t.tool_name for t in profile.tools],
            "mcps": [m.mcp_name for m in profile.mcps],
            "execution_pattern": profile.execution_pattern.value,
            "orchestration_role": profile.orchestration_role.value,
            "tags": profile.tags,
            "capabilities_summary": profile.get_capabilities_summary(),
        }
        
        return await self.vector_store.upsert(
            collection_name=CollectionType.AGENT_PROFILES,
            point_id=profile.id,
            vector=vector,
            payload=payload,
            tenant_id=tenant_id,
        )
    
    async def find_capable_agents(
        self,
        query: str,
        domain: Optional[str] = None,
        required_skills: Optional[List[str]] = None,
        tenant_id: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Find agents capable of handling a query.
        
        Args:
            query: Natural language capability description
            domain: Optional domain filter
            required_skills: Optional required skills (post-filter)
            tenant_id: Tenant isolation
        
        Returns:
            List of matching agent profiles
        """
        if not self._embedding_fn:
            logger.warning("No embedding function set")
            return []
        
        try:
            query_vector = await self._embedding_fn(query)
        except Exception as e:
            logger.error(f"Failed to embed query: {e}")
            return []
        
        results = await self.vector_store.find_similar_agents(
            query_vector=query_vector,
            domain=domain,
            tenant_id=tenant_id,
            limit=limit * 2,  # Get more for post-filtering
        )
        
        # Post-filter by required skills
        if required_skills:
            filtered = []
            for result in results:
                agent_skills = result.get("payload", {}).get("skills", [])
                if all(skill in agent_skills for skill in required_skills):
                    filtered.append(result)
            results = filtered[:limit]
        
        return results


# ============================================================================
# EMBEDDING FUNCTIONS
# ============================================================================

async def openai_embedding_fn(
    text: str,
    model: str = "text-embedding-3-small",
    api_key: Optional[str] = None,
) -> List[float]:
    """
    Generate embedding using OpenAI API.
    
    Compatible with OpenRouter for free models.
    """
    import httpx
    
    api_key = api_key or os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
    
    if not api_key:
        raise ValueError("No OpenAI/OpenRouter API key provided")
    
    # OpenRouter base URL
    base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/embeddings",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "input": text,
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        return data["data"][0]["embedding"]


# ============================================================================
# FACTORY
# ============================================================================

def create_vector_store(
    host: str = "localhost",
    port: int = 6333,
    api_key: Optional[str] = None,
    tenant_id: Optional[str] = None,
) -> QdrantVectorStore:
    """Create a configured vector store."""
    config = QdrantConfig(
        host=host,
        port=port,
        api_key=api_key,
    )
    if tenant_id:
        config.default_tenant = tenant_id
    
    return QdrantVectorStore(config)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "QdrantConfig",
    "QdrantVectorStore",
    "AgentProfileIndexer",
    "CollectionType",
    "create_vector_store",
    "openai_embedding_fn",
    "QDRANT_AVAILABLE",
]
