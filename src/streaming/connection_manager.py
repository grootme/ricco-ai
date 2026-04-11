"""
Connection Manager for Streaming Service

Manages connections for SSE and WebSocket protocols including:
- Connection lifecycle management
- Heartbeat monitoring
- Reconnection handling
- Connection metrics and monitoring
- Backpressure awareness
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
)
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import uuid
import logging
import random
from collections import defaultdict

from .models import (
    ConnectionState,
    ConnectionType,
    ConnectionInfo,
    ConnectionMetrics,
    HeartbeatConfig,
    StreamConfig,
    StreamingEvent,
    StreamingEventType,
    SSEMessage,
    WebSocketMessage,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Connection Types
# ============================================================================


class ConnectionType(str, Enum):
    """Type of connection protocol"""
    SSE = "sse"
    WEBSOCKET = "websocket"


@dataclass
class HeartbeatState:
    """State of heartbeat monitoring"""
    
    last_sent: Optional[datetime] = None
    last_received: Optional[datetime] = None
    missed_count: int = 0
    pending_pong: bool = False


@dataclass
class ReconnectionState:
    """State for reconnection handling"""
    
    attempt_count: int = 0
    last_attempt: Optional[datetime] = None
    next_delay_ms: int = 0
    token: Optional[str] = None
    
    def calculate_delay(self, config: StreamConfig) -> int:
        """Calculate next reconnection delay with exponential backoff"""
        base_delay = config.reconnect_delay_ms
        max_delay = config.max_reconnect_delay_ms
        factor = config.reconnect_backoff_factor
        
        delay = base_delay * (factor ** self.attempt_count)
        delay = min(delay, max_delay)
        
        # Add jitter
        jitter = random.randint(0, 1000)
        self.next_delay_ms = int(delay) + jitter
        
        return self.next_delay_ms


# ============================================================================
# Connection Manager
# ============================================================================


class ConnectionManager:
    """
    Manages streaming connections for SSE and WebSocket.
    
    Features:
    - Connection registration and tracking
    - Heartbeat monitoring
    - Reconnection state management
    - Connection metrics collection
    - Event broadcasting
    """
    
    def __init__(
        self,
        config: Optional[StreamConfig] = None,
    ):
        """
        Initialize the connection manager.
        
        Args:
            config: Stream configuration
        """
        self._config = config or StreamConfig()
        
        # Connection storage
        self._connections: Dict[str, ConnectionInfo] = {}
        self._session_connections: Dict[str, Set[str]] = defaultdict(set)
        self._user_connections: Dict[str, Set[str]] = defaultdict(set)
        
        # Heartbeat states
        self._heartbeat_states: Dict[str, HeartbeatState] = {}
        
        # Reconnection states
        self._reconnection_states: Dict[str, ReconnectionState] = {}
        
        # Event queues for each connection
        self._event_queues: Dict[str, asyncio.Queue] = {}
        
        # Background tasks
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Callbacks
        self._on_connect_callbacks: List[Callable[[ConnectionInfo], Awaitable[None]]] = []
        self._on_disconnect_callbacks: List[Callable[[ConnectionInfo], Awaitable[None]]] = []
        self._on_reconnect_callbacks: List[Callable[[ConnectionInfo], Awaitable[None]]] = []
        
        # State
        self._running = False
        self._lock = asyncio.Lock()
    
    # ========================================================================
    # Lifecycle Management
    # ========================================================================
    
    async def start(self) -> None:
        """Start the connection manager"""
        if self._running:
            return
        
        self._running = True
        
        # Start background tasks
        if self._config.heartbeat.enabled:
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        logger.info("Connection manager started")
    
    async def stop(self) -> None:
        """Stop the connection manager"""
        self._running = False
        
        # Cancel background tasks
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Close all connections
        for conn_id in list(self._connections.keys()):
            await self.disconnect(conn_id, reason="shutdown")
        
        logger.info("Connection manager stopped")
    
    # ========================================================================
    # Connection Management
    # ========================================================================
    
    async def register(
        self,
        connection_type: ConnectionType,
        session_id: str,
        user_id: Optional[str] = None,
        client_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ConnectionInfo:
        """
        Register a new connection.
        
        Args:
            connection_type: Type of connection (SSE/WebSocket)
            session_id: Associated session ID
            user_id: Optional user ID
            client_ip: Optional client IP
            user_agent: Optional user agent
            metadata: Optional additional metadata
            
        Returns:
            ConnectionInfo for the new connection
        """
        connection_id = str(uuid.uuid4())
        
        conn_info = ConnectionInfo(
            connection_id=connection_id,
            connection_type=connection_type,
            state=ConnectionState.CONNECTING,
            session_id=session_id,
            user_id=user_id,
            client_ip=client_ip,
            user_agent=user_agent,
            metadata=metadata or {},
        )
        
        async with self._lock:
            self._connections[connection_id] = conn_info
            self._session_connections[session_id].add(connection_id)
            
            if user_id:
                self._user_connections[user_id].add(connection_id)
            
            # Create event queue
            self._event_queues[connection_id] = asyncio.Queue(
                maxsize=self._config.backpressure.max_queue_size
            )
            
            # Initialize heartbeat state
            self._heartbeat_states[connection_id] = HeartbeatState()
            
            # Initialize reconnection state
            self._reconnection_states[connection_id] = ReconnectionState(
                token=str(uuid.uuid4())
            )
        
        # Update state
        conn_info.state = ConnectionState.CONNECTED
        
        # Fire callbacks
        for callback in self._on_connect_callbacks:
            try:
                await callback(conn_info)
            except Exception as e:
                logger.error(f"Error in connect callback: {e}")
        
        logger.info(f"Connection registered: {connection_id} (session={session_id})")
        
        return conn_info
    
    async def disconnect(
        self,
        connection_id: str,
        reason: str = "client_disconnect",
    ) -> None:
        """
        Disconnect a connection.
        
        Args:
            connection_id: Connection to disconnect
            reason: Reason for disconnection
        """
        async with self._lock:
            conn_info = self._connections.get(connection_id)
            if not conn_info:
                return
            
            conn_info.state = ConnectionState.DISCONNECTED
            conn_info.metadata["disconnect_reason"] = reason
            conn_info.metadata["disconnected_at"] = datetime.utcnow().isoformat()
            
            # Remove from indexes
            session_id = conn_info.session_id
            self._session_connections[session_id].discard(connection_id)
            
            if conn_info.user_id:
                self._user_connections[conn_info.user_id].discard(connection_id)
            
            # Clean up queues
            if connection_id in self._event_queues:
                queue = self._event_queues.pop(connection_id)
                # Drain remaining events
                while not queue.empty():
                    try:
                        queue.get_nowait()
                    except asyncio.QueueEmpty:
                        break
        
        # Fire callbacks
        for callback in self._on_disconnect_callbacks:
            try:
                await callback(conn_info)
            except Exception as e:
                logger.error(f"Error in disconnect callback: {e}")
        
        logger.info(f"Connection disconnected: {connection_id} (reason={reason})")
    
    async def reconnect(
        self,
        reconnection_token: str,
        last_event_id: Optional[str] = None,
    ) -> Optional[ConnectionInfo]:
        """
        Handle reconnection using token.
        
        Args:
            reconnection_token: Token from previous connection
            last_event_id: Last event ID received
            
        Returns:
            ConnectionInfo if reconnection successful, None otherwise
        """
        async with self._lock:
            # Find connection by token
            for conn_id, reconnect_state in self._reconnection_states.items():
                if reconnect_state.token == reconnection_token:
                    conn_info = self._connections.get(conn_id)
                    if not conn_info:
                        continue
                    
                    # Check reconnection limits
                    if reconnect_state.attempt_count >= self._config.max_reconnect_attempts:
                        logger.warning(f"Max reconnection attempts reached: {conn_id}")
                        return None
                    
                    # Update state
                    conn_info.state = ConnectionState.RECONNECTING
                    conn_info.last_event_id = last_event_id
                    conn_info.metrics.reconnect_count += 1
                    reconnect_state.attempt_count += 1
                    reconnect_state.last_attempt = datetime.utcnow()
                    
                    # Reset heartbeat
                    if conn_id in self._heartbeat_states:
                        self._heartbeat_states[conn_id] = HeartbeatState()
                    
                    # Update state
                    conn_info.state = ConnectionState.CONNECTED
                    
                    # Fire callbacks
                    for callback in self._on_reconnect_callbacks:
                        try:
                            await callback(conn_info)
                        except Exception as e:
                            logger.error(f"Error in reconnect callback: {e}")
                    
                    logger.info(f"Connection reconnected: {conn_id}")
                    return conn_info
        
        return None
    
    def get_connection(self, connection_id: str) -> Optional[ConnectionInfo]:
        """Get connection info by ID"""
        return self._connections.get(connection_id)
    
    def get_session_connections(self, session_id: str) -> List[ConnectionInfo]:
        """Get all connections for a session"""
        conn_ids = self._session_connections.get(session_id, set())
        return [
            self._connections[conn_id]
            for conn_id in conn_ids
            if conn_id in self._connections
        ]
    
    def get_user_connections(self, user_id: str) -> List[ConnectionInfo]:
        """Get all connections for a user"""
        conn_ids = self._user_connections.get(user_id, set())
        return [
            self._connections[conn_id]
            for conn_id in conn_ids
            if conn_id in self._connections
        ]
    
    # ========================================================================
    # Event Handling
    # ========================================================================
    
    async def send_event(
        self,
        connection_id: str,
        event: StreamingEvent,
        priority: int = 0,
    ) -> bool:
        """
        Queue an event for a connection.
        
        Args:
            connection_id: Target connection
            event: Event to send
            priority: Event priority (higher = more important)
            
        Returns:
            True if event was queued, False if connection not found or queue full
        """
        if connection_id not in self._connections:
            return False
        
        queue = self._event_queues.get(connection_id)
        if not queue:
            return False
        
        conn_info = self._connections[connection_id]
        
        # Check backpressure
        if self._config.backpressure.enabled:
            queue_ratio = queue.qsize() / self._config.backpressure.max_queue_size
            if queue_ratio > self._config.backpressure.high_watermark:
                # Handle high water mark
                if self._config.backpressure.drop_on_overflow:
                    # Drop lower priority events
                    if priority <= 0:
                        conn_info.metrics.events_dropped += 1
                        return False
        
        try:
            queue.put_nowait((priority, event))
            conn_info.metrics.events_dispatched += 1
            conn_info.update_activity()
            return True
        except asyncio.QueueFull:
            conn_info.metrics.events_dropped += 1
            return False
    
    async def broadcast_event(
        self,
        event: StreamingEvent,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        exclude: Optional[Set[str]] = None,
    ) -> int:
        """
        Broadcast an event to multiple connections.
        
        Args:
            event: Event to broadcast
            session_id: Broadcast to session (optional)
            user_id: Broadcast to user (optional)
            exclude: Connection IDs to exclude
            
        Returns:
            Number of connections that received the event
        """
        exclude = exclude or set()
        count = 0
        
        target_ids: Set[str] = set()
        
        if session_id:
            target_ids.update(self._session_connections.get(session_id, set()))
        
        if user_id:
            target_ids.update(self._user_connections.get(user_id, set()))
        
        if not session_id and not user_id:
            target_ids = set(self._connections.keys())
        
        target_ids -= exclude
        
        for conn_id in target_ids:
            if await self.send_event(conn_id, event):
                count += 1
        
        return count
    
    async def get_events(
        self,
        connection_id: str,
        timeout: Optional[float] = None,
    ) -> AsyncGenerator[StreamingEvent, None]:
        """
        Get events for a connection.
        
        Args:
            connection_id: Connection to get events for
            timeout: Optional timeout in seconds
            
        Yields:
            StreamingEvent objects
        """
        queue = self._event_queues.get(connection_id)
        if not queue:
            return
        
        while True:
            try:
                if timeout:
                    priority, event = await asyncio.wait_for(
                        queue.get(),
                        timeout=timeout
                    )
                else:
                    priority, event = await queue.get()
                
                yield event
                
            except asyncio.TimeoutError:
                return
            except asyncio.CancelledError:
                return
            except Exception as e:
                logger.error(f"Error getting events: {e}")
                return
    
    # ========================================================================
    # Heartbeat Management
    # ========================================================================
    
    async def record_heartbeat_sent(self, connection_id: str) -> None:
        """Record that a heartbeat was sent"""
        state = self._heartbeat_states.get(connection_id)
        if state:
            state.last_sent = datetime.utcnow()
            state.pending_pong = True
    
    async def record_heartbeat_received(self, connection_id: str) -> None:
        """Record that a heartbeat response was received"""
        state = self._heartbeat_states.get(connection_id)
        if state:
            state.last_received = datetime.utcnow()
            state.pending_pong = False
            state.missed_count = 0
            
            # Update connection activity
            conn_info = self._connections.get(connection_id)
            if conn_info:
                conn_info.update_activity()
                conn_info.metrics.last_heartbeat = datetime.utcnow()
    
    async def _heartbeat_loop(self) -> None:
        """Background task for heartbeat monitoring"""
        while self._running:
            try:
                await asyncio.sleep(self._config.heartbeat.interval_ms / 1000)
                await self._check_heartbeats()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(1)
    
    async def _check_heartbeats(self) -> None:
        """Check all connections for heartbeat status"""
        now = datetime.utcnow()
        timeout = timedelta(milliseconds=self._config.heartbeat.timeout_ms)
        
        for conn_id, state in list(self._heartbeat_states.items()):
            conn_info = self._connections.get(conn_id)
            if not conn_info or conn_info.state != ConnectionState.CONNECTED:
                continue
            
            # Check for missed heartbeat
            if state.pending_pong:
                if state.last_sent and (now - state.last_sent) > timeout:
                    state.missed_count += 1
                    state.pending_pong = False
                    
                    if state.missed_count >= self._config.heartbeat.max_missed:
                        logger.warning(f"Connection timed out: {conn_id}")
                        conn_info.state = ConnectionState.TIMEOUT
                        await self.disconnect(conn_id, reason="heartbeat_timeout")
            
            # Send heartbeat if needed
            if not state.pending_pong:
                # Send heartbeat event
                event = StreamingEvent(
                    event_id=str(uuid.uuid4()),
                    event_type=StreamingEventType.HEARTBEAT,
                    session_id=conn_info.session_id,
                    data={"timestamp": now.isoformat()},
                )
                await self.send_event(conn_id, event)
                await self.record_heartbeat_sent(conn_id)
    
    # ========================================================================
    # Cleanup
    # ========================================================================
    
    async def _cleanup_loop(self) -> None:
        """Background task for connection cleanup"""
        while self._running:
            try:
                await asyncio.sleep(60)  # Check every minute
                await self._cleanup_stale_connections()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(5)
    
    async def _cleanup_stale_connections(self) -> None:
        """Remove stale connections"""
        now = datetime.utcnow()
        session_timeout = timedelta(milliseconds=self._config.session_timeout_ms)
        
        stale_ids = []
        
        async with self._lock:
            for conn_id, conn_info in list(self._connections.items()):
                # Check for timed out sessions
                if conn_info.state == ConnectionState.DISCONNECTED:
                    stale_ids.append(conn_id)
                    continue
                
                # Check for inactive connections
                inactive_time = now - conn_info.last_activity
                if inactive_time > session_timeout:
                    stale_ids.append(conn_id)
        
        # Clean up stale connections
        for conn_id in stale_ids:
            logger.info(f"Cleaning up stale connection: {conn_id}")
            await self.disconnect(conn_id, reason="timeout")
    
    # ========================================================================
    # Callbacks
    # ========================================================================
    
    def on_connect(self, callback: Callable[[ConnectionInfo], Awaitable[None]]) -> None:
        """Register a callback for new connections"""
        self._on_connect_callbacks.append(callback)
    
    def on_disconnect(self, callback: Callable[[ConnectionInfo], Awaitable[None]]) -> None:
        """Register a callback for disconnections"""
        self._on_disconnect_callbacks.append(callback)
    
    def on_reconnect(self, callback: Callable[[ConnectionInfo], Awaitable[None]]) -> None:
        """Register a callback for reconnections"""
        self._on_reconnect_callbacks.append(callback)
    
    # ========================================================================
    # Metrics
    # ========================================================================
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get connection manager metrics"""
        total_connections = len(self._connections)
        active_connections = sum(
            1 for c in self._connections.values()
            if c.state == ConnectionState.CONNECTED
        )
        
        total_events_dispatched = sum(
            c.metrics.events_dispatched
            for c in self._connections.values()
        )
        
        total_events_dropped = sum(
            c.metrics.events_dropped
            for c in self._connections.values()
        )
        
        return {
            "total_connections": total_connections,
            "active_connections": active_connections,
            "sessions": len(self._session_connections),
            "users": len(self._user_connections),
            "events_dispatched": total_events_dispatched,
            "events_dropped": total_events_dropped,
        }
    
    def get_connection_metrics(self, connection_id: str) -> Optional[ConnectionMetrics]:
        """Get metrics for a specific connection"""
        conn_info = self._connections.get(connection_id)
        if conn_info:
            return conn_info.metrics
        return None


# ============================================================================
# Global Instance
# ============================================================================

_connection_manager: Optional[ConnectionManager] = None


def get_connection_manager(config: Optional[StreamConfig] = None) -> ConnectionManager:
    """Get the global connection manager instance"""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager(config)
    return _connection_manager
