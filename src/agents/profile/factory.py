"""
Profile-Based Agent Factory - Crea agentes desde perfiles de configuración.

Este factory NO usa enums de tipos. En su lugar, crea agentes basándose
en AgentProfile - una configuración completa que define:
- Skills del agente
- Tools/MCP disponibles
- Prompt/Contexto
- Memoria/Capital Cognitivo
- Patrón de ejecución
- Rol de orquestación

@author: OpenClaw Agent SaaS
@philosophy: Agents are what they HAVE and DO, not an enum type.
"""

from typing import Any, Dict, List, Optional, Type, Union
from uuid import UUID
import logging
import asyncio

from . import (
    AgentProfile,
    AgentProfileBuilder,
    ExecutionPattern,
    OrchestrationRole,
)

logger = logging.getLogger(__name__)


# ============================================================================
# BASE AGENT - Agente base dinámico
# ============================================================================

class DynamicAgent:
    """
    Agente dinámico configurado por perfil.
    
    NO tiene un "tipo" fijo - su comportamiento está determinado
    completamente por su AgentProfile.
    """
    
    def __init__(
        self,
        profile: AgentProfile,
        memory_vcs: Optional[Any] = None,  # MemoryVCS
        skills_registry: Optional[Any] = None,  # SkillsRegistry
        mcp_registry: Optional[Any] = None,  # MCPRegistry
    ):
        self.profile = profile
        self.memory_vcs = memory_vcs
        self.skills_registry = skills_registry
        self.mcp_registry = mcp_registry
        
        # Estado interno
        self._context: Dict[str, Any] = {}
        self._execution_history: List[Dict[str, Any]] = []
        
    @property
    def name(self) -> str:
        return self.profile.name
    
    @property
    def domain(self) -> str:
        return self.profile.domain
    
    @property
    def capabilities(self) -> Dict[str, Any]:
        return self.profile.get_capabilities_summary()
    
    def has_capability(self, skill_name: str) -> bool:
        """Verificar si el agente tiene una skill específica."""
        return self.profile.has_skill(skill_name)
    
    def has_tool_access(self, tool_name: str) -> bool:
        """Verificar si el agente tiene acceso a una herramienta."""
        return self.profile.has_tool(tool_name)
    
    async def query_memory(
        self,
        query: str,
        domain_filter: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Consultar la memoria del agente."""
        if not self.memory_vcs:
            logger.warning(f"Agent {self.name} has no memory VCS configured")
            return []
        
        effective_domain = domain_filter or self.domain
        
        results = self.memory_vcs.search(
            query=query,
            limit=limit,
            domain_filter=effective_domain,
        )
        
        return results
    
    async def store_memory(
        self,
        topic_key: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Almacenar información en la memoria del agente."""
        if not self.memory_vcs:
            logger.warning(f"Agent {self.name} has no memory VCS configured")
            return {"success": False, "error": "No memory VCS configured"}
        
        result = self.memory_vcs.upsert(
            topic_key=topic_key,
            content=content,
            metadata=metadata or {},
        )
        
        return result
    
    async def get_skill_instructions(self, skill_name: str) -> Optional[str]:
        """Obtener instrucciones de una skill específica."""
        if not self.skills_registry:
            logger.warning(f"Agent {self.name} has no skills registry configured")
            return None
        
        if not self.has_capability(skill_name):
            logger.warning(f"Agent {self.name} does not have skill: {skill_name}")
            return None
        
        skill = self.skills_registry.get(skill_name)
        if skill:
            return skill.instructions
        
        return None
    
    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Ejecutar una herramienta vía MCP."""
        if not self.mcp_registry:
            logger.warning(f"Agent {self.name} has no MCP registry configured")
            return {"success": False, "error": "No MCP registry configured"}
        
        if not self.has_tool_access(tool_name):
            logger.warning(f"Agent {self.name} does not have access to tool: {tool_name}")
            return {"success": False, "error": f"No access to tool: {tool_name}"}
        
        result = await self.mcp_registry.execute_tool(tool_name, arguments)
        
        # Registrar en historial
        self._execution_history.append({
            "tool": tool_name,
            "arguments": arguments,
            "result": result,
        })
        
        return result
    
    async def process(
        self,
        input_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Procesar una solicitud.
        
        Este método debe ser extendido por implementaciones específicas
        que integren con proveedores de LLM.
        """
        self._context.update(context or {})
        
        result = {
            "agent": self.name,
            "domain": self.domain,
            "capabilities": self.capabilities,
            "input": input_data,
            "status": "processed",
        }
        
        return result
    
    def get_execution_history(self) -> List[Dict[str, Any]]:
        """Obtener historial de ejecución."""
        return self._execution_history.copy()
    
    def get_system_prompt(self) -> str:
        """Obtener el prompt del sistema."""
        if self.profile.prompt_context:
            return self.profile.prompt_context.system_prompt
        return f"You are {self.name}, an assistant specialized in {self.domain}."


# ============================================================================
# PROFILE-BASED AGENT FACTORY
# ============================================================================

class ProfileBasedAgentFactory:
    """
    Factory para crear agentes desde perfiles.
    
    A diferencia del factory anterior basado en enums, este factory:
    - NO tiene un registro de "tipos" de agentes
    - Crea agentes dinámicamente desde AgentProfile
    - Inyecta dependencias (memoria, skills, MCP) dinámicamente
    """
    
    def __init__(
        self,
        memory_vcs: Optional[Any] = None,
        skills_registry: Optional[Any] = None,
        mcp_registry: Optional[Any] = None,
        llm_provider: Optional[Any] = None,
    ):
        self.memory_vcs = memory_vcs
        self.skills_registry = skills_registry
        self.mcp_registry = mcp_registry
        self.llm_provider = llm_provider
        
        # Cache de instancias
        self._instances: Dict[str, DynamicAgent] = {}
    
    def create_agent(
        self,
        profile: AgentProfile,
        instance_id: Optional[str] = None,
        custom_memory_vcs: Optional[Any] = None,
        custom_skills_registry: Optional[Any] = None,
        custom_mcp_registry: Optional[Any] = None,
    ) -> DynamicAgent:
        """
        Crear un agente desde un perfil.
        
        Args:
            profile: Configuración completa del agente
            instance_id: ID opcional para cachear la instancia
            custom_memory_vcs: MemoryVCS personalizado (sobrescribe el default)
            custom_skills_registry: SkillsRegistry personalizado
            custom_mcp_registry: MCPRegistry personalizado
            
        Returns:
            Instancia de DynamicAgent configurada
        """
        agent = DynamicAgent(
            profile=profile,
            memory_vcs=custom_memory_vcs or self.memory_vcs,
            skills_registry=custom_skills_registry or self.skills_registry,
            mcp_registry=custom_mcp_registry or self.mcp_registry,
        )
        
        if instance_id:
            self._instances[instance_id] = agent
            logger.info(f"Created and cached agent: {profile.name} (id: {instance_id})")
        else:
            logger.info(f"Created agent: {profile.name}")
        
        return agent
    
    def create_agent_from_builder(
        self,
        builder: AgentProfileBuilder,
        instance_id: Optional[str] = None,
    ) -> DynamicAgent:
        """Crear agente desde un builder."""
        profile = builder.build()
        return self.create_agent(profile, instance_id)
    
    def create_quick_agent(
        self,
        name: str,
        domain: str = "general",
        skills: Optional[List[str]] = None,
        tools: Optional[List[str]] = None,
        system_prompt: Optional[str] = None,
        **kwargs,
    ) -> DynamicAgent:
        """
        Crear un agente rápidamente con configuración mínima.
        
        Útil para crear agentes ad-hoc sin perfil completo.
        """
        builder = AgentProfileBuilder(name).with_domain(domain)
        
        # Agregar skills
        for skill_name in (skills or []):
            builder.with_skill(skill_name, skill_name)
        
        # Agregar tools
        for tool_name in (tools or []):
            builder.with_tool(tool_name)
        
        # Agregar prompt
        if system_prompt:
            builder.with_prompt(system_prompt)
        
        return self.create_agent_from_builder(builder)
    
    def create_orchestrator(
        self,
        name: str = "Lead Orchestrator",
        sub_agent_profiles: Optional[List[AgentProfile]] = None,
    ) -> DynamicAgent:
        """
        Crear un agente orquestador.
        
        El orquestador es un agente con:
        - Rol de orquestación: LEAD
        - Capacidad de coordinar sub-agentes
        """
        builder = AgentProfileBuilder(name).as_lead().with_domain("orchestration")
        
        if sub_agent_profiles:
            sub_ids = [p.id for p in sub_agent_profiles]
            builder.with_sub_agents(sub_ids)
        
        return self.create_agent_from_builder(builder)
    
    def create_sequential_team(
        self,
        name: str,
        agent_profiles: List[AgentProfile],
    ) -> DynamicAgent:
        """
        Crear un equipo de agentes que ejecutan secuencialmente.
        
        NOTA: Esto NO es un "tipo" de agente, es un PATRÓN de ejecución.
        """
        builder = (AgentProfileBuilder(name)
            .with_execution_pattern(ExecutionPattern.SEQUENTIAL)
            .with_sub_agents([p.id for p in agent_profiles]))
        
        orchestrator = self.create_agent_from_builder(builder)
        return orchestrator
    
    def create_parallel_team(
        self,
        name: str,
        agent_profiles: List[AgentProfile],
    ) -> DynamicAgent:
        """
        Crear un equipo de agentes que ejecutan en paralelo.
        
        NOTA: Esto NO es un "tipo" de agente, es un PATRÓN de ejecución.
        """
        builder = (AgentProfileBuilder(name)
            .with_execution_pattern(ExecutionPattern.PARALLEL)
            .with_sub_agents([p.id for p in agent_profiles]))
        
        orchestrator = self.create_agent_from_builder(builder)
        return orchestrator
    
    def get_instance(self, instance_id: str) -> Optional[DynamicAgent]:
        """Obtener una instancia cacheada por ID."""
        return self._instances.get(instance_id)
    
    def remove_instance(self, instance_id: str) -> bool:
        """Eliminar una instancia del cache."""
        if instance_id in self._instances:
            del self._instances[instance_id]
            return True
        return False
    
    def list_instances(self) -> List[str]:
        """Listar IDs de instancias cacheadas."""
        return list(self._instances.keys())
    
    def set_memory_vcs(self, memory_vcs: Any) -> None:
        """Configurar MemoryVCS global."""
        self.memory_vcs = memory_vcs
    
    def set_skills_registry(self, skills_registry: Any) -> None:
        """Configurar SkillsRegistry global."""
        self.skills_registry = skills_registry
    
    def set_mcp_registry(self, mcp_registry: Any) -> None:
        """Configurar MCPRegistry global."""
        self.mcp_registry = mcp_registry
    
    def set_llm_provider(self, llm_provider: Any) -> None:
        """Configurar proveedor LLM global."""
        self.llm_provider = llm_provider


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

# Factory global por defecto
default_factory = ProfileBasedAgentFactory()


def create_agent(
    name: str,
    domain: str = "general",
    skills: Optional[List[str]] = None,
    tools: Optional[List[str]] = None,
    system_prompt: Optional[str] = None,
    **kwargs,
) -> DynamicAgent:
    """Función de conveniencia para crear un agente rápidamente."""
    return default_factory.create_quick_agent(
        name=name,
        domain=domain,
        skills=skills,
        tools=tools,
        system_prompt=system_prompt,
        **kwargs,
    )


def create_agent_from_profile(profile: AgentProfile) -> DynamicAgent:
    """Función de conveniencia para crear un agente desde perfil."""
    return default_factory.create_agent(profile)


def create_orchestrator(
    name: str = "Lead Orchestrator",
    sub_agent_profiles: Optional[List[AgentProfile]] = None,
) -> DynamicAgent:
    """Función de conveniencia para crear un orquestador."""
    return default_factory.create_orchestrator(name, sub_agent_profiles)
