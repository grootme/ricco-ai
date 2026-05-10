"""
NEXUS - Neural Execution Unified System
IOVBA Groups - Grupo de agentes orientado a dominio
IOVBA = Investigador, Observador, Validador, Builder, Asistente

Este módulo implementa el stack estándar de 5 agentes orientados a dominio
con ciclo de capital cognitivo automejorado centralizado y descentralizado.
"""

from typing import Dict, List, Optional, Any, Literal, TypedDict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import uuid
import re
import json

# ============================================
# PLATFORM BRANDING
# ============================================

PLATFORM_BRAND = {
    "name": "NEXUS",
    "full_name": "Neural Execution Unified System",
    "tagline": "Intelligent Agent Orchestration",
    "version": "2.0.0"
}

# IOVBA Role Types
IOVBARole = Literal["investigador", "observador", "validador", "builder", "asistente"]

# Domain Types
IOVBADomain = Literal[
    "swe", "salud", "deportes", "noticias", "quimica",
    "biologia", "biotecnologia", "geopolitica", "finanzas",
    "legal", "educacion", "investigacion", "marketing", "custom"
]


# ============================================
# DOMAIN BRANDING
# ============================================

@dataclass
class IOVBADomainBrand:
    """Branding elegante para cada dominio IOVBA"""
    domain: str
    name: str
    elegant_name: str
    tagline: str
    icon: str
    color: str
    description: str


DOMAIN_BRANDING: Dict[IOVBADomain, IOVBADomainBrand] = {
    "swe": IOVBADomainBrand(
        domain="swe",
        name="Software Engineering",
        elegant_name="CODEX",
        tagline="Architecting Digital Excellence",
        icon="Code",
        color="#3B82F6",
        description="Unidad de ingeniería de software para desarrollo, testing y arquitectura de sistemas"
    ),
    "salud": IOVBADomainBrand(
        domain="salud",
        name="Salud y Medicina",
        elegant_name="VITALIS",
        tagline="Advancing Healthcare Intelligence",
        icon="Heart",
        color="#EF4444",
        description="Unidad de salud para diagnóstico, investigación médica y análisis clínico"
    ),
    "deportes": IOVBADomainBrand(
        domain="deportes",
        name="Deportes",
        elegant_name="ATHLON",
        tagline="Peak Performance Analytics",
        icon="Trophy",
        color="#F59E0B",
        description="Unidad de análisis deportivo para performance, estadísticas y predicciones"
    ),
    "noticias": IOVBADomainBrand(
        domain="noticias",
        name="Noticias y Periodismo",
        elegant_name="VERITAS",
        tagline="Truth Through Intelligence",
        icon="Newspaper",
        color="#6366F1",
        description="Unidad de noticias para investigación, verificación y análisis periodístico"
    ),
    "quimica": IOVBADomainBrand(
        domain="quimica",
        name="Química",
        elegant_name="ALCHEMY",
        tagline="Molecular Intelligence",
        icon="FlaskConical",
        color="#8B5CF6",
        description="Unidad de investigación química para análisis molecular y síntesis"
    ),
    "biologia": IOVBADomainBrand(
        domain="biologia",
        name="Biología",
        elegant_name="GENESIS",
        tagline="Life Sciences Intelligence",
        icon="Dna",
        color="#10B981",
        description="Unidad de investigación biológica para genómica y análisis de sistemas vivos"
    ),
    "biotecnologia": IOVBADomainBrand(
        domain="biotecnologia",
        name="Biotecnología",
        elegant_name="HELIX",
        tagline="Engineering Life Solutions",
        icon="Atom",
        color="#14B8A6",
        description="Unidad de biotecnología para bioingeniería y aplicaciones terapéuticas"
    ),
    "geopolitica": IOVBADomainBrand(
        domain="geopolitica",
        name="Geopolítica",
        elegant_name="DIPLOMAT",
        tagline="Strategic Global Intelligence",
        icon="Globe",
        color="#F97316",
        description="Unidad de análisis geopolítico para inteligencia estratégica y relaciones internacionales"
    ),
    "finanzas": IOVBADomainBrand(
        domain="finanzas",
        name="Finanzas",
        elegant_name="APEX",
        tagline="Financial Intelligence Redefined",
        icon="TrendingUp",
        color="#059669",
        description="Unidad de análisis financiero para mercados, inversiones y riesgos"
    ),
    "legal": IOVBADomainBrand(
        domain="legal",
        name="Legal",
        elegant_name="JUSTITIA",
        tagline="Legal Intelligence & Justice",
        icon="Scale",
        color="#7C3AED",
        description="Unidad de análisis legal para jurisprudencia, compliance y contratos"
    ),
    "educacion": IOVBADomainBrand(
        domain="educacion",
        name="Educación",
        elegant_name="MENTOR",
        tagline="Transforming Education Intelligence",
        icon="GraduationCap",
        color="#EC4899",
        description="Unidad de educación para aprendizaje personalizado y contenido pedagógico"
    ),
    "investigacion": IOVBADomainBrand(
        domain="investigacion",
        name="Investigación",
        elegant_name="PIONEER",
        tagline="Pushing Knowledge Boundaries",
        icon="Microscope",
        color="#0EA5E9",
        description="Unidad de investigación científica para descubrimiento y publicación académica"
    ),
    "marketing": IOVBADomainBrand(
        domain="marketing",
        name="Marketing",
        elegant_name="PRISMA",
        tagline="Multifaceted Marketing Intelligence",
        icon="Megaphone",
        color="#D946EF",
        description="Unidad de marketing para campañas, análisis de audiencia y optimización"
    ),
    "custom": IOVBADomainBrand(
        domain="custom",
        name="Personalizado",
        elegant_name="CUSTOM",
        tagline="Tailored Intelligence Solutions",
        icon="Settings",
        color="#64748B",
        description="Unidad personalizada para dominios específicos y configuraciones a medida"
    ),
}


