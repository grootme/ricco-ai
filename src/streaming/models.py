"""
Pydantic Models for Streaming Events

Defines all data models for the A2UI Streaming Service including:
- Streaming events (SSE and WebSocket)
- Component events for incremental rendering
- Connection state and metrics
- Backpressure and flow control configurations
- AST cache entries for compiled components
"""

from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union,
    Literal,
    Set,
    Callable,
    Awaitable,
)
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator, ConfigDict
import hashlib
import json


# ============================================================================
# Enums
# ============================================================================


class StreamingEventType(str, Enum):
    """Types of streaming events"""
    
    # Connection events
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    HEARTBEAT = "heartbeat"
    RECONNECTING = "reconnecting"
    
    # Stream lifecycle events
    STREAM_START = "stream_start"
    STREAM_END = "stream_end"
    STREAM_ERROR = "stream_error"
    STREAM_PAUSE = "stream_pause"
    STREAM_RESUME = "stream_resume"
    
    # Data events
    TOKEN = "token"
    PARTIAL_JSON = "partial_json"
    COMPONENT = "component"
    COMPONENTS_BATCH = "components_batch"
    DATA_MODEL_UPDATE = "data_model_update"
    
    # Control events
    BACKPRESSURE = "backpressure"
    FLOW_CONTROL = "flow_control"
    ACK = "ack"
    NACK = "nack"


class ComponentEventType(str, Enum):
    """Types of component events in A2UI"""
    
    CREATE_SURFACE = "createSurface"
    UPDATE_COMPONENTS = "updateComponents"
    UPDATE_DATA_MODEL = "updateDataModel"
    UPDATE_THEME = "updateTheme"
    DELETE_COMPONENTS = "deleteComponents"
    EXECUTE_ACTION = "executeAction"
    NAVIGATE = "navigate"
    SHOW_DIALOG = "showDialog"
    SHOW_TOAST = "showToast"


class StreamState(str, Enum):
    """State of a streaming session"""
    
    IDLE = "idle"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"
    CANCELLED = "cancelled"


class ConnectionState(str, Enum):
    """State of a connection"""
    
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    RECONNECTING = "reconnecting"
    ERROR = "error"
    TIMEOUT = "timeout"


class ConnectionType(str, Enum):
    """Type of connection protocol"""
    
    SSE = "sse"
    WEBSOCKET = "websocket"


class ParseState(str, Enum):
    """State of JSON parsing"""
    
    IDLE = "idle"
    IN_OBJECT = "in_object"
    IN_ARRAY = "in_array"
    IN_STRING = "in_string"
    IN_NUMBER = "in_number"
    IN_BOOLEAN = "in_boolean"
    IN_NULL = "in_null"
    ERROR = "error"
    COMPLETE = "complete"


class StreamPriority(str, Enum):
    """Priority levels for streaming"""
    
    HIGH = "high"
    NORMAL = "normal"
    LOW = "normal"
    BACKGROUND = "background"


class RenderTarget(str, Enum):
    """Target rendering platform"""
    
    REACT = "react"
    FLUTTER = "flutter"
    NATIVE = "native"
    WEB = "web"


# ============================================================================
# Streaming Event Models
# ============================================================================


class SSEMessage(BaseModel):
    """Server-Sent Event message format"""
    
    event: str = Field(default="message", description="Event type")
    data: str = Field(..., description="Event data")
    id: Optional[str] = Field(default=None, description="Event ID for reconnection")
    retry: Optional[int] = Field(default=None, description="Reconnection delay in ms")
    
    def to_sse_format(self) -> str:
        """Convert to SSE format string"""
        lines = []
        if self.id:
            lines.append(f"id: {self.id}")
        if self.event != "message":
            lines.append(f"event: {self.event}")
        if self.retry:
            lines.append(f"retry: {self.retry}")
        # Data can be multiline
        for line in self.data.split("\n"):
            lines.append(f"data: {line}")
        return "\n".join(lines) + "\n\n"


