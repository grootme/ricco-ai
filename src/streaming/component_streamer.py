"""
Component Streamer for A2UI

Handles incremental streaming of A2UI components including:
- Priority-based component queue management
- Batch optimization for efficient transmission
- SSR adaptive rendering for different targets
- AST caching for identical queries
- Backpressure handling
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
    Tuple,
)
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
import uuid
import hashlib
import json
import logging
from collections import defaultdict
import time

from .models import (
    ComponentEvent,
    ComponentEventType,
    StreamPriority,
    StreamState,
    RenderTarget,
    ParsedComponent,
    ASTCacheEntry,
    BackpressureConfig,
    StreamingEvent,
    StreamingEventType,
)

from .incremental_parser import (
    IncrementalJSONParser,
    PartialJSONResult,
    create_parser,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Priority Queue Implementation
# ============================================================================


@dataclass(order=True)
class PrioritizedComponent:
    """A component with priority for queue ordering"""
    
    priority: int  # Lower = higher priority (for min-heap)
    sequence: int  # Tie-breaker for ordering
    component: ComponentEvent = field(compare=False)
    timestamp: datetime = field(default_factory=datetime.utcnow, compare=False)


class ComponentQueue:
    """
    Priority queue for components with backpressure support.
    
    Uses a min-heap for efficient priority ordering.
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        high_watermark: float = 0.8,
        low_watermark: float = 0.3,
    ):
        """
        Initialize the component queue.
        
        Args:
            max_size: Maximum queue size
            high_watermark: Ratio to trigger backpressure
            low_watermark: Ratio to clear backpressure
        """
        self._max_size = max_size
        self._high_watermark = high_watermark
        self._low_watermark = low_watermark
        
        self._heap: List[PrioritizedComponent] = []
        self._sequence = 0
        self._backpressure_active = False
        self._lock = asyncio.Lock()
    
    async def put(
        self,
        component: ComponentEvent,
        priority: StreamPriority = StreamPriority.NORMAL,
    ) -> bool:
        """
        Add a component to the queue.
        
        Args:
            component: Component to add
            priority: Component priority
            
        Returns:
            True if added, False if queue is full
        """
        async with self._lock:
            if len(self._heap) >= self._max_size:
                return False
            
            # Convert priority to numeric value
            priority_map = {
                StreamPriority.HIGH: 0,
                StreamPriority.NORMAL: 1,
                StreamPriority.LOW: 2,
                StreamPriority.BACKGROUND: 3,
            }
            
            prioritized = PrioritizedComponent(
                priority=priority_map.get(priority, 1),
                sequence=self._sequence,
                component=component,
            )
            self._sequence += 1
            
            # Use heapq-style insertion
            self._heap.append(prioritized)
            self._heap.sort(key=lambda x: (x.priority, x.sequence))
            
            # Check backpressure
            ratio = len(self._heap) / self._max_size
            if ratio >= self._high_watermark:
                self._backpressure_active = True
            
            return True
    
    async def get(self) -> Optional[ComponentEvent]:
        """
        Get the highest priority component.
        
        Returns:
            Component or None if queue is empty
        """
        async with self._lock:
            if not self._heap:
                return None
            
            prioritized = self._heap.pop(0)
            
            # Check if we can clear backpressure
            ratio = len(self._heap) / self._max_size
            if ratio <= self._low_watermark:
                self._backpressure_active = False
            
            return prioritized.component
    
    async def get_batch(self, max_size: int = 10) -> List[ComponentEvent]:
        """
        Get a batch of components.
        
        Args:
            max_size: Maximum batch size
            
        Returns:
            List of components
        """
        batch = []
        async with self._lock:
            while self._heap and len(batch) < max_size:
                prioritized = self._heap.pop(0)
                batch.append(prioritized.component)
            
            # Check backpressure
            ratio = len(self._heap) / self._max_size
            if ratio <= self._low_watermark:
                self._backpressure_active = False
        
        return batch
    
    @property
    def is_backpressure_active(self) -> bool:
        """Check if backpressure is active"""
        return self._backpressure_active
    
    @property
    def size(self) -> int:
        """Get current queue size"""
        return len(self._heap)
    
    @property
    def is_empty(self) -> bool:
        """Check if queue is empty"""
        return len(self._heap) == 0
    
    def clear(self) -> None:
        """Clear the queue"""
        self._heap.clear()
        self._backpressure_active = False


