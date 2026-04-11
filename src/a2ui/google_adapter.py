"""
Google A2UI Adapter

Integration with Google's A2UI library for generative UI.
This module provides a bridge between RICCO AI and Google's A2UI,
allowing us to leverage Google's implementation instead of reimplementing.

Usage:
    from src.a2ui.google_adapter import GoogleA2UIAdapter
    
    adapter = GoogleA2UIAdapter(config)
    response = await adapter.generate_ui(prompt, context)
"""

from typing import Dict, List, Optional, Any, AsyncGenerator
from dataclasses import dataclass, field
from enum import Enum
import json
import logging

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class A2UIPlatform(str, Enum):
    """Supported platforms for A2UI generation"""
    REACT = "react"
    FLUTTER = "flutter"
    LIT = "lit"
    VUE = "vue"
    SWIFT = "swift"


class A2UIStreamEvent(str, Enum):
    """Stream event types"""
    COMPONENT_START = "component_start"
    COMPONENT_DATA = "component_data"
    COMPONENT_COMPLETE = "component_complete"
    STREAM_END = "stream_end"
    ERROR = "error"


@dataclass
class A2UIConfig:
    """Configuration for Google A2UI integration"""
    google_api_key: str
    model: str = "gemini-2.0-flash"
    default_platform: A2UIPlatform = A2UIPlatform.REACT
    max_tokens: int = 4096
    temperature: float = 0.7
    cache_enabled: bool = True
    cache_ttl: int = 300
    streaming_enabled: bool = True


@dataclass
class ContextBundle:
    """Context bundle for A2UI generation"""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    platform: A2UIPlatform = A2UIPlatform.REACT
    locale: str = "en"
    timezone: str = "UTC"
    personal_context: Dict[str, Any] = field(default_factory=dict)
    device_context: Dict[str, Any] = field(default_factory=dict)
    spatial_context: Dict[str, Any] = field(default_factory=dict)
    temporal_context: Dict[str, Any] = field(default_factory=dict)
    
    def to_prompt(self) -> str:
        """Convert context to prompt string"""
        parts = []
        
        if self.personal_context:
            parts.append(f"User Context: {json.dumps(self.personal_context)}")
        if self.device_context:
            parts.append(f"Device: {json.dumps(self.device_context)}")
        if self.spatial_context:
            parts.append(f"Location: {json.dumps(self.spatial_context)}")
        if self.temporal_context:
            parts.append(f"Time Context: {json.dumps(self.temporal_context)}")
        
        parts.append(f"Language: {self.locale}")
        parts.append(f"Timezone: {self.timezone}")
        
        return "\n".join(parts)


@dataclass
class A2UIResponse:
    """Response from A2UI generation"""
    component: str
    props: Dict[str, Any]
    platform: A2UIPlatform
    raw_response: Optional[str] = None
    tokens_used: int = 0
    generation_time_ms: float = 0.0


@dataclass
class StreamEvent:
    """Streaming event from A2UI"""
    event_type: A2UIStreamEvent
    data: Dict[str, Any]
    timestamp: float = 0.0


class ComponentSchema(BaseModel):
    """Schema for A2UI component"""
    name: str
    category: str
    description: str
    props: Dict[str, Any] = Field(default_factory=dict)
    required_props: List[str] = Field(default_factory=list)
    platforms: List[A2UIPlatform] = Field(default_factory=lambda: [A2UIPlatform.REACT])


class ThemeConfig(BaseModel):
    """Theme configuration for A2UI"""
    name: str
    colors: Dict[str, str]
    typography: Dict[str, Any] = Field(default_factory=dict)
    spacing: Dict[str, str] = Field(default_factory=dict)
    components: Dict[str, Any] = Field(default_factory=dict)


