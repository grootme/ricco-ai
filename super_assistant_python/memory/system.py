"""
Super Asistente Cognitivo - Sistema de Memoria
==============================================

Sistema de memoria persistente multi-capa:
- Memoria de Sesión (corto plazo): SQLite
- Memoria Episódica (mediano plazo): Cache/Redis
- Memoria Semántica (largo plazo): Milvus (vectores)
- Memoria Procedural/Declarativa: Neo4j (grafos)
"""

import asyncio
import json
import sqlite3
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

import numpy as np
from pydantic import BaseModel

from ..core.models import Memory, MemoryType
from ..core.config import settings


# ============================================
# EMBEDDING PROVIDER
# ============================================

class EmbeddingProvider(ABC):
    """Proveedor de embeddings abstracto"""
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Generar embedding para un texto"""
        pass
    
    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generar embeddings para múltiples textos"""
        pass


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """Proveedor de embeddings usando OpenAI"""
    
    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        self.api_key = api_key
        self.model = model
        self._client = None
    
    async def _get_client(self):
        if self._client is None:
            import openai
            self._client = openai.AsyncOpenAI(api_key=self.api_key)
        return self._client
    
    async def embed(self, text: str) -> List[float]:
        client = await self._get_client()
        response = await client.embeddings.create(
            input=text,
            model=self.model
        )
        return response.data[0].embedding
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        client = await self._get_client()
        response = await client.embeddings.create(
            input=texts,
            model=self.model
        )
        return [d.embedding for d in response.data]


class LocalEmbeddingProvider(EmbeddingProvider):
    """Proveedor de embeddings local usando sentence-transformers"""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
    
    def _get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self.model_name)
        return self._model
    
    async def embed(self, text: str) -> List[float]:
        model = self._get_model()
        embedding = model.encode(text)
        return embedding.tolist()
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        model = self._get_model()
        embeddings = model.encode(texts)
        return embeddings.tolist()


# ============================================
# MEMORY STORE BASE
# ============================================

class MemoryStore(ABC):
    """Almacén de memoria abstracto"""
    
    @abstractmethod
    async def store(self, memory: Memory) -> UUID:
        """Almacenar una memoria"""
        pass
    
    @abstractmethod
    async def retrieve(self, memory_id: UUID) -> Optional[Memory]:
        """Recuperar una memoria por ID"""
        pass
    
    @abstractmethod
    async def search(
        self, 
        query: str, 
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Memory]:
        """Buscar memorias"""
        pass
    
    @abstractmethod
    async def delete(self, memory_id: UUID) -> bool:
        """Eliminar una memoria"""
        pass
    
    @abstractmethod
    async def update(self, memory_id: UUID, data: Dict[str, Any]) -> bool:
        """Actualizar una memoria"""
        pass


# ============================================
# SQLITE MEMORY STORE (Session/Short-term)
# ============================================

