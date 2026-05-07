"""
A2UI Service Module
Consolidated and refactored from multiple implementations
"""

from .service import A2UIService, get_a2ui_service
from .models import (
    ComponentType, InteractionType, ResponseStatus,
    ComponentStyle, ComponentAction, ComponentValidation,
    A2UIComponent, A2UIResponse, A2UIState
)
from .context_models import (
    PersonalContext, SpatialContext, TemporalContext,
    DeviceContext, SolutionContext, HorizontalContext,
    VerticalContext, ContextBundle, UIContextMode
)
from .templates import (
    ChatUITemplate, KYCFormTemplate, ProductSearchTemplate,
    OrderStatusTemplate, TrackingTemplate
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
