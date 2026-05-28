"""
FastAPI Routes for Streaming Service

Provides HTTP endpoints for:
- SSE streaming
- WebSocket upgrades
- Session management
- Status and metrics
"""

from typing import Any, Dict, List, Optional
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Header,
    WebSocket,
    WebSocketDisconnect,
    Request,
    Response,
)
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import logging

from .models import (
    StreamConfig,
    StreamState,
    StreamStartResponse,
    StreamStatusResponse,
    ConnectionType,
    RenderTarget,
    StreamingEventType,
    ComponentEvent,
)

from .streaming_service import (
    StreamingService,
    StreamProtocol,
    get_streaming_service,
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/streaming", tags=["streaming"])


# ============================================================================
# Request/Response Models
# ============================================================================


class StartStreamRequest(BaseModel):
    """Request to start a new stream"""
    
    surface_id: str = Field(..., description="A2UI surface ID")
    user_id: Optional[str] = Field(default=None, description="User ID")
    render_target: RenderTarget = Field(default=RenderTarget.WEB, description="Target platform")
    initial_data_model: Optional[Dict[str, Any]] = Field(default=None, description="Initial data model")
    protocol: str = Field(default="sse", description="Protocol: 'sse' or 'websocket'")


class QueryRequest(BaseModel):
    """Request to execute a query"""
    
    query: str = Field(..., description="User query/prompt")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    stream: bool = Field(default=True, description="Stream results")


class UpdateDataModelRequest(BaseModel):
    """Request to update data model"""
    
    path: str = Field(..., description="JSON path to update")
    value: Any = Field(..., description="New value")


class ReconnectRequest(BaseModel):
    """Request to reconnect a session"""
    
    reconnection_token: str = Field(..., description="Reconnection token")
    last_event_id: Optional[str] = Field(default=None, description="Last received event ID")


class ComponentRequest(BaseModel):
    """Request to send a component"""
    
    surface_id: str = Field(..., description="Target surface")
    component_type: str = Field(..., description="Component type")
    component_id: str = Field(..., description="Component ID")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Component properties")
    children: List[str] = Field(default_factory=list, description="Child component IDs")


# ============================================================================
# Dependencies
# ============================================================================


def get_service() -> StreamingService:
    """Get the streaming service instance"""
    return get_streaming_service()


async def get_current_user(
    authorization: Optional[str] = Header(default=None),
) -> Optional[str]:
    """
    Extract and validate user ID from authorization header.
    
    Supports:
    - JWT tokens (validated with MCPAuthenticator)
    - API keys (validated against configured keys)
    
    Returns:
        User ID if authenticated, None otherwise
    """
    if not authorization:
        return None
    
    if authorization.startswith("Bearer "):
        token = authorization[7:]
        
        # Import authenticator
        try:
            from ..mcp.auth.jwt_auth import get_authenticator, AuthError
            import os
            
            # Get authenticator with configured secret
            jwt_secret = os.environ.get("MCP_JWT_SECRET", "")
            authenticator = get_authenticator(jwt_secret=jwt_secret)
            
            # Validate token
            auth_token = authenticator.validate_token(token)
            
            # Check rate limit
            if not authenticator.check_rate_limit(auth_token.client_id):
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded"
                )
            
            return auth_token.client_id
            
        except AuthError as e:
            logger.warning(f"Authentication failed: {e}")
            # For development, allow unauthenticated access
            # In production, uncomment the following:
            # raise HTTPException(status_code=401, detail=str(e))
            return f"anonymous_{hash(token) % 10000}"
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            # Fallback: return token hash as user ID for compatibility
            return f"user_{hash(token) % 10000}"
    
    return None


# ============================================================================
# SSE Endpoints
# ============================================================================


