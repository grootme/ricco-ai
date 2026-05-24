"""
NEXUS Cognitive Infrastructure - Contextos de Obviedad

## Qué es un Contexto de Obviedad?

Según la Promptología Ontológica (Mauricio Quiroga), el Contexto de Obviedad es:
"El conjunto de supuestos implícitos compartidos que permiten la coordinación 
efectiva entre humanos y agentes de IA sin necesidad de explicitar cada detalle."

El Contexto de Obviedad actúa como:
- El "sistema operativo" del chat/conversación
- El "rayado de cancha" semántico dentro del cual se desarrolla la interacción
- El marco de referencia que delimita y orienta la acción

## Componentes del Contexto de Obviedad

1. TRASFONDO: Conocimiento implícito acumulado
2. MANDATOS: Instrucciones activas permanentes
3. CONDICIONES: Criterios de satisfacción
4. RESTRICCIONES: Límites operativos
5. DOMINIO: Especialización temática

@author: NEXUS - Neural Execution Unified System
"""

from typing import Dict, List, Optional, Any, Set, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4
import asyncio
import json
import hashlib
import logging

logger = logging.getLogger(__name__)

# Type variables
T = TypeVar('T')


class ObviousnessType(str, Enum):
    """Tipos de Contexto de Obviedad"""
    OPERATIONAL = "operational"      # Operaciones cotidianas
    STRATEGIC = "strategic"          # Decisiones estratégicas
    TACTICAL = "tactical"            # Acciones tácticas
    DOMAIN = "domain"                # Conocimiento de dominio
    ORGANIZATIONAL = "organizational" # Políticas organizacionales
    BEHAVIORAL = "behavioral"        # Patrones de comportamiento
    TEMPORAL = "temporal"            # Contextos temporales
    RELATIONAL = "relational"        # Relaciones entre entidades


class ContextStatus(str, Enum):
    """Estado del Contexto de Obviedad"""
    DRAFT = "draft"                  # En construcción
    ACTIVE = "active"                # Activo y en uso
    SUSPENDED = "suspended"          # Suspendido temporalmente
    ARCHIVED = "archived"            # Archivado
    DEPRECATED = "deprecated"        # Deprecado


class ActivationFunction(str, Enum):
    """
    Función de activación para transmisión de contexto
    
    Similar a las funciones de activación en redes neuronales,
    determina qué parte del contexto se transmite al siguiente nivel
    """
    SIGMOID = "sigmoid"              # Transmisión gradual
    RELU = "relu"                    # Transmisión umbral
    TANH = "tanh"                    # Transmisión balanceada
    SOFTMAX = "softmax"              # Transmisión ponderada
    LINEAR = "linear"                # Transmisión directa


# ============================================================================
# TRASFONDO DE OBVIEDAD
# ============================================================================

@dataclass
class TrasfondoObviedad:
    """
    Trasfondo de Obviedad
    
    El conjunto de supuestos implícitos que no necesitan explicitarse
    porque son compartidos por todos los participantes.
    
    Según PPCC: "El contexto implícito compartido con el LLM actúa como 
    un verdadero modelo operativo de cada conversación."
    """
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    
    # Contenido semántico del trasfondo
    assumptions: List[str] = field(default_factory=list)
    implicit_knowledge: Dict[str, Any] = field(default_factory=dict)
    shared_definitions: Dict[str, str] = field(default_factory=dict)
    
    # Gramática del trasfondo (cómo se comunican las cosas)
    communication_patterns: List[str] = field(default_factory=list)
    expected_formats: Dict[str, str] = field(default_factory=dict)
    
    # Peso de transmisión (similar a pesos en redes neuronales)
    transmission_weight: float = 0.5
    activation_function: ActivationFunction = ActivationFunction.SIGMOID
    
    # Metadata
    domain: str = "general"
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def add_assumption(self, assumption: str) -> None:
        """Añade un supuesto implícito"""
        if assumption not in self.assumptions:
            self.assumptions.append(assumption)
            self.updated_at = datetime.utcnow()
    
    def add_shared_definition(self, term: str, definition: str) -> None:
        """Añade una definición compartida"""
        self.shared_definitions[term] = definition
        self.updated_at = datetime.utcnow()
    
    def compute_activation(self, input_signal: float) -> float:
        """
        Computa la función de activación
        
        Determina cuánto del trasfondo se transmite
        """
        if self.activation_function == ActivationFunction.SIGMOID:
            import math
            return 1 / (1 + math.exp(-input_signal * self.transmission_weight))
        elif self.activation_function == ActivationFunction.RELU:
            return max(0, input_signal * self.transmission_weight)
        elif self.activation_function == ActivationFunction.TANH:
            import math
            return math.tanh(input_signal * self.transmission_weight)
        else:
            return input_signal * self.transmission_weight
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "assumptions": self.assumptions,
            "implicit_knowledge": self.implicit_knowledge,
            "shared_definitions": self.shared_definitions,
            "communication_patterns": self.communication_patterns,
            "expected_formats": self.expected_formats,
            "transmission_weight": self.transmission_weight,
            "activation_function": self.activation_function.value,
            "domain": self.domain,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# ============================================================================