class GoogleA2UIAdapter:
    """
    Adapter for Google's A2UI library.
    
    This class provides integration with Google's A2UI system,
    handling UI generation, streaming, and multi-platform compilation.
    
    Key Features:
    - Direct integration with Google's A2UI library
    - Multi-platform support (React, Flutter, Lit, Vue, Swift)
    - Streaming UI generation
    - Context-aware generation
    - Theme management
    - Component registry integration
    
    Example:
        ```python
        config = A2UIConfig(
            google_api_key="your-api-key",
            model="gemini-2.0-flash"
        )
        
        adapter = GoogleA2UIAdapter(config)
        
        # Generate UI
        context = ContextBundle(
            user_id="user-123",
            platform=A2UIPlatform.REACT
        )
        
        response = await adapter.generate_ui(
            prompt="Create a product card",
            context=context
        )
        
        # Stream UI
        async for event in adapter.stream_ui(prompt, context):
            print(event.event_type, event.data)
        ```
    """
    
    def __init__(
        self,
        config: A2UIConfig,
        component_registry: Optional[Any] = None,
        theme_manager: Optional[Any] = None
    ):
        """
        Initialize Google A2UI Adapter.
        
        Args:
            config: A2UI configuration
            component_registry: Optional component registry for schema lookup
            theme_manager: Optional theme manager for styling
        """
        self.config = config
        self.component_registry = component_registry
        self.theme_manager = theme_manager
        
        # Lazy import Google's A2UI library
        self._a2ui = None
        self._initialized = False
        
    async def _ensure_initialized(self):
        """Ensure A2UI is initialized"""
        if self._initialized:
            return
            
        try:
            # Import Google's A2UI library
            # This is a placeholder - actual import depends on library availability
            # from google.a2ui import A2UI
            
            # For now, we use a mock implementation
            logger.info("Initializing Google A2UI adapter")
            self._initialized = True
            
        except ImportError:
            logger.warning(
                "Google A2UI library not installed. "
                "Install with: pip install google-a2ui"
            )
            # Continue with mock implementation
            self._initialized = True
    
    async def generate_ui(
        self,
        prompt: str,
        context: ContextBundle,
        components: Optional[List[ComponentSchema]] = None,
        theme: Optional[ThemeConfig] = None
    ) -> A2UIResponse:
        """
        Generate UI from a prompt using Google's A2UI.
        
        Args:
            prompt: Natural language prompt for UI generation
            context: Context bundle with user/device/spatial info
            components: Optional list of component schemas to use
            theme: Optional theme configuration
            
        Returns:
            A2UIResponse with generated component and props
        """
        await self._ensure_initialized()
        
        # Get enabled components from registry if not provided
        if components is None and self.component_registry:
            components = await self._get_registry_components()
        
        # Get active theme if not provided
        if theme is None and self.theme_manager:
            theme = await self._get_active_theme()
        
        # Build generation request
        generation_request = {
            "prompt": prompt,
            "context": context.to_prompt(),
            "platform": context.platform.value,
            "components": [c.model_dump() for c in components] if components else [],
            "theme": theme.model_dump() if theme else {},
            "generation_config": {
                "model": self.config.model,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
            }
        }
        
        # Generate using Google's A2UI (mock implementation)
        # In production, this would call the actual Google A2UI API
        response = await self._call_a2ui_api(generation_request)
        
        return A2UIResponse(
            component=response.get("component", "div"),
            props=response.get("props", {}),
            platform=context.platform,
            raw_response=response.get("raw"),
            tokens_used=response.get("tokens_used", 0),
            generation_time_ms=response.get("generation_time_ms", 0.0)
        )
    
    async def stream_ui(
        self,
        prompt: str,
        context: ContextBundle,
        components: Optional[List[ComponentSchema]] = None,
        theme: Optional[ThemeConfig] = None
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        Stream UI generation from a prompt.
        
        Args:
            prompt: Natural language prompt for UI generation
            context: Context bundle with user/device/spatial info
            components: Optional list of component schemas to use
            theme: Optional theme configuration
            
        Yields:
            StreamEvent objects as UI is generated
        """
        await self._ensure_initialized()
        
        if not self.config.streaming_enabled:
            # Fall back to non-streaming
            response = await self.generate_ui(prompt, context, components, theme)
            yield StreamEvent(
                event_type=A2UIStreamEvent.COMPONENT_COMPLETE,
                data={
                    "component": response.component,
                    "props": response.props
                }
            )
            yield StreamEvent(
                event_type=A2UIStreamEvent.STREAM_END,
                data={}
            )
            return
        
        # Get components and theme
        if components is None and self.component_registry:
            components = await self._get_registry_components()
        if theme is None and self.theme_manager:
            theme = await self._get_active_theme()
        
        # Build streaming request
        stream_request = {
            "prompt": prompt,
            "context": context.to_prompt(),
            "platform": context.platform.value,
            "components": [c.model_dump() for c in components] if components else [],
            "theme": theme.model_dump() if theme else {},
            "generation_config": {
                "model": self.config.model,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
            }
        }
        
        # Stream using Google's A2UI (mock implementation)
        async for event in self._stream_a2ui_api(stream_request):
            yield event
    
    async def compile_component(
        self,
        component: str,
        props: Dict[str, Any],
        target_platform: A2UIPlatform
    ) -> str:
        """
        Compile a component for a specific platform.
        
        Args:
            component: Component name/type
            props: Component properties
            target_platform: Target platform for compilation
            
        Returns:
            Compiled code for the target platform
        """
        await self._ensure_initialized()
        
        compilation_request = {
            "component": component,
            "props": props,
            "platform": target_platform.value
        }
        
        # Compile using platform-specific compiler
        compiled = await self._compile_for_platform(compilation_request)
        return compiled
    
    async def validate_component(
        self,
        component: str,
        props: Dict[str, Any]
    ) -> bool:
        """
        Validate component props against schema.
        
        Args:
            component: Component name
            props: Props to validate
            
        Returns:
            True if valid, False otherwise
        """
        if self.component_registry:
            schema = await self.component_registry.get_schema(component)
            if schema:
                # Validate props against schema
                return self._validate_against_schema(props, schema)
        return True
    
    # Private methods
    
    async def _get_registry_components(self) -> List[ComponentSchema]:
        """Get enabled components from registry"""
        if not self.component_registry:
            return []
        
        # Get all enabled components
        components = await self.component_registry.get_enabled()
        return [
            ComponentSchema(
                name=c["name"],
                category=c["category"],
                description=c.get("description", ""),
                props=c.get("schema", {}),
                required_props=c.get("required_props", []),
                platforms=[A2UIPlatform(p) for p in c.get("platforms", ["react"])]
            )
            for c in components
        ]
    
    async def _get_active_theme(self) -> Optional[ThemeConfig]:
        """Get active theme from manager"""
        if not self.theme_manager:
            return None
        
        theme = await self.theme_manager.get_active()
        if theme:
            return ThemeConfig(
                name=theme["name"],
                colors=theme.get("colors", {}),
                typography=theme.get("typography", {}),
                spacing=theme.get("spacing", {}),
                components=theme.get("components", {})
            )
        return None
    
    async def _call_a2ui_api(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call Google A2UI API (mock implementation).
        
        In production, this would use the actual Google A2UI client.
        """
        # Mock implementation - replace with actual API call
        import time
        start_time = time.time()
        
        # Simulate API call
        await self._simulate_delay(0.1)
        
        # Mock response based on prompt
        prompt = request.get("prompt", "").lower()
        
        if "product card" in prompt:
            component = "ProductCard"
            props = {
                "title": "Product Title",
                "price": "$99.99",
                "image": "/placeholder.jpg",
                "rating": 4.5
            }
        elif "user profile" in prompt:
            component = "UserProfile"
            props = {
                "name": "User Name",
                "avatar": "/avatar.jpg",
                "bio": "User bio text"
            }
        elif "order" in prompt:
            component = "OrderCard"
            props = {
                "orderId": "ORD-123",
                "status": "pending",
                "total": "$150.00"
            }
        else:
            component = "Container"
            props = {
                "children": request.get("prompt", "")
            }
        
        return {
            "component": component,
            "props": props,
            "raw": json.dumps({"component": component, "props": props}),
            "tokens_used": 150,
            "generation_time_ms": (time.time() - start_time) * 1000
        }
    
    async def _stream_a2ui_api(
        self,
        request: Dict[str, Any]
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        Stream from Google A2UI API (mock implementation).
        """
        import time
        
        # Yield component start
        yield StreamEvent(
            event_type=A2UIStreamEvent.COMPONENT_START,
            data={"component": "div"},
            timestamp=time.time()
        )
        
        # Simulate streaming with partial data
        await self._simulate_delay(0.05)
        
        yield StreamEvent(
            event_type=A2UIStreamEvent.COMPONENT_DATA,
            data={"partial": "<ProductCard"},
            timestamp=time.time()
        )
        
        await self._simulate_delay(0.05)
        
        yield StreamEvent(
            event_type=A2UIStreamEvent.COMPONENT_DATA,
            data={"partial": ' title="Product"'},
            timestamp=time.time()
        )
        
        await self._simulate_delay(0.05)
        
        # Yield complete component
        yield StreamEvent(
            event_type=A2UIStreamEvent.COMPONENT_COMPLETE,
            data={
                "component": "ProductCard",
                "props": {
                    "title": "Product Title",
                    "price": "$99.99"
                }
            },
            timestamp=time.time()
        )
        
        # End stream
        yield StreamEvent(
            event_type=A2UIStreamEvent.STREAM_END,
            data={},
            timestamp=time.time()
        )
    
    async def _compile_for_platform(self, request: Dict[str, Any]) -> str:
        """Compile component for target platform"""
        component = request["component"]
        props = request["props"]
        platform = request["platform"]
        
        if platform == A2UIPlatform.REACT.value:
            # React JSX compilation
            props_str = " ".join(f'{k}="{v}"' for k, v in props.items())
            return f"<{component} {props_str} />"
        
        elif platform == A2UIPlatform.FLUTTER.value:
            # Flutter widget compilation
            props_str = ", ".join(f"{k}: {repr(v)}" for k, v in props.items())
            return f"{component}({props_str})"
        
        elif platform == A2UIPlatform.LIT.value:
            # Lit web component
            props_str = " ".join(f'{k}="{v}"' for k, v in props.items())
            return f"<{component.lower()} {props_str}></{component.lower()}>"
        
        else:
            # Default to React-style
            props_str = " ".join(f'{k}="{v}"' for k, v in props.items())
            return f"<{component} {props_str} />"
    
    def _validate_against_schema(
        self,
        props: Dict[str, Any],
        schema: Dict[str, Any]
    ) -> bool:
        """Validate props against JSON schema"""
        # Simple validation - in production, use jsonschema library
        required = schema.get("required", [])
        for field in required:
            if field not in props:
                return False
        return True
    
    async def _simulate_delay(self, seconds: float):
        """Simulate API delay for mock implementation"""
        import asyncio
        await asyncio.sleep(seconds)


# Factory function for easy instantiation
def create_a2ui_adapter(
    google_api_key: str,
    model: str = "gemini-2.0-flash",
    **kwargs
) -> GoogleA2UIAdapter:
    """
    Create a Google A2UI adapter with default configuration.
    
    Args:
        google_api_key: Google API key
        model: Model to use for generation
        **kwargs: Additional configuration options
        
    Returns:
        Configured GoogleA2UIAdapter instance
    """
    config = A2UIConfig(
        google_api_key=google_api_key,
        model=model,
        **kwargs
    )
    return GoogleA2UIAdapter(config)