class WebSocketMessage(BaseModel):
    """WebSocket message format"""
    
    type: StreamingEventType = Field(..., description="Message type")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Message payload")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    sequence: Optional[int] = Field(default=None, description="Sequence number for ordering")
    correlation_id: Optional[str] = Field(default=None, description="ID for request-response correlation")
    
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})


class StreamingEvent(BaseModel):
    """Base streaming event"""
    
    event_id: str = Field(..., description="Unique event ID")
    event_type: StreamingEventType = Field(..., description="Event type")
    session_id: str = Field(..., description="Session ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    data: Dict[str, Any] = Field(default_factory=dict, description="Event data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})


class ComponentEvent(BaseModel):
    """A2UI component event for incremental rendering"""
    
    event_id: str = Field(..., description="Unique event ID")
    event_type: ComponentEventType = Field(..., description="Component event type")
    surface_id: str = Field(..., description="Target surface ID")
    version: str = Field(default="v0_9", description="A2UI version")
    payload: Dict[str, Any] = Field(..., description="Event payload")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Event timestamp")
    dependencies: List[str] = Field(default_factory=list, description="Component dependencies")
    priority: StreamPriority = Field(default=StreamPriority.NORMAL, description="Event priority")
    
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    def to_a2ui_command(self) -> Dict[str, Any]:
        """Convert to A2UI command format"""
        return {
            "version": self.version,
            self.event_type.value: self.payload
        }


# ============================================================================
# Configuration Models
# ============================================================================


class BackpressureConfig(BaseModel):
    """Configuration for backpressure handling"""
    
    enabled: bool = Field(default=True, description="Enable backpressure")
    max_queue_size: int = Field(default=1000, description="Maximum queue size")
    high_watermark: float = Field(default=0.8, description="High watermark (0-1)")
    low_watermark: float = Field(default=0.3, description="Low watermark (0-1)")
    throttle_ms: int = Field(default=100, description="Throttle delay in ms")
    drop_on_overflow: bool = Field(default=False, description="Drop events on overflow")
    priority_aware: bool = Field(default=True, description="Consider priority in dropping")


class HeartbeatConfig(BaseModel):
    """Configuration for heartbeat"""
    
    enabled: bool = Field(default=True, description="Enable heartbeat")
    interval_ms: int = Field(default=30000, description="Heartbeat interval in ms")
    timeout_ms: int = Field(default=10000, description="Heartbeat timeout in ms")
    max_missed: int = Field(default=3, description="Max missed heartbeats before disconnect")
    jitter_ms: int = Field(default=1000, description="Random jitter to prevent thundering herd")


class StreamConfig(BaseModel):
    """Configuration for streaming session"""
    
    session_timeout_ms: int = Field(default=300000, description="Session timeout in ms")
    max_reconnect_attempts: int = Field(default=5, description="Max reconnection attempts")
    reconnect_delay_ms: int = Field(default=1000, description="Initial reconnection delay")
    reconnect_backoff_factor: float = Field(default=2.0, description="Backoff multiplier")
    max_reconnect_delay_ms: int = Field(default=30000, description="Max reconnection delay")
    buffer_size: int = Field(default=65536, description="Stream buffer size")
    chunk_size: int = Field(default=8192, description="Chunk size for streaming")
    compression: bool = Field(default=False, description="Enable compression")
    backpressure: BackpressureConfig = Field(default_factory=BackpressureConfig)
    heartbeat: HeartbeatConfig = Field(default_factory=HeartbeatConfig)


# ============================================================================
# Connection Models
# ============================================================================


class ConnectionMetrics(BaseModel):
    """Metrics for a connection"""
    
    bytes_sent: int = Field(default=0, description="Total bytes sent")
    bytes_received: int = Field(default=0, description="Total bytes received")
    messages_sent: int = Field(default=0, description="Total messages sent")
    messages_received: int = Field(default=0, description="Total messages received")
    events_dispatched: int = Field(default=0, description="Events dispatched")
    events_dropped: int = Field(default=0, description="Events dropped")
    avg_latency_ms: float = Field(default=0.0, description="Average latency in ms")
    reconnect_count: int = Field(default=0, description="Number of reconnections")
    last_heartbeat: Optional[datetime] = Field(default=None, description="Last heartbeat time")
    errors: int = Field(default=0, description="Error count")
    
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})


