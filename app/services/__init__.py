"""
RICCO AI Service - Services Module
"""

from app.services.openrouter_service import (
    OpenRouterService,
    get_openrouter_service,
)
from app.services.rag_service import (
    RAGService,
    EmbeddingService,
    VectorStoreService,
    RerankerService,
    get_rag_service,
    get_embedding_service,
)
from app.services.kyc_service import (
    KYCService,
    KYBService,
    get_kyc_service,
    get_kyb_service,
)
from app.services.flowise_service import (
    FlowiseService,
    get_flowise_service,
)
from app.services.n8n_service import (
    N8NService,
    get_n8n_service,
)
from app.services.evoai_service import (
    EvoAIService,
    get_evoai_service,
)
from app.services.tensorflow_service import (
    TensorFlowService,
    get_tensorflow_service,
)
from app.services.ricco_integration import (
    RICCOIntegrationHub,
    get_integration_hub,
)

__all__ = [
    # OpenRouter
    "OpenRouterService",
    "get_openrouter_service",
    
    # RAG
    "RAGService",
    "EmbeddingService",
    "VectorStoreService",
    "RerankerService",
    "get_rag_service",
    "get_embedding_service",
    
    # KYC/KYB
    "KYCService",
    "KYBService",
    "get_kyc_service",
    "get_kyb_service",
    
    # Flowise
    "FlowiseService",
    "get_flowise_service",
    
    # n8n
    "N8NService",
    "get_n8n_service",
    
    # Evo-ai
    "EvoAIService",
    "get_evoai_service",
    
    # TensorFlow
    "TensorFlowService",
    "get_tensorflow_service",
    
    # RICCO Integration
    "RICCOIntegrationHub",
    "get_integration_hub",
]
