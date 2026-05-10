"""
Vector Store Factory - Unified interface for Qdrant and Milvus.

Provides:
- Qdrant: Best for SaaS multi-tenant, simpler operations
- Milvus: Best for GPU acceleration, billion-scale, NVIDIA Blueprints compatibility

@author: OpenClaw Agent SaaS
"""

from typing import Any, Dict, List, Optional, Union
from enum import Enum
from dataclasses import dataclass
import logging
import os

logger = logging.getLogger(__name__)


class VectorStoreType(str, Enum):
    """Available vector store types."""
    QDRANT = "qdrant"
    MILVUS = "milvus"
    AUTO = "auto"  # Auto-select based on configuration


@dataclass
class VectorStoreConfig:
    """Unified configuration for vector stores."""
    store_type: VectorStoreType = VectorStoreType.AUTO
    
    # Qdrant settings
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_api_key: Optional[str] = None
    
    # Milvus settings
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_use_gpu: bool = True
    
    # Common settings
    default_tenant: str = "default"
    default_vector_size: int = 1536
    
    @classmethod
    def from_env(cls) -> "VectorStoreConfig":
        """Load configuration from environment variables."""
        store_type = os.environ.get("VECTOR_STORE_TYPE", "auto")
        
        return cls(
            store_type=VectorStoreType(store_type.lower()),
            qdrant_host=os.environ.get("QDRANT_HOST", "localhost"),
            qdrant_port=int(os.environ.get("QDRANT_PORT", "6333")),
            qdrant_api_key=os.environ.get("QDRANT_API_KEY"),
            milvus_host=os.environ.get("MILVUS_HOST", "localhost"),
            milvus_port=int(os.environ.get("MILVUS_PORT", "19530")),
            milvus_use_gpu=os.environ.get("MILVUS_USE_GPU", "true").lower() == "true",
            default_tenant=os.environ.get("DEFAULT_TENANT", "default"),
        )


