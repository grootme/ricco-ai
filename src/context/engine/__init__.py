"""
Context Engine Module for RICCO AI.

Multi-level caching context fusion engine with parallel collection.
Target TTFT (Time-to-First-Token) < 500ms.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class ContextLevel(str, Enum):
    """Context cache levels."""
    L1_MEMORY = "l1_memory"
    L2_REDIS = "l2_redis"
    L3_VECTOR = "l3_vector"


class PersonalContext(BaseModel):
    """Personal user context."""
    user_id: str
    name: Optional[str] = None
    language: str = "es"
    timezone: str = "America/Havana"
    preferences: Dict[str, Any] = Field(default_factory=dict)
    trust_score: float = 0.0
    energy_points: int = 0


class SpatialContext(BaseModel):
    """Spatial/geographic context."""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    city: Optional[str] = None
    country: str = "CU"
    region: Optional[str] = None


class TemporalContext(BaseModel):
    """Temporal context."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    timezone: str = "America/Havana"
    is_weekend: bool = False
    time_of_day: str = "morning"  # morning, afternoon, evening, night


class DeviceContext(BaseModel):
    """Device context."""
    device_id: Optional[str] = None
    device_type: str = "mobile"  # mobile, desktop, tablet
    platform: str = "android"  # android, ios, web
    app_version: Optional[str] = None
    screen_size: Optional[str] = None


class SolutionContext(BaseModel):
    """Solution-specific context."""
    solution_id: str
    solution_type: str  # commerce, health, finance, etc.
    active_features: List[str] = Field(default_factory=list)
    configuration: Dict[str, Any] = Field(default_factory=dict)


class HorizontalContext(BaseModel):
    """Cross-cutting context."""
    energy_points_balance: int = 0
    trust_score: float = 0.0
    subscription_tier: str = "free"
    notification_preferences: Dict[str, bool] = Field(default_factory=dict)


class VerticalContext(BaseModel):
    """Domain-specific context."""
    domain: str
    industry: Optional[str] = None
    regulations: List[str] = Field(default_factory=list)
    custom_data: Dict[str, Any] = Field(default_factory=dict)


class SkillsContext(BaseModel):
    """AI skills context."""
    enabled_skills: List[str] = Field(default_factory=list)
    skill_levels: Dict[str, int] = Field(default_factory=dict)
    available_tools: List[str] = Field(default_factory=list)


class RAGContext(BaseModel):
    """Retrieval-augmented generation context."""
    documents: List[Dict[str, Any]] = Field(default_factory=list)
    relevance_scores: List[float] = Field(default_factory=list)
    total_chunks: int = 0


class ContextBundle(BaseModel):
    """Complete context bundle for a user."""
    bundle_id: str
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Context components
    personal: Optional[PersonalContext] = None
    spatial: Optional[SpatialContext] = None
    temporal: Optional[TemporalContext] = None
    device: Optional[DeviceContext] = None
    solution: Optional[SolutionContext] = None
    horizontal: Optional[HorizontalContext] = None
    vertical: Optional[VerticalContext] = None
    skills: Optional[SkillsContext] = None
    rag: Optional[RAGContext] = None
    
    # Metadata
    cache_hit: bool = False
    collection_time_ms: float = 0.0
    ttl_seconds: int = 900  # 15 minutes


class CacheEntry(BaseModel):
    """Cache entry for context data."""
    key: str
    value: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    level: ContextLevel = ContextLevel.L1_MEMORY
    hit_count: int = 0


class ContextEngineConfig(BaseModel):
    """Configuration for context engine."""
    l1_ttl_seconds: int = 0  # Infinite for L1
    l2_ttl_seconds: int = 900  # 15 minutes
    l3_ttl_seconds: int = 3600  # 1 hour
    max_bundle_size_bytes: int = 65536
    enable_parallel_collection: bool = True
    target_ttft_ms: int = 500


