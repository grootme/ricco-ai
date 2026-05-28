"""
AI Provider Implementations

Provider implementations for OpenAI, Anthropic, and Local providers.
"""

# Import all providers for easy access
from .anthropic_provider import AnthropicProvider
from .local_provider import LocalProvider
from .openrouter_provider import OpenRouterProvider

# OpenAI provider has relative imports - import with try/except
try:
    from .openai_provider import OpenAIProvider
except ImportError:
    OpenAIProvider = None  # Will be available when imported with proper package context

__all__ = [
    "OpenAIProvider",
    "AnthropicProvider",
    "LocalProvider",
    "OpenRouterProvider",
]
