"""
OpenRouter Service - High-level service for OpenRouter integration

This service provides a unified interface for using OpenRouter across
the RICCO AI platform. It handles:
- Model selection based on task type
- Automatic fallback to free models
- Cost optimization
- Rate limiting
- Caching
"""

import logging
from typing import Optional, Dict, Any, List, AsyncIterator
from dataclasses import dataclass
from enum import Enum

from .providers.openrouter_provider_full import (
    OpenRouterProviderFull,
    create_openrouter_provider,
    MODEL_PRICING,
    MODEL_CONTEXT_LENGTHS,
    VISION_MODELS,
    FUNCTION_CALLING_MODELS,
)
from .base import AIProviderConfig, AIGenerationOptions
from .models import AIResponse, AIProviderType
from ..config.settings import settings

logger = logging.getLogger(__name__)


# =============================================================================
# MODEL SELECTION STRATEGIES
# =============================================================================

class TaskType(str, Enum):
    """Types of tasks for model selection"""
    CHAT = "chat"
    CODE = "code"
    REASONING = "reasoning"
    CREATIVE = "creative"
    VISION = "vision"
    FAST = "fast"
    LONG_CONTEXT = "long_context"
    FUNCTION_CALLING = "function_calling"
    EMBEDDING = "embedding"


@dataclass
class ModelRecommendation:
    """Recommended model for a task"""
    model_id: str
    provider: str
    is_free: bool
    context_length: int
    supports_vision: bool
    supports_functions: bool
    estimated_cost_per_1k: float
    reason: str


# Model recommendations by task type
TASK_MODEL_RECOMMENDATIONS: Dict[TaskType, List[ModelRecommendation]] = {
    TaskType.CHAT: [
        ModelRecommendation(
            model_id="meta-llama/llama-3.1-8b-instruct:free",
            provider="meta",
            is_free=True,
            context_length=131072,
            supports_vision=False,
            supports_functions=False,
            estimated_cost_per_1k=0.0,
            reason="Best free model for general chat"
        ),
        ModelRecommendation(
            model_id="anthropic/claude-3.5-sonnet",
            provider="anthropic",
            is_free=False,
            context_length=200000,
            supports_vision=True,
            supports_functions=True,
            estimated_cost_per_1k=9.0,
            reason="Best overall model for complex conversations"
        ),
    ],
    TaskType.CODE: [
        ModelRecommendation(
            model_id="deepseek/deepseek-chat",
            provider="deepseek",
            is_free=False,
            context_length=64000,
            supports_vision=False,
            supports_functions=True,
            estimated_cost_per_1k=0.21,
            reason="Excellent for code generation, very affordable"
        ),
        ModelRecommendation(
            model_id="anthropic/claude-3.5-sonnet",
            provider="anthropic",
            is_free=False,
            context_length=200000,
            supports_vision=True,
            supports_functions=True,
            estimated_cost_per_1k=9.0,
            reason="Best for complex code tasks"
        ),
    ],
    TaskType.REASONING: [
        ModelRecommendation(
            model_id="deepseek/deepseek-reasoner",
            provider="deepseek",
            is_free=False,
            context_length=64000,
            supports_vision=False,
            supports_functions=False,
            estimated_cost_per_1k=1.37,
            reason="Excellent reasoning model, affordable"
        ),
        ModelRecommendation(
            model_id="anthropic/claude-3.5-sonnet",
            provider="anthropic",
            is_free=False,
            context_length=200000,
            supports_vision=True,
            supports_functions=True,
            estimated_cost_per_1k=9.0,
            reason="Strong reasoning capabilities"
        ),
    ],
    TaskType.CREATIVE: [
        ModelRecommendation(
            model_id="anthropic/claude-3.5-sonnet",
            provider="anthropic",
            is_free=False,
            context_length=200000,
            supports_vision=True,
            supports_functions=True,
            estimated_cost_per_1k=9.0,
            reason="Best for creative writing"
        ),
        ModelRecommendation(
            model_id="meta-llama/llama-3.1-70b-instruct:free",
            provider="meta",
            is_free=True,
            context_length=131072,
            supports_vision=False,
            supports_functions=False,
            estimated_cost_per_1k=0.0,
            reason="Good free alternative for creative tasks"
        ),
    ],
    TaskType.VISION: [
        ModelRecommendation(
            model_id="google/gemini-flash-1.5",
            provider="google",
            is_free=False,
            context_length=1000000,
            supports_vision=True,
            supports_functions=True,
            estimated_cost_per_1k=0.19,
            reason="Best value for vision tasks"
        ),
        ModelRecommendation(
            model_id="anthropic/claude-3.5-sonnet",
            provider="anthropic",
            is_free=False,
            context_length=200000,
            supports_vision=True,
            supports_functions=True,
            estimated_cost_per_1k=9.0,
            reason="Excellent vision understanding"
        ),
    ],
    TaskType.FAST: [
        ModelRecommendation(
            model_id="meta-llama/llama-3.2-3b-instruct:free",
            provider="meta",
            is_free=True,
            context_length=131072,
            supports_vision=False,
            supports_functions=False,
            estimated_cost_per_1k=0.0,
            reason="Fast and free"
        ),
        ModelRecommendation(
            model_id="openai/gpt-4o-mini",
            provider="openai",
            is_free=False,
            context_length=128000,
            supports_vision=True,
            supports_functions=True,
            estimated_cost_per_1k=0.38,
            reason="Fast with good quality"
        ),
    ],
    TaskType.LONG_CONTEXT: [
        ModelRecommendation(
            model_id="google/gemini-flash-1.5",
            provider="google",
            is_free=False,
            context_length=1000000,
            supports_vision=True,
            supports_functions=True,
            estimated_cost_per_1k=0.19,
            reason="1M context window, very affordable"
        ),
        ModelRecommendation(
            model_id="anthropic/claude-3.5-sonnet",
            provider="anthropic",
            is_free=False,
            context_length=200000,
            supports_vision=True,
            supports_functions=True,
            estimated_cost_per_1k=9.0,
            reason="200K context with excellent quality"
        ),
    ],
    TaskType.FUNCTION_CALLING: [
        ModelRecommendation(
            model_id="openai/gpt-4o-mini",
            provider="openai",
            is_free=False,
            context_length=128000,
            supports_vision=True,
            supports_functions=True,
            estimated_cost_per_1k=0.38,
            reason="Excellent function calling, affordable"
        ),
        ModelRecommendation(
            model_id="anthropic/claude-3.5-sonnet",
            provider="anthropic",
            is_free=False,
            context_length=200000,
            supports_vision=True,
            supports_functions=True,
            estimated_cost_per_1k=9.0,
            reason="Best function calling accuracy"
        ),
    ],
}


