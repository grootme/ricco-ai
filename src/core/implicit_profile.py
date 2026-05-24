"""
Agent Profile Implícito - El perfil se DETERMINA de la configuración.

FILOSOFÍA: El perfil NO es una clase hardcodeada. Se INFIERE de los componentes
que el agente tiene asignados. El agente "es" lo que TIENE y HACE.

Agent Profile = {
    SKILLS: Qué sabe hacer (inferido de skills_registry)
    TOOLS: Qué tiene disponible (inferido de tools_config)
    MCP: De dónde vienen (inferido de mcp_servers)
    MEMORY: Capital Cognitivo (inferido de memory_config)
    PROMPT: Cómo actúa (inferido de prompt_config)
    DOMAIN: Etiqueta descriptiva (inferido de domain_config)
    EXECUTION: Patrón de ejecución (inferido de execution_config)
    ORCHESTRATION: Rol en orquestación (inferido de orchestration_config)
}

Patrones GOF Aplicados:
- Strategy: Diferentes estrategias de inferencia
- Factory: Creación de configuraciones
- Interpreter: Interpretación de configuración → perfil
- Chain of Responsibility: Pipeline de inferencia

@author: NEXUS - Neural Execution Unified System
"""

from typing import (
    Dict, List, Optional, Any, Callable, Set, Type, 
    Union, Protocol, runtime_checkable
)
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from uuid import UUID, uuid4
import asyncio
import json
import logging
from abc import ABC, abstractmethod
from functools import cached_property
from collections import defaultdict

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURACIÓN SIMPLE - NO ES UN PERFIL, ES CONFIG
# ============================================================================

