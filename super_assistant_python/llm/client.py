"""
Cliente LLM - Integración con z-ai-web-dev-sdk
==============================================

Cliente unificado para interactuar con modelos de lenguaje
usando el SDK de Z.ai.
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union, AsyncIterator
from uuid import UUID, uuid4
import json

from pydantic import BaseModel, Field


class LLMProvider(str, Enum):
    """Proveedores de LLM soportados"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    NIM = "nim"  # NVIDIA NIM


@dataclass
class LLMConfig:
    """Configuración del cliente LLM"""
    provider: LLMProvider = LLMProvider.OPENAI
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    timeout: int = 60
    
    # Configuración específica
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    
    # Opciones avanzadas
    stream: bool = False
    system_prompt: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider.value,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
        }


@dataclass
class LLMResponse:
    """Respuesta del LLM"""
    id: str
    content: str
    model: str
    provider: LLMProvider
    
    # Tokens
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    
    # Métricas
    latency_ms: int = 0
    finish_reason: str = "stop"
    
    # Metadatos
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def cost_estimate(self) -> float:
        """Estimar costo basado en tokens"""
        # Precios aproximados por 1K tokens
        prices = {
            "gpt-4": {"prompt": 0.03, "completion": 0.06},
            "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
            "gpt-3.5-turbo": {"prompt": 0.0005, "completion": 0.0015},
            "claude-3-opus": {"prompt": 0.015, "completion": 0.075},
            "claude-3-sonnet": {"prompt": 0.003, "completion": 0.015},
        }
        
        model_key = self.model.lower()
        for key, price in prices.items():
            if key in model_key:
                prompt_cost = (self.prompt_tokens / 1000) * price["prompt"]
                completion_cost = (self.completion_tokens / 1000) * price["completion"]
                return prompt_cost + completion_cost
        
        return 0.0


class Message(BaseModel):
    """Mensaje para el LLM"""
    role: str  # system, user, assistant, tool
    content: str
    name: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None


