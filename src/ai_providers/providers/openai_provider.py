"""
OpenAI Provider Implementation
GPT models via OpenAI API
"""

import asyncio
import time
from typing import Optional, Dict, Any, List, AsyncIterator
import logging

from ..base import AIProvider, AIProviderConfig, AIGenerationOptions
from ..models import AIResponse, AIProviderType

logger = logging.getLogger(__name__)


class OpenAIProvider(AIProvider):
    """OpenAI GPT provider implementation"""
    
    AVAILABLE_MODELS = [
        "gpt-4o",
        "gpt-4o-mini",
        "gpt-4-turbo",
        "gpt-4",
        "gpt-3.5-turbo",
        "o1-preview",
        "o1-mini",
    ]
    
    MODEL_PRICING = {
        "gpt-4o": {"prompt": 0.0025, "completion": 0.01},
        "gpt-4o-mini": {"prompt": 0.00015, "completion": 0.0006},
        "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
        "gpt-4": {"prompt": 0.03, "completion": 0.06},
        "gpt-3.5-turbo": {"prompt": 0.0005, "completion": 0.0015},
        "o1-preview": {"prompt": 0.015, "completion": 0.06},
        "o1-mini": {"prompt": 0.003, "completion": 0.012},
    }
    
    MODEL_CONTEXT_LENGTHS = {
        "gpt-4o": 128000,
        "gpt-4o-mini": 128000,
        "gpt-4-turbo": 128000,
        "gpt-4": 8192,
        "gpt-3.5-turbo": 16385,
        "o1-preview": 128000,
        "o1-mini": 128000,
    }
    
    VISION_MODELS = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]
    
    def __init__(self, config: AIProviderConfig):
        super().__init__(config)
        self._client = None
        self._async_client = None
        
        # Set pricing based on model
        model = config.model
        if model in self.MODEL_PRICING:
            self.config.cost_per_1k_prompt_tokens = self.MODEL_PRICING[model]["prompt"]
            self.config.cost_per_1k_completion_tokens = self.MODEL_PRICING[model]["completion"]
        
        # Set context length
        self._max_context = self.MODEL_CONTEXT_LENGTHS.get(model, 8192)
        
        # Check vision support
        self.config.supports_vision = model in self.VISION_MODELS
    
    async def initialize(self) -> None:
        """Initialize OpenAI client"""
        try:
            from openai import AsyncOpenAI
            
            api_key = self.config.api_key
            if not api_key:
                import os
                api_key = os.getenv("OPENAI_API_KEY")
            
            if not api_key:
                raise ValueError("OpenAI API key not provided")
            
            self._async_client = AsyncOpenAI(
                api_key=api_key,
                base_url=self.config.base_url,
                timeout=self.config.timeout,
            )
            
            self._is_initialized = True
            logger.info(f"OpenAI provider initialized with model: {self.config.model}")
            
        except ImportError:
            raise ImportError("openai package not installed. Run: pip install openai")
    
    async def generate_response(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        options: Optional[AIGenerationOptions] = None
    ) -> AIResponse:
        """Generate response from OpenAI"""
        if not self._is_initialized:
            await self.initialize()
        
        options = options or AIGenerationOptions()
        start_time = time.time()
        
        # Build messages
        messages = []
        
        # Add system prompt
        system_prompt = options.system_prompt
        if context and "system_prompt" in context:
            system_prompt = context["system_prompt"]
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add conversation history
        if context and "conversation_history" in context:
            for msg in context["conversation_history"]:
                messages.append({"role": msg["role"], "content": msg["content"]})
        
        # Add current prompt
        messages.append({"role": "user", "content": prompt})
        
        # Build request params
        params = {
            "model": self.config.model,
            "messages": messages,
            "max_tokens": options.max_tokens or self.config.max_tokens,
            "temperature": options.temperature if options.temperature is not None else self.config.temperature,
        }
        
        if options.stop_sequences:
            params["stop"] = options.stop_sequences
        
        if options.response_format:
            params["response_format"] = options.response_format
        
        if options.tools:
            params["tools"] = options.tools
            if options.tool_choice:
                params["tool_choice"] = options.tool_choice
        
        if options.user_id:
            params["user"] = options.user_id
        
        try:
            response = await self._async_client.chat.completions.create(**params)
            
            content = response.choices[0].message.content or ""
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            return AIResponse(
                request_id=options.request_id or "",
                content=content,
                tokens_used=response.usage.total_tokens if response.usage else 0,
                prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
                completion_tokens=response.usage.completion_tokens if response.usage else 0,
                model_used=response.model,
                provider=AIProviderType.OPENAI,
                latency_ms=latency_ms,
                finish_reason=response.choices[0].finish_reason or "stop",
            )
            
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            raise
    
    async def generate_stream(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        options: Optional[AIGenerationOptions] = None
    ) -> AsyncIterator[str]:
        """Generate streaming response from OpenAI"""
        if not self._is_initialized:
            await self.initialize()
        
        options = options or AIGenerationOptions()
        
        # Build messages
        messages = []
        
        system_prompt = options.system_prompt
        if context and "system_prompt" in context:
            system_prompt = context["system_prompt"]
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        if context and "conversation_history" in context:
            for msg in context["conversation_history"]:
                messages.append({"role": msg["role"], "content": msg["content"]})
        
        messages.append({"role": "user", "content": prompt})
        
        params = {
            "model": self.config.model,
            "messages": messages,
            "max_tokens": options.max_tokens or self.config.max_tokens,
            "temperature": options.temperature if options.temperature is not None else self.config.temperature,
            "stream": True,
        }
        
        try:
            stream = await self._async_client.chat.completions.create(**params)
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"OpenAI streaming error: {e}")
            raise
    
    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using OpenAI"""
        if not self._is_initialized:
            await self.initialize()
        
        try:
            response = await self._async_client.embeddings.create(
                model="text-embedding-3-small",
                input=text,
            )
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            raise
    
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts"""
        if not self._is_initialized:
            await self.initialize()
        
        try:
            response = await self._async_client.embeddings.create(
                model="text-embedding-3-small",
                input=texts,
            )
            return [item.embedding for item in response.data]
            
        except Exception as e:
            logger.error(f"OpenAI batch embedding error: {e}")
            raise
    
    def supports_vision(self) -> bool:
        """Check if current model supports vision"""
        return self.config.supports_vision
    
    def get_model_name(self) -> str:
        """Get current model name"""
        return self.config.model
    
    def get_available_models(self) -> List[str]:
        """Get available OpenAI models"""
        return self.AVAILABLE_MODELS
    
    async def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        try:
            import tiktoken
            encoding = tiktoken.encoding_for_model(self.config.model)
            return len(encoding.encode(text))
        except ImportError:
            # Fallback: approximate token count
            return len(text.split()) * 4 // 3
        except Exception:
            return len(text.split()) * 4 // 3
    
    def get_max_context_length(self) -> int:
        """Get max context length for current model"""
        return self._max_context
    
    async def generate_with_vision(
        self,
        prompt: str,
        image_urls: List[str],
        context: Optional[Dict[str, Any]] = None,
        options: Optional[AIGenerationOptions] = None
    ) -> AIResponse:
        """Generate response with image inputs"""
        if not self.supports_vision():
            raise ValueError(f"Model {self.config.model} does not support vision")
        
        if not self._is_initialized:
            await self.initialize()
        
        options = options or AIGenerationOptions()
        start_time = time.time()
        
        # Build content with images
        content = [{"type": "text", "text": prompt}]
        for url in image_urls:
            content.append({
                "type": "image_url",
                "image_url": {"url": url}
            })
        
        messages = []
        if options.system_prompt:
            messages.append({"role": "system", "content": options.system_prompt})
        messages.append({"role": "user", "content": content})
        
        try:
            response = await self._async_client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                max_tokens=options.max_tokens or self.config.max_tokens,
            )
            
            content = response.choices[0].message.content or ""
            latency_ms = int((time.time() - start_time) * 1000)
            
            return AIResponse(
                request_id=options.request_id or "",
                content=content,
                tokens_used=response.usage.total_tokens if response.usage else 0,
                prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
                completion_tokens=response.usage.completion_tokens if response.usage else 0,
                model_used=response.model,
                provider=AIProviderType.OPENAI,
                latency_ms=latency_ms,
            )
            
        except Exception as e:
            logger.error(f"OpenAI vision error: {e}")
            raise
