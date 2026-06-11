"""
NEXUS Event Dispatcher - Dispatcher de Eventos y Tareas

Sistema de dispatch para:
- Activación de agentes por eventos
- Routing de tareas a colas
- Eventos internos (webhooks, scheduled, system)
- Integración con chat y APIs externas
"""

import asyncio
import json
import uuid
from typing import Dict, List, Optional, Any, Callable, Awaitable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
from abc import ABC, abstractmethod

from .redis_streams import RedisStreamClient, Task, TaskPriority, TaskStatus
from .event_store import EventStore, StoredEvent, EventType
from .agent_tracker import AgentAvailabilityTracker, AgentInfo, AgentStatus
from .assignment_engine import AgentAssignmentEngine, AssignmentResult

logger = logging.getLogger(__name__)


class EventSource(str, Enum):
    """Fuente del evento"""
    CHAT = "chat"                    # Mensaje de chat de usuario
    API = "api"                      # Llamada API directa
    WEBHOOK = "webhook"              # Webhook externo
    SCHEDULED = "scheduled"          # Tarea programada
    INTERNAL = "internal"            # Evento interno del sistema
    IOVBA = "iovba"                  # Evento desde grupo IOVBA
    REDIS_PUBSUB = "redis_pubsub"    # Pub/Sub de Redis
    KAFKA = "kafka"                  # Mensaje de Kafka
    RABBITMQ = "rabbitmq"            # Mensaje de RabbitMQ


