"""
Anthropic Provider Implementation
Claude models via Anthropic API
"""

import asyncio
import time
from typing import Optional, Dict, Any, List, AsyncIterator
import logging

try:
    from ..base import AIProvider, AIProviderConfig, AIGenerationOptions
    from ..models import AIResponse, AIProviderType
except ImportError:
    from src.ai_providers.base import AIProvider, AIProviderConfig, AIGenerationOptions
    from src.ai_providers.models import AIResponse, AIProviderType

logger = logging.getLogger(__name__)


class AnthropicProvider(AIProvider):
    """Anthropic Claude provider implementation"""
    
    AVAILABLE_MODELS = [
        "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022",
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
    ]
    
    MODEL_PRICING = {
        "claude-3-5-sonnet-20241022": {"prompt": 0.003, "completion": 0.015},
        "claude-3-5-haiku-20241022": {"prompt": 0.0008, "completion": 0.004},
        "claude-3-opus-20240229": {"prompt": 0.015, "completion": 0.075},
        "claude-3-sonnet-20240229": {"prompt": 0.003, "completion": 0.015},
        "claude-3-haiku-20240307": {"prompt": 0.00025, "completion": 0.00125},
    }
    
    MODEL_CONTEXT_LENGTHS = {
        "claude-3-5-sonnet-20241022": 200000,
        "claude-3-5-haiku-20241022": 200000,
        "claude-3-opus-20240229": 200000,
        "claude-3-sonnet-20240229": 200000,
        "claude-3-haiku-20240307": 200000,
    }
    
    # All Claude 3 models support vision
    VISION_MODELS = AVAILABLE_MODELS
    
    def __init__(self, config: AIProviderConfig):
        super().__init__(config)
        self._client = None
        
        # Set pricing based on model
        model = config.model
        if model in self.MODEL_PRICING:
            self.config.cost_per_1k_prompt_tokens = self.MODEL_PRICING[model]["prompt"]
            self.config.cost_per_1k_completion_tokens = self.MODEL_PRICING[model]["completion"]
        
        # Set context length
        self._max_context = self.MODEL_CONTEXT_LENGTHS.get(model, 200000)
        
        # All Claude models support vision
        self.config.supports_vision = True
    
    async def initialize(self) -> None:
        """Initialize Anthropic client"""
        try:
            from anthropic import AsyncAnthropic
            
            api_key = self.config.api_key
            if not api_key:
                import os
                api_key = os.getenv("ANTHROPIC_API_KEY")
            
            if not api_key:
                raise ValueError("Anthropic API key not provided")
            
            self._client = AsyncAnthropic(
                api_key=api_key,
                base_url=self.config.base_url,
                timeout=self.config.timeout,
            )
            
            self._is_initialized = True
            logger.info(f"Anthropic provider initialized with model: {self.config.model}")
            
        except ImportError:
            raise ImportError("anthropic package not installed. Run: pip install anthropic")
    
    async def generate_response(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        options: Optional[AIGenerationOptions] = None
    ) -> AIResponse:
        """Generate response from Anthropic Claude"""
        if not self._is_initialized:
            await self.initialize()
        
        options = options or AIGenerationOptions()
        start_time = time.time()
        
        # Build system prompt
        system_prompt = options.system_prompt
        if context and "system_prompt" in context:
            system_prompt = context["system_prompt"]
        
        # Build messages
        messages = []
        
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
        }
        
        if system_prompt:
            params["system"] = system_prompt
        
        if options.temperature is not None:
            params["temperature"] = options.temperature
        elif self.config.temperature != 0.7:
            params["temperature"] = self.config.temperature
        
        if options.stop_sequences:
            params["stop_sequences"] = options.stop_sequences
        
        if options.tools:
            params["tools"] = self._convert_tools(options.tools)
        
        try:
            response = await self._client.messages.create(**params)
            
            # Extract text content
            content = ""
            for block in response.content:
                if hasattr(block, "text"):
                    content += block.text
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            return AIResponse(
                request_id=options.request_id or "",
                content=content,
                tokens_used=response.usage.input_tokens + response.usage.output_tokens,
                prompt_tokens=response.usage.input_tokens,
                completion_tokens=response.usage.output_tokens,
                model_used=response.model,
                provider=AIProviderType.ANTHROPIC,
                latency_ms=latency_ms,
                finish_reason=response.stop_reason or "stop",
            )
            
        except Exception as e:
            logger.error(f"Anthropic generation error: {e}")
            raise
    
    async def generate_stream(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        options: Optional[AIGenerationOptions] = None
    ) -> AsyncIterator[str]:
        """Generate streaming response from Anthropic"""
        if not self._is_initialized:
            await self.initialize()
        
        options = options or AIGenerationOptions()
        
        # Build system prompt
        system_prompt = options.system_prompt
        if context and "system_prompt" in context:
            system_prompt = context["system_prompt"]
        
        # Build messages
        messages = []
        
        if context and "conversation_history" in context:
            for msg in context["conversation_history"]:
                messages.append({"role": msg["role"], "content": msg["content"]})
        
        messages.append({"role": "user", "content": prompt})
        
        params = {
            "model": self.config.model,
            "messages": messages,
            "max_tokens": options.max_tokens or self.config.max_tokens,
            "stream": True,
        }
        
        if system_prompt:
            params["system"] = system_prompt
        
        if options.temperature is not None:
            params["temperature"] = options.temperature
        
        try:
            async with self._client.messages.stream(**params) as stream:
                async for text in stream.text_stream:
                    yield text
                    
        except Exception as e:
            logger.error(f"Anthropic streaming error: {e}")
            raise
    
    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using Anthropic/Voyage"""
        # Anthropic doesn't have embeddings API directly, use a fallback
        # In production, you'd use Voyage AI or OpenAI embeddings
        if not self._is_initialized:
            await self.initialize()
        
        try:
            # Try using OpenAI embeddings as fallback
            from openai import AsyncOpenAI
            import os
            
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key:
                client = AsyncOpenAI(api_key=openai_key)
                response = await client.embeddings.create(
                    model="text-embedding-3-small",
                    input=text,
                )
                return response.data[0].embedding
            else:
                # Return dummy embedding for development
                logger.warning("No embedding provider available, returning zero vector")
                return [0.0] * 1536
                
        except Exception as e:
            logger.error(f"Embedding error: {e}")
            return [0.0] * 1536
    
    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts"""
        embeddings = []
        for text in texts:
            embedding = await self.get_embedding(text)
            embeddings.append(embedding)
        return embeddings
    
    def supports_vision(self) -> bool:
        """Check if current model supports vision"""
        return self.config.supports_vision
    
    def get_model_name(self) -> str:
        """Get current model name"""
        return self.config.model
    
    def get_available_models(self) -> List[str]:
        """Get available Anthropic models"""
        return self.AVAILABLE_MODELS
    
    async def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        # Claude uses approximately 4 characters per token
        return len(text) // 4
    
    def get_max_context_length(self) -> int:
        """Get max context length for current model"""
        return self._max_context
    
    def _convert_tools(self, openai_tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert OpenAI-style tools to Anthropic format"""
        anthropic_tools = []
        for tool in openai_tools:
            if tool.get("type") == "function":
                func = tool.get("function", {})
                anthropic_tools.append({
                    "name": func.get("name", ""),
                    "description": func.get("description", ""),
                    "input_schema": func.get("parameters", {}),
                })
        return anthropic_tools
    
    async def generate_with_vision(
        self,
        prompt: str,
        image_urls: List[str],
        context: Optional[Dict[str, Any]] = None,
        options: Optional[AIGenerationOptions] = None
    ) -> AIResponse:
        """Generate response with image inputs"""
        if not self._is_initialized:
            await self.initialize()
        
        options = options or AIGenerationOptions()
        start_time = time.time()
        
        # Build content with images
        content = []
        
        # Add images first
        for url in image_urls:
            # Determine media type from URL
            media_type = "image/jpeg"
            if url.endswith(".png"):
                media_type = "image/png"
            elif url.endswith(".gif"):
                media_type = "image/gif"
            elif url.endswith(".webp"):
                media_type = "image/webp"
            
            # For URLs, we need to fetch and encode
            if url.startswith("http"):
                import base64
                import httpx
                
                async with httpx.AsyncClient() as client:
                    response = await client.get(url)
                    image_data = base64.b64encode(response.content).decode("utf-8")
                
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_data,
                    }
                })
            else:
                # Assume base64 data
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": url,
                    }
                })
        
        # Add text prompt
        content.append({"type": "text", "text": prompt})
        
        messages = [{"role": "user", "content": content}]
        
        params = {
            "model": self.config.model,
            "messages": messages,
            "max_tokens": options.max_tokens or self.config.max_tokens,
        }
        
        if options.system_prompt:
            params["system"] = options.system_prompt
        
        try:
            response = await self._client.messages.create(**params)
            
            text_content = ""
            for block in response.content:
                if hasattr(block, "text"):
                    text_content += block.text
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            return AIResponse(
                request_id=options.request_id or "",
                content=text_content,
                tokens_used=response.usage.input_tokens + response.usage.output_tokens,
                prompt_tokens=response.usage.input_tokens,
                completion_tokens=response.usage.output_tokens,
                model_used=response.model,
                provider=AIProviderType.ANTHROPIC,
                latency_ms=latency_ms,
            )
            
        except Exception as e:
            logger.error(f"Anthropic vision error: {e}")
            raise
