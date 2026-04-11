"""
AI Recommendation Engine
Service for generating AI-powered recommendations
"""

import json
import time
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
from uuid import uuid4

from .models import (
    RecommendationContext,
    BusinessRecommendation,
    ProductRecommendation,
    PersonalizedFeed,
    AIResponse,
    AIProviderType,
)
from .base import AIProvider, AIProviderFactory, AIProviderConfig, AIGenerationOptions
from .cache_manager import AICacheManager
from .subscription_limits import SubscriptionLimitsService, SubscriptionTier

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    AI-powered recommendation engine
    
    Features:
    - Business recommendations based on context
    - Product recommendations
    - Similar business finding
    - Personalized feed generation
    """
    
    def __init__(
        self,
        provider: Optional[AIProvider] = None,
        cache_manager: Optional[AICacheManager] = None,
        limits_service: Optional[SubscriptionLimitsService] = None,
        redis_client=None,
        database_client=None
    ):
        self.provider = provider
        self.cache = cache_manager or AICacheManager()
        self.limits_service = limits_service or SubscriptionLimitsService()
        self.redis = redis_client
        self.db = database_client
    
    async def _get_provider(self, tier: SubscriptionTier) -> AIProvider:
        """Get appropriate AI provider for tier"""
        if self.provider:
            return self.provider
        
        limits = self.limits_service.get_limits(tier)
        default_model = limits.default_model
        
        # Determine provider type from model
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
    
    async def get_business_recommendations(
        self,
        user_id: str,
        location: Optional[Dict[str, Any]] = None,
        preferences: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        tier: SubscriptionTier = SubscriptionTier.FREE
    ) -> List[BusinessRecommendation]:
        """
        Get business recommendations for a user
        
        Args:
            user_id: User ID
            location: User location (lat, lng, radius)
            preferences: User preferences
            limit: Maximum number of recommendations
            tier: User's subscription tier
            
        Returns:
            List of BusinessRecommendation objects
        """
        # Check cache first
        cache_key = f"rec:business:{user_id}:{limit}"
        if self.redis:
            try:
                cached = await self.redis.get(cache_key)
                if cached:
                    data = json.loads(cached)
                    return [BusinessRecommendation(**r) for r in data]
            except Exception:
                pass
        
        # Build recommendation context
        context = RecommendationContext(
            user_id=user_id,
            location=location,
            preferences=preferences or {},
        )
        
        # Get user history if available
        context.user_history = await self._get_user_history(user_id)
        
        # Generate prompt for AI
        prompt = self._build_business_recommendation_prompt(context, limit)
        
        # Check cache for similar query
        cached_response = await self.cache.get(
            prompt,
            context={"user_id": user_id},
            model="recommendation"
        )
        
        if cached_response and cached_response.recommendations:
            return [BusinessRecommendation(**r) for r in cached_response.recommendations]
        
        # Get AI response
        provider = await self._get_provider(tier)
        
        options = AIGenerationOptions(
            max_tokens=2000,
            temperature=0.7,
            response_format={"type": "json_object"},
        )
        
        response = await provider.generate_response(
            prompt,
            context={"user_id": user_id},
            options=options
        )
        
        # Parse recommendations from response
        recommendations = self._parse_business_recommendations(response.content)
        
        # Cache the results
        response.recommendations = [r.model_dump() for r in recommendations]
        await self.cache.set(
            response,
            prompt,
            context={"user_id": user_id},
            model="recommendation",
            ttl=300
        )
        
        # Cache the list
        if self.redis:
            try:
                await self.redis.setex(
                    cache_key,
                    300,
                    json.dumps([r.model_dump() for r in recommendations])
                )
            except Exception:
                pass
        
        return recommendations
    
    async def get_product_recommendations(
        self,
        user_id: str,
        product_id: Optional[str] = None,
        business_id: Optional[str] = None,
        limit: int = 10,
        tier: SubscriptionTier = SubscriptionTier.FREE
    ) -> List[ProductRecommendation]:
        """
        Get product recommendations for a user
        
        Args:
            user_id: User ID
            product_id: Current product ID (for similar products)
            business_id: Business ID (for business products)
            limit: Maximum number of recommendations
            tier: User's subscription tier
            
        Returns:
            List of ProductRecommendation objects
        """
        # Build context
        context = RecommendationContext(
            user_id=user_id,
            current_product_id=product_id,
            current_business_id=business_id,
        )
        
        context.user_history = await self._get_user_history(user_id)
        
        # Generate prompt
        prompt = self._build_product_recommendation_prompt(context, limit)
        
        # Check cache
        cached_response = await self.cache.get(
            prompt,
            context={"user_id": user_id, "product_id": product_id},
            model="recommendation"
        )
        
        if cached_response and cached_response.recommendations:
            return [ProductRecommendation(**r) for r in cached_response.recommendations]
        
        # Get AI response
        provider = await self._get_provider(tier)
        
        options = AIGenerationOptions(
            max_tokens=2000,
            temperature=0.7,
            response_format={"type": "json_object"},
        )
        
        response = await provider.generate_response(
            prompt,
            context={"user_id": user_id},
            options=options
        )
        
        # Parse recommendations
        recommendations = self._parse_product_recommendations(response.content)
        
        # Cache results
        response.recommendations = [r.model_dump() for r in recommendations]
        await self.cache.set(
            response,
            prompt,
            context={"user_id": user_id, "product_id": product_id},
            model="recommendation",
            ttl=300
        )
        
        return recommendations
    
    async def get_similar_businesses(
        self,
        business_id: str,
        limit: int = 5,
        tier: SubscriptionTier = SubscriptionTier.FREE
    ) -> List[BusinessRecommendation]:
        """
        Get businesses similar to a given business
        
        Args:
            business_id: Business ID to find similar for
            limit: Maximum number of similar businesses
            tier: User's subscription tier
            
        Returns:
            List of similar BusinessRecommendation objects
        """
        # Check cache
        cache_key = f"rec:similar_business:{business_id}:{limit}"
        if self.redis:
            try:
                cached = await self.redis.get(cache_key)
                if cached:
                    data = json.loads(cached)
                    return [BusinessRecommendation(**r) for r in data]
            except Exception:
                pass
        
        # Get business details
        business = await self._get_business_details(business_id)
        
        if not business:
            return []
        
        # Build prompt
        prompt = f"""Find businesses similar to this one:

