"""
Agent Profile System - Arquitectura basada en Capacidades.

Un agente NO es un "tipo" - es una entidad configurada con:
- Skills: Qué sabe hacer
- Tools/MCP: Qué herramientas tiene
- Prompt/Contexto: Cómo se comporta
- Memoria/Capital Cognitivo: Qué conoce

El "dominio" o "especialización" es una ETIQUETA DESCRIPTIVA,
no una restricción arquitectónica.

@author: OpenClaw Agent SaaS
@philosophy: Agents are defined by what they HAVE and DO, not by an enum type.
"""

from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field, field_validator
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum


# ============================================================================
# CAPABILITIES - Lo que el agente PUEDE hacer
# ============================================================================

class SkillRef(BaseModel):
    """Referencia a una skill en el SkillsRegistry."""
    skill_id: str
    skill_name: str
    proficiency: float = Field(default=1.0, ge=0.0, le=1.0)
    enabled: bool = True


class ToolRef(BaseModel):
    """Referencia a una herramienta disponible."""
    tool_name: str
    source: str = "mcp"  # "mcp", "custom", "builtin"
    permissions: List[str] = Field(default_factory=lambda: ["read", "execute"])
    enabled: bool = True


class MCPRef(BaseModel):
    """Referencia a un servidor MCP."""
    mcp_id: str
    mcp_name: str
    tools: List[str] = Field(default_factory=list)
    enabled: bool = True


class MemoryScope(BaseModel):
    """Alcance de la memoria del agente."""
    domains: List[str] = Field(default_factory=list)  # Dominios de conocimiento
    access_level: str = "domain"  # "global", "domain", "session"
    retention_policy: str = "persistent"  # "persistent", "session", "ephemeral"
    max_entries: int = 10000
    enable_versioning: bool = True
    enable_relations: bool = True  # Knowledge graph


# ============================================================================
# BEHAVIOR - Cómo el agente se comporta
# ============================================================================

class PromptContext(BaseModel):
    """Contexto del prompt del sistema."""
    system_prompt: str
    role_description: str = ""
    behavioral_guidelines: List[str] = Field(default_factory=list)
    response_format: Optional[str] = None
    tone: str = "professional"  # "professional", "casual", "friendly", "formal"
    language: str = "es"


class ExecutionPattern(str, Enum):
    """
    Patrones de ejecución - CÓMO se ejecuta el agente.
    NOTA: Estos NO son tipos de agentes, son PATRONES de ejecución.
    """
    LLM = "llm"              # Agente LLM simple
    A2A = "a2a"              # Agent-to-Agent
    SEQUENTIAL = "sequential"  # Ejecución secuencial de sub-agentes
    PARALLEL = "parallel"    # Ejecución paralela de sub-agentes
    LOOP = "loop"            # Ejecución en bucle
    WORKFLOW = "workflow"    # Flujo de trabajo con nodos y edges
    TASK = "task"            # Agente basado en tareas


class OrchestrationRole(str, Enum):
    """
    Rol de orquestación - Posición en la jerarquía del swarm.
    NOTA: Esto define RESPONSABILIDADES, no un "tipo" de agente.
    """
    LEAD = "lead"            # Coordinador principal
    SPECIALIST = "specialist"  # Especialista en un área
    WORKER = "worker"        # Ejecutor de tareas
    SUPERVISOR = "supervisor"  # Supervisor de calidad


# ============================================================================
# AGENT PROFILE - La definición completa del agente
# ============================================================================

