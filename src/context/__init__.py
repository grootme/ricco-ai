"""
Context Modules for RICCO AI.

Provides context fusion engine and context bundles for intelligent
context management and user personalization.

Example:
--------
    from ricco_ai.context import ContextFusionEngine, ContextBundle
    
    engine = ContextFusionEngine()
    bundle = await engine.get_context("user123")
    print(bundle.personal.language)
"""

from .engine import (
    ContextFusionEngine,
    ContextBundle,
    PersonalContext,
    SpatialContext,
    TemporalContext,
    DeviceContext,
)
from .bundles import (
    ContextBundleService,
    ContextType,
    get_context_bundle_service,
)

__version__ = "1.0.0"

__all__ = [
    # Engine
    "ContextFusionEngine",
    "ContextBundle",
    "PersonalContext",
    "SpatialContext",
    "TemporalContext",
    "DeviceContext",
    # Bundles
    "ContextBundleService",
    "ContextType",
    "get_context_bundle_service",
]
