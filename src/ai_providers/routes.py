"""
AI Services API Routes
FastAPI routes for AI-powered recommendations and consultations
"""

import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID, uuid4
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .models import (
    AIRequest,
    AIResponse,
    RecommendationContext,
    ConsultationSession,
    BusinessRecommendation,
    ProductRecommendation,
    PersonalizedFeed,
    AIQuotaInfo,
    AIProviderType,
)
from .recommendation_engine import RecommendationEngine
from .consultation_service import ConsultationService
from .subscription_limits import SubscriptionLimitsService, SubscriptionTier
from .cache_manager import AICacheManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Services"])


# Request/Response models

class RecommendRequest(BaseModel):
    """Request for recommendations"""
    user_id: str
    location: Optional[Dict[str, Any]] = None
    preferences: Optional[Dict[str, Any]] = None
    limit: int = Field(default=10, ge=1, le=50)
    type: str = "business"  # business, product, similar, feed


class ConsultStartRequest(BaseModel):
    """Request to start a consultation"""
    user_id: str
    topic: str = "general"
    context: Optional[Dict[str, Any]] = None
    subscription_id: Optional[UUID] = None
    # Context Bundle parameters
    context_bundle_id: Optional[str] = None
    context_selection: Optional[Dict[str, bool]] = None


class ConsultMessageRequest(BaseModel):
    """Request to send a message in consultation"""
    message: str
    stream: bool = False


class QuotaResponse(BaseModel):
    """Response for quota check"""
    user_id: str
    tier: str
    can_use: bool
    daily_remaining: int
    monthly_remaining: int
    daily_used: int
    monthly_used: int
    daily_limit: int
    monthly_limit: int
    reset_times: Dict[str, str]
    available_models: List[str]
    features: Dict[str, bool]


class RecommendationsResponse(BaseModel):
    """Response with recommendations"""
    businesses: List[Dict[str, Any]] = []
    products: List[Dict[str, Any]] = []
    feed: Optional[Dict[str, Any]] = None
    cached: bool = False


class ContextRecommendRequest(BaseModel):
    """Request for context recommendations"""
    query: str
    user_id: str
    available_contexts: Optional[List[str]] = None


class ContextRecommendResponse(BaseModel):
    """Response with recommended contexts"""
    recommended_contexts: List[str]
    reasoning: Dict[str, str]
    confidence: float


class ContextSelectionUpdateRequest(BaseModel):
    """Request to update context selection"""
    session_id: str
    selection: Dict[str, bool]


class ConsultationResponse(BaseModel):
    """Response for consultation"""
    session_id: str
    status: str
    response: Optional[str] = None
    messages: List[Dict[str, Any]] = []
    tokens_used: int = 0
    context_bundle_id: Optional[str] = None
    active_contexts: List[str] = []


# Dependencies

def get_subscription_tier(user_id: str = Query(...)) -> SubscriptionTier:
    """Get user's subscription tier (mock for now)"""
    # In production, fetch from database
    return SubscriptionTier.FREE


def get_limits_service() -> SubscriptionLimitsService:
    """Get subscription limits service"""
    return SubscriptionLimitsService()


def get_recommendation_engine() -> RecommendationEngine:
    """Get recommendation engine"""
    return RecommendationEngine()


def get_consultation_service() -> ConsultationService:
    """Get consultation service"""
    return ConsultationService()


# Routes

