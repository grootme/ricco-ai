"""
RAG Ontológico con Knowledge Graph para Capital Cognitivo.
Implementa patrones de Neo4j GraphRAG y Microsoft GraphRAG.
"""

from typing import Any, Dict, List, Optional, Set, Tuple, Union
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
import asyncio
import json


# =============================================================================
# PATRONES GOF APLICADOS
# =============================================================================

# Factory Pattern - Para creación de entidades y relaciones
# Strategy Pattern - Para diferentes estrategias de extracción
# Observer Pattern - Para eventos del grafo
# Command Pattern - Para operaciones del grafo
# Builder Pattern - Para construcción de consultas
# Composite Pattern - Para estructura jerárquica de comunidades


# =============================================================================
# MODELOS DE DATOS ONTOLÓGICOS
# =============================================================================

class EntityType(str, Enum):
    """Tipos de entidades en el grafo ontológico."""
    CONCEPT = "concept"
    PERSON = "person"
    ORGANIZATION = "organization"
    TECHNOLOGY = "technology"
    SKILL = "skill"
    DOCUMENT = "document"
    CODE = "code"
    PROCESS = "process"
    EVENT = "event"
    PREFERENCE = "preference"
    MEMORY = "memory"
    AGENT = "agent"
    TOOL = "tool"


class RelationType(str, Enum):
    """Tipos de relaciones en el grafo."""
    # Jerárquicas
    IS_A = "is_a"
    HAS_A = "has_a"
    PART_OF = "part_of"
    
    # Semánticas
    RELATED_TO = "related_to"
    SIMILAR_TO = "similar_to"
    DIFFERENT_FROM = "different_from"
    
    # Causales
    CAUSES = "causes"
    ENABLES = "enables"
    PREVENTS = "prevents"
    
    # Temporales
    PRECEDES = "precedes"
    FOLLOWS = "follows"
    CONCURRENT_WITH = "concurrent_with"
    
    # Agentes
    USES = "uses"
    CREATES = "creates"
    MODIFIES = "modifies"
    DEPENDS_ON = "depends_on"
    
    # Conocimiento
    KNOWS_ABOUT = "knows_about"
    LEARNED_FROM = "learned_from"
    APPLIES_TO = "applies_to"


class NodeProperty(BaseModel):
    """Propiedad de un nodo."""
    name: str
    value: Any
    type: str = "string"
    confidence: float = 1.0


class Entity(BaseModel):
    """Entidad del Knowledge Graph."""
    id: str
    name: str
    entity_type: EntityType
    description: Optional[str] = None
    properties: List[NodeProperty] = Field(default_factory=list)
    embedding: Optional[List[float]] = None
    source_ids: List[str] = Field(default_factory=list)
    community_ids: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    confidence: float = 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def add_property(self, name: str, value: Any, type: str = "string") -> None:
        """Agrega una propiedad a la entidad."""
        self.properties.append(NodeProperty(name=name, value=value, type=type))
    
    def get_property(self, name: str) -> Optional[Any]:
        """Obtiene el valor de una propiedad."""
        for prop in self.properties:
            if prop.name == name:
                return prop.value
        return None


class Relationship(BaseModel):
    """Relación entre entidades en el Knowledge Graph."""
    id: str
    source_id: str
    target_id: str
    relation_type: RelationType
    description: Optional[str] = None
    weight: float = 1.0
    properties: List[NodeProperty] = Field(default_factory=list)
    source_ids: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    confidence: float = 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Community(BaseModel):
    """Comunidad de entidades (resultado de clustering)."""
    id: str
    level: int = 0
    title: str
    summary: Optional[str] = None
    entity_ids: List[str] = Field(default_factory=list)
    relationship_ids: List[str] = Field(default_factory=list)
    parent_id: Optional[str] = None
    children_ids: List[str] = Field(default_factory=list)
    findings: List[str] = Field(default_factory=list)
    embedding: Optional[List[float]] = None
    rank: int = 1


class Triple(BaseModel):
    """Triple RDF-style (sujeto, predicado, objeto)."""
    subject: str
    predicate: RelationType
    object: str
    confidence: float = 1.0
    source: Optional[str] = None