# ============================================
# ROLE BRANDING
# ============================================

@dataclass
class IOVBARoleBrand:
    """Branding elegante para cada rol IOVBA"""
    role: str
    elegant_name: str
    tagline: str
    description: str
    icon: str
    color: str
    gradient: str


ROLE_BRANDING: Dict[IOVBARole, IOVBARoleBrand] = {
    "investigador": IOVBARoleBrand(
        role="investigador",
        elegant_name="INVESTIGATOR",
        tagline="Discovery & Analysis",
        description="Investiga profundamente, analiza datos y descubre insights ocultos",
        icon="Microscope",
        color="#3B82F6",
        gradient="from-blue-500 to-cyan-500"
    ),
    "observador": IOVBARoleBrand(
        role="observador",
        elegant_name="OBSERVER",
        tagline="Monitoring & Patterns",
        description="Monitorea sistemas, detecta patrones y anomalías",
        icon="Eye",
        color="#F59E0B",
        gradient="from-amber-500 to-orange-500"
    ),
    "validador": IOVBARoleBrand(
        role="validador",
        elegant_name="VALIDATOR",
        tagline="Quality & Verification",
        description="Valida resultados, asegura calidad y verifica compliance",
        icon="Shield",
        color="#10B981",
        gradient="from-emerald-500 to-teal-500"
    ),
    "builder": IOVBARoleBrand(
        role="builder",
        elegant_name="BUILDER",
        tagline="Creation & Implementation",
        description="Construye soluciones, implementa sistemas y optimiza código",
        icon="Hammer",
        color="#8B5CF6",
        gradient="from-violet-500 to-purple-500"
    ),
    "asistente": IOVBARoleBrand(
        role="asistente",
        elegant_name="ASSISTANT",
        tagline="Coordination & Support",
        description="Coordina equipos, facilita comunicación y gestiona documentación",
        icon="HelpCircle",
        color="#14B8A6",
        gradient="from-teal-500 to-cyan-500"
    ),
}


class AgentStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    LEARNING = "learning"
    ERROR = "error"


class CapitalSyncMode(str, Enum):
    CENTRALIZED = "centralized"  # Sincronización con servidor central
    DECENTRALIZED = "decentralized"  # P2P entre agentes
    HYBRID = "hybrid"  # Combinación de ambos


@dataclass
class Engram:
    """Unidad de memoria cognitiva"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    content: str = ""
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    access_count: int = 0
    importance_score: float = 0.5
    source: Literal["interaction", "observation", "reflection", "instruction"] = "interaction"
    tags: List[str] = field(default_factory=list)
    
    def access(self) -> None:
        """Incrementa contador de acceso"""
        self.access_count += 1
        self.updated_at = datetime.utcnow().isoformat()


@dataclass
class CognitiveCapital:
    """
    Capital Cognitivo del agente
    Incluye engrams, métricas y configuración de sincronización
    """
    agent_id: str
    total_engrams: int = 0
    total_interactions: int = 0
    learning_score: float = 0.0
    domains: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    mcp_servers: List[str] = field(default_factory=list)
    memory_vcs_version: str = "v1.0.0"
    last_updated: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    capital_value: int = 0
    engrams: List[Engram] = field(default_factory=list)
    
    # Auto-mejora
    auto_improve_enabled: bool = True
    improvement_rate: float = 0.0
    last_improvement: Optional[str] = None
    
    # Sincronización
    sync_mode: CapitalSyncMode = CapitalSyncMode.HYBRID
    last_sync: Optional[str] = None
    sync_peers: List[str] = field(default_factory=list)
    
    def add_engram(self, engram: Engram) -> None:
        """Añade un nuevo engram"""
        self.engrams.append(engram)
        self.total_engrams = len(self.engrams)
        self._recalculate_capital()
        self.updated_at = datetime.utcnow().isoformat()
    
    def _recalculate_capital(self) -> None:
        """Recalcula el valor del capital cognitivo"""
        base_value = self.total_engrams * 10
        interaction_bonus = self.total_interactions * 2
        learning_bonus = int(self.learning_score * 1000)
        importance_bonus = sum(e.importance_score for e in self.engrams) * 5
        
        self.capital_value = int(base_value + interaction_bonus + learning_bonus + importance_bonus)
    
    def improve(self, improvement_delta: float) -> None:
        """Auto-mejora del capital"""
        if self.auto_improve_enabled:
            self.learning_score = min(1.0, self.learning_score + improvement_delta)
            self.improvement_rate = improvement_delta
            self.last_improvement = datetime.utcnow().isoformat()
            self._recalculate_capital()
    
    def get_top_engrams(self, n: int = 10) -> List[Engram]:
        """Obtiene los n engrams más importantes"""
        return sorted(self.engrams, key=lambda e: e.importance_score, reverse=True)[:n]


@dataclass
class AgentProfile:
    """Perfil de un agente IOVBA"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    domain: IOVBADomain = "swe"
    iovba_role: Optional[IOVBARole] = None
    skills: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    mcp_servers: List[str] = field(default_factory=list)
    prompt_template: str = ""
    status: AgentStatus = AgentStatus.ACTIVE
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    cognitive_capital: Optional[CognitiveCapital] = None
    
    # Métricas
    total_interactions: int = 0
    success_rate: float = 0.0
    avg_response_time: float = 0.0
    capital_growth: float = 0.0
    last_interaction: Optional[str] = None
    
    def __post_init__(self):
        if self.cognitive_capital is None:
            self.cognitive_capital = CognitiveCapital(agent_id=self.id)