class AgentProfile(BaseModel):
    """
    Perfil completo de un agente.
    
    Un agente se define por lo que TIENE y HACE, no por un "tipo".
    El campo 'domain' es una ETIQUETA DESCRIPTIVA, no una restricción.
    
    Ejemplo:
        Un agente "commerce" es commerce porque tiene:
        - skills: ["product_search", "order_management", "payment_processing"]
        - mcps: ["payment-gateway", "inventory-system"]
        - prompt: "You are an e-commerce assistant..."
        - memory_scope.domains: ["commerce", "orders", "products"]
        
        NO porque un enum diga AgentType.COMMERCE.
    """
    
    # Identidad
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str = ""
    
    # Etiqueta descriptiva de dominio (NO es un tipo restrictivo)
    domain: str = "general"  # "commerce", "health", "finance", "logistics", etc.
    sub_domains: List[str] = Field(default_factory=list)
    
    # CAPACIDADES - Lo que el agente PUEDE hacer
    skills: List[SkillRef] = Field(default_factory=list)
    tools: List[ToolRef] = Field(default_factory=list)
    mcps: List[MCPRef] = Field(default_factory=list)
    
    # MEMORIA - Capital Cognitivo
    memory_scope: MemoryScope = Field(default_factory=MemoryScope)
    
    # COMPORTAMIENTO - Cómo actúa
    prompt_context: Optional[PromptContext] = None
    
    # PATRÓN DE EJECUCIÓN - Cómo se ejecuta
    execution_pattern: ExecutionPattern = ExecutionPattern.LLM
    
    # ROL DE ORQUESTACIÓN - Posición en el swarm
    orchestration_role: OrchestrationRole = OrchestrationRole.SPECIALIST
    
    # SUB-AGENTES (para patrones sequential, parallel, loop, workflow)
    sub_agent_ids: List[UUID] = Field(default_factory=list)
    
    # CONFIGURACIÓN DE EJECUCIÓN
    model: str = "openai/gpt-oss"  # Modelo LLM a usar
    temperature: float = 0.7
    max_tokens: int = 4096
    
    # METADATOS
    tags: List[str] = Field(default_factory=list)
    version: str = "1.0.0"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    enabled: bool = True
    
    # CONFIGURACIÓN ADICIONAL (extensible)
    extra_config: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator("domain")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        """El dominio es solo una etiqueta, puede ser cualquier string."""
        return v.lower().replace(" ", "_")
    
    def get_skill_ids(self) -> List[str]:
        """Obtener IDs de todas las skills habilitadas."""
        return [s.skill_id for s in self.skills if s.enabled]
    
    def get_tool_names(self) -> List[str]:
        """Obtener nombres de todas las tools habilitadas."""
        return [t.tool_name for t in self.tools if t.enabled]
    
    def get_mcp_tools(self) -> Dict[str, List[str]]:
        """Obtener herramientas por MCP."""
        return {m.mcp_name: m.tools for m in self.mcps if m.enabled}
    
    def has_skill(self, skill_name: str) -> bool:
        """Verificar si el agente tiene una skill específica."""
        return any(s.skill_name == skill_name and s.enabled for s in self.skills)
    
    def has_tool(self, tool_name: str) -> bool:
        """Verificar si el agente tiene acceso a una herramienta."""
        return any(t.tool_name == tool_name and t.enabled for t in self.tools)
    
    def get_capabilities_summary(self) -> Dict[str, Any]:
        """Obtener resumen de capacidades del agente."""
        return {
            "domain": self.domain,
            "skills_count": len([s for s in self.skills if s.enabled]),
            "tools_count": len([t for t in self.tools if t.enabled]),
            "mcps_count": len([m for m in self.mcps if m.enabled]),
            "memory_domains": self.memory_scope.domains,
            "execution_pattern": self.execution_pattern.value,
            "orchestration_role": self.orchestration_role.value,
        }


# ============================================================================
# AGENT PROFILE BUILDER - Constructor fluido
# ============================================================================

