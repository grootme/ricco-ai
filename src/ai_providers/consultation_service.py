"""
AI Consultation Service
Service for AI-powered consultations and conversations

Este módulo implementa el servicio de consultas de IA con integración
de sanitización de datos sensibles para proteger la privacidad del usuario.
"""

import json
import time
from typing import Optional, Dict, Any, List, AsyncIterator
from datetime import datetime, timedelta
import logging
from uuid import UUID, uuid4

from .models import (
    ConsultationSession,
    ConsultationMessage,
    AIRequest,
    AIResponse,
    AIProviderType,
)
from .base import AIProvider, AIProviderFactory, AIProviderConfig, AIGenerationOptions
from .cache_manager import AICacheManager
from .subscription_limits import SubscriptionLimitsService, SubscriptionTier

# Context Bundle imports
import sys
from pathlib import Path
# Add context_bundles to path
CONTEXT_BUNDLES_PATH = Path(__file__).parent.parent / "context_bundles"
if CONTEXT_BUNDLES_PATH.exists():
    sys.path.insert(0, str(CONTEXT_BUNDLES_PATH.parent))

try:
    from context_bundles.context_prompt_builder import (
        ContextPromptBuilder,
        ContextSelection,
        ContextPromptConfig,
        AIModelFormat,
        get_context_prompt_builder
    )
    from context_bundles.context_cache import (
        ContextCache,
        get_context_cache
    )
    CONTEXT_BUNDLE_AVAILABLE = True
except ImportError as e:
    CONTEXT_BUNDLE_AVAILABLE = False

# Sanitization integration
SANITIZATION_PATH = Path(__file__).parent.parent / "sanitization"
if SANITIZATION_PATH.exists():
    sys.path.insert(0, str(SANITIZATION_PATH.parent))

try:
    from sanitization import (
        get_sanitizer,
        get_audit_logger,
        SensitiveDataSanitizer,
        SanitizationAuditLogger,
        SanitizationLevel,
    )
    SANITIZATION_AVAILABLE = True
except ImportError as e:
    SANITIZATION_AVAILABLE = False

logger = logging.getLogger(__name__)


# System prompts for different consultation topics
TOPIC_SYSTEM_PROMPTS = {
    "general": """You are a helpful AI assistant for the RICCO platform. 
You help users with business discovery, product recommendations, and general questions.
Be concise, helpful, and friendly. Provide specific recommendations when possible.""",
    
    "business": """You are a business discovery assistant for the RICCO platform.
You help users find local businesses, compare options, and make informed decisions.
Provide specific business recommendations with details like ratings, distance, and why they're relevant.""",
    
    "product": """You are a product recommendation assistant for the RICCO platform.
You help users discover products, compare options, and find the best deals.
Provide specific product recommendations with prices, features, and purchase information.""",
    
    "food": """You are a food and restaurant assistant for the RICCO platform.
You help users find restaurants, discover cuisines, and make reservations.
Provide specific restaurant recommendations with cuisine types, ratings, and menu highlights.""",
    
    "travel": """You are a travel and booking assistant for the RICCO platform.
You help users find accommodations, plan trips, and discover destinations.
Provide specific recommendations with pricing, availability, and booking information.""",
    
    "health": """You are a health and wellness assistant for the RICCO platform.
You help users find healthcare providers, schedule appointments, and access medical information.
Important: Do not provide medical advice. Always recommend consulting a healthcare professional.""",
    
    "finance": """You are a financial assistant for the RICCO platform.
You help users with budgeting, finding financial services, and understanding financial products.
Important: Do not provide specific financial advice. Recommend consulting a financial professional.""",
}