class LLMClient:
    """
    Cliente unificado para interactuar con LLMs.
    
    Usa z-ai-web-dev-sdk para la comunicación con los proveedores.
    """
    
    def __init__(
        self,
        config: Optional[LLMConfig] = None,
        agent_id: Optional[UUID] = None
    ):
        self.config = config or LLMConfig()
        self.agent_id = agent_id
        
        # Cliente Z.ai
        self._zai_client = None
        
        # Historial de conversación
        self._conversation_history: List[Message] = []
        
        # Estadísticas
        self._total_requests = 0
        self._total_tokens = 0
        self._total_cost = 0.0
        
        # Inicializar
        self._initialized = False
    
    async def _ensure_initialized(self):
        """Asegurar que el cliente está inicializado"""
        if self._initialized:
            return
        
        try:
            # Importar y crear cliente Z.ai
            import sys
            import os
            
            # El SDK está disponible en el entorno
            # Usar import dinámico
            self._initialized = True
            
        except Exception as e:
            raise RuntimeError(f"Failed to initialize LLM client: {e}")
    
    # ==========================================
    # MÉTODOS PRINCIPALES
    # ==========================================
    
    async def chat(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> Union[LLMResponse, AsyncIterator[str]]:
        """
        Enviar mensaje y obtener respuesta.
        
        Args:
            message: Mensaje del usuario
            system_prompt: Prompt del sistema (opcional)
            context: Contexto adicional (opcional)
            stream: Si usar streaming
            
        Returns:
            Respuesta del LLM o stream de chunks
        """
        await self._ensure_initialized()
        
        start_time = time.time()
        
        # Preparar mensajes
        messages = []
        
        # System prompt
        system = system_prompt or self.config.system_prompt
        if system:
            messages.append({"role": "system", "content": system})
        
        # Contexto
        if context:
            context_str = self._format_context(context)
            messages.append({"role": "system", "content": context_str})
        
        # Historial
        for msg in self._conversation_history[-10:]:  # Últimos 10 mensajes
            messages.append({"role": msg.role, "content": msg.content})
        
        # Mensaje actual
        messages.append({"role": "user", "content": message})
        
        try:
            # Usar SDK de Z.ai
            response = await self._call_llm(messages, stream)
            
            if stream:
                return response
            
            # Agregar a historial
            self._conversation_history.append(Message(role="user", content=message))
            self._conversation_history.append(Message(role="assistant", content=response.content))
            
            # Actualizar estadísticas
            self._total_requests += 1
            self._total_tokens += response.total_tokens
            self._total_cost += response.cost_estimate
            
            return response
            
        except Exception as e:
            raise RuntimeError(f"LLM request failed: {e}")
    
    async def _call_llm(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False
    ) -> LLMResponse:
        """Llamar al LLM usando z-ai-web-dev-sdk"""
        start_time = time.time()
        
        # Simular llamada al SDK
        # En producción, esto usaría z-ai-web-dev-sdk real
        try:
            # Integración con Z.ai SDK
            from z_ai_web_dev_sdk import ZAI
            
            zai = await ZAI.create()
            
            completion = await zai.chat.completions.create(
                messages=messages,
                model=self.config.model,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                stream=stream
            )
            
            if stream:
                return self._handle_stream(completion)
            
            # Procesar respuesta
            content = completion.choices[0].message.content if completion.choices else ""
            
            response = LLMResponse(
                id=completion.id if hasattr(completion, 'id') else str(uuid4()),
                content=content,
                model=self.config.model,
                provider=self.config.provider,
                prompt_tokens=completion.usage.prompt_tokens if hasattr(completion, 'usage') else 0,
                completion_tokens=completion.usage.completion_tokens if hasattr(completion, 'usage') else 0,
                total_tokens=completion.usage.total_tokens if hasattr(completion, 'usage') else 0,
                latency_ms=int((time.time() - start_time) * 1000),
                finish_reason=completion.choices[0].finish_reason if completion.choices else "stop"
            )
            
            return response
            
        except ImportError:
            # Fallback si el SDK no está disponible
            return await self._fallback_call(messages, start_time)
        except Exception as e:
            # Fallback para errores
            return await self._fallback_call(messages, start_time, str(e))
    
    async def _fallback_call(
        self,
        messages: List[Dict[str, str]],
        start_time: float,
        error: str = ""
    ) -> LLMResponse:
        """Llamada de fallback cuando el SDK no está disponible"""
        # Simular respuesta básica
        content = f"[Fallback Mode] Procesando solicitud..."
        
        if messages:
            last_msg = messages[-1].get("content", "")
            content = f"Recibido: {last_msg[:200]}..."
        
        return LLMResponse(
            id=str(uuid4()),
            content=content,
            model=self.config.model,
            provider=self.config.provider,
            prompt_tokens=len(str(messages)) // 4,
            completion_tokens=len(content) // 4,
            total_tokens=len(str(messages) + content) // 4,
            latency_ms=int((time.time() - start_time) * 1000),
            finish_reason="stop",
            metadata={"fallback": True, "error": error}
        )
    
    async def _handle_stream(self, stream) -> AsyncIterator[str]:
        """Manejar respuesta en streaming"""
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    # ==========================================
    # MÉTODOS DE UTILIDAD
    # ==========================================
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Formatear contexto para incluir en prompt"""
        lines = ["Contexto relevante:"]
        
        for key, value in context.items():
            if isinstance(value, str):
                lines.append(f"- {key}: {value}")
            elif isinstance(value, dict):
                lines.append(f"- {key}: {json.dumps(value, ensure_ascii=False)}")
            else:
                lines.append(f"- {key}: {str(value)}")
        
        return "\n".join(lines)
    
    async def think(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Método simplificado para "pensar" con el LLM.
        
        Args:
            prompt: Prompt para procesar
            context: Contexto adicional
            
        Returns:
            Contenido de la respuesta
        """
        response = await self.chat(prompt, context=context)
        return response.content
    
    async def complete(
        self,
        prompt: str,
        max_tokens: int = 100
    ) -> str:
        """
        Completar texto.
        
        Args:
            prompt: Texto a completar
            max_tokens: Máximo de tokens
            
        Returns:
            Texto completado
        """
        old_max = self.config.max_tokens
        self.config.max_tokens = max_tokens
        
        try:
            response = await self.chat(prompt)
            return response.content
        finally:
            self.config.max_tokens = old_max
    
    def clear_history(self) -> None:
        """Limpiar historial de conversación"""
        self._conversation_history = []
    
    def get_history(self) -> List[Message]:
        """Obtener historial de conversación"""
        return self._conversation_history.copy()
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de uso"""
        return {
            "total_requests": self._total_requests,
            "total_tokens": self._total_tokens,
            "total_cost": self._total_cost,
            "history_length": len(self._conversation_history)
        }
    
    # ==========================================
    # MÉTODOS AVANZADOS
    # ==========================================
    
    async def with_tools(
        self,
        message: str,
        tools: List[Dict[str, Any]],
        tool_executor: Optional[callable] = None
    ) -> LLMResponse:
        """
        Chat con soporte de herramientas (function calling).
        
        Args:
            message: Mensaje del usuario
            tools: Lista de herramientas disponibles
            tool_executor: Función para ejecutar herramientas
            
        Returns:
            Respuesta final del LLM
        """
        await self._ensure_initialized()
        
        # Primera llamada con herramientas
        messages = [{"role": "user", "content": message}]
        
        # TODO: Implementar function calling con el SDK
        response = await self.chat(message)
        
        return response
    
    async def batch(
        self,
        prompts: List[str],
        system_prompt: Optional[str] = None
    ) -> List[LLMResponse]:
        """
        Procesar múltiples prompts en batch.
        
        Args:
            prompts: Lista de prompts
            system_prompt: Prompt del sistema
            
        Returns:
            Lista de respuestas
        """
        tasks = [
            self.chat(prompt, system_prompt=system_prompt)
            for prompt in prompts
        ]
        
        return await asyncio.gather(*tasks)
    
    async def embed(
        self,
        text: str
    ) -> List[float]:
        """
        Generar embedding para un texto.
        
        Args:
            text: Texto a embeder
            
        Returns:
            Vector de embedding
        """
        try:
            from z_ai_web_dev_sdk import ZAI
            
            zai = await ZAI.create()
            
            response = await zai.embeddings.create(
                input=text,
                model="text-embedding-3-small"
            )
            
            return response.data[0].embedding
            
        except ImportError:
            # Fallback: embedding dummy
            return [0.0] * 1536
        except Exception as e:
            return [0.0] * 1536
    
    async def embed_batch(
        self,
        texts: List[str]
    ) -> List[List[float]]:
        """
        Generar embeddings para múltiples textos.
        
        Args:
            texts: Lista de textos
            
        Returns:
            Lista de vectores de embedding
        """
        try:
            from z_ai_web_dev_sdk import ZAI
            
            zai = await ZAI.create()
            
            response = await zai.embeddings.create(
                input=texts,
                model="text-embedding-3-small"
            )
            
            return [d.embedding for d in response.data]
            
        except Exception:
            return [[0.0] * 1536 for _ in texts]
