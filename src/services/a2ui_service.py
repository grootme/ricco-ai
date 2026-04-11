"""
A2UI Service - Integration with Google A2UI SDK
Uses A2UI SDK from external/A2UI as library
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
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


class A2UIService:
    """A2UI Service for dynamic UI generation"""

    def __init__(self, catalog_version: str = "v0_9"):
        self.catalog_version = catalog_version
        self._catalog: Optional[Any] = None

    async def initialize(self):
        """Initialize A2UI catalog"""
        if A2UI_SDK_AVAILABLE:
            try:
                self._catalog = BasicCatalog()
                logger.info("A2UI catalog initialized")
            except Exception as e:
                logger.error(f"Failed to initialize A2UI: {e}")

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
            "description": "A2UI extension for dynamic UI"
        }

    def parse_llm_response(self, content: str) -> List[Any]:
        """Parse LLM response for A2UI parts"""
        if A2UI_SDK_AVAILABLE and self._catalog:
            return parse_response_to_parts(content, validator=self._catalog.validator)
        return []

    # RICCO-specific UI templates
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


_a2ui_service: Optional[A2UIService] = None


def get_a2ui_service() -> A2UIService:
    """Get A2UI service singleton"""
    global _a2ui_service
    if _a2ui_service is None:
        from src.config.settings import settings
        _a2ui_service = A2UIService(catalog_version=settings.A2UI_CATALOG_VERSION)
    return _a2ui_service
