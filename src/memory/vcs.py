"""
Memory VCS (Version Control System) - Sistema de Memoria con Control de Versiones

Basado en Engram - SQLite con FTS5 para recuperación semántica.

Características:
- Topic Keys y Upserts: Las memorias no se duplican, se versionan
- Divulgación Progresiva: Tres niveles de acceso para proteger contexto
- Independencia del Agente: Memoria agnóstica al modelo de lenguaje
"""

import sqlite3
import json
import hashlib
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import uuid


class DisclosureLevel(str, Enum):
    """Niveles de divulgación progresiva"""
    COMPACT = "compact"      # Solo IDs y relevancia
    TIMELINE = "timeline"    # Línea temporal cronológica
    FULL = "full"           # Contenido completo


@dataclass
class MemoryEntry:
    """Entrada de memoria"""
    id: int
    topic_key: str
    content: str
    metadata: Dict[str, Any]
    revision: int
    created_at: datetime
    updated_at: datetime
    content_hash: str


@dataclass
class MemoryVersion:
    """Versión histórica de una memoria"""
    id: int
    memory_id: int
    version: int
    content: str
    metadata: Dict[str, Any]
    created_at: datetime


class MemoryVCS:
    """
    Sistema de Memoria con Control de Versiones (Memory VCS)
    
    Funciona como un sistema de archivos para el conocimiento del agente,
    basado en SQLite con indexación FTS5 para recuperación semántica.
    
    Usage:
        vcs = MemoryVCS()
        
        # Upsert de memoria
        result = vcs.upsert(
            topic_key="project:routing:conventions",
            content="Use camelCase for routes",
            metadata={"domain": "development"}
        )
        
        # Búsqueda semántica
        results = vcs.search("routing conventions", limit=5)
        
        # Línea temporal
        timeline = vcs.get_timeline("project:routing:conventions")
    """
    
    def __init__(
        self,
        db_path: str = "~/.openclaw/cognitive_capital.db",
        auto_init: bool = True
    ):
        """
        Inicializa el Memory VCS.
        
        Args:
            db_path: Ruta a la base de datos SQLite
            auto_init: Si debe inicializar la BD automáticamente
        """
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        if auto_init:
            self._init_db()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Obtiene conexión a la base de datos"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self):
        """Inicializa la base de datos SQLite con FTS5"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Tabla principal de memorias
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_key TEXT UNIQUE NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                revision INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                content_hash TEXT,
                access_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP,
                cognitive_value INTEGER DEFAULT 1
            )
        ''')
        
        # Índice FTS5 para búsqueda semántica
        cursor.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
                topic_key,
                content,
                metadata,
                content='memories',
                content_rowid='id'
            )
        ''')
        
        # Triggers para mantener FTS sincronizado
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories BEGIN
                INSERT INTO memories_fts(rowid, topic_key, content, metadata)
                VALUES (new.id, new.topic_key, new.content, new.metadata);
            END
        ''')
        
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories BEGIN
                INSERT INTO memories_fts(memories_fts, rowid, topic_key, content, metadata)
                VALUES('delete', old.id, old.topic_key, old.content, old.metadata);
            END
        ''')
        
        cursor.execute('''
            CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories BEGIN
                INSERT INTO memories_fts(memories_fts, rowid, topic_key, content, metadata)
                VALUES('Delete', old.id, old.topic_key, old.content, old.metadata);
                INSERT INTO memories_fts(rowid, topic_key, content, metadata)
                VALUES (new.id, new.topic_key, new.content, new.metadata);
            END
        ''')
        
        # Tabla de versiones (historial)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                memory_id INTEGER NOT NULL,
                version INTEGER NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                change_reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (memory_id) REFERENCES memories(id) ON DELETE CASCADE
            )
        ''')
        
        # Tabla de relaciones entre memorias (grafo de conocimiento)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS memory_relations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id INTEGER NOT NULL,
                target_id INTEGER NOT NULL,
                relation_type TEXT NOT NULL,
                weight REAL DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_id) REFERENCES memories(id),
                FOREIGN KEY (target_id) REFERENCES memories(id)
            )
        ''')
        
        # Índices
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_memories_topic ON memories(topic_key)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_memories_cognitive_value ON memories(cognitive_value DESC)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_memory_versions_memory ON memory_versions(memory_id, version DESC)
        ''')
        
        conn.commit()
        conn.close()
    
    def upsert(
        self,
        topic_key: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        change_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Inserta o actualiza una memoria (upsert con versionado).
        
        - Si la topic_key no existe: crea nueva memoria
        - Si ya existe: incrementa revisión y versiona el contenido anterior
        
        Args:
            topic_key: Clave única temática (ej. "project:routing:conventions")
            content: Contenido de la memoria
            metadata: Metadatos adicionales
            change_reason: Razón del cambio (para historial)
        
        Returns:
            Dict con información de la operación
        """
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        metadata_json = json.dumps(metadata or {})
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Buscar existencia
        cursor.execute(
            "SELECT id, revision, content_hash, content FROM memories WHERE topic_key = ?",
            (topic_key,)
        )
        existing = cursor.fetchone()
        
        if existing:
            memory_id, revision, old_hash, old_content = existing
            
            if old_hash == content_hash:
                # Sin cambios - solo actualizar acceso
                cursor.execute('''
                    UPDATE memories SET
                        access_count = access_count + 1,
                        last_accessed = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (memory_id,))
                
                conn.commit()
                conn.close()
                
                return {
                    "memory_id": memory_id,
                    "topic_key": topic_key,
                    "revision": revision,
                    "operation": "accessed",
                    "changed": False
                }
            
            # Versionar el contenido anterior
            cursor.execute('''
                INSERT INTO memory_versions (memory_id, version, content, metadata, change_reason)
                VALUES (?, ?, ?, ?, ?)
            ''', (memory_id, revision, old_content, 
                  cursor.execute("SELECT metadata FROM memories WHERE id = ?", (memory_id,)).fetchone()[0],
                  change_reason or "Updated via upsert"))
            
            # Actualizar con nuevo contenido
            cursor.execute('''
                UPDATE memories SET
                    content = ?,
                    metadata = ?,
                    revision = revision + 1,
                    updated_at = CURRENT_TIMESTAMP,
                    content_hash = ?,
                    access_count = access_count + 1,
                    last_accessed = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (content, metadata_json, content_hash, memory_id))
            
            revision += 1
            operation = "updated"
        else:
            # Nueva memoria
            cursor.execute('''
                INSERT INTO memories (topic_key, content, metadata, content_hash, last_accessed)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (topic_key, content, metadata_json, content_hash))
            
            memory_id = cursor.lastrowid
            revision = 1
            operation = "created"
        
        conn.commit()
        conn.close()
        
        return {
            "memory_id": memory_id,
            "topic_key": topic_key,
            "revision": revision,
            "operation": operation,
            "changed": True,
            "content_hash": content_hash
        }
    
    def search(
        self,
        query: str,
        limit: int = 10,
        disclosure_level: DisclosureLevel = DisclosureLevel.COMPACT,
        domain_filter: Optional[str] = None,
        min_cognitive_value: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Búsqueda semántica con divulgación progresiva.
        
        Nivel 1 (COMPACT): Solo IDs y relevancia - protege contexto
        Nivel 2 (TIMELINE): Línea temporal cronológica
        Nivel 3 (FULL): Contenido completo
        
        Args:
            query: Query de búsqueda (FTS5 syntax)
            limit: Máximo de resultados
            disclosure_level: Nivel de detalle
            domain_filter: Filtrar por dominio en metadata
            min_cognitive_value: Valor cognitivo mínimo
        
        Returns:
            Lista de memorias encontradas
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Sanitizar query para FTS5
        fts_query = query.replace("'", "''")
        
        results = []
        
        if disclosure_level == DisclosureLevel.COMPACT:
            # Nivel 1: Solo IDs y relevancia
            sql = '''
                SELECT m.id, m.topic_key, m.revision, m.cognitive_value
                FROM memories m
                JOIN memories_fts fts ON m.id = fts.rowid
                WHERE memories_fts MATCH ?
                AND m.cognitive_value >= ?
                ORDER BY bm25(memories_fts) ASC
                LIMIT ?
            '''
            cursor.execute(sql, (fts_query, min_cognitive_value, limit))
            
            for row in cursor.fetchall():
                results.append({
                    "id": row["id"],
                    "topic_key": row["topic_key"],
                    "revision": row["revision"],
                    "cognitive_value": row["cognitive_value"],
                    "disclosure_level": "compact"
                })
        
        elif disclosure_level == DisclosureLevel.TIMELINE:
            # Nivel 2: Línea temporal
            sql = '''
                SELECT m.id, m.topic_key, m.revision, m.created_at, m.updated_at,
                       m.cognitive_value, m.access_count
                FROM memories m
                JOIN memories_fts fts ON m.id = fts.rowid
                WHERE memories_fts MATCH ?
                AND m.cognitive_value >= ?
                ORDER BY bm25(memories_fts) ASC
                LIMIT ?
            '''
            cursor.execute(sql, (fts_query, min_cognitive_value, limit))
            
            for row in cursor.fetchall():
                results.append({
                    "id": row["id"],
                    "topic_key": row["topic_key"],
                    "revision": row["revision"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "cognitive_value": row["cognitive_value"],
                    "access_count": row["access_count"],
                    "disclosure_level": "timeline"
                })
        
        else:
            # Nivel 3: Contenido completo
            sql = '''
                SELECT m.*
                FROM memories m
                JOIN memories_fts fts ON m.id = fts.rowid
                WHERE memories_fts MATCH ?
                AND m.cognitive_value >= ?
                ORDER BY bm25(memories_fts) ASC
                LIMIT ?
            '''
            cursor.execute(sql, (fts_query, min_cognitive_value, limit))
            
            for row in cursor.fetchall():
                results.append({
                    "id": row["id"],
                    "topic_key": row["topic_key"],
                    "content": row["content"],
                    "metadata": json.loads(row["metadata"] or '{}'),
                    "revision": row["revision"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                    "cognitive_value": row["cognitive_value"],
                    "access_count": row["access_count"],
                    "disclosure_level": "full"
                })
        
        # Filtrar por dominio si especificado
        if domain_filter:
            results = [
                r for r in results
                if json.loads(self._get_metadata(r["id"], conn) or '{}').get('domain') == domain_filter
            ]
        
        conn.close()
        return results
    
    def _get_metadata(self, memory_id: int, conn: sqlite3.Connection) -> Optional[str]:
        """Obtiene metadata de una memoria"""
        cursor = conn.cursor()
        cursor.execute("SELECT metadata FROM memories WHERE id = ?", (memory_id,))
        row = cursor.fetchone()
        return row["metadata"] if row else None
    
    def get_by_key(self, topic_key: str) -> Optional[Dict[str, Any]]:
        """Obtiene una memoria por su topic_key"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM memories WHERE topic_key = ?
        ''', (topic_key,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "id": row["id"],
                "topic_key": row["topic_key"],
                "content": row["content"],
                "metadata": json.loads(row["metadata"] or '{}'),
                "revision": row["revision"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "cognitive_value": row["cognitive_value"],
                "access_count": row["access_count"]
            }
        return None
    
    def get_timeline(self, topic_key: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Obtiene la línea temporal de versiones de una memoria.
        
        Args:
            topic_key: Clave de la memoria
            limit: Máximo de versiones a retornar
        
        Returns:
            Lista de versiones ordenadas cronológicamente
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT mv.version, mv.content, mv.metadata, mv.change_reason, mv.created_at
            FROM memory_versions mv
            JOIN memories m ON mv.memory_id = m.id
            WHERE m.topic_key = ?
            ORDER BY mv.version DESC
            LIMIT ?
        ''', (topic_key, limit))
        
        timeline = []
        for row in cursor.fetchall():
            timeline.append({
                "version": row["version"],
                "content": row["content"],
                "metadata": json.loads(row["metadata"] or '{}'),
                "change_reason": row["change_reason"],
                "created_at": row["created_at"]
            })
        
        conn.close()
        return timeline
    
    def add_relation(
        self,
        source_key: str,
        target_key: str,
        relation_type: str = "related_to",
        weight: float = 1.0
    ) -> Dict[str, Any]:
        """
        Añade una relación entre dos memorias (grafo de conocimiento).
        
        Args:
            source_key: Topic key de la memoria origen
            target_key: Topic key de la memoria destino
            relation_type: Tipo de relación
            weight: Peso de la relación
        
        Returns:
            Dict con información de la relación creada
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Obtener IDs
        cursor.execute("SELECT id FROM memories WHERE topic_key = ?", (source_key,))
        source_row = cursor.fetchone()
        
        cursor.execute("SELECT id FROM memories WHERE topic_key = ?", (target_key,))
        target_row = cursor.fetchone()
        
        if not source_row or not target_row:
            conn.close()
            return {"error": "Source or target memory not found"}
        
        source_id = source_row["id"]
        target_id = target_row["id"]
        
        cursor.execute('''
            INSERT OR REPLACE INTO memory_relations (source_id, target_id, relation_type, weight)
            VALUES (?, ?, ?, ?)
        ''', (source_id, target_id, relation_type, weight))
        
        conn.commit()
        conn.close()
        
        return {
            "source": source_key,
            "target": target_key,
            "relation_type": relation_type,
            "weight": weight
        }
    
    def get_related(
        self,
        topic_key: str,
        relation_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Obtiene memorias relacionadas"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        if relation_type:
            cursor.execute('''
                SELECT m.topic_key, mr.relation_type, mr.weight
                FROM memory_relations mr
                JOIN memories m ON mr.target_id = m.id
                WHERE mr.source_id = (SELECT id FROM memories WHERE topic_key = ?)
                AND mr.relation_type = ?
                ORDER BY mr.weight DESC
            ''', (topic_key, relation_type))
        else:
            cursor.execute('''
                SELECT m.topic_key, mr.relation_type, mr.weight
                FROM memory_relations mr
                JOIN memories m ON mr.target_id = m.id
                WHERE mr.source_id = (SELECT id FROM memories WHERE topic_key = ?)
                ORDER BY mr.weight DESC
            ''', (topic_key,))
        
        related = [
            {
                "topic_key": row["topic_key"],
                "relation_type": row["relation_type"],
                "weight": row["weight"]
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        return related
    
    def delete(self, topic_key: str) -> bool:
        """Elimina una memoria y su historial"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM memories WHERE topic_key = ?", (topic_key,))
        deleted = cursor.rowcount > 0
        
        conn.commit()
        conn.close()
        
        return deleted
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del Memory VCS"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        cursor.execute("SELECT COUNT(*) as count FROM memories")
        stats["total_memories"] = cursor.fetchone()["count"]
        
        cursor.execute("SELECT COUNT(*) as count FROM memory_versions")
        stats["total_versions"] = cursor.fetchone()["count"]
        
        cursor.execute("SELECT COUNT(*) as count FROM memory_relations")
        stats["total_relations"] = cursor.fetchone()["count"]
        
        cursor.execute("SELECT SUM(cognitive_value) as total FROM memories")
        stats["total_cognitive_capital"] = cursor.fetchone()["total"] or 0
        
        cursor.execute('''
            SELECT topic_key FROM memories 
            ORDER BY access_count DESC 
            LIMIT 5
        ''')
        stats["top_accessed"] = [row["topic_key"] for row in cursor.fetchall()]
        
        conn.close()
        return stats


# Singleton global
_memory_vcs: Optional[MemoryVCS] = None


def get_memory_vcs(db_path: Optional[str] = None) -> MemoryVCS:
    """Obtiene la instancia singleton del Memory VCS"""
    global _memory_vcs
    if _memory_vcs is None:
        _memory_vcs = MemoryVCS(db_path) if db_path else MemoryVCS()
    return _memory_vcs


def reset_memory_vcs():
    """Reset del singleton (útil para tests)"""
    global _memory_vcs
    _memory_vcs = None
