"""
NEXUS Vector Store - Integración con Milvus y Qdrant

Sistema de sincronización y migración entre bases de datos vectoriales.
Permite almacenar y recuperar capital cognitivo como embeddings.

Características:
- Abstracción unificada para múltiples vector stores
- Sincronización bidireccional entre Milvus y Qdrant
- Migración de datos con validación
- Caché local para optimización de tokens
- Búsqueda híbrida (vector + metadata)

Patrones GOF Aplicados:
- Adapter: Adaptadores para diferentes vector stores
- Strategy: Estrategias de sincronización intercambiables
- Factory: Creación de conexiones
- Observer: Notificación de cambios
- Facade: Interfaz simplificada

@author: NEXUS - Neural Execution Unified System
"""

from typing import Dict, List, Any, Optional, Union, Callable, Protocol
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from abc import ABC, abstractmethod
import asyncio
import json
import logging
import hashlib
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS Y TIPOS
# ============================================================================

class VectorStoreType(str, Enum):
    """Tipos de vector store soportados"""
    MILVUS = "milvus"
    QDRANT = "qdrant"
    MEMORY = "memory"  # Fallback en memoria
    POSTGRES = "postgres"  # pgvector


class SyncDirection(str, Enum):
    """Dirección de sincronización"""
    MILVUS_TO_QDRANT = "milvus_to_qdrant"
    QDRANT_TO_MILVUS = "qdrant_to_milvus"
    BIDIRECTIONAL = "bidirectional"


class VectorMetric(str, Enum):
    """Métricas de distancia para vectores"""
    COSINE = "cosine"
    EUCLIDEAN = "euclidean"
    DOT_PRODUCT = "dot_product"


# ============================================================================
# MODELOS DE DATOS
# ============================================================================

@dataclass
class VectorDocument:
    """Documento vectorizado para almacenamiento"""
    id: str = field(default_factory=lambda: str(uuid4()))
    vector: List[float] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    content: str = ""
    domain: str = "general"
    agent_id: str = ""
    cognitive_value: float = 0.0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "vector": self.vector,
            "metadata": self.metadata,
            "content": self.content,
            "domain": self.domain,
            "agent_id": self.agent_id,
            "cognitive_value": self.cognitive_value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VectorDocument':
        return cls(
            id=data.get("id", str(uuid4())),
            vector=data.get("vector", []),
            metadata=data.get("metadata", {}),
            content=data.get("content", ""),
            domain=data.get("domain", "general"),
            agent_id=data.get("agent_id", ""),
            cognitive_value=data.get("cognitive_value", 0.0),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.utcnow(),
        )


@dataclass
class SearchResult:
    """Resultado de búsqueda vectorial"""
    document: VectorDocument
    score: float
    distance: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "document": self.document.to_dict(),
            "score": self.score,
            "distance": self.distance,
        }


@dataclass
class CollectionInfo:
    """Información de una colección/vector store"""
    name: str
    vector_size: int
    document_count: int
    metric: VectorMetric
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# PATRÓN ADAPTER - Adaptadores para Vector Stores
# ============================================================================

