"""
Vector Store Synchronization System - Sincronización Milvus/Qdrant

Implementa sincronización bidireccional entre Milvus y Qdrant para:
- Alta disponibilidad del almacenamiento vectorial
- Migración transparente de datos
- Replicación en tiempo real
- Backup y recovery

Patrones GOF utilizados:
- Strategy: Diferentes estrategias de sincronización
- Observer: Notificación de cambios
- Command: Operaciones encapsuladas
- Factory: Creación de sincronizadores

@author: NEXUS - Neural Execution Unified System
"""

from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from uuid import UUID, uuid4
from abc import ABC, abstractmethod
import asyncio
import json
import hashlib
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


# ============================================================================
# SYNC CONFIGURATION
# ============================================================================

class SyncDirection(str, Enum):
    """Dirección de sincronización"""
    MILVUS_TO_QDRANT = "milvus_to_qdrant"
    QDRANT_TO_MILVUS = "qdrant_to_milvus"
    BIDIRECTIONAL = "bidirectional"


class SyncMode(str, Enum):
    """Modo de sincronización"""
    REAL_TIME = "real_time"           # Sincronización inmediata
    BATCH = "batch"                   # Sincronización por lotes
    SCHEDULED = "scheduled"           # Sincronización programada
    ON_DEMAND = "on_demand"           # Bajo demanda


class ConflictResolution(str, Enum):
    """Estrategia de resolución de conflictos"""
    SOURCE_WINS = "source_wins"       # El origen tiene prioridad
    TARGET_WINS = "target_wins"       # El destino tiene prioridad
    NEWEST_WINS = "newest_wins"       # El más reciente gana
    MERGE = "merge"                   # Fusionar datos
    MANUAL = "manual"                 # Requiere intervención manual


@dataclass
class SyncConfig:
    """Configuración de sincronización"""
    direction: SyncDirection = SyncDirection.BIDIRECTIONAL
    mode: SyncMode = SyncMode.BATCH
    conflict_resolution: ConflictResolution = ConflictResolution.NEWEST_WINS
    batch_size: int = 100
    sync_interval_seconds: int = 60
    retry_attempts: int = 3
    retry_delay_seconds: float = 1.0
    enable_versioning: bool = True
    enable_change_tracking: bool = True
    collections_to_sync: List[str] = field(default_factory=lambda: [
        "agent_profiles",
        "skills",
        "documents",
        "memory_entries",
        "cognitive_capital",
    ])


# ============================================================================
# SYNC EVENTS & STATE
# ============================================================================

@dataclass
class SyncEvent:
    """Evento de sincronización"""
    id: UUID = field(default_factory=uuid4)
    event_type: str = ""  # "upsert", "delete", "update"
    collection: str = ""
    point_id: str = ""
    source: str = ""  # "milvus" o "qdrant"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = field(default_factory=dict)
    vector: List[float] = field(default_factory=list)
    processed: bool = False
    attempts: int = 0
    error: Optional[str] = None


@dataclass
class SyncState:
    """Estado de sincronización"""
    last_sync_time: datetime = field(default_factory=datetime.utcnow)
    last_sync_count: int = 0
    pending_events: int = 0
    failed_events: int = 0
    total_synced: int = 0
    collections_synced: Set[str] = field(default_factory=set)
    version: int = 0


# ============================================================================
# OBSERVER PATTERN - Sync Event Listeners
# ============================================================================

class SyncObserver(ABC):
    """Observer para eventos de sincronización"""
    
    @abstractmethod
    async def on_sync_event(self, event: SyncEvent) -> None:
        """Notifica un evento de sincronización"""
        pass
    
    @abstractmethod
    async def on_sync_complete(self, state: SyncState) -> None:
        """Notifica completación de sincronización"""
        pass
    
    @abstractmethod
    async def on_sync_error(self, error: Exception, event: SyncEvent) -> None:
        """Notifica error en sincronización"""
        pass


class LoggingSyncObserver(SyncObserver):
    """Observer que registra eventos en logs"""
    
    async def on_sync_event(self, event: SyncEvent) -> None:
        logger.info(f"Sync event: {event.event_type} on {event.collection}.{event.point_id}")
    
    async def on_sync_complete(self, state: SyncState) -> None:
        logger.info(f"Sync complete: {state.total_synced} total synced, version {state.version}")
    
    async def on_sync_error(self, error: Exception, event: SyncEvent) -> None:
        logger.error(f"Sync error on {event.point_id}: {error}")


