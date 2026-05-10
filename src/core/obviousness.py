"""
Trasfondo de Obviedad - Contrato Semántico para Agentes
Implementación basada en OpenClaw Agent SaaS Architecture

El Trasfondo de Obviedad funciona como el "sistema operativo" de cada conversación,
delimitando el horizonte de sentido en el que el agente debe operar.

Dimensiones SMART+R+T:
- S (Specificity): Finalidad específica y técnica
- M (Metric): Criterios cuantitativos de éxito
- A (Achievability): Alcance y fronteras operativas
- R (Relevance): Impacto organizacional y valor del Capital Cognitivo
- T (Time): Restricciones temporales y latencia
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
import json


class ObviousnessDimension(str, Enum):
    """Dimensiones del Trasfondo de Obviedad"""
    SPECIFICITY = "S"   # Finalidad
    METRIC = "M"        # Métrica
    ACHIEVABILITY = "A" # Alcance
    RELEVANCE = "R"     # Relevancia
    TIME = "T"          # Tiempo


class OrganizationalImpact(str, Enum):
    """Niveles de impacto organizacional"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINIMAL = "minimal"


class TaskPriority(str, Enum):
    """Prioridad de la tarea"""
    URGENT = "urgent"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
    BACKGROUND = "background"


class ObviousnessContext(BaseModel):
    """
    Trasfondo de Obviedad - Contrato Semántico
    
    Esta estructura evita que el modelo improvise o recurra a conocimiento
    generalizado ante instrucciones vagas. El agente actúa bajo un 
    "contrato semántico" validado que garantiza la coherencia operativa.
    """
    
    # =====================================================================
    # S - FINALIDAD (Specificity)
    # Objetivo específico y técnico de la tarea
    # =====================================================================
    objective: str = Field(
        ...,
        description="Objetivo técnico específico de la tarea a realizar"
    )
    success_criteria: List[str] = Field(
        default_factory=list,
        description="Criterios específicos que determinan el éxito de la tarea"
    )
    deliverables: List[str] = Field(
        default_factory=list,
        description="Entregables esperados de la tarea"
    )
    
    # =====================================================================
    # M - MÉTRICA (Metric)
    # Criterios cuantitativos de éxito
    # =====================================================================
    metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="Métricas cuantitativas de éxito (ej. recall >= 0.8)"
    )
    target_recall: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Objetivo de recall (0.0 - 1.0)"
    )
    target_precision: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Objetivo de precision (0.0 - 1.0)"
    )
    target_f1_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Objetivo de F1 score (0.0 - 1.0)"
    )
    custom_metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Métricas personalizadas específicas del dominio"
    )
    
    # =====================================================================
    # A - ALCANCE (Achievability)
    # Fronteras operativas positivas y negativas
    # =====================================================================
    positive_boundaries: List[str] = Field(
        default_factory=list,
        description="Acciones y recursos permitidos"
    )
    negative_boundaries: List[str] = Field(
        default_factory=list,
        description="Acciones y recursos prohibidos"
    )
    allowed_tools: List[str] = Field(
        default_factory=list,
        description="Herramientas específicas permitidas"
    )
    restricted_tools: List[str] = Field(
        default_factory=list,
        description="Herramientas prohibidas para esta tarea"
    )
    allowed_files: List[str] = Field(
        default_factory=list,
        description="Patrones de archivos permitidos"
    )
    restricted_files: List[str] = Field(
        default_factory=list,
        description="Patrones de archivos prohibidos"
    )
    allowed_domains: List[str] = Field(
        default_factory=list,
        description="Dominios de datos permitidos"
    )
    sandbox_mode: bool = Field(
        default=True,
        description="Si debe ejecutarse en sandbox aislado"
    )
    
    # =====================================================================
    # R - RELEVANCIA (Relevance)
    # Impacto organizacional y valor del Capital Cognitivo
    # =====================================================================
    organizational_impact: OrganizationalImpact = Field(
        default=OrganizationalImpact.MEDIUM,
        description="Nivel de impacto organizacional"
    )
    cognitive_capital_value: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Valor potencial de Capital Cognitivo (1-10)"
    )
    linked_knowledge_nodes: List[str] = Field(
        default_factory=list,
        description="Nodos de conocimiento relacionados en el grafo"
    )
    business_context: Optional[str] = Field(
        default=None,
        description="Contexto de negocio relevante"
    )
    stakeholder: Optional[str] = Field(
        default=None,
        description="Stakeholder principal de la tarea"
    )
    
    # =====================================================================
    # T - TIEMPO (Time)
    # Restricciones temporales y latencia
    # =====================================================================
    max_latency_seconds: Optional[int] = Field(
        default=None,
        description="Latencia máxima permitida en segundos"
    )
    deadline: Optional[datetime] = Field(
        default=None,
        description="Fecha límite de entrega"
    )
    priority: TaskPriority = Field(
        default=TaskPriority.NORMAL,
        description="Prioridad de la tarea"
    )
    max_iterations: Optional[int] = Field(
        default=None,
        description="Máximo de iteraciones permitidas"
    )
    timeout_seconds: Optional[int] = Field(
        default=300,
        description="Timeout total de ejecución"
    )
    
    # =====================================================================
    # METADATA
    # =====================================================================
    session_id: str = Field(
        ...,
        description="ID de sesión único"
    )
    user_id: str = Field(
        ...,
        description="ID del usuario que solicita"
    )
    domain: Optional[str] = Field(
        default=None,
        description="Dominio industrial (retail, health, industrial, etc.)"
    )
    agent_persona: Optional[str] = Field(
        default=None,
        description="Persona del agente (mentor, assistant, analyst, etc.)"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp de creación"
    )
    parent_context_id: Optional[str] = Field(
        default=None,
        description="ID del contexto padre (para sub-tareas)"
    )
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def to_system_prompt(self) -> str:
        """
        Genera el SYSTEM_PROMPT para inyección en el agente líder.
        
        Este prompt establece el "contrato semántico" que el agente
        debe respetar durante toda la ejecución.
        """
        sections = []
        
        # Header
        sections.append("# TRASFONDO DE OBVIEDAD")
        sections.append("## Contrato Semántico de Ejecución\n")
        
        # S - Finalidad
        sections.append("### FINALIDAD (S)")
        sections.append(f"**Objetivo:** {self.objective}")
        if self.success_criteria:
            sections.append("**Criterios de Éxito:**")
            for criteria in self.success_criteria:
                sections.append(f"- {criteria}")
        if self.deliverables:
            sections.append("**Entregables Esperados:**")
            for deliverable in self.deliverables:
                sections.append(f"- {deliverable}")
        sections.append("")
        
        # M - Métrica
        sections.append("### MÉTRICAS DE ÉXITO (M)")
        if self.metrics:
            for key, value in self.metrics.items():
                sections.append(f"- {key}: {value}")
        if self.target_recall:
            sections.append(f"- Recall objetivo: ≥ {self.target_recall:.0%}")
        if self.target_precision:
            sections.append(f"- Precision objetivo: ≥ {self.target_precision:.0%}")
        if self.target_f1_score:
            sections.append(f"- F1 Score objetivo: ≥ {self.target_f1_score:.0%}")
        sections.append("")
        
        # A - Alcance
        sections.append("### ALCANCE (A)")
        sections.append(f"**Modo Sandbox:** {'Activado' if self.sandbox_mode else 'Desactivado'}")
        if self.positive_boundaries:
            sections.append("**Permitido:**")
            for boundary in self.positive_boundaries:
                sections.append(f"- ✅ {boundary}")
        if self.negative_boundaries:
            sections.append("**Prohibido:**")
            for boundary in self.negative_boundaries:
                sections.append(f"- ❌ {boundary}")
        if self.allowed_tools:
            sections.append(f"**Herramientas Permitidas:** {', '.join(self.allowed_tools)}")
        if self.restricted_tools:
            sections.append(f"**Herramientas Prohibidas:** {', '.join(self.restricted_tools)}")
        sections.append("")
        
        # R - Relevancia
        sections.append("### RELEVANCIA ORGANIZACIONAL (R)")
        sections.append(f"**Impacto:** {self.organizational_impact}")
        sections.append(f"**Valor de Capital Cognitivo:** {self.cognitive_capital_value}/10")
        if self.business_context:
            sections.append(f"**Contexto de Negocio:** {self.business_context}")
        if self.stakeholder:
            sections.append(f"**Stakeholder:** {self.stakeholder}")
        sections.append("")
        
        # T - Tiempo
        sections.append("### RESTRICCIONES TEMPORALES (T)")
        sections.append(f"**Prioridad:** {self.priority}")
        if self.max_latency_seconds:
            sections.append(f"**Latencia Máxima:** {self.max_latency_seconds}s")
        if self.deadline:
            sections.append(f"**Deadline:** {self.deadline.isoformat()}")
        if self.timeout_seconds:
            sections.append(f"**Timeout:** {self.timeout_seconds}s")
        sections.append("")
        
        # Instrucciones de comportamiento
        sections.append("### INSTRUCCIONES DE COMPORTAMIENTO")
        sections.append("1. No procedas hasta confirmar entendimiento del objetivo")
        sections.append("2. Haz visible tu razonamiento durante la ejecución")
        sections.append("3. Si encuentras ambigüedad, solicita aclaración")
        sections.append("4. Reporta progreso de forma estructurada")
        sections.append("5. Deforma una declaración formal al completar")
        
        return "\n".join(sections)
    
    def to_compact_format(self) -> Dict[str, Any]:
        """Formato compacto para transmisión eficiente"""
        return {
            "S": {
                "obj": self.objective[:200],  # Truncar si es muy largo
                "criteria": self.success_criteria[:3]  # Máximo 3
            },
            "M": {
                "recall": self.target_recall,
                "precision": self.target_precision,
                "custom": list(self.metrics.keys())[:5]
            },
            "A": {
                "allow": self.positive_boundaries[:5],
                "deny": self.negative_boundaries[:5],
                "sandbox": self.sandbox_mode
            },
            "R": {
                "impact": self.organizational_impact,
                "ccv": self.cognitive_capital_value
            },
            "T": {
                "priority": self.priority,
                "timeout": self.timeout_seconds
            },
            "meta": {
                "session": self.session_id,
                "user": self.user_id,
                "domain": self.domain
            }
        }
    
    def validate_alignment(self, agent_response: str) -> Dict[str, Any]:
        """
        Valida la alineación de una respuesta del agente con el trasfondo.
        
        Returns:
            Dict con score de alineación y detalles
        """
        issues = []
        score = 1.0
        
        # Verificar mención de objetivo
        response_lower = agent_response.lower()
        objective_keywords = self.objective.lower().split()[:5]
        matches = sum(1 for kw in objective_keywords if kw in response_lower)
        
        if matches < 2:
            issues.append("La respuesta no refleja claramente el objetivo")
            score -= 0.2
        
        # Verificar restricciones violadas
        for restricted in self.restricted_tools + self.negative_boundaries:
            if restricted.lower() in response_lower:
                issues.append(f"Posible violación de restricción: {restricted}")
                score -= 0.3
        
        return {
            "alignment_score": max(0.0, score),
            "issues": issues,
            "passed": score >= 0.7
        }
    
    def is_within_scope(self, action: str) -> bool:
        """Verifica si una acción está dentro del alcance permitido"""
        action_lower = action.lower()
        
        # Verificar restricciones negativas primero
        for restricted in self.negative_boundaries + self.restricted_tools:
            if restricted.lower() in action_lower:
                return False
        
        # Si hay permisos positivos, verificar que la acción esté permitida
        if self.positive_boundaries or self.allowed_tools:
            for allowed in self.positive_boundaries + self.allowed_tools:
                if allowed.lower() in action_lower:
                    return True
            return False
        
        # Sin restricciones específicas, permitir
        return True