# ============================================================================
# Stream Session
# ============================================================================


@dataclass
class StreamSession:
    """Active streaming session state"""
    
    session_id: str
    surface_id: str
    user_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    state: StreamState = StreamState.IDLE
    components_sent: int = 0
    tokens_processed: int = 0
    data_model: Dict[str, Any] = field(default_factory=dict)
    component_queue: ComponentQueue = field(default_factory=ComponentQueue)
    parser: IncrementalJSONParser = field(default_factory=create_parser)
    pending_components: Dict[str, ParsedComponent] = field(default_factory=dict)
    render_target: RenderTarget = RenderTarget.WEB
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def update_activity(self) -> None:
        """Update last activity timestamp"""
        self.last_activity = datetime.utcnow()
    
    def increment_tokens(self, count: int = 1) -> None:
        """Increment token count"""
        self.tokens_processed += count


# ============================================================================
# AST Cache
# ============================================================================


class ASTCache:
    """
    LRU cache for compiled component ASTs.
    
    Caches compiled ASTs for identical queries to avoid
    redundant processing.
    """
    
    def __init__(
        self,
        max_entries: int = 1000,
        ttl_seconds: int = 3600,
    ):
        """
        Initialize the AST cache.
        
        Args:
            max_entries: Maximum cache entries
            ttl_seconds: Time to live for entries
        """
        self._max_entries = max_entries
        self._ttl_seconds = ttl_seconds
        self._cache: Dict[str, ASTCacheEntry] = {}
        self._lock = asyncio.Lock()
    
    async def get(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[ASTCacheEntry]:
        """
        Get cached AST for a query.
        
        Args:
            query: Query string
            context: Optional context
            
        Returns:
            Cached entry or None
        """
        cache_key = ASTCacheEntry.compute_hash(query, context)
        
        async with self._lock:
            entry = self._cache.get(cache_key)
            if entry:
                if entry.is_expired():
                    del self._cache[cache_key]
                    return None
                
                entry.touch()
                return entry
        
        return None
    
    async def put(
        self,
        query: str,
        ast: Dict[str, Any],
        components: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
        tags: Optional[Set[str]] = None,
    ) -> ASTCacheEntry:
        """
        Cache an AST for a query.
        
        Args:
            query: Query string
            ast: Compiled AST
            components: Component definitions
            context: Optional context
            tags: Optional tags for grouping
            
        Returns:
            Cache entry
        """
        cache_key = ASTCacheEntry.compute_hash(query, context)
        
        entry = ASTCacheEntry(
            cache_key=cache_key,
            query_hash=hashlib.sha256(query.encode()).hexdigest()[:16],
            ast=ast,
            components=components,
            ttl_seconds=self._ttl_seconds,
            tags=tags or set(),
        )
        
        async with self._lock:
            # Evict if at capacity
            if len(self._cache) >= self._max_entries:
                await self._evict_expired()
                
                if len(self._cache) >= self._max_entries:
                    # Evict least recently used
                    lru_key = min(
                        self._cache.keys(),
                        key=lambda k: self._cache[k].last_accessed
                    )
                    del self._cache[lru_key]
            
            self._cache[cache_key] = entry
        
        return entry
    
    async def _evict_expired(self) -> None:
        """Remove expired entries"""
        expired = [
            key for key, entry in self._cache.items()
            if entry.is_expired()
        ]
        for key in expired:
            del self._cache[key]
    
    def clear(self) -> None:
        """Clear the cache"""
        self._cache.clear()
    
    @property
    def size(self) -> int:
        """Get cache size"""
        return len(self._cache)


# ============================================================================
# Component Streamer
# ============================================================================


class ComponentStreamer:
    """
    Streams A2UI components incrementally from LLM tokens.
    
    Features:
    - Priority-based component queue
    - Batch optimization
    - SSR adaptive rendering
    - AST caching
    - Backpressure handling
    """
    
    def __init__(
        self,
        backpressure_config: Optional[BackpressureConfig] = None,
        cache_enabled: bool = True,
        batch_size: int = 10,
        batch_timeout_ms: int = 100,
    ):
        """
        Initialize the component streamer.
        
        Args:
            backpressure_config: Backpressure configuration
            cache_enabled: Enable AST caching
            batch_size: Maximum batch size
            batch_timeout_ms: Timeout for batch accumulation
        """
        self._backpressure_config = backpressure_config or BackpressureConfig()
        self._cache_enabled = cache_enabled
        self._batch_size = batch_size
        self._batch_timeout_ms = batch_timeout_ms
        
        # Sessions
        self._sessions: Dict[str, StreamSession] = {}
        
        # AST Cache
        self._ast_cache = ASTCache() if cache_enabled else None
        
        # Callbacks
        self._on_component_ready: Optional[Callable[[str, ComponentEvent], Awaitable[None]]] = None
        self._on_backpressure: Optional[Callable[[str, bool], Awaitable[None]]] = None
        
        # Background tasks
        self._batch_task: Optional[asyncio.Task] = None
        self._running = False
    
    # ========================================================================
    # Lifecycle
    # ========================================================================
    
    async def start(self) -> None:
        """Start the component streamer"""
        if self._running:
            return
        
        self._running = True
        logger.info("Component streamer started")
    
    async def stop(self) -> None:
        """Stop the component streamer"""
        self._running = False
        
        # Clear all sessions
        self._sessions.clear()
        
        logger.info("Component streamer stopped")
    
    # ========================================================================
    # Session Management
    # ========================================================================
    
    async def create_session(
        self,
        surface_id: str,
        user_id: Optional[str] = None,
        render_target: RenderTarget = RenderTarget.WEB,
        initial_data_model: Optional[Dict[str, Any]] = None,
    ) -> StreamSession:
        """
        Create a new streaming session.
        
        Args:
            surface_id: A2UI surface ID
            user_id: Optional user ID
            render_target: Target rendering platform
            initial_data_model: Initial data model
            
        Returns:
            New StreamSession
        """
        session_id = str(uuid.uuid4())
        
        queue = ComponentQueue(
            max_size=self._backpressure_config.max_queue_size,
            high_watermark=self._backpressure_config.high_watermark,
            low_watermark=self._backpressure_config.low_watermark,
        )
        
        session = StreamSession(
            session_id=session_id,
            surface_id=surface_id,
            user_id=user_id,
            render_target=render_target,
            data_model=initial_data_model or {},
            component_queue=queue,
        )
        
        self._sessions[session_id] = session
        
        logger.info(f"Created stream session: {session_id}")
        
        return session
    
    async def get_session(self, session_id: str) -> Optional[StreamSession]:
        """Get a streaming session"""
        return self._sessions.get(session_id)
    
    async def close_session(self, session_id: str) -> None:
        """Close a streaming session"""
        session = self._sessions.pop(session_id, None)
        if session:
            session.state = StreamState.COMPLETED
            session.component_queue.clear()
            logger.info(f"Closed stream session: {session_id}")
    
    # ========================================================================
    # Token Processing
    # ========================================================================
    
    async def feed_tokens(
        self,
        session_id: str,
        tokens: str,
    ) -> List[ComponentEvent]:
        """
        Feed tokens to the parser and emit completed components.
        
        Args:
            session_id: Session to feed tokens to
            tokens: Token string to parse
            
        Returns:
            List of completed component events
        """
        session = self._sessions.get(session_id)
        if not session:
            logger.warning(f"Session not found: {session_id}")
            return []
        
        session.update_activity()
        session.state = StreamState.ACTIVE
        
        # Feed to parser
        result = session.parser.feed(tokens)
        session.increment_tokens(len(tokens))
        
        # Get completed components
        parsed_components = session.parser.get_completed_components()
        
        # Convert to events
        events = []
        for comp in parsed_components:
            event = self._create_component_event(session, comp)
            events.append(event)
            
            # Queue the event
            await session.component_queue.put(event, comp.properties.get("_priority", StreamPriority.NORMAL))
            
            # Fire callback
            if self._on_component_ready:
                await self._on_component_ready(session_id, event)
        
        # Check backpressure
        if session.component_queue.is_backpressure_active:
            if self._on_backpressure:
                await self._on_backpressure(session_id, True)
        
        return events
    
    async def feed_token_stream(
        self,
        session_id: str,
        token_stream: AsyncGenerator[str, None],
    ) -> AsyncGenerator[ComponentEvent, None]:
        """
        Feed a stream of tokens and yield component events.
        
        Args:
            session_id: Session to feed tokens to
            token_stream: Async generator of tokens
            
        Yields:
            ComponentEvent objects as they're completed
        """
        async for tokens in token_stream:
            events = await self.feed_tokens(session_id, tokens)
            for event in events:
                yield event
    
    async def finalize_session(
        self,
        session_id: str,
    ) -> List[ComponentEvent]:
        """
        Finalize a session and return remaining components.
        
        Args:
            session_id: Session to finalize
            
        Returns:
            List of remaining component events
        """
        session = self._sessions.get(session_id)
        if not session:
            return []
        
        # Finalize parser
        result = session.parser.finalize()
        
        # Get any remaining components
        parsed_components = session.parser.get_completed_components()
        
        events = []
        for comp in parsed_components:
            event = self._create_component_event(session, comp)
            events.append(event)
        
        session.state = StreamState.COMPLETED
        
        return events
    
    # ========================================================================
    # Component Retrieval
    # ========================================================================
    
    async def get_next_component(
        self,
        session_id: str,
        timeout: Optional[float] = None,
    ) -> Optional[ComponentEvent]:
        """
        Get the next component from the queue.
        
        Args:
            session_id: Session to get from
            timeout: Optional timeout in seconds
            
        Returns:
            Component or None
        """
        session = self._sessions.get(session_id)
        if not session:
            return None
        
        if timeout:
            try:
                # Wait for component with timeout
                start = time.time()
                while session.component_queue.is_empty:
                    if time.time() - start > timeout:
                        return None
                    await asyncio.sleep(0.01)
            except asyncio.CancelledError:
                return None
        
        return await session.component_queue.get()
    
    async def get_component_batch(
        self,
        session_id: str,
        max_size: Optional[int] = None,
    ) -> List[ComponentEvent]:
        """
        Get a batch of components.
        
        Args:
            session_id: Session to get from
            max_size: Maximum batch size
            
        Returns:
            List of components
        """
        session = self._sessions.get(session_id)
        if not session:
            return []
        
        return await session.component_queue.get_batch(max_size or self._batch_size)
    
    async def stream_components(
        self,
        session_id: str,
    ) -> AsyncGenerator[ComponentEvent, None]:
        """
        Stream components as they become available.
        
        Args:
            session_id: Session to stream from
            
        Yields:
            ComponentEvent objects
        """
        session = self._sessions.get(session_id)
        if not session:
            return
        
        while session.state in (StreamState.ACTIVE, StreamState.IDLE):
            component = await session.component_queue.get()
            if component:
                yield component
                session.components_sent += 1
            else:
                await asyncio.sleep(0.01)
    
    # ========================================================================
    # AST Caching
    # ========================================================================
    
    async def get_cached_ast(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[ASTCacheEntry]:
        """Get a cached AST for a query"""
        if not self._ast_cache:
            return None
        return await self._ast_cache.get(query, context)
    
    async def cache_ast(
        self,
        query: str,
        ast: Dict[str, Any],
        components: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[ASTCacheEntry]:
        """Cache an AST for a query"""
        if not self._ast_cache:
            return None
        return await self._ast_cache.put(query, ast, components, context)
    
    # ========================================================================
    # SSR Adaptive Rendering
    # ========================================================================
    
    async def render_for_target(
        self,
        component: ParsedComponent,
        target: RenderTarget,
    ) -> Dict[str, Any]:
        """
        Render a component for a specific target.
        
        Args:
            component: Component to render
            target: Target platform
            
        Returns:
            Rendered component data
        """
        base_component = component.to_a2ui_component()
        
        if target == RenderTarget.REACT:
            return self._render_for_react(base_component)
        elif target == RenderTarget.FLUTTER:
            return self._render_for_flutter(base_component)
        elif target == RenderTarget.NATIVE:
            return self._render_for_native(base_component)
        else:
            return base_component
    
    def _render_for_react(self, component: Dict[str, Any]) -> Dict[str, Any]:
        """Render component for React"""
        # React-specific adaptations
        rendered = dict(component)
        
        # Convert style objects to React style format
        if "style" in rendered:
            style = rendered["style"]
            if isinstance(style, dict):
                # Convert snake_case to camelCase
                rendered["style"] = {
                    self._to_camel_case(k): v
                    for k, v in style.items()
                }
        
        # Add React-specific props
        rendered["_react"] = True
        
        return rendered
    
    def _render_for_flutter(self, component: Dict[str, Any]) -> Dict[str, Any]:
        """Render component for Flutter"""
        # Flutter-specific adaptations
        rendered = dict(component)
        
        # Map component types to Flutter widgets
        type_map = {
            "Column": "Column",
            "Row": "Row",
            "Text": "Text",
            "Button": "ElevatedButton",
            "TextField": "TextField",
            "Card": "Card",
            "List": "ListView",
            "Icon": "Icon",
            "Image": "Image",
            "Container": "Container",
        }
        
        if rendered.get("component") in type_map:
            rendered["component"] = type_map[rendered["component"]]
        
        # Add Flutter-specific props
        rendered["_flutter"] = True
        
        return rendered
    
    def _render_for_native(self, component: Dict[str, Any]) -> Dict[str, Any]:
        """Render component for native platforms"""
        # Native-specific adaptations (iOS/Android)
        rendered = dict(component)
        rendered["_native"] = True
        return rendered
    
    def _to_camel_case(self, snake_str: str) -> str:
        """Convert snake_case to camelCase"""
        components = snake_str.split('_')
        return components[0] + ''.join(x.title() for x in components[1:])
    
    # ========================================================================
    # Component Creation
    # ========================================================================
    
    def _create_component_event(
        self,
        session: StreamSession,
        component: ParsedComponent,
    ) -> ComponentEvent:
        """Create a ComponentEvent from a parsed component"""
        event_type = self._determine_event_type(component)
        
        return ComponentEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            surface_id=session.surface_id,
            payload={
                "id": component.component_id,
                "component": component.component_type,
                **component.properties,
                "children": component.children,
            },
            dependencies=component.children,
        )
    
    def _determine_event_type(
        self,
        component: ParsedComponent,
    ) -> ComponentEventType:
        """Determine the event type for a component"""
        # Check for special component types
        comp_type = component.component_type.lower()
        
        if comp_type in ("createdialog", "dialog", "modal"):
            return ComponentEventType.SHOW_DIALOG
        elif comp_type in ("toast", "snackbar", "notification"):
            return ComponentEventType.SHOW_TOAST
        elif comp_type in ("navigate", "router", "link"):
            return ComponentEventType.NAVIGATE
        else:
            return ComponentEventType.UPDATE_COMPONENTS
    
    # ========================================================================
    # Callbacks
    # ========================================================================
    
    def on_component_ready(
        self,
        callback: Callable[[str, ComponentEvent], Awaitable[None]],
    ) -> None:
        """Set callback for when a component is ready"""
        self._on_component_ready = callback
    
    def on_backpressure(
        self,
        callback: Callable[[str, bool], Awaitable[None]],
    ) -> None:
        """Set callback for backpressure changes"""
        self._on_backpressure = callback
    
    # ========================================================================
    # Metrics
    # ========================================================================
    
    def get_session_metrics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get metrics for a session"""
        session = self._sessions.get(session_id)
        if not session:
            return None
        
        return {
            "session_id": session.session_id,
            "state": session.state.value,
            "components_sent": session.components_sent,
            "tokens_processed": session.tokens_processed,
            "queue_size": session.component_queue.size,
            "backpressure_active": session.component_queue.is_backpressure_active,
            "uptime_seconds": (datetime.utcnow() - session.created_at).total_seconds(),
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get overall streamer metrics"""
        return {
            "active_sessions": len(self._sessions),
            "cache_size": self._ast_cache.size if self._ast_cache else 0,
            "cache_enabled": self._cache_enabled,
        }


# ============================================================================
# Global Instance
# ============================================================================

_component_streamer: Optional[ComponentStreamer] = None


def get_component_streamer(
    backpressure_config: Optional[BackpressureConfig] = None,
    **kwargs,
) -> ComponentStreamer:
    """Get the global component streamer instance"""
    global _component_streamer
    if _component_streamer is None:
        _component_streamer = ComponentStreamer(backpressure_config, **kwargs)
    return _component_streamer