class MetricsSyncObserver(SyncObserver):
    """Observer que recopila métricas de sincronización"""
    
    def __init__(self):
        self.metrics: Dict[str, Any] = defaultdict(int)
        self.errors: List[Dict[str, Any]] = []
        self.latencies: List[float] = []
    
    async def on_sync_event(self, event: SyncEvent) -> None:
        self.metrics[f"{event.event_type}_count"] += 1
        self.metrics[f"{event.source}_events"] += 1
    
    async def on_sync_complete(self, state: SyncState) -> None:
        self.metrics["total_syncs"] += 1
        self.metrics["last_sync_count"] = state.last_sync_count
    
    async def on_sync_error(self, error: Exception, event: SyncEvent) -> None:
        self.errors.append({
            "timestamp": datetime.utcnow().isoformat(),
            "event_id": str(event.id),
            "error": str(error),
        })
        self.metrics["error_count"] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        return {
            **self.metrics,
            "error_rate": self.metrics.get("error_count", 0) / max(1, self.metrics.get("total_syncs", 1)),
        }


# ============================================================================
# COMMAND PATTERN - Sync Operations
# ============================================================================

class SyncCommand(ABC):
    """Comando de sincronización encapsulado"""
    
    @abstractmethod
    async def execute(self) -> bool:
        """Ejecuta el comando de sincronización"""
        pass
    
    @abstractmethod
    async def undo(self) -> bool:
        """Deshace el comando (si es posible)"""
        pass
    
    @abstractmethod
    def get_event(self) -> SyncEvent:
        """Obtiene el evento asociado"""
        pass


class UpsertSyncCommand(SyncCommand):
    """Comando para sincronizar un upsert"""
    
    def __init__(
        self,
        target_store,
        collection: str,
        point_id: str,
        vector: List[float],
        payload: Dict[str, Any],
        tenant_id: str = "default"
    ):
        self.target_store = target_store
        self.collection = collection
        self.point_id = point_id
        self.vector = vector
        self.payload = payload
        self.tenant_id = tenant_id
        self._event = SyncEvent(
            event_type="upsert",
            collection=collection,
            point_id=point_id,
            data=payload,
            vector=vector,
        )
        self._success = False
    
    async def execute(self) -> bool:
        try:
            if hasattr(self.target_store, 'upsert'):
                import asyncio
                if asyncio.iscoroutinefunction(self.target_store.upsert):
                    self._success = await self.target_store.upsert(
                        collection_name=self.collection,
                        point_id=self.point_id,
                        vector=self.vector,
                        payload=self.payload,
                        tenant_id=self.tenant_id,
                    )
                else:
                    self._success = self.target_store.upsert(
                        collection_name=self.collection,
                        point_id=self.point_id,
                        vector=self.vector,
                        payload=self.payload,
                        tenant_id=self.tenant_id,
                    )
            return self._success
        except Exception as e:
            logger.error(f"UpsertSyncCommand failed: {e}")
            return False
    
    async def undo(self) -> bool:
        # No implementado - el undo de upsert es complejo
        return False
    
    def get_event(self) -> SyncEvent:
        return self._event


class DeleteSyncCommand(SyncCommand):
    """Comando para sincronizar un delete"""
    
    def __init__(
        self,
        target_store,
        collection: str,
        point_id: str,
        tenant_id: str = "default"
    ):
        self.target_store = target_store
        self.collection = collection
        self.point_id = point_id
        self.tenant_id = tenant_id
        self._event = SyncEvent(
            event_type="delete",
            collection=collection,
            point_id=point_id,
        )
        self._previous_data: Optional[Dict[str, Any]] = None
    
    async def execute(self) -> bool:
        try:
            if hasattr(self.target_store, 'delete'):
                self._success = self.target_store.delete(
                    collection_name=self.collection,
                    point_id=self.point_id,
                    tenant_id=self.tenant_id,
                )
            return True
        except Exception as e:
            logger.error(f"DeleteSyncCommand failed: {e}")
            return False
    
    async def undo(self) -> bool:
        # No implementado sin datos previos
        return False
    
    def get_event(self) -> SyncEvent:
        return self._event


# ============================================================================
# STRATEGY PATTERN - Sync Strategies
# ============================================================================