# MANDATO ACTIVO
# ============================================================================

@dataclass
class MandatoActivo:
    """
    Mandato Activo
    
    Instrucción permanente que guía el comportamiento del agente.
    A diferencia de los prompts puntuales, los mandatos son persistentes
    y de alto nivel.
    
    Ejemplos:
    - "Negociar antes de producir la respuesta final"
    - "Siempre verificar comprensión antes de ejecutar"
    - "Mantener trazabilidad de todas las decisiones"
    """
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    instruction: str = ""
    priority: int = 5  # 1-10, mayor = más importante
    
    # Condiciones de activación
    triggers: List[str] = field(default_factory=list)
    conditions: Dict[str, Any] = field(default_factory=dict)
    
    # Estado
    is_active: bool = True
    scope: str = "global"  # global, domain, task
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0
    
    def should_trigger(self, context: Dict[str, Any]) -> bool:
        """Determina si el mandato debe activarse"""
        if not self.is_active:
            return False
        
        for trigger in self.triggers:
            if trigger in str(context):
                return True
        
        for key, value in self.conditions.items():
            if context.get(key) != value:
                return False
        
        return True
    
    def trigger(self) -> str:
        """Activa el mandato y retorna la instrucción"""
        self.last_triggered = datetime.utcnow()
        self.trigger_count += 1
        return self.instruction
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "name": self.name,
            "instruction": self.instruction,
            "priority": self.priority,
            "triggers": self.triggers,
            "conditions": self.conditions,
            "is_active": self.is_active,
            "scope": self.scope,
            "created_at": self.created_at.isoformat(),
            "last_triggered": self.last_triggered.isoformat() if self.last_triggered else None,
            "trigger_count": self.trigger_count,
        }


# ============================================================================
# CONDICIONES DE SATISFACCIÓN
# ============================================================================

