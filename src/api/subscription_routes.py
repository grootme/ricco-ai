"""
GenUI/A2UI Subscription API Routes
Rutas API para gestión de suscripciones
Integrated from genui
"""

from fastapi import APIRouter, Depends, HTTPException, Header, Request
from typing import Optional, List
from uuid import UUID

from src.subscription.models import SubscriptionTier, UsageType, GenUISubscription, PLAN_LIMITS
from src.subscription.service import (
    GenUISubscriptionService,
    QuotaExceededError,
    RateLimitExceededError,
)

router = APIRouter(prefix="/genui", tags=["GenUI Subscription"])


def get_service(request: Request) -> GenUISubscriptionService:
    return request.app.state.genui_service


def get_user_id(x_ricco_id_token: str = Header(...)) -> str:
    """Extract user ID from RICCO ID token"""
    # Validate with RICCO ID service
    # This should decode JWT and return user_id
    # For now, return from header
    return x_ricco_id_token


# ============================================
# SUBSCRIPTION ENDPOINTS
# ============================================

@router.post("/subscriptions")
async def create_subscription(
    tier: SubscriptionTier = SubscriptionTier.FREE,
    organization_id: Optional[str] = None,
    billing_cycle: str = "monthly",
    user_id: str = Depends(get_user_id),
    service: GenUISubscriptionService = Depends(get_service),
):
    """Crear nueva suscripción a GenUI/A2UI"""
    subscription = await service.create_subscription(
        user_id=user_id,
        tier=tier,
        organization_id=organization_id,
        billing_cycle=billing_cycle,
    )
    return {"subscription": subscription.model_dump()}


@router.get("/subscriptions/me")
async def get_my_subscription(
    user_id: str = Depends(get_user_id),
    service: GenUISubscriptionService = Depends(get_service),
):
    """Obtener suscripción actual del usuario"""
    subscription = await service.get_user_subscription(user_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription found")
    
    quota = await service.check_quota(subscription.id)
    
    return {
        "subscription": subscription.model_dump(),
        "quota": quota,
    }


@router.post("/subscriptions/{subscription_id}/upgrade")
async def upgrade_subscription(
    subscription_id: UUID,
    new_tier: SubscriptionTier,
    prorate: bool = True,
    user_id: str = Depends(get_user_id),
    service: GenUISubscriptionService = Depends(get_service),
):
    """Actualizar suscripción a un plan superior"""
    subscription = await service.get_subscription(subscription_id)
    
    if not subscription or subscription.user_id != user_id:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    updated = await service.upgrade_subscription(subscription_id, new_tier, prorate)
    return {"subscription": updated.model_dump()}


# ============================================
# QUOTA ENDPOINTS
# ============================================

@router.get("/subscriptions/{subscription_id}/quota")
async def get_quota(
    subscription_id: UUID,
    user_id: str = Depends(get_user_id),
    service: GenUISubscriptionService = Depends(get_service),
):
    """Obtener información de cuota"""
    subscription = await service.get_subscription(subscription_id)
    
    if not subscription or subscription.user_id != user_id:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    quota = await service.check_quota(subscription_id)
    return quota


# ============================================
# USAGE ENDPOINTS
# ============================================

@router.post("/usage/record")
async def record_usage(
    usage_type: UsageType,
    mini_program_id: Optional[str] = None,
    surface_id: Optional[str] = None,
    solution: Optional[str] = None,
    tokens_used: int = 0,
    components_generated: int = 0,
    context_types_used: List[str] = [],
    user_id: str = Depends(get_user_id),
    service: GenUISubscriptionService = Depends(get_service),
):
    """Registrar uso de GenUI/A2UI (llamado por el backend)"""
    subscription = await service.get_user_subscription(user_id)
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription")
    
    try:
        record = await service.record_usage(
            subscription_id=subscription.id,
            usage_type=usage_type,
            user_id=user_id,
            tokens_used=tokens_used,
            mini_program_id=mini_program_id,
            surface_id=surface_id,
            solution=solution,
            context_types_used=context_types_used,
            components_generated=components_generated,
        )
        return {"record": record.model_dump()}
    except QuotaExceededError:
        raise HTTPException(status_code=429, detail="Quota exceeded")


@router.get("/subscriptions/{subscription_id}/usage")
async def get_usage_stats(
    subscription_id: UUID,
    user_id: str = Depends(get_user_id),
    service: GenUISubscriptionService = Depends(get_service),
):
    """Obtener estadísticas de uso"""
    subscription = await service.get_subscription(subscription_id)
    
    if not subscription or subscription.user_id != user_id:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    stats = await service.get_usage_stats(subscription_id)
    return stats


# ============================================
# RATE LIMIT ENDPOINT
# ============================================

@router.get("/subscriptions/{subscription_id}/rate-limit")
async def check_rate_limit(
    subscription_id: UUID,
    user_id: str = Depends(get_user_id),
    service: GenUISubscriptionService = Depends(get_service),
):
    """Verificar rate limit"""
    subscription = await service.get_subscription(subscription_id)
    
    if not subscription or subscription.user_id != user_id:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    result = await service.check_rate_limit(subscription_id)
    return result


# ============================================
# API KEY ENDPOINTS
# ============================================

@router.post("/api-keys")
async def create_api_key(
    name: str,
    scopes: List[str] = ["read", "write"],
    user_id: str = Depends(get_user_id),
    service: GenUISubscriptionService = Depends(get_service),
):
    """Crear nueva API key"""
    subscription = await service.get_user_subscription(user_id)
    
    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription")
    
    api_key, raw_key = await service.create_api_key(
        subscription_id=subscription.id,
        user_id=user_id,
        name=name,
        scopes=scopes,
    )
    
    return {
        "api_key": api_key.model_dump(),
        "key": raw_key,  # Only shown once!
        "warning": "Store this key securely. It will not be shown again.",
    }


@router.get("/api-keys")
async def list_api_keys(
    user_id: str = Depends(get_user_id),
    service: GenUISubscriptionService = Depends(get_service),
):
    """Listar API keys del usuario"""
    # Implementation would query DB for user's API keys
    pass


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: UUID,
    user_id: str = Depends(get_user_id),
    service: GenUISubscriptionService = Depends(get_service),
):
    """Revocar API key"""
    # Implementation would deactivate the key
    pass


# ============================================
# INVOICE ENDPOINTS
# ============================================

@router.get("/invoices")
async def list_invoices(
    user_id: str = Depends(get_user_id),
    service: GenUISubscriptionService = Depends(get_service),
):
    """Listar facturas"""
    subscription = await service.get_user_subscription(user_id)
    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription")
    
    # Query invoices from DB
    pass


@router.post("/subscriptions/{subscription_id}/invoices/generate")
async def generate_invoice(
    subscription_id: UUID,
    user_id: str = Depends(get_user_id),
    service: GenUISubscriptionService = Depends(get_service),
):
    """Generar factura manualmente"""
    subscription = await service.get_subscription(subscription_id)
    
    if not subscription or subscription.user_id != user_id:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    invoice = await service.generate_invoice(subscription_id)
    return {"invoice": invoice.model_dump()}


# ============================================
# PRICING INFO
# ============================================

@router.get("/pricing")
async def get_pricing():
    """Obtener información de precios"""
    return {
        "plans": [
            {
                "tier": tier.value,
                "limits": limits,
            }
            for tier, limits in PLAN_LIMITS.items()
        ]
    }
