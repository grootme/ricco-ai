"""
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

# IOVBA Role Types
IOVBARole = Literal["investigador", "observador", "validador", "builder", "asistente"]

# Domain Types
IOVBADomain = Literal[
    "swe", "salud", "deportes", "noticias", "quimica",
    "biologia", "biotecnologia", "geopolitica", "finanzas",
    "legal", "educacion", "investigacion", "marketing", "custom"
]


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
    Investidador, Observador, Validador, Builder, Asistente
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
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
        role_configs = {
            "investigador": {
                "skills": ["research", "data-analysis", "web-search", "document-analysis"],
                "tools": ["search", "scraper", "pdf-reader"],
                "description": f"Investigador especializado en {self.domain}"
            },
            "observador": {
                "skills": ["monitoring", "pattern-recognition", "anomaly-detection", "reporting"],
                "tools": ["logger", "metrics", "alerts"],
                "description": f"Observador de patrones y anomalías en {self.domain}"
            },
            "validador": {
                "skills": ["quality-assurance", "testing", "review", "verification"],
                "tools": ["validator", "tester", "checker"],
                "description": f"Validador de calidad y verificación en {self.domain}"
            },
            "builder": {
                "skills": ["implementation", "development", "optimization", "refactoring"],
                "tools": ["code-executor", "builder", "deployer"],
                "description": f"Builder e implementador en {self.domain}"
            },
            "asistente": {
                "skills": ["coordination", "communication", "documentation", "scheduling"],
                "tools": ["scheduler", "notifier", "documenter"],
                "description": f"Asistente coordinador en {self.domain}"
            }
        }
        
        config = role_configs.get(role, {})
        return AgentProfile(
            name=f"{role.capitalize()} {self.domain.upper()}",
            description=config.get("description", ""),
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
        return {
            "swe": {"name": "Software Engineering", "mcp_servers": ["github", "docker", "filesystem"]},
            "salud": {"name": "Salud y Medicina", "mcp_servers": ["medical-db", "hl7-fhir"]},
            "deportes": {"name": "Deportes", "mcp_servers": ["stats-api", "video-processing"]},
            "noticias": {"name": "Noticias y Periodismo", "mcp_servers": ["brave-search", "news-api"]},
            "quimica": {"name": "Química", "mcp_servers": ["pubchem", "chemspider"]},
            "biologia": {"name": "Biología", "mcp_servers": ["ncbi", "ensembl"]},
            "biotecnologia": {"name": "Biotecnología", "mcp_servers": ["ncbi", "uniprot", "pubmed"]},
            "geopolitica": {"name": "Geopolítica", "mcp_servers": ["brave-search", "maps-api"]},
            "finanzas": {"name": "Finanzas", "mcp_servers": ["alpha-vantage", "coingecko"]},
            "legal": {"name": "Legal", "mcp_servers": ["court-api", "statute-db"]},
            "educacion": {"name": "Educación", "mcp_servers": ["lms-integration", "content-db"]},
            "investigacion": {"name": "Investigación", "mcp_servers": ["arxiv", "pubmed", "semantic-scholar"]},
            "marketing": {"name": "Marketing", "mcp_servers": ["google-analytics", "social-apis"]},
            "custom": {"name": "Personalizado", "mcp_servers": []},
        }
    
    def create_group(
        self,
        name: str,
        domain: IOVBADomain,
        description: str = "",
        sync_mode: CapitalSyncMode = CapitalSyncMode.HYBRID,
    ) -> IOVBAGroup:
        """Crea un nuevo grupo IOVBA"""
        template = self.domain_templates.get(domain, {})
        
        group = IOVBAGroup(
            name=name,
            domain=domain,
            description=description or template.get("name", ""),
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