class ConsultationService:
    """
    AI consultation service
    
    Features:
    - Conversational AI interface
    - Topic-based consultations
    - Context-aware responses
    - Usage tracking per subscription
    - Streaming responses
    - Sensitive data sanitization for privacy protection
    """
    
    def __init__(
        self,
        provider: Optional[AIProvider] = None,
        cache_manager: Optional[AICacheManager] = None,
        limits_service: Optional[SubscriptionLimitsService] = None,
        redis_client=None,
        database_client=None,
        enable_sanitization: bool = True,
    ):
        self.provider = provider
        self.cache = cache_manager or AICacheManager()
        self.limits_service = limits_service or SubscriptionLimitsService()
        self.redis = redis_client
        self.db = database_client
        self._enable_sanitization = enable_sanitization and SANITIZATION_AVAILABLE
        
        # Inicializar sanitizador
        self._sanitizer: Optional[SensitiveDataSanitizer] = None
        self._audit_logger: Optional[SanitizationAuditLogger] = None
        
        if SANITIZATION_AVAILABLE and enable_sanitization:
            try:
                self._sanitizer = get_sanitizer()
                self._audit_logger = get_audit_logger()
                logger.info("Sanitization enabled for consultation service")
            except Exception as e:
                logger.warning(f"Failed to initialize sanitizer: {e}")
                self._enable_sanitization = False
    
    def _sanitize_prompt(self, prompt: str, user_id: str = None, session_id: str = None) -> str:
        """
        Sanitiza un prompt del usuario antes de enviarlo al modelo de IA.
        
        Args:
            prompt: Texto del prompt a sanitizar
            user_id: ID del usuario para auditoría
            session_id: ID de la sesión para auditoría
            
        Returns:
            Prompt sanitizado
        """
        if not self._enable_sanitization or not self._sanitizer:
            return prompt
        
        try:
            result = self._sanitizer.sanitize_text(prompt)
            
            if result.has_sensitive_data() and self._audit_logger:
                # Registrar detección de datos sensibles
                self._audit_logger.log_sanitization(
                    user_id=user_id,
                    session_id=session_id,
                    operation_type="sanitize",
                    data_types_detected=[dt.value for dt in result.detected_types],
                    redaction_count=result.redacted_count,
                    destination="ai_model",
                    processing_time_ms=result.processing_time_ms,
                )
                
                logger.info(
                    "Sanitized sensitive data in user prompt",
                    user_id=user_id,
                    data_types=[dt.value for dt in result.detected_types],
                    redaction_count=result.redaction_count,
                )
            
            return result.sanitized
        
        except Exception as e:
            logger.error(f"Error sanitizing prompt: {e}")
            return prompt
    
    async def _get_provider(self, tier: SubscriptionTier) -> AIProvider:
        """Get appropriate AI provider for tier"""
        if self.provider:
            return self.provider
        
        limits = self.limits_service.get_limits(tier)
        default_model = limits.default_model
        
        if "claude" in default_model:
            provider_type = AIProviderType.ANTHROPIC
        elif "gpt" in default_model:
            provider_type = AIProviderType.OPENAI
        else:
            provider_type = AIProviderType.LOCAL
        
        config = AIProviderConfig(
            provider_type=provider_type,
            model=default_model,
        )
        
        return AIProviderFactory.create(config)
    
    async def start_consultation(
        self,
        user_id: str,
        topic: str,
        context: Optional[Dict[str, Any]] = None,
        subscription_id: Optional[UUID] = None,
        tier: SubscriptionTier = SubscriptionTier.FREE,
        context_bundle_id: Optional[str] = None,
        context_selection: Optional[Dict[str, bool]] = None
    ) -> ConsultationSession:
        """
        Start a new consultation session
        
        Args:
            user_id: User ID
            topic: Consultation topic (general, business, product, etc.)
            context: Additional context for the consultation
            subscription_id: User's subscription ID
            tier: User's subscription tier
            context_bundle_id: ID del context bundle a usar (opcional)
            context_selection: Selección de contextos activos (opcional)
            
        Returns:
            New ConsultationSession
        """
        # Check quota
        quota = await self.limits_service.check_quota(user_id, tier)
        if not quota["can_use"]:
            raise ValueError("Daily consultation limit reached. Please upgrade your plan.")
        
        # Create session
        session = ConsultationSession(
            user_id=user_id,
            subscription_id=subscription_id,
            topic=topic,
            context=context,
            provider=AIProviderType.OPENAI,  # Will be updated when first message is sent
        )
        
        # Get system prompt for topic
        system_prompt = TOPIC_SYSTEM_PROMPTS.get(topic, TOPIC_SYSTEM_PROMPTS["general"])
        
        # Cargar context bundle si está disponible
        context_bundle_data = None
        if CONTEXT_BUNDLE_AVAILABLE and context_bundle_id:
            context_bundle_data = await self._load_context_bundle(
                context_bundle_id, 
                user_id,
                context_selection
            )
        
        # Add context to session
        if context:
            session.context = {
                **context,
                "system_prompt": system_prompt,
                "context_bundle_id": context_bundle_id,
            }
        else:
            session.context = {
                "system_prompt": system_prompt,
                "context_bundle_id": context_bundle_id,
            }
        
        # Si hay context bundle, enriquecer el contexto de la sesión
        if context_bundle_data:
            session.context["context_bundle"] = context_bundle_data
            session.context["system_prompt"] = await self._build_enhanced_system_prompt(
                system_prompt,
                context_bundle_data,
                topic
            )
        
        # Store session
        await self._store_session(session)
        
        logger.info(f"Started consultation session {session.id} for user {user_id}")
        
        return session
    
    async def send_message(
        self,
        session_id: UUID,
        message: str,
        tier: SubscriptionTier = SubscriptionTier.FREE
    ) -> AIResponse:
        """
        Send a message in a consultation session
        
        Args:
            session_id: Session ID
            message: User message
            tier: User's subscription tier
            
        Returns:
            AI response
        """
        # Get session
        session = await self._get_session(session_id)
        if not session:
            raise ValueError("Session not found")
        
        if session.status != "active":
            raise ValueError("Session is not active")
        
        # Check quota
        quota = await self.limits_service.check_quota(session.user_id, tier)
        if not quota["can_use"]:
            raise ValueError("Daily consultation limit reached")
        
        # Get provider
        provider = await self._get_provider(tier)
        session.provider = provider.provider_type
        session.model_used = provider.get_model_name()
        
        # Sanitize user message before processing
        sanitized_message = self._sanitize_prompt(
            message,
            user_id=session.user_id,
            session_id=str(session.id)
        )
        
        # Build conversation history
        history = []
        for msg in session.messages:
            history.append({
                "role": msg.role,
                "content": msg.content,
            })
        
        # Create user message (store sanitized version)
        user_message = ConsultationMessage(
            session_id=session.id,
            role="user",
            content=sanitized_message,
        )
        
        # Build context for AI
        context = {
            "conversation_history": history,
            "system_prompt": session.context.get("system_prompt", TOPIC_SYSTEM_PROMPTS["general"]),
        }
        
        # Add GenUI cache context if available
        if session.genui_cache_key:
            genui_context = await self.cache.get_genui_cache(session.genui_cache_key)
            if genui_context:
                context["genui_context"] = genui_context
        
        # Generate options
        limits = self.limits_service.get_limits(tier)
        options = AIGenerationOptions(
            max_tokens=min(2000, limits.max_tokens_per_request),
            temperature=0.7,
            system_prompt=context["system_prompt"],
            user_id=session.user_id,
        )
        
        # Generate response (use sanitized message)
        start_time = time.time()
        response = await provider.generate_response(
            sanitized_message,
            context=context,
            options=options
        )
        
        # Create assistant message
        assistant_message = ConsultationMessage(
            session_id=session.id,
            role="assistant",
            content=response.content,
            tokens_used=response.tokens_used,
            metadata={
                "model": response.model_used,
                "latency_ms": response.latency_ms,
            }
        )
        
        # Update session
        session.add_message(user_message)
        session.add_message(assistant_message)
        session.last_activity_at = datetime.utcnow()
        
        # Record usage
        await self.limits_service.record_usage(
            session.user_id,
            response.tokens_used,
            str(session.subscription_id) if session.subscription_id else None
        )
        
        # Store updated session
        await self._store_session(session)
        
        return response
    
    async def send_message_stream(
        self,
        session_id: UUID,
        message: str,
        tier: SubscriptionTier = SubscriptionTier.FREE
    ) -> AsyncIterator[str]:
        """
        Send a message and get streaming response
        
        Args:
            session_id: Session ID
            message: User message
            tier: User's subscription tier
            
        Yields:
            Chunks of the response
        """
        # Get session
        session = await self._get_session(session_id)
        if not session:
            raise ValueError("Session not found")
        
        if session.status != "active":
            raise ValueError("Session is not active")
        
        # Check if streaming is supported
        limits = self.limits_service.get_limits(tier)
        if not limits.supports_streaming:
            # Fall back to non-streaming
            response = await self.send_message(session_id, message, tier)
            yield response.content
            return
        
        # Check quota
        quota = await self.limits_service.check_quota(session.user_id, tier)
        if not quota["can_use"]:
            raise ValueError("Daily consultation limit reached")
        
        # Get provider
        provider = await self._get_provider(tier)
        
        # Sanitize user message
        sanitized_message = self._sanitize_prompt(
            message,
            user_id=session.user_id,
            session_id=str(session.id)
        )
        
        # Build conversation history
        history = []
        for msg in session.messages:
            history.append({
                "role": msg.role,
                "content": msg.content,
            })
        
        # Create user message (store sanitized version)
        user_message = ConsultationMessage(
            session_id=session.id,
            role="user",
            content=sanitized_message,
        )
        session.add_message(user_message)
        
        # Build context
        context = {
            "conversation_history": history,
            "system_prompt": session.context.get("system_prompt", TOPIC_SYSTEM_PROMPTS["general"]),
        }
        
        # Stream options
        options = AIGenerationOptions(
            max_tokens=min(2000, limits.max_tokens_per_request),
            temperature=0.7,
            system_prompt=context["system_prompt"],
            stream=True,
        )
        
        # Collect full response
        full_response = ""
        
        try:
            async for chunk in provider.generate_stream(sanitized_message, context=context, options=options):
                full_response += chunk
                yield chunk
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"\n[Error: {str(e)}]"
            return
        
        # Create assistant message
        assistant_message = ConsultationMessage(
            session_id=session.id,
            role="assistant",
            content=full_response,
            tokens_used=0,  # Unknown for streaming
            metadata={
                "model": provider.get_model_name(),
                "streaming": True,
            }
        )
        
        session.add_message(assistant_message)
        session.last_activity_at = datetime.utcnow()
        
        # Record usage (approximate)
        await self.limits_service.record_usage(
            session.user_id,
            len(full_response.split()),  # Approximate tokens
            str(session.subscription_id) if session.subscription_id else None
        )
        
        # Store session
        await self._store_session(session)
    
    async def end_consultation(
        self,
        session_id: UUID
    ) -> ConsultationSession:
        """
        End a consultation session
        
        Args:
            session_id: Session ID
            
        Returns:
            Final session state
        """
        session = await self._get_session(session_id)
        if not session:
            raise ValueError("Session not found")
        
        session.status = "ended"
        session.ended_at = datetime.utcnow()
        
        # Store final session state
        await self._store_session(session)
        
        logger.info(f"Ended consultation session {session_id}")
        
        return session
    
    async def get_consultation_history(
        self,
        session_id: UUID
    ) -> Optional[ConsultationSession]:
        """
        Get consultation history
        
        Args:
            session_id: Session ID
            
        Returns:
            ConsultationSession with all messages
        """
        return await self._get_session(session_id)
    
    async def get_user_sessions(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[ConsultationSession]:
        """
        Get all sessions for a user
        
        Args:
            user_id: User ID
            limit: Maximum number of sessions to return
            
        Returns:
            List of ConsultationSessions
        """
        if self.redis:
            try:
                sessions_key = f"user_sessions:{user_id}"
                session_ids = await self.redis.lrange(sessions_key, 0, limit - 1)
                
                sessions = []
                for sid in session_ids:
                    session = await self._get_session(UUID(sid.decode() if isinstance(sid, bytes) else sid))
                    if session:
                        sessions.append(session)
                
                return sessions
            except Exception as e:
                logger.error(f"Failed to get user sessions: {e}")
        
        return []
    
    async def cleanup_expired_sessions(
        self,
        max_age_hours: int = 24
    ) -> int:
        """
        Cleanup expired sessions
        
        Args:
            max_age_hours: Maximum session age in hours
            
        Returns:
            Number of sessions cleaned up
        """
        # In production, implement proper cleanup
        return 0
    
    # Storage methods
    
    async def _store_session(self, session: ConsultationSession) -> None:
        """Store session in Redis/database"""
        if self.redis:
            try:
                session_key = f"consultation:{session.id}"
                await self.redis.setex(
                    session_key,
                    86400,  # 24 hours
                    json.dumps(session.model_dump(), default=str)
                )
                
                # Add to user's session list
                sessions_key = f"user_sessions:{session.user_id}"
                await self.redis.lpush(sessions_key, str(session.id))
                await self.redis.ltrim(sessions_key, 0, 49)  # Keep last 50 sessions
            except Exception as e:
                logger.error(f"Failed to store session: {e}")
    
    async def _get_session(self, session_id: UUID) -> Optional[ConsultationSession]:
        """Get session from Redis/database"""
        if self.redis:
            try:
                session_key = f"consultation:{session_id}"
                data = await self.redis.get(session_key)
                if data:
                    session_dict = json.loads(data)
                    return ConsultationSession(**session_dict)
            except Exception as e:
                logger.error(f"Failed to get session: {e}")
        
        return None
    
    # Context helpers
    
    async def set_session_context(
        self,
        session_id: UUID,
        context_key: str,
        context_value: Any
    ) -> None:
        """Set additional context for a session"""
        session = await self._get_session(session_id)
        if session:
            if not session.context:
                session.context = {}
            session.context[context_key] = context_value
            await self._store_session(session)
    
    async def set_genui_cache_key(
        self,
        session_id: UUID,
        cache_key: str
    ) -> None:
        """Set GenUI cache key for session"""
        session = await self._get_session(session_id)
        if session:
            session.genui_cache_key = cache_key
            await self._store_session(session)
    
    # Context Bundle integration methods
    
    async def _load_context_bundle(
        self,
        bundle_id: str,
        user_id: str,
        selection: Optional[Dict[str, bool]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Carga un context bundle desde caché o base de datos
        
        Args:
            bundle_id: ID del bundle a cargar
            user_id: ID del usuario
            selection: Selección de contextos activos
            
        Returns:
            Datos del context bundle o None si no existe
        """
        if not CONTEXT_BUNDLE_AVAILABLE:
            return None
        
        try:
            cache = get_context_cache()
            
            # Intentar obtener del caché
            cached_bundle = await cache.get_session_context(bundle_id)
            if cached_bundle:
                logger.info(f"Loaded cached context bundle: {bundle_id}")
                return cached_bundle
            
            # Si no está en caché, construir desde fuentes
            # En producción, esto cargaría desde la base de datos
            # Por ahora, devolver un bundle básico
            from datetime import datetime
            basic_bundle = {
                "session_id": bundle_id,
                "user_id": user_id,
                "created_at": datetime.utcnow().isoformat(),
                "personal": {
                    "user_id": user_id,
                    "language": "es",
                    "trust_score": 0,
                },
                "temporal": {
                    "time_of_day": self._get_time_of_day(),
                    "day_of_week": datetime.utcnow().strftime("%A").lower(),
                    "is_weekend": datetime.utcnow().weekday() >= 5,
                },
                "selection": selection or {
                    "include_personal": True,
                    "include_temporal": True,
                    "include_spatial": False,
                }
            }
            
            # Guardar en caché
            await cache.set_session_context(bundle_id, user_id, basic_bundle)
            
            return basic_bundle
            
        except Exception as e:
            logger.error(f"Error loading context bundle: {e}")
            return None
    
    def _get_time_of_day(self) -> str:
        """Obtiene el momento del día actual"""
        from datetime import datetime
        hour = datetime.utcnow().hour
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 21:
            return "evening"
        return "night"
    
    async def _build_enhanced_system_prompt(
        self,
        base_prompt: str,
        context_bundle: Dict[str, Any],
        topic: str
    ) -> str:
        """
        Construye un system prompt mejorado con el context bundle
        
        Args:
            base_prompt: System prompt base
            context_bundle: Datos del context bundle
            topic: Tópico de la consulta
            
        Returns:
            System prompt mejorado con contexto
        """
        if not CONTEXT_BUNDLE_AVAILABLE:
            return base_prompt
        
        try:
            builder = get_context_prompt_builder()
            
            selection = ContextSelection(
                **context_bundle.get("selection", {
                    "include_personal": True,
                    "include_temporal": True,
                })
            )
            
            config = ContextPromptConfig(
                model_format=AIModelFormat.OPENAI,
                concise_mode=True,
                language="es"
            )
            
            prompt_data = await builder.build_prompt(
                context_bundle=context_bundle,
                selection=selection,
                config=config
            )
            
            # Combinar base prompt con contexto
            context_section = "\n".join(prompt_data["context_sections"])
            
            enhanced_prompt = f"""{base_prompt}

---
{context_section}
---

Usa esta información de contexto para personalizar tus respuestas."""
            
            return enhanced_prompt
            
        except Exception as e:
            logger.error(f"Error building enhanced prompt: {e}")
            return base_prompt
    
    async def update_context_selection(
        self,
        session_id: UUID,
        new_selection: Dict[str, bool]
    ) -> Optional[ConsultationSession]:
        """
        Actualiza la selección de contextos durante una consulta
        
        Args:
            session_id: ID de la sesión
            new_selection: Nueva selección de contextos activos
            
        Returns:
            Sesión actualizada o None
        """
        session = await self._get_session(session_id)
        if not session:
            return None
        
        if "context_bundle" not in session.context:
            return session
        
        # Actualizar selección
        session.context["context_bundle"]["selection"] = new_selection
        
        # Reconstruir system prompt
        base_prompt = TOPIC_SYSTEM_PROMPTS.get(
            session.topic, 
            TOPIC_SYSTEM_PROMPTS["general"]
        )
        session.context["system_prompt"] = await self._build_enhanced_system_prompt(
            base_prompt,
            session.context["context_bundle"],
            session.topic
        )
        
        # Guardar sesión actualizada
        await self._store_session(session)
        
        return session
    
    async def get_recommended_contexts(
        self,
        query: str
    ) -> List[str]:
        """
        Obtiene contextos recomendados para una consulta
        
        Args:
            query: Consulta del usuario
            
        Returns:
            Lista de contextos recomendados
        """
        if not CONTEXT_BUNDLE_AVAILABLE:
            return ["personal", "temporal"]
        
        try:
            builder = get_context_prompt_builder()
            # Usar un bundle vacío ya que solo necesitamos la recomendación
            return await builder.get_recommended_contexts(query, {})
        except Exception as e:
            logger.error(f"Error getting context recommendations: {e}")
            return ["personal", "temporal"]
