"""
RICCO AI Service - Integrations Module
Integraciones con frameworks de UI y servicios externos
"""

from app.integrations.flutter_genui_sdk import (
    GenUIService,
    FlutterWidget,
    FlutterAction,
    FlutterWidgetType,
    get_genui_service,
    create_flutter_response,
)

from app.integrations.react_renderer import (
    ReactRendererService,
    ReactComponent,
    ReactAction,
    ReactStyle,
    ReactComponentType,
    get_react_renderer,
    create_react_response,
    generate_commerce_homepage,
    generate_health_dashboard,
    generate_order_tracking,
)

__all__ = [
    # Flutter/GenUI
    "GenUIService",
    "FlutterWidget",
    "FlutterAction",
    "FlutterWidgetType",
    "get_genui_service",
    "create_flutter_response",
    
    # React
    "ReactRendererService",
    "ReactComponent",
    "ReactAction",
    "ReactStyle",
    "ReactComponentType",
    "get_react_renderer",
    "create_react_response",
    "generate_commerce_homepage",
    "generate_health_dashboard",
    "generate_order_tracking",
]
