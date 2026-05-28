"""
Engram Store - Almacén de Memoria

Interfaz de alto nivel para almacenar y recuperar memorias.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging
import sqlite3
from contextlib import contextmanager

from .vcs import MemoryVCS, DisclosureLevel

logger = logging.getLogger(__name__)


@dataclass
class EngramQuery:
    """
    Query para buscar engrams.
    
    Define los parámetros de búsqueda de memorias.
    """
    query: str
    limit: int = 10
    disclosure_level: DisclosureLevel = DisclosureLevel.COMPACT
    min_cognitive_value: int = 0
    tags: List[str] = field(default_factory=list)
    domain: Optional[str] = None
    agent_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.query,
            "limit": self.limit,
            "disclosure_level": self.disclosure_level.value,
            "min_cognitive_value": self.min_cognitive_value,
            "tags": self.tags,
            "domain": self.domain,
            "agent_id": self.agent_id
        }


class EngramStore:
    """
    Almacén de memoria de alto nivel.
    
    Proporciona una API simplificada para gestionar engrams
    (unidades de memoria cognitiva).
    """
    
    def __init__(self, vcs: Optional[MemoryVCS] = None, db_path: Optional[str] = None):
        self._vcs = vcs or MemoryVCS(db_path=db_path or "~/.ricco-ai/engram.db")
    
    def remember(
        self,
        topic: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Almacena un nuevo recuerdo (engram).
        
        Args:
            topic: Identificador temático único
            content: Contenido del recuerdo
            metadata: Metadatos adicionales
            tags: Etiquetas para categorización
        
        Returns:
            Resultado de la operación
        """
        full_metadata = metadata or {}
        if tags:
            full_metadata["tags"] = tags
        
        return self._vcs.upsert(
            topic_key=topic,
            content=content,
            metadata=full_metadata
        )
    
    def recall(
        self,
        query: str,
        full_content: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Recupera memorias relacionadas con una query.
        
        Args:
            query: Término de búsqueda
            full_content: Si incluir contenido completo
        
        Returns:
            Lista de memorias encontradas
        """
        level = DisclosureLevel.FULL if full_content else DisclosureLevel.COMPACT
        return self._vcs.search(query, disclosure_level=level)
    
    def recall_by_topic(self, topic: str) -> Optional[Dict[str, Any]]:
        """Recupera una memoria específica por su topic"""
        return self._vcs.get_by_key(topic)
    
    def forget(self, topic: str) -> bool:
        """Elimina una memoria"""
        return self._vcs.delete(topic)
    
    def relate(
        self,
        source_topic: str,
        target_topic: str,
        relation: str = "related_to",
        strength: float = 1.0
    ) -> Dict[str, Any]:
        """
        Crea una relación entre dos memorias.
        
        Args:
            source_topic: Topic de la memoria origen
            target_topic: Topic de la memoria destino
            relation: Tipo de relación
            strength: Fuerza de la relación (0-1)
        
        Returns:
            Resultado de la operación
        """
        return self._vcs.add_relation(
            source_key=source_topic,
            target_key=target_topic,
            relation_type=relation,
            weight=strength
        )
    
    def get_related_memories(
        self,
        topic: str,
        relation_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Obtiene memorias relacionadas"""
        return self._vcs.get_related(topic, relation_type)
    
    def get_history(self, topic: str) -> List[Dict[str, Any]]:
        """Obtiene el historial de versiones de una memoria"""
        return self._vcs.get_timeline(topic)
    
    def get_value(self) -> int:
        """Obtiene el valor cognitivo total almacenado"""
        stats = self._vcs.get_stats()
        return stats.get("total_cognitive_capital", 0)
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del almacén"""
        return self._vcs.get_stats()
    
    # Métodos de conveniencia para agentes
    
    def store_interaction(
        self,
        agent_id: str,
        interaction_type: str,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Almacena una interacción del agente.
        
        Crea un engram con formato estandarizado para interacciones.
        """
        topic = f"agent:{agent_id}:interaction:{interaction_type}:{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        metadata = {
            "agent_id": agent_id,
            "interaction_type": interaction_type,
            "context": context or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return self.remember(topic, content, metadata)
    
    def store_learning(
        self,
        agent_id: str,
        learning_type: str,
        content: str,
        importance: int = 1
    ) -> Dict[str, Any]:
        """
        Almacena un aprendizaje del agente.
        
        Los aprendizajes tienen mayor valor cognitivo.
        """
        topic = f"agent:{agent_id}:learning:{learning_type}"
        
        metadata = {
            "agent_id": agent_id,
            "learning_type": learning_type,
            "importance": importance,
            "stored_at": datetime.utcnow().isoformat()
        }
        
        # Usar upsert directo para setear cognitive_value
        result = self._vcs.upsert(topic, content, metadata)
        
        # Actualizar cognitive_value
        if result.get("memory_id"):
            self._update_cognitive_value(result["memory_id"], importance * 10)
        
        return result
    
    def _update_cognitive_value(self, memory_id: int, value: int) -> None:
        """
        Actualiza el valor cognitivo de una memoria.
        
        El valor cognitivo representa la importancia acumulada de una memoria
        en el sistema cognitivo del agente. Los aprendizajes importantes
        tienen mayor valor, mientras que interacciones rutinarias tienen menos.
        
        Args:
            memory_id: ID de la memoria a actualizar
            value: Incremento de valor cognitivo (puede ser negativo)
        """
        # Intentar múltiples formas de obtener la conexión
        conn = None
        
        if hasattr(self._vcs, '_conn'):
            conn = self._vcs._conn
        elif hasattr(self._vcs, '_get_connection'):
            try:
                conn = self._vcs._get_connection()
            except Exception as e:
                logger.warning(f"Could not get VCS connection: {e}")
        
        if conn is None:
            logger.warning("VCS does not support direct cognitive value update")
            return
        
        try:
            cursor = conn.cursor()
            
            # Verificar que la memoria existe
            cursor.execute(
                "SELECT id, cognitive_value FROM memories WHERE id = ?",
                (memory_id,)
            )
            row = cursor.fetchone()
            
            if row is None:
                logger.warning(f"Memory with id {memory_id} not found")
                return
            
            current_value = row[1] or 0
            new_value = max(0, current_value + value)  # No permitir valores negativos
            
            cursor.execute(
                "UPDATE memories SET cognitive_value = ?, last_accessed = ? WHERE id = ?",
                (new_value, datetime.utcnow().isoformat(), memory_id)
            )
            conn.commit()
            
            logger.debug(
                f"Updated cognitive value for memory {memory_id}: {current_value} -> {new_value}"
            )
        except Exception as e:
            logger.warning(f"Could not update cognitive value: {e}")
    
    def get_cognitive_capital(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Calcula el capital cognitivo total del sistema.
        
        Args:
            agent_id: Si se proporciona, filtra por agente específico
            
        Returns:
            Diccionario con estadísticas de capital cognitivo
        """
        stats = self.get_stats()
        
        result = {
            "total_memories": stats.get("total_memories", 0),
            "total_cognitive_capital": stats.get("total_cognitive_capital", 0),
            "average_value": 0,
            "high_value_memories": 0,
            "learning_memories": 0,
        }
        
        if result["total_memories"] > 0:
            result["average_value"] = result["total_cognitive_capital"] / result["total_memories"]
        
        return result
    
    @contextmanager
    def transaction(self):
        """Context manager para transacciones de base de datos."""
        conn = None
        if hasattr(self._vcs, '_conn'):
            conn = self._vcs._conn
        elif hasattr(self._vcs, '_get_connection'):
            try:
                conn = self._vcs._get_connection()
            except Exception:
                pass
        
        if conn:
            try:
                yield conn
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        else:
            yield None
    
    def search_agent_memories(
        self,
        agent_id: str,
        query: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Busca memorias de un agente específico"""
        results = self.recall(f"agent:{agent_id} {query}", full_content=True)
        return [
            r for r in results 
            if r.get("metadata", {}).get("agent_id") == agent_id
        ][:limit]
