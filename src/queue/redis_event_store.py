"""
NEXUS Redis Event Store - Almacén de Eventos con Redis

Implementa Event Sourcing con Redis para:
- Auditoría completa de todas las operaciones
- Streaming de eventos en tiempo real
- Snapshots de estado
- Consultas históricas
"""

import asyncio
import json
import uuid
from typing import Dict, List, Optional, Any, Callable, Awaitable
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import logging

try:
    import redis.asyncio as redis
    from redis.asyncio import Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Tipos de eventos del sistema"""
    # Tareas
    TASK_CREATED = "task.created"
    TASK_QUEUED = "task.queued"
    TASK_ASSIGNED = "task.assigned"
    TASK_STARTED = "task.started"
    TASK_PROGRESS = "task.progress"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_TIMEOUT = "task.timeout"
    TASK_RETRY = "task.retry"
    
    # Agentes
    AGENT_REGISTERED = "agent.registered"
    AGENT_AVAILABLE = "agent.available"
    AGENT_BUSY = "agent.busy"
    AGENT_OFFLINE = "agent.offline"
    AGENT_ERROR = "agent.error"
    
    # Usuario
    USER_SESSION_STARTED = "user.session.started"
    USER_SESSION_ENDED = "user.session.ended"
    USER_MESSAGE = "user.message"
    
    # Sistema
    SYSTEM_START = "system.start"
    SYSTEM_STOP = "system.stop"
    SYSTEM_ERROR = "system.error"
    
    # IOVBA
    IOVBA_GROUP_CREATED = "iovba.group.created"
    IOVBA_AGENT_ACTIVATED = "iovba.agent.activated"
    IOVBA_CAPITAL_SYNC = "iovba.capital.sync"
    IOVBA_LEARNING = "iovba.learning"


@dataclass
class StoredEvent:
    """Evento almacenado en el Event Store"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.TASK_CREATED
    aggregate_id: str = ""
    aggregate_type: str = ""
    tenant_id: str = ""
    user_id: str = ""
    session_id: str = ""
    version: int = 1
    timestamp: datetime = field(default_factory=datetime.utcnow)
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None
    causation_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "event_type": self.event_type.value,
            "aggregate_id": self.aggregate_id,
            "aggregate_type": self.aggregate_type,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "version": self.version,
            "timestamp": self.timestamp.isoformat(),
            "payload": self.payload,
            "metadata": self.metadata,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StoredEvent":
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            event_type=EventType(data.get("event_type", "task.created")),
            aggregate_id=data.get("aggregate_id", ""),
            aggregate_type=data.get("aggregate_type", ""),
            tenant_id=data.get("tenant_id", ""),
            user_id=data.get("user_id", ""),
            session_id=data.get("session_id", ""),
            version=data.get("version", 1),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.utcnow(),
            payload=data.get("payload", {}),
            metadata=data.get("metadata", {}),
            correlation_id=data.get("correlation_id"),
            causation_id=data.get("causation_id"),
        )


