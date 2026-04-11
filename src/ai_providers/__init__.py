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
]
