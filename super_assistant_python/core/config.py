"""
Super Asistente Cognitivo - Configuración
=========================================

Configuración centralizada usando Pydantic Settings.
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configuración principal del sistema"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # ============================================
    # APPLICATION
    # ============================================
    app_name: str = "Super Assistant Cognitive"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"
    
    # ============================================
    # API
    # ============================================
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    
    # ============================================
    # DATABASE - SQLite
    # ============================================
    sqlite_db_path: str = "data/super_assistant.db"
    
    # ============================================
    # DATABASE - Neo4j (Grafo de Conocimiento)
    # ============================================
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    neo4j_database: str = "neo4j"
    
    # ============================================
    # DATABASE - Milvus (Vector Store)
    # ============================================
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_collection: str = "cognitive_memory"
    
    # ============================================
    # LLM PROVIDERS
    # ============================================
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4"
    openai_embedding_model: str = "text-embedding-3-small"
    
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-3-opus-20240229"
    
    # Modelos locales (Ollama, vLLM, etc.)
    local_llm_host: str = "http://localhost:11434"
    local_llm_model: str = "llama2"
    
    # ============================================
    # EMBEDDINGS
    # ============================================
    embedding_provider: str = "openai"  # openai, sentence-transformers, local
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536
    
    # ============================================
    # SANDBOX
    # ============================================
    sandbox_enabled: bool = True
    sandbox_docker_image: str = "python:3.11-slim"
    sandbox_timeout: int = 60  # segundos
    sandbox_memory_limit: str = "512m"
    sandbox_cpu_limit: float = 1.0
    
    # ============================================
    # HITL (Human-in-the-Loop)
    # ============================================
    hitl_enabled: bool = True
    hitl_timeout: int = 3600  # 1 hora
    
    # Slack
    slack_bot_token: Optional[str] = None
    slack_signing_secret: Optional[str] = None
    slack_channel: str = "#approvals"
    
    # Telegram
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    
    # ============================================
    # MONITORING
    # ============================================
    prometheus_enabled: bool = True
    prometheus_port: int = 9090
    
    jaeger_enabled: bool = False
    jaeger_host: str = "localhost"
    jaeger_port: int = 6831
    
    # ============================================
    # MEMORY
    # ============================================
    memory_session_ttl: int = 3600  # 1 hora
    memory_episodic_ttl: int = 86400 * 7  # 7 días
    memory_max_context_tokens: int = 4096
    
    # ============================================
    # AUTO-IMPROVEMENT
    # ============================================
    auto_improve_enabled: bool = True
    auto_improve_interval: int = 3600  # 1 hora
    auto_improve_min_samples: int = 100
    
    # ============================================
    # SKILLS
    # ============================================
    skills_local_path: str = "skills/local"
    skills_remote_cache_path: str = "skills/remote_cache"
    
    # Repositorios remotos
    deerflow_repo: str = "https://github.com/bytedance/deer-flow"
    langchain_hub_url: str = "https://api.hub.langchain.com"
    
    @property
    def database_url(self) -> str:
        """URL de la base de datos SQLite"""
        return f"sqlite+aiosqlite:///{self.sqlite_db_path}"
    
    @property
    def is_production(self) -> bool:
        """Verificar si es ambiente de producción"""
        return self.environment == "production"


@lru_cache()
def get_settings() -> Settings:
    """Obtener configuración (cached)"""
    return Settings()


# Alias para importación fácil
settings = get_settings()
