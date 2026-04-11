"""
A2UI Modules for RICCO AI.

Provides AI-powered UI generation with streaming support.

Example:
--------
    from ricco_ai.a2ui import A2UIService, GenerationOptions, Platform
    
    service = A2UIService()
    response = await service.generate(
        "Create a product card",
        options=GenerationOptions(platform=Platform.REACT),
    )
"""

from .service import A2UIService, A2UIComponent, A2UIResponse
from .streaming import SSEHandler, WebSocketHandler, StreamingEvent
from .registry import ComponentRegistry, ThemeSystem, ComponentDefinition

__version__ = "1.0.0"

__all__ = [
    # Service
    "A2UIService",
    "A2UIComponent",
    "A2UIResponse",
    # Streaming
    "SSEHandler",
    "WebSocketHandler",
    "StreamingEvent",
    # Registry
    "ComponentRegistry",
    "ThemeSystem",
    "ComponentDefinition",
]