class AgentProfileBuilder:
    """
    Builder fluido para crear perfiles de agentes.
    
    Uso:
        profile = (AgentProfileBuilder("Mi Agente")
            .with_domain("commerce")
            .with_skill("product_search", proficiency=0.9)
            .with_mcp("payment-gateway", tools=["process_payment", "refund"])
            .with_prompt("You are a helpful commerce assistant...")
            .with_memory_domains("commerce", "orders")
            .build())
    """
    
    def __init__(self, name: str):
        self._name = name
        self._description = ""
        self._domain = "general"
        self._sub_domains: List[str] = []
        self._skills: List[SkillRef] = []
        self._tools: List[ToolRef] = []
        self._mcps: List[MCPRef] = []
        self._memory_scope = MemoryScope()
        self._prompt_context: Optional[PromptContext] = None
        self._execution_pattern = ExecutionPattern.LLM
        self._orchestration_role = OrchestrationRole.SPECIALIST
        self._sub_agent_ids: List[UUID] = []
        self._model = "openai/gpt-oss"
        self._temperature = 0.7
        self._max_tokens = 4096
        self._tags: List[str] = []
        self._extra_config: Dict[str, Any] = {}
    
    def with_description(self, description: str) -> "AgentProfileBuilder":
        self._description = description
        return self
    
    def with_domain(self, domain: str, sub_domains: Optional[List[str]] = None) -> "AgentProfileBuilder":
        self._domain = domain
        if sub_domains:
            self._sub_domains = sub_domains
        return self
    
    def with_skill(
        self, 
        skill_id: str, 
        skill_name: str, 
        proficiency: float = 1.0,
        enabled: bool = True
    ) -> "AgentProfileBuilder":
        self._skills.append(SkillRef(
            skill_id=skill_id,
            skill_name=skill_name,
            proficiency=proficiency,
            enabled=enabled
        ))
        return self
    
    def with_skills(self, skills: List[Dict[str, Any]]) -> "AgentProfileBuilder":
        for s in skills:
            self.with_skill(**s)
        return self
    
    def with_tool(
        self,
        tool_name: str,
        source: str = "mcp",
        permissions: Optional[List[str]] = None,
        enabled: bool = True
    ) -> "AgentProfileBuilder":
        self._tools.append(ToolRef(
            tool_name=tool_name,
            source=source,
            permissions=permissions or ["read", "execute"],
            enabled=enabled
        ))
        return self
    
    def with_mcp(
        self,
        mcp_id: str,
        mcp_name: str,
        tools: Optional[List[str]] = None,
        enabled: bool = True
    ) -> "AgentProfileBuilder":
        self._mcps.append(MCPRef(
            mcp_id=mcp_id,
            mcp_name=mcp_name,
            tools=tools or [],
            enabled=enabled
        ))
        return self
    
    def with_memory_scope(
        self,
        domains: Optional[List[str]] = None,
        access_level: str = "domain",
        retention_policy: str = "persistent",
        max_entries: int = 10000
    ) -> "AgentProfileBuilder":
        self._memory_scope = MemoryScope(
            domains=domains or [],
            access_level=access_level,
            retention_policy=retention_policy,
            max_entries=max_entries
        )
        return self
    
    def with_memory_domains(self, *domains: str) -> "AgentProfileBuilder":
        self._memory_scope.domains = list(domains)
        return self
    
    def with_prompt(
        self,
        system_prompt: str,
        role_description: str = "",
        tone: str = "professional",
        language: str = "es",
        behavioral_guidelines: Optional[List[str]] = None
    ) -> "AgentProfileBuilder":
        self._prompt_context = PromptContext(
            system_prompt=system_prompt,
            role_description=role_description,
            tone=tone,
            language=language,
            behavioral_guidelines=behavioral_guidelines or []
        )
        return self
    
    def with_execution_pattern(self, pattern: ExecutionPattern) -> "AgentProfileBuilder":
        self._execution_pattern = pattern
        return self
    
    def with_orchestration_role(self, role: OrchestrationRole) -> "AgentProfileBuilder":
        self._orchestration_role = role
        return self
    
    def as_lead(self) -> "AgentProfileBuilder":
        """Configurar como agente Lead (coordinador)."""
        self._orchestration_role = OrchestrationRole.LEAD
        return self
    
    def as_specialist(self) -> "AgentProfileBuilder":
        """Configurar como agente Specialist."""
        self._orchestration_role = OrchestrationRole.SPECIALIST
        return self
    
    def with_sub_agents(self, agent_ids: List[UUID]) -> "AgentProfileBuilder":
        self._sub_agent_ids = agent_ids
        return self
    
    def with_model(self, model: str, temperature: float = 0.7, max_tokens: int = 4096) -> "AgentProfileBuilder":
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        return self
    
    def with_tags(self, *tags: str) -> "AgentProfileBuilder":
        self._tags = list(tags)
        return self
    
    def with_extra_config(self, key: str, value: Any) -> "AgentProfileBuilder":
        self._extra_config[key] = value
        return self
    
    def build(self) -> AgentProfile:
        """Construir el perfil del agente."""
        return AgentProfile(
            name=self._name,
            description=self._description,
            domain=self._domain,
            sub_domains=self._sub_domains,
            skills=self._skills,
            tools=self._tools,
            mcps=self._mcps,
            memory_scope=self._memory_scope,
            prompt_context=self._prompt_context,
            execution_pattern=self._execution_pattern,
            orchestration_role=self._orchestration_role,
            sub_agent_ids=self._sub_agent_ids,
            model=self._model,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            tags=self._tags,
            extra_config=self._extra_config,
        )


# ============================================================================
# PROFILE REGISTRY - Registro de perfiles
# ============================================================================

