"""
Sistema de Memoria Multi-Tipo del Super Asistente.
Integra patrones de Mem0 con checkpointing de LangGraph.
"""

from typing import Any, Dict, List, Optional, Union, Sequence
from abc import ABC, abstractmethod
from datetime import datetime
import json
import hashlib
from pydantic import BaseModel, Field

# Importar modelos locales
import sys
sys.path.insert(0, '/home/z/my-project/super_assistant_python')
from core.models import (
    MemoryItem, MemoryType, MemorySearchResult,
    SuperAssistantState
)


# =============================================================================
# INTERFACES BASE
# =============================================================================

class MemoryStore(ABC):
    """Interface abstracta para almacenamiento de memoria."""
    
    @abstractmethod
    async def add(self, item: MemoryItem) -> str:
        """Agrega un item de memoria y retorna su ID."""
        pass
    
    @abstractmethod
    async def get(self, memory_id: str) -> Optional[MemoryItem]:
        """Obtiene un item de memoria por ID."""
        pass
    
    @abstractmethod
    async def search(
        self, 
        query: str, 
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> MemorySearchResult:
        """Busca memorias relevantes."""
        pass
    
    @abstractmethod
    async def update(self, memory_id: str, data: Dict[str, Any]) -> bool:
        """Actualiza un item de memoria."""
        pass
    
    @abstractmethod
    async def delete(self, memory_id: str) -> bool:
        """Elimina un item de memoria."""
        pass
    
    @abstractmethod
    async def get_all(
        self, 
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[MemoryItem]:
        """Obtiene todas las memorias que coinciden con filtros."""
        pass


# =============================================================================
# MEMORIA EN MEMORIA (Para desarrollo y testing)
# =============================================================================

class InMemoryStore(MemoryStore):
    """
    Implementación en memoria del almacén de memoria.
    Útil para desarrollo y testing.
    """
    
    def __init__(self):
        self._store: Dict[str, MemoryItem] = {}
        self._counter = 0
    
    def _generate_id(self) -> str:
        self._counter += 1
        return f"mem_{self._counter}"
    
    def _compute_hash(self, content: str) -> str:
        """Computa hash para deduplicación."""
        return hashlib.md5(content.encode()).hexdigest()
    
    async def add(self, item: MemoryItem) -> str:
        if not item.id:
            item.id = self._generate_id()
        
        # Computar hash si no existe
        if not item.hash:
            item.hash = self._compute_hash(item.content)
        
        # Verificar duplicados
        for existing in self._store.values():
            if existing.hash == item.hash:
                return existing.id
        
        item.created_at = datetime.utcnow()
        item.updated_at = datetime.utcnow()
        self._store[item.id] = item
        return item.id
    
    async def get(self, memory_id: str) -> Optional[MemoryItem]:
        return self._store.get(memory_id)
    
    async def search(
        self, 
        query: str, 
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None
    ) -> MemorySearchResult:
        """
        Búsqueda simple por similitud de texto.
        En producción, usar embeddings vectoriales.
        """
        filters = filters or {}
        results = []
        query_lower = query.lower()
        
        for item in self._store.values():
            # Aplicar filtros
            if filters:
                match = True
                for key, value in filters.items():
                    if hasattr(item, key):
                        if getattr(item, key) != value:
                            match = False
                            break
                if not match:
                    continue
            
            # Búsqueda simple por contenido
            score = self._simple_similarity(query_lower, item.content.lower())
            if score > 0:
                item_copy = item.model_copy()
                item_copy.score = score
                results.append(item_copy)
        
        # Ordenar por score descendente
        results.sort(key=lambda x: x.score or 0, reverse=True)
        results = results[:top_k]
        
        return MemorySearchResult(
            items=results,
            total_count=len(results),
            query=query,
            filters=filters
        )
    
    def _simple_similarity(self, query: str, content: str) -> float:
        """Similitud simple basada en palabras compartidas."""
        query_words = set(query.split())
        content_words = set(content.split())
        if not query_words:
            return 0.0
        intersection = query_words & content_words
        return len(intersection) / len(query_words)
    
    async def update(self, memory_id: str, data: Dict[str, Any]) -> bool:
        if memory_id not in self._store:
            return False
        
        item = self._store[memory_id]
        for key, value in data.items():
            if hasattr(item, key):
                setattr(item, key, value)
        item.updated_at = datetime.utcnow()
        return True
    
    async def delete(self, memory_id: str) -> bool:
        if memory_id in self._store:
            del self._store[memory_id]
            return True
        return False
    
    async def get_all(
        self, 
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 100
    ) -> List[MemoryItem]:
        filters = filters or {}
        results = []
        
        for item in self._store.values():
            match = True
            for key, value in filters.items():
                if hasattr(item, key):
                    if getattr(item, key) != value:
                        match = False
                        break
            if match:
                results.append(item)
        
        return results[:limit]


# =============================================================================
# SISTEMA DE MEMORIA MULTI-TIPO
# =============================================================================

class MultiTypeMemorySystem:
    """
    Sistema de memoria que maneja múltiples tipos de memoria.
    Inspirado en la arquitectura de Mem0.
    """
    
    def __init__(self, store: Optional[MemoryStore] = None):
        self.store = store or InMemoryStore()
        self._session_memories: Dict[str, List[MemoryItem]] = {}
    
    async def remember(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.SEMANTIC,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Almacena un nuevo recuerdo en el sistema.
        """
        item = MemoryItem(
            content=content,
            memory_type=memory_type,
            user_id=user_id,
            agent_id=agent_id,
            session_id=session_id,
            metadata=metadata or {}
        )
        
        memory_id = await self.store.add(item)
        
        # También mantener en memoria de sesión si aplica
        if session_id:
            if session_id not in self._session_memories:
                self._session_memories[session_id] = []
            self._session_memories[session_id].append(item)
        
        return memory_id
    
    async def recall(
        self,
        query: str,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        memory_types: Optional[List[MemoryType]] = None,
        top_k: int = 5
    ) -> List[MemoryItem]:
        """
        Recupera memorias relevantes.
        """
        filters = {}
        if user_id:
            filters["user_id"] = user_id
        if agent_id:
            filters["agent_id"] = agent_id
        if session_id:
            filters["session_id"] = session_id
        if memory_types:
            # Búsqueda por tipo requiere múltiples queries
            all_results = []
            for mt in memory_types:
                type_filters = {**filters, "memory_type": mt}
                result = await self.store.search(query, top_k=top_k, filters=type_filters)
                all_results.extend(result.items)
            # Re-ordenar y limitar
            all_results.sort(key=lambda x: x.score or 0, reverse=True)
            return all_results[:top_k]
        
        result = await self.store.search(query, top_k=top_k, filters=filters)
        return result.items
    
    async def get_session_memories(
        self, 
        session_id: str
    ) -> List[MemoryItem]:
        """Obtiene todas las memorias de una sesión."""
        return self._session_memories.get(session_id, [])
    
    async def forget(
        self,
        memory_id: str
    ) -> bool:
        """Elimina un recuerdo específico."""
        return await self.store.delete(memory_id)
    
    async def update_memory(
        self,
        memory_id: str,
        new_content: str
    ) -> bool:
        """Actualiza el contenido de un recuerdo."""
        return await self.store.update(memory_id, {"content": new_content})
    
    async def get_user_preferences(
        self, 
        user_id: str
    ) -> Dict[str, Any]:
        """Obtiene las preferencias de un usuario."""
        results = await self.store.search(
            query="preferences",
            top_k=100,
            filters={"user_id": user_id, "memory_type": MemoryType.PREFERENCE}
        )
        
        preferences = {}
        for item in results.items:
            key = item.metadata.get("preference_key", "unknown")
            preferences[key] = item.content
        
        return preferences
    
    async def set_user_preference(
        self,
        user_id: str,
        key: str,
        value: str
    ) -> str:
        """Establece una preferencia de usuario."""
        return await self.remember(
            content=value,
            memory_type=MemoryType.PREFERENCE,
            user_id=user_id,
            metadata={"preference_key": key}
        )
    
    async def store_procedure(
        self,
        name: str,
        steps: List[str],
        agent_id: Optional[str] = None
    ) -> str:
        """Almacena un procedimiento para uso futuro."""
        return await self.remember(
            content=json.dumps({"name": name, "steps": steps}),
            memory_type=MemoryType.PROCEDURAL,
            agent_id=agent_id,
            metadata={"procedure_name": name}
        )
    
    async def get_procedure(
        self,
        name: str,
        agent_id: Optional[str] = None
    ) -> Optional[List[str]]:
        """Recupera un procedimiento almacenado."""
        filters = {"memory_type": MemoryType.PROCEDURAL}
        if agent_id:
            filters["agent_id"] = agent_id
        
        results = await self.store.search(
            query=name,
            top_k=1,
            filters=filters
        )
        
        if results.items:
            data = json.loads(results.items[0].content)
            return data.get("steps", [])
        return None
    
    async def record_episode(
        self,
        event: str,
        context: Dict[str, Any],
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> str:
        """Registra un evento/experiencia episódica."""
        return await self.remember(
            content=event,
            memory_type=MemoryType.EPISODIC,
            user_id=user_id,
            agent_id=agent_id,
            session_id=session_id,
            metadata={"context": context, "timestamp": datetime.utcnow().isoformat()}
        )


# =============================================================================
# INTEGRACIÓN CON LANGGRAPH
# =============================================================================

class MemoryManager:
    """
    Gestor de memoria integrado con LangGraph.
    Mantiene el estado de memoria en el flujo del grafo.
    """
    
    def __init__(
        self,
        memory_system: Optional[MultiTypeMemorySystem] = None
    ):
        self.memory_system = memory_system or MultiTypeMemorySystem()
    
    async def retrieve_for_context(
        self,
        state: SuperAssistantState,
        query: Optional[str] = None
    ) -> List[MemoryItem]:
        """
        Recupera memorias relevantes para el contexto actual.
        """
        # Usar el último mensaje como query si no se proporciona
        if not query and state.messages:
            last_message = state.messages[-1]
            query = last_message.get("content", "")
        
        if not query:
            return []
        
        # Recuperar memorias de diferentes tipos
        memories = await self.memory_system.recall(
            query=query,
            user_id=state.user_id,
            session_id=state.session_id,
            memory_types=[
                MemoryType.SEMANTIC,
                MemoryType.EPISODIC,
                MemoryType.PREFERENCE
            ],
            top_k=5
        )
        
        return memories
    
    async def store_interaction(
        self,
        state: SuperAssistantState,
        user_message: str,
        assistant_response: str,
        agent_id: Optional[str] = None
    ) -> None:
        """
        Almacena una interacción en la memoria.
        """
        # Guardar mensaje del usuario
        await self.memory_system.remember(
            content=f"User: {user_message}",
            memory_type=MemoryType.EPISODIC,
            user_id=state.user_id,
            agent_id=agent_id,
            session_id=state.session_id
        )
        
        # Guardar respuesta del asistente
        await self.memory_system.remember(
            content=f"Assistant: {assistant_response}",
            memory_type=MemoryType.EPISODIC,
            user_id=state.user_id,
            agent_id=agent_id,
            session_id=state.session_id
        )
    
    async def extract_and_store_facts(
        self,
        state: SuperAssistantState,
        content: str
    ) -> List[str]:
        """
        Extrae y almacena hechos del contenido.
        (Simplificado - en producción usar LLM para extracción)
        """
        # Por ahora, almacenar como hecho semántico
        memory_id = await self.memory_system.remember(
            content=content,
            memory_type=MemoryType.SEMANTIC,
            user_id=state.user_id,
            session_id=state.session_id
        )
        
        return [memory_id]
    
    def format_memories_for_prompt(
        self,
        memories: List[MemoryItem]
    ) -> str:
        """
        Formatea memorias para incluir en un prompt.
        """
        if not memories:
            return ""
        
        formatted = "Memorias relevantes:\n"
        for i, mem in enumerate(memories, 1):
            formatted += f"{i}. [{mem.memory_type}] {mem.content}\n"
        
        return formatted


# =============================================================================
# FACTORY
# =============================================================================

def create_memory_system(
    backend: str = "in_memory",
    **kwargs
) -> MultiTypeMemorySystem:
    """
    Factory para crear el sistema de memoria.
    """
    if backend == "in_memory":
        store = InMemoryStore()
    else:
        # Por defecto usar in_memory
        store = InMemoryStore()
    
    return MultiTypeMemorySystem(store=store)
