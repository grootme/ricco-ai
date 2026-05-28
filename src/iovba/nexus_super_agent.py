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
    # Modelo gratuito de Meta a través de OpenRouter
    default_model: str = "meta-llama/llama-3.1-8b-instruct"
    max_tokens: int = 4096
    temperature: float = 0.7
    
    # Behavior
    auto_detect_domain: bool = True
    use_all_iovba_roles: bool = True
    generate_with_context: bool = True
    
    # PPCC Configuration
    enable_ppcc: bool = True  # Activar ciclo PPCC completo
    require_alignment: bool = False  # Si True, requiere confirmación del usuario
    
    # Learning
    enable_capital_learning: bool = True
    min_confidence_threshold: float = 0.6
    
    # Capital Cognitivo
    max_engrams_per_interaction: int = 3
    min_engram_importance: float = 0.3


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
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> NEXUSResponse:
        """
        Procesa una consulta del usuario y genera una respuesta inteligente.
        
        Implementa el ciclo PPCC (Proper Prompt Chat Cycle):
        1. PREPARACIÓN: Crear contexto de obviedad
        2. ALINEACIÓN: Confirmar entendimiento (si está habilitado)
        3. EJECUCIÓN: Generar respuesta con razonamiento visible
        4. DECLARACIÓN: Guardar capital cognitivo
        
        Args:
            query: La consulta del usuario
            domain: Dominio específico (opcional, se detecta automáticamente)
            role: Rol específico a enfocar (opcional)
            context: Contexto adicional (opcional)
            session_id: ID de sesión para PPCC
            user_id: ID del usuario
            
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
        
        # === FASE 1: PREPARACIÓN ===
        session_id = session_id or str(uuid.uuid4())
        user_id = user_id or "anonymous"
        
        # Cargar capital cognitivo relevante
        relevant_capital = await self._load_relevant_capital(query, domain)
        
        # Crear contexto de obviedad (SMART+R+T)
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
        
        # === FASE 2: ALINEACIÓN (opcional) ===
        # Por ahora, saltamos alineación explícita para respuestas directas
        # Pero registramos el contexto en el thinking process
        thinking_process["alignment"] = {
            "understanding": f"Consulta sobre {domain_brand.elegant_name}",
            "context_created": True,
            "capital_context": len(relevant_capital) > 0,
        }
        
        # === FASE 3: EJECUCIÓN ===
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
        
        # === FASE 4: DECLARACIÓN ===
        thinking_process["ppcc_phase"] = "declaration"
        
        # Learn from interaction
        if self.config.enable_capital_learning:
            await self._learn_from_interaction(query, domain, content, confidence)
            
            # Guardar como capital cognitivo destilado
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
        """Generate internal thinking process con PPCC"""
        domain_brand = DOMAIN_BRANDING.get(domain, DOMAIN_BRANDING["custom"])
        
        return {
            "step_1_analysis": f"Consulta recibida: '{query[:100]}...'",
            "step_2_domain_detection": f"Dominio identificado: {domain_brand.elegant_name}",
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
    
    async def _load_relevant_capital(
        self,
        query: str,
        domain: IOVBADomain,
    ) -> List[Dict[str, Any]]:
        """
        Carga capital cognitivo relevante para la consulta.
        
        Busca en:
        1. Engrams del agente (memoria a corto plazo)
        2. CognitiveCapitalStore (memoria a largo plazo)
        """
        relevant = []
        
        # Buscar en engrams locales
        for engram in self.capital.engrams:
            # Simple keyword matching - podría mejorarse con embeddings
            if any(kw.lower() in engram.content.lower() for kw in query.split()[:5]):
                relevant.append({
                    "type": "engram",
                    "content": engram.content,
                    "importance": engram.importance_score,
                    "source": "local_memory",
                })
        
        # Buscar en el store global
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
        
        return relevant[:5]  # Limitar a 5 resultados
    
    def _create_obviousness_context(
        self,
        query: str,
        domain: IOVBADomain,
        session_id: str,
        user_id: str,
        relevant_capital: List[Dict[str, Any]],
    ) -> ObviousnessContext:
        """
        Crea el contexto de obviedad (SMART+R+T) para la consulta.
        """
        domain_brand = DOMAIN_BRANDING.get(domain, DOMAIN_BRANDING["custom"])
        
        builder = ObviousnessContextBuilder(
            session_id=session_id,
            user_id=user_id,
        )
        
        # S - Finalidad
        builder.with_objective(
            objective=query,
            success_criteria=["Respuesta precisa y útil", "Información verificada"],
            deliverables=["Respuesta estructurada", "Fuentes si aplica"],
        )
        
        # A - Alcance
        builder.with_boundaries(
            allow=["web_search", "knowledge_base", "capital_cognitive"],
            deny=["personal_data", "restricted_files"],
            sandbox=True,
        )
        
        # R - Relevancia
        builder.with_relevance(
            impact="medium",
            ccv=5,
            knowledge_nodes=[domain],
        )
        
        # T - Tiempo
        builder.with_time(
            priority="normal",
            timeout=60,
        )
        
        # Dominio
        builder.with_domain(domain)
        
        return builder.build()
    
    async def _generate_response_with_capital(
        self,
        query: str,
        domain: IOVBADomain,
        roles: List[IOVBARole],
        context: Optional[Dict[str, Any]],
        relevant_capital: List[Dict[str, Any]],
        obviousness_context: ObviousnessContext,
    ) -> str:
        """
        Genera respuesta usando LLM con contexto de capital cognitivo.
        
        Integra:
        - Capital cognitivo relevante
        - Contexto de obviedad (SMART+R+T)
        - System prompt del dominio
        """
        if not self.llm_provider:
            return self._generate_fallback_response(query, domain, roles)
        
        # Construir system prompt con obviedad
        base_system_prompt = self.get_system_prompt(domain, roles[0] if roles else None)
        obviousness_prompt = obviousness_context.to_system_prompt()
        
        # Agregar capital cognitivo si existe
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
        domain: IOVBADomain,
        confidence: float,
        session_id: str,
        user_id: str,
    ) -> None:
        """
        Almacena la interacción como capital cognitivo destilado.
        
        Diferencia entre:
        - Información histórica: Registro bruto de la interacción
        - Capital cognitivo: Conocimiento destilado, útil y ontológico
        """
        from uuid import UUID, uuid4
        
        try:
            # Crear capital cognitivo destilado
            capital = StoredCapital(
                agent_id=uuid4(),  # ID del agente NEXUS
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


# ============================================
# DEPENDENCY INJECTION FACTORY
# Replaces singleton pattern for better testability and multi-tenancy
# ============================================

def get_nexus(api_key: Optional[str] = None) -> NEXUSSuperAgent:
    """
    Factory function for NEXUS instances.
    
    DEPRECATED: This function is kept for backward compatibility.
    For new code, use FastAPI dependency injection with get_nexus_service().
    
    Args:
        api_key: Optional OpenRouter API key
        
    Returns:
        A new NEXUSSuperAgent instance (or cached singleton for backward compat)
    """
    global _nexus_instance
    
    if _nexus_instance is None:
        config = NEXUSConfig()
        if api_key:
            config.openrouter_api_key = api_key
        _nexus_instance = NEXUSSuperAgent(config=config)
    
    return _nexus_instance


def create_nexus(
    openrouter_api_key: Optional[str] = None,
    config: Optional[NEXUSConfig] = None,
) -> NEXUSSuperAgent:
    """
    Factory function to create a new NEXUS instance.
    
    Use this for creating fresh instances instead of the singleton pattern.
    Ideal for multi-tenant scenarios and testing.
    
    Args:
        openrouter_api_key: Optional API key for OpenRouter
        config: Optional NEXUSConfig instance
        
    Returns:
        A new NEXUSSuperAgent instance
        
    Example:
        ```python
        nexus = create_nexus(openrouter_api_key="sk-...")
        response = await nexus.process_query("Hello")
        ```
    """
    if config is None:
        config = NEXUSConfig()
    
    if openrouter_api_key:
        config.openrouter_api_key = openrouter_api_key
    
    return NEXUSSuperAgent(config=config)


def reset_nexus() -> None:
    """
    Reset the NEXUS singleton instance.
    
    This is primarily useful for testing to ensure clean state.
    """
    global _nexus_instance
    _nexus_instance = None


# FastAPI Dependency Injection Provider
async def get_nexus_service(
    openrouter_api_key: Optional[str] = None,
    settings: Optional[Any] = None,
) -> NEXUSSuperAgent:
    """
    FastAPI dependency injection provider for NEXUS.
    
    This is the recommended way to get a NEXUS instance in FastAPI routes.
    It creates a new instance per-request, avoiding singleton issues.
    
    Usage in FastAPI:
        ```python
        from fastapi import Depends
        
        @app.post("/api/query")
        async def query_endpoint(
            query: str,
            nexus: NEXUSSuperAgent = Depends(get_nexus_service)
        ):
            response = await nexus.process_query(query)
            return response.to_dict()
        ```
    
    Args:
        openrouter_api_key: Optional API key (can be injected from settings)
        settings: Optional settings object with openrouter_api_key attribute
        
    Returns:
        A NEXUSSuperAgent instance
    """
    # Try to get API key from settings if not provided
    if openrouter_api_key is None and settings is not None:
        openrouter_api_key = getattr(settings, 'OPENROUTER_API_KEY', None)
    
    return create_nexus(openrouter_api_key=openrouter_api_key)


class NEXUSProvider:
    """
    Provider class for managing NEXUS instances with lifecycle management.
    
    Useful for applications that need:
    - Multiple NEXUS instances (multi-tenant)
    - Lifecycle management (startup/shutdown)
    - Configuration caching
    
    Example:
        ```python
        provider = NEXUSProvider(default_api_key="sk-...")
        
        # Get instance for specific tenant
        nexus = provider.get_instance("tenant_123", api_key="tenant_specific_key")
        
        # Cleanup on shutdown
        await provider.shutdown()
        ```
    """
    
    def __init__(
        self,
        default_api_key: Optional[str] = None,
        default_config: Optional[NEXUSConfig] = None,
    ):
        self._default_api_key = default_api_key
        self._default_config = default_config
        self._instances: Dict[str, NEXUSSuperAgent] = {}
    
    def get_instance(
        self,
        instance_id: str = "default",
        api_key: Optional[str] = None,
        config: Optional[NEXUSConfig] = None,
    ) -> NEXUSSuperAgent:
        """
        Get or create a NEXUS instance by ID.
        
        Args:
            instance_id: Unique identifier for the instance
            api_key: Optional API key (overrides default)
            config: Optional config (overrides default)
            
        Returns:
            NEXUSSuperAgent instance
        """
        if instance_id not in self._instances:
            effective_config = config or self._default_config or NEXUSConfig()
            effective_api_key = api_key or self._default_api_key
            
            if effective_api_key:
                effective_config.openrouter_api_key = effective_api_key
            
            self._instances[instance_id] = NEXUSSuperAgent(config=effective_config)
        
        return self._instances[instance_id]
    
    def remove_instance(self, instance_id: str) -> bool:
        """Remove an instance by ID"""
        if instance_id in self._instances:
            del self._instances[instance_id]
            return True
        return False
    
    async def shutdown(self) -> None:
        """Cleanup all instances"""
        self._instances.clear()
    
    def list_instances(self) -> List[str]:
        """List all instance IDs"""
        return list(self._instances.keys())


# Singleton instance for backward compatibility
_nexus_instance: Optional[NEXUSSuperAgent] = None
