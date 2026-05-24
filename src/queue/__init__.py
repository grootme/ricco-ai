"""
NEXUS Queue System - Sistema de Colas y Eventos para Agentes IOVBA

Arquitectura:
- Redis Streams: Colas en tiempo real (<1ms latencia)
- Redis Event Store: Almacén de eventos en Redis
- Consumer Groups: Procesamiento paralelo
- Key Namespacing: Aislamiento multi-tenant

Componentes:
- RedisStreamClient: Cliente de colas Redis
- RedisEventStore: Almacén de eventos Redis
- AgentAvailabilityTracker: Tracker de disponibilidad
- AgentAssignmentEngine: Motor de asignación
- EventDispatcher: Dispatcher de eventos
- QueueWorker: Worker de procesamiento
"""

from .redis_streams import RedisStreamClient, StreamMessage
from .redis_event_store import RedisEventStore, StoredEvent, EventType
from .agent_tracker import AgentAvailabilityTracker, AgentStatus
from .assignment_engine import AgentAssignmentEngine, AssignmentResult
from .event_dispatcher import EventDispatcher, Event
from .worker import QueueWorker, TaskProcessor

__all__ = [
    # Redis Streams
    "RedisStreamClient",
    "StreamMessage",
    
    # Event Store
    "RedisEventStore",
    "StoredEvent",
    "EventType",
    
    # Agent Tracker
    "AgentAvailabilityTracker",
    "AgentStatus",
    
    # Assignment Engine
    "AgentAssignmentEngine",
    "AssignmentResult",
    
    # Event Dispatcher
    "EventDispatcher",
    "Event",
    
    # Worker
    "QueueWorker",
    "TaskProcessor",
]
