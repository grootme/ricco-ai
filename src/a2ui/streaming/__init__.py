"""
A2UI Streaming Module for RICCO AI.

Provides SSE and WebSocket handlers for streaming UI generation.
"""

from typing import Any, Dict, Optional, AsyncIterator
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import asyncio
import logging

logger = logging.getLogger(__name__)


class StreamingEventType(str, Enum):
    """Types of streaming events."""
    START = "start"
    TOKEN = "token"
    COMPONENT = "component"
    PROGRESS = "progress"
    ERROR = "error"
    COMPLETE = "complete"


class StreamingEvent(BaseModel):
    """Event for streaming UI generation."""
    event_type: StreamingEventType
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    sequence: int = 0


class SSEHandler:
    """
    Server-Sent Events handler for one-way streaming.
    
    Provides simple streaming from server to client.
    """
    
    def __init__(self):
        self._connections: Dict[str, asyncio.Queue] = {}
        self._event_counter = 0
    
    async def connect(self, connection_id: str) -> None:
        """Register a new SSE connection."""
        self._connections[connection_id] = asyncio.Queue()
        logger.debug(f"SSE connection established: {connection_id}")
    
    async def disconnect(self, connection_id: str) -> None:
        """Remove an SSE connection."""
        queue = self._connections.pop(connection_id, None)
        if queue:
            # Signal end of stream
            await queue.put(None)
        logger.debug(f"SSE connection closed: {connection_id}")
    
    async def send_event(
        self,
        connection_id: str,
        event: StreamingEvent,
    ) -> bool:
        """Send an event to a connection."""
        queue = self._connections.get(connection_id)
        if not queue:
            return False
        
        self._event_counter += 1
        event.sequence = self._event_counter
        await queue.put(event)
        return True
    
    async def stream(
        self,
        connection_id: str,
    ) -> AsyncIterator[str]:
        """Stream events as SSE format."""
        queue = self._connections.get(connection_id)
        if not queue:
            return
        
        while True:
            event = await queue.get()
            if event is None:
                break
            
            # Format as SSE
            yield f"event: {event.event_type.value}\n"
            yield f"data: {event.model_dump_json()}\n\n"
    
    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self._connections)


class WebSocketHandler:
    """
    WebSocket handler for bidirectional streaming.
    
    Features:
    - Real-time bidirectional communication
    - Pause/resume support
    - Message acknowledgment
    """
    
    def __init__(self):
        self._connections: Dict[str, Dict[str, Any]] = {}
        self._paused: Dict[str, bool] = {}
        self._message_queues: Dict[str, asyncio.Queue] = {}
    
    async def connect(self, connection_id: str) -> None:
        """Register a new WebSocket connection."""
        self._connections[connection_id] = {
            "connected_at": datetime.utcnow(),
            "messages_sent": 0,
            "messages_received": 0,
        }
        self._message_queues[connection_id] = asyncio.Queue()
        self._paused[connection_id] = False
        logger.debug(f"WebSocket connection established: {connection_id}")
    
    async def disconnect(self, connection_id: str) -> None:
        """Remove a WebSocket connection."""
        self._connections.pop(connection_id, None)
        self._message_queues.pop(connection_id, None)
        self._paused.pop(connection_id, None)
        logger.debug(f"WebSocket connection closed: {connection_id}")
    
    async def send_message(
        self,
        connection_id: str,
        event: StreamingEvent,
    ) -> bool:
        """Send a message to a connection."""
        if connection_id not in self._connections:
            return False
        
        if self._paused.get(connection_id, False):
            # Queue message for later
            queue = self._message_queues.get(connection_id)
            if queue:
                await queue.put(event)
            return True
        
        conn = self._connections[connection_id]
        conn["messages_sent"] += 1
        return True
    
    async def receive_message(
        self,
        connection_id: str,
        message: Dict[str, Any],
    ) -> None:
        """Handle a received message from client."""
        if connection_id not in self._connections:
            return
        
        conn = self._connections[connection_id]
        conn["messages_received"] += 1
        
        # Handle control messages
        msg_type = message.get("type")
        if msg_type == "pause":
            self._paused[connection_id] = True
        elif msg_type == "resume":
            self._paused[connection_id] = False
            # Send queued messages
            queue = self._message_queues.get(connection_id)
            if queue:
                while not queue.empty():
                    event = await queue.get()
                    await self.send_message(connection_id, event)
    
    def pause(self, connection_id: str) -> None:
        """Pause streaming for a connection."""
        self._paused[connection_id] = True
    
    def resume(self, connection_id: str) -> None:
        """Resume streaming for a connection."""
        self._paused[connection_id] = False
    
    def get_connection_stats(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a connection."""
        conn = self._connections.get(connection_id)
        if not conn:
            return None
        
        return {
            **conn,
            "paused": self._paused.get(connection_id, False),
            "queued_messages": self._message_queues.get(connection_id, asyncio.Queue()).qsize(),
        }
    
    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self._connections)


class IncrementalJSONParser:
    """
    Parser for incremental JSON parsing during streaming.
    
    Enables progressive rendering of UI components as they are generated.
    """
    
    def __init__(self):
        self._buffer = ""
        self._depth = 0
        self._in_string = False
        self._escape_next = False
        self._complete_objects: list = []
    
    def feed(self, chunk: str) -> list:
        """
        Feed a chunk of JSON text to the parser.
        
        Returns list of complete JSON objects found.
        """
        self._buffer += chunk
        objects = []
        
        start_idx = 0
        for i, char in enumerate(chunk):
            if self._escape_next:
                self._escape_next = False
                continue
            
            if char == '\\' and self._in_string:
                self._escape_next = True
                continue
            
            if char == '"' and not self._escape_next:
                self._in_string = not self._in_string
                continue
            
            if self._in_string:
                continue
            
            if char == '{':
                if self._depth == 0:
                    start_idx = i
                self._depth += 1
            elif char == '}':
                self._depth -= 1
                if self._depth == 0:
                    # Complete object found
                    obj_str = self._buffer[start_idx:i+1]
                    try:
                        import json
                        obj = json.loads(obj_str)
                        objects.append(obj)
                    except json.JSONDecodeError:
                        pass
        
        return objects
    
    def reset(self) -> None:
        """Reset the parser state."""
        self._buffer = ""
        self._depth = 0
        self._in_string = False
        self._escape_next = False
        self._complete_objects = []
