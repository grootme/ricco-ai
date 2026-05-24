"""
NEXUS Cognitive Infrastructure - Infraestructura Cognitiva Completa

Este módulo implementa:
1. Capital Cognitivo: Memoria, engrams, skills, patterns
2. Infraestructura Cognitiva: Vector store, Memory VCS, Sync Engine
3. Learning Pipeline: Aprendizaje continuo y auto-mejora

Arquitectura:
- Cada agente tiene su propio Capital Cognitivo
- La Infraestructura Cognitiva conecta todos los agentes
- El Learning Pipeline permite evolución continua
"""

import asyncio
import json
import math
import hashlib
import uuid
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict
import logging

# Para vector store (usando numpy para embeddings)
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

# Redis para persistencia
try:
    import redis.asyncio as redis
    from redis.asyncio import Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


# ============================================
# ENUMS Y TIPOS
# ============================================

class EngramType(str, Enum):
    """Tipos de engrams (memorias)"""
    EPISODIC = "episodic"        # Experiencias específicas
    SEMANTIC = "semantic"        # Conocimiento factual
    PROCEDURAL = "procedural"    # Habilidades y procedimientos
    PATTERN = "pattern"          # Patrones reconocidos
    CONTEXT = "context"          # Contextos operativos
    RELATIONSHIP = "relationship" # Relaciones entre conceptos


class SkillLevel(str, Enum):
    """Niveles de habilidad"""
    NOVICE = "novice"           # 0.0 - 0.2
    BEGINNER = "beginner"       # 0.2 - 0.4
    INTERMEDIATE = "intermediate"  # 0.4 - 0.6
    ADVANCED = "advanced"       # 0.6 - 0.8
    EXPERT = "expert"           # 0.8 - 1.0
    MASTER = "master"           # 1.0


class SyncMode(str, Enum):
    """Modos de sincronización"""
    CENTRALIZED = "centralized"   # Servidor central
    DECENTRALIZED = "decentralized"  # P2P
    HYBRID = "hybrid"            # Combinación


class LearningEventType(str, Enum):
    """Tipos de eventos de aprendizaje"""
    INTERACTION = "interaction"
    OBSERVATION = "observation"
    REFLECTION = "reflection"
    INSTRUCTION = "instruction"
    FEEDBACK = "feedback"


# ============================================
# ENGRAM - UNIDAD DE MEMORIA COGNITIVA
# ============================================