class SQLiteMemoryStore(MemoryStore):
    """
    Almacén de memoria en SQLite para memorias de sesión y episódicas.
    
    Rápido acceso local, ideal para contexto activo.
    """
    
    def __init__(self, db_path: str = "data/memory.db"):
        self.db_path = db_path
        self._initialized = False
    
    async def _init_db(self):
        """Inicializar la base de datos"""
        if self._initialized:
            return
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                type TEXT NOT NULL,
                category TEXT,
                key TEXT,
                content TEXT NOT NULL,
                embedding BLOB,
                importance REAL DEFAULT 0.5,
                access_count INTEGER DEFAULT 0,
                last_accessed_at TEXT,
                expires_at TEXT,
                session_id TEXT,
                source_type TEXT,
                source_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_id ON memories(agent_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_type ON memories(type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_id ON memories(session_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_key ON memories(key)
        """)
        
        conn.commit()
        conn.close()
        
        self._initialized = True
    
    async def store(self, memory: Memory) -> UUID:
        """Almacenar una memoria"""
        await self._init_db()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        embedding_blob = None
        if memory.embedding:
            embedding_blob = np.array(memory.embedding, dtype=np.float32).tobytes()
        
        cursor.execute("""
            INSERT OR REPLACE INTO memories 
            (id, agent_id, type, category, key, content, embedding, 
             importance, access_count, last_accessed_at, expires_at,
             session_id, source_type, source_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(memory.id),
            str(memory.agent_id),
            memory.type.value,
            memory.category,
            memory.key,
            memory.content,
            embedding_blob,
            memory.importance,
            memory.access_count,
            memory.last_accessed_at.isoformat() if memory.last_accessed_at else None,
            memory.expires_at.isoformat() if memory.expires_at else None,
            str(memory.session_id) if memory.session_id else None,
            memory.source_type,
            memory.source_id,
            memory.created_at.isoformat(),
            memory.updated_at.isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        return memory.id
    
    async def retrieve(self, memory_id: UUID) -> Optional[Memory]:
        """Recuperar una memoria por ID"""
        await self._init_db()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, agent_id, type, category, key, content, embedding,
                   importance, access_count, last_accessed_at, expires_at,
                   session_id, source_type, source_id, created_at, updated_at
            FROM memories WHERE id = ?
        """, (str(memory_id),))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return self._row_to_memory(row)
    
    async def search(
        self, 
        query: str, 
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Memory]:
        """Buscar memorias por contenido (búsqueda text simple)"""
        await self._init_db()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        sql = """
            SELECT id, agent_id, type, category, key, content, embedding,
                   importance, access_count, last_accessed_at, expires_at,
                   session_id, source_type, source_id, created_at, updated_at
            FROM memories WHERE content LIKE ?
        """
        params = [f"%{query}%"]
        
        if filters:
            if "agent_id" in filters:
                sql += " AND agent_id = ?"
                params.append(str(filters["agent_id"]))
            if "type" in filters:
                sql += " AND type = ?"
                params.append(filters["type"].value if hasattr(filters["type"], "value") else filters["type"])
            if "session_id" in filters:
                sql += " AND session_id = ?"
                params.append(str(filters["session_id"]))
        
        sql += f" ORDER BY importance DESC, created_at DESC LIMIT {limit}"
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_memory(row) for row in rows]
    
    async def delete(self, memory_id: UUID) -> bool:
        """Eliminar una memoria"""
        await self._init_db()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM memories WHERE id = ?", (str(memory_id),))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted
    
    async def update(self, memory_id: UUID, data: Dict[str, Any]) -> bool:
        """Actualizar una memoria"""
        await self._init_db()
        
        if not data:
            return False
        
        set_clauses = []
        params = []
        
        for key, value in data.items():
            if key in ["content", "importance", "access_count", "last_accessed_at", "expires_at"]:
                set_clauses.append(f"{key} = ?")
                if isinstance(value, datetime):
                    params.append(value.isoformat())
                else:
                    params.append(value)
        
        if not set_clauses:
            return False
        
        set_clauses.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())
        
        params.append(str(memory_id))
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        sql = f"UPDATE memories SET {', '.join(set_clauses)} WHERE id = ?"
        cursor.execute(sql, params)
        updated = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return updated
    
    async def get_session_memories(
        self, 
        session_id: UUID,
        limit: int = 50
    ) -> List[Memory]:
        """Obtener todas las memorias de una sesión"""
        await self._init_db()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, agent_id, type, category, key, content, embedding,
                   importance, access_count, last_accessed_at, expires_at,
                   session_id, source_type, source_id, created_at, updated_at
            FROM memories 
            WHERE session_id = ? AND type = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (str(session_id), MemoryType.SESSION.value, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [self._row_to_memory(row) for row in rows]
    
    async def cleanup_expired(self) -> int:
        """Limpiar memorias expiradas"""
        await self._init_db()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.utcnow().isoformat()
        
        cursor.execute("""
            DELETE FROM memories 
            WHERE expires_at IS NOT NULL AND expires_at < ?
        """, (now,))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        return deleted
    
    def _row_to_memory(self, row: tuple) -> Memory:
        """Convertir fila de BD a modelo Memory"""
        embedding = None
        if row[6]:
            embedding = np.frombuffer(row[6], dtype=np.float32).tolist()
        
        return Memory(
            id=UUID(row[0]),
            agent_id=UUID(row[1]),
            type=MemoryType(row[2]),
            category=row[3],
            key=row[4],
            content=row[5],
            embedding=embedding,
            importance=row[7],
            access_count=row[8],
            last_accessed_at=datetime.fromisoformat(row[9]) if row[9] else None,
            expires_at=datetime.fromisoformat(row[10]) if row[10] else None,
            session_id=UUID(row[11]) if row[11] else None,
            source_type=row[12],
            source_id=row[13],
            created_at=datetime.fromisoformat(row[14]),
            updated_at=datetime.fromisoformat(row[15]),
        )


# ============================================
# VECTOR MEMORY STORE (Semantic/Long-term)
# ============================================

class VectorMemoryStore(MemoryStore):
    """
    Almacén de memoria vectorial para búsqueda semántica.
    
    Usa Milvus para almacenamiento de embeddings y búsqueda vectorial.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 19530,
        collection_name: str = "cognitive_memory",
        embedding_provider: Optional[EmbeddingProvider] = None
    ):
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.embedding_provider = embedding_provider
        self._collection = None
    
    async def _get_collection(self):
        """Obtener o crear colección en Milvus"""
        if self._collection is not None:
            return self._collection
        
        try:
            from pymilvus import Collection, connections, FieldSchema, CollectionSchema, DataType
            
            connections.connect("default", host=self.host, port=self.port)
            
            fields = [
                FieldSchema(name="id", dtype=DataType.VARCHAR, max_length=36, is_primary=True),
                FieldSchema(name="agent_id", dtype=DataType.VARCHAR, max_length=36),
                FieldSchema(name="type", dtype=DataType.VARCHAR, max_length=20),
                FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1536),
                FieldSchema(name="importance", dtype=DataType.FLOAT),
                FieldSchema(name="created_at", dtype=DataType.INT64),
            ]
            
            schema = CollectionSchema(fields=fields, description="Cognitive Memory")
            
            self._collection = Collection(self.collection_name, schema)
            
            # Crear índice para búsqueda vectorial
            index_params = {
                "metric_type": "COSINE",
                "index_type": "IVF_FLAT",
                "params": {"nlist": 1024}
            }
            self._collection.create_index("embedding", index_params)
            
            return self._collection
            
        except ImportError:
            raise RuntimeError("pymilvus is required for VectorMemoryStore")
        except Exception as e:
            raise RuntimeError(f"Failed to connect to Milvus: {e}")
    
    async def store(self, memory: Memory) -> UUID:
        """Almacenar una memoria con embedding"""
        collection = await self._get_collection()
        
        # Generar embedding si no existe
        if not memory.embedding and self.embedding_provider:
            memory.embedding = await self.embedding_provider.embed(memory.content)
        
        if not memory.embedding:
            raise ValueError("Memory must have embedding for vector store")
        
        data = [
            [str(memory.id)],
            [str(memory.agent_id)],
            [memory.type.value],
            [memory.content],
            [memory.embedding],
            [memory.importance],
            [int(memory.created_at.timestamp())]
        ]
        
        collection.insert(data)
        collection.flush()
        
        return memory.id
    
    async def retrieve(self, memory_id: UUID) -> Optional[Memory]:
        """Recuperar una memoria por ID"""
        collection = await self._get_collection()
        
        collection.load()
        results = collection.query(
            expr=f'id == "{str(memory_id)}"',
            output_fields=["id", "agent_id", "type", "content", "embedding", "importance", "created_at"]
        )
        
        if not results:
            return None
        
        return self._result_to_memory(results[0])
    
    async def search(
        self, 
        query: str, 
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Memory]:
        """Búsqueda semántica por similitud vectorial"""
        collection = await self._get_collection()
        
        if not self.embedding_provider:
            raise ValueError("Embedding provider required for semantic search")
        
        # Generar embedding de la query
        query_embedding = await self.embedding_provider.embed(query)
        
        # Construir filtro
        filter_expr = None
        if filters:
            conditions = []
            if "agent_id" in filters:
                conditions.append(f'agent_id == "{str(filters["agent_id"])}"')
            if "type" in filters:
                type_val = filters["type"].value if hasattr(filters["type"], "value") else filters["type"]
                conditions.append(f'type == "{type_val}"')
            if conditions:
                filter_expr = " and ".join(conditions)
        
        collection.load()
        
        search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}
        
        results = collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=limit,
            expr=filter_expr,
            output_fields=["id", "agent_id", "type", "content", "importance", "created_at"]
        )
        
        memories = []
        for hits in results:
            for hit in hits:
                memories.append(self._result_to_memory(hit.entity))
        
        return memories
    
    async def delete(self, memory_id: UUID) -> bool:
        """Eliminar una memoria"""
        collection = await self._get_collection()
        
        collection.delete(f'id == "{str(memory_id)}"')
        collection.flush()
        
        return True
    
    async def update(self, memory_id: UUID, data: Dict[str, Any]) -> bool:
        """Actualizar una memoria (delete + insert)"""
        # Milvus no soporta update directo
        # Obtenemos, modificamos y reinsertamos
        memory = await self.retrieve(memory_id)
        if not memory:
            return False
        
        # Actualizar campos
        for key, value in data.items():
            if hasattr(memory, key):
                setattr(memory, key, value)
        
        memory.updated_at = datetime.utcnow()
        
        # Regenerar embedding si cambió el contenido
        if "content" in data and self.embedding_provider:
            memory.embedding = await self.embedding_provider.embed(memory.content)
        
        # Eliminar y reinsertar
        await self.delete(memory_id)
        await self.store(memory)
        
        return True
    
    def _result_to_memory(self, result: dict) -> Memory:
        """Convertir resultado de Milvus a modelo Memory"""
        return Memory(
            id=UUID(result.get("id")),
            agent_id=UUID(result.get("agent_id")),
            type=MemoryType(result.get("type")),
            content=result.get("content"),
            embedding=result.get("embedding"),
            importance=result.get("importance", 0.5),
            created_at=datetime.fromtimestamp(result.get("created_at", 0)),
            updated_at=datetime.utcnow(),
        )