# =============================================================================
# FACTORY PATTERN - EntityFactory
# =============================================================================

class EntityFactory:
    """
    Factory Pattern para creación de entidades.
    Centraliza la lógica de creación y asignación de IDs.
    """
    
    _instance = None
    _id_counter = 0
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def create_entity(
        self,
        name: str,
        entity_type: EntityType,
        description: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        source_ids: Optional[List[str]] = None
    ) -> Entity:
        """Crea una nueva entidad con ID único."""
        self._id_counter += 1
        
        entity = Entity(
            id=f"entity_{self._id_counter}",
            name=name,
            entity_type=entity_type,
            description=description,
            source_ids=source_ids or []
        )
        
        if properties:
            for key, value in properties.items():
                entity.add_property(key, value)
        
        return entity
    
    def create_relationship(
        self,
        source_id: str,
        target_id: str,
        relation_type: RelationType,
        description: Optional[str] = None,
        weight: float = 1.0
    ) -> Relationship:
        """Crea una nueva relación."""
        self._id_counter += 1
        
        return Relationship(
            id=f"rel_{self._id_counter}",
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            description=description,
            weight=weight
        )


# =============================================================================
# STRATEGY PATTERN - Extraction Strategies
# =============================================================================

class ExtractionStrategy(ABC):
    """Strategy Pattern para extracción de entidades."""
    
    @abstractmethod
    async def extract(self, text: str) -> Tuple[List[Entity], List[Relationship]]:
        """Extrae entidades y relaciones del texto."""
        pass


class LLMExtractionStrategy(ExtractionStrategy):
    """Estrategia de extracción usando LLM (como GraphRAG)."""
    
    def __init__(self, entity_types: Optional[List[EntityType]] = None):
        self.entity_types = entity_types or list(EntityType)
        self.factory = EntityFactory()
    
    async def extract(self, text: str) -> Tuple[List[Entity], List[Relationship]]:
        """Extrae usando LLM con prompting estructurado."""
        # Placeholder - en producción usar LLM real
        entities = []
        relationships = []
        
        # Simular extracción basada en patrones simples
        words = text.split()
        for i, word in enumerate(words):
            if len(word) > 5 and word[0].isupper():
                entity = self.factory.create_entity(
                    name=word,
                    entity_type=EntityType.CONCEPT,
                    description=f"Extracted from context: {' '.join(words[max(0,i-2):i+3])}"
                )
                entities.append(entity)
        
        return entities, relationships


class NLPExtractionStrategy(ExtractionStrategy):
    """Estrategia de extracción usando NLP clásico (fast mode)."""
    
    def __init__(self):
        self.factory = EntityFactory()
        # Placeholder para modelos NLP
    
    async def extract(self, text: str) -> Tuple[List[Entity], List[Relationship]]:
        """Extrae usando NLP (sin LLM)."""
        entities = []
        relationships = []
        
        # Placeholder - usar spaCy o similar
        return entities, relationships


class HybridExtractionStrategy(ExtractionStrategy):
    """Estrategia híbrida: NLP + LLM."""
    
    def __init__(self):
        self.nlp_strategy = NLPExtractionStrategy()
        self.llm_strategy = LLMExtractionStrategy()
    
    async def extract(self, text: str) -> Tuple[List[Entity], List[Relationship]]:
        """Combina NLP y LLM para mejor extracción."""
        nlp_entities, nlp_rels = await self.nlp_strategy.extract(text)
        llm_entities, llm_rels = await self.llm_strategy.extract(text)
        
        # Merge con deduplicación
        all_entities = {e.name: e for e in nlp_entities}
        for e in llm_entities:
            if e.name not in all_entities:
                all_entities[e.name] = e
        
        return list(all_entities.values()), nlp_rels + llm_rels


# =============================================================================
# OBSERVER PATTERN - Graph Events
# =============================================================================