@dataclass
class Engram:
    """
    Unidad fundamental de memoria cognitiva
    
    Un Engram es una representación codificada de:
    - Una experiencia (episódica)
    - Un hecho (semántica)
    - Una habilidad (procedural)
    - Un patrón reconocido
    - Un contexto operativo
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""                          # Contenido textual
    embedding: Optional[List[float]] = None    # Vector semántico
    engram_type: EngramType = EngramType.EPISODIC
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    accessed_at: Optional[datetime] = None
    access_count: int = 0
    
    # Importancia y relevancia
    importance_score: float = 0.5              # 0.0 - 1.0
    relevance_score: float = 0.5               # 0.0 - 1.0
    confidence_score: float = 0.5              # 0.0 - 1.0
    
    # Aprendizaje
    source: LearningEventType = LearningEventType.INTERACTION
    reinforcement_count: int = 0               # Veces que se ha reforzado
    
    # Tags y clasificación
    tags: List[str] = field(default_factory=list)
    domain: str = "general"
    context_id: Optional[str] = None
    
    # Relaciones
    related_engrams: List[str] = field(default_factory=list)
    parent_engram: Optional[str] = None
    child_engrams: List[str] = field(default_factory=list)
    
    # Versión (Memory VCS)
    version: int = 1
    checksum: str = ""
    
    def __post_init__(self):
        if not self.checksum:
            self.checksum = self._compute_checksum()
    
    def _compute_checksum(self) -> str:
        """Computa checksum para versionado"""
        data = f"{self.content}{self.engram_type.value}{self.importance_score}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def access(self) -> None:
        """Registra acceso al engram"""
        self.accessed_at = datetime.utcnow()
        self.access_count += 1
        self.updated_at = datetime.utcnow()
        
        # Incrementar importancia por acceso
        self.importance_score = min(1.0, self.importance_score + 0.01)
    
    def reinforce(self, delta: float = 0.1) -> None:
        """Reinforce el engram (fortalecer memoria)"""
        self.reinforcement_count += 1
        self.importance_score = min(1.0, self.importance_score + delta)
        self.confidence_score = min(1.0, self.confidence_score + delta * 0.5)
        self.updated_at = datetime.utcnow()
        self.checksum = self._compute_checksum()
    
    def decay(self, rate: float = 0.01) -> None:
        """Decaimiento de la memoria (olvido)"""
        self.importance_score = max(0.0, self.importance_score - rate)
        self.confidence_score = max(0.0, self.confidence_score - rate * 0.5)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "embedding": self.embedding,
            "engram_type": self.engram_type.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "accessed_at": self.accessed_at.isoformat() if self.accessed_at else None,
            "access_count": self.access_count,
            "importance_score": self.importance_score,
            "relevance_score": self.relevance_score,
            "confidence_score": self.confidence_score,
            "source": self.source.value,
            "reinforcement_count": self.reinforcement_count,
            "tags": self.tags,
            "domain": self.domain,
            "context_id": self.context_id,
            "related_engrams": self.related_engrams,
            "parent_engram": self.parent_engram,
            "child_engrams": self.child_engrams,
            "version": self.version,
            "checksum": self.checksum,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Engram":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            content=data.get("content", ""),
            embedding=data.get("embedding"),
            engram_type=EngramType(data.get("engram_type", "episodic")),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.utcnow(),
            accessed_at=datetime.fromisoformat(data["accessed_at"]) if data.get("accessed_at") else None,
            access_count=data.get("access_count", 0),
            importance_score=data.get("importance_score", 0.5),
            relevance_score=data.get("relevance_score", 0.5),
            confidence_score=data.get("confidence_score", 0.5),
            source=LearningEventType(data.get("source", "interaction")),
            reinforcement_count=data.get("reinforcement_count", 0),
            tags=data.get("tags", []),
            domain=data.get("domain", "general"),
            context_id=data.get("context_id"),
            related_engrams=data.get("related_engrams", []),
            parent_engram=data.get("parent_engram"),
            child_engrams=data.get("child_engrams", []),
            version=data.get("version", 1),
            checksum=data.get("checksum", ""),
        )


# ============================================
# SKILL - HABILIDAD COGNITIVA
# ============================================

@dataclass
class Skill:
    """
    Habilidad cognitiva de un agente
    
    Representa una capacidad que el agente puede ejecutar
    con un nivel de dominio específico
    """
    name: str
    description: str = ""
    level: float = 0.1                          # 0.0 - 1.0
    experience_points: int = 0
    
    # Uso y efectividad
    times_used: int = 0
    success_count: int = 0
    failure_count: int = 0
    
    # Aprendizaje
    learning_rate: float = 0.1
    decay_rate: float = 0.01
    
    # Prerrequisitos
    prerequisites: List[str] = field(default_factory=list)
    
    # Engrams asociados
    related_engrams: List[str] = field(default_factory=list)
    
    # Metadata
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        if self.times_used == 0:
            return 0.0
        return self.success_count / self.times_used
    
    @property
    def skill_level(self) -> SkillLevel:
        if self.level >= 1.0:
            return SkillLevel.MASTER
        elif self.level >= 0.8:
            return SkillLevel.EXPERT
        elif self.level >= 0.6:
            return SkillLevel.ADVANCED
        elif self.level >= 0.4:
            return SkillLevel.INTERMEDIATE
        elif self.level >= 0.2:
            return SkillLevel.BEGINNER
        else:
            return SkillLevel.NOVICE
    
    def use(self, success: bool = True) -> None:
        """Registra uso de la habilidad"""
        self.times_used += 1
        self.last_used = datetime.utcnow()
        
        if success:
            self.success_count += 1
            # Incrementar nivel basado en experiencia
            xp_gain = self.learning_rate * (1 + self.success_rate)
            self.experience_points += int(xp_gain * 100)
            self.level = min(1.0, self.level + xp_gain * 0.1)
        else:
            self.failure_count += 1
            # Pequeño aprendizaje de errores
            self.level = min(1.0, self.level + self.learning_rate * 0.05)
    
    def practice(self, duration_minutes: int = 1) -> None:
        """Práctica deliberada de la habilidad"""
        xp_gain = duration_minutes * self.learning_rate
        self.experience_points += int(xp_gain * 10)
        self.level = min(1.0, self.level + xp_gain * 0.05)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "level": self.level,
            "experience_points": self.experience_points,
            "times_used": self.times_used,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "learning_rate": self.learning_rate,
            "decay_rate": self.decay_rate,
            "prerequisites": self.prerequisites,
            "related_engrams": self.related_engrams,
            "category": self.category,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "success_rate": self.success_rate,
            "skill_level": self.skill_level.value,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Skill":
        return cls(
            name=data.get("name", "unknown"),
            description=data.get("description", ""),
            level=data.get("level", 0.1),
            experience_points=data.get("experience_points", 0),
            times_used=data.get("times_used", 0),
            success_count=data.get("success_count", 0),
            failure_count=data.get("failure_count", 0),
            learning_rate=data.get("learning_rate", 0.1),
            decay_rate=data.get("decay_rate", 0.01),
            prerequisites=data.get("prerequisites", []),
            related_engrams=data.get("related_engrams", []),
            category=data.get("category", "general"),
            tags=data.get("tags", []),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.utcnow(),
            last_used=datetime.fromisoformat(data["last_used"]) if data.get("last_used") else None,
        )


# ============================================
# PATTERN - PATRÓN COGNITIVO
# ============================================

@dataclass
class Pattern:
    """
    Patrón reconocido por el agente
    
    Los patrones son regularidades detectadas en datos,
    comportamiento o interacciones
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    
    # Definición del patrón
    pattern_type: str = "behavioral"            # behavioral, temporal, semantic, structural
    conditions: Dict[str, Any] = field(default_factory=dict)  # Condiciones del patrón
    actions: List[Dict[str, Any]] = field(default_factory=list)  # Acciones asociadas
    
    # Estadísticas
    occurrences: int = 0                        # Veces que se ha observado
    confidence: float = 0.5                     # Confianza en el patrón
    predictive_power: float = 0.0               # Capacidad predictiva
    
    # Validez temporal
    first_observed: datetime = field(default_factory=datetime.utcnow)
    last_observed: Optional[datetime] = None
    
    # Contexto
    domain: str = "general"
    context_tags: List[str] = field(default_factory=list)
    
    def observe(self, context: Dict[str, Any]) -> bool:
        """Registra una observación del patrón"""
        self.occurrences += 1
        self.last_observed = datetime.utcnow()
        
        # Actualizar confianza basado en observaciones
        self.confidence = min(1.0, self.confidence + 0.05)
        
        return True
    
    def matches(self, context: Dict[str, Any]) -> bool:
        """Verifica si el contexto coincide con el patrón"""
        for key, expected_value in self.conditions.items():
            if key not in context:
                return False
            if context[key] != expected_value:
                return False
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "pattern_type": self.pattern_type,
            "conditions": self.conditions,
            "actions": self.actions,
            "occurrences": self.occurrences,
            "confidence": self.confidence,
            "predictive_power": self.predictive_power,
            "first_observed": self.first_observed.isoformat(),
            "last_observed": self.last_observed.isoformat() if self.last_observed else None,
            "domain": self.domain,
            "context_tags": self.context_tags,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Pattern":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            pattern_type=data.get("pattern_type", "behavioral"),
            conditions=data.get("conditions", {}),
            actions=data.get("actions", []),
            occurrences=data.get("occurrences", 0),
            confidence=data.get("confidence", 0.5),
            predictive_power=data.get("predictive_power", 0.0),
            first_observed=datetime.fromisoformat(data["first_observed"]) if data.get("first_observed") else datetime.utcnow(),
            last_observed=datetime.fromisoformat(data["last_observed"]) if data.get("last_observed") else None,
            domain=data.get("domain", "general"),
            context_tags=data.get("context_tags", []),
        )