class AgentProfileRegistry:
    """
    Registro central de perfiles de agentes.
    
    Permite:
    - Registrar perfiles por nombre/ID
    - Buscar perfiles por dominio, skills, tools
    - Crear instancias de agentes desde perfiles
    """
    
    def __init__(self):
        self._profiles: Dict[UUID, AgentProfile] = {}
        self._name_index: Dict[str, UUID] = {}
        self._domain_index: Dict[str, List[UUID]] = {}
        self._skill_index: Dict[str, List[UUID]] = {}
    
    def register(self, profile: AgentProfile) -> None:
        """Registrar un perfil."""
        self._profiles[profile.id] = profile
        self._name_index[profile.name.lower()] = profile.id
        
        # Indexar por dominio
        if profile.domain not in self._domain_index:
            self._domain_index[profile.domain] = []
        self._domain_index[profile.domain].append(profile.id)
        
        # Indexar por skills
        for skill in profile.skills:
            if skill.skill_name not in self._skill_index:
                self._skill_index[skill.skill_name] = []
            self._skill_index[skill.skill_name].append(profile.id)
    
    def get(self, profile_id: UUID) -> Optional[AgentProfile]:
        """Obtener perfil por ID."""
        return self._profiles.get(profile_id)
    
    def get_by_name(self, name: str) -> Optional[AgentProfile]:
        """Obtener perfil por nombre."""
        profile_id = self._name_index.get(name.lower())
        if profile_id:
            return self._profiles.get(profile_id)
        return None
    
    def find_by_domain(self, domain: str) -> List[AgentProfile]:
        """Buscar perfiles por dominio."""
        profile_ids = self._domain_index.get(domain.lower(), [])
        return [self._profiles[pid] for pid in profile_ids if pid in self._profiles]
    
    def find_by_skill(self, skill_name: str) -> List[AgentProfile]:
        """Buscar perfiles que tengan una skill específica."""
        profile_ids = self._skill_index.get(skill_name.lower(), [])
        return [self._profiles[pid] for pid in profile_ids if pid in self._profiles]
    
    def find_capable_agents(
        self,
        required_skills: Optional[List[str]] = None,
        required_tools: Optional[List[str]] = None,
        domain: Optional[str] = None,
    ) -> List[AgentProfile]:
        """
        Encontrar agentes capaces de realizar una tarea.
        
        Busca agentes que tengan TODAS las skills y tools requeridas.
        """
        candidates = list(self._profiles.values())
        
        if domain:
            candidates = [p for p in candidates if p.domain == domain.lower()]
        
        if required_skills:
            candidates = [
                p for p in candidates
                if all(p.has_skill(s) for s in required_skills)
            ]
        
        if required_tools:
            candidates = [
                p for p in candidates
                if all(p.has_tool(t) for t in required_tools)
            ]
        
        return candidates
    
    def list_all(self) -> List[AgentProfile]:
        """Listar todos los perfiles."""
        return list(self._profiles.values())
    
    def remove(self, profile_id: UUID) -> bool:
        """Eliminar un perfil."""
        if profile_id not in self._profiles:
            return False
        
        profile = self._profiles[profile_id]
        
        # Limpiar índices
        del self._profiles[profile_id]
        self._name_index.pop(profile.name.lower(), None)
        
        if profile.domain in self._domain_index:
            self._domain_index[profile.domain] = [
                pid for pid in self._domain_index[profile.domain] if pid != profile_id
            ]
        
        for skill in profile.skills:
            if skill.skill_name in self._skill_index:
                self._skill_index[skill.skill_name] = [
                    pid for pid in self._skill_index[skill.skill_name] if pid != profile_id
                ]
        
        return True


# ============================================================================
# PRE-BUILT PROFILES - Perfiles pre-configurados (plantillas)
# ============================================================================

def create_commerce_profile(name: str = "Commerce Agent") -> AgentProfile:
    """Crear perfil de agente de comercio (plantilla)."""
    return (AgentProfileBuilder(name)
        .with_description("Agente especializado en e-commerce y gestión de órdenes")
        .with_domain("commerce", sub_domains=["orders", "products", "payments"])
        .with_skill("product_search", "product_search", proficiency=0.95)
        .with_skill("order_management", "order_management", proficiency=0.9)
        .with_skill("payment_processing", "payment_processing", proficiency=0.85)
        .with_mcp("payment-gateway", "payment-gateway", tools=["process_payment", "refund", "verify"])
        .with_mcp("inventory-system", "inventory-system", tools=["check_stock", "reserve", "release"])
        .with_memory_domains("commerce", "orders", "products", "customers")
        .with_prompt(
            "You are a helpful e-commerce assistant. Help customers find products, "
            "manage their orders, and process payments securely.",
            role_description="Asistente de comercio electrónico",
            tone="friendly"
        )
        .with_tags("commerce", "e-commerce", "orders", "sales")
        .build())