Business: {business.get('name', 'Unknown')}
Category: {business.get('category', 'Unknown')}
Description: {business.get('description', 'No description')}
Location: {business.get('address', 'Unknown')}

Return a JSON object with a "similar_businesses" array containing {limit} similar businesses.
Each business should have: id, name, description, category, distance_km, address, rating, reason (why it's similar).
"""
        
        # Get AI response
        provider = await self._get_provider(tier)
        
        options = AIGenerationOptions(
            max_tokens=1500,
            temperature=0.7,
            response_format={"type": "json_object"},
        )
        
        response = await provider.generate_response(prompt, options=options)
        
        # Parse similar businesses
        recommendations = self._parse_business_recommendations(response.content, key="similar_businesses")
        
        # Cache results
        if self.redis:
            try:
                await self.redis.setex(
                    cache_key,
                    600,
                    json.dumps([r.model_dump() for r in recommendations])
                )
            except Exception:
                pass
        
        return recommendations
    
    async def get_personalized_feed(
        self,
        user_id: str,
        tier: SubscriptionTier = SubscriptionTier.FREE
    ) -> PersonalizedFeed:
        """
        Generate a personalized feed for a user
        
        Args:
            user_id: User ID
            tier: User's subscription tier
            
        Returns:
            PersonalizedFeed object with recommendations
        """
        # Check cache
        cache_key = f"rec:feed:{user_id}"
        if self.redis:
            try:
                cached = await self.redis.get(cache_key)
                if cached:
                    data = json.loads(cached)
                    return PersonalizedFeed(**data)
            except Exception:
                pass
        
        # Get user context
        context = RecommendationContext(
            user_id=user_id,
        )
        context.user_history = await self._get_user_history(user_id)
        context.preferences = await self._get_user_preferences(user_id)
        
        # Generate recommendations in parallel
        businesses = await self.get_business_recommendations(
            user_id,
            preferences=context.preferences,
            limit=5,
            tier=tier
        )
        
        products = await self.get_product_recommendations(
            user_id,
            limit=5,
            tier=tier
        )
        
        # Build feed
        feed = PersonalizedFeed(
            user_id=user_id,
            businesses=businesses,
            products=products,
            featured_categories=await self._get_featured_categories(context),
        )
        feed.calculate_total()
        
        # Cache feed
        if self.redis:
            try:
                await self.redis.setex(
                    cache_key,
                    300,
                    json.dumps(feed.model_dump(), default=str)
                )
            except Exception:
                pass
        
        return feed
    
    # Helper methods
    
    def _build_business_recommendation_prompt(
        self,
        context: RecommendationContext,
        limit: int
    ) -> str:
        """Build prompt for business recommendations"""
        location_str = ""
        if context.location:
            location_str = f"Location: {context.location}"
        elif context.latitude and context.longitude:
            location_str = f"Location: lat={context.latitude}, lng={context.longitude}, radius={context.radius_km}km"
        
        history_str = ""
        if context.user_history:
            recent = [h.get("business_name", h.get("name", "")) for h in context.user_history[:5]]
            history_str = f"Recent activity: {', '.join(recent)}"
        
        preferences_str = ""
        if context.preferences:
            prefs = [f"{k}: {v}" for k, v in list(context.preferences.items())[:5]]
            preferences_str = f"Preferences: {', '.join(prefs)}"
        
        return f"""Generate personalized business recommendations for a user.

{location_str}
{history_str}
{preferences_str}

Return a JSON object with a "recommendations" array containing exactly {limit} business recommendations.
Each recommendation must have:
- id (unique identifier)
- name (business name)
- description (brief description)
- category (business category)
- rating (float 0-5)
- distance_km (distance from user)
- address (physical address)
- score (relevance score 0-1)
- reason (why this business was recommended)
- tags (array of relevant tags)
"""
    
    def _build_product_recommendation_prompt(
        self,
        context: RecommendationContext,
        limit: int
    ) -> str:
        """Build prompt for product recommendations"""
        product_context = ""
        if context.current_product_id:
            product_context = f"Current product: {context.current_product_id}"
        
        business_context = ""
        if context.current_business_id:
            business_context = f"From business: {context.current_business_id}"
        
        history_str = ""
        if context.user_history:
            products = [h.get("product_name", h.get("name", "")) for h in context.user_history if h.get("type") == "product"]
            if products:
                history_str = f"Recent products viewed: {', '.join(products[:5])}"
        
        return f"""Generate personalized product recommendations for a user.

{product_context}
{business_context}
{history_str}

Return a JSON object with a "recommendations" array containing exactly {limit} product recommendations.
Each recommendation must have:
- id (unique identifier)
- name (product name)
- description (brief description)
- price (float)
- currency (default "USD")
- category (product category)
- business_id (if known)
- business_name (if known)
- score (relevance score 0-1)
- reason (why this product was recommended)
"""
    
    def _parse_business_recommendations(
        self,
        content: str,
        key: str = "recommendations"
    ) -> List[BusinessRecommendation]:
        """Parse business recommendations from AI response"""
        try:
            data = json.loads(content)
            recommendations_data = data.get(key, data.get("businesses", []))
            
            recommendations = []
            for r in recommendations_data:
                try:
                    recommendations.append(BusinessRecommendation(
                        id=str(r.get("id", str(uuid4()))),
                        name=r.get("name", "Unknown Business"),
                        description=r.get("description"),
                        category=r.get("category"),
                        rating=float(r.get("rating", 0)),
                        distance_km=float(r.get("distance_km", 0)),
                        address=r.get("address"),
                        score=float(r.get("score", 0)),
                        reason=r.get("reason"),
                        tags=r.get("tags", []),
                    ))
                except Exception as e:
                    logger.warning(f"Failed to parse recommendation: {e}")
                    continue
            
            return recommendations
            
        except json.JSONDecodeError:
            logger.error(f"Failed to parse AI response as JSON: {content[:200]}")
            return []
    
    def _parse_product_recommendations(
        self,
        content: str,
        key: str = "recommendations"
    ) -> List[ProductRecommendation]:
        """Parse product recommendations from AI response"""
        try:
            data = json.loads(content)
            recommendations_data = data.get(key, data.get("products", []))
            
            recommendations = []
            for r in recommendations_data:
                try:
                    recommendations.append(ProductRecommendation(
                        id=str(r.get("id", str(uuid4()))),
                        name=r.get("name", "Unknown Product"),
                        description=r.get("description"),
                        price=float(r.get("price", 0)),
                        currency=r.get("currency", "USD"),
                        category=r.get("category"),
                        business_id=r.get("business_id"),
                        business_name=r.get("business_name"),
                        score=float(r.get("score", 0)),
                        reason=r.get("reason"),
                    ))
                except Exception as e:
                    logger.warning(f"Failed to parse product recommendation: {e}")
                    continue
            
            return recommendations
            
        except json.JSONDecodeError:
            logger.error(f"Failed to parse AI response as JSON")
            return []
    
    async def _get_user_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user activity history"""
        # In production, query from database
        if self.redis:
            try:
                history_key = f"user_history:{user_id}"
                cached = await self.redis.get(history_key)
                if cached:
                    return json.loads(cached)
            except Exception:
                pass
        
        return []
    
    async def _get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences"""
        if self.redis:
            try:
                prefs_key = f"user_preferences:{user_id}"
                cached = await self.redis.get(prefs_key)
                if cached:
                    return json.loads(cached)
            except Exception:
                pass
        
        return {}
    
    async def _get_business_details(self, business_id: str) -> Optional[Dict[str, Any]]:
        """Get business details from database"""
        # In production, query from database
        if self.redis:
            try:
                business_key = f"business:{business_id}"
                cached = await self.redis.get(business_key)
                if cached:
                    return json.loads(cached)
            except Exception:
                pass
        
        return None
    
    async def _get_featured_categories(
        self,
        context: RecommendationContext
    ) -> List[Dict[str, Any]]:
        """Get featured categories based on context"""
        # Default categories
        categories = [
            {"id": "food", "name": "Food & Dining", "icon": "restaurant"},
            {"id": "shopping", "name": "Shopping", "icon": "store"},
            {"id": "services", "name": "Services", "icon": "build"},
            {"id": "entertainment", "name": "Entertainment", "icon": "movie"},
        ]
        
        # Could personalize based on context
        
        return categories