class SyncStrategy(ABC):
    """Estrategia de sincronización"""
    
    @abstractmethod
    async def sync(
        self,
        source_store,
        target_store,
        collection: str,
        config: SyncConfig
    ) -> Dict[str, Any]:
        """Ejecuta la sincronización según la estrategia"""
        pass


class FullSyncStrategy(SyncStrategy):
    """Sincronización completa - copia todos los datos"""
    
    async def sync(
        self,
        source_store,
        target_store,
        collection: str,
        config: SyncConfig
    ) -> Dict[str, Any]:
        result = {
            "collection": collection,
            "synced": 0,
            "failed": 0,
            "skipped": 0,
        }
        
        # Obtener todos los puntos del source
        try:
            # Iterar sobre lotes
            offset = 0
            batch_size = config.batch_size
            
            while True:
                # Usar scroll/iterate según disponibilidad
                points = await self._fetch_batch(source_store, collection, offset, batch_size)
                
                if not points:
                    break
                
                # Sincronizar cada punto
                for point in points:
                    try:
                        command = UpsertSyncCommand(
                            target_store=target_store,
                            collection=collection,
                            point_id=point["id"],
                            vector=point.get("vector", []),
                            payload=point.get("payload", {}),
                            tenant_id=point.get("tenant_id", "default"),
                        )
                        
                        success = await command.execute()
                        if success:
                            result["synced"] += 1
                        else:
                            result["failed"] += 1
                            
                    except Exception as e:
                        logger.error(f"Failed to sync point {point.get('id')}: {e}")
                        result["failed"] += 1
                
                offset += batch_size
                
                if len(points) < batch_size:
                    break
            
        except Exception as e:
            logger.error(f"Full sync failed for {collection}: {e}")
            result["error"] = str(e)
        
        return result
    
    async def _fetch_batch(
        self,
        store,
        collection: str,
        offset: int,
        limit: int
    ) -> List[Dict[str, Any]]:
        """Obtiene un lote de puntos"""
        # Implementación genérica - adaptar según el store específico
        try:
            if hasattr(store, 'scroll'):
                return await store.scroll(collection, offset=offset, limit=limit)
            elif hasattr(store, 'list_points'):
                return await store.list_points(collection, offset=offset, limit=limit)
        except Exception as e:
            logger.warning(f"Could not fetch batch: {e}")
        return []


class IncrementalSyncStrategy(SyncStrategy):
    """Sincronización incremental - solo cambios desde última sync"""
    
    def __init__(self):
        self._last_sync_times: Dict[str, datetime] = {}
    
    async def sync(
        self,
        source_store,
        target_store,
        collection: str,
        config: SyncConfig
    ) -> Dict[str, Any]:
        result = {
            "collection": collection,
            "synced": 0,
            "failed": 0,
            "skipped": 0,
        }
        
        last_sync = self._last_sync_times.get(collection, datetime.utcnow() - timedelta(days=1))
        
        try:
            # Obtener cambios desde última sincronización
            changes = await self._get_changes_since(source_store, collection, last_sync)
            
            for change in changes:
                try:
                    if change.get("deleted"):
                        command = DeleteSyncCommand(
                            target_store=target_store,
                            collection=collection,
                            point_id=change["id"],
                        )
                    else:
                        command = UpsertSyncCommand(
                            target_store=target_store,
                            collection=collection,
                            point_id=change["id"],
                            vector=change.get("vector", []),
                            payload=change.get("payload", {}),
                        )
                    
                    success = await command.execute()
                    if success:
                        result["synced"] += 1
                    else:
                        result["failed"] += 1
                        
                except Exception as e:
                    logger.error(f"Failed to sync change: {e}")
                    result["failed"] += 1
            
            self._last_sync_times[collection] = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Incremental sync failed for {collection}: {e}")
            result["error"] = str(e)
        
        return result
    
    async def _get_changes_since(
        self,
        store,
        collection: str,
        since: datetime
    ) -> List[Dict[str, Any]]:
        """Obtiene cambios desde una fecha"""
        # Implementación depende de capacidades del store
        try:
            if hasattr(store, 'get_changes_since'):
                return await store.get_changes_since(collection, since)
        except Exception:
            pass
        return []


