"""
NEXUS Redis Streams Client - Sistema de Colas en Tiempo Real

Implementa colas con Redis Streams para:
- Activación de agentes en tiempo real
- Distribución de tareas con Consumer Groups
- Aislamiento multi-tenant via key namespacing
- Procesamiento paralelo con múltiples workers
"""

import asyncio
import json
import time
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
    Redis = None

logger = logging.getLogger(__name__)


class TaskPriority(str, Enum):
    """Prioridad de tareas"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(str, Enum):
    """Estado de tareas"""
    PENDING = "pending"
    QUEUED = "queued"
    ASSIGNED = "assigned"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class StreamMessage:
    """Mensaje en el stream de Redis"""
    id: str
    stream: str
    data: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    @classmethod
    def from_redis(cls, stream: str, message_id: bytes, data: Dict[bytes, bytes]) -> "StreamMessage":
        """Crea mensaje desde respuesta de Redis"""
        decoded_data = {}
        for k, v in data.items():
            key = k.decode("utf-8") if isinstance(k, bytes) else k
            value = v.decode("utf-8") if isinstance(v, bytes) else v
            # Intentar parsear JSON
            try:
                decoded_data[key] = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                decoded_data[key] = value
        
        return cls(
            id=message_id.decode("utf-8") if isinstance(message_id, bytes) else message_id,
            stream=stream,
            data=decoded_data
        )


@dataclass
class Task:
    """Tarea para ser procesada por un agente"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = ""
    user_id: str = ""
    session_id: str = ""
    agent_id: Optional[str] = None
    iovba_group_id: Optional[str] = None
    iovba_role: Optional[str] = None
    domain: Optional[str] = None
    task_type: str = "chat"
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: int = 300
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario para Redis"""
        return {
            "id": self.id,
            "tenant_id": self.tenant_id or "",
            "user_id": self.user_id or "",
            "session_id": self.session_id or "",
            "agent_id": self.agent_id or "",
            "iovba_group_id": self.iovba_group_id or "",
            "iovba_role": self.iovba_role or "",
            "domain": self.domain or "",
            "task_type": self.task_type or "chat",
            "priority": self.priority.value,
            "status": self.status.value,
            "input_data": json.dumps(self.input_data),
            "output_data": json.dumps(self.output_data) if self.output_data else "{}",
            "error": self.error or "",
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else "",
            "completed_at": self.completed_at.isoformat() if self.completed_at else "",
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "timeout_seconds": self.timeout_seconds,
            "metadata": json.dumps(self.metadata),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Crea tarea desde diccionario"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            tenant_id=data.get("tenant_id", ""),
            user_id=data.get("user_id", ""),
            session_id=data.get("session_id", ""),
            agent_id=data.get("agent_id"),
            iovba_group_id=data.get("iovba_group_id"),
            iovba_role=data.get("iovba_role"),
            domain=data.get("domain"),
            task_type=data.get("task_type", "chat"),
            priority=TaskPriority(data.get("priority", "normal")),
            status=TaskStatus(data.get("status", "pending")),
            input_data=json.loads(data.get("input_data", "{}")) if isinstance(data.get("input_data"), str) else data.get("input_data", {}),
            output_data=json.loads(data.get("output_data", "{}")) if isinstance(data.get("output_data"), str) else data.get("output_data"),
            error=data.get("error"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.utcnow(),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            timeout_seconds=data.get("timeout_seconds", 300),
            metadata=json.loads(data.get("metadata", "{}")) if isinstance(data.get("metadata"), str) else data.get("metadata", {}),
        )


class RedisStreamClient:
    """
    Cliente de Redis Streams para gestión de colas de tareas
    
    Características:
    - Consumer Groups para procesamiento paralelo
    - Key namespacing para multi-tenancy
    - Priorización de tareas
    - Ack/Nack de mensajes
    - Monitorización en tiempo real
    """
    
    # Key patterns
    STREAM_PREFIX = "nexus:tenant:{tenant_id}:streams"
    TASK_STREAM = "{prefix}:tasks:{priority}"
    AGENT_QUEUE = "{prefix}:agent:{agent_id}:queue"
    DEAD_LETTER = "{prefix}:dead_letter"
    CONSUMER_GROUP = "nexus-workers"
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        tenant_id: str = "default",
        consumer_name: Optional[str] = None,
    ):
        if not REDIS_AVAILABLE:
            raise ImportError("redis package required: pip install redis")
        
        self.redis_url = redis_url
        self.tenant_id = tenant_id
        self.consumer_name = consumer_name or f"worker-{uuid.uuid4().hex[:8]}"
        self._redis: Optional[Redis] = None
        self._running = False
        self._consumers: Dict[str, asyncio.Task] = {}
    
    @property
    def stream_prefix(self) -> str:
        """Prefijo de streams para el tenant actual"""
        return self.STREAM_PREFIX.format(tenant_id=self.tenant_id)
    
    def get_stream_key(self, priority: TaskPriority = TaskPriority.NORMAL) -> str:
        """Obtiene key del stream por prioridad"""
        return self.TASK_STREAM.format(prefix=self.stream_prefix, priority=priority.value)
    
    def get_agent_queue_key(self, agent_id: str) -> str:
        """Obtiene key de la cola de un agente específico"""
        return self.AGENT_QUEUE.format(prefix=self.stream_prefix, agent_id=agent_id)
    
    async def connect(self) -> None:
        """Conecta al servidor Redis"""
        self._redis = redis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=False
        )
        logger.info(f"Connected to Redis: {self.redis_url}")
        
        # Crear consumer groups si no existen
        await self._ensure_consumer_groups()
    
    async def disconnect(self) -> None:
        """Desconecta del servidor Redis"""
        self._running = False
        
        # Cancelar consumers activos
        for name, task in self._consumers.items():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        if self._redis:
            await self._redis.close()
            self._redis = None
        
        logger.info("Disconnected from Redis")
    
    async def _ensure_consumer_groups(self) -> None:
        """Crea consumer groups si no existen"""
        for priority in TaskPriority:
            stream_key = self.get_stream_key(priority)
            try:
                await self._redis.xgroup_create(
                    stream_key,
                    self.CONSUMER_GROUP,
                    id="0",
                    mkstream=True
                )
                logger.info(f"Created consumer group for {stream_key}")
            except redis.ResponseError as e:
                if "BUSYGROUP" not in str(e):
                    raise
                logger.debug(f"Consumer group already exists for {stream_key}")
    
    async def publish_task(self, task: Task) -> str:
        """
        Publica una tarea en el stream correspondiente
        
        Args:
            task: Tarea a publicar
            
        Returns:
            ID del mensaje en el stream
        """
        if not self._redis:
            raise RuntimeError("Not connected to Redis")
        
        stream_key = self.get_stream_key(task.priority)
        task.status = TaskStatus.QUEUED
        
        message_id = await self._redis.xadd(
            stream_key,
            task.to_dict(),
            maxlen=10000  # Limitar tamaño del stream
        )
        
        logger.info(
            f"Published task {task.id} to {stream_key}",
            extra={
                "task_id": task.id,
                "priority": task.priority.value,
                "user_id": task.user_id,
                "stream": stream_key
            }
        )
        
        return message_id.decode("utf-8") if isinstance(message_id, bytes) else message_id
    
    async def consume_tasks(
        self,
        priority: TaskPriority = TaskPriority.NORMAL,
        count: int = 1,
        block_ms: int = 5000,
    ) -> List[tuple[StreamMessage, Task]]:
        """
        Consume tareas del stream
        
        Args:
            priority: Prioridad del stream
            count: Número máximo de mensajes
            block_ms: Tiempo de bloqueo en ms
            
        Returns:
            Lista de tuplas (StreamMessage, Task)
        """
        if not self._redis:
            raise RuntimeError("Not connected to Redis")
        
        stream_key = self.get_stream_key(priority)
        
        messages = await self._redis.xreadgroup(
            groupname=self.CONSUMER_GROUP,
            consumername=self.consumer_name,
            streams={stream_key: ">"},
            count=count,
            block=block_ms,
        )
        
        results = []
        if messages:
            for stream, msgs in messages:
                stream_name = stream.decode("utf-8") if isinstance(stream, bytes) else stream
                for msg_id, data in msgs:
                    msg = StreamMessage.from_redis(stream_name, msg_id, data)
                    try:
                        task = Task.from_dict(msg.data)
                        results.append((msg, task))
                    except Exception as e:
                        logger.error(f"Failed to parse task: {e}")
                        # Mover a dead letter queue
                        await self._move_to_dead_letter(stream_name, msg_id, data, str(e))
                        await self.ack_message(stream_name, msg_id)
        
        return results
    
    async def ack_message(self, stream: str, message_id: str) -> None:
        """Confirma procesamiento de mensaje"""
        if not self._redis:
            raise RuntimeError("Not connected to Redis")
        
        await self._redis.xack(stream, self.CONSUMER_GROUP, message_id)
        logger.debug(f"Acked message {message_id} from {stream}")
    
    async def nack_message(
        self,
        stream: str,
        message_id: str,
        retry: bool = True
    ) -> None:
        """
        Rechaza mensaje (lo devuelve a la cola)
        
        Args:
            stream: Nombre del stream
            message_id: ID del mensaje
            retry: Si True, devuelve a la cola; si False, mueve a dead letter
        """
        if not self._redis:
            raise RuntimeError("Not connected to Redis")
        
        if retry:
            # Redis Streams no tiene "nack" nativo
            # Simplemente no hacemos ack y el mensaje quedará pendiente
            # para ser reclamado
            logger.debug(f"Nack message {message_id} from {stream} (will retry)")
        else:
            # Mover a dead letter
            await self._redis.xack(stream, self.CONSUMER_GROUP, message_id)
            logger.warning(f"Nack message {message_id} from {stream} (moved to dead letter)")
    
    async def _move_to_dead_letter(
        self,
        stream: str,
        message_id: str,
        data: Dict[bytes, bytes],
        error: str
    ) -> None:
        """Mueve mensaje a cola de errores"""
        dlq_key = self.DEAD_LETTER.format(prefix=self.stream_prefix)
        
        dead_data = {
            "original_stream": stream,
            "original_id": message_id,
            "error": error,
            "timestamp": datetime.utcnow().isoformat(),
            "data": json.dumps({k.decode(): v.decode() for k, v in data.items()})
        }
        
        await self._redis.xadd(dlq_key, dead_data)
        logger.warning(f"Moved message {message_id} to dead letter queue")
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de las colas"""
        if not self._redis:
            raise RuntimeError("Not connected to Redis")
        
        stats = {
            "tenant_id": self.tenant_id,
            "streams": {},
            "pending_messages": 0,
            "dead_letter_count": 0
        }
        
        for priority in TaskPriority:
            stream_key = self.get_stream_key(priority)
            try:
                info = await self._redis.xinfo_stream(stream_key)
                
                # Contar mensajes pendientes
                pending = await self._redis.xpending(stream_key, self.CONSUMER_GROUP)
                
                stats["streams"][priority.value] = {
                    "length": info.get("length", 0),
                    "first_entry": info.get("first_entry"),
                    "last_entry": info.get("last_entry"),
                    "pending": pending.get("pending", 0) if pending else 0
                }
                stats["pending_messages"] += info.get("length", 0)
            except Exception:
                # Stream no existe aún
                stats["streams"][priority.value] = {
                    "length": 0,
                    "first_entry": None,
                    "last_entry": None,
                    "pending": 0
                }
        
        # Dead letter count
        dlq_key = self.DEAD_LETTER.format(prefix=self.stream_prefix)
        try:
            dlq_info = await self._redis.xinfo_stream(dlq_key)
            stats["dead_letter_count"] = dlq_info.get("length", 0) if dlq_info else 0
        except Exception:
            stats["dead_letter_count"] = 0
        
        return stats
    
    async def get_pending_tasks(
        self,
        min_idle_ms: int = 60000
    ) -> List[tuple[str, Task]]:
        """
        Obtiene tareas pendientes que superaron el tiempo de idle
        (para reasignación o timeout)
        """
        if not self._redis:
            raise RuntimeError("Not connected to Redis")
        
        pending_tasks = []
        
        for priority in TaskPriority:
            stream_key = self.get_stream_key(priority)
            
            # Obtener mensajes pendientes
            pending = await self._redis.xpending_range(
                stream_key,
                self.CONSUMER_GROUP,
                "-",
                "+",
                count=100
            )
            
            for p in pending:
                if p.get("time_since_delivered", 0) > min_idle_ms:
                    # Obtener el mensaje
                    msgs = await self._redis.xrange(stream_key, p["message_id"], p["message_id"])
                    if msgs:
                        msg_id, data = msgs[0]
                        msg = StreamMessage.from_redis(stream_key, msg_id, data)
                        task = Task.from_dict(msg.data)
                        pending_tasks.append((p["consumer"].decode() if isinstance(p["consumer"], bytes) else p["consumer"], task))
        
        return pending_tasks
    
    async def claim_task(
        self,
        stream: str,
        message_id: str,
        min_idle_ms: int = 60000
    ) -> Optional[Task]:
        """
        Reclama una tarea que ha estado idle demasiado tiempo
        (para tareas que fueron asignadas pero no procesadas)
        """
        if not self._redis:
            raise RuntimeError("Not connected to Redis")
        
        try:
            claimed = await self._redis.xclaim(
                stream,
                self.CONSUMER_GROUP,
                self.consumer_name,
                min_idle_ms,
                [message_id]
            )
            
            if claimed:
                msg_id, data = claimed[0]
                msg = StreamMessage.from_redis(stream, msg_id, data)
                return Task.from_dict(msg.data)
        except Exception as e:
            logger.error(f"Failed to claim task {message_id}: {e}")
        
        return None
    
    async def clear_queue(self, priority: TaskPriority = TaskPriority.NORMAL) -> int:
        """Elimina todos los mensajes de una cola"""
        if not self._redis:
            raise RuntimeError("Not connected to Redis")
        
        stream_key = self.get_stream_key(priority)
        deleted = await self._redis.delete(stream_key)
        
        # Recrear stream y consumer group
        await self._ensure_consumer_groups()
        
        return deleted