@router.post("/recommend", response_model=RecommendationsResponse)
async def get_recommendations(
    request: RecommendRequest,
    tier: SubscriptionTier = Depends(get_subscription_tier),
    engine: RecommendationEngine = Depends(get_recommendation_engine),
    limits_service: SubscriptionLimitsService = Depends(get_limits_service)
) -> RecommendationsResponse:
    """
    Get AI-powered recommendations
    
    Types:
    - business: Business recommendations based on location/preferences
    - product: Product recommendations
    - similar: Similar businesses
    - feed: Personalized feed
    """
    # Check quota
    quota = await limits_service.check_quota(request.user_id, tier)
    if not quota["can_use"]:
        raise HTTPException(
            status_code=429,
            detail="Daily recommendation limit reached. Please upgrade your plan."
        )
    
    response = RecommendationsResponse()
    
    try:
        if request.type == "business":
            businesses = await engine.get_business_recommendations(
                user_id=request.user_id,
                location=request.location,
                preferences=request.preferences,
                limit=request.limit,
                tier=tier
            )
            response.businesses = [b.model_dump() for b in businesses]
            
        elif request.type == "product":
            products = await engine.get_product_recommendations(
                user_id=request.user_id,
                limit=request.limit,
                tier=tier
            )
            response.products = [p.model_dump() for p in products]
            
        elif request.type == "feed":
            feed = await engine.get_personalized_feed(
                user_id=request.user_id,
                tier=tier
            )
            response.feed = feed.model_dump()
            response.businesses = [b.model_dump() for b in feed.businesses]
            response.products = [p.model_dump() for p in feed.products]
            
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown recommendation type: {request.type}"
            )
        
        # Record usage
        await limits_service.record_usage(request.user_id, 1)
        
    except Exception as e:
        logger.error(f"Recommendation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    return response


@router.post("/recommend/similar/{business_id}", response_model=RecommendationsResponse)
async def get_similar_businesses(
    business_id: str,
    user_id: str = Query(...),
    limit: int = Query(default=5, ge=1, le=20),
    tier: SubscriptionTier = Depends(get_subscription_tier),
    engine: RecommendationEngine = Depends(get_recommendation_engine),
    limits_service: SubscriptionLimitsService = Depends(get_limits_service)
) -> RecommendationsResponse:
    """Get businesses similar to a given business"""
    # Check quota
    quota = await limits_service.check_quota(user_id, tier)
    if not quota["can_use"]:
        raise HTTPException(
            status_code=429,
            detail="Daily recommendation limit reached."
        )
    
    try:
        businesses = await engine.get_similar_businesses(
            business_id=business_id,
            limit=limit,
            tier=tier
        )
        
        await limits_service.record_usage(user_id, 1)
        
        return RecommendationsResponse(
            businesses=[b.model_dump() for b in businesses]
        )
        
    except Exception as e:
        logger.error(f"Similar business error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/consult", response_model=ConsultationResponse)
async def start_consultation(
    request: ConsultStartRequest,
    tier: SubscriptionTier = Depends(get_subscription_tier),
    service: ConsultationService = Depends(get_consultation_service),
    limits_service: SubscriptionLimitsService = Depends(get_limits_service)
) -> ConsultationResponse:
    """
    Start a new AI consultation session
    
    Incluye soporte para context bundles:
    - context_bundle_id: ID del bundle de contexto a usar
    - context_selection: Diccionario con los contextos activos
    """
    # Check quota
    quota = await limits_service.check_quota(request.user_id, tier)
    if not quota["can_use"]:
        raise HTTPException(
            status_code=429,
            detail="Daily consultation limit reached. Please upgrade your plan."
        )
    
    try:
        session = await service.start_consultation(
            user_id=request.user_id,
            topic=request.topic,
            context=request.context,
            subscription_id=request.subscription_id,
            tier=tier,
            context_bundle_id=request.context_bundle_id,
            context_selection=request.context_selection
        )
        
        # Obtener contextos activos
        active_contexts = []
        if session.context and "context_bundle" in session.context:
            selection = session.context["context_bundle"].get("selection", {})
            active_contexts = [k.replace("include_", "") for k, v in selection.items() if v]
        
        return ConsultationResponse(
            session_id=str(session.id),
            status=session.status,
            messages=[],
            tokens_used=0,
            context_bundle_id=request.context_bundle_id,
            active_contexts=active_contexts
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Consultation start error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/consult/{session_id}", response_model=ConsultationResponse)
async def send_consultation_message(
    session_id: UUID,
    request: ConsultMessageRequest,
    tier: SubscriptionTier = Depends(get_subscription_tier),
    service: ConsultationService = Depends(get_consultation_service)
) -> ConsultationResponse:
    """Send a message in a consultation session"""
    try:
        if request.stream:
            # Return streaming response
            return StreamingResponse(
                service.send_message_stream(session_id, request.message, tier),
                media_type="text/event-stream"
            )
        
        response = await service.send_message(session_id, request.message, tier)
        
        # Get updated session
        session = await service.get_consultation_history(session_id)
        
        return ConsultationResponse(
            session_id=str(session_id),
            status=session.status if session else "unknown",
            response=response.content,
            messages=[m.model_dump() for m in session.messages] if session else [],
            tokens_used=response.tokens_used
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Consultation message error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/consult/{session_id}", response_model=ConsultationResponse)
async def get_consultation_history(
    session_id: UUID,
    service: ConsultationService = Depends(get_consultation_service)
) -> ConsultationResponse:
    """Get consultation session history"""
    session = await service.get_consultation_history(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return ConsultationResponse(
        session_id=str(session_id),
        status=session.status,
        messages=[m.model_dump() for m in session.messages],
        tokens_used=session.total_tokens_used
    )


@router.delete("/consult/{session_id}", response_model=ConsultationResponse)
async def end_consultation(
    session_id: UUID,
    service: ConsultationService = Depends(get_consultation_service)
) -> ConsultationResponse:
    """End a consultation session"""
    try:
        session = await service.end_consultation(session_id)
        
        return ConsultationResponse(
            session_id=str(session_id),
            status=session.status,
            messages=[m.model_dump() for m in session.messages],
            tokens_used=session.total_tokens_used
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/quota", response_model=QuotaResponse)
async def get_quota(
    user_id: str = Query(...),
    tier: SubscriptionTier = Depends(get_subscription_tier),
    limits_service: SubscriptionLimitsService = Depends(get_limits_service)
) -> QuotaResponse:
    """Get remaining AI usage quota"""
    quota = await limits_service.check_quota(user_id, tier)
    limits = limits_service.get_limits(tier)
    available_models = limits_service.get_available_models(tier)
    
    return QuotaResponse(
        user_id=user_id,
        tier=tier.value,
        can_use=quota["can_use"],
        daily_remaining=quota["daily_remaining"],
        monthly_remaining=quota["monthly_remaining"],
        daily_used=quota["daily_used"],
        monthly_used=quota["monthly_used"],
        daily_limit=quota["daily_limit"],
        monthly_limit=quota["monthly_limit"],
        reset_times=quota["reset_times"],
        available_models=available_models,
        features={
            "streaming": limits.supports_streaming,
            "vision": limits.supports_vision,
            "context": limits.supports_context,
            "history": limits.supports_history,
            "priority": limits.priority_processing,
        }
    )


@router.get("/usage", response_model=Dict[str, Any])
async def get_usage_stats(
    user_id: str = Query(...),
    tier: SubscriptionTier = Depends(get_subscription_tier),
    limits_service: SubscriptionLimitsService = Depends(get_limits_service)
) -> Dict[str, Any]:
    """Get detailed usage statistics"""
    return await limits_service.get_usage_stats(user_id, tier)


@router.get("/models", response_model=List[Dict[str, Any]])
async def get_available_models(
    tier: SubscriptionTier = Depends(get_subscription_tier),
    limits_service: SubscriptionLimitsService = Depends(get_limits_service)
) -> List[Dict[str, Any]]:
    """Get available AI models for user's tier"""
    limits = limits_service.get_limits(tier)
    models = limits_service.get_available_models(tier)
    
    model_info = []
    for model in models:
        info = {
            "id": model,
            "name": model,
            "provider": "unknown",
            "available": True,
            "default": model == limits.default_model,
        }
        
        if "claude" in model:
            info["provider"] = "anthropic"
            info["supports_vision"] = True
        elif "gpt" in model:
            info["provider"] = "openai"
            info["supports_vision"] = "gpt-4" in model
        else:
            info["provider"] = "local"
            info["supports_vision"] = False
        
        model_info.append(info)
    
    return model_info


@router.post("/cache/clear")
async def clear_cache(
    pattern: str = Query(default="ai_cache:*"),
    cache_manager: AICacheManager = Depends(lambda: AICacheManager())
) -> Dict[str, Any]:
    """Clear AI cache (admin only)"""
    # In production, add admin authentication
    count = await cache_manager.clear_all(pattern)
    return {"cleared": count}


@router.get("/cache/stats")
async def get_cache_stats(
    cache_manager: AICacheManager = Depends(lambda: AICacheManager())
) -> Dict[str, Any]:
    """Get cache statistics"""
    return await cache_manager.get_stats()


# Context Bundle endpoints

@router.post("/context/recommend", response_model=ContextRecommendResponse)
async def get_context_recommendations(
    request: ContextRecommendRequest,
    service: ConsultationService = Depends(get_consultation_service)
) -> ContextRecommendResponse:
    """
    Get AI-recommended contexts for a query
    
    Analiza la consulta del usuario y recomienda qué contextos
    activar para obtener mejores respuestas.
    
    Contextos disponibles:
    - personal: Información del usuario (nombre, preferencias)
    - temporal: Hora, día, temporada
    - spatial: Ubicación, lugar, clima
    - device: Tipo de dispositivo, red
    - solution: Solución RICCO activa
    - horizontal: Puntos, suscripción
    - skills: Habilidades de IA disponibles
    """
    try:
        recommended = await service.get_recommended_contexts(request.query)
        
        # Generar razonamiento para cada recomendación
        reasoning = {}
        query_lower = request.query.lower()
        
        for ctx in recommended:
            if ctx == "spatial":
                reasoning[ctx] = "La consulta menciona ubicación o cercanía"
            elif ctx == "temporal":
                reasoning[ctx] = "Contexto temporal siempre relevante"
            elif ctx == "personal":
                reasoning[ctx] = "Personalización básica"
            elif ctx == "solution":
                reasoning[ctx] = "La consulta involucra la solución activa"
            elif ctx == "horizontal":
                reasoning[ctx] = "La consulta involucra aspectos financieros"
            elif ctx == "skills":
                reasoning[ctx] = "La consulta pregunta por capacidades"
            else:
                reasoning[ctx] = "Contexto relevante"
        
        # Calcular confianza basada en matches
        confidence = min(1.0, len(recommended) / 5.0)
        
        return ContextRecommendResponse(
            recommended_contexts=recommended,
            reasoning=reasoning,
            confidence=confidence
        )
        
    except Exception as e:
        logger.error(f"Context recommendation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/consult/context", response_model=ConsultationResponse)
async def update_context_selection(
    request: ContextSelectionUpdateRequest,
    service: ConsultationService = Depends(get_consultation_service)
) -> ConsultationResponse:
    """
    Update context selection for active session
    
    Permite cambiar los contextos activos durante una consulta
    para adaptar las respuestas del AI.
    
    Selecciones disponibles:
    - include_personal: bool
    - include_temporal: bool
    - include_spatial: bool
    - include_device: bool
    - include_solution: bool
    - include_horizontal: bool
    - include_vertical: bool
    - include_skills: bool
    """
    try:
        from uuid import UUID
        session = await service.update_context_selection(
            UUID(request.session_id),
            request.selection
        )
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Obtener contextos activos
        active_contexts = []
        if session.context and "context_bundle" in session.context:
            selection = session.context["context_bundle"].get("selection", {})
            active_contexts = [k.replace("include_", "") for k, v in selection.items() if v]
        
        return ConsultationResponse(
            session_id=str(session.id),
            status=session.status,
            messages=[m.model_dump() for m in session.messages],
            tokens_used=session.total_tokens_used,
            context_bundle_id=session.context.get("context_bundle_id"),
            active_contexts=active_contexts
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Context update error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/context/types")
async def get_context_types() -> Dict[str, Any]:
    """
    Get available context types
    
    Retorna información sobre todos los tipos de contexto
    disponibles en el sistema.
    """
    return {
        "contexts": [
            {
                "id": "personal",
                "name": "Personal",
                "description": "Información personal del usuario",
                "data_fields": ["nombre", "idioma", "timezone", "trust_score"],
                "always_available": True,
            },
            {
                "id": "temporal",
                "name": "Temporal",
                "description": "Contexto de tiempo actual",
                "data_fields": ["hora", "día", "temporada", "horario laboral"],
                "always_available": True,
            },
            {
                "id": "spatial",
                "name": "Espacial",
                "description": "Ubicación y entorno",
                "data_fields": ["ubicación", "ciudad", "clima", "lugares cercanos"],
                "requires_permission": "location",
            },
            {
                "id": "device",
                "name": "Dispositivo",
                "description": "Información del dispositivo",
                "data_fields": ["tipo", "plataforma", "red", "batería"],
                "always_available": True,
            },
            {
                "id": "solution",
                "name": "Solución",
                "description": "Contexto de la solución RICCO activa",
                "data_fields": ["solución", "rol", "carrito", "búsquedas"],
                "always_available": True,
            },
            {
                "id": "horizontal",
                "name": "Horizontal",
                "description": "Datos cross-solution",
                "data_fields": ["puntos RPT", "suscripción", "trust score"],
                "always_available": True,
            },
            {
                "id": "vertical",
                "name": "Vertical",
                "description": "Contexto específico de vertical",
                "data_fields": ["comercio", "salud", "logística", "finanzas"],
                "solution_dependent": True,
            },
            {
                "id": "skills",
                "name": "Skills",
                "description": "Habilidades de IA disponibles",
                "data_fields": ["skills activos", "más usados"],
                "always_available": True,
            },
        ]
    }


# Health check

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check for AI services"""
    return {
        "status": "healthy",
        "service": "ai_services",
        "timestamp": datetime.utcnow().isoformat(),
        "features": {
            "recommendations": True,
            "consultations": True,
            "streaming": True,
            "caching": True,
        }
    }
