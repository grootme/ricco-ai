"""
Proveedores de LLM
==================

Implementaciones específicas para cada proveedor de LLM.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from .client import LLMConfig, LLMResponse, Message


class BaseLLMProvider(ABC):
    """Clase base para proveedores de LLM"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
    
    @abstractmethod
    async def complete(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> LLMResponse:
        """Completar secuencia de mensajes"""
        pass
    
    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Generar embedding"""
        pass


class OpenAIProvider(BaseLLMProvider):
    """
    Proveedor para OpenAI (GPT-4, GPT-3.5, etc.)
    
    Usa z-ai-web-dev-sdk para la comunicación.
    """
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._client = None
    
    async def _get_client(self):
        if self._client is None:
            try:
                from z_ai_web_dev_sdk import ZAI
                self._client = await ZAI.create()
            except ImportError:
                raise RuntimeError("z-ai-web-dev-sdk not available")
        return self._client
    
    async def complete(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> LLMResponse:
        start_time = time.time()
        
        client = await self._get_client()
        
        completion = await client.chat.completions.create(
            messages=messages,
            model=kwargs.get("model", self.config.model),
            temperature=kwargs.get("temperature", self.config.temperature),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
        )
        
        content = completion.choices[0].message.content if completion.choices else ""
        
        return LLMResponse(
            id=completion.id if hasattr(completion, 'id') else "",
            content=content,
            model=self.config.model,
            provider=self.config.provider,
            prompt_tokens=completion.usage.prompt_tokens if hasattr(completion, 'usage') and completion.usage else 0,
            completion_tokens=completion.usage.completion_tokens if hasattr(completion, 'usage') and completion.usage else 0,
            total_tokens=completion.usage.total_tokens if hasattr(completion, 'usage') and completion.usage else 0,
            latency_ms=int((time.time() - start_time) * 1000)
        )
    
    async def embed(self, text: str) -> List[float]:
        client = await self._get_client()
        
        response = await client.embeddings.create(
            input=text,
            model="text-embedding-3-small"
        )
        
        return response.data[0].embedding


class AnthropicProvider(BaseLLMProvider):
    """
    Proveedor para Anthropic (Claude)
    
    Usa z-ai-web-dev-sdk o cliente directo de Anthropic.
    """
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._client = None
    
    async def _get_client(self):
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.AsyncAnthropic()
            except ImportError:
                raise RuntimeError("anthropic package not installed")
        return self._client
    
    async def complete(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> LLMResponse:
        start_time = time.time()
        
        client = await self._get_client()
        
        # Separar system prompt
        system = ""
        chat_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                chat_messages.append(msg)
        
        completion = await client.messages.create(
            model=kwargs.get("model", self.config.model),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            temperature=kwargs.get("temperature", self.config.temperature),
            system=system,
            messages=chat_messages
        )
        
        content = completion.content[0].text if completion.content else ""
        
        return LLMResponse(
            id=completion.id,
            content=content,
            model=self.config.model,
            provider=self.config.provider,
            prompt_tokens=completion.usage.input_tokens,
            completion_tokens=completion.usage.output_tokens,
            total_tokens=completion.usage.input_tokens + completion.usage.output_tokens,
            latency_ms=int((time.time() - start_time) * 1000)
        )
    
    async def embed(self, text: str) -> List[float]:
        # Anthropic no tiene endpoint de embeddings directo
        # Usar OpenAI como fallback
        raise NotImplementedError("Anthropic does not provide embeddings API")


class LocalProvider(BaseLLMProvider):
    """
    Proveedor para modelos locales (Ollama, LM Studio, etc.)
    """
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.base_url = config.base_url or "http://localhost:11434"
    
    async def complete(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> LLMResponse:
        start_time = time.time()
        
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": kwargs.get("model", self.config.model),
                "messages": messages,
                "temperature": kwargs.get("temperature", self.config.temperature),
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
                "stream": False
            }
            
            async with session.post(
                f"{self.base_url}/api/chat",
                json=payload
            ) as response:
                result = await response.json()
        
        content = result.get("message", {}).get("content", "")
        
        return LLMResponse(
            id=str(time.time()),
            content=content,
            model=self.config.model,
            provider=self.config.provider,
            prompt_tokens=result.get("prompt_eval_count", 0),
            completion_tokens=result.get("eval_count", 0),
            total_tokens=result.get("prompt_eval_count", 0) + result.get("eval_count", 0),
            latency_ms=int((time.time() - start_time) * 1000)
        )
    
    async def embed(self, text: str) -> List[float]:
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": "nomic-embed-text",
                "input": text
            }
            
            async with session.post(
                f"{self.base_url}/api/embeddings",
                json=payload
            ) as response:
                result = await response.json()
        
        return result.get("embedding", [])


class NIMProvider(BaseLLMProvider):
    """
    Proveedor para NVIDIA NIM (NeMo Inference Microservice)
    
    NVIDIA NIM proporciona acceso a modelos optimizados para
    inferencia en GPU NVIDIA.
    """
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.base_url = config.base_url or "https://integrate.api.nvidia.com/v1"
        self.api_key = config.api_key
    
    async def complete(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> LLMResponse:
        start_time = time.time()
        
        import aiohttp
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": kwargs.get("model", self.config.model),
            "messages": messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                result = await response.json()
        
        content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        return LLMResponse(
            id=result.get("id", ""),
            content=content,
            model=self.config.model,
            provider=self.config.provider,
            prompt_tokens=result.get("usage", {}).get("prompt_tokens", 0),
            completion_tokens=result.get("usage", {}).get("completion_tokens", 0),
            total_tokens=result.get("usage", {}).get("total_tokens", 0),
            latency_ms=int((time.time() - start_time) * 1000)
        )
    
    async def embed(self, text: str) -> List[float]:
        import aiohttp
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "nvidia/embed-qa-4",
            "input": text,
            "input_type": "query"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/embeddings",
                headers=headers,
                json=payload
            ) as response:
                result = await response.json()
        
        return result.get("data", [{}])[0].get("embedding", [])