@dataclass
class AgentConfig:
    """
    Configuración del Agente - Datos puros, sin comportamiento.
    
    Esta es la ÚNICA estructura que se instancia explícitamente.
    El perfil se INFIERE de esta configuración.
    """
    # Identidad
    agent_id: str = field(default_factory=lambda: str(uuid4())[:8])
    name: str = "Agent"
    
    # Componentes (el perfil se infiere de estos)
    skills: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    tools: List[str] = field(default_factory=list)
    mcp_servers: List[str] = field(default_factory=list)
    memory_config: Dict[str, Any] = field(default_factory=dict)
    prompt_template: str = ""
    domain: str = "general"
    execution_pattern: str = "adaptive"  # sequential, parallel, hierarchical, adaptive
    orchestration_role: str = "worker"    # lead, worker, specialist, validator
    
    # Relaciones
    parent_id: Optional[str] = None
    child_ids: List[str] = field(default_factory=list)
    
    # Metadatos
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa la configuración"""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "skills": self.skills,
            "tools": self.tools,
            "mcp_servers": self.mcp_servers,
            "memory_config": self.memory_config,
            "prompt_template": self.prompt_template,
            "domain": self.domain,
            "execution_pattern": self.execution_pattern,
            "orchestration_role": self.orchestration_role,
            "parent_id": self.parent_id,
            "child_ids": self.child_ids,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentConfig":
        """Deserializa desde diccionario"""
        return cls(
            agent_id=data.get("agent_id", str(uuid4())[:8]),
            name=data.get("name", "Agent"),
            skills=data.get("skills", {}),
            tools=data.get("tools", []),
            mcp_servers=data.get("mcp_servers", []),
            memory_config=data.get("memory_config", {}),
            prompt_template=data.get("prompt_template", ""),
            domain=data.get("domain", "general"),
            execution_pattern=data.get("execution_pattern", "adaptive"),
            orchestration_role=data.get("orchestration_role", "worker"),
            parent_id=data.get("parent_id"),
            child_ids=data.get("child_ids", []),
            metadata=data.get("metadata", {}),
        )


# ============================================================================
# PATRÓN INTERPRETER - Infiere el perfil de la configuración
# ============================================================================

class ProfileAspect(str, Enum):
    """Aspectos que componen el perfil implícito"""
    CAPABILITY_LEVEL = "capability_level"      # Qué tan capaz es
    SPECIALIZATION = "specialization"           # Qué tan especializado
    AUTONOMY = "autonomy"                       # Qué tan autónomo
    COORDINATION_ROLE = "coordination_role"     # Rol en coordinación
    KNOWLEDGE_RICHNESS = "knowledge_richness"   # Riqueza de conocimiento
    TOOL_POWER = "tool_power"                   # Poder de herramientas


@dataclass
class InferredProfile:
    """
    Perfil Inferido - Resultado de interpretar la configuración.
    
    NO se instancia directamente, se CALCULA.
    """
    # Identidad inferida
    agent_id: str
    profile_hash: str  # Hash único basado en componentes
    
    # 8 Componentes Inferidos
    skills_summary: Dict[str, Any]      # SKILLS: Qué sabe hacer
    tools_summary: Dict[str, Any]       # TOOLS: Qué tiene disponible
    mcp_summary: Dict[str, Any]         # MCP: De dónde vienen
    memory_summary: Dict[str, Any]      # MEMORY: Capital Cognitivo
    prompt_summary: Dict[str, Any]      # PROMPT: Cómo actúa
    domain_summary: Dict[str, Any]      # DOMAIN: Etiqueta descriptiva
    execution_summary: Dict[str, Any]   # EXECUTION: Patrón
    orchestration_summary: Dict[str, Any]  # ORCHESTRATION: Rol
    
    # Métricas inferidas
    capability_score: float = 0.0
    specialization_score: float = 0.0
    autonomy_score: float = 0.0
    coordination_weight: float = 0.0
    
    # Timestamps
    inferred_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "profile_hash": self.profile_hash,
            "skills_summary": self.skills_summary,
            "tools_summary": self.tools_summary,
            "mcp_summary": self.mcp_summary,
            "memory_summary": self.memory_summary,
            "prompt_summary": self.prompt_summary,
            "domain_summary": self.domain_summary,
            "execution_summary": self.execution_summary,
            "orchestration_summary": self.orchestration_summary,
            "capability_score": self.capability_score,
            "specialization_score": self.specialization_score,
            "autonomy_score": self.autonomy_score,
            "coordination_weight": self.coordination_weight,
            "inferred_at": self.inferred_at.isoformat(),
        }


class ProfileInterpreter:
    """
    Patrón Interpreter - Interpreta la configuración y genera el perfil.
    
    El perfil NO existe como objeto independiente, se CALCULA
    cada vez que se necesita a partir de la configuración.
    """
    
    def __init__(self):
        self._cache: Dict[str, InferredProfile] = {}
        self._cache_ttl_seconds = 300  # 5 minutos
    
    def interpret(self, config: AgentConfig) -> InferredProfile:
        """
        Interpreta la configuración y retorna el perfil inferido.
        
        Este es el método principal que DETERMINA el perfil del agente
        a partir de su configuración.
        """
        # Verificar cache
        cache_key = self._make_cache_key(config)
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if self._is_cache_valid(cached):
                return cached
        
        # Inferir cada componente
        skills_summary = self._infer_skills(config)
        tools_summary = self._infer_tools(config)
        mcp_summary = self._infer_mcp(config)
        memory_summary = self._infer_memory(config)
        prompt_summary = self._infer_prompt(config)
        domain_summary = self._infer_domain(config)
        execution_summary = self._infer_execution(config)
        orchestration_summary = self._infer_orchestration(config)
        
        # Calcular métricas
        capability_score = self._calculate_capability(config)
        specialization_score = self._calculate_specialization(config)
        autonomy_score = self._calculate_autonomy(config)
        coordination_weight = self._calculate_coordination_weight(config)
        
        # Crear perfil inferido
        profile = InferredProfile(
            agent_id=config.agent_id,
            profile_hash=cache_key,
            skills_summary=skills_summary,
            tools_summary=tools_summary,
            mcp_summary=mcp_summary,
            memory_summary=memory_summary,
            prompt_summary=prompt_summary,
            domain_summary=domain_summary,
            execution_summary=execution_summary,
            orchestration_summary=orchestration_summary,
            capability_score=capability_score,
            specialization_score=specialization_score,
            autonomy_score=autonomy_score,
            coordination_weight=coordination_weight,
        )
        
        # Cachear
        self._cache[cache_key] = profile
        
        return profile
    
    def _make_cache_key(self, config: AgentConfig) -> str:
        """Genera hash único para la configuración"""
        import hashlib
        content = json.dumps(config.to_dict(), sort_keys=True, default=str)
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _is_cache_valid(self, profile: InferredProfile) -> bool:
        """Verifica si el cache sigue válido"""
        age = (datetime.utcnow() - profile.inferred_at).total_seconds()
        return age < self._cache_ttl_seconds
    
    def _infer_skills(self, config: AgentConfig) -> Dict[str, Any]:
        """INFERENCIA: SKILLS - Qué sabe hacer"""
        skills = config.skills
        
        if not skills:
            return {"count": 0, "level": "undefined", "areas": []}
        
        # Inferir nivel de skill promedio
        levels = {"novice": 1, "beginner": 2, "intermediate": 3, "advanced": 4, "expert": 5, "master": 6}
        total_level = sum(
            levels.get(s.get("level", "beginner"), 2)
            for s in skills.values()
        )
        avg_level = total_level / len(skills) if skills else 0
        
        # Inferir áreas de expertise
        areas = list(skills.keys())
        
        return {
            "count": len(skills),
            "level": self._level_to_name(avg_level),
            "areas": areas[:10],
            "diversity": len(set(areas)),
        }
    
    def _infer_tools(self, config: AgentConfig) -> Dict[str, Any]:
        """INFERENCIA: TOOLS - Qué tiene disponible"""
        tools = config.tools
        
        return {
            "count": len(tools),
            "categories": self._categorize_tools(tools),
            "access_level": "full" if len(tools) > 10 else "limited" if len(tools) > 3 else "basic",
        }
    
    def _infer_mcp(self, config: AgentConfig) -> Dict[str, Any]:
        """INFERENCIA: MCP - De dónde vienen los recursos"""
        servers = config.mcp_servers
        
        return {
            "servers_count": len(servers),
            "servers": servers,
            "external_access": len(servers) > 0,
        }
    
    def _infer_memory(self, config: AgentConfig) -> Dict[str, Any]:
        """INFERENCIA: MEMORY - Capital Cognitivo"""
        mem_config = config.memory_config
        
        return {
            "enabled": bool(mem_config),
            "type": mem_config.get("type", "none"),
            "capacity": mem_config.get("capacity", 0),
            "persistence": mem_config.get("persistence", False),
        }
    
    def _infer_prompt(self, config: AgentConfig) -> Dict[str, Any]:
        """INFERENCIA: PROMPT - Cómo actúa"""
        prompt = config.prompt_template
        
        return {
            "has_custom_prompt": bool(prompt),
            "prompt_length": len(prompt),
            "complexity": "high" if len(prompt) > 500 else "medium" if len(prompt) > 100 else "low",
        }
    
    def _infer_domain(self, config: AgentConfig) -> Dict[str, Any]:
        """INFERENCIA: DOMAIN - Etiqueta descriptiva"""
        domain = config.domain
        
        return {
            "primary": domain,
            "label": self._get_domain_label(domain),
            "is_specialized": domain != "general",
        }
    
    def _infer_execution(self, config: AgentConfig) -> Dict[str, Any]:
        """INFERENCIA: EXECUTION - Patrón de ejecución"""
        pattern = config.execution_pattern
        
        return {
            "pattern": pattern,
            "description": self._get_pattern_description(pattern),
            "supports_parallel": pattern in ["parallel", "adaptive"],
        }
    
    def _infer_orchestration(self, config: AgentConfig) -> Dict[str, Any]:
        """INFERENCIA: ORCHESTRATION - Rol en orquestación"""
        role = config.orchestration_role
        
        has_children = len(config.child_ids) > 0
        has_parent = config.parent_id is not None
        
        return {
            "role": role,
            "is_leader": role == "lead",
            "has_subordinates": has_children,
            "reports_to": has_parent,
        }
    
    def _calculate_capability(self, config: AgentConfig) -> float:
        """Calcula score de capacidad (0-1)"""
        score = 0.0
        
        # Skills contribuyen 40%
        if config.skills:
            skill_score = min(len(config.skills) / 10, 1.0) * 0.4
            score += skill_score
        
        # Tools contribuyen 30%
        if config.tools:
            tool_score = min(len(config.tools) / 15, 1.0) * 0.3
            score += tool_score
        
        # Memory contribuye 20%
        if config.memory_config:
            score += 0.2
        
        # MCP contribuye 10%
        if config.mcp_servers:
            score += min(len(config.mcp_servers) / 5, 1.0) * 0.1
        
        return round(score, 3)
    
    def _calculate_specialization(self, config: AgentConfig) -> float:
        """Calcula score de especialización (0-1)"""
        if config.domain == "general":
            return 0.0
        
        # Más skills en un solo dominio = más especialización
        if config.skills:
            areas = list(config.skills.keys())
            if len(areas) <= 3:
                return 0.8
            elif len(areas) <= 5:
                return 0.5
        
        return 0.3
    
    def _calculate_autonomy(self, config: AgentConfig) -> float:
        """Calcula score de autonomía (0-1)"""
        score = 0.5  # Base
        
        # Prompt complejo sugiere más autonomía
        if len(config.prompt_template) > 500:
            score += 0.2
        
        # Memory propia sugiere más autonomía
        if config.memory_config.get("persistence"):
            score += 0.2
        
        # Rol de liderazgo sugiere más autonomía
        if config.orchestration_role == "lead":
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_coordination_weight(self, config: AgentConfig) -> float:
        """Calcula peso en coordinación (0-1)"""
        if config.orchestration_role == "lead":
            return 1.0
        elif config.orchestration_role == "specialist":
            return 0.7
        elif config.orchestration_role == "validator":
            return 0.5
        return 0.3
    
    def _level_to_name(self, level: float) -> str:
        """Convierte nivel numérico a nombre"""
        if level >= 5.5:
            return "master"
        elif level >= 4.5:
            return "expert"
        elif level >= 3.5:
            return "advanced"
        elif level >= 2.5:
            return "intermediate"
        elif level >= 1.5:
            return "beginner"
        return "novice"
    
    def _categorize_tools(self, tools: List[str]) -> Dict[str, List[str]]:
        """Categoriza herramientas"""
        categories = defaultdict(list)
        for tool in tools:
            # Simple categorización por prefijo
            category = tool.split("_")[0] if "_" in tool else "general"
            categories[category].append(tool)
        return dict(categories)
    
    def _get_domain_label(self, domain: str) -> str:
        """Obtiene etiqueta descriptiva del dominio"""
        labels = {
            "codex": "Software Engineering",
            "vitalis": "Healthcare",
            "athlon": "Sports",
            "veritas": "News & Media",
            "alchemy": "Chemistry",
            "genesis": "Biology",
            "helix": "Biotechnology",
            "diplomat": "Geopolitics",
            "apex": "Finance",
            "justitia": "Legal",
            "mentor": "Education",
            "pioneer": "Research",
            "prisma": "Marketing",
            "orchestration": "Coordination",
            "general": "General Purpose",
        }
        return labels.get(domain, domain.title())
    
    def _get_pattern_description(self, pattern: str) -> str:
        """Obtiene descripción del patrón de ejecución"""
        descriptions = {
            "sequential": "Ejecución paso a paso, un elemento a la vez",
            "parallel": "Ejecución simultánea de tareas independientes",
            "hierarchical": "Delegación a sub-agentes en estructura de árbol",
            "adaptive": "Selección dinámica basada en características de la tarea",
        }
        return descriptions.get(pattern, "Patrón no reconocido")
    
    def clear_cache(self) -> None:
        """Limpia el cache de perfiles"""
        self._cache.clear()


# ============================================================================
# PATRÓN CHAIN OF RESPONSIBILITY - Pipeline de Inferencia
# ============================================================================

class InferenceHandler(ABC):
    """Handler abstracto para el pipeline de inferencia"""
    
    def __init__(self):
        self._next_handler: Optional["InferenceHandler"] = None
    
    def set_next(self, handler: "InferenceHandler") -> "InferenceHandler":
        self._next_handler = handler
        return handler
    
    @abstractmethod
    async def handle(self, config: AgentConfig, context: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    async def pass_to_next(self, config: AgentConfig, context: Dict[str, Any]) -> Dict[str, Any]:
        if self._next_handler:
            return await self._next_handler.handle(config, context)
        return context


class SkillsInferenceHandler(InferenceHandler):
    """Handler: Inferencia de Skills"""
    
    async def handle(self, config: AgentConfig, context: Dict[str, Any]) -> Dict[str, Any]:
        interpreter = ProfileInterpreter()
        context["skills_inferred"] = interpreter._infer_skills(config)
        return await self.pass_to_next(config, context)


class ToolsInferenceHandler(InferenceHandler):
    """Handler: Inferencia de Tools"""
    
    async def handle(self, config: AgentConfig, context: Dict[str, Any]) -> Dict[str, Any]:
        interpreter = ProfileInterpreter()
        context["tools_inferred"] = interpreter._infer_tools(config)
        return await self.pass_to_next(config, context)


class MemoryInferenceHandler(InferenceHandler):
    """Handler: Inferencia de Memory"""
    
    async def handle(self, config: AgentConfig, context: Dict[str, Any]) -> Dict[str, Any]:
        interpreter = ProfileInterpreter()
        context["memory_inferred"] = interpreter._infer_memory(config)
        return await self.pass_to_next(config, context)


class ExecutionInferenceHandler(InferenceHandler):
    """Handler: Inferencia de Execution Pattern"""
    
    async def handle(self, config: AgentConfig, context: Dict[str, Any]) -> Dict[str, Any]:
        interpreter = ProfileInterpreter()
        context["execution_inferred"] = interpreter._infer_execution(config)
        return await self.pass_to_next(config, context)


class ProfileInferencePipeline:
    """
    Pipeline de inferencia usando Chain of Responsibility.
    
    Permite extender el proceso de inferencia añadiendo handlers.
    """
    
    def __init__(self):
        # Configurar cadena de handlers
        self._skills_handler = SkillsInferenceHandler()
        self._tools_handler = ToolsInferenceHandler()
        self._memory_handler = MemoryInferenceHandler()
        self._execution_handler = ExecutionInferenceHandler()
        
        # Enlazar handlers
        self._skills_handler.set_next(self._tools_handler) \
                            .set_next(self._memory_handler) \
                            .set_next(self._execution_handler)
    
    async def run(self, config: AgentConfig) -> Dict[str, Any]:
        """Ejecuta el pipeline de inferencia"""
        context: Dict[str, Any] = {"config": config.to_dict()}
        return await self._skills_handler.handle(config, context)


# ============================================================================
# PATRÓN STRATEGY - Estrategias de Perfil
# ============================================================================

class ProfilingStrategy(ABC):
    """Estrategia abstracta para determinar cómo perfilar un agente"""
    
    @abstractmethod
    def profile(self, config: AgentConfig) -> Dict[str, Any]:
        pass


class MinimalProfilingStrategy(ProfilingStrategy):
    """Estrategia: Perfilado mínimo (solo lo esencial)"""
    
    def profile(self, config: AgentConfig) -> Dict[str, Any]:
        interpreter = ProfileInterpreter()
        return {
            "agent_id": config.agent_id,
            "domain": config.domain,
            "role": config.orchestration_role,
            "capability_score": interpreter._calculate_capability(config),
        }


class FullProfilingStrategy(ProfilingStrategy):
    """Estrategia: Perfilado completo (todos los componentes)"""
    
    def profile(self, config: AgentConfig) -> Dict[str, Any]:
        interpreter = ProfileInterpreter()
        profile = interpreter.interpret(config)
        return profile.to_dict()


class CachedProfilingStrategy(ProfilingStrategy):
    """Estrategia: Perfilado con caché"""
    
    def __init__(self, delegate: ProfilingStrategy, ttl_seconds: int = 300):
        self._delegate = delegate
        self._cache: Dict[str, tuple] = {}
        self._ttl = ttl_seconds
    
    def profile(self, config: AgentConfig) -> Dict[str, Any]:
        # Generar clave de caché usando JSON serializado
        import hashlib
        content = json.dumps(config.to_dict(), sort_keys=True, default=str)
        cache_key = f"{config.agent_id}:{hashlib.md5(content.encode()).hexdigest()[:8]}"
        
        if cache_key in self._cache:
            profile, timestamp = self._cache[cache_key]
            if (datetime.utcnow() - timestamp).total_seconds() < self._ttl:
                return profile
        
        profile = self._delegate.profile(config)
        self._cache[cache_key] = (profile, datetime.utcnow())
        return profile


# ============================================================================
# PATRÓN FACTORY - Creación de Configuraciones
# ============================================================================

class AgentConfigFactory:
    """
    Factory para crear configuraciones de agentes.
    
    NOTA: Crea CONFIG, no perfiles. Los perfiles se infieren después.
    """
    
    @staticmethod
    def create_minimal(agent_id: str, domain: str = "general") -> AgentConfig:
        """Crea configuración mínima"""
        return AgentConfig(
            agent_id=agent_id,
            domain=domain,
        )
    
    @staticmethod
    def create_with_skills(
        agent_id: str,
        skills: Dict[str, str],  # {skill_name: level}
        domain: str = "general"
    ) -> AgentConfig:
        """Crea configuración con skills"""
        skills_dict = {
            name: {"level": level, "acquired_at": datetime.utcnow().isoformat()}
            for name, level in skills.items()
        }
        return AgentConfig(
            agent_id=agent_id,
            domain=domain,
            skills=skills_dict,
        )
    
    @staticmethod
    def create_specialist(
        agent_id: str,
        domain: str,
        skills: List[str],
        tools: List[str],
    ) -> AgentConfig:
        """Crea configuración de especialista"""
        skills_dict = {
            skill: {"level": "advanced", "acquired_at": datetime.utcnow().isoformat()}
            for skill in skills
        }
        return AgentConfig(
            agent_id=agent_id,
            domain=domain,
            skills=skills_dict,
            tools=tools,
            orchestration_role="specialist",
        )
    
    @staticmethod
    def create_orchestrator(
        agent_id: str,
        child_ids: List[str],
    ) -> AgentConfig:
        """Crea configuración de orquestador"""
        return AgentConfig(
            agent_id=agent_id,
            domain="orchestration",
            orchestration_role="lead",
            child_ids=child_ids,
            execution_pattern="hierarchical",
        )
    
    @staticmethod
    def from_seed(seed: Dict[str, Any]) -> AgentConfig:
        """Crea configuración desde seed de base de datos"""
        return AgentConfig(
            agent_id=seed.get("agent_id", str(uuid4())[:8]),
            name=seed.get("name", "Agent"),
            domain=seed.get("metadata", {}).get("domain", "general"),
            skills={
                cap: {"level": "intermediate"}
                for cap in seed.get("capabilities", [])
            },
            tools=seed.get("mcp_servers", []),
            mcp_servers=seed.get("mcp_servers", []),
            prompt_template=seed.get("system_prompt", ""),
            metadata=seed.get("metadata", {}),
        )


# ============================================================================
# AGENTE DINÁMICO - NO TIENE TIPO, TIENE CONFIGURACIÓN
# ============================================================================

class DynamicAgent:
    """
    Agente Dinámico - Su comportamiento está determinado por su configuración.
    
    NO tiene un "tipo" hardcodeado. Su perfil se INFIERE de su configuración.
    """
    
    def __init__(self, config: AgentConfig):
        self._config = config
        self._interpreter = ProfileInterpreter()
        
        # Estado interno
        self._state = "idle"
        self._execution_history: List[Dict[str, Any]] = []
        self._cognitive_capital: List[Dict[str, Any]] = []
    
    @property
    def config(self) -> AgentConfig:
        """Retorna la configuración del agente"""
        return self._config
    
    @cached_property
    def profile(self) -> InferredProfile:
        """
        Retorna el perfil INFERIDO de la configuración.
        
        NOTA: El perfil no se almacena, se CALCULA.
        """
        return self._interpreter.interpret(self._config)
    
    @property
    def agent_id(self) -> str:
        return self._config.agent_id
    
    @property
    def name(self) -> str:
        return self._config.name
    
    @property
    def domain(self) -> str:
        return self._config.domain
    
    @property
    def state(self) -> str:
        return self._state
    
    def get_capability_score(self) -> float:
        """Retorna el score de capacidad inferido"""
        return self.profile.capability_score
    
    def get_specialization_score(self) -> float:
        """Retorna el score de especialización inferido"""
        return self.profile.specialization_score
    
    def has_skill(self, skill_name: str) -> bool:
        """Verifica si tiene una skill (de la configuración)"""
        return skill_name in self._config.skills
    
    def has_tool(self, tool_name: str) -> bool:
        """Verifica si tiene acceso a una herramienta (de la configuración)"""
        return tool_name in self._config.tools
    
    def can_coordinate(self) -> bool:
        """Verifica si puede coordinar otros agentes (inferido)"""
        return self.profile.orchestration_summary.get("is_leader", False)
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta una tarea según su patrón de ejecución"""
        self._state = "executing"
        
        result = {
            "agent_id": self.agent_id,
            "domain": self.domain,
            "task": task,
            "execution_pattern": self._config.execution_pattern,
            "status": "completed",
            "capability_used": self.get_capability_score(),
        }
        
        self._execution_history.append(result)
        self._state = "idle"
        
        return result
    
    def add_cognitive_capital(self, capital: Dict[str, Any]) -> None:
        """Añade capital cognitivo generado"""
        self._cognitive_capital.append({
            **capital,
            "added_at": datetime.utcnow().isoformat(),
            "agent_id": self.agent_id,
        })
    
    def get_cognitive_capital(self) -> List[Dict[str, Any]]:
        """Retorna el capital cognitivo acumulado"""
        return self._cognitive_capital.copy()
    
    def get_profile_summary(self) -> Dict[str, Any]:
        """Retorna resumen del perfil inferido"""
        profile = self.profile
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "domain": self.domain,
            "capability_score": profile.capability_score,
            "specialization_score": profile.specialization_score,
            "autonomy_score": profile.autonomy_score,
            "coordination_weight": profile.coordination_weight,
            "skills_count": profile.skills_summary.get("count", 0),
            "tools_count": profile.tools_summary.get("count", 0),
            "execution_pattern": self._config.execution_pattern,
            "orchestration_role": self._config.orchestration_role,
        }


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Configuración (lo que se instancia)
    "AgentConfig",
    "AgentConfigFactory",
    
    # Inferencia (cómo se determina el perfil)
    "ProfileInterpreter",
    "InferredProfile",
    "ProfileInferencePipeline",
    
    # Estrategias
    "ProfilingStrategy",
    "MinimalProfilingStrategy",
    "FullProfilingStrategy",
    "CachedProfilingStrategy",
    
    # Agente
    "DynamicAgent",
]