# ============================================
# UNIFIED MEMORY SYSTEM
# ============================================

class CognitiveMemorySystem:
    """
    Sistema de memoria cognitivo unificado.
    
    Coordina múltiples capas de memoria:
    - SQLite: Memoria de sesión y episódica
    - Milvus: Memoria semántica (vectorial)
    - Neo4j: Memoria procedural y declarativa (grafo)
    """
    
    def __init__(
        self,
        sqlite_store: Optional[SQLiteMemoryStore] = None,
        vector_store: Optional[VectorMemoryStore] = None,
        embedding_provider: Optional[EmbeddingProvider] = None
    ):
        self.session_store = sqlite_store or SQLiteMemoryStore()
        self.vector_store = vector_store
        self.embedding_provider = embedding_provider
    
    async def remember(
        self,
        agent_id: UUID,
        content: str,
        memory_type: MemoryType = MemoryType.SEMANTIC,
        session_id: Optional[UUID] = None,
        importance: float = 0.5,
        expires_in: Optional[int] = None
    ) -> Memory:
        """
        Almacenar un nuevo recuerdo.
        
        Args:
            agent_id: ID del agente que recuerda
            content: Contenido del recuerdo
            memory_type: Tipo de memoria
            session_id: ID de sesión (para memoria de sesión)
            importance: Importancia del recuerdo (0-1)
            expires_in: Tiempo de expiración en segundos
            
        Returns:
            La memoria creada
        """
        now = datetime.utcnow()
        expires_at = None
        if expires_in:
            expires_at = now + timedelta(seconds=expires_in)
        
        memory = Memory(
            id=uuid4(),
            agent_id=agent_id,
            type=memory_type,
            content=content,
            importance=importance,
            session_id=session_id,
            expires_at=expires_at,
            created_at=now,
            updated_at=now
        )
        
        # Almacenar según tipo
        if memory_type in [MemoryType.SESSION, MemoryType.EPISODIC]:
            await self.session_store.store(memory)
        elif memory_type == MemoryType.SEMANTIC:
            if self.vector_store:
                await self.vector_store.store(memory)
            else:
                # Fallback a SQLite si no hay vector store
                await self.session_store.store(memory)
        
        return memory
    
    async def recall(
        self,
        query: str,
        agent_id: Optional[UUID] = None,
        session_id: Optional[UUID] = None,
        limit: int = 10
    ) -> List[Memory]:
        """
        Recuperar recuerdos relevantes.
        
        Busca en todas las capas de memoria y combina resultados.
        """
        filters = {}
        if agent_id:
            filters["agent_id"] = agent_id
        if session_id:
            filters["session_id"] = session_id
        
        results = []
        
        # Buscar en memoria de sesión
        session_results = await self.session_store.search(query, limit, filters)
        results.extend(session_results)
        
        # Buscar en memoria semántica (vectorial)
        if self.vector_store:
            semantic_results = await self.vector_store.search(query, limit, filters)
            results.extend(semantic_results)
        
        # Deduplicar y ordenar por importancia
        seen_ids = set()
        unique_results = []
        for memory in results:
            if memory.id not in seen_ids:
                seen_ids.add(memory.id)
                unique_results.append(memory)
        
        unique_results.sort(key=lambda m: m.importance, reverse=True)
        
        return unique_results[:limit]
    
    async def forget(self, memory_id: UUID, memory_type: MemoryType) -> bool:
        """Olvidar (eliminar) un recuerdo"""
        if memory_type in [MemoryType.SESSION, MemoryType.EPISODIC]:
            return await self.session_store.delete(memory_id)
        elif memory_type == MemoryType.SEMANTIC and self.vector_store:
            return await self.vector_store.delete(memory_id)
        return False
    
    async def consolidate(
        self,
        session_id: UUID,
        agent_id: UUID
    ) -> List[Memory]:
        """
        Consolidar memorias de sesión en memoria semántica.
        
        Transfiere recuerdos importantes de la sesión actual
        a la memoria de largo plazo.
        """
        # Obtener memorias de sesión
        session_memories = await self.session_store.get_session_memories(session_id)
        
        consolidated = []
        
        for memory in session_memories:
            # Solo consolidar memorias importantes
            if memory.importance >= 0.7:
                # Crear memoria semántica
                semantic_memory = Memory(
                    id=uuid4(),
                    agent_id=agent_id,
                    type=MemoryType.SEMANTIC,
                    content=memory.content,
                    importance=memory.importance,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                if self.vector_store:
                    await self.vector_store.store(semantic_memory)
                    consolidated.append(semantic_memory)
        
        return consolidated
    
    async def cleanup(self) -> Dict[str, int]:
        """Limpiar memorias expiradas"""
        deleted = await self.session_store.cleanup_expired()
        return {"deleted_count": deleted}