class GraphEventType(str, Enum):
    """Tipos de eventos del grafo."""
    ENTITY_CREATED = "entity_created"
    ENTITY_UPDATED = "entity_updated"
    ENTITY_DELETED = "entity_deleted"
    RELATIONSHIP_CREATED = "relationship_created"
    RELATIONSHIP_DELETED = "relationship_deleted"
    COMMUNITY_FORMED = "community_formed"
    SCHEMA_CHANGED = "schema_changed"


class GraphEvent(BaseModel):
    """Evento del Knowledge Graph."""
    event_type: GraphEventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = Field(default_factory=dict)
    source: Optional[str] = None


class GraphObserver(ABC):
    """Observer Pattern para observar cambios en el grafo."""
    
    @abstractmethod
    async def on_event(self, event: GraphEvent) -> None:
        """Maneja un evento del grafo."""
        pass


class LoggingObserver(GraphObserver):
    """Observer que registra eventos."""
    
    def __init__(self):
        self.events: List[GraphEvent] = []
    
    async def on_event(self, event: GraphEvent) -> None:
        self.events.append(event)
        print(f"[KG Event] {event.event_type}: {event.data}")


class MemorySyncObserver(GraphObserver):
    """Observer que sincroniza con el sistema de memoria."""
    
    def __init__(self, memory_system):
        self.memory_system = memory_system
    
    async def on_event(self, event: GraphEvent) -> None:
        if event.event_type == GraphEventType.ENTITY_CREATED:
            # Sincronizar con memoria
            pass


# =============================================================================
# COMMAND PATTERN - Graph Operations
# =============================================================================

class GraphCommand(ABC):
    """Command Pattern para operaciones del grafo."""
    
    @abstractmethod
    async def execute(self, graph: 'KnowledgeGraph') -> Any:
        """Ejecuta el comando."""
        pass
    
    @abstractmethod
    async def undo(self, graph: 'KnowledgeGraph') -> None:
        """Deshace el comando."""
        pass


class AddEntityCommand(GraphCommand):
    """Comando para agregar entidad."""
    
    def __init__(self, entity: Entity):
        self.entity = entity
        self.executed = False
    
    async def execute(self, graph: 'KnowledgeGraph') -> Entity:
        graph._entities[self.entity.id] = self.entity
        self.executed = True
        return self.entity
    
    async def undo(self, graph: 'KnowledgeGraph') -> None:
        if self.executed:
            del graph._entities[self.entity.id]


class AddRelationshipCommand(GraphCommand):
    """Comando para agregar relación."""
    
    def __init__(self, relationship: Relationship):
        self.relationship = relationship
        self.executed = False
    
    async def execute(self, graph: 'KnowledgeGraph') -> Relationship:
        graph._relationships[self.relationship.id] = self.relationship
        self.executed = True
        return self.relationship
    
    async def undo(self, graph: 'KnowledgeGraph') -> None:
        if self.executed:
            del graph._relationships[self.relationship.id]


class BatchCommand(GraphCommand):
    """Comando compuesto para múltiples operaciones."""
    
    def __init__(self, commands: List[GraphCommand]):
        self.commands = commands
    
    async def execute(self, graph: 'KnowledgeGraph') -> List[Any]:
        results = []
        for cmd in self.commands:
            result = await cmd.execute(graph)
            results.append(result)
        return results
    
    async def undo(self, graph: 'KnowledgeGraph') -> None:
        for cmd in reversed(self.commands):
            await cmd.undo(graph)


# =============================================================================
# BUILDER PATTERN - Query Builder
# =============================================================================

