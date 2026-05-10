"""
NEXUS - Super Agente Coordinador
El cerebro central del sistema IOVBA que coordina todos los agentes y dominios.

NEXUS = Neural Execution Unified System - eXtended Intelligence

Este super agente:
1. Recibe consultas del usuario
2. Detecta automáticamente el dominio apropiado
3. Coordina con los 5 roles IOVBA del dominio
4. Genera respuestas inteligentes usando OpenRouter
5. Aprende de cada interacción (Capital Cognitivo)
"""

from typing import Dict, List, Optional, Any, AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import uuid
import json
import logging

from .groups import (
    IOVBAGroup,
    IOVBAGroupManager,
    IOVBADomain,
    IOVBARole,
    DOMAIN_BRANDING,
    ROLE_BRANDING,
    CognitiveCapital,
    Engram,
    AgentStatus,
)
from .lead_assistant import LeadAssistant, LeadAssistantConfig

# Import OpenRouter provider
from ..ai_providers.providers.openrouter_provider import (
    OpenRouterProvider,
    OpenRouterProviderConfig,
)

logger = logging.getLogger(__name__)


# ============================================
# NEXUS BRANDING
# ============================================

NEXUS_BRAND = {
    "name": "NEXUS",
    "full_name": "Neural Execution Unified System - eXtended Intelligence",
    "tagline": "Your Intelligent Orchestrator",
    "icon": "Brain",
    "color": "#6366F1",
    "gradient": "from-indigo-500 via-purple-500 to-pink-500",
    "description": "Super Agente Coordinador que unifica todos los dominios y agentes IOVBA",
}


# ============================================
# DOMAIN DETECTION KEYWORDS
# ============================================

DOMAIN_KEYWORDS: Dict[IOVBADomain, List[str]] = {
    "swe": [
        "código", "programming", "software", "desarrollo", "api", "debug", "bug",
        "deploy", "git", "docker", "kubernetes", "react", "python", "javascript",
        "database", "arquitectura", "sistema", "backend", "frontend", "devops"
    ],
    "salud": [
        "salud", "health", "médico", "medical", "enfermedad", "disease", "síntomas",
        "diagnóstico", "diagnosis", "tratamiento", "treatment", "paciente", "patient",
        "medicamento", "medicine", "hospital", "doctor", "doctora", "clínica",
        "hantavirus", "virus", "bacteria", "infección", "vacuna", "vaccine"
    ],
    "deportes": [
        "deporte", "sport", "fútbol", "soccer", "basketball", "tenis", "atletismo",
        "ejercicio", "exercise", "entrenamiento", "training", "jugador", "player",
        "equipo", "team", "competición", "competition", "olímpico", "olympic"
    ],
    "noticias": [
        "noticia", "news", "actualidad", "current events", "periódico", "newspaper",
        "periodismo", "journalism", "reportaje", "report", "entrevista", "interview",
        "breaking", "última hora", "titular", "headline"
    ],
    "quimica": [
        "química", "chemistry", "molécula", "molecule", "compuesto", "compound",
        "reacción", "reaction", "elemento", "element", "átomo", "atom",
        "orgánica", "organic", "laboratorio", "laboratory"
    ],
    "biologia": [
        "biología", "biology", "celular", "cell", "organismo", "organism",
        "ecosistema", "ecosystem", "evolución", "evolution", "especie", "species",
        "genética", "genetics", "adn", "dna", "ARN", "RNA"
    ],
    "biotecnologia": [
        "biotecnología", "biotechnology", "bioingeniería", "bioengineering",
        "terapia génica", "gene therapy", "crispr", "transgénico", "gmo",
        "biomedicina", "biomedicine", "farmacología", "pharmacology"
    ],
    "geopolitica": [
        "geopolítica", "geopolitics", "política internacional", "international politics",
        "diplomacia", "diplomacy", "tratado", "treaty", "sanción", "sanction",
        "país", "country", "frontera", "border", "conflicto", "conflict"
    ],
    "finanzas": [
        "finanzas", "finance", "inversión", "investment", "mercado", "market",
        "acciones", "stocks", "crypto", "criptomoneda", "bitcoin", "ethereum",
        "banco", "bank", "préstamo", "loan", "interés", "interest"
    ],
    "legal": [
        "legal", "ley", "law", "jurídico", "juridical", "contrato", "contract",
        "demanda", "lawsuit", "tribunal", "court", "abogado", "lawyer",
        "derechos", "rights", "constitución", "constitution", "reglamento"
    ],
    "educacion": [
        "educación", "education", "aprendizaje", "learning", "enseñanza", "teaching",
        "escuela", "school", "universidad", "university", "estudiante", "student",
        "profesor", "teacher", "curso", "course", "diploma", "certificado"
    ],
    "investigacion": [
        "investigación", "research", "estudio", "study", "experimento", "experiment",
        "hipótesis", "hypothesis", "metodología", "methodology", "análisis", "analysis",
        "publicación", "publication", "paper", "artículo", "científico", "scientific"
    ],
    "marketing": [
        "marketing", "publicidad", "advertising", "campaña", "campaign",
        "marca", "brand", "cliente", "customer", "ventas", "sales",
        "seo", "social media", "contenido", "content", "engagement"
    ],
    "custom": [],
}