# =============================================================================
# SERVICE CLASS
# =============================================================================

class OpenRouterService:
    """
    High-level service for OpenRouter integration.
    
    This service provides:
    - Intelligent model selection
    - Automatic cost optimization
    - Fallback handling
    - Usage tracking
    - Rate limiting awareness
    
    Usage:
        service = OpenRouterService()
        
        # Simple chat
        response = await service.chat("Hello!")
        
        # With task type
        response = await service.chat(
            "Write a Python function",
            task_type=TaskType.CODE
        )
        
        # Streaming
        async for chunk in service.stream("Tell me a story"):
            print(chunk)
        
        # With tools
        response = await service.chat_with_tools(
            "What's the weather?",
            tools=[weather_tool]
        )
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: Optional[str] = None,
        prefer_free: bool = True,
        max_cost_per_request: float = 1.0,
    ):
        """
        Initialize OpenRouter service.
        
        Args:
            api_key: OpenRouter API key (defaults to env var)
            default_model: Default model to use
            prefer_free: Whether to prefer free models
            max_cost_per_request: Maximum cost per request in USD
        """
        self._api_key = api_key or settings.OPENROUTER_API_KEY
        self._prefer_free = prefer_free
        self._max_cost = max_cost_per_request
        
        # Provider instances cache
        self._providers: Dict[str, OpenRouterProviderFull] = {}
        
        # Default model
        self._default_model = default_model or (
            "meta-llama/llama-3.1-8b-instruct:free" if prefer_free 
            else "anthropic/claude-3.5-sonnet"
        )
        
        # Usage tracking
        self._total_requests = 0
        self._total_tokens = 0
        self._total_cost = 0.0
    
    def _get_provider(self, model: str) -> OpenRouterProviderFull:
        """Get or create provider for a model."""
        if model not in self._providers:
            self._providers[model] = create_openrouter_provider(
                api_key=self._api_key,
                model=model
            )
        return self._providers[model]
    
    async def initialize(self) -> None:
        """Initialize the default provider."""
        provider = self._get_provider(self._default_model)
        await provider.initialize()
    
    # =========================================================================
    # Core Chat Methods
    # =========================================================================
    
    async def chat(
        self,
        prompt: str,
        task_type: Optional[TaskType] = None,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> AIResponse:
        """
        Generate a chat completion.
        
        Args:
            prompt: The user prompt
            task_type: Type of task for model selection
            model: Specific model to use (overrides task_type)
            system_prompt: System prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional options
        
        Returns:
            AIResponse with the generated content
        """
        # Select model
        selected_model = model or self._select_model(task_type)
        provider = self._get_provider(selected_model)
        
        if not provider.is_initialized:
            await provider.initialize()
        
        # Build options
        options = AIGenerationOptions(
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        # Generate response
        response = await provider.generate_response(prompt, options=options)
        
        # Track usage
        self._total_requests += 1
        self._total_tokens += response.tokens_used
        self._total_cost += provider.calculate_cost(
            response.prompt_tokens,
            response.completion_tokens
        )
        
        return response
    
    async def stream(
        self,
        prompt: str,
        task_type: Optional[TaskType] = None,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Generate a streaming chat completion.
        
        Args:
            prompt: The user prompt
            task_type: Type of task for model selection
            model: Specific model to use
            system_prompt: System prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional options
        
        Yields:
            Chunks of generated text
        """
        selected_model = model or self._select_model(task_type)
        provider = self._get_provider(selected_model)
        
        if not provider.is_initialized:
            await provider.initialize()
        
        options = AIGenerationOptions(
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs
        )
        
        async for chunk in provider.generate_stream(prompt, options=options):
            yield chunk
    
    async def chat_with_tools(
        self,
        prompt: str,
        tools: List[Dict[str, Any]],
        tool_choice: str = "auto",
        model: Optional[str] = None,
        **kwargs
    ) -> AIResponse:
        """
        Generate a completion with function calling.
        
        Args:
            prompt: The user prompt
            tools: List of tool definitions
            tool_choice: Tool selection mode
            model: Specific model to use
            **kwargs: Additional options
        
        Returns:
            AIResponse potentially containing tool calls
        """
        # Select a model that supports function calling
        if model is None:
            model = self._select_model(TaskType.FUNCTION_CALLING)
        
        provider = self._get_provider(model)
        
        if not provider.is_initialized:
            await provider.initialize()
        
        options = AIGenerationOptions(
            tools=tools,
            tool_choice=tool_choice,
            **kwargs
        )
        
        return await provider.generate_response(prompt, options=options)
    
    async def chat_with_vision(
        self,
        prompt: str,
        image_urls: List[str],
        model: Optional[str] = None,
        **kwargs
    ) -> AIResponse:
        """
        Generate a completion with image inputs.
        
        Args:
            prompt: The user prompt
            image_urls: List of image URLs
            model: Specific model to use
            **kwargs: Additional options
        
        Returns:
            AIResponse with the generated content
        """
        if model is None:
            model = self._select_model(TaskType.VISION)
        
        provider = self._get_provider(model)
        
        if not provider.is_initialized:
            await provider.initialize()
        
        return await provider.generate_with_vision(prompt, image_urls, options=kwargs.get("options"))
    
    # =========================================================================
    # Model Selection
    # =========================================================================
    
    def _select_model(self, task_type: Optional[TaskType]) -> str:
        """Select the best model for a task type."""
        if task_type is None:
            return self._default_model
        
        recommendations = TASK_MODEL_RECOMMENDATIONS.get(task_type, [])
        
        if not recommendations:
            return self._default_model
        
        # Filter by preferences
        if self._prefer_free:
            free_models = [r for r in recommendations if r.is_free]
            if free_models:
                return free_models[0].model_id
        
        # Check cost constraint
        affordable = [
            r for r in recommendations 
            if r.estimated_cost_per_1k <= self._max_cost * 1000
        ]
        
        if affordable:
            return affordable[0].model_id
        
        return recommendations[0].model_id
    
    def get_recommended_models(self, task_type: TaskType) -> List[ModelRecommendation]:
        """Get recommended models for a task type."""
        return TASK_MODEL_RECOMMENDATIONS.get(task_type, [])
    
    def get_model_info(self, model_id: str) -> Dict[str, Any]:
        """Get information about a specific model."""
        return {
            "model_id": model_id,
            "pricing": MODEL_PRICING.get(model_id, {"prompt": 0, "completion": 0}),
            "context_length": MODEL_CONTEXT_LENGTHS.get(model_id, 8192),
            "supports_vision": model_id in VISION_MODELS,
            "supports_functions": model_id in FUNCTION_CALLING_MODELS,
            "is_free": ":free" in model_id or MODEL_PRICING.get(model_id, {}).get("prompt", 1) == 0,
        }
    
    # =========================================================================
    # Usage & Statistics
    # =========================================================================
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics."""
        return {
            "total_requests": self._total_requests,
            "total_tokens": self._total_tokens,
            "total_cost_usd": self._total_cost,
            "default_model": self._default_model,
            "prefer_free": self._prefer_free,
        }
    
    async def close(self) -> None:
        """Close all provider connections."""
        for provider in self._providers.values():
            await provider.close()
        self._providers.clear()


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_service_instance: Optional[OpenRouterService] = None


def get_openrouter_service() -> OpenRouterService:
    """Get or create the singleton OpenRouter service."""
    global _service_instance
    if _service_instance is None:
        _service_instance = OpenRouterService()
    return _service_instance


async def quick_chat(
    prompt: str,
    task_type: Optional[TaskType] = None,
    **kwargs
) -> str:
    """
    Quick one-off chat completion.
    
    Args:
        prompt: The prompt to send
        task_type: Type of task
        **kwargs: Additional options
    
    Returns:
        Generated text content
    """
    service = get_openrouter_service()
    response = await service.chat(prompt, task_type=task_type, **kwargs)
    return response.content


async def quick_stream(
    prompt: str,
    task_type: Optional[TaskType] = None,
    **kwargs
) -> AsyncIterator[str]:
    """
    Quick one-off streaming chat.
    
    Args:
        prompt: The prompt to send
        task_type: Type of task
        **kwargs: Additional options
    
    Yields:
        Chunks of generated text
    """
    service = get_openrouter_service()
    async for chunk in service.stream(prompt, task_type=task_type, **kwargs):
        yield chunk


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "OpenRouterService",
    "TaskType",
    "ModelRecommendation",
    "TASK_MODEL_RECOMMENDATIONS",
    "get_openrouter_service",
    "quick_chat",
    "quick_stream",
]
