"""
Cognitive Capital System - Sistema de Capital Cognitivo para Agentes.

## ¿Qué es el Capital Cognitivo?

El Capital Cognitivo es el "conocimiento acumulado" que un agente posee y puede usar.
Incluye:

1. **CONOCIMIENTO** (Knowledge): Información factual y conceptual
   - Hechos, definiciones, procedimientos
   - Documentos procesados
   - Respuestas a preguntas frecuentes

2. **EXPERIENCIA** (Experience): Aprendizajes de interacciones pasadas
   - Casos resueltos exitosamente
   - Errores cometidos y cómo se corrigieron
   - Patrones de usuario identificados

3. **PATRONES** (Patterns): Patrones de comportamiento y decisión
   - Workflows exitosos
   - Decisiones tomadas en contextos específicos
   - Reglas heurísticas aprendidas

4. **HABILIDADES** (Skills): Capacidades desarrolladas
   - Procedimientos dominados
   - Tareas que puede realizar eficientemente
   - Técnicas específicas del dominio

@author: OpenClaw Agent SaaS
"""

from typing import Any, Dict, List, Optional, Set
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# CAPITAL TYPES
# ============================================================================

class CapitalType(str, Enum):
    """Tipos de Capital Cognitivo."""
    KNOWLEDGE = "knowledge"      # Conocimiento factual
    EXPERIENCE = "experience"    # Experiencia de interacciones
    PATTERN = "pattern"          # Patrones de comportamiento
    SKILL = "skill"              # Habilidades desarrolladas
    INSIGHT = "insight"          # Insights derivados
    RELATIONSHIP = "relationship"  # Relaciones entre conceptos


class CapitalSource(str, Enum):
    """Fuente del Capital Cognitivo."""
    DOCUMENT = "document"        # Procesado de documentos
    INTERACTION = "interaction"  # Interacción con usuario
    OBSERVATION = "observation"  # Observación del sistema
    DERIVED = "derived"          # Derivado de otro capital
    INJECTED = "injected"        # Inyectado externamente
    LEARNED = "learned"          # Aprendido automáticamente


class CapitalStatus(str, Enum):
    """Estado del Capital Cognitivo."""
    ACTIVE = "active"            # Activo y accesible
    ARCHIVED = "archived"        # Archivado
    DEPRECATED = "deprecated"    # Deprecado
    DRAFT = "draft"              # Borrador


# ============================================================================
# COGNITIVE CAPITAL MODEL
# ============================================================================

