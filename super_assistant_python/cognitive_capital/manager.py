"""
Capital Cognitivo Ontológico - Sistema de conocimiento acumulativo.
Implementa memoria, aprendizaje y automejora del sistema.
"""

from typing import Any, Dict, List, Optional, Set, Callable, TypeVar, Generic
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
import json
import hashlib
from collections import defaultdict


# =============================================================================
# CONCEPTOS DE CAPITAL COGNITIVO
# =============================================================================

class CognitiveAssetType(str, Enum):
    """Tipos de activos cognitivos."""
    KNOWLEDGE = "knowledge"           # Hechos y conceptos
    SKILL = "skill"                   # Habilidades ejecutables
    PATTERN = "pattern"               # Patrones reconocidos
    HEURISTIC = "heuristic"           # Reglas heurísticas
    PROCEDURE = "procedure"           # Procedimientos paso a paso
    CONTEXT = "context"               # Contexto situacional
    PREFERENCE = "preference"         # Preferencias aprendidas
    RELATIONSHIP = "relationship"     # Relaciones entre conceptos
    EXPERIENCE = "experience"         # Experiencias pasadas
    INSIGHT = "insight"               # Insights derivados


class CognitiveValue(BaseModel):
    """Valor de un activo cognitivo."""
    confidence: float = 0.5           # Confianza (0-1)
    utility: float = 0.5              # Utilidad percibida (0-1)
    recency: float = 1.0              # Recencia (0-1, 1 = reciente)
    frequency: int = 1                # Frecuencia de uso
    relevance: float = 0.5            # Relevancia actual (0-1)
    
    @property
    def composite_score(self) -> float:
        """Score compuesto del activo."""
        return (
            self.confidence * 0.3 +
            self.utility * 0.3 +
            self.recency * 0.2 +
            min(self.frequency / 10, 1.0) * 0.1 +
            self.relevance * 0.1
        )


class CognitiveAsset(BaseModel):
    """Activo cognitivo individual."""
    id: str
    asset_type: CognitiveAssetType
    name: str
    content: str
    value: CognitiveValue = Field(default_factory=CognitiveValue)
    tags: List[str] = Field(default_factory=list)
    source: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def use(self) -> None:
        """Marca el activo como usado."""
        self.last_used = datetime.utcnow()
        self.value.frequency += 1
    
    def decay(self, factor: float = 0.95) -> None:
        """Aplica decaimiento temporal."""
        self.value.recency *= factor


# =============================================================================
# PATRONES GOF PARA CAPITAL COGNITIVO
# =============================================================================

# PROTOTYPE PATTERN - Para clonación de activos
# ITERATOR PATTERN - Para navegación de capital
# VISITOR PATTERN - Para operaciones sobre activos
# DECORATOR PATTERN - Para enriquecimiento de activos
# CHAIN OF RESPONSIBILITY - Para procesamiento de aprendizaje


# =============================================================================
# PROTOTYPE PATTERN
# =============================================================================

class CognitiveAssetPrototype:
    """Prototype Pattern para clonación de activos cognitivos."""
    
    @staticmethod
    def clone(asset: CognitiveAsset) -> CognitiveAsset:
        """Clona un activo cognitivo."""
        return CognitiveAsset(
            id=f"{asset.id}_clone_{datetime.utcnow().timestamp()}",
            asset_type=asset.asset_type,
            name=asset.name,
            content=asset.content,
            value=CognitiveValue(
                confidence=asset.value.confidence,
                utility=asset.value.utility,
                recency=asset.value.recency,
                frequency=0,  # Reset frequency for clone
                relevance=asset.value.relevance
            ),
            tags=asset.tags.copy(),
            source=asset.source,
            metadata=asset.metadata.copy()
        )
    
    @staticmethod
    def clone_with_modification(
        asset: CognitiveAsset,
        modifications: Dict[str, Any]
    ) -> CognitiveAsset:
        """Clona con modificaciones."""
        cloned = CognitiveAssetPrototype.clone(asset)
        
        for key, value in modifications.items():
            if hasattr(cloned, key):
                setattr(cloned, key, value)
        
        return cloned