class UnifiedVectorStore:
    """
    Unified interface for vector stores.
    
    Automatically selects the best available store or uses the configured one.
    Supports both Qdrant and Milvus transparently.
    """
    
    def __init__(self, config: Optional[VectorStoreConfig] = None):
        self.config = config or VectorStoreConfig.from_env()
        self._qdrant = None
        self._milvus = None
        self._active_store = None
    
    @property
    def qdrant(self):
        """Lazy-load Qdrant client."""
        if self._qdrant is None:
            try:
                from .qdrant_store import QdrantVectorStore, QdrantConfig
                qconfig = QdrantConfig(
                    host=self.config.qdrant_host,
                    port=self.config.qdrant_port,
                    api_key=self.config.qdrant_api_key,
                )
                self._qdrant = QdrantVectorStore(qconfig)
                logger.info("Qdrant vector store initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Qdrant: {e}")
        return self._qdrant
    
    @property
    def milvus(self):
        """Lazy-load Milvus client."""
        if self._milvus is None:
            try:
                from .milvus_store import MilvusVectorStore, MilvusConfig
                mconfig = MilvusConfig(
                    host=self.config.milvus_host,
                    port=self.config.milvus_port,
                    use_gpu=self.config.milvus_use_gpu,
                )
                self._milvus = MilvusVectorStore(mconfig)
                self._milvus.connect()
                logger.info("Milvus vector store initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Milvus: {e}")
        return self._milvus
    
    def get_store(self, preferred: Optional[VectorStoreType] = None):
        """Get the appropriate vector store."""
        store_type = preferred or self.config.store_type
        
        if store_type == VectorStoreType.QDRANT:
            return self.qdrant
        elif store_type == VectorStoreType.MILVUS:
            return self.milvus
        else:  # AUTO
            # Prefer Qdrant for SaaS, Milvus for GPU/large scale
            if self.qdrant:
                return self.qdrant
            elif self.milvus:
                return self.milvus
            else:
                raise RuntimeError("No vector store available")
    
    # ========================================================================
    # UNIFIED API (delegates to active store)
    # ========================================================================
    
    async def upsert(
        self,
        collection_name: str,
        point_id: str,
        vector: List[float],
        payload: Dict[str, Any],
        tenant_id: Optional[str] = None,
        store_type: Optional[VectorStoreType] = None,
    ) -> bool:
        """Upsert a point into the vector store."""
        store = self.get_store(store_type)
        tenant_id = tenant_id or self.config.default_tenant
        
        if hasattr(store, 'upsert'):
            # Check if it's async
            import asyncio
            if asyncio.iscoroutinefunction(store.upsert):
                return await store.upsert(
                    collection_name=collection_name,
                    point_id=point_id,
                    vector=vector,
                    payload=payload,
                    tenant_id=tenant_id,
                )
            else:
                return store.upsert(
                    collection_name=collection_name,
                    point_id=point_id,
                    vector=vector,
                    payload=payload,
                    tenant_id=tenant_id,
                )
        return False
    
    async def search(
        self,
        collection_name: str,
        query_vector: List[float],
        limit: int = 10,
        tenant_id: Optional[str] = None,
        filter_conditions: Optional[Dict[str, Any]] = None,
        store_type: Optional[VectorStoreType] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        store = self.get_store(store_type)
        tenant_id = tenant_id or self.config.default_tenant
        
        if hasattr(store, 'search'):
            import asyncio
            if asyncio.iscoroutinefunction(store.search):
                return await store.search(
                    collection_name=collection_name,
                    query_vector=query_vector,
                    limit=limit,
                    tenant_id=tenant_id,
                    filter_conditions=filter_conditions,
                )
            else:
                return store.search(
                    collection_name=collection_name,
                    query_vector=query_vector,
                    limit=limit,
                    tenant_id=tenant_id,
                    filter_conditions=filter_conditions,
                )
        return []
    
    async def create_collection(
        self,
        collection_name: str,
        vector_size: Optional[int] = None,
        store_type: Optional[VectorStoreType] = None,
    ) -> bool:
        """Create a collection."""
        store = self.get_store(store_type)
        vector_size = vector_size or self.config.default_vector_size
        
        if hasattr(store, 'create_collection'):
            import asyncio
            if asyncio.iscoroutinefunction(store.create_collection):
                return await store.create_collection(
                    collection_name=collection_name,
                    vector_size=vector_size,
                )
            else:
                return store.create_collection(
                    collection_name=collection_name,
                    vector_size=vector_size,
                )
        return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all vector stores."""
        return {
            "qdrant": {
                "available": self._qdrant is not None,
                "host": self.config.qdrant_host,
                "port": self.config.qdrant_port,
            },
            "milvus": {
                "available": self._milvus is not None and (self._milvus.is_connected if self._milvus else False),
                "host": self.config.milvus_host,
                "port": self.config.milvus_port,
                "gpu": self.config.milvus_use_gpu,
            },
            "active_store": self.config.store_type.value,
        }


# ============================================================================
# COLLECTION TYPES (shared between Qdrant and Milvus)
# ============================================================================

class CollectionType(str):
    """Pre-defined collections for OpenClaw."""
    AGENT_PROFILES = "agent_profiles"
    SKILLS = "skills"
    DOCUMENTS = "documents"
    MEMORY_ENTRIES = "memory_entries"
    CONVERSATIONS = "conversations"
    COGNITIVE_CAPITAL = "cognitive_capital"


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_vector_store(
    store_type: str = "auto",
    **kwargs,
) -> UnifiedVectorStore:
    """Create a unified vector store."""
    config = VectorStoreConfig(
        store_type=VectorStoreType(store_type.lower()),
        **kwargs,
    )
    return UnifiedVectorStore(config)


# ============================================================================
# SYNCHRONIZATION EXPORTS
# ============================================================================

from .vector_store_sync import (
    SyncDirection,
    SyncMode,
    ConflictResolution,
    SyncConfig,
    SyncEvent,
    SyncState,
    SyncObserver,
    LoggingSyncObserver,
    MetricsSyncObserver,
    SyncCommand,
    UpsertSyncCommand,
    DeleteSyncCommand,
    SyncStrategy,
    FullSyncStrategy,
    IncrementalSyncStrategy,
    DeltaSyncStrategy,
    SyncStrategyFactory,
    VectorStoreSynchronizer,
    create_synchronizer,
)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Core
    "VectorStoreType",
    "VectorStoreConfig",
    "UnifiedVectorStore",
    "CollectionType",
    "create_vector_store",
    # Synchronization
    "SyncDirection",
    "SyncMode",
    "ConflictResolution",
    "SyncConfig",
    "SyncEvent",
    "SyncState",
    "SyncObserver",
    "LoggingSyncObserver",
    "MetricsSyncObserver",
    "SyncCommand",
    "UpsertSyncCommand",
    "DeleteSyncCommand",
    "SyncStrategy",
    "FullSyncStrategy",
    "IncrementalSyncStrategy",
    "DeltaSyncStrategy",
    "SyncStrategyFactory",
    "VectorStoreSynchronizer",
    "create_synchronizer",
]
