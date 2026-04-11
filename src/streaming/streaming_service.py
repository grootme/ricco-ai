"""
Streaming Service for A2UI

Main service that coordinates streaming operations including:
- SSE (Server-Sent Events) streaming
- WebSocket streaming
- Integration with ConnectionManager and ComponentStreamer
- LLM token streaming and component generation
"""

from typing import (
    Any,
    Dict,
    List,
    Optional,
    Set,
    Callable,
    Awaitable,
    AsyncGenerator,
    Union,
)
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import uuid
import json
import logging

from .models import (
    StreamingEvent,
    StreamingEventType,
    ComponentEvent,
    ComponentEventType,
    StreamState,
    ConnectionState,
    StreamConfig,
    BackpressureConfig,
    SSEMessage,
    WebSocketMessage,
    ParsedComponent,
    StreamStartResponse,
    StreamStatusResponse,
    ConnectionType,
    RenderTarget,
    StreamingSession as StreamSessionModel,
    ConnectionMetrics,
)

from .connection_manager import (
    ConnectionManager,
    ConnectionInfo,
    get_connection_manager,
)

from .component_streamer import (
    ComponentStreamer,
    StreamPriority,
    StreamSession,
    get_component_streamer,
)

from .incremental_parser import (
    IncrementalJSONParser,
    PartialJSONResult,
    create_parser,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Enums
# ============================================================================


class StreamProtocol(str, Enum):
    """Streaming protocol type"""
    SSE = "sse"
    WEBSOCKET = "websocket"
    BOTH = "both"


# ============================================================================
# Streaming Session Model
# ============================================================================


@dataclass
class StreamingSession:
    """
    Complete streaming session state.
    
    Combines connection info with streaming state.
    """
    
    session_id: str
    connection_id: str
    surface_id: str
    user_id: Optional[str] = None
    protocol: StreamProtocol = StreamProtocol.SSE
    state: StreamState = StreamState.IDLE
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    config: StreamConfig = field(default_factory=StreamConfig)
    
    # Streaming state
    event_sequence: int = 0
    last_event_id: Optional[str] = None
    data_model: Dict[str, Any] = field(default_factory=dict)
    
    # LLM state
    llm_streaming: bool = False
    current_query: Optional[str] = None
    tokens_received: int = 0
    
    # Metrics
    components_sent: int = 0
    events_sent: int = 0
    bytes_sent: int = 0
    
    # References
    connection_info: Optional[ConnectionInfo] = None
    component_session: Optional[StreamSession] = None
    
    def update_activity(self) -> None:
        """Update last activity timestamp"""
        self.last_activity = datetime.utcnow()
    
    def next_event_id(self) -> str:
        """Generate next event ID"""
        self.event_sequence += 1
        self.last_event_id = f"{self.session_id}:{self.event_sequence}"
        return self.last_event_id


# ============================================================================
# Streaming Service
# ============================================================================


class StreamingService:
    """
    Main streaming service for A2UI.
    
    Coordinates:
    - Connection management (SSE/WebSocket)
    - Component streaming
    - LLM token processing
    - Event dispatching
    """
    
    def __init__(
        self,
        config: Optional[StreamConfig] = None,
        protocol: StreamProtocol = StreamProtocol.BOTH,
    ):
        """
        Initialize the streaming service.
        
        Args:
            config: Stream configuration
            protocol: Supported protocols
        """
        self._config = config or StreamConfig()
        self._protocol = protocol
        
        # Sub-managers
        self._connection_manager = ConnectionManager(self._config)
        self._component_streamer = ComponentStreamer(
            backpressure_config=self._config.backpressure
        )
        
        # Sessions
        self._sessions: Dict[str, StreamingSession] = {}
        
        # LLM provider (set externally)
        self._llm_provider: Optional[Callable] = None
        
        # Callbacks
        self._on_session_start: Optional[Callable[[StreamingSession], Awaitable[None]]] = None
        self._on_session_end: Optional[Callable[[StreamingSession], Awaitable[None]]] = None
        self._on_component: Optional[Callable[[StreamingSession, ComponentEvent], Awaitable[None]]] = None
        
        # State
        self._running = False
    
    # ========================================================================
    # Lifecycle
    # ========================================================================
    
    async def start(self) -> None:
        """Start the streaming service"""
        if self._running:
            return
        
        self._running = True
        
        # Start sub-managers
        await self._connection_manager.start()
        await self._component_streamer.start()
        
        # Register connection callbacks
        self._connection_manager.on_connect(self._on_connection_connect)
        self._connection_manager.on_disconnect(self._on_connection_disconnect)
        self._connection_manager.on_reconnect(self._on_connection_reconnect)
        
        # Register component callbacks
        self._component_streamer.on_component_ready(self._on_component_ready)
        self._component_streamer.on_backpressure(self._on_backpressure_change)
        
        logger.info("Streaming service started")
    
    async def stop(self) -> None:
        """Stop the streaming service"""
        self._running = False
        
        # Stop sub-managers
        await self._connection_manager.stop()
        await self._component_streamer.stop()
        
        # Clear sessions
        self._sessions.clear()
        
        logger.info("Streaming service stopped")
    
    # ========================================================================
    # Session Management
    # ========================================================================
    
    async def create_session(
        self,
        protocol: StreamProtocol,
        surface_id: str,
        user_id: Optional[str] = None,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        initial_data_model: Optional[Dict[str, Any]] = None,
        render_target: RenderTarget = RenderTarget.WEB,
    ) -> StreamingSession:
        """
        Create a new streaming session.
        
        Args:
            protocol: Streaming protocol
            surface_id: A2UI surface ID
            user_id: Optional user ID
            client_ip: Optional client IP
            user_agent: Optional user agent
            initial_data_model: Initial data model
            render_target: Target rendering platform
            
        Returns:
            New StreamingSession
        """
        session_id = str(uuid.uuid4())
        
        # Create connection
        conn_type = (
            ConnectionType.SSE
            if protocol == StreamProtocol.SSE
            else ConnectionType.WEBSOCKET
        )
        
        conn_info = await self._connection_manager.register(
            connection_type=conn_type,
            session_id=session_id,
            user_id=user_id,
            client_ip=client_ip,
            user_agent=user_agent,
            metadata={"surface_id": surface_id},
        )
        
        # Create component session
        comp_session = await self._component_streamer.create_session(
            surface_id=surface_id,
            user_id=user_id,
            render_target=render_target,
            initial_data_model=initial_data_model,
        )
        
        # Create streaming session
        session = StreamingSession(
            session_id=session_id,
            connection_id=conn_info.connection_id,
            surface_id=surface_id,
            user_id=user_id,
            protocol=protocol,
            config=self._config,
            data_model=initial_data_model or {},
            connection_info=conn_info,
            component_session=comp_session,
        )
        
        self._sessions[session_id] = session
        
        # Fire callback
        if self._on_session_start:
            await self._on_session_start(session)
        
        logger.info(f"Created streaming session: {session_id}")
        
        return session
    
    async def get_session(self, session_id: str) -> Optional[StreamingSession]:
        """Get a streaming session"""
        return self._sessions.get(session_id)
    
    async def close_session(self, session_id: str) -> None:
        """Close a streaming session"""
        session = self._sessions.pop(session_id, None)
        if not session:
            return
        
        # Close component session
        if session.component_session:
            await self._component_streamer.close_session(
                session.component_session.session_id
            )
        
        # Disconnect
        await self._connection_manager.disconnect(
            session.connection_id,
            reason="session_closed"
        )
        
        session.state = StreamState.COMPLETED
        
        # Fire callback
        if self._on_session_end:
            await self._on_session_end(session)
        
        logger.info(f"Closed streaming session: {session_id}")
    
    # ========================================================================
    # SSE Streaming
    # ========================================================================
    
    async def create_sse_stream(
        self,
        surface_id: str,
        user_id: Optional[str] = None,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        last_event_id: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Create an SSE stream for a new session.
        
        Args:
            surface_id: A2UI surface ID
            user_id: Optional user ID
            client_ip: Optional client IP
            user_agent: Optional user agent
            last_event_id: Last event ID for reconnection
            
        Yields:
            SSE formatted strings
        """
        # Create session
        session = await self.create_session(
            protocol=StreamProtocol.SSE,
            surface_id=surface_id,
            user_id=user_id,
            client_ip=client_ip,
            user_agent=user_agent,
        )
        
        session.state = StreamState.ACTIVE
        
        # Send initial event
        yield self._format_sse_event(
            session,
            StreamingEventType.STREAM_START,
            {
                "session_id": session.session_id,
                "surface_id": surface_id,
                "config": self._config.model_dump(),
            }
        )
        
        try:
            # Stream events
            async for event in self._connection_manager.get_events(
                session.connection_id,
                timeout=self._config.heartbeat.interval_ms / 1000,
            ):
                session.update_activity()
                
                # Format and yield
                sse_data = self._format_sse_event(session, event.event_type, event.data)
                yield sse_data
                
                session.events_sent += 1
                session.bytes_sent += len(sse_data)
                
        except asyncio.CancelledError:
            logger.info(f"SSE stream cancelled: {session.session_id}")
        finally:
            # Send end event
            yield self._format_sse_event(
                session,
                StreamingEventType.STREAM_END,
                {"session_id": session.session_id}
            )
            
            await self.close_session(session.session_id)
    
    def _format_sse_event(
        self,
        session: StreamingSession,
        event_type: StreamingEventType,
        data: Dict[str, Any],
    ) -> str:
        """Format an event as SSE"""
        event_id = session.next_event_id()
        
        message = SSEMessage(
            id=event_id,
            event=event_type.value,
            data=json.dumps(data),
        )
        
        return message.to_sse_format()
    
    # ========================================================================
    # WebSocket Streaming
    # ========================================================================
    
    async def handle_websocket(
        self,
        websocket: Any,
        surface_id: str,
        user_id: Optional[str] = None,
        client_ip: Optional[str] = None,
    ) -> None:
        """
        Handle a WebSocket connection.
        
        Args:
            websocket: WebSocket connection object
            surface_id: A2UI surface ID
            user_id: Optional user ID
            client_ip: Optional client IP
        """
        # Create session
        session = await self.create_session(
            protocol=StreamProtocol.WEBSOCKET,
            surface_id=surface_id,
            user_id=user_id,
            client_ip=client_ip,
        )
        
        session.state = StreamState.ACTIVE
        
        try:
            # Send initial message
            await websocket.send_json({
                "type": StreamingEventType.STREAM_START.value,
                "payload": {
                    "session_id": session.session_id,
                    "surface_id": surface_id,
                },
                "timestamp": datetime.utcnow().isoformat(),
            })
            
            # Create receive and send tasks
            receive_task = asyncio.create_task(
                self._ws_receive_loop(websocket, session)
            )
            send_task = asyncio.create_task(
                self._ws_send_loop(websocket, session)
            )
            
            # Wait for either to complete
            done, pending = await asyncio.wait(
                [receive_task, send_task],
                return_when=asyncio.FIRST_COMPLETED,
            )
            
            # Cancel pending tasks
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            # Send end message
            try:
                await websocket.send_json({
                    "type": StreamingEventType.STREAM_END.value,
                    "payload": {"session_id": session.session_id},
                    "timestamp": datetime.utcnow().isoformat(),
                })
            except Exception:
                pass
            
            await self.close_session(session.session_id)
    
    async def _ws_receive_loop(
        self,
        websocket: Any,
        session: StreamingSession,
    ) -> None:
        """Handle incoming WebSocket messages"""
        while self._running and session.state == StreamState.ACTIVE:
            try:
                message = await websocket.receive_json()
                await self._handle_ws_message(websocket, session, message)
                session.update_activity()
            except Exception as e:
                logger.error(f"WebSocket receive error: {e}")
                break
    
    async def _ws_send_loop(
        self,
        websocket: Any,
        session: StreamingSession,
    ) -> None:
        """Handle outgoing WebSocket messages"""
        while self._running and session.state == StreamState.ACTIVE:
            try:
                async for event in self._connection_manager.get_events(
                    session.connection_id,
                    timeout=1.0,
                ):
                    message = WebSocketMessage(
                        type=event.event_type,
                        payload=event.data,
                        correlation_id=event.event_id,
                    )
                    await websocket.send_json(message.model_dump())
                    session.events_sent += 1
                    
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"WebSocket send error: {e}")
                break
    
    async def _handle_ws_message(
        self,
        websocket: Any,
        session: StreamingSession,
        message: Dict[str, Any],
    ) -> None:
        """Handle a WebSocket message"""
        msg_type = message.get("type")
        payload = message.get("payload", {})
        
        if msg_type == "ping":
            await websocket.send_json({
                "type": "pong",
                "timestamp": datetime.utcnow().isoformat(),
            })
        
        elif msg_type == "query":
            # Start LLM streaming
            query = payload.get("query")
            if query:
                await self._start_llm_stream(session, query)
        
        elif msg_type == "cancel":
            # Cancel current operation
            session.state = StreamState.CANCELLED
        
        elif msg_type == StreamingEventType.HEARTBEAT.value:
            await self._connection_manager.record_heartbeat_received(
                session.connection_id
            )
    
    # ========================================================================
    # LLM Integration
    # ========================================================================
    
    def set_llm_provider(
        self,
        provider: Callable[[str, Dict[str, Any]], AsyncGenerator[str, None]],
    ) -> None:
        """
        Set the LLM provider for streaming.
        
        Args:
            provider: Async generator function that yields tokens
        """
        self._llm_provider = provider
    
    async def _start_llm_stream(
        self,
        session: StreamingSession,
        query: str,
    ) -> None:
        """
        Start streaming from LLM.
        
        Args:
            session: Streaming session
            query: User query
        """
        if not self._llm_provider:
            logger.warning("No LLM provider configured")
            return
        
        session.current_query = query
        session.llm_streaming = True
        
        try:
            # Stream tokens from LLM
            async for tokens in self._llm_provider(query, session.data_model):
                session.tokens_received += len(tokens)
                
                # Feed to component streamer
                events = await self._component_streamer.feed_tokens(
                    session.component_session.session_id,
                    tokens,
                )
                
                # Send events
                for event in events:
                    await self._send_component_event(session, event)
            
            # Finalize
            final_events = await self._component_streamer.finalize_session(
                session.component_session.session_id
            )
            
            for event in final_events:
                await self._send_component_event(session, event)
            
        except Exception as e:
            logger.error(f"LLM stream error: {e}")
            
            await self._send_event(
                session,
                StreamingEventType.STREAM_ERROR,
                {"error": str(e)},
            )
        
        finally:
            session.llm_streaming = False
            session.current_query = None
    
    async def stream_llm_to_session(
        self,
        session_id: str,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Stream LLM output to an existing session.
        
        Args:
            session_id: Target session ID
            query: User query
            context: Optional context
        """
        session = self._sessions.get(session_id)
        if not session:
            logger.warning(f"Session not found: {session_id}")
            return
        
        if context:
            session.data_model.update(context)
        
        await self._start_llm_stream(session, query)
    
    # ========================================================================
    # Event Dispatching
    # ========================================================================
    
    async def _send_event(
        self,
        session: StreamingSession,
        event_type: StreamingEventType,
        data: Dict[str, Any],
    ) -> None:
        """Send an event to a session"""
        event = StreamingEvent(
            event_id=session.next_event_id(),
            event_type=event_type,
            session_id=session.session_id,
            data=data,
        )
        
        await self._connection_manager.send_event(
            session.connection_id,
            event,
        )
    
    async def _send_component_event(
        self,
        session: StreamingSession,
        component_event: ComponentEvent,
    ) -> None:
        """Send a component event"""
        event = StreamingEvent(
            event_id=session.next_event_id(),
            event_type=StreamingEventType.COMPONENT,
            session_id=session.session_id,
            data={
                "version": component_event.version,
                component_event.event_type.value: component_event.payload,
            },
        )
        
        await self._connection_manager.send_event(
            session.connection_id,
            event,
        )
        
        session.components_sent += 1
    
    async def broadcast_to_surface(
        self,
        surface_id: str,
        event_type: StreamingEventType,
        data: Dict[str, Any],
        exclude: Optional[Set[str]] = None,
    ) -> int:
        """
        Broadcast an event to all sessions on a surface.
        
        Args:
            surface_id: Target surface
            event_type: Event type
            data: Event data
            exclude: Session IDs to exclude
            
        Returns:
            Number of sessions reached
        """
        event = StreamingEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            session_id="",  # Broadcast
            data=data,
        )
        
        # Find sessions for surface
        target_sessions = [
            s for s in self._sessions.values()
            if s.surface_id == surface_id and s.session_id not in (exclude or set())
        ]
        
        count = 0
        for session in target_sessions:
            if await self._connection_manager.send_event(
                session.connection_id,
                event,
            ):
                count += 1
        
        return count
    
    # ========================================================================
    # Callbacks
    # ========================================================================
    
    async def _on_connection_connect(self, conn_info: ConnectionInfo) -> None:
        """Handle new connection"""
        logger.debug(f"Connection established: {conn_info.connection_id}")
    
    async def _on_connection_disconnect(self, conn_info: ConnectionInfo) -> None:
        """Handle disconnection"""
        logger.debug(f"Connection disconnected: {conn_info.connection_id}")
        
        # Find and close associated session
        session = next(
            (s for s in self._sessions.values() if s.connection_id == conn_info.connection_id),
            None
        )
        if session:
            await self.close_session(session.session_id)
    
    async def _on_connection_reconnect(self, conn_info: ConnectionInfo) -> None:
        """Handle reconnection"""
        logger.info(f"Connection reconnected: {conn_info.connection_id}")
    
    async def _on_component_ready(
        self,
        component_session_id: str,
        component_event: ComponentEvent,
    ) -> None:
        """Handle component ready from streamer"""
        # Find associated streaming session
        session = next(
            (s for s in self._sessions.values()
             if s.component_session and s.component_session.session_id == component_session_id),
            None
        )
        
        if session:
            await self._send_component_event(session, component_event)
            
            if self._on_component:
                await self._on_component(session, component_event)
    
    async def _on_backpressure_change(
        self,
        component_session_id: str,
        is_active: bool,
    ) -> None:
        """Handle backpressure state change"""
        session = next(
            (s for s in self._sessions.values()
             if s.component_session and s.component_session.session_id == component_session_id),
            None
        )
        
        if session:
            await self._send_event(
                session,
                StreamingEventType.BACKPRESSURE,
                {"active": is_active},
            )
    
    # ========================================================================
    # Status and Metrics
    # ========================================================================
    
    async def get_status(self, session_id: str) -> Optional[StreamStatusResponse]:
        """Get status for a session"""
        session = self._sessions.get(session_id)
        if not session:
            return None
        
        conn_metrics = self._connection_manager.get_connection_metrics(
            session.connection_id
        )
        
        return StreamStatusResponse(
            session_id=session.session_id,
            state=session.state,
            uptime_seconds=(datetime.utcnow() - session.created_at).total_seconds(),
            events_dispatched=session.events_sent,
            components_rendered=session.components_sent,
            pending_events=0,  # TODO: Get from queue
            metrics=conn_metrics or ConnectionMetrics(),
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get overall service metrics"""
        return {
            "running": self._running,
            "active_sessions": len(self._sessions),
            "connection_metrics": self._connection_manager.get_metrics(),
            "streamer_metrics": self._component_streamer.get_metrics(),
        }
    
    # ========================================================================
    # Public Callback Registration
    # ========================================================================
    
    def on_session_start(
        self,
        callback: Callable[[StreamingSession], Awaitable[None]],
    ) -> None:
        """Register session start callback"""
        self._on_session_start = callback
    
    def on_session_end(
        self,
        callback: Callable[[StreamingSession], Awaitable[None]],
    ) -> None:
        """Register session end callback"""
        self._on_session_end = callback
    
    def on_component(
        self,
        callback: Callable[[StreamingSession, ComponentEvent], Awaitable[None]],
    ) -> None:
        """Register component event callback"""
        self._on_component = callback


# ============================================================================
# Global Instance
# ============================================================================

_streaming_service: Optional[StreamingService] = None


def get_streaming_service(
    config: Optional[StreamConfig] = None,
    protocol: StreamProtocol = StreamProtocol.BOTH,
) -> StreamingService:
    """Get the global streaming service instance"""
    global _streaming_service
    if _streaming_service is None:
        _streaming_service = StreamingService(config, protocol)
    return _streaming_service
