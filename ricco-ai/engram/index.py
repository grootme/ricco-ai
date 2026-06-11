"""
Engram Index - Sistema de Indexación

Indexación avanzada para búsqueda eficiente de memorias.
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class IndexType(str, Enum):
    """Tipos de índice"""
    TAG = "tag"
    DOMAIN = "domain"
    AGENT = "agent"
    TEMPORAL = "temporal"
    SEMANTIC = "semantic"


@dataclass
class IndexConfig:
    """Configuración del índice"""
    name: str
    index_type: IndexType
    fields: List[str]
    unique: bool = False
    auto_update: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "index_type": self.index_type.value,
            "fields": self.fields,
            "unique": self.unique,
            "auto_update": self.auto_update
        }


@dataclass
class IndexEntry:
    """Entrada del índice"""
    key: str
    value: str
    memory_ids: Set[int] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


class MemoryIndex:
    """
    Sistema de indexación para memorias.
    
    Mantiene índices invertidos para búsqueda rápida por
    tags, dominios, agentes y otros campos.
    """
    
    def __init__(self, config: Optional[IndexConfig] = None):
        self._indices: Dict[str, Dict[str, IndexEntry]] = {}
        self._configs: Dict[str, IndexConfig] = {}
        
        # Cargar configuración por defecto
        self._load_default_configs()
    
    def _load_default_configs(self) -> None:
        """Carga configuraciones de índice por defecto"""
        default_configs = [
            IndexConfig(
                name="tags",
                index_type=IndexType.TAG,
                fields=["metadata.tags"]
            ),
            IndexConfig(
                name="domain",
                index_type=IndexType.DOMAIN,
                fields=["metadata.domain"]
            ),
            IndexConfig(
                name="agent",
                index_type=IndexType.AGENT,
                fields=["metadata.agent_id"]
            ),
            IndexConfig(
                name="temporal",
                index_type=IndexType.TEMPORAL,
                fields=["created_at", "updated_at"]
            ),
        ]
        
        for config in default_configs:
            self.create_index(config)
    
    def create_index(self, config: IndexConfig) -> None:
        """Crea un nuevo índice"""
        self._configs[config.name] = config
        self._indices[config.name] = {}
        logger.info(f"Index created: {config.name} ({config.index_type.value})")
    
    def index_memory(self, memory: Dict[str, Any]) -> None:
        """
        Indexa una memoria en todos los índices aplicables.
        
        Args:
            memory: Diccionario con los datos de la memoria
        """
        memory_id = memory.get("id")
        if not memory_id:
            return
        
        for index_name, config in self._configs.items():
            if not config.auto_update:
                continue
            
            # Extraer valores de los campos
            for field in config.fields:
                value = self._extract_field_value(memory, field)
                
                if value:
                    if isinstance(value, list):
                        for v in value:
                            self._add_to_index(index_name, str(v), memory_id)
                    else:
                        self._add_to_index(index_name, str(value), memory_id)
    
    def _extract_field_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """Extrae valor de un campo anidado"""
        parts = field_path.split(".")
        current = data
        
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                return None
            
            if current is None:
                return None
        
        return current
    
    def _add_to_index(self, index_name: str, key: str, memory_id: int) -> None:
        """Añade una entrada al índice"""
        index = self._indices.get(index_name, {})
        
        if key not in index:
            index[key] = IndexEntry(key=key, value=key)
        
        index[key].memory_ids.add(memory_id)
        index[key].updated_at = datetime.utcnow()
        
        self._indices[index_name] = index
    
    def remove_from_index(self, memory_id: int) -> None:
        """Remueve una memoria de todos los índices"""
        for index_name in self._indices:
            index = self._indices[index_name]
            for key, entry in list(index.items()):
                entry.memory_ids.discard(memory_id)
                if not entry.memory_ids:
                    del index[key]
    
    def search(
        self,
        index_name: str,
        query: str,
        fuzzy: bool = False
    ) -> List[int]:
        """
        Busca en un índice específico.
        
        Args:
            index_name: Nombre del índice
            query: Término de búsqueda
            fuzzy: Si permitir búsqueda fuzzy
        
        Returns:
            Lista de memory IDs encontrados
        """
        index = self._indices.get(index_name, {})
        
        if not fuzzy:
            entry = index.get(query)
            return list(entry.memory_ids) if entry else []
        
        # Búsqueda fuzzy
        results = set()
        query_lower = query.lower()
        
        for key, entry in index.items():
            if query_lower in key.lower():
                results.update(entry.memory_ids)
        
        return list(results)
    
    def search_multi(
        self,
        queries: Dict[str, str],
        operator: str = "AND"
    ) -> List[int]:
        """
        Busca en múltiples índices.
        
        Args:
            queries: Dict de {index_name: query}
            operator: "AND" o "OR"
        
        Returns:
            Lista de memory IDs que coinciden
        """
        result_sets = []
        
        for index_name, query in queries.items():
            ids = self.search(index_name, query)
            result_sets.append(set(ids))
        
        if not result_sets:
            return []
        
        if operator == "AND":
            return list(set.intersection(*result_sets))
        else:
            return list(set.union(*result_sets))
    
    def get_index_stats(self, index_name: str) -> Dict[str, Any]:
        """Obtiene estadísticas de un índice"""
        index = self._indices.get(index_name, {})
        
        total_entries = len(index)
        total_references = sum(len(e.memory_ids) for e in index.values())
        
        return {
            "index_name": index_name,
            "total_entries": total_entries,
            "total_references": total_references,
            "avg_references": total_references / max(1, total_entries)
        }
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de todos los índices"""
        return {
            name: self.get_index_stats(name)
            for name in self._configs
        }
    
    def rebuild_index(self, index_name: str, memories: List[Dict[str, Any]]) -> None:
        """
        Reconstruye un índice desde cero.
        
        Args:
            index_name: Nombre del índice a reconstruir
            memories: Lista de todas las memorias
        """
        if index_name not in self._configs:
            raise ValueError(f"Index {index_name} does not exist")
        
        # Limpiar índice
        self._indices[index_name] = {}
        
        # Re-indexar
        for memory in memories:
            self.index_memory(memory)
        
        logger.info(f"Index rebuilt: {index_name} ({len(memories)} memories)")
    
    def export_index(self, index_name: str) -> Dict[str, Any]:
        """Exporta un índice a diccionario"""
        index = self._indices.get(index_name, {})
        
        return {
            "config": self._configs.get(index_name).to_dict() if index_name in self._configs else None,
            "entries": {
                key: {
                    "memory_ids": list(entry.memory_ids),
                    "metadata": entry.metadata,
                    "updated_at": entry.updated_at.isoformat()
                }
                for key, entry in index.items()
            }
        }
