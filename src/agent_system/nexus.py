"""
NEXUS - Super Agent Coordinator

Configuration-driven super agent that coordinates all agents and domains.
NO hardcoded values - everything is loaded from configuration files.

NEXUS = Neural Execution Unified System - eXtended Intelligence

This super agent:
1. Receives user queries
2. Automatically detects the appropriate domain (via config)
3. Coordinates with configured roles for the domain
4. Generates intelligent responses using OpenRouter
5. Learns from each interaction (Cognitive Capital)
"""

from typing import Dict, List, Optional, Any, AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import uuid
import json
import logging

from . import (
    AgentGroup,
    AgentGroupManager,
    AgentProfile,
    CognitiveCapital,
    Engram,
    AgentStatus,
)

# Import configuration
from ..config.agent_config import get_config, ConfigLoader

# Import OpenRouter provider
from ..ai_providers.providers.openrouter_provider import (
    OpenRouterProvider,
    OpenRouterProviderConfig,
)

# Import PPCC and Obviousness
from ..core.ppcc import PPCCCycle, PPCCPhase, PPCCState
from ..core.obviousness import ObviousnessContext, ObviousnessContextBuilder

# Import cognitive capital store
from ..cognitive.capital import (
    CognitiveCapitalStore,
    CognitiveCapitalGenerator,
    CognitiveCapital as StoredCapital,
    CapitalType,
    CapitalSource,
)

logger = logging.getLogger(__name__)


