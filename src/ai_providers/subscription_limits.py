"""
Subscription-based AI Limits
Manages AI usage limits based on subscription tiers
"""

from enum import Enum
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class SubscriptionTier(str, Enum):
    """Subscription tier levels"""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


class AITierLimits(BaseModel):
    """AI-specific limits for a subscription tier"""
    tier: SubscriptionTier
    
    # Query limits
    daily_queries: int
    monthly_queries: int
    
    # Token limits
    max_tokens_per_request: int
    max_tokens_per_day: int
    max_tokens_per_month: int
    
    # Model access
    available_providers: List[str]
    available_models: List[str]
    default_model: str
    
    # Features
    supports_streaming: bool
    supports_vision: bool
    supports_context: bool
    supports_history: bool
    max_history_length: int
    context_types: List[str]
    
    # Processing
    priority_processing: bool
    priority_queue: str  # "low", "normal", "high"
    
    # Cache
    cache_ttl: int  # seconds
    cache_enabled: bool
    
    # Rate limiting
    rate_limit_per_minute: int
    rate_limit_per_hour: int


# Define limits for each tier
TIER_LIMITS: Dict[SubscriptionTier, AITierLimits] = {
    SubscriptionTier.FREE: AITierLimits(
        tier=SubscriptionTier.FREE,
        daily_queries=5,
        monthly_queries=100,
        max_tokens_per_request=1024,
        max_tokens_per_day=5000,
        max_tokens_per_month=100000,
        available_providers=["local"],
        available_models=["mock", "llama3.2"],
        default_model="mock",
        supports_streaming=False,
        supports_vision=False,
        supports_context=False,
        supports_history=False,
        max_history_length=0,
        context_types=[],
        priority_processing=False,
        priority_queue="low",
        cache_ttl=60,
        cache_enabled=True,
        rate_limit_per_minute=1,
        rate_limit_per_hour=5,
    ),
    SubscriptionTier.STARTER: AITierLimits(
        tier=SubscriptionTier.STARTER,
        daily_queries=50,
        monthly_queries=1000,
        max_tokens_per_request=4096,
        max_tokens_per_day=100000,
        max_tokens_per_month=2000000,
        available_providers=["openai", "local"],
        available_models=["gpt-4o-mini", "gpt-3.5-turbo", "mock", "llama3.2"],
        default_model="gpt-4o-mini",
        supports_streaming=True,
        supports_vision=False,
        supports_context=True,
        supports_history=True,
        max_history_length=10,
        context_types=["personal", "device"],
        priority_processing=False,
        priority_queue="normal",
        cache_ttl=300,
        cache_enabled=True,
        rate_limit_per_minute=10,
        rate_limit_per_hour=50,
    ),
    SubscriptionTier.PROFESSIONAL: AITierLimits(
        tier=SubscriptionTier.PROFESSIONAL,
        daily_queries=500,
        monthly_queries=10000,
        max_tokens_per_request=8192,
        max_tokens_per_day=500000,
        max_tokens_per_month=10000000,
        available_providers=["openai", "anthropic", "local"],
        available_models=["gpt-4o", "gpt-4o-mini", "claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "mock"],
        default_model="claude-3-5-sonnet-20241022",
        supports_streaming=True,
        supports_vision=True,
        supports_context=True,
        supports_history=True,
        max_history_length=50,
        context_types=["personal", "device", "temporal", "spatial"],
        priority_processing=False,
        priority_queue="normal",
        cache_ttl=900,
        cache_enabled=True,
        rate_limit_per_minute=30,
        rate_limit_per_hour=500,
    ),
    SubscriptionTier.BUSINESS: AITierLimits(
        tier=SubscriptionTier.BUSINESS,
        daily_queries=2000,
        monthly_queries=50000,
        max_tokens_per_request=16384,
        max_tokens_per_day=2000000,
        max_tokens_per_month=50000000,
        available_providers=["openai", "anthropic", "local"],
        available_models=["gpt-4o", "gpt-4o-mini", "claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229"],
        default_model="claude-3-5-sonnet-20241022",
        supports_streaming=True,
        supports_vision=True,
        supports_context=True,
        supports_history=True,
        max_history_length=100,
        context_types=["personal", "device", "temporal", "spatial", "solution", "horizontal"],
        priority_processing=True,
        priority_queue="high",
        cache_ttl=1800,
        cache_enabled=True,
        rate_limit_per_minute=100,
        rate_limit_per_hour=2000,
    ),
    SubscriptionTier.ENTERPRISE: AITierLimits(
        tier=SubscriptionTier.ENTERPRISE,
        daily_queries=-1,  # Unlimited
        monthly_queries=-1,
        max_tokens_per_request=32768,
        max_tokens_per_day=-1,
        max_tokens_per_month=-1,
        available_providers=["openai", "anthropic", "local"],
        available_models=["all"],  # All models available
        default_model="claude-3-5-sonnet-20241022",
        supports_streaming=True,
        supports_vision=True,
        supports_context=True,
        supports_history=True,
        max_history_length=500,
        context_types=["all"],
        priority_processing=True,
        priority_queue="high",
        cache_ttl=3600,
        cache_enabled=True,
        rate_limit_per_minute=1000,
        rate_limit_per_hour=10000,
    ),
}


class SubscriptionLimitsService:
    """Service for managing subscription-based AI limits"""
    
    def __init__(self, redis_client=None):
        self.redis = redis_client
        self._limits = TIER_LIMITS
    
    def get_limits(self, tier: SubscriptionTier) -> AITierLimits:
        """Get limits for a subscription tier"""
        return self._limits.get(tier, self._limits[SubscriptionTier.FREE])
    
    def can_use_provider(
        self,
        tier: SubscriptionTier,
        provider: str
    ) -> bool:
        """Check if a provider is available for a tier"""
        limits = self.get_limits(tier)
        return provider in limits.available_providers or "all" in limits.available_models
    
    def can_use_model(
        self,
        tier: SubscriptionTier,
        model: str
    ) -> bool:
        """Check if a model is available for a tier"""
        limits = self.get_limits(tier)
        return model in limits.available_models or "all" in limits.available_models
    
    def get_available_models(self, tier: SubscriptionTier) -> List[str]:
        """Get available models for a tier"""
        limits = self.get_limits(tier)
        if "all" in limits.available_models:
            # Return all models from all providers
            all_models = []
            for provider_limits in self._limits.values():
                all_models.extend(provider_limits.available_models)
            return list(set(all_models))
        return limits.available_models
    
    def get_default_model(self, tier: SubscriptionTier) -> str:
        """Get default model for a tier"""
        limits = self.get_limits(tier)
        return limits.default_model
    
    async def check_quota(
        self,
        user_id: str,
        tier: SubscriptionTier,
        subscription_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check if user has quota available
        
        Returns dict with:
        - can_use: bool
        - daily_remaining: int
        - monthly_remaining: int
        - reset_times: dict
        """
        limits = self.get_limits(tier)
        
        # Get usage from Redis
        daily_key = f"ai_usage:daily:{user_id}:{datetime.utcnow().strftime('%Y-%m-%d')}"
        monthly_key = f"ai_usage:monthly:{user_id}:{datetime.utcnow().strftime('%Y-%m')}"
        
        daily_used = 0
        monthly_used = 0
        
        if self.redis:
            try:
                daily_used = int(await self.redis.get(daily_key) or 0)
                monthly_used = int(await self.redis.get(monthly_key) or 0)
            except Exception as e:
                logger.warning(f"Failed to get usage from Redis: {e}")
        
        # Calculate remaining
        daily_remaining = limits.daily_queries - daily_used if limits.daily_queries > 0 else -1
        monthly_remaining = limits.monthly_queries - monthly_used if limits.monthly_queries > 0 else -1
        
        # Unlimited tiers
        if limits.daily_queries == -1:
            daily_remaining = -1
        if limits.monthly_queries == -1:
            monthly_remaining = -1
        
        can_use = (
            (daily_remaining > 0 or daily_remaining == -1) and
            (monthly_remaining > 0 or monthly_remaining == -1)
        )
        
        # Calculate reset times
        now = datetime.utcnow()
        daily_reset = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        monthly_reset = (now.replace(day=1) + timedelta(days=32)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        return {
            "can_use": can_use,
            "daily_used": daily_used,
            "daily_limit": limits.daily_queries,
            "daily_remaining": daily_remaining,
            "monthly_used": monthly_used,
            "monthly_limit": limits.monthly_queries,
            "monthly_remaining": monthly_remaining,
            "reset_times": {
                "daily": daily_reset.isoformat(),
                "monthly": monthly_reset.isoformat(),
            },
        }
    
    async def record_usage(
        self,
        user_id: str,
        tokens_used: int,
        subscription_id: Optional[str] = None
    ) -> None:
        """Record AI usage for a user"""
        if not self.redis:
            return
        
        now = datetime.utcnow()
        daily_key = f"ai_usage:daily:{user_id}:{now.strftime('%Y-%m-%d')}"
        monthly_key = f"ai_usage:monthly:{user_id}:{now.strftime('%Y-%m')}"
        tokens_daily_key = f"ai_tokens:daily:{user_id}:{now.strftime('%Y-%m-%d')}"
        tokens_monthly_key = f"ai_tokens:monthly:{user_id}:{now.strftime('%Y-%m')}"
        
        try:
            # Increment counters
            await self.redis.incr(daily_key)
            await self.redis.incr(monthly_key)
            await self.redis.incrby(tokens_daily_key, tokens_used)
            await self.redis.incrby(tokens_monthly_key, tokens_used)
            
            # Set expiration
            await self.redis.expire(daily_key, 86400 * 2)  # 2 days
            await self.redis.expire(monthly_key, 86400 * 35)  # 35 days
            await self.redis.expire(tokens_daily_key, 86400 * 2)
            await self.redis.expire(tokens_monthly_key, 86400 * 35)
            
        except Exception as e:
            logger.error(f"Failed to record usage: {e}")
    
    async def get_usage_stats(
        self,
        user_id: str,
        tier: SubscriptionTier
    ) -> Dict[str, Any]:
        """Get detailed usage statistics for a user"""
        limits = self.get_limits(tier)
        quota = await self.check_quota(user_id, tier)
        
        return {
            "tier": tier.value,
            "limits": {
                "daily_queries": limits.daily_queries,
                "monthly_queries": limits.monthly_queries,
                "max_tokens_per_request": limits.max_tokens_per_request,
            },
            "usage": {
                "daily_used": quota["daily_used"],
                "monthly_used": quota["monthly_used"],
                "daily_remaining": quota["daily_remaining"],
                "monthly_remaining": quota["monthly_remaining"],
            },
            "features": {
                "streaming": limits.supports_streaming,
                "vision": limits.supports_vision,
                "context": limits.supports_context,
                "history": limits.supports_history,
                "priority": limits.priority_processing,
            },
            "models": self.get_available_models(tier),
            "reset_times": quota["reset_times"],
        }
    
    def validate_request(
        self,
        tier: SubscriptionTier,
        model: Optional[str] = None,
        tokens_requested: int = 0,
        use_streaming: bool = False,
        use_vision: bool = False,
        use_context: bool = False,
    ) -> Dict[str, Any]:
        """
        Validate if a request is allowed for the tier
        
        Returns dict with:
        - allowed: bool
        - errors: List[str]
        - warnings: List[str]
        - suggested_model: str
        """
        limits = self.get_limits(tier)
        errors = []
        warnings = []
        
        # Check model access
        suggested_model = limits.default_model
        if model and not self.can_use_model(tier, model):
            errors.append(f"Model '{model}' not available for your tier")
            warnings.append(f"Using default model: {limits.default_model}")
            model = limits.default_model
        
        # Check token limit
        if tokens_requested > limits.max_tokens_per_request:
            errors.append(f"Requested {tokens_requested} tokens exceeds limit of {limits.max_tokens_per_request}")
        
        # Check feature access
        if use_streaming and not limits.supports_streaming:
            errors.append("Streaming not supported for your tier")
        
        if use_vision and not limits.supports_vision:
            errors.append("Vision not supported for your tier")
        
        if use_context and not limits.supports_context:
            warnings.append("Context not supported for your tier, ignoring")
        
        return {
            "allowed": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "suggested_model": suggested_model,
            "limits": limits.model_dump(),
        }
