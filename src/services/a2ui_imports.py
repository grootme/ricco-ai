"""
A2UI Service - Backward Compatibility Layer

This module provides backward compatibility for code importing from the old locations.
All imports are redirected to the new consolidated a2ui module.
"""

# Re-export everything from the new consolidated module
from src.services.a2ui import (
    # Service
    A2UIService,
    get_a2ui_service,
    # Component Models
    ComponentType,
    InteractionType,
    ResponseStatus,
    ComponentStyle,
    ComponentAction,
    ComponentValidation,
    A2UIComponent,
    A2UIResponse,
    A2UIState,
    # Context Models
    PersonalContext,
    SpatialContext,
    TemporalContext,
    DeviceContext,
    SolutionContext,
    HorizontalContext,
    VerticalContext,
    ContextBundle,
    UIContextMode,
    # Templates
    ChatUITemplate,
    KYCFormTemplate,
    ProductSearchTemplate,
    OrderStatusTemplate,
    TrackingTemplate,
)

__all__ = [
    # Service
    'A2UIService',
    'get_a2ui_service',
    # Component Models
    'ComponentType',
    'InteractionType',
    'ResponseStatus',
    'ComponentStyle',
    'ComponentAction',
    'ComponentValidation',
    'A2UIComponent',
    'A2UIResponse',
    'A2UIState',
    # Context Models
    'PersonalContext',
    'SpatialContext',
    'TemporalContext',
    'DeviceContext',
    'SolutionContext',
    'HorizontalContext',
    'VerticalContext',
    'ContextBundle',
    'UIContextMode',
    # Templates
    'ChatUITemplate',
    'KYCFormTemplate',
    'ProductSearchTemplate',
    'OrderStatusTemplate',
    'TrackingTemplate',
]
