"""
Capital Cognitivo - Núcleo del Sistema
======================================

El Capital Cognitivo es el activo acumulado de conocimiento, contexto y memoria
que se enriquece con cada interacción, permitiendo que los agentes funcionen
de manera cada vez más eficiente.

Basado en "Promptología Ontológica" de Mauricio Quiroga:
"El Capital Cognitivo elimina la ilusión del control jerárquico, 
sustituyéndola por una red de conversaciones coordinadas."
"""

import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID, uuid4
import json

from pydantic import BaseModel, Field

from ..core.models import Memory, MemoryType, Session, Message


class CapitalType(str, Enum):
    """Tipos de Capital Cognitivo"""
    # Capital explícito (documentado)
    KNOWLEDGE = "KNOWLEDGE"           # Conocimiento declarativo
    PROCEDURES = "PROCEDURES"         # Procedimientos y métodos
    PATTERNS = "PATTERNS"             # Patrones identificados
    RELATIONSHIPS = "RELATIONSHIPS"   # Relaciones entre conceptos
    
    # Capital implícito (contextual)
    CONTEXT = "CONTEXT"               # Contexto de situaciones
    INTUITIONS = "INTUITIONS"         # Intuiciones derivadas
    PREFERENCES = "PREFERENCES"       # Preferencias del usuario/sistema
    HEURISTICS = "HEURISTICS"         # Reglas heurísticas
    
    # Capital operativo
    SKILLS = "SKILLS"                 # Habilidades disponibles
    TOOLS = "TOOLS"                   # Herramientas conocidas
    AGENTS = "AGENTS"                 # Agentes y sus capacidades
    WORKFLOWS = "WORKFLOWS"           # Flujos de trabajo probados
    
    # Capital meta-cognitivo
    META_KNOWLEDGE = "META_KNOWLEDGE" # Conocimiento sobre el conocimiento
    SELF_MODEL = "SELF_MODEL"         # Modelo del propio sistema
    IMPROVEMENTS = "IMPROVEMENTS"     # Mejoras aplicadas


class CapitalEntry(BaseModel):
    """Entrada individual de Capital Cognitivo"""
    id: UUID = Field(default_factory=uuid4)
    type: CapitalType
    key: str                                  # Clave única del conocimiento
    value: Any                                # Valor del conocimiento
    confidence: float = Field(default=1.0, ge=0, le=1)  # Nivel de confianza
    
    # Metadatos
    source: Optional[str] = None              # Fuente del conocimiento
    source_type: Optional[str] = None         # Tipo de fuente (user, agent, system)
    session_id: Optional[UUID] = None         # Sesión donde se originó
    agent_id: Optional[UUID] = None           # Agente que lo generó
    
    # Uso y relevancia
    access_count: int = 0
    last_accessed: Optional[datetime] = None
    relevance_score: float = Field(default=0.5, ge=0, le=1)
    
    # Relaciones
    related_entries: List[UUID] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    
    # Ciclo de vida
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    is_active: bool = True
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


class CapitalMetrics(BaseModel):
    """Métricas del Capital Cognitivo"""
    total_entries: int = 0
    entries_by_type: Dict[str, int] = Field(default_factory=dict)
    total_accesses: int = 0
    average_confidence: float = 0.0
    average_relevance: float = 0.0
    active_sessions: int = 0
    knowledge_growth_rate: float = 0.0         # Entradas por día
    consolidation_rate: float = 0.0            # % de consolidación exitosa
    
    @property
    def health_score(self) -> float:
        """Puntuación de salud del capital (0-1)"""
        if self.total_entries == 0:
            return 0.0
        
        factors = [
            self.average_confidence,
            self.average_relevance,
            min(1.0, self.knowledge_growth_rate / 10),  # Normalizar
            self.consolidation_rate,
        ]
        return sum(factors) / len(factors)