class GraphQueryBuilder:
    """Builder Pattern para construir consultas al grafo."""
    
    def __init__(self):
        self._entity_types: List[EntityType] = []
        self._relation_types: List[RelationType] = []
        self._conditions: List[str] = []
        self._limit: int = 100
        self._order_by: Optional[str] = None
        self._include_embeddings: bool = False
    
    def select_entities(self, types: List[EntityType]) -> 'GraphQueryBuilder':
        """Selecciona tipos de entidades."""
        self._entity_types.extend(types)
        return self
    
    def select_relations(self, types: List[RelationType]) -> 'GraphQueryBuilder':
        """Selecciona tipos de relaciones."""
        self._relation_types.extend(types)
        return self
    
    def where(self, condition: str) -> 'GraphQueryBuilder':
        """Agrega condición."""
        self._conditions.append(condition)
        return self
    
    def limit(self, n: int) -> 'GraphQueryBuilder':
        """Establece límite."""
        self._limit = n
        return self
    
    def order_by(self, field: str) -> 'GraphQueryBuilder':
        """Establece ordenamiento."""
        self._order_by = field
        return self
    
    def include_embeddings(self, include: bool = True) -> 'GraphQueryBuilder':
        """Incluye embeddings en resultado."""
        self._include_embeddings = include
        return self
    
    def build(self) -> Dict[str, Any]:
        """Construye la consulta."""
        return {
            "entity_types": self._entity_types,
            "relation_types": self._relation_types,
            "conditions": self._conditions,
            "limit": self._limit,
            "order_by": self._order_by,
            "include_embeddings": self._include_embeddings
        }


# =============================================================================
# KNOWLEDGE GRAPH PRINCIPAL
# =============================================================================

