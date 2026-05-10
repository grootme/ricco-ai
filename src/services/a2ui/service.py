"""
A2UI Service - Consolidated Implementation
Merged from: a2ui_service.py, a2ui_service_enhanced.py, app/services/a2ui_service.py

Implements:
- Strategy Pattern: Different UI generation strategies
- Template Method Pattern: Template-based component generation
- Observer Pattern: Context-aware UI updates
- Singleton Pattern: Service instance management
"""

import sys
import uuid
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from enum import Enum

from loguru import logger

from .models import (
    ComponentType, ResponseStatus, A2UIComponent, A2UIResponse, A2UIState,
    ComponentBuilder, ResponseBuilder
)
from .context_models import (
    PersonalContext, SpatialContext, TemporalContext, DeviceContext,
    SolutionContext, HorizontalContext, VerticalContext, ContextBundle,
    ContextBundleBuilder, UIContextMode
)
from .templates import (
    UITemplate, ChatUITemplate, KYCFormTemplate, ProductSearchTemplate,
    OrderStatusTemplate, TrackingTemplate, TemplateRegistry
)

# =============================================================================
# A2UI SDK Integration
# =============================================================================

# Try to import A2UI SDK from external directory
A2UI_SDK_PATH = Path(__file__).parent.parent.parent.parent.parent / "external" / "A2UI" / "agent_sdks" / "python" / "src"
if A2UI_SDK_PATH.exists():
    sys.path.insert(0, str(A2UI_SDK_PATH))

try:
    from a2ui.a2a import (
        create_a2ui_part,
        get_a2ui_agent_extension,
        parse_response_to_parts,
        A2UI_EXTENSION_BASE_URI
    )
    from a2ui.core.schema.catalog import A2uiCatalog
    from a2ui.basic_catalog.provider import BasicCatalog
    A2UI_SDK_AVAILABLE = True
    logger.info("A2UI SDK loaded successfully")
except ImportError as e:
    A2UI_SDK_AVAILABLE = False
    A2UI_EXTENSION_BASE_URI = "https://a2ui.org/a2a-extension/a2ui"
    logger.warning(f"A2UI SDK not available: {e}")


# =============================================================================
# Context Bundle Cache (for performance)
# =============================================================================

class ContextCache:
    """Simple in-memory cache for context bundles"""
    
    def __init__(self, ttl: int = 3600):
        self._cache: Dict[str, tuple] = {}  # key -> (value, expiry)
        self._ttl = ttl
    
    def get(self, key: str) -> Optional[ContextBundle]:
        if key in self._cache:
            value, expiry = self._cache[key]
            if datetime.utcnow().timestamp() < expiry:
                return value
            del self._cache[key]
        return None
    
    def set(self, key: str, value: ContextBundle) -> None:
        expiry = datetime.utcnow().timestamp() + self._ttl
        self._cache[key] = (value, expiry)
    
    def delete(self, key: str) -> bool:
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self) -> None:
        self._cache.clear()


# =============================================================================
# Theme Manager (Strategy Pattern)
# =============================================================================

class ThemeManager:
    """
    Manages themes based on context.
    
    Implements: Strategy Pattern - different theme strategies
    """
    
    @staticmethod
    def get_theme_from_context(context: Optional[ContextBundle]) -> Dict[str, Any]:
        """Determine theme based on context"""
        theme = {
            "mode": "light",
            "primary": "#1976D2",
            "secondary": "#424242",
            "background": "#FFFFFF",
            "surface": "#F5F5F5"
        }
        
        if not context:
            return theme
        
        # Dark mode from device
        if context.device and context.device.color_scheme == "dark":
            theme.update({
                "mode": "dark",
                "primary": "#90CAF9",
                "secondary": "#BDBDBD",
                "background": "#121212",
                "surface": "#1E1E1E"
            })
        
        # Battery saving mode
        if context.is_low_battery():
            theme["mode"] = "dark"
        
        # High contrast for accessibility
        if (context.personal and 
            context.personal.preferences.get("high_contrast", False)):
            theme.update({
                "primary": "#000000",
                "secondary": "#FFFFFF",
                "background": "#FFFFFF"
            })
        
        return theme