# =============================================================================
# ITERATOR PATTERN
# =============================================================================

class CognitiveIterator(ABC):
    """Iterator Pattern para navegación de capital."""
    
    @abstractmethod
    def has_next(self) -> bool:
        pass
    
    @abstractmethod
    def next(self) -> CognitiveAsset:
        pass
    
    @abstractmethod
    def current(self) -> Optional[CognitiveAsset]:
        pass


class ByTypeIterator(CognitiveIterator):
    """Iterador por tipo de activo."""
    
    def __init__(self, assets: List[CognitiveAsset], asset_type: CognitiveAssetType):
        self.assets = [a for a in assets if a.asset_type == asset_type]
        self.index = 0
    
    def has_next(self) -> bool:
        return self.index < len(self.assets)
    
    def next(self) -> CognitiveAsset:
        asset = self.assets[self.index]
        self.index += 1
        return asset
    
    def current(self) -> Optional[CognitiveAsset]:
        if self.index < len(self.assets):
            return self.assets[self.index]
        return None


class ByValueIterator(CognitiveIterator):
    """Iterador ordenado por valor."""
    
    def __init__(self, assets: List[CognitiveAsset], min_score: float = 0.0):
        self.assets = sorted(
            [a for a in assets if a.value.composite_score >= min_score],
            key=lambda a: a.value.composite_score,
            reverse=True
        )
        self.index = 0
    
    def has_next(self) -> bool:
        return self.index < len(self.assets)
    
    def next(self) -> CognitiveAsset:
        asset = self.assets[self.index]
        self.index += 1
        return asset
    
    def current(self) -> Optional[CognitiveAsset]:
        if self.index < len(self.assets):
            return self.assets[self.index]
        return None


# =============================================================================
# VISITOR PATTERN
# =============================================================================

class CognitiveVisitor(ABC):
    """Visitor Pattern para operaciones sobre activos."""
    
    @abstractmethod
    def visit_knowledge(self, asset: CognitiveAsset) -> Any:
        pass
    
    @abstractmethod
    def visit_skill(self, asset: CognitiveAsset) -> Any:
        pass
    
    @abstractmethod
    def visit_pattern(self, asset: CognitiveAsset) -> Any:
        pass


class ExportVisitor(CognitiveVisitor):
    """Visitor para exportación de activos."""
    
    def __init__(self, format: str = "json"):
        self.format = format
        self.exported: List[Dict[str, Any]] = []
    
    def visit_knowledge(self, asset: CognitiveAsset) -> Dict[str, Any]:
        data = asset.model_dump()
        self.exported.append(data)
        return data
    
    def visit_skill(self, asset: CognitiveAsset) -> Dict[str, Any]:
        data = asset.model_dump()
        data["executable"] = True
        self.exported.append(data)
        return data
    
    def visit_pattern(self, asset: CognitiveAsset) -> Dict[str, Any]:
        data = asset.model_dump()
        data["pattern_type"] = "recognized"
        self.exported.append(data)
        return data


class DecayVisitor(CognitiveVisitor):
    """Visitor para aplicar decaimiento."""
    
    def __init__(self, factor: float = 0.95):
        self.factor = factor
    
    def visit_knowledge(self, asset: CognitiveAsset) -> None:
        asset.decay(self.factor)
    
    def visit_skill(self, asset: CognitiveAsset) -> None:
        asset.decay(self.factor * 0.9)  # Skills decay slower
    
    def visit_pattern(self, asset: CognitiveAsset) -> None:
        asset.decay(self.factor * 0.95)


# =============================================================================
# DECORATOR PATTERN
# =============================================================================

class AssetDecorator(ABC):
    """Decorator Pattern para enriquecimiento de activos."""
    
    def __init__(self, asset: CognitiveAsset):
        self._asset = asset
    
    @property
    def asset(self) -> CognitiveAsset:
        return self._asset
    
    def get_enriched(self) -> CognitiveAsset:
        """Retorna el activo enriquecido."""
        return self._asset