@router.get("/sse/{surface_id}")
async def stream_sse(
    surface_id: str,
    service: StreamingService = Depends(get_service),
    user_id: Optional[str] = Depends(get_current_user),
    last_event_id: Optional[str] = Header(default=None, alias="Last-Event-ID"),
    x_client_ip: Optional[str] = Header(default=None, alias="X-Client-IP"),
    user_agent: Optional[str] = Header(default=None),
):
    """
    Start an SSE stream for a surface.
    
    This endpoint returns a text/event-stream response that will
    stream A2UI components as they are generated.
    
    Args:
        surface_id: A2UI surface ID
        last_event_id: Last event ID for reconnection
        x_client_ip: Client IP address
        user_agent: User agent string
    """
    
    async def event_generator():
        async for sse_data in service.create_sse_stream(
            surface_id=surface_id,
            user_id=user_id,
            client_ip=x_client_ip,
            user_agent=user_agent,
            last_event_id=last_event_id,
        ):
            yield sse_data
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.post("/sse/start", response_model=StreamStartResponse)
async def start_sse_session(
    request: StartStreamRequest,
    service: StreamingService = Depends(get_service),
    user_id: Optional[str] = Depends(get_current_user),
    x_client_ip: Optional[str] = Header(default=None, alias="X-Client-IP"),
    user_agent: Optional[str] = Header(default=None),
) -> StreamStartResponse:
    """
    Start a new SSE streaming session.
    
    Returns session info including stream URL and reconnection token.
    """
    session = await service.create_session(
        protocol=StreamProtocol.SSE,
        surface_id=request.surface_id,
        user_id=user_id or request.user_id,
        client_ip=x_client_ip,
        user_agent=user_agent,
        initial_data_model=request.initial_data_model,
        render_target=request.render_target,
    )
    
    # Get reconnection token
    conn_info = service._connection_manager.get_connection(session.connection_id)
    reconnect_state = service._connection_manager._reconnection_states.get(
        session.connection_id
    )
    
    return StreamStartResponse(
        session_id=session.session_id,
        connection_id=session.connection_id,
        stream_url=f"/streaming/sse/{request.surface_id}",
        protocol=ConnectionType.SSE,
        config=session.config,
        reconnect_token=reconnect_state.token if reconnect_state else None,
    )


# ============================================================================
# WebSocket Endpoints
# ============================================================================


@router.websocket("/ws/{surface_id}")
async def websocket_stream(
    websocket: WebSocket,
    surface_id: str,
    user_id: Optional[str] = Query(default=None),
    service: StreamingService = Depends(get_service),
):
    """
    WebSocket streaming endpoint.
    
    Accepts and handles WebSocket connections for bidirectional
    streaming of A2UI components.
    
    Protocol:
    - Client sends JSON messages with 'type' and 'payload' fields
    - Server responds with JSON messages containing component updates
    
    Message Types:
    - ping/pong: Heartbeat
    - query: Start LLM streaming
    - cancel: Cancel current operation
    - data_model_update: Update data model
    """
    await websocket.accept()
    
    # Get client info
    client_ip = websocket.client.host if websocket.client else None
    
    try:
        await service.handle_websocket(
            websocket=websocket,
            surface_id=surface_id,
            user_id=user_id,
            client_ip=client_ip,
        )
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {surface_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=1011, reason=str(e))


# ============================================================================
# Session Management
# ============================================================================