def create_health_profile(name: str = "Health Agent") -> AgentProfile:
    """Crear perfil de agente de salud (plantilla)."""
    return (AgentProfileBuilder(name)
        .with_description("Agente especializado en consultas de salud y bienestar")
        .with_domain("health", sub_domains=["consultations", "appointments", "wellness"])
        .with_skill("symptom_assessment", "symptom_assessment", proficiency=0.8)
        .with_skill("appointment_scheduling", "appointment_scheduling", proficiency=0.95)
        .with_skill("health_information", "health_information", proficiency=0.85)
        .with_mcp("booking-system", "booking-system", tools=["book_appointment", "cancel", "reschedule"])
        .with_memory_domains("health", "appointments", "wellness")
        .with_prompt(
            "You are a health consultation assistant. Help users with general health "
            "information, symptom assessment guidance, and appointment scheduling. "
            "Always remind users to consult healthcare professionals for medical advice.",
            role_description="Asistente de consultas de salud",
            tone="professional"
        )
        .with_tags("health", "wellness", "appointments", "consultations")
        .build())


def create_finance_profile(name: str = "Finance Agent") -> AgentProfile:
    """Crear perfil de agente financiero (plantilla)."""
    return (AgentProfileBuilder(name)
        .with_description("Agente especializado en operaciones y asesoría financiera")
        .with_domain("finance", sub_domains=["banking", "investments", "advisory"])
        .with_skill("financial_analysis", "financial_analysis", proficiency=0.9)
        .with_skill("investment_guidance", "investment_guidance", proficiency=0.85)
        .with_skill("transaction_management", "transaction_management", proficiency=0.9)
        .with_mcp("banking-api", "banking-api", tools=["check_balance", "transfer", "history"])
        .with_mcp("market-data", "market-data", tools=["get_quotes", "get_news", "get_trends"])
        .with_memory_domains("finance", "investments", "transactions")
        .with_prompt(
            "You are a financial advisory assistant. Help users with financial "
            "information, investment guidance, and transaction management. "
            "Always include appropriate disclaimers about financial advice.",
            role_description="Asistente de asesoría financiera",
            tone="professional"
        )
        .with_tags("finance", "banking", "investments", "advisory")
        .build())


def create_logistics_profile(name: str = "Logistics Agent") -> AgentProfile:
    """Crear perfil de agente de logística (plantilla)."""
    return (AgentProfileBuilder(name)
        .with_description("Agente especializado en envíos y logística")
        .with_domain("logistics", sub_domains=["shipping", "tracking", "inventory"])
        .with_skill("shipment_tracking", "shipment_tracking", proficiency=0.95)
        .with_skill("delivery_planning", "delivery_planning", proficiency=0.85)
        .with_skill("inventory_management", "inventory_management", proficiency=0.9)
        .with_mcp("shipping-carriers", "shipping-carriers", tools=["track_package", "estimate_delivery", "create_label"])
        .with_mcp("warehouse-system", "warehouse-system", tools=["check_inventory", "reserve_stock", "update_location"])
        .with_memory_domains("logistics", "shipments", "tracking", "inventory")
        .with_prompt(
            "You are a logistics assistant. Help users track shipments, "
            "plan deliveries, and manage inventory efficiently.",
            role_description="Asistente de logística y envíos",
            tone="professional"
        )
        .with_tags("logistics", "shipping", "tracking", "delivery")
        .build())


def create_orchestrator_profile(name: str = "Lead Orchestrator") -> AgentProfile:
    """Crear perfil de agente orquestador principal (plantilla)."""
    return (AgentProfileBuilder(name)
        .with_description("Agente coordinador principal del swarm")
        .with_domain("orchestration", sub_domains=["coordination", "delegation", "routing"])
        .with_skill("task_routing", "task_routing", proficiency=0.95)
        .with_skill("agent_coordination", "agent_coordination", proficiency=0.95)
        .with_skill("conflict_resolution", "conflict_resolution", proficiency=0.9)
        .as_lead()
        .with_memory_domains("orchestration", "routing", "agents")
        .with_prompt(
            "You are the lead orchestrator agent. Your role is to coordinate "
            "the swarm of specialist agents, route tasks appropriately, "
            "and ensure efficient collaboration between agents.",
            role_description="Coordinador del swarm de agentes",
            tone="professional"
        )
        .with_tags("orchestrator", "lead", "coordination", "routing")
        .build())


# Instancia global del registro
profile_registry = AgentProfileRegistry()

# Registrar perfiles pre-built
for create_fn in [create_commerce_profile, create_health_profile, create_finance_profile, 
                   create_logistics_profile, create_orchestrator_profile]:
    profile = create_fn()
    profile_registry.register(profile)