class ConnectionInfo(BaseModel):
    """Information about a connection"""
    
    connection_id: str = Field(..., description="Unique connection ID")
    connection_type: ConnectionType = Field(..., description="Connection type")
    state: ConnectionState = Field(default=ConnectionState.CONNECTING, description="Current state")
    session_id: str = Field(..., description="Associated session ID")
    user_id: Optional[str] = Field(default=None, description="User ID")
    client_ip: Optional[str] = Field(default=None, description="Client IP address")
    user_agent: Optional[str] = Field(default=None, description="User agent")
    connected_at: datetime = Field(default_factory=datetime.utcnow, description="Connection time")
    last_activity: datetime = Field(default_factory=datetime.utcnow, description="Last activity")
    last_event_id: Optional[str] = Field(default=None, description="Last event ID for reconnection")
    metrics: ConnectionMetrics = Field(default_factory=ConnectionMetrics, description="Connection metrics")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    def update_activity(self) -> None:
        """Update last activity timestamp"""
        self.last_activity = datetime.utcnow()


# ============================================================================
# Parser Models
# ============================================================================


class ParsedComponent(BaseModel):
    """A parsed A2UI component from streaming"""
    
    component_id: str = Field(..., description="Component ID")
    component_type: str = Field(..., description="Component type")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Component properties")
    children: List[str] = Field(default_factory=list, description="Child component IDs")
    bindings: Dict[str, str] = Field(default_factory=dict, description="Data bindings")
    events: Dict[str, str] = Field(default_factory=dict, description="Event handlers")
    is_complete: bool = Field(default=True, description="Whether component is fully parsed")
    parse_position: int = Field(default=0, description="Position in stream where parsed")
    raw_json: Optional[str] = Field(default=None, description="Raw JSON source")
    
    def to_a2ui_component(self) -> Dict[str, Any]:
        """Convert to A2UI component format"""
        component = {
            "id": self.component_id,
            "component": self.component_type,
            **self.properties
        }
        if self.children:
            component["children"] = self.children
        return component


class PartialJSONResult(BaseModel):
    """Result of parsing partial JSON"""
    
    is_complete: bool = Field(default=False, description="Whether JSON is complete")
    is_valid: bool = Field(default=False, description="Whether JSON is valid")
    value: Optional[Any] = Field(default=None, description="Parsed value if complete")
    partial_value: Optional[Any] = Field(default=None, description="Partial parsed value")
    parsed_components: List[ParsedComponent] = Field(default_factory=list, description="Parsed components")
    state: ParseState = Field(default=ParseState.IDLE, description="Current parse state")
    position: int = Field(default=0, description="Current position in stream")
    depth: int = Field(default=0, description="Current nesting depth")
    error: Optional[str] = Field(default=None, description="Error message if any")
    expects: List[str] = Field(default_factory=list, description="Expected tokens")
    
    model_config = ConfigDict(arbitrary_types_allowed=True)


# ============================================================================
# AST Cache Models
# ============================================================================