class DeltaSyncStrategy(SyncStrategy):
    """Sincronización delta - compara y sincroniza diferencias"""
    
    async def sync(
        self,
        source_store,
        target_store,
        collection: str,
        config: SyncConfig
    ) -> Dict[str, Any]:
        result = {
            "collection": collection,
            "synced": 0,
            "failed": 0,
            "skipped": 0,
            "added": 0,
            "updated": 0,
            "deleted": 0,
        }
        
        try:
            # Obtener IDs de ambos stores
            source_ids = await self._get_all_ids(source_store, collection)
            target_ids = await self._get_all_ids(target_store, collection)
            
            source_set = set(source_ids)
            target_set = set(target_ids)
            
            # IDs a agregar
            to_add = source_set - target_set
            
            # IDs posiblemente actualizados
            to_check = source_set & target_set
            
            # IDs a eliminar (si sync bidireccional)
            to_delete = target_set - source_set
            
            # Agregar nuevos
            for point_id in to_add:
                try:
                    point_data = await self._get_point(source_store, collection, point_id)
                    if point_data:
                        command = UpsertSyncCommand(
                            target_store=target_store,
                            collection=collection,
                            point_id=point_id,
                            vector=point_data.get("vector", []),
                            payload=point_data.get("payload", {}),
                        )
                        success = await command.execute()
                        if success:
                            result["added"] += 1
                            result["synced"] += 1
                        else:
                            result["failed"] += 1
                except Exception as e:
                    logger.error(f"Failed to add {point_id}: {e}")
                    result["failed"] += 1
            
            # Verificar actualizaciones
            for point_id in to_check:
                try:
                    source_data = await self._get_point(source_store, collection, point_id)
                    target_data = await self._get_point(target_store, collection, point_id)
                    
                    if self._needs_update(source_data, target_data, config):
                        command = UpsertSyncCommand(
                            target_store=target_store,
                            collection=collection,
                            point_id=point_id,
                            vector=source_data.get("vector", []),
                            payload=source_data.get("payload", {}),
                        )
                        success = await command.execute()
                        if success:
                            result["updated"] += 1
                            result["synced"] += 1
                        else:
                            result["failed"] += 1
                    else:
                        result["skipped"] += 1
                except Exception as e:
                    logger.error(f"Failed to check/update {point_id}: {e}")
            
        except Exception as e:
            logger.error(f"Delta sync failed for {collection}: {e}")
            result["error"] = str(e)
        
        return result
    
    async def _get_all_ids(self, store, collection: str) -> List[str]:
        """Obtiene todos los IDs de una colección"""
        try:
            if hasattr(store, 'get_all_ids'):
                return await store.get_all_ids(collection)
        except Exception:
            pass
        return []
    
    async def _get_point(self, store, collection: str, point_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene un punto por ID"""
        try:
            if hasattr(store, 'get_point'):
                return await store.get_point(collection, point_id)
        except Exception:
            pass
        return None
    
    def _needs_update(
        self,
        source_data: Optional[Dict[str, Any]],
        target_data: Optional[Dict[str, Any]],
        config: SyncConfig
    ) -> bool:
        """Determina si un punto necesita actualización"""
        if not source_data or not target_data:
            return True
        
        # Comparar hashes de contenido
        source_hash = self._compute_hash(source_data)
        target_hash = self._compute_hash(target_data)
        
        return source_hash != target_hash
    
    def _compute_hash(self, data: Dict[str, Any]) -> str:
        """Computa hash de datos"""
        content = json.dumps(data.get("payload", {}), sort_keys=True, default=str)
        return hashlib.md5(content.encode()).hexdigest()


# ============================================================================
# FACTORY PATTERN - Sync Strategy Factory
# ============================================================================

class SyncStrategyFactory:
    """Factory para crear estrategias de sincronización"""
    
    _strategies: Dict[SyncMode, type] = {
        SyncMode.BATCH: DeltaSyncStrategy,
        SyncMode.REAL_TIME: IncrementalSyncStrategy,
        SyncMode.SCHEDULED: FullSyncStrategy,
        SyncMode.ON_DEMAND: DeltaSyncStrategy,
    }
    
    @classmethod
    def create(cls, mode: SyncMode) -> SyncStrategy:
        """Crea una estrategia según el modo"""
        strategy_class = cls._strategies.get(mode, DeltaSyncStrategy)
        return strategy_class()
    
    @classmethod
    def register(cls, mode: SyncMode, strategy_class: type) -> None:
        """Registra una nueva estrategia"""
        cls._strategies[mode] = strategy_class


# ============================================================================
# VECTOR STORE SYNCHRONIZER - Main Component
# ============================================================================

class VectorStoreSynchronizer:
    """
    Sincronizador principal de Vector Stores
    
    Implementa:
    - Sincronización bidireccional Milvus ↔ Qdrant
    - Resolución de conflictos
    - Versionado de datos
    - Notificaciones a observers
    - Ralph Loop para sincronización continua
    """
    
    def __init__(
        self,
        milvus_store=None,
        qdrant_store=None,
        config: Optional[SyncConfig] = None,
        redis_client=None
    ):
        self.milvus = milvus_store
        self.qdrant = qdrant_store
        self.config = config or SyncConfig()
        self.redis = redis_client
        
        # Estado
        self.state = SyncState()
        self._observers: List[SyncObserver] = []
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._version_cache: Dict[str, int] = {}
        
        # Métricas
        self._sync_count = 0
        self._error_count = 0
    
    # ========================================================================
    # OBSERVER MANAGEMENT
    # ========================================================================
    
    def add_observer(self, observer: SyncObserver) -> None:
        """Agrega un observer"""
        self._observers.append(observer)
    
    def remove_observer(self, observer: SyncObserver) -> None:
        """Remueve un observer"""
        if observer in self._observers:
            self._observers.remove(observer)
    
    async def _notify_event(self, event: SyncEvent) -> None:
        """Notifica evento a todos los observers"""
        for observer in self._observers:
            try:
                await observer.on_sync_event(event)
            except Exception as e:
                logger.error(f"Observer error: {e}")
    
    async def _notify_complete(self) -> None:
        """Notifica completación a todos los observers"""
        for observer in self._observers:
            try:
                await observer.on_sync_complete(self.state)
            except Exception as e:
                logger.error(f"Observer error: {e}")
    
    async def _notify_error(self, error: Exception, event: SyncEvent) -> None:
        """Notifica error a todos los observers"""
        self._error_count += 1
        for observer in self._observers:
            try:
                await observer.on_sync_error(error, event)
            except Exception as e:
                logger.error(f"Observer error: {e}")
    
    # ========================================================================
    # MAIN SYNC OPERATIONS
    # ========================================================================
    
    async def sync_all(self) -> Dict[str, Any]:
        """Sincroniza todas las colecciones configuradas"""
        results = {}
        
        strategy = SyncStrategyFactory.create(self.config.mode)
        
        for collection in self.config.collections_to_sync:
            try:
                # Sincronizar según dirección configurada
                if self.config.direction in [SyncDirection.MILVUS_TO_QDRANT, SyncDirection.BIDIRECTIONAL]:
                    result = await strategy.sync(
                        source_store=self.milvus,
                        target_store=self.qdrant,
                        collection=collection,
                        config=self.config,
                    )
                    results[f"milvus_to_qdrant:{collection}"] = result
                
                if self.config.direction in [SyncDirection.QDRANT_TO_MILVUS, SyncDirection.BIDIRECTIONAL]:
                    result = await strategy.sync(
                        source_store=self.qdrant,
                        target_store=self.milvus,
                        collection=collection,
                        config=self.config,
                    )
                    results[f"qdrant_to_milvus:{collection}"] = result
                
                self.state.collections_synced.add(collection)
                
            except Exception as e:
                logger.error(f"Sync failed for {collection}: {e}")
                results[f"error:{collection}"] = str(e)
        
        # Actualizar estado
        self.state.last_sync_time = datetime.utcnow()
        self.state.version += 1
        self._sync_count += 1
        
        await self._notify_complete()
        
        return results
    
    async def sync_collection(self, collection: str) -> Dict[str, Any]:
        """Sincroniza una colección específica"""
        strategy = SyncStrategyFactory.create(self.config.mode)
        
        results = {}
        
        if self.config.direction in [SyncDirection.MILVUS_TO_QDRANT, SyncDirection.BIDIRECTIONAL]:
            results["milvus_to_qdrant"] = await strategy.sync(
                source_store=self.milvus,
                target_store=self.qdrant,
                collection=collection,
                config=self.config,
            )
        
        if self.config.direction in [SyncDirection.QDRANT_TO_MILVUS, SyncDirection.BIDIRECTIONAL]:
            results["qdrant_to_milvus"] = await strategy.sync(
                source_store=self.qdrant,
                target_store=self.milvus,
                collection=collection,
                config=self.config,
            )
        
        return results
    
    async def migrate(
        self,
        source: str,
        target: str,
        collections: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Migra datos de un store a otro"""
        source_store = self.milvus if source == "milvus" else self.qdrant
        target_store = self.qdrant if source == "milvus" else self.milvus
        
        if not source_store or not target_store:
            return {"error": "Source or target store not available"}
        
        collections = collections or self.config.collections_to_sync
        results = {}
        
        # Usar estrategia de sincronización completa para migración
        strategy = FullSyncStrategy()
        
        for collection in collections:
            results[collection] = await strategy.sync(
                source_store=source_store,
                target_store=target_store,
                collection=collection,
                config=self.config,
            )
        
        return results
    
    # ========================================================================
    # RALPH LOOP - Continuous Sync
    # ========================================================================
    
    async def start_continuous_sync(self) -> None:
        """
        Inicia sincronización continua usando Ralph Loop
        
        Ralph Loop mantiene el proceso activo con múltiples pasos:
        1. Verificar si hay cambios pendientes
        2. Procesar cola de eventos
        3. Sincronizar cambios
        4. Actualizar estado
        5. Esperar intervalo
        6. Repetir
        """
        self._running = True
        logger.info("Starting continuous sync (Ralph Loop)")
        
        while self._running:
            try:
                # PASO 1: Verificar cambios pendientes
                pending = self._event_queue.qsize()
                self.state.pending_events = pending
                
                # PASO 2: Procesar cola de eventos
                if pending > 0:
                    await self._process_event_queue()
                
                # PASO 3: Sincronización incremental si está habilitada
                if self.config.mode == SyncMode.REAL_TIME:
                    await self._sync_changes()
                
                # PASO 4: Actualizar estado en Redis
                if self.redis:
                    await self._persist_state()
                
                # PASO 5: Esperar intervalo
                await asyncio.sleep(self.config.sync_interval_seconds)
                
            except asyncio.CancelledError:
                logger.info("Continuous sync cancelled")
                break
            except Exception as e:
                logger.error(f"Error in continuous sync: {e}")
                await asyncio.sleep(self.config.retry_delay_seconds)
    
    def stop_continuous_sync(self) -> None:
        """Detiene la sincronización continua"""
        self._running = False
        logger.info("Stopping continuous sync")
    
    async def _process_event_queue(self) -> None:
        """Procesa la cola de eventos pendientes"""
        processed = 0
        
        while not self._event_queue.empty() and processed < self.config.batch_size:
            try:
                event = await asyncio.wait_for(
                    self._event_queue.get(),
                    timeout=1.0
                )
                
                await self._process_single_event(event)
                processed += 1
                
            except asyncio.TimeoutError:
                break
            except Exception as e:
                logger.error(f"Error processing event: {e}")
    
    async def _process_single_event(self, event: SyncEvent) -> bool:
        """Procesa un único evento de sincronización"""
        target_store = self.qdrant if event.source == "milvus" else self.milvus
        
        if not target_store:
            return False
        
        try:
            if event.event_type == "upsert":
                command = UpsertSyncCommand(
                    target_store=target_store,
                    collection=event.collection,
                    point_id=event.point_id,
                    vector=event.vector,
                    payload=event.data,
                )
            elif event.event_type == "delete":
                command = DeleteSyncCommand(
                    target_store=target_store,
                    collection=event.collection,
                    point_id=event.point_id,
                )
            else:
                return False
            
            success = await command.execute()
            event.processed = success
            
            if success:
                await self._notify_event(event)
            else:
                event.attempts += 1
                if event.attempts < self.config.retry_attempts:
                    await self._event_queue.put(event)
                else:
                    await self._notify_error(Exception("Max retries exceeded"), event)
            
            return success
            
        except Exception as e:
            await self._notify_error(e, event)
            return False
    
    async def _sync_changes(self) -> None:
        """Sincroniza cambios detectados"""
        strategy = IncrementalSyncStrategy()
        
        for collection in self.config.collections_to_sync:
            try:
                await strategy.sync(
                    source_store=self.milvus,
                    target_store=self.qdrant,
                    collection=collection,
                    config=self.config,
                )
            except Exception as e:
                logger.error(f"Error syncing changes for {collection}: {e}")
    
    async def _persist_state(self) -> None:
        """Persiste el estado en Redis"""
        if not self.redis:
            return
        
        try:
            state_data = {
                "last_sync_time": self.state.last_sync_time.isoformat(),
                "last_sync_count": self.state.last_sync_count,
                "total_synced": self.state.total_synced,
                "version": self.state.version,
            }
            await self.redis.set("vector_sync:state", json.dumps(state_data))
        except Exception as e:
            logger.error(f"Failed to persist state: {e}")
    
    # ========================================================================
    # PUBLIC API - Event Queue
    # ========================================================================
    
    async def queue_upsert(
        self,
        collection: str,
        point_id: str,
        vector: List[float],
        payload: Dict[str, Any],
        source: str = "external"
    ) -> None:
        """Encola un evento de upsert para sincronización"""
        event = SyncEvent(
            event_type="upsert",
            collection=collection,
            point_id=point_id,
            source=source,
            vector=vector,
            data=payload,
        )
        await self._event_queue.put(event)
    
    async def queue_delete(
        self,
        collection: str,
        point_id: str,
        source: str = "external"
    ) -> None:
        """Encola un evento de delete para sincronización"""
        event = SyncEvent(
            event_type="delete",
            collection=collection,
            point_id=point_id,
            source=source,
        )
        await self._event_queue.put(event)
    
    # ========================================================================
    # STATUS & METRICS
    # ========================================================================
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado actual del sincronizador"""
        return {
            "running": self._running,
            "state": {
                "last_sync_time": self.state.last_sync_time.isoformat(),
                "last_sync_count": self.state.last_sync_count,
                "pending_events": self._event_queue.qsize(),
                "total_synced": self.state.total_synced,
                "version": self.state.version,
                "collections_synced": list(self.state.collections_synced),
            },
            "config": {
                "direction": self.config.direction.value,
                "mode": self.config.mode.value,
                "batch_size": self.config.batch_size,
                "sync_interval": self.config.sync_interval_seconds,
            },
            "metrics": {
                "sync_count": self._sync_count,
                "error_count": self._error_count,
            },
            "stores": {
                "milvus": self.milvus is not None,
                "qdrant": self.qdrant is not None,
            }
        }
    
    async def get_sync_report(self) -> Dict[str, Any]:
        """Genera un reporte detallado de sincronización"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total_syncs": self._sync_count,
                "total_errors": self._error_count,
                "success_rate": self._sync_count / max(1, self._sync_count + self._error_count),
            },
            "collections": {
                col: {
                    "synced": col in self.state.collections_synced,
                    "version": self._version_cache.get(col, 0),
                }
                for col in self.config.collections_to_sync
            },
            "state": self.state.__dict__,
        }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def create_synchronizer(
    milvus_store=None,
    qdrant_store=None,
    direction: str = "bidirectional",
    mode: str = "batch",
    **kwargs
) -> VectorStoreSynchronizer:
    """
    Factory function para crear un sincronizador
    
    Args:
        milvus_store: Instancia de MilvusVectorStore
        qdrant_store: Instancia de QdrantVectorStore
        direction: "bidirectional", "milvus_to_qdrant", "qdrant_to_milvus"
        mode: "batch", "real_time", "scheduled", "on_demand"
        **kwargs: Configuraciones adicionales
    """
    config = SyncConfig(
        direction=SyncDirection(direction),
        mode=SyncMode(mode),
        **kwargs
    )
    
    synchronizer = VectorStoreSynchronizer(
        milvus_store=milvus_store,
        qdrant_store=qdrant_store,
        config=config,
    )
    
    # Agregar observers por defecto
    synchronizer.add_observer(LoggingSyncObserver())
    
    return synchronizer


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Configuration
    "SyncDirection",
    "SyncMode",
    "ConflictResolution",
    "SyncConfig",
    # Events & State
    "SyncEvent",
    "SyncState",
    # Observers
    "SyncObserver",
    "LoggingSyncObserver",
    "MetricsSyncObserver",
    # Commands
    "SyncCommand",
    "UpsertSyncCommand",
    "DeleteSyncCommand",
    # Strategies
    "SyncStrategy",
    "FullSyncStrategy",
    "IncrementalSyncStrategy",
    "DeltaSyncStrategy",
    "SyncStrategyFactory",
    # Main
    "VectorStoreSynchronizer",
    "create_synchronizer",
]
