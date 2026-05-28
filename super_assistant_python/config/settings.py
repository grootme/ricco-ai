"""
Configuración central del Super Asistente con Capital Cognitivo.
Basado en patrones de NVIDIA NeMo Agent Toolkit y LangGraph.
"""

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings
from enum import Enum
from functools import lru_cache


class LLMProvider(str, Enum):
    """Proveedores de LLM soportados."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    NVIDIA_NIM = "nvidia_nim"
    OLLAMA = "ollama"
    AZURE_OPENAI = "azure_openai"
    GROQ = "groq"
    DEEPSEEK = "deepseek"


class MemoryBackend(str, Enum):
    """Backends de memoria soportados."""
    MEM0 = "mem0"
    QDRANT = "qdrant"
    POSTGRES = "postgres"
    SQLITE = "sqlite"
    REDIS = "redis"


class VectorStoreType(str, Enum):
    """Tipos de vector store soportados."""
    QDRANT = "qdrant"
    MILVUS = "milvus"
    PGVECTOR = "pgvector"
    FAISS = "faiss"
    CHROMA = "chroma"


class LLMConfig(BaseModel):
    """Configuración de LLM."""
    provider: LLMProvider = LLMProvider.OPENAI
    model_name: str = "gpt-4-turbo-preview"
    temperature: float = 0.7
    max_tokens: int = 4096
    api_key: Optional[SecretStr] = None
    base_url: Optional[str] = None
    
    # Configuración de retry
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Configuración de streaming
    streaming: bool = True
    
    class Config:
        use_enum_values = True


class MemoryConfig(BaseModel):
    """Configuración del sistema de memoria."""
    backend: MemoryBackend = MemoryBackend.MEM0
    vector_store: VectorStoreType = VectorStoreType.QDRANT
    
    # Configuración de Mem0
    mem0_api_key: Optional[SecretStr] = None
    mem0_org_id: Optional[str] = None
    mem0_project_id: Optional[str] = None
    
    # Configuración de vector store
    vector_store_url: Optional[str] = None
    vector_store_collection: str = "super_assistant_memory"
    
    # Configuración de memoria
    short_term_limit: int = 10  # Últimos N mensajes
    long_term_top_k: int = 5    # Top K memorias relevantes
    enable_entity_extraction: bool = True
    
    class Config:
        use_enum_values = True


class GuardrailsConfig(BaseModel):
    """Configuración de guardrails de seguridad."""
    enabled: bool = True
    
    # Rails de entrada
    input_rails: List[str] = Field(
        default_factory=lambda: [
            "check_jailbreak",
            "check_content_safety",
            "mask_sensitive_data"
        ]
    )
    
    # Rails de salida
    output_rails: List[str] = Field(
        default_factory=lambda: [
            "check_content_safety",
            "check_facts"
        ]
    )
    
    # Rails de herramientas
    tool_input_rails: List[str] = Field(
        default_factory=lambda: ["validate_arguments"]
    )
    tool_output_rails: List[str] = Field(
        default_factory=lambda: ["validate_results"]
    )
    
    # Configuración de ejecución
    parallel_rails: bool = True
    fail_fast: bool = True


class HITLConfig(BaseModel):
    """Configuración de Human-in-the-Loop."""
    enabled: bool = True
    
    # Tipos de interacción
    allow_interruption: bool = True
    require_approval_for_tools: List[str] = Field(default_factory=list)
    require_approval_for_actions: List[str] = Field(
        default_factory=lambda: [
            "delete_data",
            "send_email",
            "execute_code",
            "modify_files"
        ]
    )
    
    # Timeout para respuesta humana
    human_timeout_seconds: int = 300
    
    # Configuración de notificaciones
    notification_channels: List[str] = Field(default_factory=list)


class SubagentConfig(BaseModel):
    """Configuración de un subagente."""
    name: str
    role: str
    goal: str
    backstory: str
    tools: List[str] = Field(default_factory=list)
    max_iterations: int = 10
    verbose: bool = False
    enable_memory: bool = True
    llm_config: Optional[LLMConfig] = None


class OrchestrationConfig(BaseModel):
    """Configuración de orquestación de agentes."""
    # Tipo de orquestación
    use_hierarchical: bool = True
    max_subagent_calls: int = 5
    
    # Configuración de paralelismo
    enable_parallel_execution: bool = True
    max_parallel_tasks: int = 3
    
    # Timeout
    task_timeout_seconds: int = 300
    
    # Configuración de checkpointing
    enable_checkpointing: bool = True
    checkpoint_backend: str = "sqlite"


class Settings(BaseSettings):
    """Configuración principal del Super Asistente."""
    
    # Identificación
    app_name: str = "Super Assistant"
    app_version: str = "1.0.0"
    environment: str = "development"
    
    # LLM por defecto
    llm: LLMConfig = Field(default_factory=LLMConfig)
    
    # Memoria
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    
    # Seguridad
    guardrails: GuardrailsConfig = Field(default_factory=GuardrailsConfig)
    
    # Human-in-the-Loop
    hitl: HITLConfig = Field(default_factory=HITLConfig)
    
    # Orquestación
    orchestration: OrchestrationConfig = Field(default_factory=OrchestrationConfig)
    
    # Subagentes
    subagents: Dict[str, SubagentConfig] = Field(default_factory=dict)
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    
    # Base de datos
    database_url: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"
        use_enum_values = True


# Configuraciones de subagentes por defecto
DEFAULT_SUBAGENTS = {
    "researcher": SubagentConfig(
        name="Researcher",
        role="Investigador de Información",
        goal="Buscar, recopilar y sintetizar información relevante de múltiples fuentes",
        backstory="""Eres un investigador experto con acceso a múltiples fuentes de información.
        Tu especialidad es encontrar datos precisos, verificar fuentes y presentar 
        información de manera clara y estructurada.""",
        tools=["web_search", "document_retrieval", "knowledge_base_query"],
        max_iterations=15,
        enable_memory=True
    ),
    "analyzer": SubagentConfig(
        name="Analyzer",
        role="Analista de Datos",
        goal="Analizar datos, identificar patrones y generar insights accionables",
        backstory="""Eres un analista de datos senior con experiencia en múltiples dominios.
        Destacas en identificar patrones, anomalías y oportunidades a partir de datos complejos.""",
        tools=["data_analysis", "statistical_analysis", "visualization"],
        max_iterations=10,
        enable_memory=True
    ),
    "builder": SubagentConfig(
        name="Builder",
        role="Constructor de Soluciones",
        goal="Implementar, construir y desplegar soluciones técnicas",
        backstory="""Eres un ingeniero de software experto capaz de construir soluciones
        desde cero. Tienes experiencia en múltiples lenguajes y frameworks.""",
        tools=["code_generator", "file_operations", "shell_execute"],
        max_iterations=20,
        enable_memory=True
    ),
    "validator": SubagentConfig(
        name="Validator",
        role="Validador de Calidad",
        goal="Verificar, validar y asegurar la calidad de las soluciones",
        backstory="""Eres un especialista en QA con ojo crítico para detectar problemas.
        Tu trabajo es asegurar que todo funcione correctamente antes de entregar.""",
        tools=["test_runner", "code_review", "validation_check"],
        max_iterations=10,
        enable_memory=True
    ),
    "memory_keeper": SubagentConfig(
        name="MemoryKeeper",
        role="Guardián de Memoria",
        goal="Gestionar, organizar y recuperar información del sistema de memoria",
        backstory="""Eres el guardián del conocimiento acumulado. Tu trabajo es mantener
        la memoria organizada y accesible para todos los agentes.""",
        tools=["memory_store", "memory_retrieve", "memory_search"],
        max_iterations=5,
        enable_memory=True
    ),
    "security_guard": SubagentConfig(
        name="SecurityGuard",
        role="Guardián de Seguridad",
        goal="Proteger el sistema y validar operaciones sensibles",
        backstory="""Eres un especialista en seguridad que supervisa todas las operaciones
        sensibles. Tu trabajo es prevenir problemas de seguridad antes de que ocurran.""",
        tools=["security_scan", "permission_check", "audit_log"],
        max_iterations=5,
        enable_memory=True
    )
}


@lru_cache()
def get_settings() -> Settings:
    """Obtiene la configuración del Super Asistente (cached)."""
    settings = Settings()
    
    # Cargar subagentes por defecto si no están configurados
    if not settings.subagents:
        settings.subagents = DEFAULT_SUBAGENTS
    
    return settings


def configure_from_yaml(path: str) -> Settings:
    """Carga configuración desde un archivo YAML."""
    import yaml
    with open(path, 'r') as f:
        config_dict = yaml.safe_load(f)
    return Settings(**config_dict)


def configure_from_dict(config_dict: Dict[str, Any]) -> Settings:
    """Carga configuración desde un diccionario."""
    return Settings(**config_dict)