class ASTCacheEntry(BaseModel):
    """Cached compiled AST for a component"""
    
    cache_key: str = Field(..., description="Cache key (hash of query)")
    query_hash: str = Field(..., description="Hash of the original query")
    ast: Dict[str, Any] = Field(..., description="Compiled AST")
    components: List[Dict[str, Any]] = Field(default_factory=list, description="Component definitions")
    data_model_template: Optional[Dict[str, Any]] = Field(default=None, description="Data model template")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation time")
    last_accessed: datetime = Field(default_factory=datetime.utcnow, description="Last access time")
    access_count: int = Field(default=0, description="Number of accesses")
    ttl_seconds: int = Field(default=3600, description="Time to live in seconds")
    size_bytes: int = Field(default=0, description="Size in bytes")
    tags: Set[str] = Field(default_factory=set, description="Tags for grouping")
    
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    def touch(self) -> None:
        """Update last accessed time and increment count"""
        self.last_accessed = datetime.utcnow()
        self.access_count += 1
    
    def is_expired(self) -> bool:
        """Check if entry is expired"""
        elapsed = (datetime.utcnow() - self.last_accessed).total_seconds()
        return elapsed > self.ttl_seconds
    
    @staticmethod
    def compute_hash(query: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Compute cache key hash"""
        content = query
        if context:
            content += json.dumps(context, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# ============================================================================
# Streaming Session Models
# ============================================================================


class StreamingSession(BaseModel):
    """Active streaming session"""
    
    session_id: str = Field(..., description="Unique session ID")
    connection_id: str = Field(..., description="Associated connection ID")
    user_id: Optional[str] = Field(default=None, description="User ID")
    surface_id: str = Field(..., description="A2UI surface ID")
    state: StreamState = Field(default=StreamState.IDLE, description="Current state")
    protocol: ConnectionType = Field(default=ConnectionType.SSE, description="Protocol used")
    config: StreamConfig = Field(default_factory=StreamConfig, description="Session config")
    started_at: datetime = Field(default_factory=datetime.utcnow, description="Start time")
    last_event_id: Optional[str] = Field(default=None, description="Last event ID")
    event_sequence: int = Field(default=0, description="Event sequence counter")
    pending_components: List[str] = Field(default_factory=list, description="Pending component IDs")
    data_model: Dict[str, Any] = Field(default_factory=dict, description="Current data model")
    context: Dict[str, Any] = Field(default_factory=dict, description="Session context")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    def next_event_id(self) -> str:
        """Generate next event ID"""
        self.event_sequence += 1
        self.last_event_id = f"{self.session_id}:{self.event_sequence}"
        return self.last_event_id
    
    def update_data_model(self, path: str, value: Any) -> None:
        """Update data model at path"""
        parts = path.strip("/").split("/")
        current = self.data_model
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        if parts:
            current[parts[-1]] = value


# ============================================================================
# Response Models
# ============================================================================


class StreamStartResponse(BaseModel):
    """Response for stream start request"""
    
    session_id: str = Field(..., description="Session ID")
    connection_id: str = Field(..., description="Connection ID")
    stream_url: str = Field(..., description="Stream URL")
    protocol: ConnectionType = Field(..., description="Protocol to use")
    config: StreamConfig = Field(..., description="Stream configuration")
    reconnect_token: Optional[str] = Field(default=None, description="Token for reconnection")


class StreamStatusResponse(BaseModel):
    """Response for stream status request"""
    
    session_id: str = Field(..., description="Session ID")
    state: StreamState = Field(..., description="Current state")
    uptime_seconds: float = Field(..., description="Session uptime")
    events_dispatched: int = Field(..., description="Events dispatched")
    components_rendered: int = Field(..., description="Components rendered")
    pending_events: int = Field(..., description="Pending events in queue")
    metrics: ConnectionMetrics = Field(..., description="Connection metrics")


class ComponentBatch(BaseModel):
    """Batch of components for efficient transmission"""
    
    batch_id: str = Field(..., description="Batch ID")
    surface_id: str = Field(..., description="Target surface")
    components: List[ComponentEvent] = Field(..., description="Components in batch")
    is_last: bool = Field(default=False, description="Is this the last batch")
    sequence: int = Field(default=0, description="Batch sequence number")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Batch timestamp")
    
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})


# ============================================================================
# Callback Types (for type hints)
# ============================================================================

# Type alias for async event handlers
EventHandler = Callable[[StreamingEvent], Awaitable[None]]
ComponentHandler = Callable[[ComponentEvent], Awaitable[None]]
TokenHandler = Callable[[str], Awaitable[None]]