class RedisEventStore:
    """
    Event Store con Redis Streams
    
    Características:
    - Append-only con Redis Streams
    - Event streaming en tiempo real
    - Consultas por aggregate, tipo, tenant
    - Snapshots con Redis Hash
    """
    
    # Key patterns
    EVENT_STREAM = "nexus:tenant:{tenant_id}:events:stream"
    AGGREGATE_EVENTS = "nexus:tenant:{tenant_id}:events:aggregate:{aggregate_type}:{aggregate_id}"
    SNAPSHOT_KEY = "nexus:tenant:{tenant_id}:snapshots:{aggregate_id}"
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        tenant_id: str = "default"
    ):
        if not REDIS_AVAILABLE:
            raise ImportError("redis package required: pip install redis")
        
        self.redis_url = redis_url
        self.tenant_id = tenant_id
        self._redis: Optional[Redis] = None
    
    def _get_stream_key(self) -> str:
        return self.EVENT_STREAM.format(tenant_id=self.tenant_id)
    
    def _get_aggregate_key(self, aggregate_type: str, aggregate_id: str) -> str:
        return self.AGGREGATE_EVENTS.format(
            tenant_id=self.tenant_id,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id
        )
    
    def _get_snapshot_key(self, aggregate_id: str) -> str:
        return self.SNAPSHOT_KEY.format(
            tenant_id=self.tenant_id,
            aggregate_id=aggregate_id
        )
    
    async def connect(self) -> None:
        """Conecta a Redis"""
        self._redis = redis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=False
        )
        logger.info(f"RedisEventStore connected to Redis")
    
    async def disconnect(self) -> None:
        """Desconecta de Redis"""
        if self._redis:
            await self._redis.close()
            self._redis = None
    
    async def append(self, event: StoredEvent) -> str:
        """
        Agrega un evento al store
        
        Args:
            event: Evento a almacenar
            
        Returns:
            ID del evento
        """
        if not self._redis:
            raise RuntimeError("Not connected to Redis")
        
        event_data = event.to_dict()
        
        # Agregar al stream principal
        stream_key = self._get_stream_key()
        message_id = await self._redis.xadd(
            stream_key,
            {k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) 
             for k, v in event_data.items()},
            maxlen=100000  # Limitar tamaño
        )
        
        # Agregar al índice del aggregate
        aggregate_key = self._get_aggregate_key(
            event.aggregate_type,
            event.aggregate_id
        )
        await self._redis.xadd(
            aggregate_key,
            {k: json.dumps(v) if isinstance(v, (dict, list)) else str(v) 
             for k, v in event_data.items()},
            maxlen=1000
        )
        
        logger.debug(
            f"Event appended: {event.event_type.value}",
            extra={
                "event_id": event.id,
                "aggregate_id": event.aggregate_id,
                "aggregate_type": event.aggregate_type,
            }
        )
        
        return event.id
    
    async def get_events(
        self,
        aggregate_id: Optional[str] = None,
        aggregate_type: Optional[str] = None,
        event_type: Optional[EventType] = None,
        limit: int = 100,
    ) -> List[StoredEvent]:
        """Consulta eventos con filtros"""
        if not self._redis:
            raise RuntimeError("Not connected to Redis")
        
        events = []
        
        if aggregate_id and aggregate_type:
            # Obtener eventos de un aggregate específico
            aggregate_key = self._get_aggregate_key(aggregate_type, aggregate_id)
            messages = await self._redis.xrange(aggregate_key, "-", "+", count=limit)
            
            for msg_id, data in messages:
                event_dict = self._decode_message(data)
                if event_type and event_dict.get("event_type") != event_type.value:
                    continue
                events.append(StoredEvent.from_dict(event_dict))
        else:
            # Obtener del stream principal
            stream_key = self._get_stream_key()
            messages = await self._redis.xrange(stream_key, "-", "+", count=limit)
            
            for msg_id, data in messages:
                event_dict = self._decode_message(data)
                if event_type and event_dict.get("event_type") != event_type.value:
                    continue
                events.append(StoredEvent.from_dict(event_dict))
        
        return events
    
    def _decode_message(self, data: Dict[bytes, bytes]) -> Dict[str, Any]:
        """Decodifica mensaje de Redis"""
        result = {}
        for k, v in data.items():
            key = k.decode("utf-8") if isinstance(k, bytes) else k
            value = v.decode("utf-8") if isinstance(v, bytes) else v
            try:
                result[key] = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                result[key] = value
        return result
    
    async def save_snapshot(
        self,
        aggregate_id: str,
        aggregate_type: str,
        version: int,
        state: Dict[str, Any]
    ) -> None:
        """Guarda un snapshot de estado"""
        if not self._redis:
            raise RuntimeError("Not connected to Redis")
        
        snapshot_key = self._get_snapshot_key(aggregate_id)
        await self._redis.hset(snapshot_key, mapping={
            "aggregate_type": aggregate_type,
            "version": version,
            "state": json.dumps(state),
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def get_snapshot(self, aggregate_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene el snapshot de un aggregate"""
        if not self._redis:
            raise RuntimeError("Not connected to Redis")
        
        snapshot_key = self._get_snapshot_key(aggregate_id)
        data = await self._redis.hgetall(snapshot_key)
        
        if not data:
            return None
        
        return {
            "aggregate_id": aggregate_id,
            "aggregate_type": data.get(b"aggregate_type", b"").decode(),
            "version": int(data.get(b"version", b"0").decode()),
            "state": json.loads(data.get(b"state", b"{}").decode()),
            "timestamp": data.get(b"timestamp", b"").decode()
        }
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas del Event Store"""
        if not self._redis:
            raise RuntimeError("Not connected to Redis")
        
        stream_key = self._get_stream_key()
        
        try:
            info = await self._redis.xinfo_stream(stream_key)
            return {
                "total_events": info.get("length", 0),
                "first_entry": info.get("first_entry"),
                "last_entry": info.get("last_entry"),
            }
        except Exception:
            return {
                "total_events": 0,
                "first_entry": None,
                "last_entry": None,
            }
    
    async def subscribe(
        self,
        handler: Callable[[StoredEvent], Awaitable[None]],
        event_types: Optional[List[EventType]] = None
    ) -> None:
        """
        Suscribe a eventos en tiempo real
        
        Args:
            handler: Función async para procesar eventos
            event_types: Tipos de eventos a filtrar (None = todos)
        """
        if not self._redis:
            raise RuntimeError("Not connected to Redis")
        
        stream_key = self._get_stream_key()
        last_id = "$"  # Solo nuevos eventos
        
        while True:
            try:
                messages = await self._redis.xread(
                    {stream_key: last_id},
                    block=5000,
                    count=10
                )
                
                if messages:
                    for stream, msgs in messages:
                        for msg_id, data in msgs:
                            last_id = msg_id.decode() if isinstance(msg_id, bytes) else msg_id
                            event_dict = self._decode_message(data)
                            
                            if event_types:
                                if event_dict.get("event_type") not in [e.value for e in event_types]:
                                    continue
                            
                            event = StoredEvent.from_dict(event_dict)
                            await handler(event)
                            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in event subscription: {e}")
                await asyncio.sleep(1)