class KnowledgeGraph:
    """
    Knowledge Graph Ontológico para Capital Cognitivo.
    Implementa patrones de Neo4j GraphRAG y Microsoft GraphRAG.
    """
    
    def __init__(
        self,
        extraction_strategy: Optional[ExtractionStrategy] = None
    ):
        # Almacenamiento
        self._entities: Dict[str, Entity] = {}
        self._relationships: Dict[str, Relationship] = {}
        self._communities: Dict[str, Community] = {}
        
        # Índices
        self._entity_name_index: Dict[str, str] = {}
        self._entity_type_index: Dict[EntityType, Set[str]] = {}
        self._adjacency: Dict[str, Set[str]] = {}  # entity_id -> related entity_ids
        
        # Estrategia de extracción
        self._extraction_strategy = extraction_strategy or HybridExtractionStrategy()
        
        # Observers
        self._observers: List[GraphObserver] = []
        
        # Factory
        self._factory = EntityFactory()
        
        # Historial de comandos (para undo)
        self._command_history: List[GraphCommand] = []
    
    # === Observer Management ===
    
    def add_observer(self, observer: GraphObserver) -> None:
        """Agrega un observer."""
        self._observers.append(observer)
    
    async def _notify(self, event: GraphEvent) -> None:
        """Notifica a todos los observers."""
        for observer in self._observers:
            await observer.on_event(event)
    
    # === Entity Operations ===
    
    async def add_entity(
        self,
        name: str,
        entity_type: EntityType,
        description: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None
    ) -> Entity:
        """Agrega una entidad al grafo."""
        entity = self._factory.create_entity(
            name=name,
            entity_type=entity_type,
            description=description,
            properties=properties
        )
        
        cmd = AddEntityCommand(entity)
        await cmd.execute(self)
        self._command_history.append(cmd)
        
        # Actualizar índices
        self._entity_name_index[name.lower()] = entity.id
        if entity_type not in self._entity_type_index:
            self._entity_type_index[entity_type] = set()
        self._entity_type_index[entity_type].add(entity.id)
        
        # Notificar
        await self._notify(GraphEvent(
            event_type=GraphEventType.ENTITY_CREATED,
            data={"entity_id": entity.id, "name": name, "type": entity_type}
        ))
        
        return entity
    
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        """Obtiene una entidad por ID."""
        return self._entities.get(entity_id)
    
    def get_entity_by_name(self, name: str) -> Optional[Entity]:
        """Obtiene una entidad por nombre."""
        entity_id = self._entity_name_index.get(name.lower())
        if entity_id:
            return self._entities.get(entity_id)
        return None
    
    def get_entities_by_type(self, entity_type: EntityType) -> List[Entity]:
        """Obtiene entidades por tipo."""
        entity_ids = self._entity_type_index.get(entity_type, set())
        return [self._entities[eid] for eid in entity_ids if eid in self._entities]
    
    # === Relationship Operations ===
    
    async def add_relationship(
        self,
        source_id: str,
        target_id: str,
        relation_type: RelationType,
        description: Optional[str] = None,
        weight: float = 1.0
    ) -> Relationship:
        """Agrega una relación al grafo."""
        relationship = self._factory.create_relationship(
            source_id=source_id,
            target_id=target_id,
            relation_type=relation_type,
            description=description,
            weight=weight
        )
        
        cmd = AddRelationshipCommand(relationship)
        await cmd.execute(self)
        self._command_history.append(cmd)
        
        # Actualizar adjacencia
        if source_id not in self._adjacency:
            self._adjacency[source_id] = set()
        self._adjacency[source_id].add(target_id)
        
        await self._notify(GraphEvent(
            event_type=GraphEventType.RELATIONSHIP_CREATED,
            data={"relationship_id": relationship.id}
        ))
        
        return relationship
    
    def get_relationships(
        self,
        entity_id: str,
        relation_type: Optional[RelationType] = None
    ) -> List[Relationship]:
        """Obtiene relaciones de una entidad."""
        relationships = []
        for rel in self._relationships.values():
            if rel.source_id == entity_id or rel.target_id == entity_id:
                if relation_type is None or rel.relation_type == relation_type:
                    relationships.append(rel)
        return relationships
    
    def get_neighbors(self, entity_id: str) -> List[Entity]:
        """Obtiene entidades vecinas."""
        neighbor_ids = self._adjacency.get(entity_id, set())
        return [self._entities[nid] for nid in neighbor_ids if nid in self._entities]
    
    # === Extraction ===
    
    async def extract_from_text(self, text: str) -> Tuple[List[Entity], List[Relationship]]:
        """Extrae entidades y relaciones de texto."""
        return await self._extraction_strategy.extract(text)
    
    async def ingest_document(
        self,
        document: str,
        source_id: Optional[str] = None
    ) -> Tuple[List[Entity], List[Relationship]]:
        """Ingiera un documento completo al grafo."""
        entities, relationships = await self.extract_from_text(document)
        
        # Agregar al grafo
        for entity in entities:
            if source_id and source_id not in entity.source_ids:
                entity.source_ids.append(source_id)
            await self.add_entity(
                name=entity.name,
                entity_type=entity.entity_type,
                description=entity.description
            )
        
        for rel in relationships:
            await self.add_relationship(
                source_id=rel.source_id,
                target_id=rel.target_id,
                relation_type=rel.relation_type
            )
        
        return entities, relationships
    
    # === Query ===
    
    def query(self) -> GraphQueryBuilder:
        """Crea un builder de consultas."""
        return GraphQueryBuilder()
    
    def execute_query(self, query: Dict[str, Any]) -> List[Entity]:
        """Ejecuta una consulta."""
        results = []
        
        entity_types = query.get("entity_types", [])
        limit = query.get("limit", 100)
        
        if entity_types:
            for et in entity_types:
                results.extend(self.get_entities_by_type(et))
        else:
            results = list(self._entities.values())
        
        return results[:limit]
    
    # === Community Detection (Leiden-style) ===
    
    async def detect_communities(
        self,
        max_cluster_size: int = 10
    ) -> List[Community]:
        """Detecta comunidades usando algoritmo tipo Leiden."""
        # Placeholder - en producción usar graspologic o similar
        communities = []
        
        # Simular detección simple basada en conectividad
        visited = set()
        community_id = 0
        
        for entity_id in self._entities:
            if entity_id not in visited:
                # BFS para encontrar componente conectado
                component = set()
                queue = [entity_id]
                
                while queue:
                    current = queue.pop(0)
                    if current in visited:
                        continue
                    visited.add(current)
                    component.add(current)
                    
                    for neighbor_id in self._adjacency.get(current, set()):
                        if neighbor_id not in visited:
                            queue.append(neighbor_id)
                
                if component:
                    community_id += 1
                    community = Community(
                        id=f"community_{community_id}",
                        level=0,
                        title=f"Community {community_id}",
                        entity_ids=list(component)
                    )
                    communities.append(community)
                    self._communities[community.id] = community
        
        return communities
    
    # === Semantic Search ===
    
    async def semantic_search(
        self,
        query: str,
        top_k: int = 5
    ) -> List[Tuple[Entity, float]]:
        """Búsqueda semántica en el grafo."""
        # Placeholder - en producción usar embeddings
        results = []
        query_lower = query.lower()
        
        for entity in self._entities.values():
            score = 0.0
            if query_lower in entity.name.lower():
                score += 0.5
            if entity.description and query_lower in entity.description.lower():
                score += 0.3
            
            if score > 0:
                results.append((entity, score))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    # === Serialization ===
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa el grafo a diccionario."""
        return {
            "entities": [e.model_dump() for e in self._entities.values()],
            "relationships": [r.model_dump() for r in self._relationships.values()],
            "communities": [c.model_dump() for c in self._communities.values()]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KnowledgeGraph':
        """Deserializa el grafo."""
        kg = cls()
        
        for entity_data in data.get("entities", []):
            entity = Entity(**entity_data)
            kg._entities[entity.id] = entity
            kg._entity_name_index[entity.name.lower()] = entity.id
        
        for rel_data in data.get("relationships", []):
            rel = Relationship(**rel_data)
            kg._relationships[rel.id] = rel
        
        for comm_data in data.get("communities", []):
            comm = Community(**comm_data)
            kg._communities[comm.id] = comm
        
        return kg


# =============================================================================
# FACADE PATTERN - Simplified Interface
# =============================================================================

class CognitiveKnowledgeBase:
    """
    Facade Pattern para acceso simplificado al Knowledge Graph.
    Combina Knowledge Graph con capacidades de RAG.
    """
    
    def __init__(self):
        self.graph = KnowledgeGraph()
        self._setup_observers()
    
    def _setup_observers(self) -> None:
        """Configura observers por defecto."""
        self.graph.add_observer(LoggingObserver())
    
    async def learn(self, text: str, source: Optional[str] = None) -> Dict[str, Any]:
        """Aprende de un texto, extrayendo conocimiento."""
        entities, relationships = await self.graph.ingest_document(text, source)
        
        return {
            "learned": True,
            "entities_created": len(entities),
            "relationships_created": len(relationships),
            "source": source
        }
    
    async def query(self, question: str) -> Dict[str, Any]:
        """Consulta el conocimiento."""
        # Búsqueda semántica
        results = await self.graph.semantic_search(question, top_k=5)
        
        # Expandir con vecinos
        expanded_entities = set()
        for entity, score in results:
            expanded_entities.add(entity)
            for neighbor in self.graph.get_neighbors(entity.id)[:3]:
                expanded_entities.add(neighbor)
        
        return {
            "question": question,
            "relevant_entities": [
                {"name": e.name, "type": e.entity_type, "description": e.description}
                for e in expanded_entities
            ],
            "confidence": results[0][1] if results else 0.0
        }
    
    async def get_context_for_agent(
        self,
        task: str,
        agent_role: str
    ) -> Dict[str, Any]:
        """Obtiene contexto relevante para un agente."""
        # Buscar entidades relevantes
        entities = await self.graph.semantic_search(task, top_k=10)
        
        # Filtrar por relevancia al rol
        relevant = [
            e for e, score in entities
            if score > 0.2
        ]
        
        return {
            "task": task,
            "agent_role": agent_role,
            "relevant_knowledge": [
                {"entity": e.name, "description": e.description}
                for e in relevant
            ],
            "context_confidence": entities[0][1] if entities else 0.0
        }


# =============================================================================
# SINGLETON PATTERN - Global Knowledge Base
# =============================================================================

class GlobalKnowledgeBase:
    """Singleton para acceso global al Knowledge Graph."""
    
    _instance: Optional[CognitiveKnowledgeBase] = None
    
    @classmethod
    def get_instance(cls) -> CognitiveKnowledgeBase:
        if cls._instance is None:
            cls._instance = CognitiveKnowledgeBase()
        return cls._instance
    
    @classmethod
    def reset(cls) -> None:
        cls._instance = None
