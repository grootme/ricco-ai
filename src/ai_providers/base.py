"""
Base AI Provider Interface
Abstract interface for AI providers
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, AsyncIterator
from pydantic import BaseModel, Field
from enum import Enum

from .models import AIRequest, AIResponse, AIProviderType


class AIProviderConfig(BaseModel):
    """Configuration for AI provider"""
    provider_type: AIProviderType
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: str = "gpt-4o-mini"
    
    # Generation settings
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 1.0
    
    # Rate limiting
    requests_per_minute: int = 60
    tokens_per_minute: int = 90000
    
    # Retry settings
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Timeout
    timeout: float = 60.0
    
    # Features
    supports_streaming: bool = True
    supports_vision: bool = False
    supports_functions: bool = True
    
    # Cost tracking
    cost_per_1k_prompt_tokens: float = 0.0
    cost_per_1k_completion_tokens: float = 0.0
    
    class Config:
        use_enum_values = True


class AIGenerationOptions(BaseModel):
    """Options for AI generation"""
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    stop_sequences: Optional[List[str]] = None
    
    # System prompt
    system_prompt: Optional[str] = None
    
    # Response format
    response_format: Optional[Dict[str, Any]] = None
    
    # Tools/functions
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[str] = None
    
    # Streaming
    stream: bool = False
    
    # Metadata
    user_id: Optional[str] = None
    request_id: Optional[str] = None


class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    def __init__(self, config: AIProviderConfig):
        self.config = config
        self._is_initialized = False
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider (validate API key, etc.)"""
        pass
    
    @abstractmethod
    async def generate_response(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        options: Optional[AIGenerationOptions] = None
    ) -> AIResponse:
        """
        Generate a response from the AI
        
        Args:
            prompt: The input prompt
            context: Additional context for the prompt
            options: Generation options
            
        Returns:
            AIResponse with the generated content
        """
        pass
    
    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        options: Optional[AIGenerationOptions] = None
    ) -> AsyncIterator[str]:
        """
        Generate a streaming response from the AI
        
        Args:
            prompt: The input prompt
            context: Additional context for the prompt
            options: Generation options
            
        Yields:
            Chunks of the generated content
        """
        pass
    
    @abstractmethod
    async def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding vector for text
        
        Args:
            text: The text to embed
            
        Returns:
            List of floats representing the embedding
        """
        pass
    
    @abstractmethod
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Get embedding vectors for multiple texts
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        pass
    
    @abstractmethod
    def supports_vision(self) -> bool:
        """
        Check if the provider supports vision/image inputs
        
        Returns:
            True if vision is supported
        """
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """
        Get the name of the current model
        
        Returns:
            Model name string
        """
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """
        Get list of available models for this provider
        
        Returns:
            List of model names
        """
        pass
    
    @abstractmethod
    async def count_tokens(self, text: str) -> int:
        """
        Count tokens in text
        
        Args:
            text: The text to count tokens for
            
        Returns:
            Number of tokens
        """
        pass
    
    @abstractmethod
    def get_max_context_length(self) -> int:
        """
        Get maximum context length for the current model
        
        Returns:
            Maximum number of tokens
        """
        pass
    
    async def health_check(self) -> bool:
        """
        Check if the provider is healthy and available
        
        Returns:
            True if healthy
        """
        try:
            if not self._is_initialized:
                await self.initialize()
            # Simple test generation
            response = await self.generate_response(
                "Say 'ok' if you can hear me.",
                options=AIGenerationOptions(max_tokens=5)
            )
            return bool(response.content)
        except Exception:
            return False
    
    def calculate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        """
        Calculate cost for a request
        
        Args:
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            
        Returns:
            Cost in USD
        """
        prompt_cost = (prompt_tokens / 1000) * self.config.cost_per_1k_prompt_tokens
        completion_cost = (completion_tokens / 1000) * self.config.cost_per_1k_completion_tokens
        return prompt_cost + completion_cost
    
    async def generate_with_history(
        self,
        prompt: str,
        history: List[Dict[str, str]],
        context: Optional[Dict[str, Any]] = None,
        options: Optional[AIGenerationOptions] = None
    ) -> AIResponse:
        """
        Generate response with conversation history
        
        Args:
            prompt: The input prompt
            history: List of previous messages with 'role' and 'content'
            context: Additional context
            options: Generation options
            
        Returns:
            AIResponse with the generated content
        """
        # Default implementation - providers can override for optimization
        full_context = context or {}
        full_context["conversation_history"] = history
        return await self.generate_response(prompt, full_context, options)
    
    @property
    def provider_type(self) -> AIProviderType:
        """Get provider type"""
        return self.config.provider_type
    
    @property
    def is_initialized(self) -> bool:
        """Check if provider is initialized"""
        return self._is_initialized


class AIProviderFactory:
    """Factory for creating AI providers"""
    
    _providers: Dict[AIProviderType, type] = {}
    
    @classmethod
    def register(cls, provider_type: AIProviderType, provider_class: type) -> None:
        """Register a provider class"""
        cls._providers[provider_type] = provider_class
    
    @classmethod
    def create(cls, config: AIProviderConfig) -> AIProvider:
        """Create a provider instance"""
        provider_class = cls._providers.get(config.provider_type)
        if not provider_class:
            raise ValueError(f"Unknown provider type: {config.provider_type}")
        return provider_class(config)
    
    @classmethod
    def get_available_providers(cls) -> List[AIProviderType]:
        """Get list of registered provider types"""
        return list(cls._providers.keys())


# Import providers and register them
def _register_providers():
    """Register all available providers"""
    try:
        from .providers.openai_provider import OpenAIProvider
        AIProviderFactory.register(AIProviderType.OPENAI, OpenAIProvider)
    except ImportError:
        pass
    
    try:
        from .providers.anthropic_provider import AnthropicProvider
        AIProviderFactory.register(AIProviderType.ANTHROPIC, AnthropicProvider)
    except ImportError:
        pass
    
    try:
        from .providers.local_provider import LocalProvider
        AIProviderFactory.register(AIProviderType.LOCAL, LocalProvider)
    except ImportError:
        pass
    
    try:
        from .providers.openrouter_provider_full import OpenRouterProviderFull
        AIProviderFactory.register(AIProviderType.OPENROUTER, OpenRouterProviderFull)
    except ImportError:
        pass


# Register providers on module load
_register_providers()
