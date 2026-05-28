"""
Super Asistente Cognitivo - Módulo LLM
======================================

Integración con proveedores de LLM usando z-ai-web-dev-sdk.

Soporta:
- OpenAI (GPT-4, GPT-4-turbo, etc.)
- Anthropic (Claude)
- Modelos locales vía Ollama
- NVIDIA NIM
"""

from .client import LLMClient, LLMConfig, LLMResponse
from .providers import OpenAIProvider, AnthropicProvider, LocalProvider
from .embeddings import EmbeddingClient

__all__ = [
    "LLMClient",
    "LLMConfig",
    "LLMResponse",
    "OpenAIProvider",
    "AnthropicProvider",
    "LocalProvider",
    "EmbeddingClient",
]