# =============================================================================
# Main A2UI Service
# =============================================================================

class A2UIService:
    """
    Consolidated A2UI Service for RICCO AI.
    
    Features:
    - Dynamic UI generation with A2UI SDK
    - Context-aware surfaces
    - Template-based component generation
    - Theme management
    - Multiple UI modes
    
    Implements:
    - Strategy Pattern: Different generation strategies
    - Template Method Pattern: Template-based creation
    - Facade Pattern: Simplified interface to complex subsystems
    """
    
    def __init__(
        self,
        catalog_version: str = "v0_9",
        enable_context: bool = True
    ):
        """
        Initialize A2UI service.
        
        Args:
            catalog_version: A2UI catalog version
            enable_context: Enable context-aware features
        """
        self.catalog_version = catalog_version
        self._catalog: Optional[Any] = None
        self._context_cache = ContextCache() if enable_context else None
        self._sessions: Dict[str, A2UIState] = {}
        self._enable_context = enable_context
        self._theme_manager = ThemeManager()
        self._initialized = False
    
    # =========================================================================
    # Lifecycle
    # =========================================================================
    
    async def initialize(self) -> None:
        """Initialize A2UI service and SDK"""
        if self._initialized:
            return
        
        # Initialize A2UI SDK
        if A2UI_SDK_AVAILABLE:
            try:
                self._catalog = BasicCatalog()
                logger.info("A2UI catalog initialized")
            except Exception as e:
                logger.error(f"Failed to initialize A2UI catalog: {e}")
        
        self._initialized = True
    
    async def shutdown(self) -> None:
        """Cleanup resources"""
        self._sessions.clear()
        if self._context_cache:
            self._context_cache.clear()
        self._initialized = False
    
    # =========================================================================
    # Session Management
    # =========================================================================
    
    async def create_session(
        self,
        user_id: str,
        solution: str,
        device_context: Optional[DeviceContext] = None
    ) -> A2UIState:
        """Create a new A2UI session"""
        session_id = str(uuid.uuid4())
        
        state = A2UIState(
            session_id=session_id,
            user_id=user_id,
            solution=solution,
            context={
                "device": device_context.model_dump() if device_context else {}
            }
        )
        
        self._sessions[session_id] = state
        logger.info(f"Created A2UI session {session_id} for user {user_id}")
        
        return state
    
    async def get_session(self, session_id: str) -> Optional[A2UIState]:
        """Get session by ID"""
        return self._sessions.get(session_id)
    
    async def update_session(
        self,
        session_id: str,
        form_data: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[A2UIState]:
        """Update session state"""
        state = self._sessions.get(session_id)
        if not state:
            return None
        
        if form_data:
            state.form_data.update(form_data)
        
        if context:
            state.context.update(context)
        
        state.updated_at = datetime.utcnow()
        return state
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
    
    # =========================================================================
    # Surface Operations
    # =========================================================================
    
    def create_surface(
        self,
        surface_id: str,
        catalog_id: str = "https://a2ui.org/specification/v0_9/basic_catalog.json",
        theme: Optional[Dict] = None,
        send_data_model: bool = False
    ) -> Dict[str, Any]:
        """Create a new UI surface"""
        return {
            "version": self.catalog_version,
            "createSurface": {
                "surfaceId": surface_id,
                "catalogId": catalog_id,
                "theme": theme or {},
                "sendDataModel": send_data_model
            }
        }
    
    def update_components(
        self,
        surface_id: str,
        components: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Update components on a surface"""
        return {
            "version": self.catalog_version,
            "updateComponents": {
                "surfaceId": surface_id,
                "components": components
            }
        }
    
    def update_data_model(
        self,
        surface_id: str,
        path: str,
        value: Any
    ) -> Dict[str, Any]:
        """Update data model for a surface"""
        return {
            "version": self.catalog_version,
            "updateDataModel": {
                "surfaceId": surface_id,
                "path": path,
                "value": value
            }
        }
    
    def delete_surface(self, surface_id: str) -> Dict[str, Any]:
        """Delete a surface"""
        return {
            "version": self.catalog_version,
            "deleteSurface": {
                "surfaceId": surface_id
            }
        }
    
    # =========================================================================
    # Context-Aware UI Generation
    # =========================================================================
    
    async def create_contextual_surface(
        self,
        surface_id: str,
        user_id: str,
        session_id: str,
        context_bundle: Optional[ContextBundle] = None,
        ui_mode: UIContextMode = UIContextMode.STANDARD
    ) -> List[Dict[str, Any]]:
        """
        Create a context-aware UI surface.
        
        Args:
            surface_id: Surface ID
            user_id: User ID
            session_id: Session ID
            context_bundle: Pre-built context bundle (optional)
            ui_mode: UI generation mode
            
        Returns:
            List of A2UI commands
        """
        commands = []
        
        # Load or use provided context
        if not context_bundle and self._context_cache:
            context_bundle = self._context_cache.get(session_id)
        
        # Get theme from context
        theme = self._theme_manager.get_theme_from_context(context_bundle)
        
        # Create base surface
        commands.append({
            "version": self.catalog_version,
            "createSurface": {
                "surfaceId": surface_id,
                "catalogId": "https://a2ui.org/specification/v0_9/basic_catalog.json",
                "theme": theme,
                "sendDataModel": True
            }
        })
        
        # Generate components based on mode
        components = self._generate_mode_components(surface_id, context_bundle, ui_mode)
        
        commands.append({
            "version": self.catalog_version,
            "updateComponents": {
                "surfaceId": surface_id,
                "components": components
            }
        })
        
        # Initialize data model
        data_model = self._create_initial_data_model(context_bundle)
        commands.append({
            "version": self.catalog_version,
            "updateDataModel": {
                "surfaceId": surface_id,
                "path": "/",
                "value": data_model
            }
        })
        
        return commands
    
    def _generate_mode_components(
        self,
        surface_id: str,
        context: Optional[ContextBundle],
        mode: UIContextMode
    ) -> List[Dict[str, Any]]:
        """Generate components based on UI mode"""
        if mode == UIContextMode.MINIMAL:
            return self._create_minimal_components(surface_id, context)
        elif mode == UIContextMode.DETAILED:
            return self._create_detailed_components(surface_id, context)
        elif mode == UIContextMode.ACCESSIBILITY:
            return self._create_accessibility_components(surface_id, context)
        else:
            return self._create_standard_components(surface_id, context)
    
    def _create_minimal_components(
        self,
        surface_id: str,
        context: Optional[ContextBundle]
    ) -> List[Dict[str, Any]]:
        """Create minimal components"""
        return [
            {"id": "root", "component": "Column", "children": ["content"]},
            {"id": "content", "component": "Text", "text": {"path": "/content"}}
        ]
    
    def _create_standard_components(
        self,
        surface_id: str,
        context: Optional[ContextBundle]
    ) -> List[Dict[str, Any]]:
        """Create standard components"""
        components = [
            {"id": "root", "component": "Column", "children": ["header", "content", "footer"]},
            {"id": "header", "component": "Row", "children": ["title", "context_indicator"]},
            {"id": "title", "component": "Text", "text": "RICCO AI", "variant": "h6"},
            {"id": "context_indicator", "component": "Icon", "name": "info"},
            {"id": "content", "component": "Column", "children": ["messages", "input"]},
            {"id": "messages", "component": "List", "children": {"path": "/messages", "componentId": "message"}},
            {"id": "message", "component": "Card", "child": "message_text"},
            {"id": "message_text", "component": "Text", "text": {"path": "/content"}},
            {"id": "input", "component": "TextField", "label": "Mensaje", "value": {"path": "/input"}},
            {"id": "footer", "component": "Row", "children": ["status"]}
        ]
        
        # Add location badge if available
        if context and context.spatial and context.spatial.city:
            components.append({
                "id": "location_badge",
                "component": "Chip",
                "label": context.spatial.city,
                "icon": "location_on"
            })
        
        return components
    
    def _create_detailed_components(
        self,
        surface_id: str,
        context: Optional[ContextBundle]
    ) -> List[Dict[str, Any]]:
        """Create detailed components with context panel"""
        return [
            {"id": "root", "component": "Column", "children": ["header", "context_panel", "content", "actions", "footer"]},
            {"id": "header", "component": "AppBar", "title": "RICCO AI", "actions": ["settings"]},
            {"id": "settings", "component": "IconButton", "icon": "settings"},
            {"id": "context_panel", "component": "Card", "child": "context_content"},
            {"id": "context_content", "component": "Row", "children": ["time", "location", "device"]},
            {"id": "time", "component": "Text", "text": {"path": "/context/time"}},
            {"id": "location", "component": "Text", "text": {"path": "/context/location"}},
            {"id": "device", "component": "Icon", "name": {"path": "/context/device_icon"}},
            {"id": "content", "component": "Expanded", "child": "messages"},
            {"id": "messages", "component": "ListView", "children": {"path": "/messages", "componentId": "message"}},
            {"id": "message", "component": "MessageBubble", "content": {"path": "/content"}, "role": {"path": "/role"}},
            {"id": "actions", "component": "Row", "children": ["context_toggle", "send"]},
            {"id": "context_toggle", "component": "IconButton", "icon": "tune"},
            {"id": "send", "component": "Button", "child": "send_icon", "variant": "primary"},
            {"id": "send_icon", "component": "Icon", "name": "send"},
            {"id": "footer", "component": "BottomBar", "children": ["quota"]}
        ]
    
    def _create_accessibility_components(
        self,
        surface_id: str,
        context: Optional[ContextBundle]
    ) -> List[Dict[str, Any]]:
        """Create accessibility-optimized components"""
        return [
            {"id": "root", "component": "Column", "children": ["header", "content", "input"]},
            {"id": "header", "component": "Text", "text": "RICCO AI", "variant": "h4", "semanticLabel": "Asistente RICCO"},
            {"id": "content", "component": "Column", "children": {"path": "/messages", "componentId": "message"}},
            {"id": "message", "component": "Card", "child": "message_text", "semanticLabel": {"path": "/semantic_label"}},
            {"id": "message_text", "component": "Text", "text": {"path": "/content"}, "style": {"fontSize": 18}},
            {"id": "input", "component": "TextField", "label": "Escribe tu mensaje", "value": {"path": "/input"}, "style": {"fontSize": 18}}
        ]
    
    def _create_initial_data_model(
        self,
        context: Optional[ContextBundle]
    ) -> Dict[str, Any]:
        """Create initial data model with context"""
        data = {
            "messages": [],
            "input": "",
            "context": {
                "time": "",
                "location": "",
                "device_icon": "smartphone"
            }
        }
        
        if context:
            if context.temporal:
                data["context"]["time"] = context.temporal.time_of_day
            
            if context.spatial and context.spatial.city:
                data["context"]["location"] = context.spatial.city
            
            if context.device:
                data["context"]["device_icon"] = self._get_device_icon(context.device.device_type)
        
        return data
    
    def _get_device_icon(self, device_type: str) -> str:
        """Get icon for device type"""
        icons = {
            "mobile": "smartphone",
            "tablet": "tablet",
            "desktop": "computer",
            "smartwatch": "watch",
            "smarttv": "tv"
        }
        return icons.get(device_type, "device_unknown")
    
    # =========================================================================
    # Template-Based UI Generation
    # =========================================================================
    
    async def generate_from_template(
        self,
        template_name: str,
        surface_id: str,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Generate UI using a template.
        
        Args:
            template_name: Name of the template to use
            surface_id: Surface ID
            **kwargs: Template-specific parameters
            
        Returns:
            List of A2UI commands
        """
        template = TemplateRegistry.get_template(template_name)
        if not template:
            raise ValueError(f"Unknown template: {template_name}")
        
        commands = []
        
        # Create surface
        commands.append(self.create_surface(surface_id))
        
        # Generate components
        components = template.create_components(surface_id=surface_id, **kwargs)
        commands.append(self.create_update_components_command(surface_id, components))
        
        # Initialize data model
        if hasattr(template, 'create_initial_data_model'):
            data_model = template.create_initial_data_model()
            commands.append(self.update_data_model(surface_id, "/", data_model))
        
        return commands
    
    def create_update_components_command(
        self,
        surface_id: str,
        components: List[A2UIComponent]
    ) -> Dict[str, Any]:
        """Create update components command from component objects"""
        def component_to_dict(comp: A2UIComponent) -> Dict[str, Any]:
            result = {
                "id": comp.id,
                "component": comp.type.value,
            }
            
            if comp.properties:
                result.update(comp.properties)
            
            if comp.children:
                if all(isinstance(c, str) for c in comp.children):
                    result["children"] = comp.children
                else:
                    result["children"] = [component_to_dict(c) for c in comp.children]
            
            return result
        
        return {
            "version": self.catalog_version,
            "updateComponents": {
                "surfaceId": surface_id,
                "components": [component_to_dict(c) for c in components]
            }
        }
    
    # =========================================================================
    # Convenience Methods (Backward Compatibility)
    # =========================================================================
    
    def create_chat_ui(
        self,
        surface_id: str,
        user_name: str = "User",
        assistant_name: str = "RICCO AI"
    ) -> List[Dict]:
        """Create RICCO chat interface (convenience method)"""
        template = ChatUITemplate()
        return [
            self.create_surface(surface_id),
            self.create_update_components_command(
                surface_id,
                template.create_components(surface_id=surface_id, user_name=user_name, assistant_name=assistant_name)
            ),
            self.update_data_model(surface_id, "/", template.create_initial_data_model())
        ]
    
    def create_kyc_form(
        self,
        surface_id: str,
        kyc_type: str = "individual"
    ) -> List[Dict]:
        """Create KYC form for RICCO ID (convenience method)"""
        template = KYCFormTemplate()
        return [
            self.create_surface(surface_id),
            self.create_update_components_command(
                surface_id,
                template.create_components(surface_id=surface_id, kyc_type=kyc_type)
            ),
            self.update_data_model(surface_id, "/", template.create_initial_data_model())
        ]
    
    # =========================================================================
    # A2A Protocol Integration
    # =========================================================================
    
    def create_a2ui_part(self, a2ui_data: Dict[str, Any]) -> Any:
        """Create A2A Part with A2UI data"""
        if A2UI_SDK_AVAILABLE:
            return create_a2ui_part(a2ui_data)
        return {"data": a2ui_data, "metadata": {"mimeType": "application/json+a2ui"}}
    
    def get_agent_extension(
        self,
        version: str = "0.9",
        supported_catalog_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get A2UI agent extension for A2A protocol"""
        if A2UI_SDK_AVAILABLE:
            return get_a2ui_agent_extension(
                version=version,
                supported_catalog_ids=supported_catalog_ids or []
            ).model_dump()
        return {
            "uri": f"{A2UI_EXTENSION_BASE_URI}/v{version}",
            "description": "A2UI extension for dynamic UI with context awareness"
        }
    
    def parse_llm_response(self, content: str) -> List[Any]:
        """Parse LLM response for A2UI parts"""
        if A2UI_SDK_AVAILABLE and self._catalog:
            return parse_response_to_parts(content, validator=self._catalog.validator)
        return []
    
    # =========================================================================
    # Context Bundle Building
    # =========================================================================
    
    async def build_context_bundle(
        self,
        user_id: str,
        session_id: str,
        solution: str,
        request_context: Optional[Dict[str, Any]] = None
    ) -> ContextBundle:
        """
        Build comprehensive context bundle for AI agent.
        
        Args:
            user_id: User ID
            session_id: Session ID
            solution: Solution ID
            request_context: Request context data
            
        Returns:
            ContextBundle with all context types
        """
        now = datetime.utcnow()
        
        # Build temporal context
        hour = now.hour
        if 6 <= hour < 12:
            time_of_day = "morning"
        elif 12 <= hour < 18:
            time_of_day = "afternoon"
        elif 18 <= hour < 22:
            time_of_day = "evening"
        else:
            time_of_day = "night"
        
        temporal = TemporalContext(
            current_time=now,
            timezone=request_context.get("timezone", "UTC") if request_context else "UTC",
            time_of_day=time_of_day,
            day_of_week=now.strftime("%A").lower(),
            is_weekend=now.weekday() >= 5,
            month=now.month,
            quarter=(now.month - 1) // 3 + 1
        )
        
        # Build personal context
        personal = PersonalContext(
            user_id=user_id,
            language=request_context.get("language", "es") if request_context else "es",
            timezone=temporal.timezone
        )
        
        # Build device context
        device = None
        if request_context and "device" in request_context:
            device_data = request_context["device"]
            device = DeviceContext(
                device_type=device_data.get("type", "mobile"),
                platform=device_data.get("platform", "unknown"),
                screen_width=device_data.get("screen_width", 375),
                screen_height=device_data.get("screen_height", 667),
                battery_level=device_data.get("battery_level"),
                network_type=device_data.get("network_type", "wifi")
            )
        
        # Build spatial context
        spatial = None
        if request_context and "location" in request_context:
            loc_data = request_context["location"]
            spatial = SpatialContext(
                latitude=loc_data.get("latitude"),
                longitude=loc_data.get("longitude"),
                city=loc_data.get("city"),
                country=loc_data.get("country")
            )
        
        # Build solution context
        solution_context = SolutionContext(
            solution_id=solution,
            solution_name=solution.replace("ricco-", "").title()
        )
        
        # Build horizontal context
        horizontal = HorizontalContext(
            accessible_solutions=list(request_context.get("permissions", {}).keys()) if request_context else []
        )
        
        # Create bundle
        bundle = (
            ContextBundleBuilder(session_id, user_id)
                .with_personal_context(personal)
                .with_spatial_context(spatial)
                .with_temporal_context(temporal)
                .with_device_context(device)
                .with_solution_context(solution_context)
                .with_horizontal_context(horizontal)
                .with_skills(request_context.get("skills", []) if request_context else [])
                .build()
        )
        
        # Cache the bundle
        if self._context_cache:
            self._context_cache.set(session_id, bundle)
        
        return bundle
    
    async def get_context_bundle(self, session_id: str) -> Optional[ContextBundle]:
        """Get cached context bundle"""
        if self._context_cache:
            return self._context_cache.get(session_id)
        return None


# =============================================================================
# Singleton Instance
# =============================================================================

_a2ui_service: Optional[A2UIService] = None


def get_a2ui_service() -> A2UIService:
    """
    Get A2UI service singleton.
    
    Implements: Singleton Pattern
    """
    global _a2ui_service
    if _a2ui_service is None:
        try:
            from src.config.settings import settings
            _a2ui_service = A2UIService(
                catalog_version=settings.A2UI_CATALOG_VERSION,
                enable_context=True
            )
        except ImportError:
            _a2ui_service = A2UIService()
    return _a2ui_service


def reset_a2ui_service() -> None:
    """Reset singleton instance (useful for testing)"""
    global _a2ui_service
    if _a2ui_service:
        _a2ui_service = None