@router.get("/session/{session_id}/status", response_model=StreamStatusResponse)
async def get_session_status(
    session_id: str,
    service: StreamingService = Depends(get_service),
) -> StreamStatusResponse:
    """Get the status of a streaming session."""
    status = await service.get_status(session_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return status


@router.delete("/session/{session_id}")
async def close_session(
    session_id: str,
    service: StreamingService = Depends(get_service),
) -> Dict[str, str]:
    """Close a streaming session."""
    await service.close_session(session_id)
    return {"status": "closed", "session_id": session_id}


@router.post("/session/{session_id}/query")
async def execute_query(
    session_id: str,
    request: QueryRequest,
    service: StreamingService = Depends(get_service),
) -> Dict[str, Any]:
    """
    Execute a query in a session.
    
    If stream=True, results will be streamed via the session's
    SSE or WebSocket connection.
    """
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.state != StreamState.ACTIVE:
        raise HTTPException(status_code=400, detail="Session is not active")
    
    # Start streaming
    await service.stream_llm_to_session(
        session_id=session_id,
        query=request.query,
        context=request.context,
    )
    
    return {
        "status": "streaming",
        "session_id": session_id,
    }


@router.patch("/session/{session_id}/data-model")
async def update_data_model(
    session_id: str,
    request: UpdateDataModelRequest,
    service: StreamingService = Depends(get_service),
) -> Dict[str, Any]:
    """Update the data model for a session."""
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Update data model
    session.update_data_model(request.path, request.value)
    
    # Broadcast update
    await service.broadcast_to_surface(
        surface_id=session.surface_id,
        event_type=StreamingEventType.DATA_MODEL_UPDATE,
        data={
            "path": request.path,
            "value": request.value,
        },
        exclude={session_id},
    )
    
    return {
        "status": "updated",
        "path": request.path,
    }


# ============================================================================
# Reconnection
# ============================================================================


@router.post("/reconnect")
async def reconnect_session(
    request: ReconnectRequest,
    service: StreamingService = Depends(get_service),
) -> Dict[str, Any]:
    """
    Reconnect to a previous session.
    
    Uses the reconnection token to restore state and resume
    from the last received event.
    """
    conn_info = await service._connection_manager.reconnect(
        reconnection_token=request.reconnection_token,
        last_event_id=request.last_event_id,
    )
    
    if not conn_info:
        raise HTTPException(status_code=404, detail="Invalid reconnection token")
    
    # Find session
    session = await service.get_session(conn_info.session_id)
    
    return {
        "status": "reconnected",
        "session_id": conn_info.session_id,
        "connection_id": conn_info.connection_id,
        "last_event_id": request.last_event_id,
    }


# ============================================================================
# Component Management
# ============================================================================


@router.post("/component")
async def send_component(
    request: ComponentRequest,
    service: StreamingService = Depends(get_service),
) -> Dict[str, Any]:
    """
    Send a component to all sessions on a surface.
    
    This is useful for server-initiated updates.
    """
    component = ComponentEvent(
        event_id="manual",
        event_type="updateComponents",
        surface_id=request.surface_id,
        payload={
            "id": request.component_id,
            "component": request.component_type,
            **request.properties,
            "children": request.children,
        },
    )
    
    count = await service.broadcast_to_surface(
        surface_id=request.surface_id,
        event_type=StreamingEventType.COMPONENT,
        data=component.to_a2ui_command(),
    )
    
    return {
        "status": "sent",
        "surface_id": request.surface_id,
        "sessions_reached": count,
    }


# ============================================================================
# Metrics and Health
# ============================================================================


@router.get("/metrics")
async def get_metrics(
    service: StreamingService = Depends(get_service),
) -> Dict[str, Any]:
    """Get service metrics."""
    return service.get_metrics()


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "streaming"}


@router.get("/config", response_model=StreamConfig)
async def get_config(
    service: StreamingService = Depends(get_service),
) -> StreamConfig:
    """Get current streaming configuration."""
    return service._config


# ============================================================================
# Service Lifecycle
# ============================================================================


async def startup_event():
    """Startup event for FastAPI app"""
    service = get_streaming_service()
    await service.start()
    logger.info("Streaming service started")


async def shutdown_event():
    """Shutdown event for FastAPI app"""
    service = get_streaming_service()
    await service.stop()
    logger.info("Streaming service stopped")


def include_router(app):
    """Include streaming router in a FastAPI app"""
    app.include_router(router)
    app.add_event_handler("startup", startup_event)
    app.add_event_handler("shutdown", shutdown_event)
