"""
RICCO AI Configuration Settings
Extended from evo-ai with RICCO-specific settings
"""

import os
from pathlib import Path
from typing import Optional, List, Union
from pydantic_settings import BaseSettings
from pydantic import field_validator
import secrets
from dotenv import load_dotenv

# Load .env from project root
project_root = Path(__file__).parent.parent.parent
env_file = project_root / ".env"
load_dotenv(env_file)


class Settings(BaseSettings):
    """RICCO AI Settings"""

    # API
    API_TITLE: str = "RICCO AI"
    API_DESCRIPTION: str = "RICCO AI - Multi-agent orchestration with A2UI"
    API_VERSION: str = "2.0.0"
    API_URL: str = os.getenv("API_URL", "http://localhost:8000")

    # Organization
    ORGANIZATION_NAME: str = "RICCO"
    ORGANIZATION_URL: str = "https://ricco.com"

    # Database
    POSTGRES_CONNECTION_STRING: str = os.getenv(
        "POSTGRES_CONNECTION_STRING", 
        "postgresql://postgres:root@localhost:5432/ricco_ai"
    )
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL", None)  # For SQLite/other DBs

    # AI Engine (adk or crewai)
    AI_ENGINE: str = os.getenv("AI_ENGINE", "adk")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR: str = "logs"

    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB: int = int(os.getenv("REDIS_DB", 0))
    REDIS_PASSWORD: Optional[str] = os.getenv("REDIS_PASSWORD")
    REDIS_SSL: bool = os.getenv("REDIS_SSL", "false").lower() == "true"
    REDIS_KEY_PREFIX: str = "ricco_ai:"
    REDIS_TTL: int = 3600
    TOOLS_CACHE_TTL: int = 3600

    # JWT
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")  # MUST be set via environment
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_TIME: int = 3600
    
    # Production Mode
    PRODUCTION_MODE: bool = os.getenv("PRODUCTION_MODE", "false").lower() == "true"

    # Encryption
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", secrets.token_urlsafe(32))

    # Email
    EMAIL_PROVIDER: str = os.getenv("EMAIL_PROVIDER", "sendgrid")
    SENDGRID_API_KEY: str = os.getenv("SENDGRID_API_KEY", "")
    EMAIL_FROM: str = os.getenv("EMAIL_FROM", "noreply@ricco.com")
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_USE_TLS: bool = True

    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # CORS - Restricted for security
    CORS_ORIGINS: Union[str, List[str]] = "http://localhost:3000,http://localhost:8000"
    
    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return v.split(',')
        return v

    # Security
    TOKEN_EXPIRY_HOURS: int = 24
    PASSWORD_MIN_LENGTH: int = 8
    MAX_LOGIN_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_MINUTES: int = 30

    # Admin
    ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "admin@ricco.com")
    ADMIN_INITIAL_PASSWORD: str = os.getenv("ADMIN_INITIAL_PASSWORD", "")  # MUST be set in production

    # Observability
    LANGFUSE_PUBLIC_KEY: str = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    LANGFUSE_SECRET_KEY: str = os.getenv("LANGFUSE_SECRET_KEY", "")
    OTEL_EXPORTER_OTLP_ENDPOINT: str = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")

    # ========== RICCO ID Integration ==========
    RICCO_ID_URL: str = os.getenv("RICCO_ID_URL", "http://localhost:3000")
    RICCO_SHARED_SECRET: str = os.getenv("RICCO_SHARED_SECRET", "")
    RICCO_ID_JWT_ISSUER: str = os.getenv("RICCO_ID_JWT_ISSUER", "ricco-id")

    # ========== OpenRouter ==========
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    DEFAULT_MODEL: str = os.getenv("DEFAULT_MODEL", "anthropic/claude-3.5-sonnet")
    DEFAULT_MAX_TOKENS: int = 4096
    DEFAULT_TEMPERATURE: float = 0.7

    # ========== A2UI ==========
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    A2UI_CATALOG_VERSION: str = "v0_9"

    # ========== Vector Store ==========
    VECTOR_STORE_PROVIDER: str = os.getenv("VECTOR_STORE_PROVIDER", "chromadb")
    CHROMADB_HOST: str = os.getenv("CHROMADB_HOST", "localhost")
    CHROMADB_PORT: int = 8000
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")

    # ========== Embeddings ==========
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_DIMENSION: int = 1536

    # ========== RAG ==========
    RAG_CHUNK_SIZE: int = 500
    RAG_CHUNK_OVERLAP: int = 50
    RAG_TOP_K: int = 5

    # ========== Context Engineering ==========
    CONTEXT_MAX_TOKENS: int = 8000

    # ========== MCP Arsenal ==========
    MCP_SERVERS_DIR: str = os.getenv("MCP_SERVERS_DIR", "./mcp_servers")
    MCP_MAX_CONCURRENT: int = 10

    # ========== Feature Flags ==========
    ENABLE_STREAMING: bool = True
    ENABLE_A2A: bool = True
    ENABLE_A2UI: bool = True

    # ========== Rate Limiting ==========
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_DEFAULT_REQUESTS: int = int(os.getenv("RATE_LIMIT_DEFAULT_REQUESTS", 100))
    RATE_LIMIT_DEFAULT_WINDOW: int = int(os.getenv("RATE_LIMIT_DEFAULT_WINDOW", 60))
    RATE_LIMIT_AUTH_REQUESTS: int = int(os.getenv("RATE_LIMIT_AUTH_REQUESTS", 10))
    RATE_LIMIT_CHAT_REQUESTS: int = int(os.getenv("RATE_LIMIT_CHAT_REQUESTS", 30))
    RATE_LIMIT_API_KEY_REQUESTS: int = int(os.getenv("RATE_LIMIT_API_KEY_REQUESTS", 1000))

    # ========== Monitoring ==========
    MONITORING_ENABLED: bool = os.getenv("MONITORING_ENABLED", "true").lower() == "true"
    PROMETHEUS_ENABLED: bool = os.getenv("PROMETHEUS_ENABLED", "true").lower() == "true"
    METRICS_PATH: str = os.getenv("METRICS_PATH", "/metrics")
    JAEGER_ENABLED: bool = os.getenv("JAEGER_ENABLED", "false").lower() == "true"
    JAEGER_AGENT_HOST: str = os.getenv("JAEGER_AGENT_HOST", "localhost")
    JAEGER_AGENT_PORT: int = int(os.getenv("JAEGER_AGENT_PORT", 6831))

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "allow"  # Allow extra fields from .env
    }
    
    def validate_production_secrets(self) -> List[str]:
        """
        Validate that required secrets are set in production mode.
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        if self.PRODUCTION_MODE:
            if not self.JWT_SECRET_KEY:
                errors.append("JWT_SECRET_KEY must be set in production mode")
            if not self.ADMIN_INITIAL_PASSWORD:
                errors.append("ADMIN_INITIAL_PASSWORD must be set in production mode")
            if not self.ENCRYPTION_KEY:
                errors.append("ENCRYPTION_KEY must be set in production mode")
            if self.CORS_ORIGINS == "*":
                errors.append("CORS_ORIGINS should not be '*' in production mode")
        
        return errors


settings = Settings()


# RICCO Solutions Configuration
RICCO_SOLUTIONS = {
    "ricco-commerce": {
        "name": "RICCO Commerce",
        "domain": "commerce.ricco.com",
        "agents": ["commerce-assistant", "commerce-recommender"],
        "mcps": ["mcp-postgres", "mcp-redis", "mcp-stripe"]
    },
    "ricco-health": {
        "name": "RICCO Health",
        "domain": "health.ricco.com",
        "agents": ["health-assistant", "health-document-analyst"],
        "mcps": ["mcp-postgres", "mcp-redis", "mcp-calendar"]
    },
    "ricco-logistics": {
        "name": "RICCO Logistics",
        "domain": "logistics.ricco.com",
        "agents": ["logistics-assistant", "logistics-route-optimizer"],
        "mcps": ["mcp-postgres", "mcp-redis", "mcp-google-maps"]
    },
    "ricco-id": {
        "name": "RICCO ID",
        "domain": "id.ricco.com",
        "agents": ["id-assistant", "id-kyc-processor"],
        "mcps": ["mcp-postgres", "mcp-redis", "mcp-pdf"]
    },
    "ricco-finance": {
        "name": "RICCO Finance",
        "domain": "finance.ricco.com",
        "agents": ["finance-assistant", "finance-analyst"],
        "mcps": ["mcp-postgres", "mcp-redis", "mcp-qvapay"]
    },
}

# Model routes for OpenRouter
MODEL_ROUTES = {
    "fast": ("openai", "gpt-4o-mini", "quick responses"),
    "smart": ("anthropic", "claude-3.5-sonnet", "complex reasoning"),
    "creative": ("anthropic", "claude-3.5-sonnet", "creative writing"),
    "coding": ("anthropic", "claude-3.5-sonnet", "code generation"),
    "vision": ("anthropic", "claude-3.5-sonnet", "image analysis"),
    "claude-3.5-sonnet": ("anthropic", "claude-3.5-sonnet", "general"),
    "gpt-4o": ("openai", "gpt-4o", "general"),
    "gpt-4o-mini": ("openai", "gpt-4o-mini", "fast"),
    "llama-3.3-70b": ("meta", "llama-3.3-70b-instruct", "open source"),
    "gemini-pro": ("google", "gemini-1.5-pro", "general"),
}
