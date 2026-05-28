"""
Local Provider Implementation
Local model fallback for basic/free tiers
"""

import asyncio
import time
from typing import Optional, Dict, Any, List, AsyncIterator
import logging
import json

try:
    from ..base import AIProvider, AIProviderConfig, AIGenerationOptions
    from ..models import AIResponse, AIProviderType
except ImportError:
    from src.ai_providers.base import AIProvider, AIProviderConfig, AIGenerationOptions
    from src.ai_providers.models import AIResponse, AIProviderType

logger = logging.getLogger(__name__)


class LocalProvider(AIProvider):
    """
    Local model provider implementation
    
    This provider supports multiple backends:
    1. Ollama (local LLM server)
    2. LM Studio (local LLM server)
    3. Mock/echo responses for testing
    """
    
    AVAILABLE_MODELS = [
        "llama3.2",
        "llama3.1",
        "mistral",
        "mixtral",
        "codellama",
        "phi3",
        "gemma2",
        "qwen2.5",
        "mock",  # For testing
    ]
    
    MODEL_CONTEXT_LENGTHS = {
        "llama3.2": 128000,
        "llama3.1": 128000,
        "mistral": 32768,
        "mixtral": 32768,
        "codellama": 16384,
        "phi3": 128000,
        "gemma2": 8192,
        "qwen2.5": 32768,
        "mock": 4096,
    }
    
    # Local models are free
    MODEL_PRICING = {
        "llama3.2": {"prompt": 0.0, "completion": 0.0},
        "llama3.1": {"prompt": 0.0, "completion": 0.0},
        "mistral": {"prompt": 0.0, "completion": 0.0},
        "mixtral": {"prompt": 0.0, "completion": 0.0},
        "codellama": {"prompt": 0.0, "completion": 0.0},
        "phi3": {"prompt": 0.0, "completion": 0.0},
        "gemma2": {"prompt": 0.0, "completion": 0.0},
        "qwen2.5": {"prompt": 0.0, "completion": 0.0},
        "mock": {"prompt": 0.0, "completion": 0.0},
    }
    
    def __init__(self, config: AIProviderConfig):
        super().__init__(config)
        self._client = None
        self._base_url = config.base_url or "http://localhost:11434"  # Default Ollama
        
        # Set context length
        self._max_context = self.MODEL_CONTEXT_LENGTHS.get(config.model, 8192)
        
        # Local models generally don't support vision (except some)
        self.config.supports_vision = False
        
        # Free!
        self.config.cost_per_1k_prompt_tokens = 0.0
        self.config.cost_per_1k_completion_tokens = 0.0
    
    async def initialize(self) -> None:
        """Initialize local model client"""
        model = self.config.model
        
        if model == "mock":
            self._is_initialized = True
            logger.info("Local mock provider initialized")
            return
        
        # Try to connect to Ollama
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self._base_url}/api/tags", timeout=5.0)
                if response.status_code == 200:
                    self._is_initialized = True
                    logger.info(f"Local provider initialized with Ollama at {self._base_url}")
                    return
        except Exception as e:
            logger.warning(f"Could not connect to Ollama: {e}")
        
        # Try LM Studio format
        try:
            import httpx
            
            lm_studio_url = self.config.base_url or "http://localhost:1234"
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{lm_studio_url}/v1/models", timeout=5.0)
                if response.status_code == 200:
                    self._base_url = lm_studio_url
                    self._is_initialized = True
                    logger.info(f"Local provider initialized with LM Studio at {self._base_url}")
                    return
        except Exception as e:
            logger.warning(f"Could not connect to LM Studio: {e}")
        
        # Fall back to mock mode
        logger.warning("No local LLM server found, using mock responses")
        self.config.model = "mock"
        self._is_initialized = True
    
    async def generate_response(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        options: Optional[AIGenerationOptions] = None
    ) -> AIResponse:
        """Generate response from local model"""
        if not self._is_initialized:
            await self.initialize()
        
        options = options or AIGenerationOptions()
        start_time = time.time()
        
        # Handle mock mode
        if self.config.model == "mock":
            return await self._generate_mock_response(prompt, context, options, start_time)
        
        # Build messages for Ollama format
        messages = []
        
        if options.system_prompt:
            messages.append({"role": "system", "content": options.system_prompt})
        
        if context and "conversation_history" in context:
            for msg in context["conversation_history"]:
                messages.append({"role": msg["role"], "content": msg["content"]})
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            import httpx
            
            # Ollama API format
            payload = {
                "model": self.config.model,
                "messages": messages,
                "stream": False,
                "options": {
                    "num_predict": options.max_tokens or self.config.max_tokens,
                    "temperature": options.temperature if options.temperature is not None else self.config.temperature,
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self._base_url}/api/chat",
                    json=payload,
                    timeout=self.config.timeout,
                )
                
                if response.status_code != 200:
                    raise Exception(f"Ollama error: {response.text}")
                
                data = response.json()
                content = data.get("message", {}).get("content", "")
                
                latency_ms = int((time.time() - start_time) * 1000)
                
                # Ollama provides token counts
                eval_count = data.get("eval_count", 0)
                prompt_eval_count = data.get("prompt_eval_count", 0)
                
                return AIResponse(
                    request_id=options.request_id or "",
                    content=content,
                    tokens_used=eval_count + prompt_eval_count,
                    prompt_tokens=prompt_eval_count,
                    completion_tokens=eval_count,
                    model_used=self.config.model,
                    provider=AIProviderType.LOCAL,
                    latency_ms=latency_ms,
                )
                
        except Exception as e:
            logger.error(f"Local generation error: {e}")
            # Fall back to mock
            return await self._generate_mock_response(prompt, context, options, start_time)
    
    async def generate_stream(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        options: Optional[AIGenerationOptions] = None
    ) -> AsyncIterator[str]:
        """Generate streaming response from local model"""
        if not self._is_initialized:
            await self.initialize()
        
        options = options or AIGenerationOptions()
        
        # Handle mock mode
        if self.config.model == "mock":
            mock_response = f"I understand you're asking about: {prompt[:100]}... This is a simulated response for testing purposes."
            words = mock_response.split()
            for word in words:
                yield word + " "
                await asyncio.sleep(0.05)
            return
        
        # Build messages
        messages = []
        
        if options.system_prompt:
            messages.append({"role": "system", "content": options.system_prompt})
        
        if context and "conversation_history" in context:
            for msg in context["conversation_history"]:
                messages.append({"role": msg["role"], "content": msg["content"]})
        
        messages.append({"role": "user", "content": prompt})
        
        try:
            import httpx
            
            payload = {
                "model": self.config.model,
                "messages": messages,
                "stream": True,
                "options": {
                    "num_predict": options.max_tokens or self.config.max_tokens,
                    "temperature": options.temperature if options.temperature is not None else self.config.temperature,
                }
            }
            
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{self._base_url}/api/chat",
                    json=payload,
                    timeout=self.config.timeout,
                ) as response:
                    async for line in response.aiter_lines():
                        if line:
                            try:
                                data = json.loads(line)
                                if "message" in data:
                                    content = data["message"].get("content", "")
                                    if content:
                                        yield content
                            except json.JSONDecodeError:
                                continue
                                
        except Exception as e:
            logger.error(f"Local streaming error: {e}")
            yield f"Error: {str(e)}"
    
    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text using local model"""
        if not self._is_initialized:
            await self.initialize()
        
        # Handle mock mode
        if self.config.model == "mock":
            # Return deterministic pseudo-embedding based on text hash
            import hashlib
            hash_bytes = hashlib.sha256(text.encode()).digest()
            embedding = []
            for i in range(0, 64, 4):
                val = int.from_bytes(hash_bytes[i:i+4], 'big')
                embedding.append((val / (2**32 - 1)) * 2 - 1)
            return embedding[:384]  # Common small embedding size
        
        try:
            import httpx
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self._base_url}/api/embeddings",
                    json={
                        "model": self.config.model,
                        "prompt": text,
                    },
                    timeout=30.0,
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("embedding", [])
                else:
                    logger.warning(f"Embedding failed: {response.text}")
                    return [0.0] * 384
                    
        except Exception as e:
            logger.error(f"Local embedding error: {e}")
            return [0.0] * 384
    
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
        """Get available local models"""
        return self.AVAILABLE_MODELS
    
    async def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        # Approximate token count
        return len(text.split()) * 4 // 3
    
    def get_max_context_length(self) -> int:
        """Get max context length for current model"""
        return self._max_context
    
    async def _generate_mock_response(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]],
        options: AIGenerationOptions,
        start_time: float
    ) -> AIResponse:
        """Generate a mock response for testing"""
        
        # Simulate processing delay
        await asyncio.sleep(0.1)
        
        # Generate contextual mock response
        prompt_lower = prompt.lower()
        
        if "recommend" in prompt_lower:
            content = self._mock_recommendation_response(prompt, context)
        elif "consultation" in prompt_lower or "help" in prompt_lower:
            content = self._mock_consultation_response(prompt, context)
        elif "similar" in prompt_lower:
            content = self._mock_similar_response(prompt, context)
        else:
            content = f"I understand you're asking about: '{prompt[:100]}...'\n\nThis is a simulated response from the local AI provider. In production, this would be a real AI-generated response tailored to your query."
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        return AIResponse(
            request_id=options.request_id or "",
            content=content,
            tokens_used=len(content.split()),
            prompt_tokens=len(prompt.split()),
            completion_tokens=len(content.split()),
            model_used="mock",
            provider=AIProviderType.LOCAL,
            latency_ms=latency_ms,
        )
    
    def _mock_recommendation_response(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Generate mock recommendation response"""
        return f"""Based on your query, here are some recommendations:

1. **Local Business A** - Highly rated option nearby
   - Rating: 4.8/5 ⭐
   - Distance: 0.5 km
   - Category: Restaurant

2. **Local Business B** - Popular choice
   - Rating: 4.5/5 ⭐
   - Distance: 1.2 km
   - Category: Cafe

3. **Local Business C** - Budget-friendly option
   - Rating: 4.3/5 ⭐
   - Distance: 0.8 km
   - Category: Restaurant

*Note: This is mock data for demonstration purposes. Real recommendations would be personalized based on your preferences and history.*"""
    
    def _mock_consultation_response(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Generate mock consultation response"""
        return f"""Thank you for your question! I'd be happy to help you with that.

Here are some general suggestions based on your query:

1. Consider your specific needs and preferences
2. Compare different options available to you
3. Look for reviews and ratings from other users
4. Check for any promotions or discounts

Is there anything specific you'd like me to elaborate on?

*Note: This is a simulated response. In production, you would receive personalized AI-powered assistance.*"""
    
    def _mock_similar_response(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Generate mock similar items response"""
        return f"""Here are some similar options you might be interested in:

1. **Similar Item A** - 95% match
   - Same category with excellent reviews
   
2. **Similar Item B** - 89% match
   - Popular alternative with similar features

3. **Similar Item C** - 82% match
   - Budget-friendly alternative

*Note: This is mock data for testing purposes.*"""
