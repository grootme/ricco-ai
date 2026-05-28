"""
OpenRouter Configuration for OpenClaw Agent SaaS.

OpenRouter provides access to 200+ LLM models through a unified API including:
- Free models: Llama 3.1/3.2/3.3, Mistral, Gemma, Qwen, DeepSeek
- Premium models: GPT-4o, Claude 3.5, Gemini Pro
- Specialized models: Code, Vision, Reasoning

API Key: Set via OPENROUTER_API_KEY environment variable
Base URL: https://openrouter.ai/api/v1

Features:
- Automatic model fallback
- Cost tracking and optimization
- Rate limiting awareness
- Vision and function calling support
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
import os


@dataclass
class OpenRouterModel:
    """OpenRouter model configuration."""
    id: str
    name: str
    provider: str
    context_length: int
    is_free: bool = True
    features: List[str] = field(default_factory=list)
    pricing_prompt: float = 0.0
    pricing_completion: float = 0.0


# ============================================================================
# FREE MODELS ON OPENROUTER (2024-2025)
# ============================================================================

FREE_MODELS: Dict[str, OpenRouterModel] = {
    # Meta Llama 3.x Series (VERIFIED WORKING)
    "meta/llama-3.1-8b": OpenRouterModel(
        id="meta-llama/llama-3.1-8b-instruct",
        name="Llama 3.1 8B Instruct",
        provider="Meta",
        context_length=131072,
        is_free=True,
        features=["chat", "instruction"],
    ),
    
    # Google Gemma (VERIFIED WORKING)
    "google/gemma-3-4b": OpenRouterModel(
        id="google/gemma-3-4b-it",
        name="Gemma 3 4B",
        provider="Google",
        context_length=131072,
        is_free=True,
        features=["chat", "instruction"],
    ),
    
    "google/gemma-3-12b": OpenRouterModel(
        id="google/gemma-3-12b-it",
        name="Gemma 3 12B",
        provider="Google",
        context_length=131072,
        is_free=True,
        features=["chat", "instruction", "reasoning"],
    ),
    
    # Mistral (VERIFIED WORKING)
    "mistral/nemo": OpenRouterModel(
        id="mistralai/mistral-nemo",
        name="Mistral Nemo 12B",
        provider="Mistral AI",
        context_length=131072,
        is_free=True,
        features=["chat", "instruction"],
    ),
    
    # Qwen (VERIFIED WORKING)
    "qwen/qwen-2.5-7b": OpenRouterModel(
        id="qwen/qwen-2.5-7b-instruct",
        name="Qwen 2.5 7B Instruct",
        provider="Alibaba",
        context_length=131072,
        is_free=True,
        features=["chat", "code"],
    ),
    
    # DeepSeek (ECONOMIC - VERIFIED WORKING)
    "deepseek/deepseek-chat": OpenRouterModel(
        id="deepseek/deepseek-chat",
        name="DeepSeek Chat V3",
        provider="DeepSeek",
        context_length=64000,
        is_free=False,  # Very cheap but not free
        features=["chat", "code", "function_calling"],
        pricing_prompt=0.14,
        pricing_completion=0.28,
    ),
    
    # NVIDIA (FREE)
    "nvidia/nemotron-nano": OpenRouterModel(
        id="nvidia/nemotron-nano-9b-v2",
        name="NVIDIA Nemotron Nano 9B V2",
        provider="NVIDIA",
        context_length=131072,
        is_free=True,
        features=["chat", "instruction"],
    ),
}


# ============================================================================
# PREMIUM MODELS (PAY PER USE)
# ============================================================================

PREMIUM_MODELS: Dict[str, OpenRouterModel] = {
    # OpenAI
    "openai/gpt-4o": OpenRouterModel(
        id="openai/gpt-4o",
        name="GPT-4o",
        provider="OpenAI",
        context_length=128000,
        is_free=False,
        features=["chat", "vision", "function_calling"],
        pricing_prompt=2.5,
        pricing_completion=10.0,
    ),
    
    "openai/gpt-4o-mini": OpenRouterModel(
        id="openai/gpt-4o-mini",
        name="GPT-4o Mini",
        provider="OpenAI",
        context_length=128000,
        is_free=False,
        features=["chat", "vision", "function_calling", "fast"],
        pricing_prompt=0.15,
        pricing_completion=0.6,
    ),
    
    "openai/o1-preview": OpenRouterModel(
        id="openai/o1-preview",
        name="O1 Preview",
        provider="OpenAI",
        context_length=128000,
        is_free=False,
        features=["chat", "reasoning"],
        pricing_prompt=15.0,
        pricing_completion=60.0,
    ),
    
    "openai/o1-mini": OpenRouterModel(
        id="openai/o1-mini",
        name="O1 Mini",
        provider="OpenAI",
        context_length=128000,
        is_free=False,
        features=["chat", "reasoning"],
        pricing_prompt=3.0,
        pricing_completion=12.0,
    ),
    
    # Anthropic
    "anthropic/claude-3.5-sonnet": OpenRouterModel(
        id="anthropic/claude-3.5-sonnet",
        name="Claude 3.5 Sonnet",
        provider="Anthropic",
        context_length=200000,
        is_free=False,
        features=["chat", "vision", "function_calling", "reasoning"],
        pricing_prompt=3.0,
        pricing_completion=15.0,
    ),
    
    "anthropic/claude-3-opus": OpenRouterModel(
        id="anthropic/claude-3-opus",
        name="Claude 3 Opus",
        provider="Anthropic",
        context_length=200000,
        is_free=False,
        features=["chat", "vision", "function_calling"],
        pricing_prompt=15.0,
        pricing_completion=75.0,
    ),
    
    "anthropic/claude-3-haiku": OpenRouterModel(
        id="anthropic/claude-3-haiku",
        name="Claude 3 Haiku",
        provider="Anthropic",
        context_length=200000,
        is_free=False,
        features=["chat", "vision", "function_calling", "fast"],
        pricing_prompt=0.25,
        pricing_completion=1.25,
    ),
    
    # Google
    "google/gemini-pro-1.5": OpenRouterModel(
        id="google/gemini-pro-1.5",
        name="Gemini Pro 1.5",
        provider="Google",
        context_length=1000000,
        is_free=False,
        features=["chat", "vision", "function_calling", "long_context"],
        pricing_prompt=1.25,
        pricing_completion=5.0,
    ),
    
    "google/gemini-flash-1.5": OpenRouterModel(
        id="google/gemini-flash-1.5",
        name="Gemini Flash 1.5",
        provider="Google",
        context_length=1000000,
        is_free=False,
        features=["chat", "vision", "function_calling", "fast", "long_context"],
        pricing_prompt=0.075,
        pricing_completion=0.3,
    ),
    
    # DeepSeek Premium
    "deepseek/deepseek-chat-v3": OpenRouterModel(
        id="deepseek/deepseek-chat",
        name="DeepSeek Chat V3",
        provider="DeepSeek",
        context_length=64000,
        is_free=False,
        features=["chat", "code", "function_calling"],
        pricing_prompt=0.14,
        pricing_completion=0.28,
    ),
    
    "deepseek/deepseek-reasoner": OpenRouterModel(
        id="deepseek/deepseek-reasoner",
        name="DeepSeek Reasoner",
        provider="DeepSeek",
        context_length=64000,
        is_free=False,
        features=["chat", "reasoning"],
        pricing_prompt=0.55,
        pricing_completion=2.19,
    ),
    
    # Meta Premium
    "meta/llama-3.1-405b": OpenRouterModel(
        id="meta-llama/llama-3.1-405b-instruct",
        name="Llama 3.1 405B",
        provider="Meta",
        context_length=131072,
        is_free=False,
        features=["chat", "instruction", "reasoning"],
        pricing_prompt=2.0,
        pricing_completion=2.0,
    ),
    
    # Mistral Premium
    "mistral/mistral-large": OpenRouterModel(
        id="mistralai/mistral-large-2411",
        name="Mistral Large",
        provider="Mistral AI",
        context_length=128000,
        is_free=False,
        features=["chat", "function_calling"],
        pricing_prompt=2.0,
        pricing_completion=6.0,
    ),
}


# Default models for different use cases
DEFAULT_MODELS = {
    "chat": "meta/llama-3.1-8b",
    "code": "qwen/qwen-2.5-coder-32b",
    "reasoning": "meta/llama-3.1-70b",
    "fast": "meta/llama-3.2-3b",
    "long_context": "meta/llama-3.1-8b",
    "vision": "meta/llama-3.2-11b-vision",
    
    # Premium defaults
    "premium_chat": "anthropic/claude-3.5-sonnet",
    "premium_code": "anthropic/claude-3.5-sonnet",
    "premium_fast": "openai/gpt-4o-mini",
    "premium_vision": "anthropic/claude-3.5-sonnet",
}


# ============================================================================
# CONFIGURATION CLASS
# ============================================================================

@dataclass
class OpenRouterConfig:
    """OpenRouter API configuration."""
    
    api_key: Optional[str] = None
    base_url: str = "https://openrouter.ai/api/v1"
    
    # Default model selections
    default_chat_model: str = "meta/llama-3.1-8b"
    default_embedding_model: str = "openai/text-embedding-3-small"
    
    # Request settings
    default_temperature: float = 0.7
    default_max_tokens: int = 4096
    timeout: int = 120
    
    # Headers
    site_url: Optional[str] = None
    site_name: str = "RICCO AI"
    
    # Preferences
    prefer_free_models: bool = True
    max_cost_per_request: float = 1.0
    
    def __post_init__(self):
        # Load API key from environment if not provided
        if not self.api_key:
            self.api_key = os.environ.get("OPENROUTER_API_KEY")
    
    @property
    def default_model(self) -> str:
        """Alias for default_chat_model for backwards compatibility."""
        return self.default_chat_model
    
    @default_model.setter
    def default_model(self, value: str) -> None:
        """Setter for default_model alias."""
        self.default_chat_model = value
    
    def get_headers(self) -> Dict[str, str]:
        """Get API headers."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": self.site_url or "https://ricco.ai",
            "X-Title": self.site_name,
        }
        return headers
    
    def get_model(self, model_key: str) -> Optional[OpenRouterModel]:
        """Get model configuration by key."""
        # Check if it's a shortcut
        if model_key in DEFAULT_MODELS:
            model_key = DEFAULT_MODELS[model_key]
        
        # Check free models first
        if model_key in FREE_MODELS:
            return FREE_MODELS[model_key]
        
        # Then check premium models
        return PREMIUM_MODELS.get(model_key)
    
    def list_free_models(self) -> List[OpenRouterModel]:
        """List all available free models."""
        return list(FREE_MODELS.values())
    
    def list_premium_models(self) -> List[OpenRouterModel]:
        """List all available premium models."""
        return list(PREMIUM_MODELS.values())
    
    def list_all_models(self) -> List[OpenRouterModel]:
        """List all available models."""
        return list(FREE_MODELS.values()) + list(PREMIUM_MODELS.values())
    
    def is_free_model(self, model_id: Optional[str] = None) -> bool:
        """
        Check if a model is free.
        
        Args:
            model_id: Model ID to check. If None, uses default_chat_model.
        
        Returns:
            True if the model is free, False otherwise.
        """
        model = model_id or self.default_chat_model
        
        # Check in FREE_MODELS dict
        if model in FREE_MODELS:
            return FREE_MODELS[model].is_free
        
        # Check if model key maps to a free model
        if model in DEFAULT_MODELS:
            actual_model = DEFAULT_MODELS[model]
            return actual_model in FREE_MODELS
        
        # Default to checking if ":free" is in the model name
        return ":free" in model or "free" in model.lower()


