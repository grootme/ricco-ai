"""
Rate Limiting Middleware for RICCO AI
Supports Redis-based distributed rate limiting with multiple strategies
"""

import time
import hashlib
import asyncio
from typing import Callable, Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

from fastapi import Request, HTTPException, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class RateLimitStrategy(Enum):
    """Rate limiting strategies"""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"


@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    requests: int
    window_seconds: int
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    key_prefix: str = "rate_limit"
    block_duration: int = 0  # 0 = no block, >0 = block for N seconds after limit exceeded


@dataclass
class RateLimitResult:
    """Result of rate limit check"""
    allowed: bool
    remaining: int
    reset_at: float
    retry_after: Optional[int] = None
    blocked: bool = False


class InMemoryStore:
    """In-memory rate limit store for development/fallback"""
    
    def __init__(self):
        self._store: Dict[str, List[float]] = {}
        self._blocks: Dict[str, float] = {}
    
    async def get_requests(self, key: str, window_start: float) -> List[float]:
        """Get requests within window"""
        if key not in self._store:
            return []
        return [ts for ts in self._store[key] if ts >= window_start]
    
    async def add_request(self, key: str, timestamp: float) -> None:
        """Add a request timestamp"""
        if key not in self._store:
            self._store[key] = []
        self._store[key].append(timestamp)
    
    async def is_blocked(self, key: str) -> bool:
        """Check if key is blocked"""
        if key not in self._blocks:
            return False
        if self._blocks[key] < time.time():
            del self._blocks[key]
            return False
        return True
    
    async def set_block(self, key: str, duration: int) -> None:
        """Block a key for duration seconds"""
        self._blocks[key] = time.time() + duration
    
    async def cleanup(self, max_age: int = 3600) -> None:
        """Cleanup old entries"""
        cutoff = time.time() - max_age
        for key in list(self._store.keys()):
            self._store[key] = [ts for ts in self._store[key] if ts >= cutoff]
            if not self._store[key]:
                del self._store[key]


