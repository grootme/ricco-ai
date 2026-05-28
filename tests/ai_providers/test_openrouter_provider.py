"""
Tests for OpenRouter Provider

Comprehensive tests for the OpenRouter provider implementation.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import json

from src.ai_providers.providers.openrouter_provider_full import (
    OpenRouterProviderFull,
    OpenRouterProviderConfigExtra,
    create_openrouter_provider,
    MODEL_PRICING,
    MODEL_CONTEXT_LENGTHS,
    VISION_MODELS,
    FUNCTION_CALLING_MODELS,
)
from src.ai_providers.base import AIProviderConfig, AIGenerationOptions
from src.ai_providers.models import AIProviderType


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def provider_config():
    """Create a basic provider configuration."""
    return AIProviderConfig(
        provider_type=AIProviderType.OPENROUTER,
        api_key="test-api-key",
        model="meta-llama/llama-3.1-8b-instruct:free"
    )


@pytest.fixture
def mock_response():
    """Create a mock API response."""
    return {
        "id": "test-id",
        "choices": [
            {
                "message": {
                    "content": "Hello! How can I help you?"
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 8,
            "total_tokens": 18
        },
        "model": "meta-llama/llama-3.1-8b-instruct:free"
    }


@pytest.fixture
def mock_streaming_response():
    """Create mock streaming response chunks."""
    return [
        b'data: {"choices": [{"delta": {"content": "Hello"}}]}\n',
        b'data: {"choices": [{"delta": {"content": " there"}}]}\n',
        b'data: {"choices": [{"delta": {"content": "!"}}]}\n',
        b'data: [DONE]\n',
    ]


# =============================================================================
# PROVIDER INITIALIZATION TESTS
# =============================================================================

class TestOpenRouterProviderInit:
    """Tests for provider initialization."""
    
    def test_provider_creation(self, provider_config):
        """Test provider can be created with config."""
        provider = OpenRouterProviderFull(provider_config)
        
        assert provider.config.model == "meta-llama/llama-3.1-8b-instruct:free"
        assert provider.config.provider_type == AIProviderType.OPENROUTER
        assert not provider.is_initialized
    
    def test_provider_with_free_model(self, provider_config):
        """Test provider recognizes free models."""
        provider = OpenRouterProviderFull(provider_config)
        
        assert provider.is_free_model() is True
    
    def test_provider_with_premium_model(self):
        """Test provider with premium model."""
        config = AIProviderConfig(
            provider_type=AIProviderType.OPENROUTER,
            api_key="test-key",
            model="anthropic/claude-3.5-sonnet"
        )
        provider = OpenRouterProviderFull(config)
        
        assert provider.is_free_model() is False
        assert provider.supports_vision() is True
    
    def test_provider_pricing_setup(self, provider_config):
        """Test pricing is set correctly."""
        provider = OpenRouterProviderFull(provider_config)
        
        # Free model should have 0 cost
        assert provider.config.cost_per_1k_prompt_tokens == 0.0
        assert provider.config.cost_per_1k_completion_tokens == 0.0
    
    def test_provider_context_length(self, provider_config):
        """Test context length is set correctly."""
        provider = OpenRouterProviderFull(provider_config)
        
        assert provider.get_max_context_length() == 131072


# =============================================================================
# CHAT COMPLETION TESTS
# =============================================================================

class TestChatCompletion:
    """Tests for chat completion functionality."""
    
    @pytest.mark.asyncio
    async def test_basic_chat_completion(self, provider_config, mock_response):
        """Test basic chat completion."""
        provider = OpenRouterProviderFull(provider_config)
        
        # Mock the HTTP session
        mock_session = AsyncMock()
        mock_response_obj = AsyncMock()
        mock_response_obj.status = 200
        mock_response_obj.json = AsyncMock(return_value=mock_response)
        mock_session.post = MagicMock(return_value=mock_response_obj)
        mock_response_obj.__aenter__ = AsyncMock(return_value=mock_response_obj)
        mock_response_obj.__aexit__ = AsyncMock()
        
        provider._session = mock_session
        provider._is_initialized = True
        
        response = await provider.generate_response("Hello!")
        
        assert response.content == "Hello! How can I help you?"
        assert response.tokens_used == 18
        assert response.provider == AIProviderType.OPENROUTER
    
    @pytest.mark.asyncio
    async def test_chat_with_system_prompt(self, provider_config, mock_response):
        """Test chat with system prompt."""
        provider = OpenRouterProviderFull(provider_config)
        
        mock_session = AsyncMock()
        mock_response_obj = AsyncMock()
        mock_response_obj.status = 200
        mock_response_obj.json = AsyncMock(return_value=mock_response)
        mock_session.post = MagicMock(return_value=mock_response_obj)
        mock_response_obj.__aenter__ = AsyncMock(return_value=mock_response_obj)
        mock_response_obj.__aexit__ = AsyncMock()
        
        provider._session = mock_session
        provider._is_initialized = True
        
        options = AIGenerationOptions(
            system_prompt="You are a helpful assistant."
        )
        
        response = await provider.generate_response("Hello!", options=options)
        
        assert response.content == "Hello! How can I help you?"
    
    @pytest.mark.asyncio
    async def test_chat_with_conversation_history(self, provider_config, mock_response):
        """Test chat with conversation history."""
        provider = OpenRouterProviderFull(provider_config)
        
        mock_session = AsyncMock()
        mock_response_obj = AsyncMock()
        mock_response_obj.status = 200
        mock_response_obj.json = AsyncMock(return_value=mock_response)
        mock_session.post = MagicMock(return_value=mock_response_obj)
        mock_response_obj.__aenter__ = AsyncMock(return_value=mock_response_obj)
        mock_response_obj.__aexit__ = AsyncMock()
        
        provider._session = mock_session
        provider._is_initialized = True
        
        context = {
            "conversation_history": [
                {"role": "user", "content": "Hi"},
                {"role": "assistant", "content": "Hello!"}
            ]
        }
        
        response = await provider.generate_response(
            "How are you?",
            context=context
        )
        
        assert response.content == "Hello! How can I help you?"


# =============================================================================
# STREAMING TESTS
# =============================================================================

class TestStreaming:
    """Tests for streaming functionality."""
    
    @pytest.mark.asyncio
    async def test_streaming_completion(self, provider_config, mock_streaming_response):
        """Test streaming chat completion."""
        provider = OpenRouterProviderFull(provider_config)
        
        # Create mock async iterator for streaming
        async def mock_aiter():
            for chunk in mock_streaming_response:
                yield chunk
        
        mock_response_obj = AsyncMock()
        mock_response_obj.status = 200
        mock_response_obj.content = mock_aiter()
        
        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_response_obj)
        mock_response_obj.__aenter__ = AsyncMock(return_value=mock_response_obj)
        mock_response_obj.__aexit__ = AsyncMock()
        
        provider._session = mock_session
        provider._is_initialized = True
        
        chunks = []
        async for chunk in provider.generate_stream("Hello"):
            chunks.append(chunk)
        
        assert chunks == ["Hello", " there", "!"]


# =============================================================================
# VISION TESTS
# =============================================================================

class TestVision:
    """Tests for vision functionality."""
    
    def test_vision_support_detection(self):
        """Test vision support detection."""
        # Model with vision support
        config = AIProviderConfig(
            provider_type=AIProviderType.OPENROUTER,
            api_key="test-key",
            model="anthropic/claude-3.5-sonnet"
        )
        provider = OpenRouterProviderFull(config)
        assert provider.supports_vision() is True
        
        # Model without vision support
        config_no_vision = AIProviderConfig(
            provider_type=AIProviderType.OPENROUTER,
            api_key="test-key",
            model="meta-llama/llama-3.1-8b-instruct:free"
        )
        provider_no_vision = OpenRouterProviderFull(config_no_vision)
        assert provider_no_vision.supports_vision() is False
    
    @pytest.mark.asyncio
    async def test_vision_completion(self, mock_response):
        """Test vision completion."""
        config = AIProviderConfig(
            provider_type=AIProviderType.OPENROUTER,
            api_key="test-key",
            model="anthropic/claude-3.5-sonnet"
        )
        provider = OpenRouterProviderFull(config)
        
        mock_session = AsyncMock()
        mock_response_obj = AsyncMock()
        mock_response_obj.status = 200
        mock_response_obj.json = AsyncMock(return_value=mock_response)
        mock_session.post = MagicMock(return_value=mock_response_obj)
        mock_response_obj.__aenter__ = AsyncMock(return_value=mock_response_obj)
        mock_response_obj.__aexit__ = AsyncMock()
        
        provider._session = mock_session
        provider._is_initialized = True
        
        response = await provider.generate_with_vision(
            "What's in this image?",
            ["https://example.com/image.jpg"]
        )
        
        assert response.content == "Hello! How can I help you?"
    
    @pytest.mark.asyncio
    async def test_vision_error_for_non_vision_model(self, provider_config):
        """Test error when using vision with non-vision model."""
        provider = OpenRouterProviderFull(provider_config)
        provider._is_initialized = True
        
        with pytest.raises(ValueError, match="does not support vision"):
            await provider.generate_with_vision(
                "What's in this image?",
                ["https://example.com/image.jpg"]
            )


# =============================================================================
# EMBEDDING TESTS
# =============================================================================

class TestEmbeddings:
    """Tests for embedding functionality."""
    
    @pytest.mark.asyncio
    async def test_single_embedding(self, provider_config):
        """Test single embedding generation."""
        provider = OpenRouterProviderFull(provider_config)
        
        mock_embedding_response = {
            "data": [
                {"embedding": [0.1, 0.2, 0.3, 0.4]}
            ]
        }
        
        mock_session = AsyncMock()
        mock_response_obj = AsyncMock()
        mock_response_obj.status = 200
        mock_response_obj.json = AsyncMock(return_value=mock_embedding_response)
        mock_session.post = MagicMock(return_value=mock_response_obj)
        mock_response_obj.__aenter__ = AsyncMock(return_value=mock_response_obj)
        mock_response_obj.__aexit__ = AsyncMock()
        
        provider._session = mock_session
        provider._is_initialized = True
        
        embedding = await provider.get_embedding("Hello world")
        
        assert embedding == [0.1, 0.2, 0.3, 0.4]
    
    @pytest.mark.asyncio
    async def test_batch_embeddings(self, provider_config):
        """Test batch embedding generation."""
        provider = OpenRouterProviderFull(provider_config)
        
        mock_embedding_response = {
            "data": [
                {"embedding": [0.1, 0.2]},
                {"embedding": [0.3, 0.4]}
            ]
        }
        
        mock_session = AsyncMock()
        mock_response_obj = AsyncMock()
        mock_response_obj.status = 200
        mock_response_obj.json = AsyncMock(return_value=mock_embedding_response)
        mock_session.post = MagicMock(return_value=mock_response_obj)
        mock_response_obj.__aenter__ = AsyncMock(return_value=mock_response_obj)
        mock_response_obj.__aexit__ = AsyncMock()
        
        provider._session = mock_session
        provider._is_initialized = True
        
        embeddings = await provider.get_embeddings(["Hello", "World"])
        
        assert len(embeddings) == 2
        assert embeddings[0] == [0.1, 0.2]
        assert embeddings[1] == [0.3, 0.4]


# =============================================================================
# UTILITY FUNCTION TESTS
# =============================================================================

class TestUtilityFunctions:
    """Tests for utility functions."""
    
    def test_create_openrouter_provider(self):
        """Test create_openrouter_provider function."""
        provider = create_openrouter_provider(
            api_key="test-key",
            model="anthropic/claude-3.5-sonnet"
        )
        
        assert isinstance(provider, OpenRouterProviderFull)
        assert provider.config.model == "anthropic/claude-3.5-sonnet"
    
    def test_get_available_models(self, provider_config):
        """Test getting available models."""
        provider = OpenRouterProviderFull(provider_config)
        models = provider.get_available_models()
        
        assert len(models) > 0
        assert "anthropic/claude-3.5-sonnet" in models
        assert "openai/gpt-4o" in models
    
    def test_count_tokens(self, provider_config):
        """Test token counting."""
        provider = OpenRouterProviderFull(provider_config)
        
        # Approximate: 4 chars per token
        count = asyncio.run(provider.count_tokens("Hello world"))
        assert count >= 0
    
    def test_calculate_cost(self, provider_config):
        """Test cost calculation."""
        provider = OpenRouterProviderFull(provider_config)
        
        # Free model should have 0 cost
        cost = provider.calculate_cost(100, 50)
        assert cost == 0.0
    
    def test_calculate_cost_premium_model(self):
        """Test cost calculation for premium model."""
        config = AIProviderConfig(
            provider_type=AIProviderType.OPENROUTER,
            api_key="test-key",
            model="anthropic/claude-3.5-sonnet"
        )
        provider = OpenRouterProviderFull(config)
        
        # Claude 3.5 Sonnet: $3/1M prompt, $15/1M completion
        cost = provider.calculate_cost(1000, 500)
        assert cost > 0


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================

class TestErrorHandling:
    """Tests for error handling."""
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self, provider_config):
        """Test API error handling."""
        provider = OpenRouterProviderFull(provider_config)
        
        mock_session = AsyncMock()
        mock_response_obj = AsyncMock()
        mock_response_obj.status = 500
        mock_response_obj.text = AsyncMock(return_value="Internal Server Error")
        mock_session.post = MagicMock(return_value=mock_response_obj)
        mock_response_obj.__aenter__ = AsyncMock(return_value=mock_response_obj)
        mock_response_obj.__aexit__ = AsyncMock()
        
        provider._session = mock_session
        provider._is_initialized = True
        
        with pytest.raises(Exception):
            await provider.generate_response("Hello!")
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, provider_config):
        """Test timeout handling."""
        provider = OpenRouterProviderFull(provider_config)
        
        mock_session = AsyncMock()
        mock_session.post = AsyncMock(side_effect=asyncio.TimeoutError())
        
        provider._session = mock_session
        provider._is_initialized = True
        
        with pytest.raises(TimeoutError):
            await provider.generate_response("Hello!")


# =============================================================================
# MODEL CONSTANTS TESTS
# =============================================================================

class TestModelConstants:
    """Tests for model constants."""
    
    def test_model_pricing_defined(self):
        """Test model pricing is defined for key models."""
        assert "anthropic/claude-3.5-sonnet" in MODEL_PRICING
        assert "openai/gpt-4o" in MODEL_PRICING
        assert "meta-llama/llama-3.1-8b-instruct:free" in MODEL_PRICING
    
    def test_context_lengths_defined(self):
        """Test context lengths are defined for key models."""
        assert MODEL_CONTEXT_LENGTHS["anthropic/claude-3.5-sonnet"] == 200000
        assert MODEL_CONTEXT_LENGTHS["openai/gpt-4o"] == 128000
    
    def test_vision_models_list(self):
        """Test vision models list."""
        assert "anthropic/claude-3.5-sonnet" in VISION_MODELS
        assert "openai/gpt-4o" in VISION_MODELS
        assert "meta-llama/llama-3.1-8b-instruct:free" not in VISION_MODELS
    
    def test_function_calling_models_list(self):
        """Test function calling models list."""
        assert "anthropic/claude-3.5-sonnet" in FUNCTION_CALLING_MODELS
        assert "openai/gpt-4o" in FUNCTION_CALLING_MODELS


# =============================================================================
# INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests (require API key)."""
    
    @pytest.mark.skip(reason="Requires valid API key")
    @pytest.mark.asyncio
    async def test_real_chat_completion(self):
        """Test real chat completion with API."""
        import os
        
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            pytest.skip("OPENROUTER_API_KEY not set")
        
        provider = create_openrouter_provider(
            api_key=api_key,
            model="meta-llama/llama-3.1-8b-instruct:free"
        )
        
        await provider.initialize()
        response = await provider.generate_response("Say 'hello'")
        
        assert response.content
        assert len(response.content) > 0
        
        await provider.close()


# =============================================================================
# RUN TESTS
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