@dataclass
class IOVBAGroup:
    """
    Grupo IOVBA - 5 agentes orientados a dominio
    Investigador, Observador, Validador, Builder, Asistente
    
    Cada grupo tiene un nombre elegante único según su dominio:
    - CODEX (SWE)
    - VITALIS (Salud)
    - ATHLON (Deportes)
    - VERITAS (Noticias)
    - ALCHEMY (Química)
    - GENESIS (Biología)
    - HELIX (Biotecnología)
    - DIPLOMAT (Geopolítica)
    - APEX (Finanzas)
    - JUSTITIA (Legal)
    - MENTOR (Educación)
    - PIONEER (Investigación)
    - PRISMA (Marketing)
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    elegant_name: str = ""  # Nombre elegante del dominio
    domain: IOVBADomain = "swe"
    description: str = ""
    status: AgentStatus = AgentStatus.ACTIVE
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    # Los 5 agentes del stack IOVBA
    investigador: Optional[AgentProfile] = None
    observador: Optional[AgentProfile] = None
    validador: Optional[AgentProfile] = None
    builder: Optional[AgentProfile] = None
    asistente: Optional[AgentProfile] = None
    
    # Capital compartido del grupo
    shared_capital: Optional[CognitiveCapital] = None
    
    # Métricas del grupo
    total_tasks: int = 0
    success_rate: float = 0.0
    avg_completion_time: float = 0.0
    domain_expertise: float = 0.0
    
    # Sincronización
    sync_mode: CapitalSyncMode = CapitalSyncMode.HYBRID
    centralized_capital: Optional[CognitiveCapital] = None
    
    def __post_init__(self):
        if self.shared_capital is None:
            self.shared_capital = CognitiveCapital(agent_id=self.id)
        if self.centralized_capital is None:
            self.centralized_capital = CognitiveCapital(agent_id=f"{self.id}_central")
        
        # Set elegant name from domain branding
        if not self.elegant_name and self.domain in DOMAIN_BRANDING:
            self.elegant_name = DOMAIN_BRANDING[self.domain].elegant_name
        
        # Crear agentes si no existen
        if not self.investigador:
            self.investigador = self._create_role_agent("investigador")
        if not self.observador:
            self.observador = self._create_role_agent("observador")
        if not self.validador:
            self.validador = self._create_role_agent("validador")
        if not self.builder:
            self.builder = self._create_role_agent("builder")
        if not self.asistente:
            self.asistente = self._create_role_agent("asistente")
    
    def _create_role_agent(self, role: IOVBARole) -> AgentProfile:
        """Crea un agente para un rol específico"""
        domain_brand = DOMAIN_BRANDING.get(self.domain, DOMAIN_BRANDING["custom"])
        role_brand = ROLE_BRANDING.get(role, ROLE_BRANDING["asistente"])
        
        role_configs = {
            "investigador": {
                "skills": ["research", "data-analysis", "web-search", "document-analysis", "deep-investigation"],
                "tools": ["search", "scraper", "pdf-reader", "database-query"],
            },
            "observador": {
                "skills": ["monitoring", "pattern-recognition", "anomaly-detection", "reporting", "metrics-analysis"],
                "tools": ["logger", "metrics", "alerts", "dashboard"],
            },
            "validador": {
                "skills": ["quality-assurance", "testing", "review", "verification", "compliance-check"],
                "tools": ["validator", "tester", "checker", "linter"],
            },
            "builder": {
                "skills": ["implementation", "development", "optimization", "refactoring", "architecture"],
                "tools": ["code-executor", "builder", "deployer", "compiler"],
            },
            "asistente": {
                "skills": ["coordination", "communication", "documentation", "scheduling", "orchestration"],
                "tools": ["scheduler", "notifier", "documenter", "workflow-manager"],
            }
        }
        
        config = role_configs.get(role, {})
        return AgentProfile(
            name=f"{role_brand.elegant_name} {domain_brand.elegant_name}",
            description=f"{role_brand.description} en {domain_brand.name}",
            domain=self.domain,
            iovba_role=role,
            skills=config.get("skills", []),
            tools=config.get("tools", []),
        )
    
    def get_all_agents(self) -> Dict[IOVBARole, AgentProfile]:
        """Retorna todos los agentes del grupo"""
        return {
            "investigador": self.investigador,
            "observador": self.observador,
            "validador": self.validador,
            "builder": self.builder,
            "asistente": self.asistente,
        }
    
    async def sync_capital(self, mode: Optional[CapitalSyncMode] = None) -> Dict[str, Any]:
        """
        Sincroniza el capital cognitivo entre agentes
        Modo centralizado: todos sincronizan con capital central
        Modo descentralizado: P2P entre agentes
        Modo híbrido: combinación de ambos
        """
        sync_mode = mode or self.sync_mode
        sync_result = {
            "mode": sync_mode.value,
            "timestamp": datetime.utcnow().isoformat(),
            "synced_agents": [],
            "total_engrams_synced": 0,
        }
        
        agents = self.get_all_agents()
        
        if sync_mode == CapitalSyncMode.CENTRALIZED:
            # Sincronizar todos al capital centralizado
            for role, agent in agents.items():
                if agent and agent.cognitive_capital:
                    # Merge engrams to central
                    self.centralized_capital.engrams.extend(agent.cognitive_capital.engrams)
                    sync_result["synced_agents"].append(role)
                    sync_result["total_engrams_synced"] += len(agent.cognitive_capital.engrams)
            
            # Distribuir capital mejorado de vuelta
            for role, agent in agents.items():
                if agent and agent.cognitive_capital:
                    agent.cognitive_capital.learning_score = self.centralized_capital.learning_score
                    agent.cognitive_capital.last_sync = datetime.utcnow().isoformat()
        
        elif sync_mode == CapitalSyncMode.DECENTRALIZED:
            # P2P sync entre agentes
            agent_list = [a for a in agents.values() if a and a.cognitive_capital]
            for i, agent1 in enumerate(agent_list):
                for agent2 in agent_list[i+1:]:
                    # Share top engrams
                    top_engrams_1 = agent1.cognitive_capital.get_top_engrams(5)
                    top_engrams_2 = agent2.cognitive_capital.get_top_engrams(5)
                    
                    for e in top_engrams_1:
                        if e not in agent2.cognitive_capital.engrams:
                            agent2.cognitive_capital.add_engram(e)
                            sync_result["total_engrams_synced"] += 1
                    
                    for e in top_engrams_2:
                        if e not in agent1.cognitive_capital.engrams:
                            agent1.cognitive_capital.add_engram(e)
                            sync_result["total_engrams_synced"] += 1
        
        elif sync_mode == CapitalSyncMode.HYBRID:
            # Primero P2P, luego centralizado
            await self.sync_capital(CapitalSyncMode.DECENTRALIZED)
            await self.sync_capital(CapitalSyncMode.CENTRALIZED)
        
        # Update shared capital
        self.shared_capital.last_sync = datetime.utcnow().isoformat()
        
        return sync_result
    
    async def auto_improve(self) -> Dict[str, Any]:
        """
        Auto-mejora del grupo
        Analiza performance y mejora el capital cognitivo
        """
        improvement_result = {
            "timestamp": datetime.utcnow().isoformat(),
            "improvements": [],
            "new_engrams": 0,
            "capital_delta": 0,
        }
        
        # Analizar agentes y generar mejoras
        for role, agent in self.get_all_agents().items():
            if agent and agent.cognitive_capital:
                # Calcular mejora basada en métricas
                improvement_delta = agent.success_rate * 0.1
                agent.cognitive_capital.improve(improvement_delta)
                
                improvement_result["improvements"].append({
                    "agent": role,
                    "delta": improvement_delta,
                    "new_score": agent.cognitive_capital.learning_score,
                })
        
        # Sincronizar después de mejorar
        await self.sync_capital()
        
        return improvement_result


class IOVBAGroupManager:
    """
    Gestor de grupos IOVBA
    Crea, gestiona y coordina grupos de agentes
    """
    
    def __init__(self):
        self.groups: Dict[str, IOVBAGroup] = {}
        self.domain_templates: Dict[IOVBADomain, Dict[str, Any]] = self._init_templates()
    
    def _init_templates(self) -> Dict[IOVBADomain, Dict[str, Any]]:
        """Inicializa templates por dominio"""
        templates = {}
        for domain, brand in DOMAIN_BRANDING.items():
            templates[domain] = {
                "name": brand.name,
                "elegant_name": brand.elegant_name,
                "tagline": brand.tagline,
                "description": brand.description,
                "mcp_servers": self._get_mcp_servers_for_domain(domain)
            }
        return templates
    
    def _get_mcp_servers_for_domain(self, domain: IOVBADomain) -> List[str]:
        """Retorna MCP servers recomendados para cada dominio"""
        mcp_map = {
            "swe": ["github", "docker", "filesystem", "git"],
            "salud": ["medical-db", "hl7-fhir", "pubmed"],
            "deportes": ["stats-api", "video-processing", "data-analytics"],
            "noticias": ["brave-search", "news-api", "fact-checker"],
            "quimica": ["pubchem", "chemspider", "rdkit"],
            "biologia": ["ncbi", "ensembl", "uniprot"],
            "biotecnologia": ["ncbi", "uniprot", "pubmed", "alphafold"],
            "geopolitica": ["brave-search", "maps-api", "news-api"],
            "finanzas": ["alpha-vantage", "coingecko", "yahoo-finance"],
            "legal": ["court-api", "statute-db", "legal-search"],
            "educacion": ["lms-integration", "content-db", "video-platform"],
            "investigacion": ["arxiv", "pubmed", "semantic-scholar", "google-scholar"],
            "marketing": ["google-analytics", "social-apis", "seo-tools"],
            "custom": [],
        }
        return mcp_map.get(domain, [])
    
    def create_group(
        self,
        name: str,
        domain: IOVBADomain,
        description: str = "",
        sync_mode: CapitalSyncMode = CapitalSyncMode.HYBRID,
    ) -> IOVBAGroup:
        """Crea un nuevo grupo IOVBA con nombre elegante"""
        template = self.domain_templates.get(domain, {})
        brand = DOMAIN_BRANDING.get(domain, DOMAIN_BRANDING["custom"])
        
        group = IOVBAGroup(
            name=name or f"{brand.elegant_name} Unit",
            elegant_name=brand.elegant_name,
            domain=domain,
            description=description or brand.description,
            sync_mode=sync_mode,
        )
        
        # Configurar MCP servers del template
        mcp_servers = template.get("mcp_servers", [])
        for role, agent in group.get_all_agents().items():
            if agent:
                agent.mcp_servers = mcp_servers
        
        self.groups[group.id] = group
        return group
    
    def get_group(self, group_id: str) -> Optional[IOVBAGroup]:
        """Obtiene un grupo por ID"""
        return self.groups.get(group_id)
    
    def list_groups(self) -> List[IOVBAGroup]:
        """Lista todos los grupos"""
        return list(self.groups.values())
    
    async def sync_all_groups(self) -> Dict[str, Any]:
        """Sincroniza todos los grupos"""
        results = {}
        for group_id, group in self.groups.items():
            results[group_id] = await group.sync_capital()
        return results
    
    async def auto_improve_all(self) -> Dict[str, Any]:
        """Auto-mejora todos los grupos"""
        results = {}
        for group_id, group in self.groups.items():
            results[group_id] = await group.auto_improve()
        return results
    
    def get_domain_branding(self, domain: IOVBADomain) -> IOVBADomainBrand:
        """Retorna el branding de un dominio"""
        return DOMAIN_BRANDING.get(domain, DOMAIN_BRANDING["custom"])
    
    def get_all_domain_brands(self) -> Dict[IOVBADomain, IOVBADomainBrand]:
        """Retorna todos los brandings de dominio"""
        return DOMAIN_BRANDING
