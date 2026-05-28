"""
NEXUS Event Store - Almacén de Eventos Persistente

Implementa Event Sourcing con PostgreSQL para:
- Auditoría completa de todas las operaciones
- Replay de eventos para recuperación
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
from contextlib import asynccontextmanager

try:
    from sqlalchemy import Column, String, DateTime, Text, Integer, JSON, Index, create_engine
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
    from sqlalchemy.orm import declarative_base, sessionmaker
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    declarative_base = lambda: object

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
    aggregate_id: str = ""  # ID de la entidad (task, agent, user, etc.)
    aggregate_type: str = ""  # Tipo de entidad (task, agent, user, iovba_group)
    tenant_id: str = ""
    user_id: str = ""
    session_id: str = ""
    version: int = 1
    timestamp: datetime = field(default_factory=datetime.utcnow)
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None  # Para rastrear flujos relacionados
    causation_id: Optional[str] = None  # ID del evento que causó este
    
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


if SQLALCHEMY_AVAILABLE:
    Base = declarative_base()
    
    class EventModel(Base):
        """Modelo SQLAlchemy para eventos"""
        __tablename__ = "nexus_events"
        
        id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        event_type = Column(String(50), nullable=False, index=True)
        aggregate_id = Column(String(100), nullable=False, index=True)
        aggregate_type = Column(String(50), nullable=False, index=True)
        tenant_id = Column(String(100), nullable=False, index=True)
        user_id = Column(String(100), index=True)
        session_id = Column(String(100), index=True)
        version = Column(Integer, nullable=False, default=1)
        timestamp = Column(DateTime, nullable=False, index=True)
        payload = Column(JSON, nullable=False, default=dict)
        event_metadata = Column(JSON, nullable=False, default=dict)
        correlation_id = Column(String(100), index=True)
        causation_id = Column(String(100))
        
        __table_args__ = (
            Index("ix_nexus_events_aggregate", "aggregate_type", "aggregate_id"),
            Index("ix_nexus_events_tenant_timestamp", "tenant_id", "timestamp"),
        )
    
    class SnapshotModel(Base):
        """Modelo para snapshots de estado"""
        __tablename__ = "nexus_snapshots"
        
        id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
        aggregate_id = Column(String(100), nullable=False, unique=True)
        aggregate_type = Column(String(50), nullable=False)
        version = Column(Integer, nullable=False)
        state = Column(JSON, nullable=False)
        timestamp = Column(DateTime, nullable=False)


class EventStore:
    """
    Event Store para persistencia y auditoría
    
    Características:
    - Append-only storage
    - Event replay para recuperación
    - Snapshots para optimización
    - Consultas por aggregate, tipo, tenant, usuario
    """
    
    def __init__(self, database_url: str = "postgresql+asyncpg://localhost/nexus"):
        if not SQLALCHEMY_AVAILABLE:
            raise ImportError("sqlalchemy with asyncpg required")
        
        self.database_url = database_url
        self._engine = None
        self._session_factory = None
    
    async def initialize(self) -> None:
        """Inicializa conexión y crea tablas"""
        self._engine = create_async_engine(
            self.database_url,
            echo=False,
            pool_size=10,
            max_overflow=20
        )
        
        self._session_factory = async_sessionmaker(
            self._engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Crear tablas
        async with self._engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info(f"EventStore initialized: {self.database_url}")
    
    async def close(self) -> None:
        """Cierra la conexión"""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
    
    @asynccontextmanager
    async def session(self):
        """Context manager para sesiones"""
        if not self._session_factory:
            raise RuntimeError("EventStore not initialized")
        
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    async def append(self, event: StoredEvent) -> str:
        """
        Agrega un evento al store
        
        Args:
            event: Evento a almacenar
            
        Returns:
            ID del evento
        """
        async with self.session() as session:
            model = EventModel(
                id=uuid.UUID(event.id),
                event_type=event.event_type.value,
                aggregate_id=event.aggregate_id,
                aggregate_type=event.aggregate_type,
                tenant_id=event.tenant_id,
                user_id=event.user_id,
                session_id=event.session_id,
                version=event.version,
                timestamp=event.timestamp,
                payload=event.payload,
                event_metadata=event.metadata,
                correlation_id=event.correlation_id,
                causation_id=event.causation_id,
            )
            session.add(model)
        
        logger.debug(
            f"Event appended: {event.event_type.value}",
            extra={
                "event_id": event.id,
                "aggregate_id": event.aggregate_id,
                "aggregate_type": event.aggregate_type,
            }
        )
        
        return event.id
    
    async def append_batch(self, events: List[StoredEvent]) -> List[str]:
        """Agrega múltiples eventos en una transacción"""
        async with self.session() as session:
            models = []
            for event in events:
                model = EventModel(
                    id=uuid.UUID(event.id),
                    event_type=event.event_type.value,
                    aggregate_id=event.aggregate_id,
                    aggregate_type=event.aggregate_type,
                    tenant_id=event.tenant_id,
                    user_id=event.user_id,
                    session_id=event.session_id,
                    version=event.version,
                    timestamp=event.timestamp,
                    payload=event.payload,
                    event_metadata=event.metadata,
                    correlation_id=event.correlation_id,
                    causation_id=event.causation_id,
                )
                models.append(model)
            
            session.add_all(models)
        
        return [e.id for e in events]
    
    async def get_events(
        self,
        aggregate_id: Optional[str] = None,
        aggregate_type: Optional[str] = None,
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
        event_type: Optional[EventType] = None,
        from_timestamp: Optional[datetime] = None,
        to_timestamp: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[StoredEvent]:
        """
        Consulta eventos con filtros
        """
        async with self.session() as session:
            from sqlalchemy import select
            
            query = select(EventModel)
            
            if aggregate_id:
                query = query.where(EventModel.aggregate_id == aggregate_id)
            if aggregate_type:
                query = query.where(EventModel.aggregate_type == aggregate_type)
            if tenant_id:
                query = query.where(EventModel.tenant_id == tenant_id)
            if user_id:
                query = query.where(EventModel.user_id == user_id)
            if event_type:
                query = query.where(EventModel.event_type == event_type.value)
            if from_timestamp:
                query = query.where(EventModel.timestamp >= from_timestamp)
            if to_timestamp:
                query = query.where(EventModel.timestamp <= to_timestamp)
            
            query = query.order_by(EventModel.timestamp.asc())
            query = query.limit(limit).offset(offset)
            
            result = await session.execute(query)
            models = result.scalars().all()
            
            return [
                StoredEvent(
                    id=str(m.id),
                    event_type=EventType(m.event_type),
                    aggregate_id=m.aggregate_id,
                    aggregate_type=m.aggregate_type,
                    tenant_id=m.tenant_id,
                    user_id=m.user_id or "",
                    session_id=m.session_id or "",
                    version=m.version,
                    timestamp=m.timestamp,
                    payload=m.payload or {},
                    metadata=m.event_metadata or {},
                    correlation_id=m.correlation_id,
                    causation_id=m.causation_id,
                )
                for m in models
            ]
    
    async def get_aggregate_events(
        self,
        aggregate_id: str,
        from_version: int = 0,
    ) -> List[StoredEvent]:
        """
        Obtiene todos los eventos de un aggregate desde una versión
        (para replay)
        """
        async with self.session() as session:
            from sqlalchemy import select
            
            query = select(EventModel).where(
                EventModel.aggregate_id == aggregate_id,
                EventModel.version > from_version
            ).order_by(EventModel.version.asc())
            
            result = await session.execute(query)
            models = result.scalars().all()
            
            return [
                StoredEvent(
                    id=str(m.id),
                    event_type=EventType(m.event_type),
                    aggregate_id=m.aggregate_id,
                    aggregate_type=m.aggregate_type,
                    tenant_id=m.tenant_id,
                    user_id=m.user_id or "",
                    session_id=m.session_id or "",
                    version=m.version,
                    timestamp=m.timestamp,
                    payload=m.payload or {},
                    metadata=m.event_metadata or {},
                    correlation_id=m.correlation_id,
                    causation_id=m.causation_id,
                )
                for m in models
            ]
    
    async def save_snapshot(
        self,
        aggregate_id: str,
        aggregate_type: str,
        version: int,
        state: Dict[str, Any]
    ) -> None:
        """Guarda un snapshot de estado"""
        async with self.session() as session:
            from sqlalchemy import update
            
            # Upsert
            existing = await session.execute(
                select(SnapshotModel).where(SnapshotModel.aggregate_id == aggregate_id)
            )
            existing = existing.scalar_one_or_none()
            
            if existing:
                existing.version = version
                existing.state = state
                existing.timestamp = datetime.utcnow()
            else:
                snapshot = SnapshotModel(
                    aggregate_id=aggregate_id,
                    aggregate_type=aggregate_type,
                    version=version,
                    state=state,
                    timestamp=datetime.utcnow()
                )
                session.add(snapshot)
    
    async def get_snapshot(self, aggregate_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene el snapshot más reciente de un aggregate"""
        async with self.session() as session:
            result = await session.execute(
                select(SnapshotModel).where(SnapshotModel.aggregate_id == aggregate_id)
            )
            snapshot = result.scalar_one_or_none()
            
            if snapshot:
                return {
                    "aggregate_id": snapshot.aggregate_id,
                    "aggregate_type": snapshot.aggregate_type,
                    "version": snapshot.version,
                    "state": snapshot.state,
                    "timestamp": snapshot.timestamp.isoformat()
                }
            return None
    
    async def replay_events(
        self,
        aggregate_id: str,
        handler: Callable[[StoredEvent], Awaitable[None]],
        from_version: int = 0
    ) -> int:
        """
        Replay de eventos para un aggregate
        
        Args:
            aggregate_id: ID del aggregate
            handler: Función async para procesar cada evento
            from_version: Versión desde la cual replay
            
        Returns:
            Número de eventos procesados
        """
        events = await self.get_aggregate_events(aggregate_id, from_version)
        
        for event in events:
            await handler(event)
        
        return len(events)
    
    async def get_statistics(
        self,
        tenant_id: Optional[str] = None,
        from_timestamp: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Obtiene estadísticas del Event Store"""
        async with self.session() as session:
            from sqlalchemy import func, select
            
            query = select(
                EventModel.event_type,
                func.count(EventModel.id).label("count")
            )
            
            if tenant_id:
                query = query.where(EventModel.tenant_id == tenant_id)
            if from_timestamp:
                query = query.where(EventModel.timestamp >= from_timestamp)
            
            query = query.group_by(EventModel.event_type)
            
            result = await session.execute(query)
            event_counts = {row.event_type: row.count for row in result}
            
            # Total events
            total_query = select(func.count(EventModel.id))
            if tenant_id:
                total_query = total_query.where(EventModel.tenant_id == tenant_id)
            if from_timestamp:
                total_query = total_query.where(EventModel.timestamp >= from_timestamp)
            
            total_result = await session.execute(total_query)
            total = total_result.scalar()
            
            return {
                "total_events": total,
                "events_by_type": event_counts,
                "tenant_id": tenant_id,
                "from_timestamp": from_timestamp.isoformat() if from_timestamp else None,
            }
