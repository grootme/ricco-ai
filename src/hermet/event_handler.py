"""
Event Handler for Hermet Agent

Processes events from various sources and routes them to appropriate handlers.
"""

import asyncio
import time
from collections import deque
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
import uuid


class EventType(str, Enum):
    """Types of events Hermet can process"""
    # System events
    SYSTEM_ALERT = "system_alert"
    HEALTH_CHECK = "health_check"
    THRESHOLD_BREACH = "threshold_breach"
    
    # Agent events
    AGENT_STARTED = "agent_started"
    AGENT_STOPPED = "agent_stopped"
    AGENT_ERROR = "agent_error"
    AGENT_SUCCESS = "agent_success"
    
    # MCP events
    MCP_SERVER_UP = "mcp_server_up"
    MCP_SERVER_DOWN = "mcp_server_down"
    MCP_TOOL_CALLED = "mcp_tool_called"
    MCP_ERROR = "mcp_error"
    
    # LLM events
    LLM_REQUEST = "llm_request"
    LLM_RESPONSE = "llm_response"
    LLM_ERROR = "llm_error"
    LLM_RATE_LIMIT = "llm_rate_limit"
    
    # Database events
    DB_SLOW_QUERY = "db_slow_query"
    DB_ERROR = "db_error"
    DB_CONNECTION_LOST = "db_connection_lost"
    
    # HTTP events
    HTTP_ERROR = "http_error"
    HTTP_SLOW_REQUEST = "http_slow_request"
    HTTP_RATE_LIMIT = "http_rate_limit"
    
    # Queue events
    QUEUE_OVERFLOW = "queue_overflow"
    QUEUE_STUCK = "queue_stuck"
    
    # Custom events
    CUSTOM = "custom"


@dataclass
class Event:
    """Event data structure"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: EventType = EventType.CUSTOM
    source: str = "unknown"
    timestamp: float = field(default_factory=time.time)
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    processed: bool = False
    priority: int = 0  # Higher = more important
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "source": self.source,
            "timestamp": self.timestamp,
            "data": self.data,
            "metadata": self.metadata,
            "processed": self.processed,
            "priority": self.priority,
        }


class EventHandler:
    """
    Event handler for processing and routing events
    
    Features:
    - Event queue with priority
    - Event filtering
    - Event routing to subscribers
    - Event aggregation
    """
    
    def __init__(
        self,
        max_queue_size: int = 10000,
        batch_size: int = 100,
    ):
        self.max_queue_size = max_queue_size
        self.batch_size = batch_size
        
        self.logger = logging.getLogger("hermet.event_handler")
        
        # Event queues
        self._queue: deque = deque(maxlen=max_queue_size)
        self._priority_queue: deque = deque(maxlen=1000)
        
        # Subscribers
        self._subscribers: Dict[str, List[Callable]] = {}
        
        # Event filters
        self._filters: List[Callable] = []
        
        # Event history
        self._history: deque = deque(maxlen=1000)
        
        # Statistics
        self._events_processed = 0
        self._events_dropped = 0
        self._initialized = False
    
    async def initialize(self):
        """Initialize the event handler"""
        self._initialized = True
        self.logger.info("Event handler initialized")
    
    async def emit(
        self,
        event_data: Dict[str, Any],
        event_type: Optional[EventType] = None,
        source: Optional[str] = None,
        priority: int = 0,
    ) -> Event:
        """Emit a new event"""
        if not self._initialized:
            await self.initialize()
        
        # Create event
        event = Event(
            type=event_type or EventType(event_data.get("type", "custom")),
            source=source or event_data.get("source", "unknown"),
            data=event_data.get("data", event_data),
            metadata=event_data.get("metadata", {}),
            priority=priority,
        )
        
        # Apply filters
        for filter_func in self._filters:
            try:
                if not filter_func(event):
                    self._events_dropped += 1
                    return event
            except Exception as e:
                self.logger.error(f"Error in event filter: {e}")
        
        # Add to queue
        if priority > 0:
            self._priority_queue.append(event)
        else:
            self._queue.append(event)
        
        # Add to history
        self._history.append(event)
        
        return event
    
    async def process_batch(self) -> List[Event]:
        """Process a batch of events"""
        if not self._initialized:
            await self.initialize()
        
        events = []
        
        # Process priority events first
        while len(events) < self.batch_size and self._priority_queue:
            event = self._priority_queue.popleft()
            event.processed = True
            events.append(event)
            self._events_processed += 1
        
        # Then process regular events
        while len(events) < self.batch_size and self._queue:
            event = self._queue.popleft()
            event.processed = True
            events.append(event)
            self._events_processed += 1
        
        # Notify subscribers for each event
        for event in events:
            await self._notify_subscribers(event)
        
        return events
    
    async def _notify_subscribers(self, event: Event):
        """Notify all subscribers of an event"""
        # Notify by event type
        type_subscribers = self._subscribers.get(event.type.value, [])
        for callback in type_subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                self.logger.error(f"Error in subscriber callback: {e}")
        
        # Notify wildcard subscribers
        wildcard_subscribers = self._subscribers.get("*", [])
        for callback in wildcard_subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                self.logger.error(f"Error in wildcard subscriber callback: {e}")
    
    def subscribe(
        self,
        event_type: str,
        callback: Callable,
    ):
        """Subscribe to events of a specific type"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
        self.logger.info(f"Subscribed to {event_type} events")
    
    def unsubscribe(
        self,
        event_type: str,
        callback: Callable,
    ):
        """Unsubscribe from events"""
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(callback)
            except ValueError:
                pass
    
    def add_filter(self, filter_func: Callable):
        """Add an event filter"""
        self._filters.append(filter_func)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event handler statistics"""
        return {
            "events_processed": self._events_processed,
            "events_dropped": self._events_dropped,
            "queue_size": len(self._queue),
            "priority_queue_size": len(self._priority_queue),
            "history_size": len(self._history),
            "subscriber_count": sum(len(s) for s in self._subscribers.values()),
        }
    
    def get_history(
        self,
        event_type: Optional[EventType] = None,
        limit: int = 100,
    ) -> List[Event]:
        """Get event history"""
        history = list(self._history)
        
        if event_type:
            history = [e for e in history if e.type == event_type]
        
        return history[-limit:]
    
    def clear_queue(self):
        """Clear the event queue"""
        self._queue.clear()
        self._priority_queue.clear()
        self.logger.info("Event queue cleared")