class EmbeddingDecorator(AssetDecorator):
    """Decora un activo con embeddings."""
    
    def __init__(self, asset: CognitiveAsset, embedding: List[float]):
        super().__init__(asset)
        self._embedding = embedding
    
    def get_enriched(self) -> CognitiveAsset:
        enriched = CognitiveAssetPrototype.clone(self._asset)
        enriched.metadata["embedding"] = self._embedding
        enriched.metadata["embedding_dim"] = len(self._embedding)
        return enriched


class ProvenanceDecorator(AssetDecorator):
    """Decora un activo con provenance."""
    
    def __init__(
        self,
        asset: CognitiveAsset,
        source_agent: str,
        source_task: str
    ):
        super().__init__(asset)
        self._source_agent = source_agent
        self._source_task = source_task
    
    def get_enriched(self) -> CognitiveAsset:
        enriched = CognitiveAssetPrototype.clone(self._asset)
        enriched.metadata["provenance"] = {
            "agent": self._source_agent,
            "task": self._source_task,
            "timestamp": datetime.utcnow().isoformat()
        }
        return enriched


# =============================================================================
# CHAIN OF RESPONSIBILITY PATTERN
# =============================================================================

class LearningHandler(ABC):
    """Chain of Responsibility para procesamiento de aprendizaje."""
    
    def __init__(self):
        self._next: Optional[LearningHandler] = None
    
    def set_next(self, handler: 'LearningHandler') -> 'LearningHandler':
        self._next = handler
        return handler
    
    async def handle(self, content: str, context: Dict[str, Any]) -> Optional[CognitiveAsset]:
        result = await self._process(content, context)
        
        if result is None and self._next:
            return await self._next.handle(content, context)
        
        return result
    
    @abstractmethod
    async def _process(
        self,
        content: str,
        context: Dict[str, Any]
    ) -> Optional[CognitiveAsset]:
        pass


class KnowledgeExtractionHandler(LearningHandler):
    """Handler para extraer conocimiento."""
    
    async def _process(
        self,
        content: str,
        context: Dict[str, Any]
    ) -> Optional[CognitiveAsset]:
        # Detectar si es conocimiento
        if any(kw in content.lower() for kw in ["es", "son", "significa", "define"]):
            return CognitiveAsset(
                id=f"knowledge_{hashlib.md5(content.encode()).hexdigest()[:8]}",
                asset_type=CognitiveAssetType.KNOWLEDGE,
                name=content[:50],
                content=content
            )
        return None


class SkillExtractionHandler(LearningHandler):
    """Handler para extraer skills."""
    
    async def _process(
        self,
        content: str,
        context: Dict[str, Any]
    ) -> Optional[CognitiveAsset]:
        # Detectar si es skill
        if any(kw in content.lower() for kw in ["cómo", "pasos", "procedimiento", "método"]):
            return CognitiveAsset(
                id=f"skill_{hashlib.md5(content.encode()).hexdigest()[:8]}",
                asset_type=CognitiveAssetType.SKILL,
                name=content[:50],
                content=content
            )
        return None


class PatternExtractionHandler(LearningHandler):
    """Handler para extraer patrones."""
    
    async def _process(
        self,
        content: str,
        context: Dict[str, Any]
    ) -> Optional[CognitiveAsset]:
        # Detectar patrones
        if "patrón" in content.lower() or "siempre" in content.lower():
            return CognitiveAsset(
                id=f"pattern_{hashlib.md5(content.encode()).hexdigest()[:8]}",
                asset_type=CognitiveAssetType.PATTERN,
                name=content[:50],
                content=content
            )
        return None


# =============================================================================
# COGNITIVE CAPITAL STORE
# =============================================================================

