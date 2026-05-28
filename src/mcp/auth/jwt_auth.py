"""
MCP Authentication Module

Provides JWT-based authentication for MCP (Model Context Protocol) servers.
Supports API key validation, JWT tokens, and rate limiting per client.
"""

from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import secrets
import logging
import json

try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False

try:
    from pydantic import BaseModel, Field
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    # Fallback: create a simple BaseModel
    class BaseModel:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)

logger = logging.getLogger(__name__)


class AuthMethod(str, Enum):
    """Authentication methods supported"""
    API_KEY = "api_key"
    JWT = "jwt"
    BEARER = "bearer"
    NONE = "none"


class AuthError(Exception):
    """Authentication error"""
    def __init__(self, message: str, code: str = "auth_error"):
        super().__init__(message)
        self.code = code


@dataclass
class MCPAuthConfig:
    """Configuration for MCP authentication"""
    enabled: bool = True
    method: AuthMethod = AuthMethod.JWT
    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24
    api_keys: List[str] = field(default_factory=list)
    require_https: bool = True
    rate_limit_per_minute: int = 60
    
    def __post_init__(self):
        if not self.jwt_secret:
            self.jwt_secret = secrets.token_urlsafe(32)
            logger.warning("JWT secret auto-generated. Set MCP_JWT_SECRET for production.")


@dataclass
class AuthToken:
    """Represents an authenticated token"""
    client_id: str
    issued_at: datetime
    expires_at: datetime
    scopes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at
    
    def has_scope(self, scope: str) -> bool:
        return scope in self.scopes or "*" in self.scopes


if PYDANTIC_AVAILABLE:
    class TokenRequest(BaseModel):
        """Request for a new token"""
        client_id: str = Field(..., min_length=1, max_length=100)
        api_key: str = Field(..., min_length=1)
        scopes: List[str] = Field(default_factory=list)
    
    class TokenResponse(BaseModel):
        """Response with a new token"""
        access_token: str
        token_type: str = "Bearer"
        expires_in: int
        scopes: List[str]
else:
    class TokenRequest:
        def __init__(self, client_id: str, api_key: str, scopes: List[str] = None):
            self.client_id = client_id
            self.api_key = api_key
            self.scopes = scopes or []
    
    class TokenResponse:
        def __init__(self, access_token: str, expires_in: int, scopes: List[str]):
            self.access_token = access_token
            self.token_type = "Bearer"
            self.expires_in = expires_in
            self.scopes = scopes