@dataclass
class CondicionesSatisfaccion:
    """
    Condiciones de Satisfacción
    
    Define qué significa que una tarea o acción sea "exitosa".
    Permite evaluación objetiva del cumplimiento.
    
    Según PPCC: "El ciclo solo se completa mediante una declaración 
    explícita de desempeño."
    """
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    
    # Criterios de éxito (SMART: Specific, Measurable, Achievable, Relevant, Time-bound)
    criteria: List[Dict[str, Any]] = field(default_factory=list)
    
    # Métricas de evaluación
    metrics: Dict[str, float] = field(default_factory=dict)
    thresholds: Dict[str, float] = field(default_factory=dict)
    
    # Umbral de satisfacción
    satisfaction_threshold: float = 0.8  # 80% de criterios cumplidos
    
    # Metadata
    domain: str = "general"
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def add_criterion(
        self,
        name: str,
        description: str,
        weight: float = 1.0,
        required: bool = True
    ) -> None:
        """Añade un criterio de satisfacción"""
        self.criteria.append({
            "name": name,
            "description": description,
            "weight": weight,
            "required": required,
            "evaluated": False,
            "satisfied": False,
        })
    
    def evaluate(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evalúa si se cumplen las condiciones
        
        Returns:
            Dict con score de satisfacción y detalles
        """
        evaluation = {
            "timestamp": datetime.utcnow().isoformat(),
            "criteria_evaluated": 0,
            "criteria_satisfied": 0,
            "required_satisfied": 0,
            "required_total": 0,
            "score": 0.0,
            "satisfied": False,
            "details": [],
        }
        
        total_weight = 0.0
        satisfied_weight = 0.0
        
        for criterion in self.criteria:
            criterion_name = criterion["name"]
            weight = criterion.get("weight", 1.0)
            required = criterion.get("required", True)
            
            # Evaluar criterio
            is_satisfied = self._evaluate_criterion(criterion_name, results)
            criterion["evaluated"] = True
            criterion["satisfied"] = is_satisfied
            
            evaluation["criteria_evaluated"] += 1
            total_weight += weight
            
            if required:
                evaluation["required_total"] += 1
            
            if is_satisfied:
                evaluation["criteria_satisfied"] += 1
                satisfied_weight += weight
                if required:
                    evaluation["required_satisfied"] += 1
            
            evaluation["details"].append({
                "criterion": criterion_name,
                "satisfied": is_satisfied,
                "required": required,
            })
        
        # Calcular score
        if total_weight > 0:
            evaluation["score"] = satisfied_weight / total_weight
        
        # Determinar satisfacción global
        evaluation["satisfied"] = (
            evaluation["score"] >= self.satisfaction_threshold and
            evaluation["required_satisfied"] == evaluation["required_total"]
        )
        
        return evaluation
    
    def _evaluate_criterion(self, criterion_name: str, results: Dict[str, Any]) -> bool:
        """Evalúa un criterio específico"""
        # Buscar en métricas
        if criterion_name in self.metrics:
            threshold = self.thresholds.get(criterion_name, 0.5)
            actual_value = results.get(criterion_name, 0)
            return actual_value >= threshold
        
        # Buscar en resultados directos
        if criterion_name in results:
            return bool(results[criterion_name])
        
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "criteria": self.criteria,
            "metrics": self.metrics,
            "thresholds": self.thresholds,
            "satisfaction_threshold": self.satisfaction_threshold,
            "domain": self.domain,
            "created_at": self.created_at.isoformat(),
        }


# ============================================================================
# CONTEXTO DE OBVIEDAD COMPLETO
# ============================================================================

@dataclass
class ContextoObviedad:
    """
    Contexto de Obviedad Completo
    
    Unidad fundamental de la Infraestructura Cognitiva.
    Combina todos los elementos que permiten la coordinación efectiva.
    
    Según la tesis final: "Las redes neuronales de Contextos de Obviedad 
    representan ese salto desde la automatización aislada a la 
    inteligencia organizacional viva."
    """
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    description: str = ""
    context_type: ObviousnessType = ObviousnessType.OPERATIONAL
    
    # Componentes principales
    trasfondo: Optional[TrasfondoObviedad] = None
    mandatos: List[MandatoActivo] = field(default_factory=list)
    condiciones: Optional[CondicionesSatisfaccion] = None
    
    # Restricciones
    restrictions: List[str] = field(default_factory=list)
    allowed_actions: List[str] = field(default_factory=list)
    forbidden_actions: List[str] = field(default_factory=list)
    
    # Dominio y scope
    domain: str = "general"
    sub_domain: Optional[str] = None
    scope: str = "global"  # global, domain, task, session
    
    # Conexiones con otros contextos (red)
    parent_context_id: Optional[UUID] = None
    child_context_ids: List[UUID] = field(default_factory=list)
    related_context_ids: List[UUID] = field(default_factory=list)
    
    # Estado
    status: ContextStatus = ContextStatus.DRAFT
    
    # Peso de relevancia (para coordinación)
    relevance_weight: float = 0.5
    priority: int = 5
    
    # Estadísticas de uso
    activation_count: int = 0
    last_activated: Optional[datetime] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    
    def initialize_trasfondo(self, name: str = "default") -> TrasfondoObviedad:
        """Inicializa el trasfondo de obviedad"""
        self.trasfondo = TrasfondoObviedad(
            name=f"{self.name}_trasfondo",
            domain=self.domain
        )
        return self.trasfondo
    
    def add_mandato(self, mandato: MandatoActivo) -> None:
        """Añade un mandato activo"""
        self.mandatos.append(mandato)
        # Ordenar por prioridad
        self.mandatos.sort(key=lambda m: m.priority, reverse=True)
        self.updated_at = datetime.utcnow()
    
    def get_active_mandatos(self) -> List[MandatoActivo]:
        """Obtiene mandatos activos ordenados por prioridad"""
        return [m for m in self.mandatos if m.is_active]
    
    def activate(self, context_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Activa el contexto y retorna la información relevante
        """
        self.activation_count += 1
        self.last_activated = datetime.utcnow()
        
        activation_result = {
            "context_id": str(self.id),
            "context_name": self.name,
            "domain": self.domain,
            "trasfondo": self.trasfondo.to_dict() if self.trasfondo else None,
            "active_mandatos": [m.trigger() for m in self.get_active_mandatos()],
            "restrictions": self.restrictions,
            "allowed_actions": self.allowed_actions,
        }
        
        return activation_result
    
    def evaluate_satisfaction(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Evalúa si los resultados satisfacen las condiciones"""
        if not self.condiciones:
            return {"satisfied": True, "message": "No conditions defined"}
        
        return self.condiciones.evaluate(results)
    
    def add_restriction(self, restriction: str) -> None:
        """Añade una restricción"""
        if restriction not in self.restrictions:
            self.restrictions.append(restriction)
            self.updated_at = datetime.utcnow()
    
    def connect_to(self, other_context: "ContextoObviedad", relation: str = "related") -> None:
        """Conecta con otro contexto"""
        if relation == "parent":
            self.parent_context_id = other_context.id
            other_context.child_context_ids.append(self.id)
        elif relation == "child":
            self.child_context_ids.append(other_context.id)
            other_context.parent_context_id = self.id
        else:
            if other_context.id not in self.related_context_ids:
                self.related_context_ids.append(other_context.id)
        
        self.updated_at = datetime.utcnow()
    
    def compute_transmission(self, input_signal: float = 1.0) -> float:
        """
        Computa la transmisión del contexto
        
        Similar a forward pass en redes neuronales
        """
        if self.trasfondo:
            return self.trasfondo.compute_activation(input_signal * self.relevance_weight)
        return input_signal * self.relevance_weight
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "context_type": self.context_type.value,
            "trasfondo": self.trasfondo.to_dict() if self.trasfondo else None,
            "mandatos": [m.to_dict() for m in self.mandatos],
            "condiciones": self.condiciones.to_dict() if self.condiciones else None,
            "restrictions": self.restrictions,
            "allowed_actions": self.allowed_actions,
            "forbidden_actions": self.forbidden_actions,
            "domain": self.domain,
            "sub_domain": self.sub_domain,
            "scope": self.scope,
            "parent_context_id": str(self.parent_context_id) if self.parent_context_id else None,
            "child_context_ids": [str(c) for c in self.child_context_ids],
            "related_context_ids": [str(c) for c in self.related_context_ids],
            "status": self.status.value,
            "relevance_weight": self.relevance_weight,
            "priority": self.priority,
            "activation_count": self.activation_count,
            "last_activated": self.last_activated.isoformat() if self.last_activated else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextoObviedad":
        """Crea desde diccionario"""
        context = cls(
            id=UUID(data["id"]),
            name=data.get("name", ""),
            description=data.get("description", ""),
            context_type=ObviousnessType(data.get("context_type", "operational")),
            domain=data.get("domain", "general"),
            sub_domain=data.get("sub_domain"),
            scope=data.get("scope", "global"),
            status=ContextStatus(data.get("status", "draft")),
            relevance_weight=data.get("relevance_weight", 0.5),
            priority=data.get("priority", 5),
            activation_count=data.get("activation_count", 0),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.utcnow(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.utcnow(),
            created_by=data.get("created_by"),
            restrictions=data.get("restrictions", []),
            allowed_actions=data.get("allowed_actions", []),
            forbidden_actions=data.get("forbidden_actions", []),
        )
        
        if data.get("trasfondo"):
            context.trasfondo = TrasfondoObviedad(**data["trasfondo"])
        
        if data.get("mandatos"):
            context.mandatos = [MandatoActivo(**m) for m in data["mandatos"]]
        
        if data.get("parent_context_id"):
            context.parent_context_id = UUID(data["parent_context_id"])
        
        if data.get("child_context_ids"):
            context.child_context_ids = [UUID(c) for c in data["child_context_ids"]]
        
        if data.get("related_context_ids"):
            context.related_context_ids = [UUID(c) for c in data["related_context_ids"]]
        
        return context


# ============================================================================
# RED DE CONTEXTOS DE OBVIEDAD
# ============================================================================

class RedContextosObviedad:
    """
    Red de Contextos de Obviedad
    
    La infraestructura cognitiva que conecta todos los contextos.
    Permite la coordinación superior entre agentes.
    
    Según la tesis: "Una red de contextos bien entrenada coordina mejor 
    que cualquier organigrama y reduce la necesidad de intervención jerárquica."
    """
    
    def __init__(self, name: str = "NEXUS Cognitive Network"):
        self.name = name
        self.contexts: Dict[UUID, ContextoObviedad] = {}
        self.domain_index: Dict[str, List[UUID]] = {}
        self.type_index: Dict[ObviousnessType, List[UUID]] = {}
        
        # Contexto raíz
        self.root_context_id: Optional[UUID] = None
    
    def add_context(self, context: ContextoObviedad) -> UUID:
        """Añade un contexto a la red"""
        self.contexts[context.id] = context
        
        # Indexar por dominio
        if context.domain not in self.domain_index:
            self.domain_index[context.domain] = []
        self.domain_index[context.domain].append(context.id)
        
        # Indexar por tipo
        if context.context_type not in self.type_index:
            self.type_index[context.context_type] = []
        self.type_index[context.context_type].append(context.id)
        
        # Si no hay contexto raíz, este lo es
        if self.root_context_id is None and context.scope == "global":
            self.root_context_id = context.id
        
        return context.id
    
    def get_context(self, context_id: UUID) -> Optional[ContextoObviedad]:
        """Obtiene un contexto por ID"""
        return self.contexts.get(context_id)
    
    def get_contexts_by_domain(self, domain: str) -> List[ContextoObviedad]:
        """Obtiene contextos por dominio"""
        context_ids = self.domain_index.get(domain, [])
        return [self.contexts[cid] for cid in context_ids if cid in self.contexts]
    
    def get_contexts_by_type(self, context_type: ObviousnessType) -> List[ContextoObviedad]:
        """Obtiene contextos por tipo"""
        context_ids = self.type_index.get(context_type, [])
        return [self.contexts[cid] for cid in context_ids if cid in self.contexts]
    
    def activate_for_domain(self, domain: str, context_data: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Activa todos los contextos relevantes para un dominio
        """
        activations = []
        contexts = self.get_contexts_by_domain(domain)
        
        # Ordenar por prioridad y peso de relevancia
        contexts.sort(key=lambda c: (c.priority, c.relevance_weight), reverse=True)
        
        for context in contexts:
            if context.status == ContextStatus.ACTIVE:
                activation = context.activate(context_data)
                activations.append(activation)
        
        return activations
    
    def compute_network_transmission(self, input_signal: float = 1.0) -> Dict[str, float]:
        """
        Computa la transmisión de señales por toda la red
        
        Similar a forward propagation en redes neuronales
        """
        transmissions = {}
        
        for context_id, context in self.contexts.items():
            if context.status == ContextStatus.ACTIVE:
                transmission = context.compute_transmission(input_signal)
                transmissions[str(context_id)] = transmission
        
        return transmissions
    
    def get_network_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas de la red"""
        return {
            "total_contexts": len(self.contexts),
            "active_contexts": len([c for c in self.contexts.values() if c.status == ContextStatus.ACTIVE]),
            "domains": list(self.domain_index.keys()),
            "contexts_by_domain": {k: len(v) for k, v in self.domain_index.items()},
            "contexts_by_type": {k.value: len(v) for k, v in self.type_index.items()},
            "total_mandatos": sum(len(c.mandatos) for c in self.contexts.values()),
            "total_activations": sum(c.activation_count for c in self.contexts.values()),
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa la red completa"""
        return {
            "name": self.name,
            "root_context_id": str(self.root_context_id) if self.root_context_id else None,
            "contexts": {str(k): v.to_dict() for k, v in self.contexts.items()},
            "domain_index": {k: [str(i) for i in v] for k, v in self.domain_index.items()},
            "metrics": self.get_network_metrics(),
        }


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "ObviousnessType",
    "ContextStatus",
    "ActivationFunction",
    "TrasfondoObviedad",
    "MandatoActivo",
    "CondicionesSatisfaccion",
    "ContextoObviedad",
    "RedContextosObviedad",
]