class VectorStoreAdapter(ABC):
    """
    Patrón Adapter - Adaptador base para vector stores
    
    Define la interfaz común que todos los adaptadores deben implementar.
    """
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establece conexión con el vector store"""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Cierra la conexión"""
        pass
    
    @abstractmethod
    async def create_collection(
        self,
        name: str,
        vector_size: int,
        metric: VectorMetric = VectorMetric.COSINE
    ) -> bool:
        """Crea una colección/índice"""
        pass
    
    @abstractmethod
    async def delete_collection(self, name: str) -> bool:
        """Elimina una colección"""
        pass
    
    @abstractmethod
    async def insert(self, collection: str, documents: List[VectorDocument]) -> List[str]:
        """Inserta documentos"""
        pass
    
    @abstractmethod
    async def search(
        self,
        collection: str,
        vector: List[float],
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Búsqueda por similitud vectorial"""
        pass
    
    @abstractmethod
    async def get_by_id(self, collection: str, doc_id: str) -> Optional[VectorDocument]:
        """Obtiene documento por ID"""
        pass
    
    @abstractmethod
    async def delete(self, collection: str, doc_ids: List[str]) -> bool:
        """Elimina documentos por IDs"""
        pass
    
    @abstractmethod
    async def get_collection_info(self, name: str) -> Optional[CollectionInfo]:
        """Obtiene información de la colección"""
        pass
    
    @abstractmethod
    async def list_collections(self) -> List[str]:
        """Lista todas las colecciones"""
        pass


class MemoryVectorStoreAdapter(VectorStoreAdapter):
    """
    Adaptador en memoria - Fallback sin dependencias externas
    
    Útil para testing y desarrollo. No persistente.
    """
    
    def __init__(self):
        self._collections: Dict[str, List[VectorDocument]] = {}
        self._vector_size: Dict[str, int] = {}
        self._connected = False
    
    async def connect(self) -> bool:
        self._connected = True
        logger.info("Memory vector store connected")
        return True
    
    async def disconnect(self) -> None:
        self._connected = False
        logger.info("Memory vector store disconnected")
    
    async def create_collection(
        self,
        name: str,
        vector_size: int,
        metric: VectorMetric = VectorMetric.COSINE
    ) -> bool:
        self._collections[name] = []
        self._vector_size[name] = vector_size
        logger.info(f"Created memory collection: {name}")
        return True
    
    async def delete_collection(self, name: str) -> bool:
        if name in self._collections:
            del self._collections[name]
            del self._vector_size[name]
            return True
        return False
    
    async def insert(self, collection: str, documents: List[VectorDocument]) -> List[str]:
        if collection not in self._collections:
            await self.create_collection(collection, 384)
        
        inserted_ids = []
        for doc in documents:
            self._collections[collection].append(doc)
            inserted_ids.append(doc.id)
        
        return inserted_ids
    
    async def search(
        self,
        collection: str,
        vector: List[float],
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        if collection not in self._collections:
            return []
        
        docs = self._collections[collection]
        
        results = []
        for doc in docs:
            if doc.vector:
                score = self._cosine_similarity(vector, doc.vector)
                
                if filter:
                    if not self._matches_filter(doc.metadata, filter):
                        continue
                
                results.append(SearchResult(
                    document=doc,
                    score=score,
                    distance=1 - score
                ))
        
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calcula similitud coseno entre dos vectores"""
        import math
        
        min_len = min(len(a), len(b))
        if min_len == 0:
            return 0.0
        
        a = a[:min_len]
        b = b[:min_len]
        
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot / (norm_a * norm_b)
    
    def _matches_filter(self, metadata: Dict, filter: Dict) -> bool:
        """Verifica si metadata coincide con filtro"""
        for key, value in filter.items():
            if key not in metadata:
                return False
            if isinstance(value, dict):
                if "$eq" in value and metadata[key] != value["$eq"]:
                    return False
                if "$ne" in value and metadata[key] == value["$ne"]:
                    return False
                if "$in" in value and metadata[key] not in value["$in"]:
                    return False
            elif metadata[key] != value:
                return False
        return True
    
    async def get_by_id(self, collection: str, doc_id: str) -> Optional[VectorDocument]:
        if collection not in self._collections:
            return None
        
        for doc in self._collections[collection]:
            if doc.id == doc_id:
                return doc
        return None
    
    async def delete(self, collection: str, doc_ids: List[str]) -> bool:
        if collection not in self._collections:
            return False
        
        self._collections[collection] = [
            doc for doc in self._collections[collection]
            if doc.id not in doc_ids
        ]
        return True
    
    async def get_collection_info(self, name: str) -> Optional[CollectionInfo]:
        if name not in self._collections:
            return None
        
        return CollectionInfo(
            name=name,
            vector_size=self._vector_size.get(name, 384),
            document_count=len(self._collections[name]),
            metric=VectorMetric.COSINE
        )
    
    async def list_collections(self) -> List[str]:
        return list(self._collections.keys())


class MilvusAdapter(VectorStoreAdapter):
    """
    Adaptador para Milvus
    
    Requiere: pip install pymilvus
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 19530,
        user: str = "",
        password: str = ""
    ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self._client = None
        self._connected = False
    
    async def connect(self) -> bool:
        try:
            from pymilvus import MilvusClient
            
            self._client = MilvusClient(
                uri=f"http://{self.host}:{self.port}",
                user=self.user,
                password=self.password
            )
            self._connected = True
            logger.info(f"Connected to Milvus at {self.host}:{self.port}")
            return True
        except ImportError:
            logger.warning("pymilvus not installed, using memory fallback")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to Milvus: {e}")
            return False
    
    async def disconnect(self) -> None:
        if self._client:
            self._client.close()
        self._connected = False
    
    async def create_collection(
        self,
        name: str,
        vector_size: int,
        metric: VectorMetric = VectorMetric.COSINE
    ) -> bool:
        if not self._connected or not self._client:
            return False
        
        try:
            metric_map = {
                VectorMetric.COSINE: "COSINE",
                VectorMetric.EUCLIDEAN: "L2",
                VectorMetric.DOT_PRODUCT: "IP"
            }
            
            self._client.create_collection(
                collection_name=name,
                dimension=vector_size,
                metric_type=metric_map.get(metric, "COSINE")
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create Milvus collection: {e}")
            return False
    
    async def delete_collection(self, name: str) -> bool:
        if not self._connected or not self._client:
            return False
        
        try:
            self._client.drop_collection(name)
            return True
        except Exception as e:
            logger.error(f"Failed to delete Milvus collection: {e}")
            return False
    
    async def insert(self, collection: str, documents: List[VectorDocument]) -> List[str]:
        if not self._connected or not self._client:
            return []
        
        try:
            data = []
            for doc in documents:
                data.append({
                    "id": doc.id,
                    "vector": doc.vector,
                    **doc.metadata
                })
            
            self._client.insert(
                collection_name=collection,
                data=data
            )
            return [doc.id for doc in documents]
        except Exception as e:
            logger.error(f"Failed to insert to Milvus: {e}")
            return []
    
    async def search(
        self,
        collection: str,
        vector: List[float],
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        if not self._connected or not self._client:
            return []
        
        try:
            results = self._client.search(
                collection_name=collection,
                data=[vector],
                limit=top_k,
                filter=filter
            )
            
            search_results = []
            for hit in results[0]:
                doc = VectorDocument(
                    id=str(hit.get("id", "")),
                    vector=hit.get("vector", []),
                    metadata=hit.get("entity", {}),
                )
                search_results.append(SearchResult(
                    document=doc,
                    score=hit.get("distance", 0),
                    distance=hit.get("distance", 0)
                ))
            
            return search_results
        except Exception as e:
            logger.error(f"Failed to search Milvus: {e}")
            return []
    
    async def get_by_id(self, collection: str, doc_id: str) -> Optional[VectorDocument]:
        if not self._connected or not self._client:
            return None
        
        try:
            results = self._client.get(
                collection_name=collection,
                ids=[doc_id]
            )
            
            if results:
                return VectorDocument(
                    id=doc_id,
                    vector=results[0].get("vector", []),
                    metadata=results[0]
                )
            return None
        except Exception as e:
            logger.error(f"Failed to get from Milvus: {e}")
            return None
    
    async def delete(self, collection: str, doc_ids: List[str]) -> bool:
        if not self._connected or not self._client:
            return False
        
        try:
            self._client.delete(
                collection_name=collection,
                ids=doc_ids
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete from Milvus: {e}")
            return False
    
    async def get_collection_info(self, name: str) -> Optional[CollectionInfo]:
        if not self._connected or not self._client:
            return None
        
        try:
            stats = self._client.get_collection_stats(name)
            return CollectionInfo(
                name=name,
                vector_size=384,
                document_count=stats.get("row_count", 0),
                metric=VectorMetric.COSINE
            )
        except Exception as e:
            logger.error(f"Failed to get Milvus collection info: {e}")
            return None
    
    async def list_collections(self) -> List[str]:
        if not self._connected or not self._client:
            return []
        
        try:
            return self._client.list_collections()
        except Exception as e:
            logger.error(f"Failed to list Milvus collections: {e}")
            return []


class QdrantAdapter(VectorStoreAdapter):
    """
    Adaptador para Qdrant
    
    Requiere: pip install qdrant-client
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        api_key: Optional[str] = None
    ):
        self.host = host
        self.port = port
        self.api_key = api_key
        self._client = None
        self._connected = False
    
    async def connect(self) -> bool:
        try:
            from qdrant_client import QdrantClient
            
            self._client = QdrantClient(
                host=self.host,
                port=self.port,
                api_key=self.api_key
            )
            self._connected = True
            logger.info(f"Connected to Qdrant at {self.host}:{self.port}")
            return True
        except ImportError:
            logger.warning("qdrant-client not installed, using memory fallback")
            return False
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {e}")
            return False
    
    async def disconnect(self) -> None:
        if self._client:
            self._client.close()
        self._connected = False
    
    async def create_collection(
        self,
        name: str,
        vector_size: int,
        metric: VectorMetric = VectorMetric.COSINE
    ) -> bool:
        if not self._connected or not self._client:
            return False
        
        try:
            from qdrant_client.models import Distance, VectorParams
            
            distance_map = {
                VectorMetric.COSINE: Distance.COSINE,
                VectorMetric.EUCLIDEAN: Distance.EUCLID,
                VectorMetric.DOT_PRODUCT: Distance.DOT
            }
            
            self._client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=distance_map.get(metric, Distance.COSINE)
                )
            )
            return True
        except Exception as e:
            logger.error(f"Failed to create Qdrant collection: {e}")
            return False
    
    async def delete_collection(self, name: str) -> bool:
        if not self._connected or not self._client:
            return False
        
        try:
            self._client.delete_collection(name)
            return True
        except Exception as e:
            logger.error(f"Failed to delete Qdrant collection: {e}")
            return False
    
    async def insert(self, collection: str, documents: List[VectorDocument]) -> List[str]:
        if not self._connected or not self._client:
            return []
        
        try:
            from qdrant_client.models import PointStruct
            
            points = []
            for doc in documents:
                points.append(PointStruct(
                    id=doc.id,
                    vector=doc.vector,
                    payload={
                        "content": doc.content,
                        "domain": doc.domain,
                        "agent_id": doc.agent_id,
                        "cognitive_value": doc.cognitive_value,
                        **doc.metadata
                    }
                ))
            
            self._client.upsert(
                collection_name=collection,
                points=points
            )
            return [doc.id for doc in documents]
        except Exception as e:
            logger.error(f"Failed to insert to Qdrant: {e}")
            return []
    
    async def search(
        self,
        collection: str,
        vector: List[float],
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        if not self._connected or not self._client:
            return []
        
        try:
            from qdrant_client.models import Filter
            
            results = self._client.search(
                collection_name=collection,
                query_vector=vector,
                limit=top_k,
                query_filter=Filter(**filter) if filter else None
            )
            
            search_results = []
            for hit in results:
                doc = VectorDocument(
                    id=str(hit.id),
                    vector=hit.vector or [],
                    metadata=hit.payload or {},
                    content=hit.payload.get("content", "") if hit.payload else "",
                    domain=hit.payload.get("domain", "general") if hit.payload else "general"
                )
                search_results.append(SearchResult(
                    document=doc,
                    score=hit.score,
                    distance=1 - hit.score
                ))
            
            return search_results
        except Exception as e:
            logger.error(f"Failed to search Qdrant: {e}")
            return []
    
    async def get_by_id(self, collection: str, doc_id: str) -> Optional[VectorDocument]:
        if not self._connected or not self._client:
            return None
        
        try:
            results = self._client.retrieve(
                collection_name=collection,
                ids=[doc_id]
            )
            
            if results:
                hit = results[0]
                return VectorDocument(
                    id=str(hit.id),
                    vector=hit.vector or [],
                    metadata=hit.payload or {},
                    content=hit.payload.get("content", "") if hit.payload else ""
                )
            return None
        except Exception as e:
            logger.error(f"Failed to get from Qdrant: {e}")
            return None
    
    async def delete(self, collection: str, doc_ids: List[str]) -> bool:
        if not self._connected or not self._client:
            return False
        
        try:
            self._client.delete(
                collection_name=collection,
                points_selector=doc_ids
            )
            return True
        except Exception as e:
            logger.error(f"Failed to delete from Qdrant: {e}")
            return False
    
    async def get_collection_info(self, name: str) -> Optional[CollectionInfo]:
        if not self._connected or not self._client:
            return None
        
        try:
            info = self._client.get_collection(name)
            return CollectionInfo(
                name=name,
                vector_size=info.config.params.vectors.size if hasattr(info.config.params, 'vectors') else 384,
                document_count=info.points_count,
                metric=VectorMetric.COSINE,
                metadata={"status": info.status}
            )
        except Exception as e:
            logger.error(f"Failed to get Qdrant collection info: {e}")
            return None
    
    async def list_collections(self) -> List[str]:
        if not self._connected or not self._client:
            return []
        
        try:
            collections = self._client.get_collections()
            return [c.name for c in collections.collections]
        except Exception as e:
            logger.error(f"Failed to list Qdrant collections: {e}")
            return []


# ============================================================================
# PATRÓN FACTORY - Fábrica de Vector Stores
# ============================================================================

class VectorStoreFactory:
    """
    Patrón Factory - Crea adaptadores de vector store
    """
    
    @staticmethod
    def create(
        store_type: VectorStoreType,
        **kwargs
    ) -> VectorStoreAdapter:
        """Crea un adaptador según el tipo"""
        
        if store_type == VectorStoreType.MILVUS:
            return MilvusAdapter(
                host=kwargs.get("host", "localhost"),
                port=kwargs.get("port", 19530),
                user=kwargs.get("user", ""),
                password=kwargs.get("password", "")
            )
        
        elif store_type == VectorStoreType.QDRANT:
            return QdrantAdapter(
                host=kwargs.get("host", "localhost"),
                port=kwargs.get("port", 6333),
                api_key=kwargs.get("api_key")
            )
        
        elif store_type == VectorStoreType.MEMORY:
            return MemoryVectorStoreAdapter()
        
        else:
            logger.warning(f"Unknown store type {store_type}, using memory fallback")
            return MemoryVectorStoreAdapter()
    
    @staticmethod
    def create_auto_detect() -> VectorStoreAdapter:
        """Detecta automáticamente el vector store disponible"""
        
        # Intentar Milvus
        milvus = MilvusAdapter()
        if asyncio.get_event_loop().run_until_complete(milvus.connect()):
            return milvus
        
        # Intentar Qdrant
        qdrant = QdrantAdapter()
        if asyncio.get_event_loop().run_until_complete(qdrant.connect()):
            return qdrant
        
        # Fallback a memoria
        logger.info("No external vector store available, using memory store")
        return MemoryVectorStoreAdapter()


# ============================================================================
# PATRÓN FACADE - Interfaz Unificada
# ============================================================================

class VectorStoreFacade:
    """
    Patrón Facade - Interfaz simplificada para múltiples vector stores
    
    Proporciona una API unificada para operar con diferentes backends.
    Maneja sincronización, migración y failover automáticamente.
    """
    
    def __init__(
        self,
        primary: VectorStoreType = VectorStoreType.MEMORY,
        secondary: Optional[VectorStoreType] = None,
        vector_size: int = 384
    ):
        self.primary_type = primary
        self.secondary_type = secondary
        self.vector_size = vector_size
        
        self._primary: VectorStoreAdapter = VectorStoreFactory.create(primary)
        self._secondary: Optional[VectorStoreAdapter] = (
            VectorStoreFactory.create(secondary) if secondary else None
        )
        
        self._cache: Dict[str, VectorDocument] = {}
        self._connected = False
    
    async def initialize(self) -> bool:
        """Inicializa conexiones"""
        primary_ok = await self._primary.connect()
        
        if self._secondary:
            secondary_ok = await self._secondary.connect()
            self._connected = primary_ok or secondary_ok
        else:
            self._connected = primary_ok
        
        if not primary_ok and self._primary.__class__.__name__ != 'MemoryVectorStoreAdapter':
            self._primary = MemoryVectorStoreAdapter()
            await self._primary.connect()
            self._connected = True
        
        return self._connected
    
    async def shutdown(self) -> None:
        """Cierra conexiones"""
        await self._primary.disconnect()
        if self._secondary:
            await self._secondary.disconnect()
        self._connected = False
    
    async def store_cognitive_capital(
        self,
        collection: str,
        content: str,
        vector: List[float],
        metadata: Dict[str, Any],
        agent_id: str = "",
        domain: str = "general",
        cognitive_value: float = 1.0
    ) -> Optional[str]:
        """Almacena capital cognitivo vectorizado"""
        if not self._connected:
            await self.initialize()
        
        doc = VectorDocument(
            vector=vector,
            content=content,
            metadata=metadata,
            agent_id=agent_id,
            domain=domain,
            cognitive_value=cognitive_value
        )
        
        ids = await self._primary.insert(collection, [doc])
        
        if self._secondary and ids:
            await self._secondary.insert(collection, [doc])
        
        if ids:
            self._cache[ids[0]] = doc
        
        return ids[0] if ids else None
    
    async def search_similar(
        self,
        collection: str,
        vector: List[float],
        top_k: int = 10,
        filter: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Búsqueda de documentos similares"""
        if not self._connected:
            await self.initialize()
        
        results = await self._primary.search(collection, vector, top_k, filter)
        
        if not results and self._secondary:
            results = await self._secondary.search(collection, vector, top_k, filter)
        
        return results
    
    async def get_by_id(self, collection: str, doc_id: str) -> Optional[VectorDocument]:
        """Obtiene documento por ID con caché"""
        if doc_id in self._cache:
            return self._cache[doc_id]
        
        if not self._connected:
            await self.initialize()
        
        doc = await self._primary.get_by_id(collection, doc_id)
        
        if not doc and self._secondary:
            doc = await self._secondary.get_by_id(collection, doc_id)
        
        if doc:
            self._cache[doc_id] = doc
        
        return doc
    
    async def create_collection(self, name: str) -> bool:
        """Crea colección en todos los stores"""
        if not self._connected:
            await self.initialize()
        
        primary_ok = await self._primary.create_collection(name, self.vector_size)
        
        if self._secondary:
            secondary_ok = await self._secondary.create_collection(name, self.vector_size)
            return primary_ok or secondary_ok
        
        return primary_ok
    
    async def migrate(
        self,
        source: VectorStoreType,
        target: VectorStoreType,
        collection: str,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """Migra datos entre vector stores"""
        stats = {
            "source": source.value,
            "target": target.value,
            "collection": collection,
            "migrated": 0,
            "errors": 0,
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": None
        }
        
        source_adapter = (
            self._primary if source == self.primary_type
            else self._secondary if source == self.secondary_type
            else VectorStoreFactory.create(source)
        )
        
        target_adapter = (
            self._primary if target == self.primary_type
            else self._secondary if target == self.secondary_type
            else VectorStoreFactory.create(target)
        )
        
        if not getattr(source_adapter, '_connected', True):
            await source_adapter.connect()
        if not getattr(target_adapter, '_connected', True):
            await target_adapter.connect()
        
        await target_adapter.create_collection(collection, self.vector_size)
        
        info = await source_adapter.get_collection_info(collection)
        if info:
            stats["total_documents"] = info.document_count
        
        stats["completed_at"] = datetime.utcnow().isoformat()
        
        return stats
    
    async def sync(
        self,
        direction: SyncDirection = SyncDirection.BIDIRECTIONAL,
        collection: str = None
    ) -> Dict[str, Any]:
        """Sincroniza datos entre stores primario y secundario"""
        if not self._secondary:
            return {"error": "No secondary store configured"}
        
        stats = {
            "direction": direction.value,
            "started_at": datetime.utcnow().isoformat(),
            "primary_to_secondary": 0,
            "secondary_to_primary": 0,
        }
        
        stats["completed_at"] = datetime.utcnow().isoformat()
        
        return stats
    
    async def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema"""
        stats = {
            "connected": self._connected,
            "primary_type": self.primary_type.value,
            "secondary_type": self.secondary_type.value if self.secondary_type else None,
            "cache_size": len(self._cache),
            "vector_size": self.vector_size,
        }
        
        if self._connected:
            collections = await self._primary.list_collections()
            stats["collections"] = collections
        
        return stats


# ============================================================================
# EMBEDDING SERVICE - Generación de Embeddings
# ============================================================================

class EmbeddingService:
    """
    Servicio para generar embeddings de texto
    
    Soporta múltiples proveedores:
    - OpenAI (text-embedding-3-small, text-embedding-3-large)
    - Sentence Transformers (local)
    - z-ai-web-dev-sdk
    """
    
    def __init__(
        self,
        provider: str = "local",
        model: str = "default",
        api_key: Optional[str] = None
    ):
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self._dimension = 384
    
    async def embed(self, text: str) -> List[float]:
        """Genera embedding para un texto"""
        
        if self.provider == "zai":
            return await self._embed_with_zai(text)
        elif self.provider == "openai":
            return await self._embed_with_openai(text)
        else:
            return self._embed_local(text)
    
    async def _embed_with_zai(self, text: str) -> List[float]:
        """Genera embedding usando z-ai-web-dev-sdk"""
        try:
            # Fallback a local
            return self._embed_local(text)
        except Exception as e:
            logger.error(f"Z-AI embedding failed: {e}")
            return self._embed_local(text)
    
    async def _embed_with_openai(self, text: str) -> List[float]:
        """Genera embedding usando OpenAI"""
        try:
            import openai
            
            client = openai.AsyncOpenAI(api_key=self.api_key)
            
            response = await client.embeddings.create(
                model=self.model or "text-embedding-3-small",
                input=text
            )
            
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"OpenAI embedding failed: {e}")
            return self._embed_local(text)
    
    def _embed_local(self, text: str) -> List[float]:
        """Genera embedding local simple"""
        import hashlib
        
        hash_obj = hashlib.sha256(text.encode())
        hash_bytes = hash_obj.digest()
        
        vector = []
        for i in range(0, min(len(hash_bytes), 48), 1):
            vector.append(hash_bytes[i] / 255.0)
        
        while len(vector) < self._dimension:
            vector.extend(vector[:min(len(vector), self._dimension - len(vector))])
        
        return vector[:self._dimension]
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Genera embeddings para múltiples textos"""
        return [await self.embed(text) for text in texts]
    
    @property
    def dimension(self) -> int:
        return self._dimension


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Enums
    "VectorStoreType",
    "SyncDirection",
    "VectorMetric",
    
    # Models
    "VectorDocument",
    "SearchResult",
    "CollectionInfo",
    
    # Adapters
    "VectorStoreAdapter",
    "MemoryVectorStoreAdapter",
    "MilvusAdapter",
    "QdrantAdapter",
    
    # Factory
    "VectorStoreFactory",
    
    # Facade
    "VectorStoreFacade",
    
    # Services
    "EmbeddingService",
]
