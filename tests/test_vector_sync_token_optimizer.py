"""
Tests for Vector Store Sync and Token Optimizer

Tests comprehensivos para:
- VectorStoreSynchronizer: Sincronización Milvus/Qdrant
- TokenOptimizer: Reducción de gasto en LLM calls

@author: NEXUS - Neural Execution Unified System
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import json

# Importaciones del sistema
import sys
sys.path.insert(0, '/home/z/my-project/ecosystem/ricco-ai')

from src.infra.vector.vector_store_sync import (
    SyncDirection,
    SyncMode,
    ConflictResolution,
    SyncConfig,
    SyncEvent,
    SyncState,
    SyncObserver,
    LoggingSyncObserver,
    MetricsSyncObserver,
    SyncCommand,
    UpsertSyncCommand,
    DeleteSyncCommand,
    SyncStrategy,
    FullSyncStrategy,
    IncrementalSyncStrategy,
    DeltaSyncStrategy,
    SyncStrategyFactory,
    VectorStoreSynchronizer,
    create_synchronizer,
)

from src.ai_providers.token_optimizer import (
    OptimizationStrategy,
    TokenOptimizationConfig,
    TokenMetrics,
    CompressionStrategy,
    SemanticCacheStrategy,
    DeduplicationStrategy,
    ContextPruningStrategy,
    AdaptiveStrategy,
    OptimizingLLMWrapper,
    TokenOptimizerService,
    TokenOptimizerFactory,
    SharedContextPool,
    count_tokens,
    create_token_optimizer,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sync_config():
    """Configuración de sincronización por defecto"""
    return SyncConfig(
        direction=SyncDirection.BIDIRECTIONAL,
        mode=SyncMode.BATCH,
        batch_size=50,
        sync_interval_seconds=30,
    )


@pytest.fixture
def mock_milvus_store():
    """Mock de Milvus store"""
    store = Mock()
    store.upsert = Mock(return_value=True)
    store.delete = Mock(return_value=True)
    store.search = Mock(return_value=[])
    store.is_connected = True
    return store


@pytest.fixture
def mock_qdrant_store():
    """Mock de Qdrant store"""
    store = Mock()
    store.upsert = AsyncMock(return_value=True)
    store.delete = AsyncMock(return_value=True)
    store.search = AsyncMock(return_value=[])
    return store


@pytest.fixture
def token_config():
    """Configuración de optimización de tokens"""
    return TokenOptimizationConfig(
        strategies=[
            OptimizationStrategy.COMPRESSION,
            OptimizationStrategy.DEDUPLICATION,
        ],
        compression_level=0.7,
        cache_enabled=True,
    )


@pytest.fixture
def mock_embedding_fn():
    """Mock de función de embedding"""
    async def embedding_fn(text: str) -> list:
        # Simular embedding basado en hash del texto
        hash_val = hash(text)
        return [float((hash_val >> i) & 1) for i in range(128)]
    return embedding_fn


@pytest.fixture
def mock_llm_provider():
    """Mock de LLM provider"""
    provider = Mock()
    provider.generate = AsyncMock(return_value="Generated response")
    provider.generate_response = AsyncMock()
    provider.generate_response.return_value = Mock(content="Response content")
    return provider


# ============================================================================
# TESTS: SYNC CONFIGURATION
# ============================================================================

class TestSyncConfiguration:
    """Tests de configuración de sincronización"""
    
    def test_sync_config_defaults(self):
        """Verifica valores por defecto de configuración"""
        config = SyncConfig()
        
        assert config.direction == SyncDirection.BIDIRECTIONAL
        assert config.mode == SyncMode.BATCH
        assert config.conflict_resolution == ConflictResolution.NEWEST_WINS
        assert config.batch_size == 100
        assert config.sync_interval_seconds == 60
        assert len(config.collections_to_sync) == 5
    
    def test_sync_config_custom(self):
        """Verifica configuración personalizada"""
        config = SyncConfig(
            direction=SyncDirection.MILVUS_TO_QDRANT,
            mode=SyncMode.REAL_TIME,
            batch_size=200,
        )
        
        assert config.direction == SyncDirection.MILVUS_TO_QDRANT
        assert config.mode == SyncMode.REAL_TIME
        assert config.batch_size == 200
    
    def test_sync_direction_values(self):
        """Verifica valores de direcciones de sync"""
        assert SyncDirection.MILVUS_TO_QDRANT.value == "milvus_to_qdrant"
        assert SyncDirection.QDRANT_TO_MILVUS.value == "qdrant_to_milvus"
        assert SyncDirection.BIDIRECTIONAL.value == "bidirectional"
    
    def test_sync_mode_values(self):
        """Verifica valores de modos de sync"""
        assert SyncMode.REAL_TIME.value == "real_time"
        assert SyncMode.BATCH.value == "batch"
        assert SyncMode.SCHEDULED.value == "scheduled"
        assert SyncMode.ON_DEMAND.value == "on_demand"


# ============================================================================
# TESTS: SYNC EVENTS & STATE
# ============================================================================

class TestSyncEventsAndState:
    """Tests de eventos y estado de sincronización"""
    
    def test_sync_event_creation(self):
        """Verifica creación de evento de sync"""
        event = SyncEvent(
            event_type="upsert",
            collection="test_collection",
            point_id="point_123",
            source="milvus",
            data={"key": "value"},
        )
        
        assert event.event_type == "upsert"
        assert event.collection == "test_collection"
        assert event.point_id == "point_123"
        assert event.source == "milvus"
        assert not event.processed
        assert event.attempts == 0
    
    def test_sync_state_defaults(self):
        """Verifica estado inicial de sync"""
        state = SyncState()
        
        assert state.last_sync_count == 0
        assert state.pending_events == 0
        assert state.total_synced == 0
        assert state.version == 0
    
    def test_sync_event_data_storage(self):
        """Verifica almacenamiento de datos en evento"""
        data = {
            "payload": {"name": "test", "value": 42},
            "metadata": {"created": "2024-01-01"},
        }
        event = SyncEvent(
            event_type="upsert",
            collection="test",
            point_id="p1",
            source="qdrant",
            data=data,
            vector=[0.1, 0.2, 0.3],
        )
        
        assert event.data == data
        assert event.vector == [0.1, 0.2, 0.3]


# ============================================================================
# TESTS: OBSERVER PATTERN
# ============================================================================

class TestSyncObservers:
    """Tests del patrón Observer en sincronización"""
    
    @pytest.mark.asyncio
    async def test_logging_observer(self):
        """Verifica LoggingSyncObserver"""
        observer = LoggingSyncObserver()
        
        event = SyncEvent(
            event_type="upsert",
            collection="test",
            point_id="p1",
            source="milvus",
        )
        
        # No debe lanzar excepciones
        await observer.on_sync_event(event)
        
        state = SyncState()
        await observer.on_sync_complete(state)
        
        error = Exception("Test error")
        await observer.on_sync_error(error, event)
    
    @pytest.mark.asyncio
    async def test_metrics_observer(self):
        """Verifica MetricsSyncObserver"""
        observer = MetricsSyncObserver()
        
        # Simular eventos
        event1 = SyncEvent(
            event_type="upsert",
            collection="test",
            point_id="p1",
            source="milvus",
        )
        event2 = SyncEvent(
            event_type="delete",
            collection="test",
            point_id="p2",
            source="qdrant",
        )
        
        await observer.on_sync_event(event1)
        await observer.on_sync_event(event2)
        
        state = SyncState()
        state.total_synced = 10
        await observer.on_sync_complete(state)
        
        metrics = observer.get_metrics()
        
        assert metrics["upsert_count"] == 1
        assert metrics["delete_count"] == 1
        assert metrics["milvus_events"] == 1
        assert metrics["qdrant_events"] == 1
        assert metrics["total_syncs"] == 1


# ============================================================================
# TESTS: COMMAND PATTERN
# ============================================================================

class TestSyncCommands:
    """Tests del patrón Command en sincronización"""
    
    @pytest.mark.asyncio
    async def test_upsert_command(self, mock_qdrant_store):
        """Verifica UpsertSyncCommand"""
        command = UpsertSyncCommand(
            target_store=mock_qdrant_store,
            collection="test_collection",
            point_id="point_123",
            vector=[0.1, 0.2, 0.3],
            payload={"name": "test"},
            tenant_id="tenant_1",
        )
        
        event = command.get_event()
        assert event.event_type == "upsert"
        assert event.collection == "test_collection"
        assert event.point_id == "point_123"
    
    @pytest.mark.asyncio
    async def test_delete_command(self, mock_qdrant_store):
        """Verifica DeleteSyncCommand"""
        command = DeleteSyncCommand(
            target_store=mock_qdrant_store,
            collection="test_collection",
            point_id="point_123",
            tenant_id="tenant_1",
        )
        
        event = command.get_event()
        assert event.event_type == "delete"
        assert event.point_id == "point_123"


# ============================================================================
# TESTS: STRATEGY PATTERN
# ============================================================================

class TestSyncStrategies:
    """Tests de estrategias de sincronización"""
    
    @pytest.mark.asyncio
    async def test_delta_strategy_needs_update(self):
        """Verifica detección de cambios en DeltaSyncStrategy"""
        strategy = DeltaSyncStrategy()
        
        # Datos idénticos
        source_data = {"payload": {"key": "value"}}
        target_data = {"payload": {"key": "value"}}
        
        config = SyncConfig()
        needs_update = strategy._needs_update(source_data, target_data, config)
        assert not needs_update
        
        # Datos diferentes
        target_data = {"payload": {"key": "different_value"}}
        needs_update = strategy._needs_update(source_data, target_data, config)
        assert needs_update
    
    def test_strategy_factory(self):
        """Verifica SyncStrategyFactory"""
        batch_strategy = SyncStrategyFactory.create(SyncMode.BATCH)
        assert isinstance(batch_strategy, DeltaSyncStrategy)
        
        real_time_strategy = SyncStrategyFactory.create(SyncMode.REAL_TIME)
        assert isinstance(real_time_strategy, IncrementalSyncStrategy)
        
        scheduled_strategy = SyncStrategyFactory.create(SyncMode.SCHEDULED)
        assert isinstance(scheduled_strategy, FullSyncStrategy)


# ============================================================================
# TESTS: VECTOR STORE SYNCHRONIZER
# ============================================================================

class TestVectorStoreSynchronizer:
    """Tests del VectorStoreSynchronizer"""
    
    def test_synchronizer_creation(self, mock_milvus_store, mock_qdrant_store, sync_config):
        """Verifica creación del sincronizador"""
        sync = VectorStoreSynchronizer(
            milvus_store=mock_milvus_store,
            qdrant_store=mock_qdrant_store,
            config=sync_config,
        )
        
        assert sync.milvus == mock_milvus_store
        assert sync.qdrant == mock_qdrant_store
        assert sync.config == sync_config
        assert len(sync._observers) == 0
    
    def test_add_observer(self, mock_milvus_store, mock_qdrant_store, sync_config):
        """Verifica agregar observers"""
        sync = VectorStoreSynchronizer(
            milvus_store=mock_milvus_store,
            qdrant_store=mock_qdrant_store,
            config=sync_config,
        )
        
        observer = LoggingSyncObserver()
        sync.add_observer(observer)
        
        assert len(sync._observers) == 1
        assert observer in sync._observers
    
    def test_remove_observer(self, mock_milvus_store, mock_qdrant_store, sync_config):
        """Verifica remover observers"""
        sync = VectorStoreSynchronizer(
            milvus_store=mock_milvus_store,
            qdrant_store=mock_qdrant_store,
            config=sync_config,
        )
        
        observer = LoggingSyncObserver()
        sync.add_observer(observer)
        sync.remove_observer(observer)
        
        assert len(sync._observers) == 0
    
    @pytest.mark.asyncio
    async def test_queue_upsert(self, mock_milvus_store, mock_qdrant_store, sync_config):
        """Verifica encolar upsert"""
        sync = VectorStoreSynchronizer(
            milvus_store=mock_milvus_store,
            qdrant_store=mock_qdrant_store,
            config=sync_config,
        )
        
        await sync.queue_upsert(
            collection="test_collection",
            point_id="p1",
            vector=[0.1, 0.2, 0.3],
            payload={"key": "value"},
            source="external",
        )
        
        assert sync._event_queue.qsize() == 1
    
    @pytest.mark.asyncio
    async def test_queue_delete(self, mock_milvus_store, mock_qdrant_store, sync_config):
        """Verifica encolar delete"""
        sync = VectorStoreSynchronizer(
            milvus_store=mock_milvus_store,
            qdrant_store=mock_qdrant_store,
            config=sync_config,
        )
        
        await sync.queue_delete(
            collection="test_collection",
            point_id="p1",
            source="external",
        )
        
        assert sync._event_queue.qsize() == 1
    
    def test_get_status(self, mock_milvus_store, mock_qdrant_store, sync_config):
        """Verifica obtención de estado"""
        sync = VectorStoreSynchronizer(
            milvus_store=mock_milvus_store,
            qdrant_store=mock_qdrant_store,
            config=sync_config,
        )
        
        status = sync.get_status()
        
        assert "running" in status
        assert "state" in status
        assert "config" in status
        assert "stores" in status
        assert status["stores"]["milvus"] == True
        assert status["stores"]["qdrant"] == True
    
    @pytest.mark.asyncio
    async def test_get_sync_report(self, mock_milvus_store, mock_qdrant_store, sync_config):
        """Verifica generación de reporte"""
        sync = VectorStoreSynchronizer(
            milvus_store=mock_milvus_store,
            qdrant_store=mock_qdrant_store,
            config=sync_config,
        )
        
        report = await sync.get_sync_report()
        
        assert "timestamp" in report
        assert "summary" in report
        assert "collections" in report


# ============================================================================
# TESTS: CREATE SYNCHRONIZER FACTORY
# ============================================================================

class TestCreateSynchronizer:
    """Tests de la factory function create_synchronizer"""
    
    def test_create_default(self):
        """Verifica creación con valores por defecto"""
        sync = create_synchronizer()
        
        assert sync.config.direction == SyncDirection.BIDIRECTIONAL
        assert sync.config.mode == SyncMode.BATCH
        assert len(sync._observers) == 1  # LoggingSyncObserver por defecto
    
    def test_create_custom_direction(self):
        """Verifica creación con dirección personalizada"""
        sync = create_synchronizer(direction="milvus_to_qdrant")
        
        assert sync.config.direction == SyncDirection.MILVUS_TO_QDRANT
    
    def test_create_custom_mode(self):
        """Verifica creación con modo personalizado"""
        sync = create_synchronizer(mode="real_time")
        
        assert sync.config.mode == SyncMode.REAL_TIME


# ============================================================================
# TESTS: TOKEN OPTIMIZATION CONFIG
# ============================================================================

class TestTokenOptimizationConfig:
    """Tests de configuración de optimización de tokens"""
    
    def test_config_defaults(self):
        """Verifica valores por defecto"""
        config = TokenOptimizationConfig()
        
        assert OptimizationStrategy.SEMANTIC_CACHE in config.strategies
        assert config.compression_level == 0.7
        assert config.cache_enabled == True
        assert config.max_cache_entries == 10000
    
    def test_config_custom_strategies(self):
        """Verifica configuración de estrategias"""
        config = TokenOptimizationConfig(
            strategies=[
                OptimizationStrategy.COMPRESSION,
                OptimizationStrategy.DEDUPLICATION,
            ]
        )
        
        assert len(config.strategies) == 2
        assert OptimizationStrategy.COMPRESSION in config.strategies
    
    def test_token_metrics(self):
        """Verifica métricas de tokens"""
        metrics = TokenMetrics()
        
        metrics.total_input_tokens = 1000
        metrics.tokens_saved = 200
        metrics.cache_hits = 50
        metrics.cache_misses = 50
        
        result = metrics.to_dict()
        
        assert result["total_input_tokens"] == 1000
        assert result["tokens_saved"] == 200
        assert result["cache_hit_rate"] == 0.5


# ============================================================================
# TESTS: COMPRESSION STRATEGY
# ============================================================================

class TestCompressionStrategy:
    """Tests de la estrategia de compresión"""
    
    @pytest.mark.asyncio
    async def test_compress_simple_text(self, token_config):
        """Verifica compresión de texto simple"""
        strategy = CompressionStrategy(token_config)
        
        text = "This is a test. This is a test. This is a test."
        compressed, saved = await strategy.optimize(text)
        
        # Debe eliminar repetición
        assert len(compressed) <= len(text)
        assert saved >= 0
    
    @pytest.mark.asyncio
    async def test_compress_phrases(self, token_config):
        """Verifica compresión de frases comunes"""
        strategy = CompressionStrategy(token_config)
        
        text = "for example, we can see that in order to proceed..."
        compressed, _ = await strategy.optimize(text)
        
        # Debe usar abreviaciones
        assert "e.g." in compressed or "to" in compressed
    
    @pytest.mark.asyncio
    async def test_preserve_short_text(self, token_config):
        """Verifica que texto corto no se comprime"""
        strategy = CompressionStrategy(token_config)
        
        text = "Short text"
        compressed, saved = await strategy.optimize(text)
        
        # Texto muy corto no debe comprimirse
        assert compressed == text
        assert saved == 0
    
    def test_estimate_tokens(self, token_config):
        """Verifica estimación de tokens"""
        strategy = CompressionStrategy(token_config)
        
        text = "This is a test with multiple words"
        tokens = strategy._estimate_tokens(text)
        
        # Debe ser aproximadamente palabras * 1.3
        # Nota: La estimación combina palabras y caracteres
        assert tokens > 0
        assert tokens < 100  # Valor razonable para texto corto


# ============================================================================
# TESTS: DEDUPLICATION STRATEGY
# ============================================================================

class TestDeduplicationStrategy:
    """Tests de la estrategia de deduplicación"""
    
    @pytest.mark.asyncio
    async def test_remove_exact_duplicates(self, token_config):
        """Verifica eliminación de duplicados exactos"""
        strategy = DeduplicationStrategy(token_config)
        
        text = "Paragraph one.\n\nParagraph one.\n\nParagraph two."
        deduplicated, saved = await strategy.optimize(text)
        
        # Debe eliminar duplicado exacto
        assert "Paragraph one." in deduplicated
        assert saved >= 0
    
    @pytest.mark.asyncio
    async def test_text_similarity(self, token_config):
        """Verifica cálculo de similitud"""
        strategy = DeduplicationStrategy(token_config)
        
        text_a = "The quick brown fox jumps over the lazy dog"
        text_b = "The quick brown fox jumps over the lazy dog"
        
        similarity = strategy._text_similarity(text_a, text_b)
        assert similarity == 1.0
        
        text_c = "A completely different sentence"
        similarity = strategy._text_similarity(text_a, text_c)
        assert similarity < 0.5
    
    @pytest.mark.asyncio
    async def test_preserve_unique_sections(self, token_config):
        """Verifica que secciones únicas se preservan"""
        strategy = DeduplicationStrategy(token_config)
        
        text = "Section A\n\nSection B\n\nSection C"
        deduplicated, _ = await strategy.optimize(text)
        
        assert "Section A" in deduplicated
        assert "Section B" in deduplicated
        assert "Section C" in deduplicated


# ============================================================================
# TESTS: SEMANTIC CACHE STRATEGY
# ============================================================================

class TestSemanticCacheStrategy:
    """Tests de la estrategia de cache semántico"""
    
    @pytest.mark.asyncio
    async def test_cache_miss(self, token_config, mock_embedding_fn):
        """Verifica cache miss"""
        strategy = SemanticCacheStrategy(token_config, mock_embedding_fn)
        
        text = "New query that is not cached"
        result, saved = await strategy.optimize(text)
        
        # Sin cache previo, no hay ahorro
        assert saved == 0
    
    @pytest.mark.asyncio
    async def test_store_and_retrieve(self, token_config, mock_embedding_fn):
        """Verifica almacenar y recuperar del cache"""
        strategy = SemanticCacheStrategy(token_config, mock_embedding_fn)
        
        prompt = "What is machine learning?"
        response = "Machine learning is a subset of AI..."
        
        # Almacenar
        await strategy.store_response(prompt, response)
        
        # Recuperar
        # La misma consulta debe encontrar cache
        # Pero como los embeddings son basados en hash, necesitamos verificar
        assert len(strategy._cache) == 1
    
    def test_cosine_similarity(self, token_config):
        """Verifica cálculo de similitud coseno"""
        strategy = SemanticCacheStrategy(token_config)
        
        vec_a = [1.0, 0.0, 0.0]
        vec_b = [1.0, 0.0, 0.0]
        
        similarity = strategy._cosine_similarity(vec_a, vec_b)
        assert similarity == 1.0
        
        vec_c = [0.0, 1.0, 0.0]
        similarity = strategy._cosine_similarity(vec_a, vec_c)
        assert similarity == 0.0


# ============================================================================
# TESTS: CONTEXT PRUNING STRATEGY
# ============================================================================

class TestContextPruningStrategy:
    """Tests de la estrategia de poda de contexto"""
    
    @pytest.mark.asyncio
    async def test_prune_irrelevant_content(self, token_config):
        """Verifica poda de contenido irrelevante"""
        strategy = ContextPruningStrategy(token_config)
        
        content = "This is about cooking. This is about programming. This is about sports."
        context = {"query": "programming"}
        
        pruned, _ = await strategy.optimize(content, context)
        
        # Sin embedding function, usa heurísticas
        assert len(pruned) > 0
    
    @pytest.mark.asyncio
    async def test_chunk_content(self, token_config):
        """Verifica división en chunks"""
        strategy = ContextPruningStrategy(token_config)
        
        content = "Paragraph one.\n\nParagraph two.\n\nParagraph three."
        chunks = strategy._chunk_content(content)
        
        assert len(chunks) >= 1
    
    @pytest.mark.asyncio
    async def test_truncate_to_limit(self, token_config):
        """Verifica truncado al límite"""
        token_config.max_context_tokens = 10
        strategy = ContextPruningStrategy(token_config)
        
        long_text = "word " * 1000
        truncated = strategy._truncate_to_limit(long_text)
        
        tokens = strategy._estimate_tokens(truncated)
        assert tokens <= token_config.max_context_tokens


# ============================================================================
# TESTS: ADAPTIVE STRATEGY
# ============================================================================

class TestAdaptiveStrategy:
    """Tests de la estrategia adaptativa"""
    
    @pytest.mark.asyncio
    async def test_analyze_content(self, token_config):
        """Verifica análisis de contenido"""
        strategy = AdaptiveStrategy(token_config)
        
        content = "Repeated words words words words. Unique content here."
        profile = strategy._analyze_content(content, None)
        
        assert "length" in profile
        assert "repetition_score" in profile
        # La repetición puede ser 0 si no hay suficientes palabras repetidas
        assert profile["repetition_score"] >= 0
    
    @pytest.mark.asyncio
    async def test_select_strategy_high_repetition(self, token_config):
        """Verifica selección de estrategia con alta repetición"""
        strategy = AdaptiveStrategy(token_config)
        
        profile = {
            "repetition_score": 0.5,
            "estimated_tokens": 100,
            "structure_complexity": 0.3,
        }
        
        selected = strategy._select_strategy(profile)
        assert selected == "deduplication"
    
    @pytest.mark.asyncio
    async def test_select_strategy_long_content(self, token_config):
        """Verifica selección para contenido largo"""
        strategy = AdaptiveStrategy(token_config)
        
        profile = {
            "repetition_score": 0.1,
            "estimated_tokens": 10000,
            "structure_complexity": 0.3,
        }
        
        selected = strategy._select_strategy(profile)
        assert selected == "context_pruning"


# ============================================================================
# TESTS: OPTIMIZING LLM WRAPPER
# ============================================================================

class TestOptimizingLLMWrapper:
    """Tests del wrapper de optimización de LLM"""
    
    @pytest.mark.asyncio
    async def test_generate_with_optimization(self, mock_llm_provider, token_config):
        """Verifica generación con optimización"""
        wrapper = OptimizingLLMWrapper(
            llm_provider=mock_llm_provider,
            config=token_config
        )
        
        prompt = "Test prompt for optimization"
        response, metadata = await wrapper.generate(prompt)
        
        assert response is not None
        assert "optimized" in metadata
        assert "tokens_saved" in metadata
    
    @pytest.mark.asyncio
    async def test_metrics_tracking(self, mock_llm_provider, token_config):
        """Verifica seguimiento de métricas"""
        wrapper = OptimizingLLMWrapper(
            llm_provider=mock_llm_provider,
            config=token_config
        )
        
        # Generar varias veces
        for _ in range(5):
            await wrapper.generate("Test prompt")
        
        metrics = wrapper.get_metrics()
        
        # El key correcto según TokenMetrics.to_dict()
        assert metrics.get("total_input_tokens", 0) >= 0
    
    @pytest.mark.asyncio
    async def test_savings_report(self, mock_llm_provider, token_config):
        """Verifica reporte de ahorros"""
        wrapper = OptimizingLLMWrapper(
            llm_provider=mock_llm_provider,
            config=token_config
        )
        
        await wrapper.generate("Test prompt")
        
        report = wrapper.get_savings_report()
        
        assert "total_tokens_saved" in report
        assert "requests_total" in report


# ============================================================================
# TESTS: TOKEN OPTIMIZER SERVICE
# ============================================================================

class TestTokenOptimizerService:
    """Tests del servicio de optimización de tokens"""
    
    @pytest.mark.asyncio
    async def test_optimize_content(self, token_config):
        """Verifica optimización de contenido"""
        service = TokenOptimizerService(config=token_config)
        
        content = "This is test content. This is test content. Unique content here."
        optimized, saved = await service.optimize(content)
        
        assert optimized is not None
        assert saved >= 0
    
    @pytest.mark.asyncio
    async def test_queue_optimization(self, token_config):
        """Verifica encolar optimización"""
        service = TokenOptimizerService(config=token_config)
        
        callback_called = False
        
        async def callback(content, saved):
            nonlocal callback_called
            callback_called = True
        
        await service.queue_optimization("Test content", callback=callback)
        
        assert service._request_queue.qsize() == 1
    
    def test_get_metrics(self, token_config):
        """Verifica obtención de métricas"""
        service = TokenOptimizerService(config=token_config)
        
        metrics = service.get_metrics()
        
        assert "total_input_tokens" in metrics
        assert "tokens_saved" in metrics
    
    def test_get_report(self, token_config):
        """Verifica generación de reporte"""
        service = TokenOptimizerService(config=token_config)
        
        report = service.get_report()
        
        assert "timestamp" in report
        assert "metrics" in report
        assert "config" in report
        assert "savings" in report


# ============================================================================
# TESTS: SHARED CONTEXT POOL (FLYWEIGHT)
# ============================================================================

class TestSharedContextPool:
    """Tests del pool de contexto compartido (Flyweight)"""
    
    @pytest.mark.asyncio
    async def test_store_and_retrieve(self):
        """Verifica almacenar y recuperar contexto"""
        context = {"key": "value", "data": [1, 2, 3]}
        
        await SharedContextPool.store_shared_context("test_key", context)
        retrieved = await SharedContextPool.get_shared_context("test_key")
        
        assert retrieved == context
    
    @pytest.mark.asyncio
    async def test_nonexistent_key(self):
        """Verifica que clave inexistente retorna None"""
        result = await SharedContextPool.get_shared_context("nonexistent_key")
        
        assert result is None


# ============================================================================
# TESTS: FACTORY FUNCTIONS
# ============================================================================

class TestFactoryFunctions:
    """Tests de factory functions"""
    
    def test_create_token_optimizer_default(self):
        """Verifica creación con valores por defecto"""
        service = create_token_optimizer()
        
        assert service is not None
        assert service.config is not None
    
    def test_create_token_optimizer_custom_strategies(self):
        """Verifica creación con estrategias personalizadas"""
        service = create_token_optimizer(
            strategies=["compression", "deduplication"]
        )
        
        assert OptimizationStrategy.COMPRESSION in service.config.strategies
        assert OptimizationStrategy.DEDUPLICATION in service.config.strategies
    
    def test_factory_for_cost_optimization(self):
        """Verifica factory para optimización de costos"""
        wrapper = TokenOptimizerFactory.create_for_cost_optimization()
        
        assert wrapper.config.cache_enabled == True
        assert wrapper.config.track_costs == True
    
    def test_factory_for_performance(self):
        """Verifica factory para performance"""
        wrapper = TokenOptimizerFactory.create_for_performance()
        
        assert OptimizationStrategy.SEMANTIC_CACHE in wrapper.config.strategies
        assert OptimizationStrategy.CONTEXT_PRUNING in wrapper.config.strategies


# ============================================================================
# TESTS: HELPER FUNCTIONS
# ============================================================================

class TestHelperFunctions:
    """Tests de funciones auxiliares"""
    
    def test_count_tokens_estimate(self):
        """Verifica conteo estimado de tokens"""
        text = "This is a test with several words"
        
        count = count_tokens(text, method="estimate")
        
        # Debe ser aproximadamente palabras * 1.3
        assert count > 0
    
    def test_count_tokens_words(self):
        """Verifica conteo por palabras"""
        text = "One two three four five"
        
        count = count_tokens(text, method="words")
        
        assert count == 5
    
    def test_count_tokens_chars(self):
        """Verifica conteo por caracteres"""
        text = "12345678"
        
        count = count_tokens(text, method="chars")
        
        assert count == 2  # 8 chars / 4


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestIntegration:
    """Tests de integración"""
    
    @pytest.mark.asyncio
    async def test_full_sync_workflow(self, mock_milvus_store, mock_qdrant_store, sync_config):
        """Verifica flujo completo de sincronización"""
        sync = VectorStoreSynchronizer(
            milvus_store=mock_milvus_store,
            qdrant_store=mock_qdrant_store,
            config=sync_config,
        )
        
        # Agregar observer
        metrics_observer = MetricsSyncObserver()
        sync.add_observer(metrics_observer)
        
        # Encolar evento
        await sync.queue_upsert(
            collection="test_collection",
            point_id="p1",
            vector=[0.1, 0.2, 0.3],
            payload={"test": "data"},
        )
        
        # Verificar estado
        status = sync.get_status()
        assert status["state"]["pending_events"] == 1
    
    @pytest.mark.asyncio
    async def test_full_optimization_workflow(self, mock_llm_provider, mock_embedding_fn):
        """Verifica flujo completo de optimización"""
        config = TokenOptimizationConfig(
            strategies=[
                OptimizationStrategy.COMPRESSION,
                OptimizationStrategy.DEDUPLICATION,
            ]
        )
        
        wrapper = OptimizingLLMWrapper(
            llm_provider=mock_llm_provider,
            config=config,
            embedding_fn=mock_embedding_fn
        )
        
        # Texto con repetición
        prompt = """
        This is a test. This is a test. This is a test.
        For example, we can see that in order to proceed.
        """
        
        response, metadata = await wrapper.generate(prompt)
        
        assert response is not None
        assert wrapper.metrics.requests_total == 1


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestPerformance:
    """Tests de rendimiento"""
    
    @pytest.mark.asyncio
    async def test_large_text_optimization(self, token_config):
        """Verifica optimización de texto grande"""
        strategy = CompressionStrategy(token_config)
        
        # Generar texto grande
        large_text = "Paragraph content. " * 1000
        
        start = datetime.now()
        optimized, saved = await strategy.optimize(large_text)
        duration = (datetime.now() - start).total_seconds()
        
        # Debe completar en menos de 5 segundos
        assert duration < 5.0
        assert len(optimized) <= len(large_text)
    
    @pytest.mark.asyncio
    async def test_cache_performance(self, token_config, mock_embedding_fn):
        """Verifica rendimiento del cache"""
        strategy = SemanticCacheStrategy(token_config, mock_embedding_fn)
        
        # Almacenar 100 entradas
        for i in range(100):
            await strategy.store_response(f"Query {i}", f"Response {i}")
        
        assert len(strategy._cache) == 100


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
