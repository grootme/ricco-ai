"""
OpenRouter Configuration for OpenClaw Agent SaaS.

OpenRouter provides access to 15+ free LLM models including:
- Tencent Hy3
- NVIDIA Nemotron
- Poolside Laguna
- OpenAI GPT-OSS
- And more...

API Key: Set via OPENROUTER_API_KEY environment variable
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


# ============================================================================
# FREE MODELS ON OPENROUTER (2024-2025)
# ============================================================================

FREE_MODELS: Dict[str, OpenRouterModel] = {
    # Tencent
    "tencent/hy3": OpenRouterModel(
        id="tencent/hy3",
        name="Tencent Hy3",
        provider="Tencent",
        context_length=32768,
        is_free=True,
        features=["chat", "reasoning"],
    ),
    
    # NVIDIA
    "nvidia/nemotron": OpenRouterModel(
        id="nvidia/nemotron-4-340b-instruct",
        name="NVIDIA Nemotron 4 340B",
        provider="NVIDIA",
        context_length=4096,
        is_free=True,
        features=["chat", "instruction"],
    ),
    
    # OpenAI (free tier)
    "openai/gpt-oss": OpenRouterModel(
        id="openai/gpt-oss",
        name="OpenAI GPT-OSS",
        provider="OpenAI",
        context_length=128000,
        is_free=True,
        features=["chat", "function_calling"],
    ),
    
    # Poolside
    "poolside/laguna": OpenRouterModel(
        id="poolside/laguna-1.0",
        name="Poolside Laguna 1.0",
        provider="Poolside",
        context_length=8192,
        is_free=True,
        features=["chat", "code"],
    ),
    
    # Meta Llama
    "meta/llama-3.1-8b": OpenRouterModel(
        id="meta-llama/llama-3.1-8b-instruct",
        name="Llama 3.1 8B Instruct",
        provider="Meta",
        context_length=131072,
        is_free=True,
        features=["chat", "instruction"],
    ),
    
    "meta/llama-3.1-70b": OpenRouterModel(
        id="meta-llama/llama-3.1-70b-instruct",
        name="Llama 3.1 70B Instruct",
        provider="Meta",
        context_length=131072,
        is_free=True,
        features=["chat", "instruction", "reasoning"],
    ),
    
    # Google
    "google/gemma-2-9b": OpenRouterModel(
        id="google/gemma-2-9b-it",
        name="Gemma 2 9B",
        provider="Google",
        context_length=8192,
        is_free=True,
        features=["chat", "instruction"],
    ),
    
    # Mistral
    "mistral/mistral-7b": OpenRouterModel(
        id="mistralai/mistral-7b-instruct",
        name="Mistral 7B Instruct",
        provider="Mistral AI",
        context_length=32768,
        is_free=True,
        features=["chat", "instruction"],
    ),
    
    # Qwen
    "qwen/qwen-2-7b": OpenRouterModel(
        id="qwen/qwen-2-7b-instruct",
        name="Qwen 2 7B Instruct",
        provider="Alibaba",
        context_length=32768,
        is_free=True,
        features=["chat", "code"],
    ),
    
    # DeepSeek
    "deepseek/deepseek-chat": OpenRouterModel(
        id="deepseek/deepseek-chat",
        name="DeepSeek Chat",
        provider="DeepSeek",
        context_length=64000,
        is_free=True,
        features=["chat", "code", "reasoning"],
    ),
}

# Default models for different use cases
DEFAULT_MODELS = {
    "chat": "meta/llama-3.1-8b",
    "code": "deepseek/deepseek-chat",
    "reasoning": "meta/llama-3.1-70b",
    "fast": "mistral/mistral-7b",
    "long_context": "openai/gpt-oss",
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
    timeout: int = 60
    
    # Headers
    site_url: Optional[str] = None
    site_name: str = "OpenClaw Agent SaaS"
    
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
            "HTTP-Referer": self.site_url or "https://openclaw.ai",
            "X-Title": self.site_name,
        }
        return headers
    
    def get_model(self, model_key: str) -> Optional[OpenRouterModel]:
        """Get model configuration by key."""
        # Check if it's a shortcut
        if model_key in DEFAULT_MODELS:
            model_key = DEFAULT_MODELS[model_key]
        
        return FREE_MODELS.get(model_key)
    
    def list_free_models(self) -> List[OpenRouterModel]:
        """List all available free models."""
        return list(FREE_MODELS.values())
    
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
            return actual_model in FREE_MODELS and FREE_MODELS[actual_model].is_free
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
        
        Note: OpenRouter may not support embeddings directly.
        Use OpenAI embeddings with your OpenRouter API key.
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
) -> OpenRouterConfig:
    """
    Get OpenRouter configuration with custom settings.
    
    This function creates a customized OpenRouter configuration for use
    in tests, agents, and integrations throughout the OpenClaw ecosystem.
    
    Args:
        api_key: OpenRouter API key (defaults to OPENROUTER_API_KEY env var)
        base_url: API base URL (defaults to https://openrouter.ai/api/v1)
        default_model: Default chat model key (e.g., "meta/llama-3.1-8b")
        temperature: Default temperature for completions (0.0-2.0)
        max_tokens: Default max tokens for completions
        timeout: Request timeout in seconds
        site_url: Your site URL for OpenRouter headers
        site_name: Your site name for OpenRouter headers
    
    Returns:
        OpenRouterConfig instance with the specified settings
    
    Example:
        >>> config = get_openrouter_config(
        ...     api_key="sk-or-...",
        ...     default_model="deepseek/deepseek-chat",
        ...     temperature=0.5,
        ...     max_tokens=2048,
        ... )
        >>> client = OpenRouterClient(config)
    
    Environment Variables:
        OPENROUTER_API_KEY: Default API key if not provided
        OPENROUTER_BASE_URL: Override base URL
        OPENROUTER_SITE_URL: Default site URL
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
    
    return OpenRouterConfig(**config_kwargs)


def get_openrouter_client(
    api_key: Optional[str] = None,
    **config_kwargs,
) -> OpenRouterClient:
    """
    Convenience function to create an OpenRouter client directly.
    
    Args:
        api_key: OpenRouter API key
        **config_kwargs: Additional configuration options passed to get_openrouter_config
    
    Returns:
        OpenRouterClient instance ready to use
    
    Example:
        >>> client = get_openrouter_client(api_key="sk-or-...")
        >>> response = await client.chat_completion([
        ...     {"role": "user", "content": "Hello!"}
        ... ])
    """
    config = get_openrouter_config(api_key=api_key, **config_kwargs)
    return OpenRouterClient(config)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "OpenRouterConfig",
    "OpenRouterClient",
    "OpenRouterModel",
    "FREE_MODELS",
    "DEFAULT_MODELS",
    "create_openrouter_client",
    "get_default_config",
    "get_openrouter_config",
    "get_openrouter_client",
]
