"""
GenUI/A2UI Subscription Service
Servicio principal para gestión de suscripciones y uso
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID
import hashlib
import secrets

from .subscription import (
    SubscriptionTier,
    UsageType,
    PLAN_LIMITS,
    GenUISubscription,
    GenUIUsageRecord,
    GenUIQuota,
    GenUIInvoice,
    GenUIAPIKey,
)


class GenUISubscriptionService:
    """Servicio de suscripción para GenUI/A2UI"""
    
    def __init__(self, db_session, redis_client, ricco_id_client):
        self.db = db_session
        self.redis = redis_client
        self.ricco_id = ricco_id_client
    
    # ============================================
    # SUBSCRIPTION MANAGEMENT
    # ============================================
    
    async def create_subscription(
        self,
        user_id: str,
        tier: SubscriptionTier = SubscriptionTier.FREE,
        organization_id: Optional[str] = None,
        billing_cycle: str = "monthly",
    ) -> GenUISubscription:
        """Crear una nueva suscripción"""
        now = datetime.utcnow()
        
        if billing_cycle == "yearly":
            period_end = now + timedelta(days=365)
        else:
            period_end = now + timedelta(days=30)
        
        limits = PLAN_LIMITS[tier]
        
        subscription = GenUISubscription(
            user_id=user_id,
            organization_id=organization_id,
            tier=tier,
            billing_cycle=billing_cycle,
            current_period_start=now,
            current_period_end=period_end,
            enabled_context_types=limits["context_types"],
        )
        
        # Save to DB
        await self.db.insert("genui_subscriptions", subscription.model_dump())
        
        # Create initial quota
        await self._create_quota(subscription.id, limits)
        
        return subscription
    
    async def upgrade_subscription(
        self,
        subscription_id: UUID,
        new_tier: SubscriptionTier,
        prorate: bool = True,
    ) -> GenUISubscription:
        """Actualizar suscripción a un plan superior"""
        subscription = await self.get_subscription(subscription_id)
        
        old_tier = subscription.tier
        limits = PLAN_LIMITS[new_tier]
        
        # Calculate proration if needed
        if prorate and subscription.tier != SubscriptionTier.FREE:
            proration_amount = await self._calculate_proration(subscription, new_tier)
            # Handle proration billing...
        
        # Update subscription
        subscription.tier = new_tier
        subscription.enabled_context_types = limits["context_types"]
        subscription.updated_at = datetime.utcnow()
        
        await self.db.update(
            "genui_subscriptions",
            subscription.model_dump(),
            {"id": str(subscription_id)}
        )
        
        # Update quota
        await self._update_quota_limits(subscription_id, limits)
        
        return subscription
    
    async def get_subscription(self, subscription_id: UUID) -> Optional[GenUISubscription]:
        """Obtener suscripción por ID"""
        result = await self.db.find_one(
            "genui_subscriptions",
            {"id": str(subscription_id)}
        )
        return GenUISubscription(**result) if result else None
    
    async def get_user_subscription(self, user_id: str) -> Optional[GenUISubscription]:
        """Obtener suscripción activa de un usuario"""
        result = await self.db.find_one(
            "genui_subscriptions",
            {"user_id": user_id, "status": "active"}
        )
        return GenUISubscription(**result) if result else None
    
    # ============================================
    # USAGE TRACKING
    # ============================================
    
    async def check_quota(self, subscription_id: UUID) -> Dict[str, Any]:
        """Verificar cuota disponible"""
        quota = await self._get_quota(subscription_id)
        
        # Check daily reset
        if self._needs_daily_reset(quota):
            await self._reset_daily_quota(quota)
        
        # Check monthly reset
        if self._needs_monthly_reset(quota):
            await self._reset_monthly_quota(quota)
        
        return {
            "remaining_monthly": quota.remaining_monthly(),
            "remaining_daily": quota.remaining_daily(),
            "monthly_limit": quota.monthly_limit,
            "daily_limit": quota.daily_limit,
            "can_use": quota.can_use(),
        }
    
    async def record_usage(
        self,
        subscription_id: UUID,
        usage_type: UsageType,
        user_id: str,
        tokens_used: int = 0,
        mini_program_id: Optional[str] = None,
        surface_id: Optional[str] = None,
        solution: Optional[str] = None,
        context_types_used: Optional[List[str]] = None,
        latency_ms: int = 0,
        components_generated: int = 0,
        metadata: Optional[Dict] = None,
    ) -> GenUIUsageRecord:
        """Registrar uso de GenUI/A2UI"""
        
        # Check quota first
        quota = await self._get_quota(subscription_id)
        if not quota.can_use():
            raise QuotaExceededError("Quota exceeded for this period")
        
        # Calculate cost in Energy Points
        cost_credits = self._calculate_usage_cost(
            usage_type, tokens_used, components_generated
        )
        
        record = GenUIUsageRecord(
            subscription_id=subscription_id,
            user_id=user_id,
            usage_type=usage_type,
            mini_program_id=mini_program_id,
            surface_id=surface_id,
            solution=solution,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            components_generated=components_generated,
            context_types_used=context_types_used or [],
            cost_credits=cost_credits,
            metadata=metadata,
        )
        
        # Save record
        await self.db.insert("genui_usage_records", record.model_dump())
        
        # Update quota
        await self._increment_quota_usage(subscription_id, 1, cost_credits)
        
        # Cache recent usage in Redis for rate limiting
        await self._cache_usage_for_rate_limit(subscription_id)
        
        return record
    
    async def get_usage_stats(
        self,
        subscription_id: UUID,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Obtener estadísticas de uso"""
        
        if not period_start:
            period_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
        if not period_end:
            period_end = datetime.utcnow()
        
        records = await self.db.find(
            "genui_usage_records",
            {
                "subscription_id": str(subscription_id),
                "timestamp": {"$gte": period_start, "$lte": period_end}
            }
        )
        
        # Aggregate stats
        total_queries = len(records)
        total_tokens = sum(r.get("tokens_used", 0) for r in records)
        total_cost = sum(r.get("cost_credits", 0) for r in records)
        avg_latency = sum(r.get("latency_ms", 0) for r in records) / max(total_queries, 1)
        
        by_type = {}
        for r in records:
            t = r.get("usage_type", "unknown")
            by_type[t] = by_type.get(t, 0) + 1
        
        by_solution = {}
        for r in records:
            s = r.get("solution", "unknown")
            by_solution[s] = by_solution.get(s, 0) + 1
        
        return {
            "period": {
                "start": period_start,
                "end": period_end,
            },
            "total_queries": total_queries,
            "total_tokens": total_tokens,
            "total_cost_credits": total_cost,
            "avg_latency_ms": avg_latency,
            "by_type": by_type,
            "by_solution": by_solution,
        }
    
    # ============================================
    # RATE LIMITING
    # ============================================
    
    async def check_rate_limit(self, subscription_id: UUID) -> Dict[str, Any]:
        """Verificar rate limit"""
        subscription = await self.get_subscription(subscription_id)
        limits = PLAN_LIMITS[subscription.tier]
        
        rate_limit = limits["rate_limit_per_minute"]
        if rate_limit == -1:
            return {"allowed": True, "unlimited": True}
        
        # Get usage in last minute from Redis
        key = f"rate_limit:{subscription_id}"
        current = await self.redis.incr(key)
        
        if current == 1:
            await self.redis.expire(key, 60)  # 1 minute window
        
        allowed = current <= rate_limit
        
        return {
            "allowed": allowed,
            "current": current,
            "limit": rate_limit,
            "reset_in_seconds": await self.redis.ttl(key),
        }
    
    # ============================================
    # API KEYS
    # ============================================
    
    async def create_api_key(
        self,
        subscription_id: UUID,
        user_id: str,
        name: str,
        scopes: List[str] = None,
    ) -> tuple[GenUIAPIKey, str]:
        """Crear API key (retorna la key completa solo una vez)"""
        
        # Generate key
        raw_key = f"genui_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_prefix = raw_key[:12]
        
        api_key = GenUIAPIKey(
            subscription_id=subscription_id,
            user_id=user_id,
            key_hash=key_hash,
            key_prefix=key_prefix,
            name=name,
            scopes=scopes or ["read", "write"],
        )
        
        await self.db.insert("genui_api_keys", api_key.model_dump())
        
        return api_key, raw_key  # raw_key should be shown only once
    
    async def validate_api_key(self, raw_key: str) -> Optional[GenUIAPIKey]:
        """Validar API key"""
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        
        api_key = await self.db.find_one(
            "genui_api_keys",
            {"key_hash": key_hash, "is_active": True}
        )
        
        if api_key:
            # Update last used
            await self.db.update(
                "genui_api_keys",
                {"last_used_at": datetime.utcnow()},
                {"id": api_key["id"]}
            )
            return GenUIAPIKey(**api_key)
        
        return None
    
    # ============================================
    # INVOICING
    # ============================================
    
    async def generate_invoice(self, subscription_id: UUID) -> GenUIInvoice:
        """Generar factura para el período actual"""
        subscription = await self.get_subscription(subscription_id)
        limits = PLAN_LIMITS[subscription.tier]
        
        # Get usage stats
        stats = await self.get_usage_stats(subscription_id)
        
        # Calculate amounts
        base_amount = limits["price_monthly"]
        if subscription.billing_cycle == "yearly":
            base_amount = base_amount * 12 * 0.85  # 15% discount
        
        # Extra usage
        monthly_limit = limits["monthly_queries"]
        extra_queries = max(0, stats["total_queries"] - monthly_limit) if monthly_limit != -1 else 0
        extra_usage_amount = extra_queries * limits["price_per_extra_query"]
        
        invoice = GenUIInvoice(
            subscription_id=subscription_id,
            user_id=subscription.user_id,
            period_start=subscription.current_period_start,
            period_end=subscription.current_period_end,
            base_amount=base_amount if isinstance(base_amount, (int, float)) else 0,
            extra_usage_amount=extra_usage_amount,
            total_amount=base_amount + extra_usage_amount if isinstance(base_amount, (int, float)) else extra_usage_amount,
            queries_included=monthly_limit if monthly_limit != -1 else -1,
            queries_used=stats["total_queries"],
            extra_queries=extra_queries,
        )
        
        await self.db.insert("genui_invoices", invoice.model_dump())
        
        return invoice
    
    # ============================================
    # PRIVATE HELPERS
    # ============================================
    
    def _calculate_usage_cost(
        self,
        usage_type: UsageType,
        tokens_used: int,
        components_generated: int,
    ) -> float:
        """Calcular costo en Energy Points"""
        # Base costs by type
        base_costs = {
            UsageType.SURFACE_GENERATION: 1.0,
            UsageType.ACTION_PROCESSING: 0.5,
            UsageType.CATALOG_LOADING: 0.1,
            UsageType.CONTEXT_BUILDING: 0.3,
            UsageType.AI_INFERENCE: 2.0,
            UsageType.MINI_PROGRAM_RUN: 1.5,
        }
        
        base = base_costs.get(usage_type, 1.0)
        
        # Token cost (1000 tokens = 0.1 credits)
        token_cost = tokens_used / 10000
        
        # Component cost
        component_cost = components_generated * 0.01
        
        return base + token_cost + component_cost
    
    async def _create_quota(self, subscription_id: UUID, limits: Dict) -> GenUIQuota:
        """Crear cuota inicial"""
        now = datetime.utcnow()
        
        quota = GenUIQuota(
            subscription_id=subscription_id,
            period=now.strftime("%Y-%m"),
            monthly_limit=limits["monthly_queries"],
            daily_limit=limits["daily_queries"],
            last_reset_daily=now,
            last_reset_monthly=now,
        )
        
        await self.db.insert("genui_quotas", quota.model_dump())
        return quota
    
    async def _get_quota(self, subscription_id: UUID) -> GenUIQuota:
        """Obtener cuota actual"""
        result = await self.db.find_one(
            "genui_quotas",
            {"subscription_id": str(subscription_id)}
        )
        return GenUIQuota(**result) if result else None
    
    async def _increment_quota_usage(
        self,
        subscription_id: UUID,
        count: int,
        cost: float,
    ):
        """Incrementar uso de cuota"""
        quota = await self._get_quota(subscription_id)
        
        updates = {
            "monthly_used": quota.monthly_used + count,
            "daily_used": quota.daily_used + count,
        }
        
        # Check if extra usage
        if quota.monthly_limit != -1 and quota.monthly_used + count > quota.monthly_limit:
            extra = quota.monthly_used + count - quota.monthly_limit
            updates["extra_queries_used"] = quota.extra_queries_used + extra
            updates["extra_queries_cost"] = quota.extra_queries_cost + (extra * cost)
        
        await self.db.update(
            "genui_quotas",
            updates,
            {"subscription_id": str(subscription_id)}
        )
    
    async def _update_quota_limits(self, subscription_id: UUID, limits: Dict):
        """Actualizar límites de cuota"""
        await self.db.update(
            "genui_quotas",
            {
                "monthly_limit": limits["monthly_queries"],
                "daily_limit": limits["daily_queries"],
            },
            {"subscription_id": str(subscription_id)}
        )
    
    def _needs_daily_reset(self, quota: GenUIQuota) -> bool:
        now = datetime.utcnow()
        return (now - quota.last_reset_daily).days >= 1
    
    def _needs_monthly_reset(self, quota: GenUIQuota) -> bool:
        now = datetime.utcnow()
        return now.month != quota.last_reset_monthly.month or now.year != quota.last_reset_monthly.year
    
    async def _reset_daily_quota(self, quota: GenUIQuota):
        await self.db.update(
            "genui_quotas",
            {
                "daily_used": 0,
                "last_reset_daily": datetime.utcnow(),
            },
            {"subscription_id": str(quota.subscription_id)}
        )
    
    async def _reset_monthly_quota(self, quota: GenUIQuota):
        now = datetime.utcnow()
        await self.db.update(
            "genui_quotas",
            {
                "monthly_used": 0,
                "daily_used": 0,
                "extra_queries_used": 0,
                "extra_queries_cost": 0,
                "period": now.strftime("%Y-%m"),
                "last_reset_monthly": now,
                "last_reset_daily": now,
            },
            {"subscription_id": str(quota.subscription_id)}
        )
    
    async def _cache_usage_for_rate_limit(self, subscription_id: UUID):
        key = f"usage:{subscription_id}:{datetime.utcnow().strftime('%Y-%m-%d:%H:%M')}"
        await self.redis.incr(key)
        await self.redis.expire(key, 3600)  # 1 hour TTL
    
    async def _calculate_proration(
        self,
        subscription: GenUISubscription,
        new_tier: SubscriptionTier,
    ) -> float:
        """Calcular prorrateo de cambio de plan"""
        # Calculate unused days
        now = datetime.utcnow()
        total_days = (subscription.current_period_end - subscription.current_period_start).days
        remaining_days = (subscription.current_period_end - now).days
        
        # Calculate proration
        old_price = PLAN_LIMITS[subscription.tier]["price_monthly"]
        new_price = PLAN_LIMITS[new_tier]["price_monthly"]
        
        if isinstance(old_price, (int, float)) and isinstance(new_price, (int, float)):
            unused_value = old_price * (remaining_days / total_days)
            new_period_value = new_price * (remaining_days / total_days)
            return new_period_value - unused_value
        
        return 0


class QuotaExceededError(Exception):
    """Raised when quota is exceeded"""
    pass


class RateLimitExceededError(Exception):
    """Raised when rate limit is exceeded"""
    pass
