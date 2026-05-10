"""
NEXUS Vector Store Module

Integración con Milvus y Qdrant para almacenamiento de capital cognitivo vectorizado.
"""

from .core import (
    # Enums
    VectorStoreType,
    SyncDirection,
    VectorMetric,
    
    # Models
    VectorDocument,
    SearchResult,
    CollectionInfo,
    
    # Adapters
    VectorStoreAdapter,
    MemoryVectorStoreAdapter,
    MilvusAdapter,
    QdrantAdapter,
    
    # Factory
    VectorStoreFactory,
    
    # Facade
    VectorStoreFacade,
    
    # Services
    EmbeddingService,
)

__all__ = [
    "VectorStoreType",
    "SyncDirection",
    "VectorMetric",
    "VectorDocument",
    "SearchResult",
    "CollectionInfo",
    "VectorStoreAdapter",
    "MemoryVectorStoreAdapter",
    "MilvusAdapter",
    "QdrantAdapter",
    "VectorStoreFactory",
    "VectorStoreFacade",
    "EmbeddingService",
]
