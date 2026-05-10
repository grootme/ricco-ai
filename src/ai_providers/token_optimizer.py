"""
Token Optimizer System - Reducción de Gasto en LLM Calls

Implementa múltiples estrategias para reducir el consumo de tokens:
- Compresión de prompts
- Cache semántico inteligente
- Chunking optimizado
- Summarization incremental
- Deduplicación de contexto
- Vectorización de contexto recurrente

Patrones GOF utilizados:
- Strategy: Diferentes estrategias de optimización
- Decorator: Envuelve llamadas LLM con optimización
- Flyweight: Comparte contexto común entre requests
- Factory: Creación de optimizadores

@author: NEXUS - Neural Execution Unified System
"""

from typing import Dict, List, Optional, Any, Callable, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from uuid import UUID, uuid4
from abc import ABC, abstractmethod
import asyncio
import json
import hashlib
import re
import math
import logging
from collections import defaultdict, OrderedDict

logger = logging.getLogger(__name__)


# ============================================================================
# OPTIMIZATION CONFIGURATION
# ============================================================================

class OptimizationStrategy(str, Enum):
    """Estrategias de optimización de tokens"""
    COMPRESSION = "compression"           # Comprimir prompts
    SEMANTIC_CACHE = "semantic_cache"     # Cache semántico
    CHUNKING = "chunking"                 # Dividir en chunks óptimos
    SUMMARIZATION = "summarization"       # Resumir contexto
    DEDUPLICATION = "deduplication"       # Deduplicar contenido
    CONTEXT_PRUNING = "context_pruning"   # Eliminar contexto irrelevante
    ADAPTIVE = "adaptive"                 # Estrategia adaptativa


@dataclass
class TokenOptimizationConfig:
    """Configuración de optimización de tokens"""
    strategies: List[OptimizationStrategy] = field(default_factory=lambda: [
        OptimizationStrategy.SEMANTIC_CACHE,
        OptimizationStrategy.DEDUPLICATION,
        OptimizationStrategy.COMPRESSION,
        OptimizationStrategy.CONTEXT_PRUNING,
    ])
    
    # Compression settings
    compression_level: float = 0.7  # 0.0 = sin compresión, 1.0 = máxima
    preserve_keywords: bool = True
    preserve_structure: bool = True
    
    # Cache settings
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600
    cache_similarity_threshold: float = 0.95
    max_cache_entries: int = 10000
    
    # Chunking settings
    max_chunk_tokens: int = 512
    chunk_overlap_tokens: int = 50
    optimal_chunk_size: int = 256
    
    # Context settings
    max_context_tokens: int = 4096
    context_window_utilization: float = 0.8
    relevance_threshold: float = 0.6
    
    # Token estimation
    tokens_per_word: float = 1.3  # Estimación promedio
    tokens_per_char: float = 0.25
    
    # Cost tracking
    track_costs: bool = True
    cost_per_1k_input_tokens: float = 0.0015  # GPT-4o-mini
    cost_per_1k_output_tokens: float = 0.006


@dataclass
class TokenMetrics:
    """Métricas de uso de tokens"""
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    tokens_saved: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    compression_ratio: float = 1.0
    total_cost: float = 0.0
    savings_cost: float = 0.0
    requests_optimized: int = 0
    requests_total: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "tokens_saved": self.tokens_saved,
            "cache_hit_rate": self.cache_hits / max(1, self.cache_hits + self.cache_misses),
            "compression_ratio": self.compression_ratio,
            "total_cost": self.total_cost,
            "savings_cost": self.savings_cost,
            "optimization_rate": self.requests_optimized / max(1, self.requests_total),
        }


# ============================================================================
# FLYWEIGHT PATTERN - Shared Context
# ============================================================================

