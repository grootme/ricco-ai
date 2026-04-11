"""
RICCO AI Service - Context Engineering Module
Sistema de ingeniería de contexto para agentes de IA personalizados
"""

from app.context.context_engineering_service import (
    ContextEngineeringService,
    ContextBundle,
    ContextType,
    
    # Context Models
    PersonalContext,
    SpatialContext,
    TemporalContext,
    DeviceContext,
    SolutionContext,
    HorizontalContext,
    VerticalContext,
    SkillsContext,
    ConversationContext,
    
    # Service getter
    get_context_service,
)

__all__ = [
    "ContextEngineeringService",
    "ContextBundle",
    "ContextType",
    "PersonalContext",
    "SpatialContext",
    "TemporalContext",
    "DeviceContext",
    "SolutionContext",
    "HorizontalContext",
    "VerticalContext",
    "SkillsContext",
    "ConversationContext",
    "get_context_service",
]
