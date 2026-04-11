"""
A2UI Service - Enhanced Integration with Google A2UI SDK and Context Bundles

This is a fused version combining:
- Original ricco-ai A2UIService (basic UI generation)
- genui A2UIContextService (context-aware UI with Context Bundles)

Features:
- Dynamic UI generation
- Context-aware surfaces
- Theme management
- Multiple UI modes (minimal, standard, detailed, accessibility)
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from enum import Enum
import logging

from loguru import logger

# Add A2UI SDK to path
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


# Context Bundles imports
CONTEXT_BUNDLES_PATH = Path(__file__).parent.parent.parent.parent.parent / "external" / "context_bundles"
if CONTEXT_BUNDLES_PATH.exists():
    sys.path.insert(0, str(CONTEXT_BUNDLES_PATH.parent))

try:
    from context_bundles.context_prompt_builder import (
        ContextPromptBuilder,
        ContextSelection,
        ContextPromptConfig,
        AIModelFormat,
        get_context_prompt_builder
    )
    from context_bundles.context_cache import (
        ContextCache,
        get_context_cache
    )
    CONTEXT_BUNDLE_AVAILABLE = True
except ImportError as e:
    CONTEXT_BUNDLE_AVAILABLE = False
    logger.warning(f"Context Bundle not available for A2UI: {e}")


class UIContextMode(str, Enum):
    """UI generation modes based on context"""
    MINIMAL = "minimal"      # Basic UI, few elements
    STANDARD = "standard"    # Standard UI
    DETAILED = "detailed"    # Detailed UI with more information
    ACCESSIBILITY = "accessibility"  # UI optimized for accessibility


class A2UIService:
    """
    Enhanced A2UI Service with Context Bundle integration.
    
    Combines:
    - Dynamic UI generation (from original ricco-ai)
    - Context-aware surfaces (from genui)
    - Theme management
    """

    def __init__(
        self,
        catalog_version: str = "v0_9",
        enable_context: bool = True
    ):
        """
        Initialize A2UI service with optional context support.
        
        Args:
            catalog_version: A2UI catalog version
            enable_context: Enable Context Bundle integration
        """
        self.catalog_version = catalog_version
        self._catalog: Optional[Any] = None
        self._context_cache: Optional[ContextCache] = None
        self._prompt_builder: Optional[ContextPromptBuilder] = None
        self._enable_context = enable_context and CONTEXT_BUNDLE_AVAILABLE

    async def initialize(self) -> None:
        """Initialize A2UI catalog and Context Bundle"""
        # Initialize A2UI
        if A2UI_SDK_AVAILABLE:
            try:
                self._catalog = BasicCatalog()
                logger.info("A2UI catalog initialized")
            except Exception as e:
                logger.error(f"Failed to initialize A2UI: {e}")

        # Initialize Context Bundle
        if self._enable_context:
            try:
                self._context_cache = get_context_cache()
                await self._context_cache.initialize()
                self._prompt_builder = get_context_prompt_builder()
                logger.info("Context Bundle initialized for A2UI")
            except Exception as e:
                logger.error(f"Failed to initialize Context Bundle: {e}")
                self._enable_context = False

    # =========================================================================
    # Basic Surface Operations (from original ricco-ai)
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
    # Context-Aware Operations (from genui)
    # =========================================================================

    async def create_contextual_surface(
        self,
        surface_id: str,
        user_id: str,
        session_id: str,
        context_bundle: Optional[Dict[str, Any]] = None,
        ui_mode: UIContextMode = UIContextMode.STANDARD
    ) -> List[Dict[str, Any]]:
        """
        Create a context-aware UI surface.
        
        Args:
            surface_id: Surface ID
            user_id: User ID
            session_id: Session ID
            context_bundle: Context bundle (optional)
            ui_mode: UI mode
            
        Returns:
            List of A2UI commands
        """
        commands = []

        # Load context if not provided
        if not context_bundle and self._enable_context:
            context_bundle = await self._load_context(session_id, user_id)

        # Determine theme based on context
        theme = self._get_theme_from_context(context_bundle)

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
        if ui_mode == UIContextMode.MINIMAL:
            components = self._create_minimal_components(surface_id, context_bundle)
        elif ui_mode == UIContextMode.DETAILED:
            components = self._create_detailed_components(surface_id, context_bundle)
        elif ui_mode == UIContextMode.ACCESSIBILITY:
            components = self._create_accessibility_components(surface_id, context_bundle)
        else:
            components = self._create_standard_components(surface_id, context_bundle)

        commands.append({
            "version": self.catalog_version,
            "updateComponents": {
                "surfaceId": surface_id,
                "components": components
            }
        })

        # Initialize data model with context
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

    async def update_with_context(
        self,
        surface_id: str,
        user_id: str,
        context_bundle: Optional[Dict[str, Any]] = None,
        changes: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Update UI based on context changes.
        
        Args:
            surface_id: Surface ID
            user_id: User ID
            context_bundle: Updated context bundle
            changes: Specific changes to apply
            
        Returns:
            List of A2UI commands
        """
        commands = []

        if not context_bundle or not self._enable_context:
            return commands

        # Detect changes relevant to UI
        ui_updates = self._detect_ui_changes(context_bundle, changes)

        if ui_updates:
            commands.append({
                "version": self.catalog_version,
                "updateDataModel": {
                    "surfaceId": surface_id,
                    "path": "/context",
                    "value": ui_updates
                }
            })

        # Check if theme change is needed
        theme_update = self._check_theme_update(context_bundle)
        if theme_update:
            commands.append({
                "version": self.catalog_version,
                "updateTheme": {
                    "surfaceId": surface_id,
                    "theme": theme_update
                }
            })

        return commands

    async def generate_contextual_prompt(
        self,
        context_bundle: Dict[str, Any],
        intent: str
    ) -> str:
        """
        Generate prompt for UI generation based on context.
        
        Args:
            context_bundle: Context bundle
            intent: User intent
            
        Returns:
            Prompt optimized for UI generation
        """
        if not self._prompt_builder:
            return f"Generate UI for: {intent}"

        selection = ContextSelection(
            include_personal=True,
            include_spatial=True,
            include_temporal=True,
            include_device=True,
            include_solution=True,
        )

        config = ContextPromptConfig(
            model_format=AIModelFormat.OPENAI,
            concise_mode=True,
            include_instructions=False
        )

        prompt_data = await self._prompt_builder.build_prompt(
            context_bundle=context_bundle,
            selection=selection,
            config=config
        )

        # Add specific UI instructions
        ui_prompt = f"""Generate A2UI components for the following intent:
{intent}

Context:
{prompt_data['formatted_prompt']}

Generate valid A2UI JSON components."""

        return ui_prompt

    # =========================================================================
    # A2A Integration
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
        """Get A2UI agent extension for A2A"""
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
    # RICCO-specific UI templates
    # =========================================================================

    def create_chat_ui(self, surface_id: str, user_name: str = "User") -> List[Dict]:
        """Create RICCO chat interface"""
        return [
            self.create_surface(surface_id),
            self.update_components(surface_id, [
                {"id": "root", "component": "Column", "children": ["header", "messages", "input"]},
                {"id": "header", "component": "Row", "children": ["avatar", "title"]},
                {"id": "avatar", "component": "Icon", "name": "smart_toy"},
                {"id": "title", "component": "Text", "text": "RICCO AI", "variant": "h6"},
                {"id": "messages", "component": "List", "children": {"path": "/messages", "componentId": "message"}},
                {"id": "input", "component": "TextField", "label": "Message", "value": {"path": "/input"}}
            ]),
            self.update_data_model(surface_id, "/", {"messages": [], "input": ""})
        ]

    def create_kyc_form(self, surface_id: str, kyc_type: str = "individual") -> List[Dict]:
        """Create KYC form for RICCO ID"""
        return [
            self.create_surface(surface_id),
            self.update_components(surface_id, [
                {"id": "root", "component": "Card", "child": "form"},
                {"id": "form", "component": "Column", "children": ["title", "fields", "submit"]},
                {"id": "title", "component": "Text", "text": f"{'Individual' if kyc_type == 'individual' else 'Business'} Verification", "variant": "h5"},
                {"id": "fields", "component": "Column", "children": ["name_field", "id_field"]},
                {"id": "name_field", "component": "TextField", "label": "Full Name", "value": {"path": "/kyc/name"}},
                {"id": "id_field", "component": "TextField", "label": "ID Number", "value": {"path": "/kyc/idNumber"}},
                {"id": "submit", "component": "Button", "child": "submit_text", "variant": "primary", "action": {"event": {"name": "submit_kyc"}}},
                {"id": "submit_text", "component": "Text", "text": "Submit"}
            ]),
            self.update_data_model(surface_id, "/", {"kyc": {}})
        ]

    # =========================================================================
    # Private Helper Methods
    # =========================================================================

    async def _load_context(
        self,
        session_id: str,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Load context from cache"""
        if not self._context_cache:
            return None

        context = await self._context_cache.get_session_context(session_id)
        if context:
            return context

        # Create basic context if not exists
        return {
            "session_id": session_id,
            "user_id": user_id,
            "temporal": {
                "time_of_day": self._get_time_of_day(),
                "is_weekend": datetime.utcnow().weekday() >= 5
            }
        }

    def _get_time_of_day(self) -> str:
        """Get time of day"""
        hour = datetime.utcnow().hour
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 21:
            return "evening"
        return "night"

    def _get_theme_from_context(
        self,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Get theme based on context"""
        theme = {
            "mode": "light",
            "primary": "#1976D2",
            "secondary": "#424242"
        }

        if not context:
            return theme

        # Detect dark mode from device
        device = context.get("device", {})
        if device.get("color_scheme") == "dark":
            theme["mode"] = "dark"
            theme["primary"] = "#90CAF9"
            theme["secondary"] = "#BDBDBD"

        # Adjust for low battery
        if device.get("battery_level", 100) < 20:
            theme["mode"] = "dark"  # Battery saving

        # Adjust for accessibility
        personal = context.get("personal", {})
        if personal.get("preferences", {}).get("high_contrast"):
            theme["primary"] = "#000000"
            theme["secondary"] = "#FFFFFF"

        return theme

    def _create_minimal_components(
        self,
        surface_id: str,
        context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Create minimal components"""
        return [
            {"id": "root", "component": "Column", "children": ["content"]},
            {"id": "content", "component": "Text", "text": {"path": "/content"}}
        ]

    def _create_standard_components(
        self,
        surface_id: str,
        context: Optional[Dict[str, Any]]
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

        # Add location badge if there's location
        if context and context.get("spatial"):
            components.append({
                "id": "location_badge",
                "component": "Chip",
                "label": {"path": "/location"},
                "icon": "location_on"
            })

        return components

    def _create_detailed_components(
        self,
        surface_id: str,
        context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Create detailed components"""
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
        context: Optional[Dict[str, Any]]
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
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Create initial data model"""
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
            temporal = context.get("temporal", {})
            data["context"]["time"] = temporal.get("time_of_day", "")

            spatial = context.get("spatial", {})
            if spatial.get("city"):
                data["context"]["location"] = spatial["city"]

            device = context.get("device", {})
            device_type = device.get("device_type", "mobile")
            data["context"]["device_icon"] = self._get_device_icon(device_type)

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

    def _detect_ui_changes(
        self,
        context: Dict[str, Any],
        changes: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Detect changes relevant to UI"""
        updates = {}

        # Location changes
        if changes and "location" in changes:
            spatial = context.get("spatial", {})
            updates["location"] = spatial.get("city", "")

        # Time changes
        temporal = context.get("temporal", {})
        updates["time"] = temporal.get("time_of_day", "")

        return updates

    def _check_theme_update(
        self,
        context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Check if theme update is needed"""
        device = context.get("device", {})
        current_scheme = device.get("color_scheme")

        if current_scheme:
            return self._get_theme_from_context(context)

        return None


# Singleton instance
_a2ui_service: Optional[A2UIService] = None


def get_a2ui_service() -> A2UIService:
    """Get A2UI service singleton"""
    global _a2ui_service
    if _a2ui_service is None:
        from src.config.settings import settings
        _a2ui_service = A2UIService(catalog_version=settings.A2UI_CATALOG_VERSION)
    return _a2ui_service
