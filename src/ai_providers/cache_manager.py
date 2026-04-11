"""
AI Response Cache Manager
Manages caching of AI responses with semantic similarity
"""

import hashlib
import json
import time
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
import logging

from .models import AIResponse, AIRequest

logger = logging.getLogger(__name__)


class AICacheManager:
    """
    Manager for caching AI responses
    
    Features:
    - Exact match caching
    - Semantic similarity matching
    - TTL-based expiration
    - Integration with GenUI cache
    """
    
    def __init__(
        self,
        redis_client=None,
        genui_cache_client=None,
        embedding_service=None,
        default_ttl: int = 300,
        similarity_threshold: float = 0.95
    ):
        self.redis = redis_client
        self.genui_cache = genui_cache_client
        self.embedding_service = embedding_service
        self.default_ttl = default_ttl
        self.similarity_threshold = similarity_threshold
        
        # In-memory cache for development
        self._memory_cache: Dict[str, Tuple[Dict[str, Any], float]] = {}
    
    def _generate_cache_key(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a cache key for a request"""
        # Normalize and hash the components
        components = {
            "prompt": prompt.strip().lower(),
            "context": context or {},
            "model": model or "default",
            "options": options or {},
        }
        
        # Sort keys for consistent hashing
        content = json.dumps(components, sort_keys=True, default=str)
        hash_value = hashlib.sha256(content.encode()).hexdigest()[:32]
        
        return f"ai_cache:{hash_value}"
    
    async def get(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None
    ) -> Optional[AIResponse]:
        """
        Get cached response if available
        
        Args:
            prompt: The input prompt
            context: Request context
            model: Model name
            options: Generation options
            
        Returns:
            Cached AIResponse or None
        """
        cache_key = self._generate_cache_key(prompt, context, model, options)
        
        # Try Redis cache first
        if self.redis:
            try:
                cached_data = await self.redis.get(cache_key)
                if cached_data:
                    data = json.loads(cached_data)
                    response = AIResponse(**data)
                    response.cached = True
                    response.cache_key = cache_key
                    logger.debug(f"Cache hit: {cache_key}")
                    return response
            except Exception as e:
                logger.warning(f"Redis cache get error: {e}")
        
        # Try memory cache
        if cache_key in self._memory_cache:
            data, expires_at = self._memory_cache[cache_key]
            if time.time() < expires_at:
                response = AIResponse(**data)
                response.cached = True
                response.cache_key = cache_key
                return response
            else:
                del self._memory_cache[cache_key]
        
        # Try semantic similarity search
        if self.embedding_service and self.redis:
            similar_response = await self._find_similar_cached(prompt, context, model)
            if similar_response:
                return similar_response
        
        return None
    
    async def set(
        self,
        response: AIResponse,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Cache a response
        
        Args:
            response: The AI response to cache
            prompt: Original prompt
            context: Request context
            model: Model name
            options: Generation options
            ttl: Time-to-live in seconds
            
        Returns:
            True if cached successfully
        """
        cache_key = self._generate_cache_key(prompt, context, model, options)
        ttl = ttl or self.default_ttl
        
        response_data = response.model_dump()
        response_data["cache_key"] = cache_key
        
        # Cache in Redis
        if self.redis:
            try:
                await self.redis.setex(
                    cache_key,
                    ttl,
                    json.dumps(response_data, default=str)
                )
                
                # Also store embedding for similarity search
                if self.embedding_service:
                    embedding = await self.embedding_service.get_embedding(prompt)
                    await self._store_embedding(cache_key, embedding, ttl)
                
                logger.debug(f"Cached response: {cache_key}")
                return True
                
            except Exception as e:
                logger.error(f"Redis cache set error: {e}")
        
        # Fallback to memory cache
        self._memory_cache[cache_key] = (response_data, time.time() + ttl)
        
        return True
    
    async def invalidate(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        model: Optional[str] = None
    ) -> bool:
        """Invalidate a cached response"""
        cache_key = self._generate_cache_key(prompt, context, model)
        
        if self.redis:
            try:
                await self.redis.delete(cache_key)
                await self._delete_embedding(cache_key)
                return True
            except Exception as e:
                logger.error(f"Cache invalidation error: {e}")
        
        if cache_key in self._memory_cache:
            del self._memory_cache[cache_key]
        
        return True
    
    async def clear_all(self, pattern: str = "ai_cache:*") -> int:
        """Clear all cached responses matching pattern"""
        count = 0
        
        if self.redis:
            try:
                keys = await self.redis.keys(pattern)
                if keys:
                    count = await self.redis.delete(*keys)
            except Exception as e:
                logger.error(f"Cache clear error: {e}")
        
        # Clear memory cache
        keys_to_delete = [k for k in self._memory_cache if k.startswith(pattern.replace("*", ""))]
        for key in keys_to_delete:
            del self._memory_cache[key]
            count += 1
        
        return count
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        stats = {
            "memory_cache_size": len(self._memory_cache),
            "redis_available": self.redis is not None,
            "embedding_service_available": self.embedding_service is not None,
        }
        
        if self.redis:
            try:
                # Get count of AI cache keys
                keys = await self.redis.keys("ai_cache:*")
                stats["redis_cache_size"] = len(keys)
                
                # Get memory usage if available
                info = await self.redis.info("memory")
                stats["redis_memory_used"] = info.get("used_memory_human", "unknown")
            except Exception:
                stats["redis_cache_size"] = "unknown"
        
        return stats
    
    async def _find_similar_cached(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]],
        model: Optional[str]
    ) -> Optional[AIResponse]:
        """Find a similar cached response using embeddings"""
        if not self.embedding_service or not self.redis:
            return None
        
        try:
            # Get embedding for current prompt
            query_embedding = await self.embedding_service.get_embedding(prompt)
            
            # Search for similar embeddings
            similar_keys = await self._search_similar_embeddings(query_embedding, limit=5)
            
            for key, similarity in similar_keys:
                if similarity >= self.similarity_threshold:
                    # Get the cached response
                    cached_data = await self.redis.get(key)
                    if cached_data:
                        data = json.loads(cached_data)
                        response = AIResponse(**data)
                        response.cached = True
                        response.cache_key = key
                        logger.info(f"Found similar cached response (similarity: {similarity:.2f})")
                        return response
                        
        except Exception as e:
            logger.warning(f"Similarity search error: {e}")
        
        return None
    
    async def _store_embedding(
        self,
        cache_key: str,
        embedding: List[float],
        ttl: int
    ) -> None:
        """Store embedding for similarity search"""
        if not self.redis:
            return
        
        embedding_key = f"ai_embedding:{cache_key.split(':')[-1]}"
        
        try:
            # Store as JSON array
            await self.redis.setex(
                embedding_key,
                ttl,
                json.dumps({
                    "embedding": embedding,
                    "cache_key": cache_key,
                    "created_at": datetime.utcnow().isoformat(),
                })
            )
        except Exception as e:
            logger.warning(f"Failed to store embedding: {e}")
    
    async def _delete_embedding(self, cache_key: str) -> None:
        """Delete embedding when invalidating cache"""
        if not self.redis:
            return
        
        embedding_key = f"ai_embedding:{cache_key.split(':')[-1]}"
        
        try:
            await self.redis.delete(embedding_key)
        except Exception:
            pass
    
    async def _search_similar_embeddings(
        self,
        query_embedding: List[float],
        limit: int = 5
    ) -> List[Tuple[str, float]]:
        """Search for similar embeddings in cache"""
        if not self.redis:
            return []
        
        similar = []
        
        try:
            # Get all embedding keys
            embedding_keys = await self.redis.keys("ai_embedding:*")
            
            for key in embedding_keys[:100]:  # Limit search for performance
                try:
                    data = await self.redis.get(key)
                    if data:
                        embedding_data = json.loads(data)
                        stored_embedding = embedding_data.get("embedding", [])
                        cache_key = embedding_data.get("cache_key", "")
                        
                        if stored_embedding and cache_key:
                            # Calculate cosine similarity
                            similarity = self._cosine_similarity(query_embedding, stored_embedding)
                            similar.append((cache_key, similarity))
                except Exception:
                    continue
            
            # Sort by similarity and return top results
            similar.sort(key=lambda x: x[1], reverse=True)
            return similar[:limit]
            
        except Exception as e:
            logger.error(f"Embedding search error: {e}")
            return []
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        if len(a) != len(b):
            return 0.0
        
        dot_product = sum(x * y for x, y in zip(a, b))
        magnitude_a = sum(x * x for x in a) ** 0.5
        magnitude_b = sum(x * x for x in b) ** 0.5
        
        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0
        
        return dot_product / (magnitude_a * magnitude_b)
    
    # GenUI integration methods
    
    async def get_genui_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached GenUI UI generation"""
        if self.genui_cache:
            try:
                return await self.genui_cache.get(f"genui:{key}")
            except Exception:
                pass
        return None
    
    async def set_genui_cache(
        self,
        key: str,
        value: Dict[str, Any],
        ttl: int = 3600
    ) -> bool:
        """Cache GenUI UI generation"""
        if self.genui_cache:
            try:
                await self.genui_cache.setex(f"genui:{key}", ttl, json.dumps(value))
                return True
            except Exception:
                pass
        return False
    
    async def get_a2ui_component(
        self,
        component_id: str,
        context_hash: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached A2UI component"""
        key = f"a2ui:component:{component_id}:{context_hash}"
        
        if self.redis:
            try:
                cached = await self.redis.get(key)
                if cached:
                    return json.loads(cached)
            except Exception:
                pass
        
        return None
    
    async def set_a2ui_component(
        self,
        component_id: str,
        context_hash: str,
        component_data: Dict[str, Any],
        ttl: int = 1800
    ) -> bool:
        """Cache A2UI component"""
        key = f"a2ui:component:{component_id}:{context_hash}"
        
        if self.redis:
            try:
                await self.redis.setex(key, ttl, json.dumps(component_data))
                return True
            except Exception:
                pass
        
        return False