@dataclass
class CognitiveCapital:
    """Una unidad de Capital Cognitivo."""
    id: UUID = field(default_factory=uuid4)
    agent_id: UUID = field(default_factory=uuid4)
    capital_type: CapitalType = CapitalType.KNOWLEDGE
    source: CapitalSource = CapitalSource.INTERACTION
    domain: str = "general"
    sub_domain: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    title: str = ""
    content: str = ""
    keywords: List[str] = field(default_factory=list)
    cognitive_value: float = 0.5
    confidence: float = 0.8
    usage_count: int = 0
    last_used: Optional[datetime] = None
    related_capital_ids: List[UUID] = field(default_factory=list)
    parent_capital_id: Optional[UUID] = None
    status: CapitalStatus = CapitalStatus.ACTIVE
    version: int = 1
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertir a diccionario."""
        return {
            "id": str(self.id),
            "agent_id": str(self.agent_id),
            "capital_type": self.capital_type.value,
            "source": self.source.value,
            "domain": self.domain,
            "sub_domain": self.sub_domain,
            "context": self.context,
            "title": self.title,
            "content": self.content,
            "keywords": self.keywords,
            "cognitive_value": self.cognitive_value,
            "confidence": self.confidence,
            "usage_count": self.usage_count,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "related_capital_ids": [str(c) for c in self.related_capital_ids],
            "parent_capital_id": str(self.parent_capital_id) if self.parent_capital_id else None,
            "status": self.status.value,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "attributes": self.attributes,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CognitiveCapital":
        """Crear desde diccionario."""
        return cls(
            id=UUID(data["id"]),
            agent_id=UUID(data["agent_id"]),
            capital_type=CapitalType(data["capital_type"]),
            source=CapitalSource(data["source"]),
            domain=data["domain"],
            sub_domain=data.get("sub_domain"),
            context=data.get("context", {}),
            title=data.get("title", ""),
            content=data.get("content", ""),
            keywords=data.get("keywords", []),
            cognitive_value=data.get("cognitive_value", 0.5),
            confidence=data.get("confidence", 0.8),
            usage_count=data.get("usage_count", 0),
            last_used=datetime.fromisoformat(data["last_used"]) if data.get("last_used") else None,
            related_capital_ids=[UUID(c) for c in data.get("related_capital_ids", [])],
            parent_capital_id=UUID(data["parent_capital_id"]) if data.get("parent_capital_id") else None,
            status=CapitalStatus(data.get("status", "active")),
            version=data.get("version", 1),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            attributes=data.get("attributes", {}),
        )
    
    def update_usage(self):
        """Actualizar estadísticas de uso."""
        self.usage_count += 1
        self.last_used = datetime.utcnow()
        self.updated_at = datetime.utcnow()


# ============================================================================
# NVIDIA BLUEPRINT DOMAINS
# ============================================================================

class NVIDIABlueprintDomain(str, Enum):
    """Dominios basados en NVIDIA AI Blueprints."""
    
    WAREHOUSE_OPERATIONS = "warehouse_operations"
    CUSTOMER_SERVICE = "customer_service"
    DIGITAL_HUMAN = "digital_human"
    VIDEO_ANALYTICS = "video_analytics"
    ENTERPRISE_RAG = "enterprise_rag"
    DOCUMENT_PROCESSING = "document_processing"
    ENTERPRISE_RESEARCH = "enterprise_research"
    BIOMEDICAL_RESEARCH = "biomedical_research"
    RETAIL_COMMERCE = "retail_commerce"
    CATALOG_ENRICHMENT = "catalog_enrichment"
    DRUG_DISCOVERY = "drug_discovery"
    HEALTHCARE = "healthcare"
    CONTENT_GENERATION = "content_generation"
    PDF_TO_PODCAST = "pdf_to_podcast"
    VISUAL_DESIGN = "visual_design"
    GENERATIVE_AI = "generative_ai"
    ORCHESTRATION = "orchestration"
    GENERAL = "general"


DOMAIN_DESCRIPTIONS = {
    NVIDIABlueprintDomain.WAREHOUSE_OPERATIONS: {
        "name": "Warehouse Operations",
        "description": "Optimización de operaciones de almacén, inventario y logística",
        "agents": ["Equipment Agent", "Operations Agent", "Safety Agent", "Forecasting Agent", "Document Agent"],
        "key_skills": ["asset_tracking", "inventory_management", "safety_monitoring", "demand_forecasting"],
    },
    NVIDIABlueprintDomain.CUSTOMER_SERVICE: {
        "name": "Customer Service",
        "description": "Servicio al cliente con soporte automatizado",
        "agents": ["RAG Agent", "Support Agent", "Router Agent"],
        "key_skills": ["customer_support", "rag_qa", "ticket_routing"],
    },
    NVIDIABlueprintDomain.VIDEO_ANALYTICS: {
        "name": "Video Analytics",
        "description": "Búsqueda, resumen y análisis de video",
        "agents": ["Ingestion Agent", "VLM Agent", "Search Agent", "Summarization Agent"],
        "key_skills": ["video_search", "video_summarization", "visual_qa"],
    },
    NVIDIABlueprintDomain.ENTERPRISE_RAG: {
        "name": "Enterprise RAG",
        "description": "Retrieval-Augmented Generation empresarial",
        "agents": ["Document Agent", "Embedding Agent", "Retrieval Agent", "Generation Agent"],
        "key_skills": ["document_processing", "embedding", "semantic_search", "generation"],
    },
    NVIDIABlueprintDomain.DRUG_DISCOVERY: {
        "name": "Drug Discovery",
        "description": "Descubrimiento de fármacos con IA generativa",
        "agents": ["Protein Agent", "Molecule Agent", "Docking Agent", "Screening Agent"],
        "key_skills": ["protein_structure", "molecule_generation", "virtual_screening"],
    },
    NVIDIABlueprintDomain.HEALTHCARE: {
        "name": "Healthcare",
        "description": "Consultas de salud y programación de citas",
        "agents": ["Consultation Agent", "Scheduling Agent", "Wellness Agent"],
        "key_skills": ["health_consultation", "appointment_scheduling", "wellness_tracking"],
    },
    NVIDIABlueprintDomain.RETAIL_COMMERCE: {
        "name": "Retail & Commerce",
        "description": "E-commerce y gestión de productos",
        "agents": ["Product Agent", "Order Agent", "Customer Agent"],
        "key_skills": ["product_search", "order_management", "customer_service"],
    },
    NVIDIABlueprintDomain.ORCHESTRATION: {
        "name": "Orchestration",
        "description": "Coordinación de múltiples agentes",
        "agents": ["Lead Agent", "Router Agent", "Coordinator Agent"],
        "key_skills": ["task_routing", "agent_coordination", "conflict_resolution"],
    },
}


# ============================================================================
# COGNITIVE CAPITAL STORE
# ============================================================================

class CognitiveCapitalStore:
    """Almacenamiento de Capital Cognitivo."""
    
    def __init__(self):
        self._capitals: Dict[UUID, CognitiveCapital] = {}
        self._agent_index: Dict[UUID, List[UUID]] = {}
        self._domain_index: Dict[str, List[UUID]] = {}
    
    def store(self, capital: CognitiveCapital) -> bool:
        """Almacenar un capital."""
        self._capitals[capital.id] = capital
        
        if capital.agent_id not in self._agent_index:
            self._agent_index[capital.agent_id] = []
        if capital.id not in self._agent_index[capital.agent_id]:
            self._agent_index[capital.agent_id].append(capital.id)
        
        if capital.domain not in self._domain_index:
            self._domain_index[capital.domain] = []
        if capital.id not in self._domain_index[capital.domain]:
            self._domain_index[capital.domain].append(capital.id)
        
        return True
    
    def get(self, capital_id: UUID) -> Optional[CognitiveCapital]:
        return self._capitals.get(capital_id)
    
    def get_by_agent(self, agent_id: UUID) -> List[CognitiveCapital]:
        capital_ids = self._agent_index.get(agent_id, [])
        return [self._capitals[cid] for cid in capital_ids if cid in self._capitals]
    
    def get_by_domain(self, domain: str) -> List[CognitiveCapital]:
        capital_ids = self._domain_index.get(domain, [])
        return [self._capitals[cid] for cid in capital_ids if cid in self._capitals]
    
    def search(self, query: str, limit: int = 10) -> List[CognitiveCapital]:
        results = []
        query_lower = query.lower()
        for capital in self._capitals.values():
            if (query_lower in capital.title.lower() or
                query_lower in capital.content.lower() or
                any(query_lower in kw.lower() for kw in capital.keywords)):
                results.append(capital)
        results.sort(key=lambda c: c.cognitive_value, reverse=True)
        return results[:limit]
    
    def delete(self, capital_id: UUID) -> bool:
        if capital_id not in self._capitals:
            return False
        capital = self._capitals[capital_id]
        del self._capitals[capital_id]
        if capital.agent_id in self._agent_index:
            self._agent_index[capital.agent_id] = [
                cid for cid in self._agent_index[capital.agent_id] if cid != capital_id
            ]
        return True
    
    def get_agent_capital_summary(self, agent_id: UUID) -> Dict[str, Any]:
        capitals = self.get_by_agent(agent_id)
        total_value = sum(c.cognitive_value for c in capitals)
        return {
            "agent_id": str(agent_id),
            "total_capitals": len(capitals),
            "total_cognitive_value": total_value,
            "average_value": total_value / len(capitals) if capitals else 0,
        }


# ============================================================================
# COGNITIVE CAPITAL GENERATOR
# ============================================================================

class CognitiveCapitalGenerator:
    """Generador automático de Capital Cognitivo."""
    
    def __init__(self, store: CognitiveCapitalStore):
        self.store = store
    
    async def generate_from_interaction(
        self,
        agent_id: UUID,
        interaction: Dict[str, Any],
        domain: str = "general",
    ) -> Optional[CognitiveCapital]:
        """Generar capital desde una interacción exitosa."""
        if not interaction.get("success", False):
            return None
        
        capital = CognitiveCapital(
            agent_id=agent_id,
            capital_type=CapitalType.EXPERIENCE,
            source=CapitalSource.INTERACTION,
            domain=domain,
            title=f"Experiencia: {interaction.get('user_input', '')[:50]}",
            content=f"Pregunta: {interaction.get('user_input')}\nRespuesta: {interaction.get('agent_response')}",
            keywords=self._extract_keywords(interaction),
            cognitive_value=self._calculate_value(interaction),
        )
        
        self.store.store(capital)
        return capital
    
    def _extract_keywords(self, interaction: Dict[str, Any]) -> List[str]:
        user_input = interaction.get("user_input", "").lower()
        return [w for w in user_input.split() if len(w) > 4][:5]
    
    def _calculate_value(self, interaction: Dict[str, Any]) -> float:
        value = 0.5
        if interaction.get("success"):
            value += 0.2
        if len(interaction.get("user_input", "")) > 100:
            value += 0.1
        return min(1.0, value)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "CapitalType",
    "CapitalSource", 
    "CapitalStatus",
    "CognitiveCapital",
    "CognitiveCapitalStore",
    "CognitiveCapitalGenerator",
    "NVIDIABlueprintDomain",
    "DOMAIN_DESCRIPTIONS",
]