class CognitiveCapital:
    """
    Sistema de Capital Cognitivo.
    
    El Capital Cognitivo es el núcleo que permite:
    1. Acumular conocimiento de forma estructurada
    2. Recuperar contexto relevante eficientemente
    3. Compartir conocimiento entre agentes
    4. Auto-mejorar basándose en experiencia
    
    Filosofía (basada en Promptología Ontológica):
    - El lenguaje crea realidad, no la describe
    - Las conversaciones son la unidad operativa
    - El Capital Cognitivo emerge de la interacción
    - La obviedad compartida reduce fricción cognitiva
    """
    
    def __init__(
        self,
        agent_id: UUID,
        storage_backend: Optional[Any] = None
    ):
        self.agent_id = agent_id
        self._storage = storage_backend
        
        # Caché en memoria
        self._entries: Dict[UUID, CapitalEntry] = {}
        self._index_by_key: Dict[str, UUID] = {}
        self._index_by_type: Dict[CapitalType, Set[UUID]] = {
            t: set() for t in CapitalType
        }
        self._index_by_tags: Dict[str, Set[UUID]] = {}
        
        # Métricas
        self._metrics = CapitalMetrics()
        
        # Contexto activo
        self._active_context: Dict[str, Any] = {}
        
    # ==========================================
    # GESTIÓN DE CAPITAL
    # ==========================================
    
    async def deposit(
        self,
        type: CapitalType,
        key: str,
        value: Any,
        confidence: float = 1.0,
        source: Optional[str] = None,
        session_id: Optional[UUID] = None,
        tags: List[str] = None,
        expires_in: Optional[int] = None
    ) -> CapitalEntry:
        """
        Depositar nuevo capital cognitivo.
        
        Args:
            type: Tipo de capital
            key: Clave única identificadora
            value: Valor del conocimiento
            confidence: Nivel de confianza (0-1)
            source: Fuente del conocimiento
            session_id: Sesión de origen
            tags: Etiquetas para clasificación
            expires_in: Tiempo de expiración en segundos
            
        Returns:
            La entrada creada
        """
        # Verificar si ya existe
        if key in self._index_by_key:
            existing_id = self._index_by_key[key]
            return await self.update(existing_id, {
                "value": value,
                "confidence": max(confidence, self._entries[existing_id].confidence),
                "updated_at": datetime.utcnow()
            })
        
        # Crear nueva entrada
        expires_at = None
        if expires_in:
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        entry = CapitalEntry(
            id=uuid4(),
            type=type,
            key=key,
            value=value,
            confidence=confidence,
            source=source,
            session_id=session_id,
            agent_id=self.agent_id,
            tags=tags or [],
            expires_at=expires_at
        )
        
        # Almacenar
        self._entries[entry.id] = entry
        self._index_by_key[key] = entry.id
        self._index_by_type[type].add(entry.id)
        
        # Indexar por tags
        for tag in entry.tags:
            if tag not in self._index_by_tags:
                self._index_by_tags[tag] = set()
            self._index_by_tags[tag].add(entry.id)
        
        # Actualizar métricas
        self._metrics.total_entries += 1
        self._metrics.entries_by_type[type.value] = \
            self._metrics.entries_by_type.get(type.value, 0) + 1
        
        # Persistir si hay storage
        if self._storage:
            await self._persist_entry(entry)
        
        return entry
    
    async def withdraw(
        self,
        key: str,
        update_access: bool = True
    ) -> Optional[CapitalEntry]:
        """
        Retirar (recuperar) capital por clave.
        
        Args:
            key: Clave del conocimiento
            update_access: Si actualizar métricas de acceso
            
        Returns:
            La entrada encontrada o None
        """
        if key not in self._index_by_key:
            return None
        
        entry_id = self._index_by_key[key]
        entry = self._entries.get(entry_id)
        
        if not entry or not entry.is_active:
            return None
        
        # Verificar expiración
        if entry.expires_at and entry.expires_at < datetime.utcnow():
            await self.deprecate(entry_id)
            return None
        
        # Actualizar acceso
        if update_access:
            entry.access_count += 1
            entry.last_accessed = datetime.utcnow()
            self._metrics.total_accesses += 1
        
        return entry
    
    async def withdraw_by_type(
        self,
        type: CapitalType,
        limit: int = 10,
        min_confidence: float = 0.0,
        sort_by_relevance: bool = True
    ) -> List[CapitalEntry]:
        """
        Retirar capital por tipo.
        
        Args:
            type: Tipo de capital
            limit: Máximo de entradas
            min_confidence: Confianza mínima
            sort_by_relevance: Ordenar por relevancia
            
        Returns:
            Lista de entradas
        """
        entry_ids = self._index_by_type.get(type, set())
        
        entries = []
        for eid in entry_ids:
            entry = self._entries.get(eid)
            if entry and entry.is_active and entry.confidence >= min_confidence:
                # Verificar expiración
                if entry.expires_at and entry.expires_at < datetime.utcnow():
                    await self.deprecate(eid)
                    continue
                entries.append(entry)
        
        # Ordenar
        if sort_by_relevance:
            entries.sort(key=lambda e: e.relevance_score, reverse=True)
        else:
            entries.sort(key=lambda e: e.access_count, reverse=True)
        
        return entries[:limit]
    
    async def search(
        self,
        query: str,
        types: Optional[List[CapitalType]] = None,
        tags: Optional[List[str]] = None,
        limit: int = 10
    ) -> List[CapitalEntry]:
        """
        Buscar capital cognitivo.
        
        Args:
            query: Texto de búsqueda
            types: Filtrar por tipos
            tags: Filtrar por tags
            limit: Máximo de resultados
            
        Returns:
            Lista de entradas matching
        """
        results = []
        
        # Buscar por tags
        if tags:
            tag_entries = set()
            for tag in tags:
                if tag in self._index_by_tags:
                    tag_entries.update(self._index_by_tags[tag])
            
            for eid in tag_entries:
                entry = self._entries.get(eid)
                if self._matches_filters(entry, types, query):
                    results.append(entry)
        else:
            # Búsqueda general
            for entry in self._entries.values():
                if self._matches_filters(entry, types, query):
                    results.append(entry)
        
        # Ordenar por relevancia y confianza
        results.sort(
            key=lambda e: (e.relevance_score * e.confidence),
            reverse=True
        )
        
        return results[:limit]
    
    async def update(
        self,
        entry_id: UUID,
        data: Dict[str, Any]
    ) -> Optional[CapitalEntry]:
        """Actualizar una entrada existente"""
        entry = self._entries.get(entry_id)
        if not entry:
            return None
        
        # Actualizar campos permitidos
        for key, value in data.items():
            if hasattr(entry, key) and key not in ['id', 'created_at']:
                setattr(entry, key, value)
        
        entry.updated_at = datetime.utcnow()
        
        if self._storage:
            await self._persist_entry(entry)
        
        return entry
    
    async def deprecate(self, entry_id: UUID) -> bool:
        """Marcar entrada como deprecada"""
        entry = self._entries.get(entry_id)
        if not entry:
            return False
        
        entry.is_active = False
        entry.updated_at = datetime.utcnow()
        
        # Actualizar índices
        self._index_by_key.pop(entry.key, None)
        self._index_by_type[entry.type].discard(entry_id)
        for tag in entry.tags:
            self._index_by_tags.get(tag, set()).discard(entry_id)
        
        return True
    
    # ==========================================
    # CONSOLIDACIÓN Y SÍNTESIS
    # ==========================================
    
    async def consolidate(
        self,
        session_id: UUID,
        threshold_confidence: float = 0.7
    ) -> Dict[str, Any]:
        """
        Consolidar capital de una sesión.
        
        Transfiere conocimiento valioso de la sesión al capital permanente.
        
        Args:
            session_id: ID de la sesión
            threshold_confidence: Umbral mínimo para consolidar
            
        Returns:
            Resumen de consolidación
        """
        consolidated = {
            "entries_consolidated": 0,
            "relationships_created": 0,
            "patterns_identified": 0,
            "capital_deposited": []
        }
        
        session_entries = [
            e for e in self._entries.values()
            if e.session_id == session_id and e.confidence >= threshold_confidence
        ]
        
        for entry in session_entries:
            # Incrementar relevancia
            entry.relevance_score = min(1.0, entry.relevance_score + 0.1)
            
            # Identificar patrones
            patterns = await self._identify_patterns(entry)
            for pattern in patterns:
                await self.deposit(
                    type=CapitalType.PATTERNS,
                    key=f"pattern:{pattern['key']}",
                    value=pattern['value'],
                    confidence=pattern['confidence'],
                    source="consolidation",
                    tags=["auto-generated", "pattern"]
                )
                consolidated["patterns_identified"] += 1
            
            consolidated["entries_consolidated"] += 1
            consolidated["capital_deposited"].append(str(entry.id))
        
        # Crear relaciones entre entradas relacionadas
        relationships = await self._create_relationships(session_entries)
        consolidated["relationships_created"] = relationships
        
        return consolidated
    
    async def synthesize(
        self,
        context: Dict[str, Any],
        max_entries: int = 20
    ) -> Dict[str, Any]:
        """
        Sintetizar capital relevante para un contexto.
        
        Combina múltiples entradas en un contexto coherente.
        
        Args:
            context: Contexto de la síntesis
            max_entries: Máximo de entradas a incluir
            
        Returns:
            Conocimiento sintetizado
        """
        synthesis = {
            "relevant_knowledge": [],
            "procedures": [],
            "patterns": [],
            "context": {},
            "recommendations": []
        }
        
        # Recuperar conocimiento relevante
        for key, value in context.items():
            if isinstance(value, str):
                entries = await self.search(value, limit=5)
                for entry in entries:
                    if entry.type == CapitalType.KNOWLEDGE:
                        synthesis["relevant_knowledge"].append({
                            "key": entry.key,
                            "value": entry.value,
                            "confidence": entry.confidence
                        })
                    elif entry.type == CapitalType.PROCEDURES:
                        synthesis["procedures"].append(entry.value)
                    elif entry.type == CapitalType.PATTERNS:
                        synthesis["patterns"].append(entry.value)
        
        # Construir contexto combinado
        synthesis["context"] = await self._build_combined_context(
            synthesis["relevant_knowledge"]
        )
        
        # Generar recomendaciones
        synthesis["recommendations"] = await self._generate_recommendations(
            synthesis
        )
        
        # Limitar resultados
        synthesis["relevant_knowledge"] = synthesis["relevant_knowledge"][:max_entries]
        
        return synthesis
    
    # ==========================================
    # COMPARTIR Y TRANSFERIR
    # ==========================================
    
    async def share_with(
        self,
        target_agent_id: UUID,
        entry_keys: List[str],
        share_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Compartir capital con otro agente.
        
        Args:
            target_agent_id: ID del agente destino
            entry_keys: Claves a compartir
            share_context: Contexto adicional
            
        Returns:
            Resumen de transferencia
        """
        transferred = []
        
        for key in entry_keys:
            entry = await self.withdraw(key, update_access=False)
            if entry:
                transferred.append({
                    "key": key,
                    "type": entry.type.value,
                    "confidence": entry.confidence,
                    "shared_at": datetime.utcnow().isoformat()
                })
        
        return {
            "source_agent": str(self.agent_id),
            "target_agent": str(target_agent_id),
            "entries_transferred": len(transferred),
            "entries": transferred,
            "context": share_context
        }
    
    async def import_from(
        self,
        source_agent_id: UUID,
        entries: List[Dict[str, Any]],
        import_context: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Importar capital de otro agente.
        
        Args:
            source_agent_id: ID del agente fuente
            entries: Entradas a importar
            import_context: Contexto de importación
            
        Returns:
            Número de entradas importadas
        """
        imported = 0
        
        for entry_data in entries:
            try:
                await self.deposit(
                    type=CapitalType(entry_data["type"]),
                    key=entry_data["key"],
                    value=entry_data["value"],
                    confidence=entry_data.get("confidence", 0.8),
                    source=f"agent:{source_agent_id}",
                    tags=entry_data.get("tags", [])
                )
                imported += 1
            except Exception:
                continue
        
        return imported
    
    # ==========================================
    # MÉTRICAS Y SALUD
    # ==========================================
    
    async def get_metrics(self) -> CapitalMetrics:
        """Obtener métricas actuales del capital"""
        # Actualizar métricas calculadas
        if self._entries:
            confidences = [e.confidence for e in self._entries.values() if e.is_active]
            relevances = [e.relevance_score for e in self._entries.values() if e.is_active]
            
            self._metrics.average_confidence = (
                sum(confidences) / len(confidences) if confidences else 0
            )
            self._metrics.average_relevance = (
                sum(relevances) / len(relevances) if relevances else 0
            )
        
        return self._metrics
    
    async def health_check(self) -> Dict[str, Any]:
        """Verificar salud del capital cognitivo"""
        metrics = await self.get_metrics()
        
        issues = []
        recommendations = []
        
        # Verificar problemas
        if metrics.total_entries == 0:
            issues.append("No hay capital acumulado")
            recommendations.append("Realizar interacciones para acumular conocimiento")
        
        if metrics.average_confidence < 0.5:
            issues.append("Confianza promedio baja")
            recommendations.append("Revisar y validar conocimiento existente")
        
        if metrics.knowledge_growth_rate < 1:
            issues.append("Crecimiento de conocimiento estancado")
            recommendations.append("Diversificar tipos de interacciones")
        
        return {
            "health_score": metrics.health_score,
            "status": "healthy" if metrics.health_score > 0.6 else "needs_attention",
            "metrics": metrics.model_dump(),
            "issues": issues,
            "recommendations": recommendations
        }
    
    # ==========================================
    # MÉTODOS PRIVADOS
    # ==========================================
    
    def _matches_filters(
        self,
        entry: Optional[CapitalEntry],
        types: Optional[List[CapitalType]],
        query: str
    ) -> bool:
        """Verificar si una entrada matches los filtros"""
        if not entry or not entry.is_active:
            return False
        
        if types and entry.type not in types:
            return False
        
        # Búsqueda de texto en key, value, y tags
        query_lower = query.lower()
        if query_lower in entry.key.lower():
            return True
        if query_lower in str(entry.value).lower():
            return True
        if any(query_lower in tag.lower() for tag in entry.tags):
            return True
        
        return False
    
    async def _identify_patterns(self, entry: CapitalEntry) -> List[Dict[str, Any]]:
        """Identificar patrones en una entrada"""
        patterns = []
        
        # TODO: Implementar detección de patrones más sofisticada
        # Por ahora, detectar patrones simples en texto
        if isinstance(entry.value, str):
            words = entry.value.lower().split()
            if len(words) >= 3:
                # Detectar n-grams como patrones potenciales
                for i in range(len(words) - 2):
                    ngram = " ".join(words[i:i+3])
                    patterns.append({
                        "key": f"ngram_{hash(ngram)}",
                        "value": ngram,
                        "confidence": 0.6
                    })
        
        return patterns[:5]  # Limitar a 5 patrones
    
    async def _create_relationships(
        self,
        entries: List[CapitalEntry]
    ) -> int:
        """Crear relaciones entre entradas relacionadas"""
        relationships = 0
        
        for i, entry1 in enumerate(entries):
            for entry2 in entries[i+1:]:
                # Detectar relación por tags compartidos
                common_tags = set(entry1.tags) & set(entry2.tags)
                if len(common_tags) >= 2:
                    if entry2.id not in entry1.related_entries:
                        entry1.related_entries.append(entry2.id)
                    if entry1.id not in entry2.related_entries:
                        entry2.related_entries.append(entry1.id)
                    relationships += 1
        
        return relationships
    
    async def _build_combined_context(
        self,
        knowledge: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Construir contexto combinado de múltiples entradas"""
        context = {}
        
        for item in knowledge:
            key = item.get("key", "unknown")
            value = item.get("value")
            context[key] = value
        
        return context
    
    async def _generate_recommendations(
        self,
        synthesis: Dict[str, Any]
    ) -> List[str]:
        """Generar recomendaciones basadas en síntesis"""
        recommendations = []
        
        # Recomendar procedimientos relevantes
        if synthesis["procedures"]:
            recommendations.append(
                f"Considerar usar procedimiento: {synthesis['procedures'][0]}"
            )
        
        # Recomendar basado en patrones
        if synthesis["patterns"]:
            recommendations.append(
                f"Patrón identificado aplicable: {synthesis['patterns'][0]}"
            )
        
        return recommendations
    
    async def _persist_entry(self, entry: CapitalEntry) -> None:
        """Persistir entrada en storage backend"""
        if self._storage:
            # TODO: Implementar persistencia real
            pass