class ObviousnessContextBuilder:
    """
    Builder para crear ObviousnessContext de forma fluida.
    
    Usage:
        context = (ObviousnessContextBuilder(session_id, user_id)
            .with_objective("Analizar ventas Q1")
            .with_metrics(recall=0.8, precision=0.85)
            .with_boundaries(allow=["database"], deny=["production"])
            .with_relevance(impact="high", ccv=8)
            .with_time(priority="high", timeout=600)
            .build())
    """
    
    def __init__(self, session_id: str, user_id: str):
        self._data = {
            "session_id": session_id,
            "user_id": user_id
        }
    
    def with_objective(
        self,
        objective: str,
        success_criteria: Optional[List[str]] = None,
        deliverables: Optional[List[str]] = None
    ) -> 'ObviousnessContextBuilder':
        """Establece la finalidad (S)"""
        self._data["objective"] = objective
        if success_criteria:
            self._data["success_criteria"] = success_criteria
        if deliverables:
            self._data["deliverables"] = deliverables
        return self
    
    def with_metrics(
        self,
        recall: Optional[float] = None,
        precision: Optional[float] = None,
        f1: Optional[float] = None,
        custom: Optional[Dict[str, float]] = None
    ) -> 'ObviousnessContextBuilder':
        """Establece las métricas (M)"""
        if recall:
            self._data["target_recall"] = recall
        if precision:
            self._data["target_precision"] = precision
        if f1:
            self._data["target_f1_score"] = f1
        if custom:
            self._data["metrics"] = custom
        return self
    
    def with_boundaries(
        self,
        allow: Optional[List[str]] = None,
        deny: Optional[List[str]] = None,
        tools: Optional[List[str]] = None,
        restricted_tools: Optional[List[str]] = None,
        sandbox: bool = True
    ) -> 'ObviousnessContextBuilder':
        """Establece el alcance (A)"""
        if allow:
            self._data["positive_boundaries"] = allow
        if deny:
            self._data["negative_boundaries"] = deny
        if tools:
            self._data["allowed_tools"] = tools
        if restricted_tools:
            self._data["restricted_tools"] = restricted_tools
        self._data["sandbox_mode"] = sandbox
        return self
    
    def with_relevance(
        self,
        impact: str = "medium",
        ccv: int = 5,
        business_context: Optional[str] = None,
        stakeholder: Optional[str] = None,
        knowledge_nodes: Optional[List[str]] = None
    ) -> 'ObviousnessContextBuilder':
        """Establece la relevancia (R)"""
        self._data["organizational_impact"] = impact
        self._data["cognitive_capital_value"] = ccv
        if business_context:
            self._data["business_context"] = business_context
        if stakeholder:
            self._data["stakeholder"] = stakeholder
        if knowledge_nodes:
            self._data["linked_knowledge_nodes"] = knowledge_nodes
        return self
    
    def with_time(
        self,
        priority: str = "normal",
        timeout: Optional[int] = None,
        latency: Optional[int] = None,
        deadline: Optional[datetime] = None
    ) -> 'ObviousnessContextBuilder':
        """Establece restricciones temporales (T)"""
        self._data["priority"] = priority
        if timeout:
            self._data["timeout_seconds"] = timeout
        if latency:
            self._data["max_latency_seconds"] = latency
        if deadline:
            self._data["deadline"] = deadline
        return self
    
    def with_domain(self, domain: str, persona: Optional[str] = None) -> 'ObviousnessContextBuilder':
        """Establece dominio industrial"""
        self._data["domain"] = domain
        if persona:
            self._data["agent_persona"] = persona
        return self
    
    def with_parent(self, parent_id: str) -> 'ObviousnessContextBuilder':
        """Establece contexto padre para sub-tareas"""
        self._data["parent_context_id"] = parent_id
        return self
    
    def build(self) -> ObviousnessContext:
        """Construye el ObviousnessContext"""
        return ObviousnessContext(**self._data)
