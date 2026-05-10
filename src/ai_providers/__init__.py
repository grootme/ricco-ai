"""
AI Providers Module for RICCO AI

Provider implementations and base classes for AI services.
Integrated from genui.
"""

from .base import (
    AIProvider,
    AIProviderConfig,
    AIProviderFactory,
    AIGenerationOptions,
)
from .models import (
    AIProviderType,
    AIRequest,
    AIResponse,
    RecommendationType,
    ConsultationStatus,
    RecommendationContext,
    ConsultationMessage,
    ConsultationSession,
    BusinessRecommendation,
    ProductRecommendation,
    PersonalizedFeed,
    AIQuotaInfo,
)

# Token Optimizer imports
from .token_optimizer import (
    OptimizationStrategy,
    TokenOptimizationConfig,
    TokenMetrics,
    CompressionStrategy,
    SemanticCacheStrategy,
    DeduplicationStrategy,
    ContextPruningStrategy,
    AdaptiveStrategy,
    OptimizingLLMWrapper,
    TokenOptimizerService,
    TokenOptimizerFactory,
    SharedContextPool,
    count_tokens,
    create_token_optimizer,
)

__all__ = [
    # Base
    "AIProvider",
    "AIProviderConfig",
    "AIProviderFactory",
    "AIGenerationOptions",
    # Models
    "AIProviderType",
    "AIRequest",
    "AIResponse",
    "RecommendationType",
    "ConsultationStatus",
    "RecommendationContext",
    "ConsultationMessage",
    "ConsultationSession",
    "BusinessRecommendation",
    "ProductRecommendation",
    "PersonalizedFeed",
    "AIQuotaInfo",
    # Token Optimizer
    "OptimizationStrategy",
    "TokenOptimizationConfig",
    "TokenMetrics",
    "CompressionStrategy",
    "SemanticCacheStrategy",
    "DeduplicationStrategy",
    "ContextPruningStrategy",
    "AdaptiveStrategy",
    "OptimizingLLMWrapper",
    "TokenOptimizerService",
    "TokenOptimizerFactory",
    "SharedContextPool",
    "count_tokens",
    "create_token_optimizer",
]