@dataclass
class NEXUSConfig:
    """Configuración del Super Agente NEXUS"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "NEXUS"
    
    # API Configuration
    openrouter_api_key: str = ""
    default_model: str = "anthropic/claude-3.5-sonnet"
    max_tokens: int = 4096
    temperature: float = 0.7
    
    # Behavior
    auto_detect_domain: bool = True
    use_all_iovba_roles: bool = True
    generate_with_context: bool = True
    
    # Learning
    enable_capital_learning: bool = True
    min_confidence_threshold: float = 0.6


@dataclass
class NEXUSResponse:
    """Respuesta de NEXUS"""
    content: str
    domain: IOVBADomain
    domain_brand: str  # Elegant name
    confidence: float
    roles_consulted: List[IOVBARole]
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
    NEXUS - Super Agente Coordinador del Sistema IOVBA
    
    Es el punto de entrada único para todas las consultas del usuario.
    Coordina con todos los dominios y agentes para proporcionar respuestas
    inteligentes y contextualizadas.
    
    Capacidades:
    - Detección automática de dominio
    - Coordinación con los 5 roles IOVBA
    - Generación de respuestas con LLM (OpenRouter)
    - Aprendizaje continuo (Capital Cognitivo)
    - Streaming de respuestas
    """
    
    def __init__(
        self,
        config: Optional[NEXUSConfig] = None,
        openrouter_api_key: Optional[str] = None,
    ):
        self.config = config or NEXUSConfig()
        
        # Override API key if provided
        if openrouter_api_key:
            self.config.openrouter_api_key = openrouter_api_key
        
        # Initialize components
        self.group_manager = IOVBAGroupManager()
        self.lead_assistant = LeadAssistant(
            config=LeadAssistantConfig(name="NEXUS Lead Assistant"),
            group_manager=self.group_manager,
        )
        
        # Initialize OpenRouter provider
        self.llm_provider: Optional[OpenRouterProvider] = None
        if self.config.openrouter_api_key:
            self._init_llm_provider()
        
        # Cognitive Capital for NEXUS
        self.capital = CognitiveCapital(agent_id=self.config.id)
        
        # Interaction history for learning
        self.interaction_history: List[Dict[str, Any]] = []
        
        # Initialize all domain groups
        self._initialize_all_domains()
        
        logger.info(f"NEXUS Super Agent initialized with ID: {self.config.id}")
    
    def _init_llm_provider(self) -> None:
        """Initialize the OpenRouter LLM provider"""
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
        """Initialize all domain groups"""
        for domain in DOMAIN_BRANDING.keys():
            if domain != "custom":
                brand = DOMAIN_BRANDING[domain]
                self.group_manager.create_group(
                    name=f"{brand.elegant_name} Unit",
                    domain=domain,
                    description=brand.description,
                )
        logger.info(f"Initialized {len(self.group_manager.groups)} domain groups")
    
    def detect_domain(self, query: str) -> tuple[IOVBADomain, float]:
        """
        Detecta el dominio más apropiado para la consulta.
        
        Returns:
            Tuple de (dominio, confianza)
        """
        query_lower = query.lower()
        scores: Dict[IOVBADomain, int] = {}
        
        for domain, keywords in DOMAIN_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in query_lower)
            if score > 0:
                scores[domain] = score
        
        if not scores:
            return "custom", 0.3
        
        # Get best domain
        best_domain = max(scores, key=scores.get)
        total_matches = scores[best_domain]
        
        # Calculate confidence
        max_possible = len(DOMAIN_KEYWORDS.get(best_domain, []))
        confidence = min(0.95, 0.4 + (total_matches / max(max_possible, 1)) * 0.5)
        
        return best_domain, confidence
    
    def get_system_prompt(self, domain: IOVBADomain, role: Optional[IOVBARole] = None) -> str:
        """Generate the system prompt for the LLM"""
        domain_brand = DOMAIN_BRANDING.get(domain, DOMAIN_BRANDING["custom"])
        
        base_prompt = f"""Eres NEXUS, el Super Agente Coordinador del sistema IOVBA.

## Tu Identidad
- Nombre: NEXUS (Neural Execution Unified System - eXtended Intelligence)
- Rol: Coordinador supremo de todos los agentes y dominios IOVBA
- Dominio detectado: {domain_brand.elegant_name} ({domain_brand.name})
- Tagline: {domain_brand.tagline}

## Los 5 Roles IOVBA que coordinas:
1. **INVESTIGATOR** - Descubre y analiza información profunda
2. **OBSERVER** - Monitorea y detecta patrones
3. **VALIDATOR** - Valida y asegura calidad
4. **BUILDER** - Construye e implementa soluciones
5. **ASSISTANT** - Coordina y facilita comunicación

## Tu Estilo de Respuesta:
- Profesional pero cercano
- Estructurado con secciones claras
- Incluye análisis profundo cuando es necesario
- Proporciona recomendaciones accionables
- Usa markdown para formato

## Instrucciones:
1. Analiza la consulta desde múltiples perspectivas
2. Aplica el conocimiento del dominio {domain_brand.elegant_name}
3. Coordina virtualmente con los roles IOVBA apropiados
4. Genera una respuesta completa y útil
"""
        
        if role:
            role_brand = ROLE_BRANDING.get(role, ROLE_BRANDING["asistente"])
            base_prompt += f"""
## Rol Especializado Activo: {role_brand.elegant_name}
{role_brand.description}
Enfoca tu respuesta principalmente desde esta perspectiva.
"""
        
        return base_prompt
    
    async def process_query(
        self,
        query: str,
        domain: Optional[IOVBADomain] = None,
        role: Optional[IOVBARole] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> NEXUSResponse:
        """
        Procesa una consulta del usuario y genera una respuesta inteligente.
        
        Args:
            query: La consulta del usuario
            domain: Dominio específico (opcional, se detecta automáticamente)
            role: Rol específico a enfocar (opcional)
            context: Contexto adicional (opcional)
            
        Returns:
            NEXUSResponse con la respuesta completa
        """
        # Detect domain if not specified
        if not domain and self.config.auto_detect_domain:
            domain, confidence = self.detect_domain(query)
        else:
            domain = domain or "custom"
            confidence = 0.8
        
        domain_brand = DOMAIN_BRANDING.get(domain, DOMAIN_BRANDING["custom"])
        
        # Get thinking process
        thinking_process = await self._generate_thinking_process(query, domain, context)
        
        # Determine which roles to consult
        roles_consulted = self._determine_roles(query, role)
        
        # Generate response using LLM
        content = await self._generate_response(query, domain, roles_consulted, context)
        
        # Learn from interaction
        if self.config.enable_capital_learning:
            await self._learn_from_interaction(query, domain, content, confidence)
        
        return NEXUSResponse(
            content=content,
            domain=domain,
            domain_brand=domain_brand.elegant_name,
            confidence=confidence,
            roles_consulted=roles_consulted,
            thinking_process=thinking_process,
        )
    
    async def _generate_thinking_process(
        self,
        query: str,
        domain: IOVBADomain,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate internal thinking process"""
        domain_brand = DOMAIN_BRANDING.get(domain, DOMAIN_BRANDING["custom"])
        
        return {
            "step_1_analysis": f"Consulta recibida: '{query[:100]}...'",
            "step_2_domain_detection": f"Dominio identificado: {domain_brand.elegant_name}",
            "step_3_role_coordination": "Coordinando con roles IOVBA apropiados",
            "step_4_knowledge_retrieval": "Accediendo capital cognitivo",
            "step_5_response_generation": "Generando respuesta estructurada",
            "context_used": context is not None,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    def _determine_roles(
        self,
        query: str,
        specific_role: Optional[IOVBARole] = None,
    ) -> List[IOVBARole]:
        """Determine which IOVBA roles to consult"""
        if specific_role:
            return [specific_role]
        
        query_lower = query.lower()
        roles: List[IOVBARole] = []
        
        # Keyword-based role detection
        if any(kw in query_lower for kw in ["investigar", "buscar", "analizar", "research", "investigate", "qué es", "explica"]):
            roles.append("investigador")
        
        if any(kw in query_lower for kw in ["monitorear", "detectar", "patrones", "monitor", "observe", "tendencias"]):
            roles.append("observador")
        
        if any(kw in query_lower for kw in ["verificar", "validar", "probar", "validate", "verify", "es correcto"]):
            roles.append("validador")
        
        if any(kw in query_lower for kw in ["crear", "construir", "implementar", "build", "create", "generar", "hacer"]):
            roles.append("builder")
        
        # Always include assistant for coordination
        if not roles:
            roles.append("asistente")
            roles.append("investigador")  # Default to investigation
        
        return roles
    
    async def _generate_response(
        self,
        query: str,
        domain: IOVBADomain,
        roles: List[IOVBARole],
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate the actual response using LLM"""
        if not self.llm_provider:
            # Fallback to template response
            return self._generate_fallback_response(query, domain, roles)
        
        # Build messages
        system_prompt = self.get_system_prompt(domain, roles[0] if roles else None)
        
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
    
    def _generate_fallback_response(
        self,
        query: str,
        domain: IOVBADomain,
        roles: List[IOVBARole],
    ) -> str:
        """Generate a fallback response when LLM is not available"""
        domain_brand = DOMAIN_BRANDING.get(domain, DOMAIN_BRANDING["custom"])
        
        return f"""# Respuesta desde {domain_brand.elegant_name}

He recibido tu consulta: "{query[:100]}..."

**Dominio detectado:** {domain_brand.elegant_name} - {domain_brand.name}
**Roles consultados:** {', '.join(r.capitalize() for r in roles)}

---

⚠️ **Nota:** El proveedor LLM no está configurado. Para obtener respuestas completas, configura la API key de OpenRouter.

Para configurar, establece la variable de entorno `OPENROUTER_API_KEY` o pasa la clave al inicializar NEXUS.
"""
    
    async def _learn_from_interaction(
        self,
        query: str,
        domain: IOVBADomain,
        response: str,
        confidence: float,
    ) -> None:
        """Learn from the interaction and update cognitive capital"""
        # Create engram
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
        self.interaction_history.append({
            "query": query,
            "domain": domain,
            "confidence": confidence,
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        # Keep only last 100 interactions in memory
        if len(self.interaction_history) > 100:
            self.interaction_history = self.interaction_history[-100:]
    
    async def stream_response(
        self,
        query: str,
        domain: Optional[IOVBADomain] = None,
        role: Optional[IOVBARole] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[str]:
        """
        Stream the response token by token.
        
        Yields chunks of the response as they are generated.
        """
        # Detect domain
        if not domain and self.config.auto_detect_domain:
            domain, _ = self.detect_domain(query)
        domain = domain or "custom"
        
        # Determine roles
        roles = self._determine_roles(query, role)
        
        if not self.llm_provider:
            # Yield fallback response
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
        """Get the current status of NEXUS"""
        return {
            "id": self.config.id,
            "name": NEXUS_BRAND["name"],
            "full_name": NEXUS_BRAND["full_name"],
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
        """Get list of available domains"""
        domains = []
        for domain, brand in DOMAIN_BRANDING.items():
            domains.append({
                "domain": domain,
                "name": brand.name,
                "elegant_name": brand.elegant_name,
                "tagline": brand.tagline,
                "icon": brand.icon,
                "color": brand.color,
                "description": brand.description,
            })
        return domains
    
    def get_available_roles(self) -> List[Dict[str, Any]]:
        """Get list of available roles"""
        roles = []
        for role, brand in ROLE_BRANDING.items():
            roles.append({
                "role": role,
                "elegant_name": brand.elegant_name,
                "tagline": brand.tagline,
                "description": brand.description,
                "icon": brand.icon,
                "color": brand.color,
            })
        return roles


# Singleton instance for global access
_nexus_instance: Optional[NEXUSSuperAgent] = None


def get_nexus(api_key: Optional[str] = None) -> NEXUSSuperAgent:
    """Get or create the NEXUS singleton instance"""
    global _nexus_instance
    
    if _nexus_instance is None:
        config = NEXUSConfig()
        if api_key:
            config.openrouter_api_key = api_key
        _nexus_instance = NEXUSSuperAgent(config=config)
    
    return _nexus_instance


def reset_nexus() -> None:
    """Reset the NEXUS singleton"""
    global _nexus_instance
    _nexus_instance = None
