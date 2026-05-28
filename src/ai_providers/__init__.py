"""
AI Providers Module for RICCO AI

Provider implementations and base classes for AI services.
Integrated from genui.

Supported Providers:
- OpenAI: GPT-4o, GPT-4o-mini, o1-preview, o1-mini
- Anthropic: Claude 3.5 Sonnet, Claude 3 Opus, Claude 3 Haiku
- OpenRouter: 200+ models including free Llama 3.1, Mistral, DeepSeek
- Local: Local model support for development
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

# OpenRouter Provider (full implementation)
from .providers.openrouter_provider_full import (
    OpenRouterProviderFull,
    OpenRouterProviderConfigExtra,
    create_openrouter_provider,
    quick_chat,
    quick_stream,
    register_openrouter_provider,
    MODEL_PRICING as OPENROUTER_MODEL_PRICING,
    MODEL_CONTEXT_LENGTHS as OPENROUTER_CONTEXT_LENGTHS,
    VISION_MODELS as OPENROUTER_VISION_MODELS,
    FUNCTION_CALLING_MODELS as OPENROUTER_FUNCTION_MODELS,
)

# OpenAI Provider
from .providers.openai_provider import OpenAIProvider

# Anthropic Provider
from .providers.anthropic_provider import AnthropicProvider

# Local Provider
from .providers.local_provider import LocalProvider

# Provider factory functions
def create_openai_provider(api_key: str = None, model: str = "gpt-4o"):
    """Create an OpenAI provider instance."""
    from .base import AIProviderConfig
    config = AIProviderConfig(api_key=api_key, model=model)
    return OpenAIProvider(config)

def create_anthropic_provider(api_key: str = None, model: str = "claude-3-5-sonnet-20241022"):
    """Create an Anthropic provider instance."""
    from .base import AIProviderConfig
    config = AIProviderConfig(api_key=api_key, model=model)
    return AnthropicProvider(config)

def create_local_provider(model: str = "local-model"):
    """Create a local provider instance for development."""
    from .base import AIProviderConfig
    config = AIProviderConfig(api_key="local", model=model)
    return LocalProvider(config)

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
    # OpenRouter Provider
    "OpenRouterProviderFull",
    "OpenRouterProviderConfigExtra",
    "create_openrouter_provider",
    "quick_chat",
    "quick_stream",
    "register_openrouter_provider",
    "OPENROUTER_MODEL_PRICING",
    "OPENROUTER_CONTEXT_LENGTHS",
    "OPENROUTER_VISION_MODELS",
    "OPENROUTER_FUNCTION_MODELS",
    # OpenAI Provider
    "OpenAIProvider",
    "create_openai_provider",
    # Anthropic Provider
    "AnthropicProvider",
    "create_anthropic_provider",
    # Local Provider
    "LocalProvider",
    "create_local_provider",
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

# Auto-register OpenRouter provider on import
register_openrouter_provider()