@dataclass
class NEXUSConfig:
    """NEXUS Super Agent Configuration - loaded from config files."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "NEXUS"
    
    # API Configuration
    openrouter_api_key: str = ""
    default_model: str = "meta-llama/llama-3.1-8b-instruct"
    max_tokens: int = 4096
    temperature: float = 0.7
    
    # Behavior (loaded from config)
    auto_detect_domain: bool = True
    use_all_roles: bool = True
    generate_with_context: bool = True
    
    # PPCC Configuration
    enable_ppcc: bool = True
    require_alignment: bool = False
    
    # Learning
    enable_capital_learning: bool = True
    min_confidence_threshold: float = 0.6
    
    # Capital Cognitivo
    max_engrams_per_interaction: int = 3
    min_engram_importance: float = 0.3
    
    def __post_init__(self):
        """Load defaults from configuration."""
        config = get_config()
        features = config.get_features()
        defaults = config.get_defaults()
        
        self.auto_detect_domain = features.get("auto_detect_domain", True)
        self.use_all_roles = features.get("use_all_roles", True)
        self.generate_with_context = features.get("generate_with_context", True)
        self.enable_ppcc = features.get("enable_ppcc", True)
        self.enable_capital_learning = features.get("enable_capital_learning", True)
        
        self.min_confidence_threshold = defaults.get("confidence_threshold", 0.6)
        self.max_engrams_per_interaction = defaults.get("max_engrams_per_interaction", 3)
        self.min_engram_importance = defaults.get("min_engram_importance", 0.3)


@dataclass
class NEXUSResponse:
    """NEXUS response."""
    content: str
    domain: str
    domain_brand: str
    confidence: float
    roles_consulted: List[str]
    thinking_process: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "domain": self.domain,
            "domain_brand": self.domain_brand,
            "confidence": self.confidence,
            "roles_consulted": self.roles_consulted,
            "thinking_process": self.thinking_process,
            "timestamp": self.timestamp,
        }


class NEXUSSuperAgent:
    """
    NEXUS - Configuration-Driven Super Agent Coordinator.
    
    The single entry point for all user queries.
    Coordinates with all domains and agents to provide
    intelligent and contextualized responses.
    
    Capabilities:
    - Automatic domain detection (via configuration)
    - Coordination with configured roles
    - Response generation with LLM (OpenRouter)
    - Continuous learning (Cognitive Capital)
    - Response streaming
    """
    
    def __init__(
        self,
        config: Optional[NEXUSConfig] = None,
        openrouter_api_key: Optional[str] = None,
    ):
        self.config = config or NEXUSConfig()
        self.app_config = get_config()
        
        # Override API key if provided
        if openrouter_api_key:
            self.config.openrouter_api_key = openrouter_api_key
        
        # Initialize components
        self.group_manager = AgentGroupManager()
        
        # Initialize OpenRouter provider
        self.llm_provider: Optional[OpenRouterProvider] = None
        if self.config.openrouter_api_key:
            self._init_llm_provider()
        
        # Cognitive Capital for NEXUS
        self.capital = CognitiveCapital(agent_id=self.config.id)
        
        # Cognitive Capital Store for persistence
        self.capital_store = CognitiveCapitalStore()
        self.capital_generator = CognitiveCapitalGenerator(self.capital_store)
        
        # Interaction history for learning
        self.interaction_history: List[Dict[str, Any]] = []
        
        # Active PPCC sessions
        self.active_ppcc_sessions: Dict[str, PPCCCycle] = {}
        
        # Initialize all domain groups
        self._initialize_all_domains()
        
        logger.info(f"NEXUS Super Agent initialized with ID: {self.config.id}")
    
    def _init_llm_provider(self) -> None:
        """Initialize the OpenRouter LLM provider."""
        provider_config = OpenRouterProviderConfig(
            model=self.config.default_model,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
        )
        self.llm_provider = OpenRouterProvider(
            config=provider_config,
            api_key=self.config.openrouter_api_key,
        )
        logger.info(f"OpenRouter provider initialized with model: {self.config.default_model}")
    
    def _initialize_all_domains(self) -> None:
        """Initialize all domain groups from configuration."""
        domains = self.app_config.get_domains()
        
        for domain_id in domains.keys():
            if domain_id != "custom":
                domain_config = self.app_config.get_domain(domain_id)
                if domain_config:
                    self.group_manager.create_group(
                        name=f"{domain_config.get('elegant_name', 'Custom')} Unit",
                        domain=domain_id,
                        description=domain_config.get("description", ""),
                    )
        logger.info(f"Initialized {len(self.group_manager.groups)} domain groups")
    
    def detect_domain(self, query: str) -> tuple:
        """
        Detect the most appropriate domain for a query.
        Uses configuration-driven keyword matching.
        
        Returns:
            Tuple of (domain, confidence)
        """
        return self.app_config.detect_domain(query)
    
    def get_system_prompt(self, domain: str, role: Optional[str] = None) -> str:
        """Generate the system prompt for the LLM - configuration driven."""
        domain_config = self.app_config.get_domain(domain)
        nexus_config = self.app_config.get_nexus_config()
        
        domain_name = domain_config.get("name", "Custom") if domain_config else "Custom"
        domain_elegant = domain_config.get("elegant_name", "CUSTOM") if domain_config else "CUSTOM"
        domain_tagline = domain_config.get("tagline", "") if domain_config else ""
        
        base_prompt = f"""Eres NEXUS, el Super Agente Coordinador del sistema.

## Tu Identidad
- Nombre: NEXUS (Neural Execution Unified System - eXtended Intelligence)
- Rol: Coordinador supremo de todos los agentes y dominios
- Dominio detectado: {domain_elegant} ({domain_name})
- Tagline: {domain_tagline}

## Los Roles que coordinas:
"""
        
        # Add roles from configuration
        roles = self.app_config.get_roles()
        for role_id, role_config in roles.items():
            elegant_name = role_config.get("elegant_name", role_id.upper())
            description = role_config.get("description", "")
            base_prompt += f"- **{elegant_name}** - {description}\n"
        
        base_prompt += """
## Tu Estilo de Respuesta:
- Profesional pero cercano
- Estructurado con secciones claras
- Incluye análisis profundo cuando es necesario
- Proporciona recomendaciones accionables
- Usa markdown para formato