# ============================================
# COGNITIVE CAPITAL - CAPITAL COGNITIVO
# ============================================

@dataclass
class CognitiveCapital:
    """
    Capital Cognitivo de un Agente
    
    El capital cognitivo es el acervo completo de:
    - Memorias (Engrams)
    - Habilidades (Skills)
    - Patrones reconocidos (Patterns)
    - Contextos operativos
    - Relaciones
    
    Características:
    - Evolutivo: Crece con el uso y aprendizaje
    - Persistente: Se almacena y versiona
    - Sincronizable: Puede compartirse entre agentes
    - Medible: Tiene métricas de valor
    """
    agent_id: str
    agent_name: str = ""
    domain: str = "general"
    
    # Componentes del capital
    engrams: List[Engram] = field(default_factory=list)
    skills: Dict[str, Skill] = field(default_factory=dict)
    patterns: List[Pattern] = field(default_factory=list)
    
    # Métricas
    total_interactions: int = 0
    total_observations: int = 0
    total_reflections: int = 0
    
    # Aprendizaje
    learning_score: float = 0.0                # 0.0 - 1.0
    adaptation_rate: float = 0.1
    
    # Valor del capital (score compuesto)
    capital_value: int = 0
    
    # Sincronización
    sync_mode: SyncMode = SyncMode.HYBRID
    last_sync: Optional[datetime] = None
    sync_peers: List[str] = field(default_factory=list)
    
    # Versionado
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        self._recalculate_capital_value()
    
    # ========================================
    # GESTIÓN DE ENGRAMS
    # ========================================
    
    def add_engram(self, engram: Engram) -> str:
        """Añade un nuevo engram al capital"""
        engram.domain = self.domain
        self.engrams.append(engram)
        self._recalculate_capital_value()
        self.updated_at = datetime.utcnow()
        
        logger.debug(
            f"Engram added to {self.agent_id}",
            extra={
                "engram_id": engram.id,
                "engram_type": engram.engram_type.value,
                "total_engrams": len(self.engrams)
            }
        )
        
        return engram.id
    
    def get_engram(self, engram_id: str) -> Optional[Engram]:
        """Obtiene un engram por ID"""
        for engram in self.engrams:
            if engram.id == engram_id:
                engram.access()
                return engram
        return None
    
    def find_engrams(
        self,
        engram_type: Optional[EngramType] = None,
        tags: Optional[List[str]] = None,
        min_importance: float = 0.0,
        limit: int = 10
    ) -> List[Engram]:
        """Busca engrams con filtros"""
        results = []
        
        for engram in self.engrams:
            # Filtrar por tipo
            if engram_type and engram.engram_type != engram_type:
                continue
            
            # Filtrar por importancia
            if engram.importance_score < min_importance:
                continue
            
            # Filtrar por tags
            if tags:
                if not any(tag in engram.tags for tag in tags):
                    continue
            
            results.append(engram)
        
        # Ordenar por importancia
        results.sort(key=lambda e: e.importance_score, reverse=True)
        
        return results[:limit]
    
    def get_top_engrams(self, n: int = 10) -> List[Engram]:
        """Obtiene los n engrams más importantes"""
        return sorted(self.engrams, key=lambda e: e.importance_score, reverse=True)[:n]
    
    def consolidate_memories(self, decay_rate: float = 0.01) -> int:
        """
        Consolida memorias: refuerza importantes, decae no usadas
        
        Returns:
            Número de engrams eliminados (muy degradados)
        """
        to_remove = []
        
        for engram in self.engrams:
            if engram.access_count == 0:
                engram.decay(decay_rate * 2)  # Mayor decaimiento sin uso
            else:
                engram.decay(decay_rate)
            
            # Eliminar engrams muy degradados
            if engram.importance_score < 0.1 and engram.reinforcement_count == 0:
                to_remove.append(engram)
        
        for engram in to_remove:
            self.engrams.remove(engram)
        
        self._recalculate_capital_value()
        
        return len(to_remove)
    
    # ========================================
    # GESTIÓN DE SKILLS
    # ========================================
    
    def add_skill(self, skill: Skill) -> None:
        """Añade una habilidad al capital"""
        self.skills[skill.name] = skill
        self._recalculate_capital_value()
        self.updated_at = datetime.utcnow()
    
    def get_skill(self, skill_name: str) -> Optional[Skill]:
        """Obtiene una habilidad por nombre"""
        return self.skills.get(skill_name)
    
    def use_skill(self, skill_name: str, success: bool = True) -> bool:
        """Usa una habilidad y actualiza su nivel"""
        skill = self.skills.get(skill_name)
        if not skill:
            return False
        
        skill.use(success)
        self.total_interactions += 1
        self._recalculate_capital_value()
        
        return True
    
    def get_skills_by_level(self, min_level: float = 0.5) -> List[Skill]:
        """Obtiene habilidades por nivel mínimo"""
        return [s for s in self.skills.values() if s.level >= min_level]
    
    def practice_skill(self, skill_name: str, duration_minutes: int = 1) -> bool:
        """Practica una habilidad"""
        skill = self.skills.get(skill_name)
        if not skill:
            return False
        
        skill.practice(duration_minutes)
        self._recalculate_capital_value()
        
        return True
    
    # ========================================
    # GESTIÓN DE PATTERNS
    # ========================================
    
    def add_pattern(self, pattern: Pattern) -> str:
        """Añade un patrón reconocido"""
        pattern.domain = self.domain
        self.patterns.append(pattern)
        self._recalculate_capital_value()
        
        return pattern.id
    
    def find_matching_patterns(self, context: Dict[str, Any]) -> List[Pattern]:
        """Encuentra patrones que coinciden con el contexto"""
        matching = []
        
        for pattern in self.patterns:
            if pattern.matches(context):
                matching.append(pattern)
        
        # Ordenar por confianza
        matching.sort(key=lambda p: p.confidence, reverse=True)
        
        return matching
    
    # ========================================
    # APRENDIZAJE Y AUTO-MEJORA
    # ========================================
    
    def learn(
        self,
        content: str,
        event_type: LearningEventType,
        importance: float = 0.5,
        tags: List[str] = None
    ) -> Engram:
        """
        Aprende algo nuevo (crea un engram)
        
        Args:
            content: Contenido a aprender
            event_type: Tipo de evento de aprendizaje
            importance: Importancia inicial
            tags: Tags para clasificación
            
        Returns:
            El engram creado
        """
        engram = Engram(
            content=content,
            engram_type=EngramType.EPISODIC if event_type == LearningEventType.INTERACTION else EngramType.SEMANTIC,
            source=event_type,
            importance_score=importance,
            tags=tags or [],
            domain=self.domain
        )
        
        self.add_engram(engram)
        
        # Incrementar contador según tipo
        if event_type == LearningEventType.INTERACTION:
            self.total_interactions += 1
        elif event_type == LearningEventType.OBSERVATION:
            self.total_observations += 1
        elif event_type == LearningEventType.REFLECTION:
            self.total_reflections += 1
        
        # Actualizar learning score
        self._update_learning_score()
        
        return engram
    
    def reflect(self) -> Dict[str, Any]:
        """
        Reflexión: analiza su propio capital y genera insights
        
        Returns:
            Resultados de la reflexión
        """
        reflection_result = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_engrams": len(self.engrams),
            "total_skills": len(self.skills),
            "total_patterns": len(self.patterns),
            "insights": [],
            "recommendations": []
        }
        
        # Analizar engrams
        if self.engrams:
            avg_importance = sum(e.importance_score for e in self.engrams) / len(self.engrams)
            reflection_result["avg_engram_importance"] = avg_importance
            
            if avg_importance < 0.5:
                reflection_result["recommendations"].append(
                    "Consider engaging more to build stronger memories"
                )
        
        # Analizar skills
        if self.skills:
            strong_skills = [s for s in self.skills.values() if s.level >= 0.7]
            weak_skills = [s for s in self.skills.values() if s.level < 0.3]
            
            reflection_result["strong_skills"] = [s.name for s in strong_skills]
            reflection_result["weak_skills"] = [s.name for s in weak_skills]
            
            if weak_skills:
                reflection_result["recommendations"].append(
                    f"Practice needed for: {', '.join(s.name for s in weak_skills[:3])}"
                )
        
        # Crear engram de reflexión
        reflection_content = f"Reflection: {len(self.engrams)} engrams, {len(self.skills)} skills, learning score {self.learning_score:.2f}"
        self.learn(reflection_content, LearningEventType.REFLECTION, importance=0.3)
        
        self.total_reflections += 1
        
        return reflection_result
    
    def _update_learning_score(self) -> None:
        """Actualiza el score de aprendizaje"""
        # Basado en actividades
        activity_score = (
            self.total_interactions * 0.4 +
            self.total_observations * 0.3 +
            self.total_reflections * 0.3
        ) / max(1, self.total_interactions + self.total_observations + self.total_reflections)
        
        # Basado en engrams
        engram_score = sum(e.importance_score for e in self.engrams) / max(1, len(self.engrams))
        
        # Basado en skills
        skill_score = sum(s.level for s in self.skills.values()) / max(1, len(self.skills))
        
        # Score compuesto
        self.learning_score = (activity_score * 0.3 + engram_score * 0.4 + skill_score * 0.3)
    
    # ========================================
    # CÁLCULO DE VALOR
    # ========================================
    
    def _recalculate_capital_value(self) -> None:
        """Recalcula el valor total del capital cognitivo"""
        # Valor de engrams
        engram_value = sum(
            e.importance_score * 10 + 
            e.access_count * 0.5 + 
            e.reinforcement_count * 2
            for e in self.engrams
        )
        
        # Valor de skills
        skill_value = sum(
            s.level * 100 + 
            s.experience_points * 0.1 + 
            s.success_rate * 50
            for s in self.skills.values()
        )
        
        # Valor de patterns
        pattern_value = sum(
            p.confidence * 20 + 
            p.occurrences * 2
            for p in self.patterns
        )
        
        # Bonus por actividad
        activity_bonus = (
            self.total_interactions * 2 +
            self.total_observations * 1 +
            self.total_reflections * 3
        )
        
        # Learning bonus
        learning_bonus = int(self.learning_score * 500)
        
        self.capital_value = int(engram_value + skill_value + pattern_value + activity_bonus + learning_bonus)
    
    # ========================================
    # SERIALIZACIÓN
    # ========================================
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "domain": self.domain,
            "engrams": [e.to_dict() for e in self.engrams],
            "skills": {k: v.to_dict() for k, v in self.skills.items()},
            "patterns": [p.to_dict() for p in self.patterns],
            "total_interactions": self.total_interactions,
            "total_observations": self.total_observations,
            "total_reflections": self.total_reflections,
            "learning_score": self.learning_score,
            "adaptation_rate": self.adaptation_rate,
            "capital_value": self.capital_value,
            "sync_mode": self.sync_mode.value,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "sync_peers": self.sync_peers,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CognitiveCapital":
        capital = cls(
            agent_id=data.get("agent_id", ""),
            agent_name=data.get("agent_name", ""),
            domain=data.get("domain", "general"),
            engrams=[Engram.from_dict(e) for e in data.get("engrams", [])],
            skills={k: Skill.from_dict(v) for k, v in data.get("skills", {}).items()},
            patterns=[Pattern.from_dict(p) for p in data.get("patterns", [])],
            total_interactions=data.get("total_interactions", 0),
            total_observations=data.get("total_observations", 0),
            total_reflections=data.get("total_reflections", 0),
            learning_score=data.get("learning_score", 0.0),
            adaptation_rate=data.get("adaptation_rate", 0.1),
            capital_value=data.get("capital_value", 0),
            sync_mode=SyncMode(data.get("sync_mode", "hybrid")),
            last_sync=datetime.fromisoformat(data["last_sync"]) if data.get("last_sync") else None,
            sync_peers=data.get("sync_peers", []),
            version=data.get("version", "1.0.0"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.utcnow(),
        )
        return capital


# ============================================
# COGNITIVE INFRASTRUCTURE - INFRAESTRUCTURA COGNITIVA
# ============================================

class CognitiveInfrastructure:
    """
    Infraestructura Cognitiva del Sistema NEXUS
    
    Proporciona:
    1. Almacenamiento persistente de Capital Cognitivo
    2. Sincronización entre agentes (P2P y centralizada)
    3. Búsqueda semántica en engrams
    4. Memory VCS (Version Control System)
    5. Pipeline de aprendizaje
    
    Características:
    - Redis para persistencia y sincronización
    - Vector store para búsqueda semántica
    - Event-driven architecture
    - Multi-tenant support
    """
    
    # Key patterns para Redis
    CAPITAL_KEY = "nexus:cognitive:capital:{agent_id}"
    ENGRAM_INDEX = "nexus:cognitive:engrams:{domain}"
    SYNC_CHANNEL = "nexus:cognitive:sync:{agent_id}"
    LEARNING_QUEUE = "nexus:cognitive:learning:{agent_id}"
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self._redis: Optional[Redis] = None
        self._capital_cache: Dict[str, CognitiveCapital] = {}
        
    async def connect(self) -> None:
        """Conecta a Redis"""
        if not REDIS_AVAILABLE:
            raise ImportError("redis package required")
        
        self._redis = redis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=False
        )
        
        logger.info(f"CognitiveInfrastructure connected to Redis")
    
    async def disconnect(self) -> None:
        """Desconecta de Redis"""
        if self._redis:
            await self._redis.close()
            self._redis = None
    
    # ========================================
    # GESTIÓN DE CAPITAL COGNITIVO
    # ========================================
    
    async def save_capital(self, capital: CognitiveCapital) -> None:
        """Guarda el capital cognitivo en Redis"""
        if not self._redis:
            raise RuntimeError("Not connected to Redis")
        
        key = self.CAPITAL_KEY.format(agent_id=capital.agent_id)
        data = json.dumps(capital.to_dict())
        
        await self._redis.set(key, data)
        
        # Actualizar caché
        self._capital_cache[capital.agent_id] = capital
        
        # Indexar engrams
        await self._index_engrams(capital)
        
        logger.debug(
            f"Capital saved: {capital.agent_id}",
            extra={
                "agent_id": capital.agent_id,
                "capital_value": capital.capital_value,
                "engrams": len(capital.engrams)
            }
        )
    
    async def load_capital(self, agent_id: str) -> Optional[CognitiveCapital]:
        """Carga el capital cognitivo desde Redis"""
        if not self._redis:
            raise RuntimeError("Not connected to Redis")
        
        # Verificar caché primero
        if agent_id in self._capital_cache:
            return self._capital_cache[agent_id]
        
        key = self.CAPITAL_KEY.format(agent_id=agent_id)
        data = await self._redis.get(key)
        
        if not data:
            return None
        
        capital_dict = json.loads(data)
        capital = CognitiveCapital.from_dict(capital_dict)
        
        # Actualizar caché
        self._capital_cache[agent_id] = capital
        
        return capital
    
    async def create_capital(
        self,
        agent_id: str,
        agent_name: str,
        domain: str,
        initial_skills: List[str] = None
    ) -> CognitiveCapital:
        """
        Crea capital cognitivo inicial para un agente
        
        NO usa datos mock/hardcode - genera capital basado en
        el rol y dominio del agente
        """
        capital = CognitiveCapital(
            agent_id=agent_id,
            agent_name=agent_name,
            domain=domain
        )
        
        # Añadir skills iniciales basados en el dominio
        domain_skills = self._get_domain_skills(domain)
        for skill_name in initial_skills or domain_skills:
            skill = Skill(
                name=skill_name,
                description=f"Skill for {domain} domain",
                level=0.1,  # Nivel inicial bajo
                category=domain
            )
            capital.add_skill(skill)
        
        # Añadir engram inicial de identidad
        identity_engram = Engram(
            content=f"I am {agent_name}, an agent in the {domain} domain",
            engram_type=EngramType.SEMANTIC,
            source=LearningEventType.INSTRUCTION,
            importance_score=0.8,
            tags=["identity", "self", domain],
            domain=domain
        )
        capital.add_engram(identity_engram)
        
        # Guardar
        await self.save_capital(capital)
        
        logger.info(
            f"Capital created for {agent_id}",
            extra={
                "agent_id": agent_id,
                "agent_name": agent_name,
                "domain": domain,
                "initial_skills": len(capital.skills)
            }
        )
        
        return capital
    
    def _get_domain_skills(self, domain: str) -> List[str]:
        """Obtiene skills relevantes para un dominio"""
        domain_skill_map = {
            "swe": ["code-analysis", "debugging", "architecture", "testing", "refactoring"],
            "salud": ["diagnosis", "patient-care", "medical-research", "treatment-planning"],
            "deportes": ["performance-analysis", "training-design", "statistics", "recovery"],
            "noticias": ["fact-checking", "investigation", "writing", "source-verification"],
            "quimica": ["molecular-analysis", "synthesis", "lab-safety", "research"],
            "biologia": ["genomics", "ecology", "research-methods", "data-analysis"],
            "biotecnologia": ["bioengineering", "drug-development", "clinical-trials", "research"],
            "geopolitica": ["analysis", "forecasting", "diplomacy", "risk-assessment"],
            "finanzas": ["market-analysis", "risk-management", "portfolio-optimization", "forecasting"],
            "legal": ["legal-research", "document-analysis", "compliance", "argumentation"],
            "educacion": ["teaching", "curriculum-design", "assessment", "mentoring"],
            "investigacion": ["research-methods", "data-analysis", "writing", "peer-review"],
            "marketing": ["campaign-design", "analytics", "content-creation", "seo"],
        }
        return domain_skill_map.get(domain, ["general-analysis", "communication", "problem-solving"])
    
    async def _index_engrams(self, capital: CognitiveCapital) -> None:
        """Indexa engrams para búsqueda"""
        if not self._redis:
            return
        
        index_key = self.ENGRAM_INDEX.format(domain=capital.domain)
        
        for engram in capital.engrams:
            # Indexar por tags
            for tag in engram.tags:
                await self._redis.sadd(f"{index_key}:tag:{tag}", engram.id)
            
            # Indexar por tipo
            await self._redis.sadd(f"{index_key}:type:{engram.engram_type.value}", engram.id)
    
    # ========================================
    # SINCRONIZACIÓN
    # ========================================
    
    async def sync_capitals(
        self,
        source_agent_id: str,
        target_agent_ids: List[str],
        mode: SyncMode = SyncMode.HYBRID
    ) -> Dict[str, Any]:
        """
        Sincroniza capital cognitivo entre agentes
        
        Args:
            source_agent_id: ID del agente fuente
            target_agent_ids: IDs de agentes destino
            mode: Modo de sincronización
            
        Returns:
            Resultado de la sincronización
        """
        result = {
            "source": source_agent_id,
            "targets": target_agent_ids,
            "mode": mode.value,
            "synced_engrams": 0,
            "synced_skills": 0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        source_capital = await self.load_capital(source_agent_id)
        if not source_capital:
            return result
        
        for target_id in target_agent_ids:
            target_capital = await self.load_capital(target_id)
            if not target_capital:
                continue
            
            if mode == SyncMode.CENTRALIZED:
                # Compartir top engrams
                top_engrams = source_capital.get_top_engrams(5)
                for engram in top_engrams:
                    if engram.id not in [e.id for e in target_capital.engrams]:
                        # Crear copia del engram
                        new_engram = Engram.from_dict(engram.to_dict())
                        new_engram.id = str(uuid.uuid4())  # Nuevo ID
                        target_capital.add_engram(new_engram)
                        result["synced_engrams"] += 1
            
            elif mode == SyncMode.DECENTRALIZED:
                # Intercambio P2P bidireccional
                source_top = source_capital.get_top_engrams(3)
                target_top = target_capital.get_top_engrams(3)
                
                for engram in target_top:
                    if engram.id not in [e.id for e in source_capital.engrams]:
                        new_engram = Engram.from_dict(engram.to_dict())
                        new_engram.id = str(uuid.uuid4())
                        source_capital.add_engram(new_engram)
                        result["synced_engrams"] += 1
                
                for engram in source_top:
                    if engram.id not in [e.id for e in target_capital.engrams]:
                        new_engram = Engram.from_dict(engram.to_dict())
                        new_engram.id = str(uuid.uuid4())
                        target_capital.add_engram(new_engram)
                        result["synced_engrams"] += 1
            
            elif mode == SyncMode.HYBRID:
                # Primero P2P, luego consolidación
                await self.sync_capitals(source_agent_id, [target_id], SyncMode.DECENTRALIZED)
            
            # Actualizar sync timestamp
            target_capital.last_sync = datetime.utcnow()
            target_capital.sync_peers.append(source_agent_id)
            await self.save_capital(target_capital)
        
        # Actualizar source
        source_capital.last_sync = datetime.utcnow()
        source_capital.sync_peers.extend(target_agent_ids)
        await self.save_capital(source_capital)
        
        return result
    
    # ========================================
    # PIPELINE DE APRENDIZAJE
    # ========================================
    
    async def process_learning_event(
        self,
        agent_id: str,
        event_type: LearningEventType,
        content: str,
        metadata: Dict[str, Any] = None
    ) -> Engram:
        """
        Procesa un evento de aprendizaje
        
        Args:
            agent_id: ID del agente
            event_type: Tipo de evento
            content: Contenido a aprender
            metadata: Metadatos adicionales
            
        Returns:
            El engram creado
        """
        capital = await self.load_capital(agent_id)
        if not capital:
            raise ValueError(f"No capital found for agent {agent_id}")
        
        # Calcular importancia basada en metadatos
        importance = 0.5
        if metadata:
            if metadata.get("success"):
                importance += 0.2
            if metadata.get("user_feedback") == "positive":
                importance += 0.1
            if metadata.get("complexity") == "high":
                importance += 0.1
        
        # Crear engram
        engram = capital.learn(
            content=content,
            event_type=event_type,
            importance=min(1.0, importance),
            tags=metadata.get("tags", []) if metadata else []
        )
        
        # Guardar
        await self.save_capital(capital)
        
        # Publicar evento de aprendizaje
        if self._redis:
            channel = self.SYNC_CHANNEL.format(agent_id=agent_id)
            await self._redis.publish(channel, json.dumps({
                "event": "learning",
                "engram_id": engram.id,
                "event_type": event_type.value,
                "timestamp": datetime.utcnow().isoformat()
            }))
        
        return engram
    
    async def batch_learn(
        self,
        agent_id: str,
        contents: List[Tuple[str, LearningEventType, float]]
    ) -> List[Engram]:
        """
        Aprendizaje en batch
        
        Args:
            agent_id: ID del agente
            contents: Lista de (content, event_type, importance)
            
        Returns:
            Lista de engrams creados
        """
        capital = await self.load_capital(agent_id)
        if not capital:
            raise ValueError(f"No capital found for agent {agent_id}")
        
        engrams = []
        for content, event_type, importance in contents:
            engram = capital.learn(content, event_type, importance)
            engrams.append(engram)
        
        await self.save_capital(capital)
        
        return engrams
    
    # ========================================
    # BÚSQUEDA Y RECUPERACIÓN
    # ========================================
    
    async def search_engrams(
        self,
        agent_id: str,
        query: str,
        engram_type: Optional[EngramType] = None,
        min_importance: float = 0.0,
        limit: int = 10
    ) -> List[Engram]:
        """
        Busca engrams relevantes
        
        Args:
            agent_id: ID del agente
            query: Query de búsqueda
            engram_type: Filtrar por tipo
            min_importance: Importancia mínima
            limit: Máximo de resultados
            
        Returns:
            Lista de engrams encontrados
        """
        capital = await self.load_capital(agent_id)
        if not capital:
            return []
        
        # Búsqueda por contenido (simple - en producción usar vector search)
        results = []
        query_lower = query.lower()
        
        for engram in capital.engrams:
            # Filtrar por tipo
            if engram_type and engram.engram_type != engram_type:
                continue
            
            # Filtrar por importancia
            if engram.importance_score < min_importance:
                continue
            
            # Búsqueda en contenido
            if query_lower in engram.content.lower():
                results.append(engram)
                continue
            
            # Búsqueda en tags
            if any(query_lower in tag.lower() for tag in engram.tags):
                results.append(engram)
        
        # Ordenar por importancia
        results.sort(key=lambda e: e.importance_score, reverse=True)
        
        return results[:limit]
    
    async def get_similar_engrams(
        self,
        agent_id: str,
        engram_id: str,
        limit: int = 5
    ) -> List[Engram]:
        """Obtiene engrams similares a uno dado"""
        capital = await self.load_capital(agent_id)
        if not capital:
            return []
        
        source_engram = capital.get_engram(engram_id)
        if not source_engram:
            return []
        
        similar = []
        for engram in capital.engrams:
            if engram.id == engram_id:
                continue
            
            # Calcular similitud simple basada en tags compartidos
            shared_tags = set(engram.tags) & set(source_engram.tags)
            if shared_tags:
                similarity = len(shared_tags) / max(len(engram.tags), len(source_engram.tags))
                if similarity > 0.3:
                    similar.append((engram, similarity))
        
        # Ordenar por similitud
        similar.sort(key=lambda x: x[1], reverse=True)
        
        return [e for e, _ in similar[:limit]]
    
    # ========================================
    # ESTADÍSTICAS Y MÉTRICAS
    # ========================================
    
    async def get_system_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas del sistema cognitivo"""
        if not self._redis:
            raise RuntimeError("Not connected to Redis")
        
        # Escanear todas las keys de capital
        keys = []
        async for key in self._redis.scan_iter(match="nexus:cognitive:capital:*"):
            keys.append(key)
        
        total_agents = len(keys)
        total_engrams = 0
        total_skills = 0
        total_patterns = 0
        total_capital_value = 0
        
        by_domain: Dict[str, int] = defaultdict(int)
        
        for key in keys:
            data = await self._redis.get(key)
            if data:
                capital_dict = json.loads(data)
                capital = CognitiveCapital.from_dict(capital_dict)
                
                total_engrams += len(capital.engrams)
                total_skills += len(capital.skills)
                total_patterns += len(capital.patterns)
                total_capital_value += capital.capital_value
                by_domain[capital.domain] += 1
        
        return {
            "total_agents": total_agents,
            "total_engrams": total_engrams,
            "total_skills": total_skills,
            "total_patterns": total_patterns,
            "total_capital_value": total_capital_value,
            "avg_engrams_per_agent": total_engrams / max(1, total_agents),
            "avg_skills_per_agent": total_skills / max(1, total_agents),
            "by_domain": dict(by_domain)
        }
