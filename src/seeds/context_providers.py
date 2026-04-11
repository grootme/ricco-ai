"""
Context Provider Seeds for RICCO AI.

Database-managed context provider configurations.
"""

from typing import Any, Dict, List

# Context provider seed data
CONTEXT_PROVIDER_SEEDS: List[Dict[str, Any]] = [
    # Personal Context
    {
        "provider_id": "personal-context",
        "provider_type": "personal",
        "name": "Personal Context Provider",
        "description": "Provides user profile and preferences context",
        "context_type": "personal",
        "source": "ricco-api",
        "config": {
            "cache_ttl_seconds": 900,
            "fields": [
                "user_id", "name", "language", "timezone",
                "preferences", "trust_score", "energy_points",
            ],
        },
        "priority": 1,
        "is_enabled": True,
    },
    
    # Spatial Context
    {
        "provider_id": "spatial-context",
        "provider_type": "spatial",
        "name": "Spatial Context Provider",
        "description": "Provides location and geographic context",
        "context_type": "spatial",
        "source": "ricco-api",
        "config": {
            "cache_ttl_seconds": 300,
            "fields": [
                "latitude", "longitude", "city", "country", "region",
            ],
            "requires_consent": True,
        },
        "priority": 2,
        "is_enabled": True,
    },
    
    # Temporal Context
    {
        "provider_id": "temporal-context",
        "provider_type": "temporal",
        "name": "Temporal Context Provider",
        "description": "Provides time and date context",
        "context_type": "temporal",
        "source": "system",
        "config": {
            "cache_ttl_seconds": 60,
            "fields": [
                "timestamp", "timezone", "is_weekend", "time_of_day",
            ],
        },
        "priority": 0,
        "is_enabled": True,
    },
    
    # Device Context
    {
        "provider_id": "device-context",
        "provider_type": "device",
        "name": "Device Context Provider",
        "description": "Provides device and platform context",
        "context_type": "device",
        "source": "session",
        "config": {
            "cache_ttl_seconds": 3600,
            "fields": [
                "device_id", "device_type", "platform",
                "app_version", "screen_size",
            ],
        },
        "priority": 3,
        "is_enabled": True,
    },
    
    # Solution Context
    {
        "provider_id": "solution-context",
        "provider_type": "solution",
        "name": "Solution Context Provider",
        "description": "Provides solution-specific context",
        "context_type": "solution",
        "source": "ricco-api",
        "config": {
            "cache_ttl_seconds": 1800,
            "fields": [
                "solution_id", "solution_type",
                "active_features", "configuration",
            ],
        },
        "priority": 2,
        "is_enabled": True,
    },
    
    # Horizontal Context
    {
        "provider_id": "horizontal-context",
        "provider_type": "horizontal",
        "name": "Horizontal Context Provider",
        "description": "Provides cross-cutting context (Energy Points, Trust Score)",
        "context_type": "horizontal",
        "source": "ricco-api",
        "config": {
            "cache_ttl_seconds": 300,
            "fields": [
                "energy_points_balance", "trust_score",
                "subscription_tier", "notification_preferences",
            ],
        },
        "priority": 1,
        "is_enabled": True,
    },
    
    # Vertical Context
    {
        "provider_id": "vertical-context",
        "provider_type": "vertical",
        "name": "Vertical Context Provider",
        "description": "Provides domain-specific context",
        "context_type": "vertical",
        "source": "ricco-api",
        "config": {
            "cache_ttl_seconds": 900,
            "fields": [
                "domain", "industry", "regulations", "custom_data",
            ],
        },
        "priority": 3,
        "is_enabled": True,
    },
    
    # Skills Context
    {
        "provider_id": "skills-context",
        "provider_type": "skills",
        "name": "Skills Context Provider",
        "description": "Provides AI skills and capabilities context",
        "context_type": "skills",
        "source": "mcp-registry",
        "config": {
            "cache_ttl_seconds": 1800,
            "fields": [
                "enabled_skills", "skill_levels", "available_tools",
            ],
        },
        "priority": 4,
        "is_enabled": True,
    },
    
    # RAG Context
    {
        "provider_id": "rag-context",
        "provider_type": "rag",
        "name": "RAG Context Provider",
        "description": "Provides retrieval-augmented generation context",
        "context_type": "rag",
        "source": "qdrant",
        "config": {
            "cache_ttl_seconds": 600,
            "fields": [
                "documents", "relevance_scores", "total_chunks",
            ],
            "max_chunks": 10,
            "min_relevance": 0.7,
        },
        "priority": 5,
        "is_enabled": True,
    },
    
    # Conversation Context
    {
        "provider_id": "conversation-context",
        "provider_type": "conversation",
        "name": "Conversation Context Provider",
        "description": "Provides current conversation state",
        "context_type": "conversation",
        "source": "session",
        "config": {
            "cache_ttl_seconds": 0,  # No cache - always fresh
            "fields": [
                "message_history", "intent", "entities",
                "sentiment", "conversation_state",
            ],
            "max_history_messages": 20,
        },
        "priority": 0,
        "is_enabled": True,
    },
]


def get_providers_by_type(provider_type: str) -> List[Dict[str, Any]]:
    """Get all providers of a specific type."""
    return [
        provider for provider in CONTEXT_PROVIDER_SEEDS
        if provider["provider_type"] == provider_type
    ]


def get_enabled_providers() -> List[Dict[str, Any]]:
    """Get all enabled providers."""
    return [
        provider for provider in CONTEXT_PROVIDER_SEEDS
        if provider.get("is_enabled", True)
    ]


def get_providers_by_priority() -> List[Dict[str, Any]]:
    """Get providers sorted by priority (lowest first)."""
    return sorted(
        get_enabled_providers(),
        key=lambda p: p.get("priority", 10)
    )


def get_all_provider_types() -> List[str]:
    """Get all unique provider types."""
    return list(set(provider["provider_type"] for provider in CONTEXT_PROVIDER_SEEDS))