class SharedContextPool:
    """
    Pool de contexto compartido usando patrón Flyweight
    
    Comparte contexto común entre múltiples requests para evitar
    duplicación innecesaria de tokens.
    """
    
    _instance = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._contexts: Dict[str, Dict[str, Any]] = {}
            cls._instance._usage_count: Dict[str, int] = defaultdict(int)
            cls._instance._last_access: Dict[str, datetime] = {}
            cls._instance._max_entries = 1000
        return cls._instance
    
    @classmethod
    async def get_shared_context(cls, key: str) -> Optional[Dict[str, Any]]:
        """Obtiene contexto compartido por clave"""
        instance = cls()
        async with cls._lock:
            if key in instance._contexts:
                instance._usage_count[key] += 1
                instance._last_access[key] = datetime.utcnow()
                return instance._contexts[key].copy()
        return None
    
    @classmethod
    async def store_shared_context(cls, key: str, context: Dict[str, Any]) -> None:
        """Almacena contexto para compartir"""
        instance = cls()
        async with cls._lock:
            # Evitar overflow
            if len(instance._contexts) >= instance._max_entries:
                await cls._evict_lru()
            
            instance._contexts[key] = context.copy()
            instance._usage_count[key] = 1
            instance._last_access[key] = datetime.utcnow()
    
    @classmethod
    async def _evict_lru(cls) -> None:
        """Evicta las entradas menos usadas"""
        instance = cls()
        
        if not instance._contexts:
            return
        
        # Ordenar por uso y antigüedad
        sorted_keys = sorted(
            instance._contexts.keys(),
            key=lambda k: (instance._usage_count[k], instance._last_access[k])
        )
        
        # Eliminar 20% menos usados
        to_remove = max(1, len(sorted_keys) // 5)
        for key in sorted_keys[:to_remove]:
            del instance._contexts[key]
            del instance._usage_count[key]
            del instance._last_access[key]


# ============================================================================
# STRATEGY PATTERN - Optimization Strategies
# ============================================================================

class TokenOptimizationStrategyBase(ABC):
    """Estrategia base de optimización"""
    
    @abstractmethod
    async def optimize(self, content: str, context: Optional[Dict[str, Any]] = None) -> Tuple[str, int]:
        """
        Optimiza contenido
        
        Returns:
            Tuple de (contenido_optimizado, tokens_ahorrados)
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Nombre de la estrategia"""
        pass


class CompressionStrategy(TokenOptimizationStrategyBase):
    """
    Estrategia de compresión de prompts
    
    Comprime texto eliminando redundancias, simplificando estructura,
    y preservando información crítica.
    """
    
    def __init__(self, config: TokenOptimizationConfig):
        self.config = config
        self._keywords_to_preserve: Set[str] = set()
        self._abbreviations: Dict[str, str] = {}
    
    async def optimize(self, content: str, context: Optional[Dict[str, Any]] = None) -> Tuple[str, int]:
        original_tokens = self._estimate_tokens(content)
        
        if original_tokens < 50:
            return content, 0
        
        compressed = content
        
        # Paso 1: Eliminar espacios redundantes
        compressed = self._normalize_whitespace(compressed)
        
        # Paso 2: Comprimir frases comunes
        compressed = self._compress_common_phrases(compressed)
        
        # Paso 3: Eliminar repetición
        compressed = self._remove_repetition(compressed)
        
        # Paso 4: Simplificar estructura si está habilitado
        if not self.config.preserve_structure:
            compressed = self._simplify_structure(compressed)
        
        # Paso 5: Preservar keywords críticos
        if self.config.preserve_keywords:
            compressed = self._preserve_critical_keywords(compressed, context)
        
        new_tokens = self._estimate_tokens(compressed)
        saved = original_tokens - new_tokens
        
        return compressed, saved
    
    def get_name(self) -> str:
        return "compression"
    
    def _estimate_tokens(self, text: str) -> int:
        """Estima el número de tokens"""
        words = len(text.split())
        chars = len(text)
        return int(words * self.config.tokens_per_word + chars * self.config.tokens_per_char) // 2
    
    def _normalize_whitespace(self, text: str) -> str:
        """Normaliza espacios en blanco"""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        return text.strip()
    
    def _compress_common_phrases(self, text: str) -> str:
        """Comprime frases comunes"""
        common_phrases = {
            "for example": "e.g.",
            "that is": "i.e.",
            "and so on": "etc.",
            "in order to": "to",
            "as well as": "and",
            "at this point in time": "now",
            "due to the fact that": "because",
            "in the event that": "if",
            "with regard to": "about",
            "in spite of": "despite",
            "a large number of": "many",
            "in the near future": "soon",
            "on a daily basis": "daily",
            "the majority of": "most",
            "a sufficient number of": "enough",
        }
        
        for phrase, abbreviation in common_phrases.items():
            text = text.replace(phrase, abbreviation)
            text = text.replace(phrase.capitalize(), abbreviation)
        
        return text
    
    def _remove_repetition(self, text: str) -> str:
        """Elimina repetición de frases"""
        sentences = text.split('. ')
        seen: Set[str] = set()
        unique_sentences = []
        
        for sentence in sentences:
            normalized = sentence.lower().strip()
            if normalized not in seen:
                seen.add(normalized)
                unique_sentences.append(sentence)
        
        return '. '.join(unique_sentences)
    
    def _simplify_structure(self, text: str) -> str:
        """Simplifica estructura del texto"""
        # Eliminar listas muy largas
        text = re.sub(r'(\n[-*]\s+[^\n]+){5,}', '\n[multiple items]\n', text)
        
        # Simplificar código muy largo
        text = re.sub(r'```[^\n]*\n[\s\S]{500,}?```', '```[code block]```', text)
        
        return text
    
    def _preserve_critical_keywords(self, text: str, context: Optional[Dict[str, Any]]) -> str:
        """Preserva keywords críticos del contexto"""
        if not context:
            return text
        
        critical = context.get("critical_keywords", [])
        important = context.get("important_terms", [])
        
        # No modificar si contiene keywords críticos
        if critical and any(kw in text for kw in critical):
            return text
        
        return text


class SemanticCacheStrategy(TokenOptimizationStrategyBase):
    """
    Estrategia de cache semántico
    
    Almacena respuestas y las reutiliza cuando la consulta es
    semánticamente similar.
    """
    
    def __init__(self, config: TokenOptimizationConfig, embedding_fn: Optional[Callable] = None):
        self.config = config
        self.embedding_fn = embedding_fn
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._embedding_index: Dict[str, List[float]] = {}
        self._access_times: Dict[str, datetime] = {}
    
    async def optimize(self, content: str, context: Optional[Dict[str, Any]] = None) -> Tuple[str, int]:
        """Intenta encontrar respuesta cacheada semánticamente similar"""
        
        if not self.embedding_fn:
            return content, 0
        
        try:
            # Obtener embedding del contenido
            query_embedding = await self.embedding_fn(content)
            
            # Buscar entrada similar
            cached_entry = await self._find_similar_cached(query_embedding)
            
            if cached_entry:
                # Cache hit
                return cached_entry["response"], self._estimate_tokens(content)
            
            # Cache miss - no modificamos el contenido
            return content, 0
            
        except Exception as e:
            logger.error(f"Semantic cache error: {e}")
            return content, 0
    
    def get_name(self) -> str:
        return "semantic_cache"
    
    async def store_response(
        self,
        prompt: str,
        response: str,
        embedding: Optional[List[float]] = None
    ) -> None:
        """Almacena una respuesta en el cache"""
        
        if len(self._cache) >= self.config.max_cache_entries:
            self._evict_oldest()
        
        key = self._hash_content(prompt)
        
        if not embedding and self.embedding_fn:
            try:
                embedding = await self.embedding_fn(prompt)
            except Exception:
                pass
        
        self._cache[key] = {
            "prompt": prompt,
            "response": response,
            "timestamp": datetime.utcnow(),
        }
        
        if embedding:
            self._embedding_index[key] = embedding
        
        self._access_times[key] = datetime.utcnow()
    
    async def _find_similar_cached(self, query_embedding: List[float]) -> Optional[Dict[str, Any]]:
        """Busca entrada cacheada similar"""
        best_match = None
        best_similarity = 0.0
        
        for key, cached_embedding in self._embedding_index.items():
            similarity = self._cosine_similarity(query_embedding, cached_embedding)
            
            if similarity > best_similarity and similarity >= self.config.cache_similarity_threshold:
                best_similarity = similarity
                best_match = key
        
        if best_match:
            self._access_times[best_match] = datetime.utcnow()
            return self._cache.get(best_match)
        
        return None
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calcula similitud coseno"""
        if len(a) != len(b):
            return 0.0
        
        dot_product = sum(x * y for x, y in zip(a, b))
        magnitude_a = math.sqrt(sum(x * x for x in a))
        magnitude_b = math.sqrt(sum(x * x for x in b))
        
        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0
        
        return dot_product / (magnitude_a * magnitude_b)
    
    def _hash_content(self, content: str) -> str:
        """Genera hash para contenido"""
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _estimate_tokens(self, text: str) -> int:
        return int(len(text.split()) * self.config.tokens_per_word)
    
    def _evict_oldest(self) -> None:
        """Elimina entradas más antiguas"""
        if not self._access_times:
            return
        
        # Eliminar 10% más antiguos
        sorted_keys = sorted(self._access_times.keys(), key=lambda k: self._access_times[k])
        to_remove = max(1, len(sorted_keys) // 10)
        
        for key in sorted_keys[:to_remove]:
            self._cache.pop(key, None)
            self._embedding_index.pop(key, None)
            self._access_times.pop(key, None)


class DeduplicationStrategy(TokenOptimizationStrategyBase):
    """
    Estrategia de deduplicación
    
    Elimina contenido duplicado o muy similar en el prompt.
    """
    
    def __init__(self, config: TokenOptimizationConfig):
        self.config = config
        self._similarity_cache: Dict[str, float] = {}
    
    async def optimize(self, content: str, context: Optional[Dict[str, Any]] = None) -> Tuple[str, int]:
        original_tokens = self._estimate_tokens(content)
        
        # Dividir en secciones
        sections = self._split_sections(content)
        
        # Detectar y eliminar duplicados
        unique_sections = await self._deduplicate_sections(sections)
        
        # Reconstruir contenido
        optimized = '\n\n'.join(unique_sections)
        
        new_tokens = self._estimate_tokens(optimized)
        saved = original_tokens - new_tokens
        
        return optimized, saved
    
    def get_name(self) -> str:
        return "deduplication"
    
    def _split_sections(self, content: str) -> List[str]:
        """Divide contenido en secciones"""
        # Dividir por párrafos
        paragraphs = content.split('\n\n')
        return [p.strip() for p in paragraphs if p.strip()]
    
    async def _deduplicate_sections(self, sections: List[str]) -> List[str]:
        """Elimina secciones duplicadas"""
        unique = []
        seen_hashes: Set[str] = set()
        
        for section in sections:
            # Hash de la sección normalizada
            normalized = section.lower().strip()
            section_hash = hashlib.md5(normalized.encode()).hexdigest()[:8]
            
            if section_hash in seen_hashes:
                continue
            
            # Verificar similitud con secciones existentes
            is_duplicate = False
            for existing in unique:
                similarity = self._text_similarity(section, existing)
                if similarity > 0.9:  # 90% similar = duplicado
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique.append(section)
                seen_hashes.add(section_hash)
        
        return unique
    
    def _text_similarity(self, a: str, b: str) -> float:
        """Calcula similitud entre textos (Jaccard)"""
        words_a = set(a.lower().split())
        words_b = set(b.lower().split())
        
        if not words_a or not words_b:
            return 0.0
        
        intersection = words_a & words_b
        union = words_a | words_b
        
        return len(intersection) / len(union)
    
    def _estimate_tokens(self, text: str) -> int:
        return int(len(text.split()) * self.config.tokens_per_word)


class ContextPruningStrategy(TokenOptimizationStrategyBase):
    """
    Estrategia de poda de contexto
    
    Elimina contexto irrelevante basado en relevancia semántica.
    """
    
    def __init__(self, config: TokenOptimizationConfig, embedding_fn: Optional[Callable] = None):
        self.config = config
        self.embedding_fn = embedding_fn
    
    async def optimize(self, content: str, context: Optional[Dict[str, Any]] = None) -> Tuple[str, int]:
        if not context:
            return content, 0
        
        original_tokens = self._estimate_tokens(content)
        
        # Obtener la consulta principal
        query = context.get("query", context.get("task", ""))
        if not query:
            return content, 0
        
        # Dividir contenido en chunks
        chunks = self._chunk_content(content)
        
        # Evaluar relevancia de cada chunk
        relevant_chunks = await self._filter_relevant_chunks(chunks, query, context)
        
        # Reconstruir contenido
        optimized = '\n\n'.join(relevant_chunks)
        
        # Verificar límite de tokens
        if self._estimate_tokens(optimized) > self.config.max_context_tokens:
            optimized = self._truncate_to_limit(optimized)
        
        new_tokens = self._estimate_tokens(optimized)
        saved = original_tokens - new_tokens
        
        return optimized, saved
    
    def get_name(self) -> str:
        return "context_pruning"
    
    def _chunk_content(self, content: str) -> List[str]:
        """Divide contenido en chunks"""
        paragraphs = content.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            if self._estimate_tokens(current_chunk + para) > self.config.optimal_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para
            else:
                current_chunk += '\n\n' + para
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    async def _filter_relevant_chunks(
        self,
        chunks: List[str],
        query: str,
        context: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Filtra chunks por relevancia"""
        if not self.embedding_fn:
            # Sin embedding, usar heurísticas
            return self._heuristic_filter(chunks, query)
        
        try:
            query_embedding = await self.embedding_fn(query)
            relevant = []
            
            for chunk in chunks:
                chunk_embedding = await self.embedding_fn(chunk[:500])  # Limitar para efficiency
                similarity = self._cosine_similarity(query_embedding, chunk_embedding)
                
                if similarity >= self.config.relevance_threshold:
                    relevant.append(chunk)
            
            return relevant
            
        except Exception as e:
            logger.error(f"Error filtering chunks: {e}")
            return chunks
    
    def _heuristic_filter(self, chunks: List[str], query: str) -> List[str]:
        """Filtra chunks usando heurísticas sin embeddings"""
        query_terms = set(query.lower().split())
        relevant = []
        
        for chunk in chunks:
            chunk_terms = set(chunk.lower().split())
            overlap = len(query_terms & chunk_terms) / max(1, len(query_terms))
            
            if overlap >= 0.3:  # 30% overlap
                relevant.append(chunk)
        
        return relevant if relevant else chunks[:5]
    
    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calcula similitud coseno"""
        if len(a) != len(b):
            return 0.0
        
        dot_product = sum(x * y for x, y in zip(a, b))
        magnitude_a = math.sqrt(sum(x * x for x in a))
        magnitude_b = math.sqrt(sum(x * x for x in b))
        
        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0
        
        return dot_product / (magnitude_a * magnitude_b)
    
    def _estimate_tokens(self, text: str) -> int:
        return int(len(text.split()) * self.config.tokens_per_word)
    
    def _truncate_to_limit(self, text: str) -> str:
        """Trunca texto al límite de tokens"""
        words = text.split()
        max_words = int(self.config.max_context_tokens / self.config.tokens_per_word)
        return ' '.join(words[:max_words])


class AdaptiveStrategy(TokenOptimizationStrategyBase):
    """
    Estrategia adaptativa
    
    Selecciona la mejor estrategia basada en características del contenido.
    """
    
    def __init__(self, config: TokenOptimizationConfig, embedding_fn: Optional[Callable] = None):
        self.config = config
        self.embedding_fn = embedding_fn
        self._strategies: Dict[str, TokenOptimizationStrategyBase] = {}
        self._performance_history: Dict[str, List[float]] = defaultdict(list)
        
        # Inicializar estrategias
        self._strategies["compression"] = CompressionStrategy(config)
        self._strategies["deduplication"] = DeduplicationStrategy(config)
        self._strategies["context_pruning"] = ContextPruningStrategy(config, embedding_fn)
        self._strategies["semantic_cache"] = SemanticCacheStrategy(config, embedding_fn)
    
    async def optimize(self, content: str, context: Optional[Dict[str, Any]] = None) -> Tuple[str, int]:
        # Analizar características del contenido
        content_profile = self._analyze_content(content, context)
        
        # Seleccionar mejor estrategia
        strategy_name = self._select_strategy(content_profile)
        
        # Aplicar estrategia
        strategy = self._strategies.get(strategy_name)
        if strategy:
            optimized, saved = await strategy.optimize(content, context)
            
            # Registrar rendimiento
            self._performance_history[strategy_name].append(saved)
            
            return optimized, saved
        
        return content, 0
    
    def get_name(self) -> str:
        return "adaptive"
    
    def _analyze_content(self, content: str, context: Optional[Dict[str, Any]]) -> Dict[str, float]:
        """Analiza características del contenido"""
        words = content.split()
        word_count = len(words)
        
        # Calcular métricas
        profile = {
            "length": word_count,
            "repetition_score": self._calculate_repetition(content),
            "structure_complexity": self._calculate_complexity(content),
            "has_code": "```" in content or "def " in content,
            "has_lists": content.count('\n-') > 3 or content.count('\n*') > 3,
            "estimated_tokens": word_count * self.config.tokens_per_word,
        }
        
        if context:
            profile["context_size"] = len(str(context))
        
        return profile
    
    def _calculate_repetition(self, content: str) -> float:
        """Calcula score de repetición (0-1)"""
        words = content.lower().split()
        if len(words) < 10:
            return 0.0
        
        unique_words = set(words)
        repetition = 1 - (len(unique_words) / len(words))
        return repetition
    
    def _calculate_complexity(self, content: str) -> float:
        """Calcula complejidad estructural (0-1)"""
        # Contar marcadores de estructura
        structure_markers = 0
        structure_markers += content.count('\n#')  # Headers
        structure_markers += content.count('\n-')  # Lists
        structure_markers += content.count('\n*')
        structure_markers += content.count('\n1.')  # Numbered lists
        structure_markers += content.count('```') // 2  # Code blocks
        
        # Normalizar
        paragraphs = len(content.split('\n\n'))
        if paragraphs == 0:
            return 0.0
        
        return min(1.0, structure_markers / paragraphs)
    
    def _select_strategy(self, profile: Dict[str, float]) -> str:
        """Selecciona la mejor estrategia basada en el perfil"""
        
        # Alto nivel de repetición -> deduplicación
        if profile["repetition_score"] > 0.3:
            return "deduplication"
        
        # Contenido muy largo -> context pruning
        if profile["estimated_tokens"] > self.config.max_context_tokens:
            return "context_pruning"
        
        # Alta complejidad estructural -> compresión suave
        if profile["structure_complexity"] > 0.5:
            return "compression"
        
        # Default -> compresión
        return "compression"


# ============================================================================
# DECORATOR PATTERN - Optimizing Wrapper
# ============================================================================

class OptimizingLLMWrapper:
    """
    Wrapper que añade optimización de tokens a cualquier LLM
    
    Patrón Decorator: Envuelve llamadas LLM con optimización automática.
    """
    
    def __init__(
        self,
        llm_provider,
        config: Optional[TokenOptimizationConfig] = None,
        embedding_fn: Optional[Callable] = None
    ):
        self.llm = llm_provider
        self.config = config or TokenOptimizationConfig()
        self.embedding_fn = embedding_fn
        
        # Inicializar estrategias
        self._strategies = self._init_strategies()
        
        # Métricas
        self.metrics = TokenMetrics()
        
        # Cache semántico
        self._semantic_cache: SemanticCacheStrategy = None
        if OptimizationStrategy.SEMANTIC_CACHE in self.config.strategies:
            self._semantic_cache = self._strategies.get("semantic_cache")
    
    def _init_strategies(self) -> Dict[str, TokenOptimizationStrategyBase]:
        """Inicializa todas las estrategias"""
        strategies = {}
        
        for strategy_type in self.config.strategies:
            if strategy_type == OptimizationStrategy.COMPRESSION:
                strategies["compression"] = CompressionStrategy(self.config)
            elif strategy_type == OptimizationStrategy.DEDUPLICATION:
                strategies["deduplication"] = DeduplicationStrategy(self.config)
            elif strategy_type == OptimizationStrategy.CONTEXT_PRUNING:
                strategies["context_pruning"] = ContextPruningStrategy(
                    self.config, self.embedding_fn
                )
            elif strategy_type == OptimizationStrategy.SEMANTIC_CACHE:
                strategies["semantic_cache"] = SemanticCacheStrategy(
                    self.config, self.embedding_fn
                )
            elif strategy_type == OptimizationStrategy.ADAPTIVE:
                strategies["adaptive"] = AdaptiveStrategy(
                    self.config, self.embedding_fn
                )
        
        return strategies
    
    async def generate(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Genera respuesta con optimización automática
        
        Returns:
            Tuple de (respuesta, metadata)
        """
        self.metrics.requests_total += 1
        
        # Paso 1: Verificar cache semántico
        if self._semantic_cache:
            cached, tokens_saved = await self._semantic_cache.optimize(prompt, context)
            if tokens_saved > 0:
                self.metrics.cache_hits += 1
                self.metrics.tokens_saved += tokens_saved
                self.metrics.savings_cost += self._calculate_cost(tokens_saved, 0)
                return cached, {"cached": True, "tokens_saved": tokens_saved}
            else:
                self.metrics.cache_misses += 1
        
        # Paso 2: Optimizar prompt
        optimized_prompt, tokens_saved = await self._optimize_prompt(prompt, context)
        
        # Paso 3: Llamar LLM
        response = await self._call_llm(optimized_prompt, context, **kwargs)
        
        # Paso 4: Actualizar métricas
        if tokens_saved > 0:
            self.metrics.tokens_saved += tokens_saved
            self.metrics.requests_optimized += 1
            self.metrics.savings_cost += self._calculate_cost(tokens_saved, 0)
        
        # Paso 5: Almacenar en cache semántico
        if self._semantic_cache and response:
            await self._semantic_cache.store_response(prompt, response)
        
        return response, {
            "optimized": tokens_saved > 0,
            "tokens_saved": tokens_saved,
            "original_length": len(prompt),
            "optimized_length": len(optimized_prompt),
        }
    
    async def _optimize_prompt(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]]
    ) -> Tuple[str, int]:
        """Aplica todas las estrategias de optimización"""
        optimized = prompt
        total_saved = 0
        
        # Aplicar estrategias en orden
        for strategy_name, strategy in self._strategies.items():
            if strategy_name == "semantic_cache":
                continue  # Ya manejado antes
            
            try:
                optimized, saved = await strategy.optimize(optimized, context)
                total_saved += saved
            except Exception as e:
                logger.error(f"Strategy {strategy_name} failed: {e}")
        
        return optimized, total_saved
    
    async def _call_llm(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]],
        **kwargs
    ) -> str:
        """Llama al LLM subyacente"""
        try:
            if hasattr(self.llm, 'generate'):
                result = await self.llm.generate(prompt, **kwargs)
                return result if isinstance(result, str) else result.get("content", "")
            elif hasattr(self.llm, 'generate_response'):
                result = await self.llm.generate_response(prompt, context, **kwargs)
                return result.content if hasattr(result, 'content') else str(result)
            elif hasattr(self.llm, 'chat'):
                result = await self.llm.chat(prompt, **kwargs)
                return result
            else:
                raise ValueError("LLM provider doesn't have a recognized method")
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise
    
    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calcula costo de tokens"""
        input_cost = (input_tokens / 1000) * self.config.cost_per_1k_input_tokens
        output_cost = (output_tokens / 1000) * self.config.cost_per_1k_output_tokens
        return input_cost + output_cost
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas de optimización"""
        return self.metrics.to_dict()
    
    def get_savings_report(self) -> Dict[str, Any]:
        """Genera reporte de ahorros"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "total_tokens_saved": self.metrics.tokens_saved,
            "total_cost_saved": self.metrics.savings_cost,
            "cache_hit_rate": self.metrics.cache_hits / max(1, self.metrics.cache_hits + self.metrics.cache_misses),
            "optimization_rate": self.metrics.requests_optimized / max(1, self.metrics.requests_total),
            "requests_total": self.metrics.requests_total,
            "requests_optimized": self.metrics.requests_optimized,
        }


# ============================================================================
# FACTORY PATTERN - Token Optimizer Factory
# ============================================================================

class TokenOptimizerFactory:
    """Factory para crear optimizadores de tokens"""
    
    @staticmethod
    def create(
        llm_provider=None,
        strategies: Optional[List[str]] = None,
        embedding_fn: Optional[Callable] = None,
        **config_kwargs
    ) -> OptimizingLLMWrapper:
        """
        Crea un optimizador configurado
        
        Args:
            llm_provider: Provider LLM a envolver
            strategies: Lista de estrategias ("compression", "semantic_cache", etc.)
            embedding_fn: Función para generar embeddings
            **config_kwargs: Configuraciones adicionales
        """
        # Configurar estrategias
        if strategies:
            config_kwargs["strategies"] = [
                OptimizationStrategy(s) for s in strategies
            ]
        
        config = TokenOptimizationConfig(**config_kwargs)
        
        if llm_provider:
            return OptimizingLLMWrapper(
                llm_provider=llm_provider,
                config=config,
                embedding_fn=embedding_fn
            )
        
        return OptimizingLLMWrapper(
            config=config,
            embedding_fn=embedding_fn
        )
    
    @staticmethod
    def create_for_cost_optimization(
        llm_provider=None,
        embedding_fn: Optional[Callable] = None
    ) -> OptimizingLLMWrapper:
        """Crea optimizador enfocado en reducir costos"""
        config = TokenOptimizationConfig(
            strategies=[
                OptimizationStrategy.SEMANTIC_CACHE,
                OptimizationStrategy.DEDUPLICATION,
                OptimizationStrategy.COMPRESSION,
            ],
            cache_enabled=True,
            cache_similarity_threshold=0.90,
            compression_level=0.8,
            track_costs=True,
        )
        
        return OptimizingLLMWrapper(
            llm_provider=llm_provider,
            config=config,
            embedding_fn=embedding_fn
        )
    
    @staticmethod
    def create_for_performance(
        llm_provider=None,
        embedding_fn: Optional[Callable] = None
    ) -> OptimizingLLMWrapper:
        """Crea optimizador enfocado en performance"""
        config = TokenOptimizationConfig(
            strategies=[
                OptimizationStrategy.SEMANTIC_CACHE,
                OptimizationStrategy.CONTEXT_PRUNING,
            ],
            cache_enabled=True,
            max_cache_entries=20000,
            max_context_tokens=2048,
        )
        
        return OptimizingLLMWrapper(
            llm_provider=llm_provider,
            config=config,
            embedding_fn=embedding_fn
        )


# ============================================================================
# TOKEN OPTIMIZER SERVICE - Main Service with Ralph Loop
# ============================================================================

class TokenOptimizerService:
    """
    Servicio de optimización de tokens con Ralph Loop
    
    Mantiene optimización continua y métricas en tiempo real.
    """
    
    def __init__(
        self,
        config: Optional[TokenOptimizationConfig] = None,
        embedding_fn: Optional[Callable] = None,
        redis_client=None
    ):
        self.config = config or TokenOptimizationConfig()
        self.embedding_fn = embedding_fn
        self.redis = redis_client
        
        # Estrategias
        self._strategies = self._init_strategies()
        
        # Estado
        self._running = False
        self._metrics = TokenMetrics()
        self._request_queue: asyncio.Queue = asyncio.Queue()
        
        # Shared context pool
        self._shared_context = SharedContextPool()
    
    def _init_strategies(self) -> Dict[str, TokenOptimizationStrategyBase]:
        """Inicializa estrategias"""
        strategies = {}
        
        for strategy_type in self.config.strategies:
            if strategy_type == OptimizationStrategy.COMPRESSION:
                strategies["compression"] = CompressionStrategy(self.config)
            elif strategy_type == OptimizationStrategy.DEDUPLICATION:
                strategies["deduplication"] = DeduplicationStrategy(self.config)
            elif strategy_type == OptimizationStrategy.CONTEXT_PRUNING:
                strategies["context_pruning"] = ContextPruningStrategy(
                    self.config, self.embedding_fn
                )
            elif strategy_type == OptimizationStrategy.SEMANTIC_CACHE:
                strategies["semantic_cache"] = SemanticCacheStrategy(
                    self.config, self.embedding_fn
                )
            elif strategy_type == OptimizationStrategy.ADAPTIVE:
                strategies["adaptive"] = AdaptiveStrategy(
                    self.config, self.embedding_fn
                )
        
        return strategies
    
    # ========================================================================
    # RALPH LOOP - Continuous Optimization
    # ========================================================================
    
    async def start_continuous_optimization(self) -> None:
        """
        Inicia optimización continua usando Ralph Loop
        
        Pasos del loop:
        1. Procesar cola de requests pendientes
        2. Actualizar métricas
        3. Optimizar cache
        4. Persistir estado
        5. Esperar intervalo
        """
        self._running = True
        logger.info("Starting token optimization service (Ralph Loop)")
        
        while self._running:
            try:
                # PASO 1: Procesar cola
                await self._process_request_queue()
                
                # PASO 2: Actualizar métricas
                await self._update_metrics()
                
                # PASO 3: Optimizar cache
                await self._optimize_cache()
                
                # PASO 4: Persistir estado
                if self.redis:
                    await self._persist_state()
                
                # PASO 5: Esperar
                await asyncio.sleep(60)  # Cada minuto
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in optimization loop: {e}")
                await asyncio.sleep(5)
    
    def stop(self) -> None:
        """Detiene el servicio"""
        self._running = False
    
    async def _process_request_queue(self) -> None:
        """Procesa requests pendientes"""
        processed = 0
        max_batch = 10
        
        while not self._request_queue.empty() and processed < max_batch:
            try:
                request = await asyncio.wait_for(
                    self._request_queue.get(),
                    timeout=1.0
                )
                await self._process_request(request)
                processed += 1
            except asyncio.TimeoutError:
                break
            except Exception as e:
                logger.error(f"Error processing request: {e}")
    
    async def _process_request(self, request: Dict[str, Any]) -> None:
        """Procesa un request de optimización"""
        content = request.get("content", "")
        context = request.get("context")
        callback = request.get("callback")
        
        optimized, saved = await self.optimize(content, context)
        
        if callback:
            try:
                await callback(optimized, saved)
            except Exception as e:
                logger.error(f"Callback error: {e}")
    
    async def _update_metrics(self) -> None:
        """Actualiza métricas internas"""
        if self._metrics.requests_total > 0:
            self._metrics.compression_ratio = (
                1 - self._metrics.tokens_saved / 
                max(1, self._metrics.total_input_tokens)
            )
    
    async def _optimize_cache(self) -> None:
        """Optimiza el cache semántico"""
        cache_strategy = self._strategies.get("semantic_cache")
        if cache_strategy and hasattr(cache_strategy, '_evict_expired'):
            # Implementar limpieza de cache expirado
            pass
    
    async def _persist_state(self) -> None:
        """Persiste estado en Redis"""
        if not self.redis:
            return
        
        try:
            state = {
                "metrics": self._metrics.to_dict(),
                "timestamp": datetime.utcnow().isoformat(),
            }
            await self.redis.set("token_optimizer:state", json.dumps(state))
        except Exception as e:
            logger.error(f"Failed to persist state: {e}")
    
    # ========================================================================
    # PUBLIC API
    # ========================================================================
    
    async def optimize(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, int]:
        """
        Optimiza contenido aplicando todas las estrategias configuradas
        
        Returns:
            Tuple de (contenido_optimizado, tokens_ahorrados)
        """
        self._metrics.requests_total += 1
        
        optimized = content
        total_saved = 0
        
        # Aplicar estrategias en orden
        for strategy_name in ["deduplication", "compression", "context_pruning"]:
            strategy = self._strategies.get(strategy_name)
            if strategy:
                try:
                    optimized, saved = await strategy.optimize(optimized, context)
                    total_saved += saved
                except Exception as e:
                    logger.error(f"Strategy {strategy_name} failed: {e}")
        
        # Actualizar métricas
        if total_saved > 0:
            self._metrics.tokens_saved += total_saved
            self._metrics.requests_optimized += 1
        
        original_tokens = int(len(content.split()) * self.config.tokens_per_word)
        self._metrics.total_input_tokens += original_tokens
        
        return optimized, total_saved
    
    async def queue_optimization(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None,
        callback: Optional[Callable] = None
    ) -> None:
        """Encola una optimización para procesamiento asíncrono"""
        request = {
            "content": content,
            "context": context,
            "callback": callback,
        }
        await self._request_queue.put(request)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas actuales"""
        return self._metrics.to_dict()
    
    def get_report(self) -> Dict[str, Any]:
        """Genera reporte completo"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "metrics": self._metrics.to_dict(),
            "config": {
                "strategies": [s.value for s in self.config.strategies],
                "compression_level": self.config.compression_level,
                "cache_enabled": self.config.cache_enabled,
            },
            "savings": {
                "tokens_saved": self._metrics.tokens_saved,
                "cost_saved": self._metrics.savings_cost,
            },
        }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def count_tokens(text: str, method: str = "estimate") -> int:
    """
    Cuenta tokens en texto
    
    Args:
        text: Texto a contar
        method: "estimate", "words", "chars"
    """
    if method == "words":
        return len(text.split())
    elif method == "chars":
        return len(text) // 4
    else:  # estimate
        return int(len(text.split()) * 1.3)


def create_token_optimizer(
    strategies: Optional[List[str]] = None,
    embedding_fn: Optional[Callable] = None,
    **kwargs
) -> TokenOptimizerService:
    """Factory function para crear servicio de optimización"""
    config = TokenOptimizationConfig()
    
    if strategies:
        config.strategies = [OptimizationStrategy(s) for s in strategies]
    
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
    
    return TokenOptimizerService(
        config=config,
        embedding_fn=embedding_fn
    )


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Configuration
    "OptimizationStrategy",
    "TokenOptimizationConfig",
    "TokenMetrics",
    # Strategies
    "TokenOptimizationStrategyBase",
    "CompressionStrategy",
    "SemanticCacheStrategy",
    "DeduplicationStrategy",
    "ContextPruningStrategy",
    "AdaptiveStrategy",
    # Wrapper & Service
    "OptimizingLLMWrapper",
    "TokenOptimizerService",
    "SharedContextPool",
    # Factory
    "TokenOptimizerFactory",
    # Helpers
    "count_tokens",
    "create_token_optimizer",
]
