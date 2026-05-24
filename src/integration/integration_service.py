"""
Integration Service - Vector Sync & Token Optimizer with Redis Queue

Integra VectorStoreSynchronizer y TokenOptimizer con el sistema de colas Redis
para procesamiento asíncrono y optimización continua.

@author: NEXUS - Neural Execution Unified System
"""

from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import json
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# INTEGRATION CONFIGURATION
# ============================================================================

@dataclass
class IntegrationConfig:
    """Configuración de integración"""
    # Redis settings
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    
    # Sync settings
    enable_vector_sync: bool = True
    sync_interval_seconds: int = 60
    
    # Token optimizer settings
    enable_token_optimization: bool = True
    optimization_strategies: List[str] = field(default_factory=lambda: [
        "compression", "deduplication", "semantic_cache"
    ])
    
    # Queue settings
    sync_queue_name: str = "nexus:vector_sync"
    optimization_queue_name: str = "nexus:token_optimization"
    result_queue_name: str = "nexus:results"


# ============================================================================
# VECTOR SYNC INTEGRATION
# ============================================================================

class VectorSyncIntegration:
    """
    Integración del VectorStoreSynchronizer con Redis Streams
    
    Procesa eventos de sincronización desde la cola Redis y los
    distribuye a los stores apropiados.
    """
    
    def __init__(
        self,
        redis_client,
        milvus_store=None,
        qdrant_store=None,
        config: Optional[IntegrationConfig] = None
    ):
        self.redis = redis_client
        self.milvus = milvus_store
        self.qdrant = qdrant_store
        self.config = config or IntegrationConfig()
        
        # Importar y crear sincronizador
        from src.infra.vector.vector_store_sync import (
            VectorStoreSynchronizer,
            SyncConfig,
            SyncMode,
            SyncDirection,
            MetricsSyncObserver,
        )
        
        sync_config = SyncConfig(
            mode=SyncMode.BATCH,
            direction=SyncDirection.BIDIRECTIONAL,
            sync_interval_seconds=self.config.sync_interval_seconds,
        )
        
        self.synchronizer = VectorStoreSynchronizer(
            milvus_store=milvus_store,
            qdrant_store=qdrant_store,
            config=sync_config,
            redis_client=redis_client,
        )
        
        # Agregar observer de métricas
        self._metrics_observer = MetricsSyncObserver()
        self.synchronizer.add_observer(self._metrics_observer)
        
        # Estado
        self._running = False
        self._worker_task = None
    
    async def start(self) -> None:
        """Inicia el worker de sincronización"""
        if self._running:
            return
        
        self._running = True
        self._worker_task = asyncio.create_task(self._run_worker())
        logger.info("VectorSyncIntegration started")
    
    async def stop(self) -> None:
        """Detiene el worker"""
        self._running = False
        self.synchronizer.stop_continuous_sync()
        
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        
        logger.info("VectorSyncIntegration stopped")
    
    async def _run_worker(self) -> None:
        """Worker principal que procesa la cola"""
        while self._running:
            try:
                # Leer de Redis Stream
                events = await self._read_sync_events()
                
                for event in events:
                    await self._process_sync_event(event)
                
                # Sincronización periódica
                await self.synchronizer.sync_all()
                
                # Esperar intervalo
                await asyncio.sleep(self.config.sync_interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in sync worker: {e}")
                await asyncio.sleep(5)
    
    async def _read_sync_events(self) -> List[Dict[str, Any]]:
        """Lee eventos de sincronización desde Redis"""
        events = []
        
        try:
            # Usar XREAD para leer de Redis Streams
            result = await self.redis.xread(
                {self.config.sync_queue_name: "0"},
                count=10,
                block=1000
            )
            
            if result:
                for stream_name, messages in result:
                    for message_id, data in messages:
                        events.append({
                            "id": message_id,
                            **data
                        })
                        # Acknowledge message
                        await self.redis.xack(
                            self.config.sync_queue_name,
                            "sync_consumer",
                            message_id
                        )
        
        except Exception as e:
            logger.error(f"Error reading sync events: {e}")
        
        return events
    
    async def _process_sync_event(self, event: Dict[str, Any]) -> None:
        """Procesa un evento de sincronización"""
        event_type = event.get("type", "upsert")
        collection = event.get("collection", "")
        point_id = event.get("point_id", "")
        
        if event_type == "upsert":
            await self.synchronizer.queue_upsert(
                collection=collection,
                point_id=point_id,
                vector=event.get("vector", []),
                payload=event.get("payload", {}),
                source=event.get("source", "redis_queue"),
            )
        elif event_type == "delete":
            await self.synchronizer.queue_delete(
                collection=collection,
                point_id=point_id,
                source=event.get("source", "redis_queue"),
            )
    
    async def publish_sync_event(self, event: Dict[str, Any]) -> None:
        """Publica un evento de sincronización en Redis"""
        try:
            await self.redis.xadd(
                self.config.sync_queue_name,
                event,
                maxlen=10000
            )
        except Exception as e:
            logger.error(f"Error publishing sync event: {e}")
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas de sincronización"""
        return self._metrics_observer.get_metrics()
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene estado de la integración"""
        return {
            "running": self._running,
            "synchronizer_status": self.synchronizer.get_status(),
            "metrics": self.get_metrics(),
        }


# ============================================================================
# TOKEN OPTIMIZER INTEGRATION
# ============================================================================

class TokenOptimizerIntegration:
    """
    Integración del TokenOptimizer con Redis
    
    Procesa requests de optimización desde la cola y aplica
    las estrategias configuradas.
    """
    
    def __init__(
        self,
        redis_client,
        embedding_fn: Optional[Callable] = None,
        config: Optional[IntegrationConfig] = None
    ):
        self.redis = redis_client
        self.embedding_fn = embedding_fn
        self.config = config or IntegrationConfig()
        
        # Importar y crear servicio
        from src.ai_providers.token_optimizer import (
            TokenOptimizerService,
            TokenOptimizationConfig,
            OptimizationStrategy,
        )
        
        strategies = [
            OptimizationStrategy(s) 
            for s in self.config.optimization_strategies
        ]
        
        opt_config = TokenOptimizationConfig(
            strategies=strategies,
            cache_enabled=True,
            track_costs=True,
        )
        
        self.optimizer = TokenOptimizerService(
            config=opt_config,
            embedding_fn=embedding_fn,
            redis_client=redis_client,
        )
        
        # Estado
        self._running = False
        self._worker_task = None
        self._metrics_key = "nexus:token_metrics"
    
    async def start(self) -> None:
        """Inicia el worker de optimización"""
        if self._running:
            return
        
        self._running = True
        self._worker_task = asyncio.create_task(self._run_worker())
        logger.info("TokenOptimizerIntegration started")
    
    async def stop(self) -> None:
        """Detiene el worker"""
        self._running = False
        self.optimizer.stop()
        
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        
        logger.info("TokenOptimizerIntegration stopped")
    
    async def _run_worker(self) -> None:
        """Worker principal"""
        while self._running:
            try:
                # Procesar cola de optimización
                requests = await self._read_optimization_requests()
                
                for request in requests:
                    await self._process_optimization_request(request)
                
                # Actualizar métricas en Redis
                await self._update_metrics()
                
                # Esperar intervalo
                await asyncio.sleep(10)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in optimization worker: {e}")
                await asyncio.sleep(5)
    
    async def _read_optimization_requests(self) -> List[Dict[str, Any]]:
        """Lee requests de optimización desde Redis"""
        requests = []
        
        try:
            # Usar lista Redis para requests
            while True:
                result = await self.redis.lpop(self.config.optimization_queue_name)
                if not result:
                    break
                requests.append(json.loads(result))
        
        except Exception as e:
            logger.error(f"Error reading optimization requests: {e}")
        
        return requests
    
    async def _process_optimization_request(self, request: Dict[str, Any]) -> None:
        """Procesa un request de optimización"""
        content = request.get("content", "")
        context = request.get("context")
        callback_key = request.get("callback_key")
        
        # Optimizar
        optimized, saved = await self.optimizer.optimize(content, context)
        
        # Publicar resultado
        if callback_key:
            result = {
                "optimized_content": optimized,
                "tokens_saved": saved,
                "timestamp": datetime.utcnow().isoformat(),
            }
            await self.redis.set(callback_key, json.dumps(result), ex=3600)
    
    async def _update_metrics(self) -> None:
        """Actualiza métricas en Redis"""
        metrics = self.optimizer.get_metrics()
        await self.redis.set(self._metrics_key, json.dumps(metrics))
    
    async def request_optimization(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None,
        callback_key: Optional[str] = None
    ) -> str:
        """
        Solicita optimización de contenido
        
        Returns:
            Key para obtener el resultado
        """
        request = {
            "content": content,
            "context": context,
            "callback_key": callback_key,
        }
        
        await self.redis.rpush(
            self.config.optimization_queue_name,
            json.dumps(request)
        )
        
        return callback_key or ""
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas de optimización"""
        return self.optimizer.get_metrics()
    
    def get_report(self) -> Dict[str, Any]:
        """Obtiene reporte de optimización"""
        return self.optimizer.get_report()


# ============================================================================
# UNIFIED INTEGRATION SERVICE
# ============================================================================

class UnifiedIntegrationService:
    """
    Servicio unificado que integra Vector Sync y Token Optimizer
    
    Coordina ambos servicios y proporciona una interfaz unificada.
    """
    
    def __init__(
        self,
        redis_client,
        milvus_store=None,
        qdrant_store=None,
        embedding_fn: Optional[Callable] = None,
        config: Optional[IntegrationConfig] = None
    ):
        self.config = config or IntegrationConfig()
        
        # Crear integraciones
        self.vector_sync = VectorSyncIntegration(
            redis_client=redis_client,
            milvus_store=milvus_store,
            qdrant_store=qdrant_store,
            config=self.config,
        ) if self.config.enable_vector_sync else None
        
        self.token_optimizer = TokenOptimizerIntegration(
            redis_client=redis_client,
            embedding_fn=embedding_fn,
            config=self.config,
        ) if self.config.enable_token_optimization else None
        
        self.redis = redis_client
        self._running = False
    
    async def start(self) -> None:
        """Inicia todos los servicios"""
        if self._running:
            return
        
        self._running = True
        
        if self.vector_sync:
            await self.vector_sync.start()
        
        if self.token_optimizer:
            await self.token_optimizer.start()
        
        logger.info("UnifiedIntegrationService started")
    
    async def stop(self) -> None:
        """Detiene todos los servicios"""
        self._running = False
        
        if self.vector_sync:
            await self.vector_sync.stop()
        
        if self.token_optimizer:
            await self.token_optimizer.stop()
        
        logger.info("UnifiedIntegrationService stopped")
    
    # ========================================================================
    # VECTOR SYNC API
    # ========================================================================
    
    async def sync_vector(
        self,
        collection: str,
        point_id: str,
        vector: List[float],
        payload: Dict[str, Any],
        source: str = "api"
    ) -> None:
        """Sincroniza un vector"""
        if self.vector_sync:
            await self.vector_sync.publish_sync_event({
                "type": "upsert",
                "collection": collection,
                "point_id": point_id,
                "vector": vector,
                "payload": payload,
                "source": source,
            })
    
    async def delete_vector(
        self,
        collection: str,
        point_id: str,
        source: str = "api"
    ) -> None:
        """Elimina un vector sincronizado"""
        if self.vector_sync:
            await self.vector_sync.publish_sync_event({
                "type": "delete",
                "collection": collection,
                "point_id": point_id,
                "source": source,
            })
    
    # ========================================================================
    # TOKEN OPTIMIZATION API
    # ========================================================================
    
    async def optimize_content(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Optimiza contenido directamente
        
        Returns:
            Dict con contenido optimizado y tokens ahorrados
        """
        if self.token_optimizer:
            optimized, saved = await self.token_optimizer.optimizer.optimize(
                content, context
            )
            return {
                "optimized_content": optimized,
                "tokens_saved": saved,
                "original_length": len(content),
            }
        return {"optimized_content": content, "tokens_saved": 0}
    
    async def queue_optimization(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Encola optimización para procesamiento asíncrono"""
        if self.token_optimizer:
            callback_key = f"opt_result:{datetime.utcnow().timestamp()}"
            return await self.token_optimizer.request_optimization(
                content, context, callback_key
            )
        return ""
    
    # ========================================================================
    # STATUS & METRICS
    # ========================================================================
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene estado de todos los servicios"""
        status = {
            "running": self._running,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if self.vector_sync:
            status["vector_sync"] = self.vector_sync.get_status()
        
        if self.token_optimizer:
            status["token_optimizer"] = {
                "metrics": self.token_optimizer.get_metrics(),
                "report": self.token_optimizer.get_report(),
            }
        
        return status
    
    async def get_metrics_for_dashboard(self) -> Dict[str, Any]:
        """Obtiene métricas para dashboard"""
        metrics = {
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if self.vector_sync:
            vs_metrics = self.vector_sync.get_metrics()
            metrics["vector_sync"] = {
                "sync_count": vs_metrics.get("total_syncs", 0),
                "error_count": vs_metrics.get("error_count", 0),
                "error_rate": vs_metrics.get("error_rate", 0),
            }
        
        if self.token_optimizer:
            opt_metrics = self.token_optimizer.get_metrics()
            metrics["token_optimizer"] = {
                "total_input_tokens": opt_metrics.get("total_input_tokens", 0),
                "tokens_saved": opt_metrics.get("tokens_saved", 0),
                "cache_hit_rate": opt_metrics.get("cache_hit_rate", 0),
                "optimization_rate": opt_metrics.get("optimization_rate", 0),
            }
        
        return metrics


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_integration_service(
    redis_client,
    milvus_store=None,
    qdrant_store=None,
    embedding_fn: Optional[Callable] = None,
    enable_vector_sync: bool = True,
    enable_token_optimization: bool = True,
    **kwargs
) -> UnifiedIntegrationService:
    """
    Factory para crear el servicio de integración
    
    Args:
        redis_client: Cliente Redis
        milvus_store: Store de Milvus (opcional)
        qdrant_store: Store de Qdrant (opcional)
        embedding_fn: Función de embedding (opcional)
        enable_vector_sync: Habilitar sincronización de vectores
        enable_token_optimization: Habilitar optimización de tokens
        **kwargs: Configuraciones adicionales
    """
    config = IntegrationConfig(
        enable_vector_sync=enable_vector_sync,
        enable_token_optimization=enable_token_optimization,
        **kwargs
    )
    
    return UnifiedIntegrationService(
        redis_client=redis_client,
        milvus_store=milvus_store,
        qdrant_store=qdrant_store,
        embedding_fn=embedding_fn,
        config=config,
    )


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "IntegrationConfig",
    "VectorSyncIntegration",
    "TokenOptimizerIntegration",
    "UnifiedIntegrationService",
    "create_integration_service",
]