@dataclass
class Event:
    """Evento del sistema"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source: EventSource = EventSource.CHAT
    event_type: str = "message"
    tenant_id: str = ""
    user_id: str = ""
    session_id: str = ""
    agent_id: Optional[str] = None
    iovba_group_id: Optional[str] = None
    iovba_role: Optional[str] = None
    domain: Optional[str] = None
    priority: TaskPriority = TaskPriority.NORMAL
    payload: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None  # Para respuestas
    
    def to_task(self) -> Task:
        """Convierte evento a tarea"""
        return Task(
            id=str(uuid.uuid4()),
            tenant_id=self.tenant_id,
            user_id=self.user_id,
            session_id=self.session_id,
            agent_id=self.agent_id,
            iovba_group_id=self.iovba_group_id,
            iovba_role=self.iovba_role,
            domain=self.domain,
            task_type=self.event_type,
            priority=self.priority,
            input_data=self.payload,
            metadata={
                "event_id": self.id,
                "source": self.source.value,
                "correlation_id": self.correlation_id,
                "reply_to": self.reply_to,
                **self.metadata
            }
        )


class EventProcessor(ABC):
    """Interface para procesadores de eventos"""
    
    @abstractmethod
    async def process(self, event: Event) -> Optional[Task]:
        """Procesa un evento y opcionalmente retorna una tarea"""
        pass


class ChatEventProcessor(EventProcessor):
    """Procesador de eventos de chat"""
    
    async def process(self, event: Event) -> Optional[Task]:
        if event.source != EventSource.CHAT:
            return None
        
        # Validar payload de chat
        if "message" not in event.payload:
            logger.warning(f"Chat event without message: {event.id}")
            return None
        
        # Crear tarea
        task = event.to_task()
        task.task_type = "chat"
        
        return task


class WebhookEventProcessor(EventProcessor):
    """Procesador de webhooks"""
    
    def __init__(self):
        self._registered_hooks: Dict[str, Callable] = {}
    
    def register_hook(self, hook_type: str, handler: Callable):
        self._registered_hooks[hook_type] = handler
    
    async def process(self, event: Event) -> Optional[Task]:
        if event.source != EventSource.WEBHOOK:
            return None
        
        hook_type = event.payload.get("hook_type", "generic")
        
        if hook_type in self._registered_hooks:
            # Ejecutar handler específico
            handler = self._registered_hooks[hook_type]
            result = await handler(event)
            if result:
                return result
        
        # Default: crear tarea
        task = event.to_task()
        task.task_type = f"webhook.{hook_type}"
        
        return task


class ScheduledEventProcessor(EventProcessor):
    """Procesador de eventos programados"""
    
    async def process(self, event: Event) -> Optional[Task]:
        if event.source != EventSource.SCHEDULED:
            return None
        
        # Crear tarea programada
        task = event.to_task()
        task.task_type = event.event_type
        
        return task


class EventDispatcher:
    """
    Dispatcher central de eventos
    
    Características:
    - Múltiples fuentes de eventos
    - Procesadores de eventos plugables
    - Routing a colas por prioridad
    - Persistencia en Event Store
    - Integración con Assignment Engine
    """
    
    def __init__(
        self,
        stream_client: RedisStreamClient,
        event_store: Optional[EventStore] = None,
        assignment_engine: Optional[AgentAssignmentEngine] = None,
        agent_tracker: Optional[AgentAvailabilityTracker] = None,
    ):
        self.stream_client = stream_client
        self.event_store = event_store
        self.assignment_engine = assignment_engine
        self.agent_tracker = agent_tracker
        
        # Procesadores de eventos
        self._processors: List[EventProcessor] = [
            ChatEventProcessor(),
            WebhookEventProcessor(),
            ScheduledEventProcessor(),
        ]
        
        # Handlers de eventos específicos
        self._event_handlers: Dict[str, List[Callable]] = {}
        
        # Callbacks
        self._on_task_created: Optional[Callable] = None
        self._on_task_assigned: Optional[Callable] = None
    
    def add_processor(self, processor: EventProcessor) -> None:
        """Agrega un procesador de eventos"""
        self._processors.append(processor)
    
    def on_event(self, event_type: str, handler: Callable) -> None:
        """Registra un handler para un tipo de evento"""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
    
    def on_task_created(self, callback: Callable) -> None:
        """Registra callback para cuando se crea una tarea"""
        self._on_task_created = callback
    
    def on_task_assigned(self, callback: Callable) -> None:
        """Registra callback para cuando se asigna una tarea"""
        self._on_task_assigned = callback
    
    async def dispatch(self, event: Event) -> str:
        """
        Dispara un evento en el sistema
        
        Args:
            event: Evento a disparar
            
        Returns:
            ID de la tarea creada (si aplica)
        """
        logger.info(
            f"Dispatching event: {event.event_type}",
            extra={
                "event_id": event.id,
                "source": event.source.value,
                "user_id": event.user_id,
            }
        )
        
        # 1. Persistir evento
        if self.event_store:
            stored_event = StoredEvent(
                id=event.id,
                event_type=EventType.TASK_CREATED,
                aggregate_id=event.id,
                aggregate_type="event",
                tenant_id=event.tenant_id,
                user_id=event.user_id,
                session_id=event.session_id,
                payload=event.payload,
                metadata={
                    "source": event.source.value,
                    "event_type": event.event_type,
                },
                correlation_id=event.correlation_id,
            )
            await self.event_store.append(stored_event)
        
        # 2. Ejecutar handlers específicos
        handlers = self._event_handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Event handler error: {e}")
        
        # 3. Procesar evento (convertir a tarea)
        task = None
        for processor in self._processors:
            result = await processor.process(event)
            if result:
                task = result
                break
        
        if not task:
            # Crear tarea default
            task = event.to_task()
        
        # 4. Asignar agente si es posible
        if self.assignment_engine and not task.agent_id:
            assignment = await self.assignment_engine.assign(task)
            
            if assignment.success:
                task.agent_id = assignment.agent_id
                task.status = TaskStatus.ASSIGNED
                
                logger.info(
                    f"Task {task.id} assigned to agent {assignment.agent_id}",
                    extra={
                        "task_id": task.id,
                        "agent_id": assignment.agent_id,
                        "strategy": assignment.strategy_used.value
                    }
                )
                
                if self._on_task_assigned:
                    await self._on_task_assigned(task, assignment)
            else:
                logger.warning(
                    f"No agent available for task {task.id}",
                    extra={
                        "task_id": task.id,
                        "reason": assignment.reason
                    }
                )
        
        # 5. Publicar tarea en cola
        task.status = TaskStatus.QUEUED
        message_id = await self.stream_client.publish_task(task)
        
        logger.info(
            f"Task {task.id} published to queue",
            extra={
                "task_id": task.id,
                "priority": task.priority.value,
                "message_id": message_id
            }
        )
        
        if self._on_task_created:
            await self._on_task_created(task)
        
        return task.id
    
    async def dispatch_batch(self, events: List[Event]) -> List[str]:
        """Dispara múltiples eventos"""
        task_ids = []
        for event in events:
            task_id = await self.dispatch(event)
            task_ids.append(task_id)
        return task_ids
    
    async def dispatch_chat_message(
        self,
        message: str,
        user_id: str,
        session_id: str,
        tenant_id: str = "default",
        agent_id: Optional[str] = None,
        domain: Optional[str] = None,
        iovba_role: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Conveniencia: Dispara un mensaje de chat
        
        Args:
            message: Contenido del mensaje
            user_id: ID del usuario
            session_id: ID de la sesión
            tenant_id: ID del tenant
            agent_id: ID del agente (opcional)
            domain: Dominio (opcional)
            iovba_role: Rol IOVBA (opcional)
            metadata: Metadata adicional
            
        Returns:
            ID de la tarea creada
        """
        event = Event(
            source=EventSource.CHAT,
            event_type="chat.message",
            tenant_id=tenant_id,
            user_id=user_id,
            session_id=session_id,
            agent_id=agent_id,
            domain=domain,
            iovba_role=iovba_role,
            payload={
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            },
            metadata=metadata or {}
        )
        
        return await self.dispatch(event)
    
    async def dispatch_webhook(
        self,
        hook_type: str,
        payload: Dict[str, Any],
        tenant_id: str = "default",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Conveniencia: Dispara un webhook
        
        Args:
            hook_type: Tipo de webhook
            payload: Datos del webhook
            tenant_id: ID del tenant
            metadata: Metadata adicional
            
        Returns:
            ID de la tarea creada
        """
        event = Event(
            source=EventSource.WEBHOOK,
            event_type=f"webhook.{hook_type}",
            tenant_id=tenant_id,
            payload=payload,
            metadata=metadata or {}
        )
        
        return await self.dispatch(event)
    
    async def dispatch_internal(
        self,
        event_type: str,
        payload: Dict[str, Any],
        tenant_id: str = "default",
        priority: TaskPriority = TaskPriority.NORMAL
    ) -> str:
        """
        Conveniencia: Dispara un evento interno
        
        Args:
            event_type: Tipo de evento
            payload: Datos del evento
            tenant_id: ID del tenant
            priority: Prioridad de la tarea
            
        Returns:
            ID de la tarea creada
        """
        event = Event(
            source=EventSource.INTERNAL,
            event_type=event_type,
            tenant_id=tenant_id,
            priority=priority,
            payload=payload
        )
        
        return await self.dispatch(event)
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """Obtiene estado de las colas"""
        stats = await self.stream_client.get_queue_stats()
        
        if self.agent_tracker:
            agent_stats = await self.agent_tracker.get_statistics()
            stats["agents"] = agent_stats
        
        return stats
