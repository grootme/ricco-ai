"""
RICCO AI Service - Core Configuration
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Application
    app_name: str = "RICCO AI Service"
    app_version: str = "2.0.0"
    debug: bool = False
    environment: str = "development"
    api_prefix: str = "/api/v1"
    secret_key: str = "change-in-production"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Security
    api_key_header: str = "X-API-Key"
    cors_origins: list[str] = ["*"]
    
    # OpenRouter
    openrouter_api_key: Optional[str] = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_default_model: str = "anthropic/claude-3-haiku"
    
    # OpenAI
    openai_api_key: Optional[str] = None
    openai_embedding_model: str = "text-embedding-3-small"
    
    # Embeddings
    embedding_provider: str = "openai"
    embedding_dimension: int = 1536
    
    # Vector Store
    vector_store_provider: str = "chromadb"
    chromadb_host: str = "localhost"
    chromadb_port: int = 8000
    
    # RAG
    rag_chunk_size: int = 1000
    rag_chunk_overlap: int = 200
    rag_top_k: int = 5
    rag_rerank_enabled: bool = True
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "ricco"
    postgres_password: str = "ricco_password"
    postgres_db: str = "ricco_ai"
    
    # Evo-ai (A2A Protocol)
    evoai_base_url: Optional[str] = None
    evoai_api_key: Optional[str] = None
    a2a_protocol_enabled: bool = True
    
    # TensorFlow
    tensorflow_enabled: bool = True
    tensorflow_gpu: bool = False
    
    # Flowise
    flowise_base_url: Optional[str] = None
    flowise_api_key: Optional[str] = None
    
    # n8n
    n8n_base_url: Optional[str] = None
    n8n_api_key: Optional[str] = None
    
    # Feature Flags
    enable_streaming: bool = True
    enable_tensorflow: bool = True
    enable_a2a: bool = True
    
    # RICCO
    ricco_id_url: str = "http://localhost:3000"
    ricco_shared_secret: str = "change-in-production"
    
    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