## Instrucciones:
1. Analiza la consulta desde múltiples perspectivas
2. Aplica el conocimiento del dominio
3. Coordina virtualmente con los roles apropiados
4. Genera una respuesta completa y útil
"""
        
        if role:
            role_config = self.app_config.get_role(role)
            if role_config:
                role_elegant = role_config.get("elegant_name", role.upper())
                role_description = role_config.get("description", "")
                base_prompt += f"""
## Rol Especializado Activo: {role_elegant}
{role_description}
Enfoca tu respuesta principalmente desde esta perspectiva.
"""
        
        return base_prompt
    
    async def process_query(
        self,
        query: str,
        domain: Optional[str] = None,
        role: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> NEXUSResponse:
        """
        Process a user query and generate an intelligent response.
        
        Implements PPCC cycle (Proper Prompt Chat Cycle):
        1. PREPARATION: Create obviousness context
        2. ALIGNMENT: Confirm understanding (if enabled)
        3. EXECUTION: Generate response with visible reasoning
        4. DECLARATION: Save cognitive capital
        """
        # Detect domain if not specified
        if not domain and self.config.auto_detect_domain:
            domain, confidence = self.detect_domain(query)
        else:
            domain = domain or "custom"
            confidence = 0.8
        
        domain_config = self.app_config.get_domain(domain)
        domain_brand = domain_config.get("elegant_name", "CUSTOM") if domain_config else "CUSTOM"
        
        # === PHASE 1: PREPARATION ===
        session_id = session_id or str(uuid.uuid4())
        user_id = user_id or "anonymous"
        
        # Load relevant cognitive capital
        relevant_capital = await self._load_relevant_capital(query, domain)
        
        # Create obviousness context (SMART+R+T)
        obviousness_context = self._create_obviousness_context(
            query=query,
            domain=domain,
            session_id=session_id,
            user_id=user_id,
            relevant_capital=relevant_capital,
        )
        
        # Get thinking process
        thinking_process = await self._generate_thinking_process(query, domain, context)
        thinking_process["ppcc_phase"] = "preparation"
        thinking_process["capital_loaded"] = len(relevant_capital)
        
        # Determine which roles to consult
        roles_consulted = self._determine_roles(query, role)
        
        # === PHASE 2: ALIGNMENT (optional) ===
        thinking_process["alignment"] = {
            "understanding": f"Consulta sobre {domain_brand}",
            "context_created": True,
            "capital_context": len(relevant_capital) > 0,
        }
        
        # === PHASE 3: EXECUTION ===
        thinking_process["ppcc_phase"] = "execution"
        
        # Generate response using LLM with capital context
        content = await self._generate_response_with_capital(
            query=query,
            domain=domain,
            roles=roles_consulted,
            context=context,
            relevant_capital=relevant_capital,
            obviousness_context=obviousness_context,
        )
        
        # === PHASE 4: DECLARATION ===
        thinking_process["ppcc_phase"] = "declaration"
        
        # Learn from interaction
        if self.config.enable_capital_learning:
            await self._learn_from_interaction(query, domain, content, confidence)
            
            # Store as distilled cognitive capital
            await self._store_cognitive_capital(
                query=query,
                response=content,
                domain=domain,
                confidence=confidence,
                session_id=session_id,
                user_id=user_id,
            )
        
        return NEXUSResponse(
            content=content,
            domain=domain,
            domain_brand=domain_brand,
            confidence=confidence,
            roles_consulted=roles_consulted,
            thinking_process=thinking_process,
        )
    
    async def _generate_thinking_process(
        self,
        query: str,
        domain: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate internal thinking process with PPCC."""
        domain_config = self.app_config.get_domain(domain)
        domain_brand = domain_config.get("elegant_name", "CUSTOM") if domain_config else "CUSTOM"
        
        return {
            "step_1_analysis": f"Consulta recibida: '{query[:100]}...'",
            "step_2_domain_detection": f"Dominio identificado: {domain_brand}",
            "step_3_preparation": "Creando contexto de obviedad (SMART+R+T)",
            "step_4_capital_retrieval": "Buscando capital cognitivo relevante",
            "step_5_alignment": "Verificando alineación semántica",
            "step_6_execution": "Generando respuesta con razonamiento visible",
            "step_7_declaration": "Guardando capital cognitivo destilado",
            "context_used": context is not None,
            "timestamp": datetime.utcnow().isoformat(),
            "ppcc_enabled": self.config.enable_ppcc,
        }
    
    def _determine_roles(
        self,
        query: str,
        specific_role: Optional[str] = None,
    ) -> List[str]:
        """Determine which roles to consult - configuration driven."""
        return self.app_config.detect_roles(query, specific_role)
    
    async def _load_relevant_capital(
        self,
        query: str,
        domain: str,
    ) -> List[Dict[str, Any]]:
        """Load relevant cognitive capital for the query."""
        relevant = []
        
        # Search in local engrams
        for engram in self.capital.engrams:
            if any(kw.lower() in engram.content.lower() for kw in query.split()[:5]):
                relevant.append({
                    "type": "engram",
                    "content": engram.content,
                    "importance": engram.importance_score,
                    "source": "local_memory",
                })
        
        # Search in global store
        try:
            capital_results = self.capital_store.search(query, limit=3)
            for cap in capital_results:
                relevant.append({
                    "type": "capital",
                    "content": cap.content,
                    "importance": cap.cognitive_value,
                    "source": "global_store",
                    "domain": cap.domain,
                })
        except Exception as e:
            logger.warning(f"Could not search capital store: {e}")
        
        return relevant[:5]
    
    def _create_obviousness_context(
        self,
        query: str,
        domain: str,
        session_id: str,
        user_id: str,
        relevant_capital: List[Dict[str, Any]],
    ) -> ObviousnessContext:
        """Create obviousness context (SMART+R+T) for the query."""
        domain_config = self.app_config.get_domain(domain)
        domain_brand = domain_config.get("elegant_name", "CUSTOM") if domain_config else "CUSTOM"
        
        builder = ObviousnessContextBuilder(
            session_id=session_id,
            user_id=user_id,
        )
        
        # S - Specific
        builder.with_objective(
            objective=query,
            success_criteria=["Respuesta precisa y útil", "Información verificada"],
            deliverables=["Respuesta estructurada", "Fuentes si aplica"],
        )
        
        # A - Allowable
        builder.with_boundaries(
            allow=["web_search", "knowledge_base", "capital_cognitive"],
            deny=["personal_data", "restricted_files"],
            sandbox=True,
        )
        
        # R - Relevant
        builder.with_relevance(
            impact="medium",
            ccv=5,
            knowledge_nodes=[domain],
        )
        
        # T - Time
        builder.with_time(
            priority="normal",
            timeout=60,
        )
        
        # Domain
        builder.with_domain(domain)
        
        return builder.build()
    
    async def _generate_response_with_capital(
        self,
        query: str,
        domain: str,
        roles: List[str],
        context: Optional[Dict[str, Any]],
        relevant_capital: List[Dict[str, Any]],
        obviousness_context: ObviousnessContext,
    ) -> str:
        """Generate response using LLM with cognitive capital context."""
        if not self.llm_provider:
            return self._generate_fallback_response(query, domain, roles)
        
        # Build system prompt with obviousness
        base_system_prompt = self.get_system_prompt(domain, roles[0] if roles else None)
        obviousness_prompt = obviousness_context.to_system_prompt()
        
        # Add cognitive capital if exists
        capital_context = ""
        if relevant_capital:
            capital_context = "\n\n## CAPITAL COGNITIVO RELEVANTE\n"
            capital_context += "Información previamente aprendida que puede ser útil:\n\n"
            for i, cap in enumerate(relevant_capital, 1):
                capital_context += f"### Conocimiento {i} (importancia: {cap['importance']:.2f})\n"
                capital_context += f"{cap['content'][:500]}\n\n"
        
        system_prompt = f"{base_system_prompt}\n\n{obviousness_prompt}{capital_context}"
        
        messages = [{"role": "user", "content": query}]
        
        # Add context if available
        if context:
            context_str = json.dumps(context, ensure_ascii=False, indent=2)
            messages[0]["content"] = f"{query}\n\nContexto adicional:\n{context_str}"
        
        try:
            result = await self.llm_provider.chat_completion(
                messages=messages,
                system_prompt=system_prompt,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )
            
            if result.get("success"):
                return result.get("content", "")
            else:
                logger.error(f"LLM error: {result.get('message', 'Unknown error')}")
                return self._generate_fallback_response(query, domain, roles)
                
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return self._generate_fallback_response(query, domain, roles)
    
    async def _store_cognitive_capital(
        self,
        query: str,
        response: str,
        domain: str,
        confidence: float,
        session_id: str,
        user_id: str,
    ) -> None:
        """Store the interaction as distilled cognitive capital."""
        from uuid import UUID, uuid4
        
        try:
            capital = StoredCapital(
                agent_id=uuid4(),
                capital_type=CapitalType.KNOWLEDGE,
                source=CapitalSource.INTERACTION,
                domain=domain,
                title=f"Q&A: {query[:50]}...",
                content=f"Pregunta: {query}\n\nRespuesta: {response}",
                keywords=query.split()[:5],
                cognitive_value=confidence,
            )
            
            self.capital_store.store(capital)
            logger.info(f"Stored cognitive capital for query: {query[:50]}...")
        except Exception as e:
            logger.warning(f"Could not store cognitive capital: {e}")
    
    def _generate_fallback_response(
        self,
        query: str,
        domain: str,
        roles: List[str],
    ) -> str:
        """Generate a fallback response when LLM is not available."""
        domain_config = self.app_config.get_domain(domain)
        domain_brand = domain_config.get("elegant_name", "CUSTOM") if domain_config else "CUSTOM"
        domain_name = domain_config.get("name", "Custom") if domain_config else "Custom"
        
        return f"""# Respuesta desde {domain_brand}

He recibido tu consulta: "{query[:100]}..."

**Dominio detectado:** {domain_brand} - {domain_name}
**Roles consultados:** {', '.join(r.capitalize() for r in roles)}

---

⚠️ **Nota:** El proveedor LLM no está configurado. Para obtener respuestas completas, configura la API key de OpenRouter.

Para configurar, establece la variable de entorno `OPENROUTER_API_KEY` o pasa la clave al inicializar NEXUS.
"""
    
    async def _learn_from_interaction(
        self,
        query: str,
        domain: str,
        response: str,
        confidence: float,
    ) -> None:
        """Learn from the interaction and update cognitive capital."""
        engram = Engram(
            content=f"Q: {query[:200]}\nA: {response[:500]}",
            metadata={
                "domain": domain,
                "confidence": confidence,
                "timestamp": datetime.utcnow().isoformat(),
            },
            importance_score=confidence,
            source="interaction",
            tags=[domain, "nexus_interaction"],
        )
        
        self.capital.add_engram(engram)
        self.capital.total_interactions += 1
        
        # Store in history
        defaults = self.app_config.get_defaults()
        limit = defaults.get("interaction_history_limit", 100)
        
        self.interaction_history.append({
            "query": query,
            "domain": domain,
            "confidence": confidence,
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        # Keep only last N interactions
        if len(self.interaction_history) > limit:
            self.interaction_history = self.interaction_history[-limit:]
    
    async def stream_response(
        self,
        query: str,
        domain: Optional[str] = None,
        role: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[str]:
        """Stream the response token by token."""
        # Detect domain
        if not domain and self.config.auto_detect_domain:
            domain, _ = self.detect_domain(query)
        domain = domain or "custom"
        
        # Determine roles
        roles = self._determine_roles(query, role)
        
        if not self.llm_provider:
            fallback = self._generate_fallback_response(query, domain, roles)
            yield fallback
            return
        
        # Build system prompt
        system_prompt = self.get_system_prompt(domain, roles[0] if roles else None)
        
        messages = [{"role": "user", "content": query}]
        
        if context:
            context_str = json.dumps(context, ensure_ascii=False, indent=2)
            messages[0]["content"] = f"{query}\n\nContexto adicional:\n{context_str}"
        
        # Stream from LLM
        try:
            async for chunk in self.llm_provider.stream_chat(
                messages=messages,
                system_prompt=system_prompt,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            ):
                yield chunk
        except Exception as e:
            logger.error(f"Error streaming response: {e}")
            yield self._generate_fallback_response(query, domain, roles)
    
    def get_status(self) -> Dict[str, Any]:
        """Get the current status of NEXUS."""
        nexus_config = self.app_config.get_nexus_config()
        
        return {
            "id": self.config.id,
            "name": nexus_config.get("name", "NEXUS"),
            "full_name": nexus_config.get("full_name", "Neural Execution Unified System"),
            "status": "active",
            "domains_available": len(self.group_manager.groups),
            "llm_configured": self.llm_provider is not None,
            "model": self.config.default_model if self.llm_provider else "none",
            "capital": {
                "total_engrams": self.capital.total_engrams,
                "total_interactions": self.capital.total_interactions,
                "capital_value": self.capital.capital_value,
            },
            "last_interactions": len(self.interaction_history),
        }
    
    def get_available_domains(self) -> List[Dict[str, Any]]:
        """Get list of available domains - configuration driven."""
        domains = []
        for domain_id, domain_config in self.app_config.get_domains().items():
            domains.append({
                "domain": domain_id,
                "name": domain_config.get("name", ""),
                "elegant_name": domain_config.get("elegant_name", ""),
                "tagline": domain_config.get("tagline", ""),
                "icon": domain_config.get("icon", ""),
                "color": domain_config.get("color", ""),
                "description": domain_config.get("description", ""),
            })
        return domains
    
    def get_available_roles(self) -> List[Dict[str, Any]]:
        """Get list of available roles - configuration driven."""
        roles = []
        for role_id, role_config in self.app_config.get_roles().items():
            roles.append({
                "role": role_id,
                "elegant_name": role_config.get("elegant_name", ""),
                "tagline": role_config.get("tagline", ""),
                "description": role_config.get("description", ""),
                "icon": role_config.get("icon", ""),
                "color": role_config.get("color", ""),
            })
        return roles


# Singleton instance
_nexus_instance: Optional[NEXUSSuperAgent] = None


def get_nexus(api_key: Optional[str] = None) -> NEXUSSuperAgent:
    """Get or create the NEXUS singleton instance."""
    global _nexus_instance
    
    if _nexus_instance is None:
        config = NEXUSConfig()
        if api_key:
            config.openrouter_api_key = api_key
        _nexus_instance = NEXUSSuperAgent(config=config)
    
    return _nexus_instance


def reset_nexus() -> None:
    """Reset the NEXUS singleton."""
    global _nexus_instance
    _nexus_instance = None


# Branding from configuration
def get_nexus_brand() -> Dict[str, Any]:
    """Get NEXUS branding from configuration."""
    config = get_config()
    return config.get_nexus_config()


# Export NEXUS_BRAND for backward compatibility (loaded from config)
NEXUS_BRAND = get_nexus_brand()


__all__ = [
    "NEXUSSuperAgent",
    "NEXUSConfig",
    "NEXUSResponse",
    "get_nexus",
    "reset_nexus",
    "get_nexus_brand",
    "NEXUS_BRAND",
]
