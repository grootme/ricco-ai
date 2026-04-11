"""
Streaming Module for RICCO AI

SSE and WebSocket streaming services for A2UI.
Integrated from genui.
"""

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
)
from .streaming_service import (
    StreamingService,
    StreamProtocol,
    get_streaming_service,
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

__all__ = [
    # Models
    "StreamingEvent",
    "StreamingEventType",
    "ComponentEvent",
    "ComponentEventType",
    "StreamState",
    "ConnectionState",
    "StreamConfig",
    "BackpressureConfig",
    "SSEMessage",
    "WebSocketMessage",
    "ParsedComponent",
    "StreamStartResponse",
    "StreamStatusResponse",
    "ConnectionType",
    "RenderTarget",
    "StreamSessionModel",
    # Services
    "StreamingService",
    "StreamProtocol",
    "get_streaming_service",
    "ConnectionManager",
    "ConnectionInfo",
    "get_connection_manager",
    "ComponentStreamer",
    "StreamPriority",
    "StreamSession",
    "get_component_streamer",
    "IncrementalJSONParser",
    "PartialJSONResult",
    "create_parser",
]
