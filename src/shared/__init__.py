"""
Shared module for RICCO AI.

This module provides consolidated, OCP-compliant abstractions:
- enums: All shared enumerations in a single source of truth
- registry: Base registry pattern for extensible component registration
"""

from .enums import (
    # AI Provider
    AIProviderType,
    
    # Agent
    AgentType,
    AgentCapability,
    AgentState,
    SkillLevel,
    
    # MCP
    MCPCategory,
    TransportType,
    HealthStatus,
    ToolRiskLevel,
    
    # Skills
    SkillCategory,
    SkillStatus,
    
    # Context
    ContextType,
    
    # UI
    UIContextMode,
    A2UIComponentType,
    A2UIPlatform,
    
    # Subscription
    SubscriptionTier,
    
    # Streaming
    ConnectionType,
    StreamEventType,
    
    # Blueprint
    BlueprintType,
    BlueprintStatus,
)

from .registry import (
    EntityRegistry,
    RegistryEntry,
    registry,
)

__all__ = [
    # Enums
    "AIProviderType",
    "AgentType",
    "AgentCapability",
    "AgentState",
    "SkillLevel",
    "MCPCategory",
    "TransportType",
    "HealthStatus",
    "ToolRiskLevel",
    "SkillCategory",
    "SkillStatus",
    "ContextType",
    "UIContextMode",
    "A2UIComponentType",
    "A2UIPlatform",
    "SubscriptionTier",
    "ConnectionType",
    "StreamEventType",
    "BlueprintType",
    "BlueprintStatus",
    
    # Registry
    "EntityRegistry",
    "RegistryEntry",
    "registry",
]