class RedisStore:
    """Redis-based distributed rate limit store"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def get_requests(self, key: str, window_start: float) -> List[float]:
        """Get requests within window using Redis sorted set"""
        members = await self.redis.zrangebyscore(key, window_start, "+inf")
        return [float(m.decode()) for m in members]
    
    async def add_request(self, key: str, timestamp: float) -> None:
        """Add a request timestamp to Redis sorted set"""
        pipe = self.redis.pipeline()
        pipe.zadd(key, {str(timestamp): timestamp})
        pipe.expire(key, 3600)  # 1 hour TTL
        await pipe.execute()
    
    async def is_blocked(self, block_key: str) -> bool:
        """Check if key is blocked"""
        ttl = await self.redis.ttl(block_key)
        return ttl > 0
    
    async def set_block(self, block_key: str, duration: int) -> None:
        """Block a key for duration seconds"""
        await self.redis.setex(block_key, duration, "1")
    
    async def get_remaining(self, key: str, window_start: float, limit: int) -> int:
        """Get remaining requests"""
        count = await self.redis.zcount(key, window_start, "+inf")
        return max(0, limit - count)


class RateLimiter:
    """
    Advanced Rate Limiter with multiple strategies
    """
    
    def __init__(
        self,
        redis_url: Optional[str] = None,
        default_config: Optional[RateLimitConfig] = None,
    ):
        self.store: Any = None
        self.redis_client: Optional[redis.Redis] = None
        self.default_config = default_config or RateLimitConfig(
            requests=100,
            window_seconds=60,
            strategy=RateLimitStrategy.SLIDING_WINDOW
        )
        
        # Route-specific configurations
        self.route_configs: Dict[str, RateLimitConfig] = {}
        
        # Initialize store
        if redis_url and REDIS_AVAILABLE:
            self._init_redis(redis_url)
        else:
            self.store = InMemoryStore()
    
    def _init_redis(self, redis_url: str) -> None:
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(redis_url)
            self.store = RedisStore(self.redis_client)
        except Exception:
            self.store = InMemoryStore()
    
    def configure_route(self, route: str, config: RateLimitConfig) -> None:
        """Configure rate limit for a specific route"""
        self.route_configs[route] = config
    
    def _get_config(self, route: str) -> RateLimitConfig:
        """Get config for a route"""
        for pattern, config in self.route_configs.items():
            if route.startswith(pattern):
                return config
        return self.default_config
    
    def _generate_key(self, request: Request, config: RateLimitConfig) -> str:
        """Generate rate limit key from request"""
        # Get client identifier
        client_id = self._get_client_id(request)
        route = request.url.path
        
        # Create hash for key
        key_data = f"{config.key_prefix}:{client_id}:{route}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:32]
    
    def _get_client_id(self, request: Request) -> str:
        """Extract client identifier from request"""
        # Try various sources
        headers = request.headers
        
        # API Key
        api_key = headers.get("X-API-Key") or headers.get("Authorization", "").replace("Bearer ", "")
        if api_key:
            return f"api:{hashlib.sha256(api_key.encode()).hexdigest()[:16]}"
        
        # User ID from state
        if hasattr(request.state, "user_id"):
            return f"user:{request.state.user_id}"
        
        # Session ID
        session_id = headers.get("X-Session-ID")
        if session_id:
            return f"session:{session_id}"
        
        # IP address fallback
        forwarded = headers.get("X-Forwarded-For")
        if forwarded:
            return f"ip:{forwarded.split(',')[0].strip()}"
        
        client_host = request.client.host if request.client else "unknown"
        return f"ip:{client_host}"
    
    async def check_rate_limit(
        self,
        request: Request,
        config: Optional[RateLimitConfig] = None
    ) -> RateLimitResult:
        """Check if request is within rate limit"""
        route = request.url.path
        config = config or self._get_config(route)
        key = self._generate_key(request, config)
        block_key = f"{key}:blocked"
        
        # Check if blocked
        if await self.store.is_blocked(block_key):
            ttl = await self._get_block_ttl(block_key)
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_at=time.time() + (ttl or 60),
                retry_after=ttl,
                blocked=True
            )
        
        now = time.time()
        window_start = now - config.window_seconds
        
        # Strategy-specific implementation
        if config.strategy == RateLimitStrategy.SLIDING_WINDOW:
            return await self._sliding_window_check(key, config, now, window_start)
        elif config.strategy == RateLimitStrategy.FIXED_WINDOW:
            return await self._fixed_window_check(key, config, now)
        elif config.strategy == RateLimitStrategy.TOKEN_BUCKET:
            return await self._token_bucket_check(key, config, now)
        else:
            return await self._sliding_window_check(key, config, now, window_start)
    
    async def _sliding_window_check(
        self,
        key: str,
        config: RateLimitConfig,
        now: float,
        window_start: float
    ) -> RateLimitResult:
        """Sliding window rate limit check"""
        requests = await self.store.get_requests(key, window_start)
        
        if len(requests) >= config.requests:
            if config.block_duration > 0:
                await self.store.set_block(f"{key}:blocked", config.block_duration)
            
            oldest = min(requests) if requests else now
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_at=oldest + config.window_seconds,
                retry_after=int(oldest + config.window_seconds - now)
            )
        
        await self.store.add_request(key, now)
        return RateLimitResult(
            allowed=True,
            remaining=config.requests - len(requests) - 1,
            reset_at=now + config.window_seconds
        )
    
    async def _fixed_window_check(
        self,
        key: str,
        config: RateLimitConfig,
        now: float
    ) -> RateLimitResult:
        """Fixed window rate limit check"""
        window_start = int(now / config.window_seconds) * config.window_seconds
        requests = await self.store.get_requests(key, window_start)
        
        if len(requests) >= config.requests:
            reset_at = window_start + config.window_seconds
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_at=reset_at,
                retry_after=int(reset_at - now)
            )
        
        await self.store.add_request(key, now)
        return RateLimitResult(
            allowed=True,
            remaining=config.requests - len(requests) - 1,
            reset_at=window_start + config.window_seconds
        )
    
    async def _token_bucket_check(
        self,
        key: str,
        config: RateLimitConfig,
        now: float
    ) -> RateLimitResult:
        """Token bucket rate limit check"""
        bucket_key = f"{key}:bucket"
        
        # Get current tokens (simplified implementation)
        requests = await self.store.get_requests(key, now - config.window_seconds)
        tokens = max(0, config.requests - len(requests))
        
        # Refill tokens based on time elapsed
        refill_rate = config.requests / config.window_seconds
        
        if tokens <= 0:
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_at=now + (1 / refill_rate),
                retry_after=int(1 / refill_rate)
            )
        
        await self.store.add_request(key, now)
        return RateLimitResult(
            allowed=True,
            remaining=tokens - 1,
            reset_at=now + config.window_seconds
        )
    
    async def _get_block_ttl(self, block_key: str) -> Optional[int]:
        """Get TTL for blocked key"""
        if isinstance(self.store, RedisStore) and self.redis_client:
            return await self.redis_client.ttl(block_key)
        return 60  # Default block duration


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI Middleware for Rate Limiting
    """
    
    def __init__(
        self,
        app: ASGIApp,
        rate_limiter: RateLimiter,
        excluded_paths: Optional[List[str]] = None,
        on_rate_limit_exceeded: Optional[Callable] = None,
    ):
        super().__init__(app)
        self.rate_limiter = rate_limiter
        self.excluded_paths = excluded_paths or ["/health", "/docs", "/openapi.json", "/"]
        self.on_rate_limit_exceeded = on_rate_limit_exceeded
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting"""
        # Skip excluded paths
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)
        
        # Check rate limit
        result = await self.rate_limiter.check_rate_limit(request)
        
        if not result.allowed:
            # Call custom handler if provided
            if self.on_rate_limit_exceeded:
                return await self.on_rate_limit_exceeded(request, result)
            
            # Default response
            return JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": result.retry_after,
                    "blocked": result.blocked
                },
                headers={
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(result.reset_at)),
                    "Retry-After": str(result.retry_after or 60)
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Remaining"] = str(result.remaining)
        response.headers["X-RateLimit-Reset"] = str(int(result.reset_at))
        
        return response


# Convenience functions
def setup_rate_limiting(
    app,
    redis_url: Optional[str] = None,
    default_requests: int = 100,
    default_window: int = 60,
    route_configs: Optional[Dict[str, RateLimitConfig]] = None,
    excluded_paths: Optional[List[str]] = None,
) -> RateLimiter:
    """
    Setup rate limiting for a FastAPI application
    
    Args:
        app: FastAPI application
        redis_url: Redis connection URL (optional, falls back to in-memory)
        default_requests: Default number of requests per window
        default_window: Default window size in seconds
        route_configs: Route-specific configurations
        excluded_paths: Paths to exclude from rate limiting
    
    Returns:
        RateLimiter instance
    """
    default_config = RateLimitConfig(
        requests=default_requests,
        window_seconds=default_window,
        strategy=RateLimitStrategy.SLIDING_WINDOW
    )
    
    rate_limiter = RateLimiter(
        redis_url=redis_url,
        default_config=default_config
    )
    
    # Configure route-specific limits
    if route_configs:
        for route, config in route_configs.items():
            rate_limiter.configure_route(route, config)
    
    # Add middleware
    app.add_middleware(
        RateLimitMiddleware,
        rate_limiter=rate_limiter,
        excluded_paths=excluded_paths
    )
    
    return rate_limiter


# Pre-configured rate limit profiles
RATE_LIMIT_PROFILES = {
    "strict": RateLimitConfig(requests=10, window_seconds=60),
    "standard": RateLimitConfig(requests=100, window_seconds=60),
    "relaxed": RateLimitConfig(requests=1000, window_seconds=60),
    "api_key": RateLimitConfig(requests=10000, window_seconds=3600),
    "auth": RateLimitConfig(
        requests=5,
        window_seconds=60,
        block_duration=300  # Block for 5 minutes after exceeding
    ),
    "chat": RateLimitConfig(requests=30, window_seconds=60),
    "streaming": RateLimitConfig(requests=10, window_seconds=60),
}