class MCPAuthenticator:
    """
    Authenticator for MCP protocol.
    
    Supports multiple authentication methods:
    - API Key: Simple key-based authentication
    - JWT: Token-based authentication with expiration
    - Bearer: OAuth-style bearer tokens
    
    Example:
        ```python
        auth = MCPAuthenticator(config)
        
        # Validate token
        token = auth.validate_token(request.headers.get("Authorization"))
        
        # Generate new token
        token_response = auth.generate_token(client_id="client_1", api_key="key_123")
        ```
    """
    
    def __init__(self, config: Optional[MCPAuthConfig] = None):
        self.config = config or MCPAuthConfig()
        self._tokens: Dict[str, AuthToken] = {}
        self._rate_limits: Dict[str, List[datetime]] = {}
    
    def validate_request(
        self,
        authorization_header: Optional[str],
        api_key_header: Optional[str] = None,
    ) -> AuthToken:
        """
        Validate an incoming request.
        
        Args:
            authorization_header: The Authorization header value
            api_key_header: Optional X-API-Key header value
            
        Returns:
            AuthToken if validation succeeds
            
        Raises:
            AuthError if validation fails
        """
        if not self.config.enabled:
            return self._create_anonymous_token()
        
        # Try Bearer token first
        if authorization_header:
            if authorization_header.startswith("Bearer "):
                token = authorization_header[7:]
                return self.validate_token(token)
            
            # Try API key in Authorization header
            return self._validate_api_key(authorization_header)
        
        # Try API key header
        if api_key_header:
            return self._validate_api_key(api_key_header)
        
        raise AuthError("No authentication credentials provided", "no_credentials")
    
    def validate_token(self, token: str) -> AuthToken:
        """
        Validate a JWT or API key token.
        
        Args:
            token: The token to validate
            
        Returns:
            AuthToken if valid
            
        Raises:
            AuthError if invalid or expired
        """
        if not self.config.enabled:
            return self._create_anonymous_token()
        
        # Check if it's a stored token (API key auth)
        if token in self._tokens:
            stored = self._tokens[token]
            if stored.is_expired():
                del self._tokens[token]
                raise AuthError("Token has expired", "token_expired")
            return stored
        
        # Try JWT validation
        if self.config.method in (AuthMethod.JWT, AuthMethod.BEARER):
            return self._validate_jwt(token)
        
        raise AuthError("Invalid token", "invalid_token")
    
    def _validate_jwt(self, token: str) -> AuthToken:
        """Validate a JWT token"""
        if not JWT_AVAILABLE:
            raise AuthError("JWT library not installed. Install with: pip install PyJWT", "jwt_not_available")
        
        try:
            payload = jwt.decode(
                token,
                self.config.jwt_secret,
                algorithms=[self.config.jwt_algorithm]
            )
            
            return AuthToken(
                client_id=payload.get("sub", "unknown"),
                issued_at=datetime.fromtimestamp(payload.get("iat", 0)),
                expires_at=datetime.fromtimestamp(payload.get("exp", 0)),
                scopes=payload.get("scopes", []),
                metadata=payload.get("metadata", {}),
            )
            
        except jwt.ExpiredSignatureError:
            raise AuthError("Token has expired", "token_expired")
        except jwt.InvalidTokenError as e:
            raise AuthError(f"Invalid token: {e}", "invalid_token")
    
    def _validate_api_key(self, api_key: str) -> AuthToken:
        """Validate an API key"""
        if api_key not in self.config.api_keys:
            # Hash the key for comparison if stored as hash
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            if key_hash not in self.config.api_keys:
                raise AuthError("Invalid API key", "invalid_api_key")
        
        # Create a token for this API key
        client_id = f"apikey_{hashlib.sha256(api_key.encode()).hexdigest()[:16]}"
        
        return AuthToken(
            client_id=client_id,
            issued_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=self.config.jwt_expiry_hours),
            scopes=["*"],
            metadata={"auth_method": "api_key"},
        )
    
    def generate_token(
        self,
        client_id: str,
        api_key: str,
        scopes: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TokenResponse:
        """
        Generate a new authentication token.
        
        Args:
            client_id: Client identifier
            api_key: API key for validation
            scopes: List of permission scopes
            metadata: Additional metadata
            
        Returns:
            TokenResponse with the new token
        """
        # Validate API key first
        if api_key not in self.config.api_keys:
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            if key_hash not in self.config.api_keys:
                raise AuthError("Invalid API key", "invalid_api_key")
        
        scopes = scopes or ["*"]
        metadata = metadata or {}
        expires_in = self.config.jwt_expiry_hours * 3600
        
        if self.config.method == AuthMethod.JWT and JWT_AVAILABLE:
            # Generate JWT token
            now = datetime.utcnow()
            payload = {
                "sub": client_id,
                "iat": int(now.timestamp()),
                "exp": int((now + timedelta(seconds=expires_in)).timestamp()),
                "scopes": scopes,
                "metadata": metadata,
            }
            
            token = jwt.encode(
                payload,
                self.config.jwt_secret,
                algorithm=self.config.jwt_algorithm
            )
            
        else:
            # Generate random token
            token = secrets.token_urlsafe(32)
            
            # Store the token
            self._tokens[token] = AuthToken(
                client_id=client_id,
                issued_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(seconds=expires_in),
                scopes=scopes,
                metadata=metadata,
            )
        
        return TokenResponse(
            access_token=token,
            expires_in=expires_in,
            scopes=scopes,
        )
    
    def revoke_token(self, token: str) -> bool:
        """Revoke a token"""
        if token in self._tokens:
            del self._tokens[token]
            return True
        return False
    
    def check_rate_limit(self, client_id: str) -> bool:
        """
        Check if client is within rate limits.
        
        Returns:
            True if within limits, False if exceeded
        """
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        
        # Get or create rate limit entry
        if client_id not in self._rate_limits:
            self._rate_limits[client_id] = []
        
        # Clean old entries
        self._rate_limits[client_id] = [
            ts for ts in self._rate_limits[client_id]
            if ts > minute_ago
        ]
        
        # Check limit
        if len(self._rate_limits[client_id]) >= self.config.rate_limit_per_minute:
            return False
        
        # Record this request
        self._rate_limits[client_id].append(now)
        return True
    
    def _create_anonymous_token(self) -> AuthToken:
        """Create an anonymous token for unauthenticated access"""
        return AuthToken(
            client_id="anonymous",
            issued_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1),
            scopes=["read"],
            metadata={"auth_method": "anonymous"},
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get authentication statistics"""
        return {
            "enabled": self.config.enabled,
            "method": self.config.method.value,
            "active_tokens": len(self._tokens),
            "rate_limited_clients": len([
                c for c, timestamps in self._rate_limits.items()
                if len(timestamps) >= self.config.rate_limit_per_minute
            ]),
        }


def create_auth_middleware(
    authenticator: MCPAuthenticator,
    exclude_paths: Optional[List[str]] = None,
) -> Callable:
    """
    Create a FastAPI middleware for MCP authentication.
    
    Args:
        authenticator: MCPAuthenticator instance
        exclude_paths: Paths to exclude from authentication
        
    Returns:
        Middleware function
    """
    exclude_paths = exclude_paths or ["/health", "/metrics", "/docs", "/openapi.json"]
    
    async def auth_middleware(request, call_next):
        # Skip excluded paths
        if any(request.url.path.startswith(p) for p in exclude_paths):
            return await call_next(request)
        
        # Get auth headers
        auth_header = request.headers.get("Authorization")
        api_key = request.headers.get("X-API-Key")
        
        try:
            # Validate
            token = authenticator.validate_request(auth_header, api_key)
            
            # Check rate limit
            if not authenticator.check_rate_limit(token.client_id):
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=429,
                    content={"error": "Rate limit exceeded", "code": "rate_limit"}
                )
            
            # Add token to request state
            request.state.auth_token = token
            
            return await call_next(request)
            
        except AuthError as e:
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=401,
                content={"error": str(e), "code": e.code}
            )
    
    return auth_middleware


# Convenience function
def get_authenticator(
    jwt_secret: Optional[str] = None,
    api_keys: Optional[List[str]] = None,
) -> MCPAuthenticator:
    """
    Get an MCPAuthenticator instance.
    
    Args:
        jwt_secret: Secret for JWT signing (optional, auto-generated if not provided)
        api_keys: List of valid API keys
        
    Returns:
        MCPAuthenticator instance
    """
    config = MCPAuthConfig(
        jwt_secret=jwt_secret or "",
        api_keys=api_keys or [],
    )
    return MCPAuthenticator(config)