class ContextFusionEngine:
    """
    Context Fusion Engine for RICCO AI.
    
    Features:
    - Multi-level caching (L1/L2/L3)
    - Parallel collection of 9 context types
    - Pre-computation of common bundles
    - Trust Score integration
    
    Context Types:
    1. Personal - User profile and preferences
    2. Spatial - Location and geographical data
    3. Temporal - Time and date information
    4. Device - Device and platform info
    5. Solution - Solution-specific context
    6. Horizontal - Cross-cutting concerns
    7. Vertical - Domain-specific context
    8. Skills - Skills and capabilities
    9. RAG - Retrieval-augmented generation
    """
    
    def __init__(self, config: Optional[ContextEngineConfig] = None):
        self.config = config or ContextEngineConfig()
        
        # Cache layers
        self._l1_cache: Dict[str, CacheEntry] = {}  # In-memory
        # self._l2_cache: Redis client
        # self._l3_cache: Vector DB client
        
        # Providers
        self._providers: Dict[str, Any] = {}
        
        # Metrics
        self._total_requests = 0
        self._cache_hits = 0
        self._total_collection_time_ms = 0.0
    
    async def start(self) -> None:
        """Start the context engine."""
        logger.info("Context Fusion Engine started")
    
    async def stop(self) -> None:
        """Stop the context engine."""
        logger.info("Context Fusion Engine stopped")
    
    async def get_context(
        self,
        user_id: str,
        context_types: Optional[List[str]] = None,
        use_cache: bool = True,
    ) -> ContextBundle:
        """
        Get context bundle for a user.
        
        Args:
            user_id: User identifier
            context_types: Types of context to include (all if None)
            use_cache: Whether to use cached data
            
        Returns:
            ContextBundle with requested context types
        """
        import time
        import uuid
        
        start_time = time.time()
        self._total_requests += 1
        
        bundle_id = str(uuid.uuid4())
        
        # Check cache
        cache_key = f"context:{user_id}"
        if use_cache:
            cached = self._get_from_cache(cache_key)
            if cached:
                self._cache_hits += 1
                return ContextBundle(
                    bundle_id=bundle_id,
                    user_id=user_id,
                    cache_hit=True,
                    collection_time_ms=(time.time() - start_time) * 1000,
                    **cached,
                )
        
        # Collect context
        bundle = await self._collect_context(user_id, context_types)
        bundle.bundle_id = bundle_id
        bundle.collection_time_ms = (time.time() - start_time) * 1000
        self._total_collection_time_ms += bundle.collection_time_ms
        
        # Cache the bundle
        if use_cache:
            self._set_cache(cache_key, bundle.model_dump())
        
        return bundle
    
    async def _collect_context(
        self,
        user_id: str,
        context_types: Optional[List[str]] = None,
    ) -> ContextBundle:
        """Collect context from providers."""
        import asyncio
        
        # Default temporal context
        now = datetime.utcnow()
        hour = now.hour
        if 6 <= hour < 12:
            time_of_day = "morning"
        elif 12 <= hour < 18:
            time_of_day = "afternoon"
        elif 18 <= hour < 22:
            time_of_day = "evening"
        else:
            time_of_day = "night"
        
        bundle = ContextBundle(
            bundle_id="",
            user_id=user_id,
            temporal=TemporalContext(
                timezone="America/Havana",
                is_weekend=now.weekday() >= 5,
                time_of_day=time_of_day,
            ),
        )
        
        # Collect other contexts in parallel if enabled
        if self.config.enable_parallel_collection:
            tasks = []
            
            if context_types is None or "personal" in context_types:
                tasks.append(self._collect_personal(user_id))
            if context_types is None or "spatial" in context_types:
                tasks.append(self._collect_spatial(user_id))
            if context_types is None or "device" in context_types:
                tasks.append(self._collect_device(user_id))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, PersonalContext):
                    bundle.personal = result
                elif isinstance(result, SpatialContext):
                    bundle.spatial = result
                elif isinstance(result, DeviceContext):
                    bundle.device = result
        else:
            if context_types is None or "personal" in context_types:
                bundle.personal = await self._collect_personal(user_id)
            if context_types is None or "spatial" in context_types:
                bundle.spatial = await self._collect_spatial(user_id)
            if context_types is None or "device" in context_types:
                bundle.device = await self._collect_device(user_id)
        
        return bundle
    
    async def _collect_personal(self, user_id: str) -> PersonalContext:
        """Collect personal context."""
        # Placeholder - would fetch from user service
        return PersonalContext(user_id=user_id)
    
    async def _collect_spatial(self, user_id: str) -> SpatialContext:
        """Collect spatial context."""
        # Placeholder - would fetch from location service
        return SpatialContext()
    
    async def _collect_device(self, user_id: str) -> DeviceContext:
        """Collect device context."""
        # Placeholder - would fetch from session data
        return DeviceContext()
    
    def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """Get value from cache."""
        entry = self._l1_cache.get(key)
        if entry:
            if entry.expires_at and entry.expires_at < datetime.utcnow():
                del self._l1_cache[key]
                return None
            entry.hit_count += 1
            return entry.value
        return None
    
    def _set_cache(self, key: str, value: Dict[str, Any]) -> None:
        """Set value in cache."""
        from datetime import timedelta
        
        entry = CacheEntry(
            key=key,
            value=value,
            level=ContextLevel.L1_MEMORY,
            expires_at=datetime.utcnow() + timedelta(seconds=self.config.l2_ttl_seconds),
        )
        self._l1_cache[key] = entry
    
    def invalidate_cache(self, user_id: str) -> None:
        """Invalidate cache for a user."""
        cache_key = f"context:{user_id}"
        self._l1_cache.pop(cache_key, None)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get engine metrics."""
        hit_rate = (
            self._cache_hits / self._total_requests * 100
            if self._total_requests > 0 else 0
        )
        avg_collection_time = (
            self._total_collection_time_ms / (self._total_requests - self._cache_hits)
            if (self._total_requests - self._cache_hits) > 0 else 0
        )
        
        return {
            "total_requests": self._total_requests,
            "cache_hits": self._cache_hits,
            "cache_hit_rate": hit_rate,
            "avg_collection_time_ms": avg_collection_time,
            "target_ttft_ms": self.config.target_ttft_ms,
            "meeting_target": avg_collection_time < self.config.target_ttft_ms,
        }
