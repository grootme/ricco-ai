"""
OpenRouter Provider - AI Provider implementation for OpenRouter API

Implementa la interfaz de AI Provider para usar modelos de OpenRouter.
Soporta streaming, chat completions y multi-turn conversations.
"""

import asyncio
import aiohttp
from typing import Optional, Dict, Any, List, AsyncIterator, Callable
from dataclasses import dataclass
import json
import logging

from ...config.openrouter_config import OpenRouterConfig, OpenRouterModel, get_openrouter_config

logger = logging.getLogger(__name__)


@dataclass
class OpenRouterProviderConfig:
    """Configuración específica del provider OpenRouter"""
    model: str = "meta-llama/llama-3-8b-instruct:free"
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 1.0
    stream: bool = True


class OpenRouterProvider:
    """
    Provider para OpenRouter API.
    
    OpenRouter permite acceder a múltiples modelos LLM a través de una sola API.
    Incluye modelos gratuitos como Llama 3, Mistral 7B, Gemma, etc.
    
    Usage:
        provider = OpenRouterProvider(
            api_key="sk-or-v1-...",
            model="meta-llama/llama-3-8b-instruct:free"
        )
        
        # Chat completion
        response = await provider.chat_completion(messages)
        
        # Streaming
        async for chunk in provider.stream_chat(messages):
            print(chunk)
    """
    
    def __init__(
        self,
        config: Optional[OpenRouterProviderConfig] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        openrouter_config: Optional[OpenRouterConfig] = None
    ):
        """
        Inicializa el provider de OpenRouter.
        
        Args:
            config: Configuración del provider
            api_key: API key de OpenRouter (opcional, usa env var si no se especifica)
            model: Modelo a usar (opcional)
            openrouter_config: Configuración de OpenRouter (opcional)
        """
        self.config = config or OpenRouterProviderConfig()
        self._openrouter_config = openrouter_config or get_openrouter_config()
        
        # Override API key si se especifica
        if api_key:
            self._openrouter_config.api_key = api_key
        
        # Override model si se especifica
        if model:
            self.config.model = model
        
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Obtiene o crea la sesión HTTP"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers=self._openrouter_config.get_headers(),
                timeout=aiohttp.ClientTimeout(total=self._openrouter_config.timeout)
            )
        return self._session
    
    async def close(self) -> None:
        """Cierra la sesión HTTP"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Realiza un chat completion.
        
        Args:
            messages: Lista de mensajes de la conversación
            system_prompt: System prompt opcional
            temperature: Temperatura de sampling
            max_tokens: Máximo de tokens a generar
            
        Returns:
            Respuesta del modelo
        """
        session = await self._get_session()
        
        # Construir lista de mensajes
        formatted_messages = []
        if system_prompt:
            formatted_messages.append({
                "role": "system",
                "content": system_prompt
            })
        formatted_messages.extend(messages)
        
        payload = {
            "model": self.config.model,
            "messages": formatted_messages,
            "max_tokens": max_tokens or self.config.max_tokens,
            "temperature": temperature or self.config.temperature,
            **kwargs
        }
        
        try:
            async with session.post(
                f"{self._openrouter_config.base_url}/chat/completions",
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"OpenRouter API error: {response.status} - {error_text}")
                    return {
                        "error": True,
                        "status_code": response.status,
                        "message": error_text
                    }
                
                result = await response.json()
                return {
                    "success": True,
                    "content": result["choices"][0]["message"]["content"],
                    "model": result.get("model"),
                    "usage": result.get("usage", {}),
                    "raw_response": result
                }
                
        except asyncio.TimeoutError:
            logger.error("OpenRouter request timed out")
            return {"error": True, "message": "Request timed out"}
        except Exception as e:
            logger.error(f"OpenRouter request failed: {e}")
            return {"error": True, "message": str(e)}
    
    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        on_chunk: Optional[Callable[[str], None]] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Realiza un chat completion con streaming.
        
        Yields chunks de texto a medida que se generan.
        
        Args:
            messages: Lista de mensajes de la conversación
            system_prompt: System prompt opcional
            temperature: Temperatura de sampling
            max_tokens: Máximo de tokens a generar
            on_chunk: Callback opcional para cada chunk
            
        Yields:
            Chunks de texto generados
        """
        session = await self._get_session()
        
        # Construir lista de mensajes
        formatted_messages = []
        if system_prompt:
            formatted_messages.append({
                "role": "system",
                "content": system_prompt
            })
        formatted_messages.extend(messages)
        
        payload = {
            "model": self.config.model,
            "messages": formatted_messages,
            "max_tokens": max_tokens or self.config.max_tokens,
            "temperature": temperature or self.config.temperature,
            "stream": True,
            **kwargs
        }
        
        full_response = ""
        
        try:
            async with session.post(
                f"{self._openrouter_config.base_url}/chat/completions",
                json=payload
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(f"OpenRouter streaming error: {response.status} - {error_text}")
                    yield f"[ERROR: {error_text}]"
                    return
                
                async for line in response.content:
                    line_text = line.decode('utf-8').strip()
                    
                    if not line_text or line_text == "data: [DONE]":
                        continue
                    
                    if line_text.startswith("data: "):
                        try:
                            data = json.loads(line_text[6:])
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                content = delta.get("content", "")
                                
                                if content:
                                    full_response += content
                                    if on_chunk:
                                        on_chunk(content)
                                    yield content
                                    
                        except json.JSONDecodeError:
                            continue
                            
        except asyncio.TimeoutError:
            logger.error("OpenRouter streaming timed out")
            yield "[ERROR: Request timed out]"
        except Exception as e:
            logger.error(f"OpenRouter streaming failed: {e}")
            yield f"[ERROR: {str(e)}]"
    
    async def embed(self, text: str, **kwargs) -> List[float]:
        """
        Genera embeddings para un texto.
        
        Nota: OpenRouter no soporta embeddings directamente.
        Este método está incluido por compatibilidad de interfaz.
        """
        raise NotImplementedError(
            "OpenRouter no soporta embeddings directamente. "
            "Use un provider diferente para embeddings."
        )
    
    def get_model_name(self) -> str:
        """Obtiene el nombre del modelo actual"""
        return self.config.model
    
    def get_available_models(self) -> List[str]:
        """Obtiene lista de modelos disponibles"""
        return self._openrouter_config.get_model_list()
    
    def is_free_model(self) -> bool:
        """Verifica si el modelo actual es gratuito"""
        return self._openrouter_config.is_free_model(self.config.model)
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Prueba la conexión con OpenRouter.
        
        Returns:
            Dict con resultado de la prueba
        """
        try:
            result = await self.chat_completion(
                messages=[{"role": "user", "content": "Hello, respond with 'OK'"}],
                max_tokens=10
            )
            
            if result.get("success"):
                return {
                    "success": True,
                    "model": self.config.model,
                    "is_free": self.is_free_model(),
                    "response": result.get("content", "")[:50]
                }
            else:
                return {
                    "success": False,
                    "error": result.get("message", "Unknown error")
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def analyze_with_context(
        self,
        query: str,
        context: Dict[str, Any],
        obviousness_prompt: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Analiza una query con contexto de obviedad.
        
        Args:
            query: Query del usuario
            context: Contexto de obviedad (SMART+R+T)
            obviousness_prompt: Prompt de trasfondo de obviedad
            
        Returns:
            Análisis con razonamiento
        """
        # Construir prompt con contexto
        system_prompt = obviousness_prompt or self._build_obviousness_prompt(context)
        
        messages = [
            {
                "role": "user",
                "content": f"""Analiza la siguiente solicitud y responde de forma estructurada:

QUERY: {query}

CONTEXTO:
{json.dumps(context, indent=2, ensure_ascii=False)}

Proporciona:
1. Entendimiento de la solicitud
2. Análisis de viabilidad
3. Pasos recomendados
4. Posibles riesgos o consideraciones
"""
            }
        ]
        
        return await self.chat_completion(
            messages=messages,
            system_prompt=system_prompt,
            **kwargs
        )
    
    def _build_obviousness_prompt(self, context: Dict[str, Any]) -> str:
        """Construye el system prompt desde el contexto de obviedad"""
        prompt_parts = ["# TRASFONDO DE OBVIEDAD\n"]
        
        # S - Finalidad
        if "objective" in context:
            prompt_parts.append(f"## Objetivo\n{context['objective']}\n")
        
        # M - Métricas
        if "metrics" in context or "target_recall" in context:
            prompt_parts.append("## Métricas de Éxito")
            if "target_recall" in context:
                prompt_parts.append(f"- Recall objetivo: {context.get('target_recall')}")
            if "target_precision" in context:
                prompt_parts.append(f"- Precision objetivo: {context.get('target_precision')}")
        
        # A - Alcance
        if "positive_boundaries" in context or "negative_boundaries" in context:
            prompt_parts.append("## Alcance")
            if context.get("positive_boundaries"):
                prompt_parts.append(f"Permitido: {', '.join(context['positive_boundaries'])}")
            if context.get("negative_boundaries"):
                prompt_parts.append(f"Prohibido: {', '.join(context['negative_boundaries'])}")
        
        # R - Relevancia
        if "organizational_impact" in context:
            prompt_parts.append(f"## Impacto Organizacional: {context['organizational_impact']}")
        
        # T - Tiempo
        if "priority" in context:
            prompt_parts.append(f"## Prioridad: {context['priority']}")
        
        prompt_parts.append("\n## Instrucciones")
        prompt_parts.append("1. Analiza cuidadosamente antes de responder")
        prompt_parts.append("2. Considera todas las restricciones definidas")
        prompt_parts.append("3. Proporciona respuestas estructuradas y claras")
        
        return "\n".join(prompt_parts)