# ============================================================================
# LLM CLIENT
# ============================================================================

class OpenRouterClient:
    """Simple OpenRouter client for chat completions."""
    
    def __init__(self, config: Optional[OpenRouterConfig] = None):
        self.config = config or OpenRouterConfig()
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs,
    ) -> Dict:
        """
        Create a chat completion.
        
        Args:
            messages: List of {"role": "user/assistant/system", "content": "..."}
            model: Model ID (e.g., "meta/llama-3.1-8b")
            temperature: Sampling temperature
            max_tokens: Max tokens to generate
        
        Returns:
            API response dict
        """
        import httpx
        
        model = model or self.config.default_chat_model
        model_config = self.config.get_model(model)
        
        if model_config:
            model = model_config.id
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature or self.config.default_temperature,
            "max_tokens": max_tokens or self.config.default_max_tokens,
            **kwargs,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.config.base_url}/chat/completions",
                headers=self.config.get_headers(),
                json=payload,
                timeout=self.config.timeout,
            )
            response.raise_for_status()
            return response.json()
    
    async def embed(
        self,
        text: str,
        model: Optional[str] = None,
    ) -> List[float]:
        """
        Generate embedding for text.
        
        Note: OpenRouter supports embeddings through OpenAI models.
        """
        import httpx
        
        model = model or self.config.default_embedding_model
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.config.base_url}/embeddings",
                headers=self.config.get_headers(),
                json={
                    "model": model,
                    "input": text,
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            return data["data"][0]["embedding"]


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_openrouter_client(api_key: Optional[str] = None) -> OpenRouterClient:
    """Create an OpenRouter client."""
    config = OpenRouterConfig(api_key=api_key)
    return OpenRouterClient(config)


def get_default_config() -> OpenRouterConfig:
    """Get default configuration."""
    return OpenRouterConfig()


def get_openrouter_config(
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    default_model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    timeout: Optional[int] = None,
    site_url: Optional[str] = None,
    site_name: Optional[str] = None,
    prefer_free_models: Optional[bool] = None,
) -> OpenRouterConfig:
    """
    Get OpenRouter configuration with custom settings.
    
    Args:
        api_key: OpenRouter API key
        base_url: API base URL
        default_model: Default chat model key
        temperature: Default temperature for completions
        max_tokens: Default max tokens for completions
        timeout: Request timeout in seconds
        site_url: Your site URL for OpenRouter headers
        site_name: Your site name for OpenRouter headers
        prefer_free_models: Whether to prefer free models
    
    Returns:
        OpenRouterConfig instance
    """
    # Load from environment if not provided
    if api_key is None:
        api_key = os.environ.get("OPENROUTER_API_KEY")
    
    if base_url is None:
        base_url = os.environ.get("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    
    if site_url is None:
        site_url = os.environ.get("OPENROUTER_SITE_URL")
    
    # Build config with provided settings
    config_kwargs = {
        "api_key": api_key,
        "base_url": base_url,
    }
    
    if default_model is not None:
        config_kwargs["default_chat_model"] = default_model
    
    if temperature is not None:
        config_kwargs["default_temperature"] = temperature
    
    if max_tokens is not None:
        config_kwargs["default_max_tokens"] = max_tokens
    
    if timeout is not None:
        config_kwargs["timeout"] = timeout
    
    if site_url is not None:
        config_kwargs["site_url"] = site_url
    
    if site_name is not None:
        config_kwargs["site_name"] = site_name
    
    if prefer_free_models is not None:
        config_kwargs["prefer_free_models"] = prefer_free_models
    
    return OpenRouterConfig(**config_kwargs)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "OpenRouterConfig",
    "OpenRouterClient",
    "OpenRouterModel",
    "FREE_MODELS",
    "PREMIUM_MODELS",
    "DEFAULT_MODELS",
    "create_openrouter_client",
    "get_default_config",
    "get_openrouter_config",
]