class CognitiveCapitalStore:
    """
    Almacén de Capital Cognitivo.
    Maneja activos cognitivos con valoración y decaimiento.
    """
    
    def __init__(self):
        self._assets: Dict[str, CognitiveAsset] = {}
        self._by_type: Dict[CognitiveAssetType, Set[str]] = defaultdict(set)
        self._by_tag: Dict[str, Set[str]] = defaultdict(set)
        
        # Chain de aprendizaje
        self._learning_chain = self._build_learning_chain()
    
    def _build_learning_chain(self) -> LearningHandler:
        """Construye la cadena de aprendizaje."""
        knowledge = KnowledgeExtractionHandler()
        skill = SkillExtractionHandler()
        pattern = PatternExtractionHandler()
        
        knowledge.set_next(skill).set_next(pattern)
        return knowledge
    
    async def add(self, asset: CognitiveAsset) -> str:
        """Agrega un activo cognitivo."""
        self._assets[asset.id] = asset
        self._by_type[asset.asset_type].add(asset.id)
        
        for tag in asset.tags:
            self._by_tag[tag].add(asset.id)
        
        return asset.id
    
    async def learn(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[CognitiveAsset]:
        """Aprende del contenido."""
        asset = await self._learning_chain.handle(content, context or {})
        
        if asset:
            await self.add(asset)
        
        return asset
    
    def get(self, asset_id: str) -> Optional[CognitiveAsset]:
        """Obtiene un activo por ID."""
        asset = self._assets.get(asset_id)
        if asset:
            asset.use()
        return asset
    
    def get_by_type(
        self,
        asset_type: CognitiveAssetType,
        min_score: float = 0.0
    ) -> List[CognitiveAsset]:
        """Obtiene activos por tipo."""
        assets = [
            self._assets[aid]
            for aid in self._by_type.get(asset_type, set())
            if aid in self._assets
        ]
        
        return [
            a for a in assets
            if a.value.composite_score >= min_score
        ]
    
    def get_by_tag(self, tag: str) -> List[CognitiveAsset]:
        """Obtiene activos por tag."""
        return [
            self._assets[aid]
            for aid in self._by_tag.get(tag, set())
            if aid in self._assets
        ]
    
    def search(
        self,
        query: str,
        top_k: int = 10
    ) -> List[Tuple[CognitiveAsset, float]]:
        """Búsqueda en el capital."""
        results = []
        query_lower = query.lower()
        
        for asset in self._assets.values():
            score = 0.0
            
            if query_lower in asset.name.lower():
                score += 0.5
            if query_lower in asset.content.lower():
                score += 0.3
            if any(query_lower in tag.lower() for tag in asset.tags):
                score += 0.2
            
            score *= asset.value.composite_score
            
            if score > 0:
                results.append((asset, score))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def get_top_assets(
        self,
        limit: int = 10,
        asset_type: Optional[CognitiveAssetType] = None
    ) -> List[CognitiveAsset]:
        """Obtiene los activos de mayor valor."""
        if asset_type:
            assets = self.get_by_type(asset_type)
        else:
            assets = list(self._assets.values())
        
        sorted_assets = sorted(
            assets,
            key=lambda a: a.value.composite_score,
            reverse=True
        )
        
        return sorted_assets[:limit]
    
    def accept(self, visitor: CognitiveVisitor) -> List[Any]:
        """Acepta un visitor."""
        results = []
        
        for asset in self._assets.values():
            if asset.asset_type == CognitiveAssetType.KNOWLEDGE:
                results.append(visitor.visit_knowledge(asset))
            elif asset.asset_type == CognitiveAssetType.SKILL:
                results.append(visitor.visit_skill(asset))
            elif asset.asset_type == CognitiveAssetType.PATTERN:
                results.append(visitor.visit_pattern(asset))
        
        return results
    
    def apply_decay(self, factor: float = 0.95) -> None:
        """Aplica decaimiento a todos los activos."""
        for asset in self._assets.values():
            asset.decay(factor)
    
    def prune(self, threshold: float = 0.1) -> int:
        """Elimina activos por debajo del umbral."""
        to_remove = [
            aid for aid, asset in self._assets.items()
            if asset.value.composite_score < threshold
        ]
        
        for aid in to_remove:
            self.remove(aid)
        
        return len(to_remove)
    
    def remove(self, asset_id: str) -> bool:
        """Elimina un activo."""
        if asset_id not in self._assets:
            return False
        
        asset = self._assets.pop(asset_id)
        self._by_type[asset.asset_type].discard(asset_id)
        
        for tag in asset.tags:
            self._by_tag[tag].discard(asset_id)
        
        return True
    
    def create_iterator(
        self,
        by_type: Optional[CognitiveAssetType] = None,
        min_score: float = 0.0
    ) -> CognitiveIterator:
        """Crea un iterador."""
        assets = list(self._assets.values())
        
        if by_type:
            return ByTypeIterator(assets, by_type)
        else:
            return ByValueIterator(assets, min_score)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas del capital."""
        type_counts = {
            t.value: len(ids)
            for t, ids in self._by_type.items()
        }
        
        total_value = sum(
            a.value.composite_score
            for a in self._assets.values()
        )
        
        return {
            "total_assets": len(self._assets),
            "by_type": type_counts,
            "total_tags": len(self._by_tag),
            "average_value": total_value / len(self._assets) if self._assets else 0,
            "top_10_score": sum(
                a.value.composite_score
                for a in self.get_top_assets(10)
            )
        }


# =============================================================================
# COGNITIVE CAPITAL MANAGER (FACADE)
# =============================================================================

class CognitiveCapitalManager:
    """
    Facade para gestión de Capital Cognitivo.
    Integra todos los componentes.
    """
    
    def __init__(self):
        self.store = CognitiveCapitalStore()
        self._learning_history: List[Dict[str, Any]] = []
    
    async def learn_from_interaction(
        self,
        user_input: str,
        agent_response: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Aprende de una interacción."""
        results = []
        
        # Aprender del input
        input_asset = await self.store.learn(
            user_input,
            {"source": "user_input", **(context or {})}
        )
        if input_asset:
            results.append(("input", input_asset.id))
        
        # Aprender del response
        response_asset = await self.store.learn(
            agent_response,
            {"source": "agent_response", **(context or {})}
        )
        if response_asset:
            results.append(("response", response_asset.id))
        
        # Registrar en historial
        self._learning_history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "input_length": len(user_input),
            "response_length": len(agent_response),
            "assets_created": len(results)
        })
        
        return {
            "learned": True,
            "assets_created": len(results),
            "details": results
        }
    
    async def get_context_for_task(
        self,
        task: str,
        max_assets: int = 10
    ) -> Dict[str, Any]:
        """Obtiene contexto relevante para una tarea."""
        # Buscar activos relevantes
        relevant = self.store.search(task, top_k=max_assets)
        
        # Agrupar por tipo
        by_type: Dict[str, List[str]] = defaultdict(list)
        for asset, score in relevant:
            by_type[asset.asset_type.value].append(asset.content)
        
        return {
            "task": task,
            "relevant_assets": len(relevant),
            "by_type": dict(by_type),
            "top_context": relevant[0][0].content if relevant else None,
            "confidence": relevant[0][1] if relevant else 0.0
        }
    
    def get_capital_report(self) -> Dict[str, Any]:
        """Genera un reporte del capital cognitivo."""
        stats = self.store.get_statistics()
        
        return {
            "cognitive_capital_report": {
                "generated_at": datetime.utcnow().isoformat(),
                "statistics": stats,
                "top_assets": [
                    {
                        "name": a.name,
                        "type": a.asset_type.value,
                        "score": a.value.composite_score
                    }
                    for a in self.store.get_top_assets(5)
                ],
                "learning_events": len(self._learning_history)
            }
        }
    
    def export_capital(self, format: str = "json") -> Dict[str, Any]:
        """Exporta el capital cognitivo."""
        visitor = ExportVisitor(format)
        self.store.accept(visitor)
        
        return {
            "format": format,
            "assets": visitor.exported,
            "exported_at": datetime.utcnow().isoformat()
        }
    
    def apply_decay_cycle(self, factor: float = 0.95) -> Dict[str, Any]:
        """Aplica un ciclo de decaimiento."""
        stats_before = self.store.get_statistics()
        
        self.store.apply_decay(factor)
        pruned = self.store.prune(threshold=0.05)
        
        stats_after = self.store.get_statistics()
        
        return {
            "decay_factor": factor,
            "assets_pruned": pruned,
            "average_value_before": stats_before["average_value"],
            "average_value_after": stats_after["average_value"]
        }


# Import Tuple for type hints
from typing import Tuple
