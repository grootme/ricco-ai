"""
Configuration Schemas for RICCO AI.

Pydantic models for database-managed configuration.

This module provides schema definitions for:
- MCPServerConfig: MCP server configurations
- AgentConfig: Agent configurations
- ContextProviderConfig: Context provider configurations
- A2UIComponentConfig: A2UI component configurations

Consolidated: Enums moved to src/shared/enums.py for OCP compliance.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

# Import consolidated enums from single source of truth
try:
    from src.shared.enums import (
        MCPCategory,
        TransportType,
        HealthStatus,
        AgentType,
        AgentCapability,
        ContextType,
        A2UIComponentType,
        A2UIPlatform,
        ToolRiskLevel,
        SubscriptionTier,
    )
except ImportError:
    # Fallback for direct imports
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from shared.enums import (
        MCPCategory,
        TransportType,
        HealthStatus,
        AgentType,
        AgentCapability,
        ContextType,
        A2UIComponentType,
        A2UIPlatform,
        ToolRiskLevel,
        SubscriptionTier,
    )


# ==================== MCP Server Config ====================

# Enums imported from src.shared.enums


class ServerMetadataConfig(BaseModel):
    """Server metadata configuration."""
    version: str = "1.0.0"
    weight: int = Field(default=100, ge=1, le=1000)
    priority: int = Field(default=0, ge=0, le=100)
    tags: List[str] = Field(default_factory=list)
    owner: Optional[str] = None
    documentation_url: Optional[str] = None
    rate_limit_per_minute: Optional[int] = None
    custom: Dict[str, Any] = Field(default_factory=dict)


class MCPServerConfig(BaseModel):
    """
    MCP Server Configuration.
    
    Defines the configuration for an MCP server stored in the database.
    """
    # Identification
    server_id: Optional[str] = None
    name: str
    category: MCPCategory
    description: str = ""
    
    # Connection
    transport: TransportType
    endpoint: str
    
    # Capabilities
    tools: List[str] = Field(default_factory=list)
    capabilities: List[str] = Field(default_factory=list)
    
    # Configuration
    metadata: ServerMetadataConfig = Field(default_factory=ServerMetadataConfig)
    
    # Health status (runtime)
    health_status: HealthStatus = Field(default=HealthStatus.UNKNOWN)
    last_heartbeat: Optional[datetime] = None
    
    # State
    is_enabled: bool = True
    is_active: bool = True
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "name": "filesystem-local",
                "category": "filesystem",
                "description": "Local filesystem operations",
                "transport": "stdio",
                "endpoint": "/usr/local/bin/mcp-filesystem",
                "tools": ["file_read", "file_write", "directory_list"],
                "capabilities": ["read", "write"],
                "metadata": {
                    "version": "1.0.0",
                    "weight": 100,
                },
            }]
        }
    }


class MCPServerConfigCreate(BaseModel):
    """Model for creating a new MCP server config."""
    name: str
    category: MCPCategory
    transport: TransportType
    endpoint: str
    description: str = ""
    tools: List[str] = Field(default_factory=list)
    capabilities: List[str] = Field(default_factory=list)
    metadata: Optional[ServerMetadataConfig] = None
    is_enabled: bool = True


class MCPServerConfigUpdate(BaseModel):
    """Model for updating an MCP server config."""
    name: Optional[str] = None
    description: Optional[str] = None
    endpoint: Optional[str] = None
    tools: Optional[List[str]] = None
    capabilities: Optional[List[str]] = None
    metadata: Optional[ServerMetadataConfig] = None
    is_enabled: Optional[bool] = None
    is_active: Optional[bool] = None
    health_status: Optional[HealthStatus] = None


# ==================== Agent Config ====================

# AgentType and AgentCapability imported from src.shared.enums


class AgentMetadataConfig(BaseModel):
    """Agent metadata configuration."""
    priority: int = Field(default=0, ge=0, le=100)
    is_primary: bool = False
    is_fallback: bool = False
    domain: Optional[str] = None
    requires_disclaimer: bool = False
    supports_visa_payment: bool = False
    supports_crypto: bool = False
    custom: Dict[str, Any] = Field(default_factory=dict)


class AgentConfig(BaseModel):
    """
    Agent Configuration.
    
    Defines the configuration for an AI agent stored in the database.
    """
    # Identification
    agent_id: Optional[str] = None
    agent_type: AgentType
    name: str
    description: str = ""
    
    # Capabilities
    capabilities: List[AgentCapability] = Field(default_factory=list)
    
    # LLM Configuration
    system_prompt: Optional[str] = None
    max_tokens: int = Field(default=4096, ge=1, le=32000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    
    # MCP Integration
    mcp_servers: List[str] = Field(default_factory=list)
    
    # Mixins
    mixins: List[str] = Field(default_factory=list)
    
    # Configuration
    metadata: AgentMetadataConfig = Field(default_factory=AgentMetadataConfig)
    
    # State
    is_enabled: bool = True
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "agent_type": "commerce",
                "name": "Commerce Agent",
                "description": "E-commerce specialist",
                "capabilities": ["order_management", "inventory_check"],
                "system_prompt": "You are a commerce specialist...",
                "mcp_servers": ["ricco-core", "payment-processor"],
            }]
        }
    }


class AgentConfigCreate(BaseModel):
    """Model for creating a new agent config."""
    agent_type: AgentType
    name: str
    description: str = ""
    capabilities: List[AgentCapability] = Field(default_factory=list)
    system_prompt: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7
    mcp_servers: List[str] = Field(default_factory=list)
    mixins: List[str] = Field(default_factory=list)
    metadata: Optional[AgentMetadataConfig] = None
    is_enabled: bool = True


class AgentConfigUpdate(BaseModel):
    """Model for updating an agent config."""
    name: Optional[str] = None
    description: Optional[str] = None
    capabilities: Optional[List[AgentCapability]] = None
    system_prompt: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    mcp_servers: Optional[List[str]] = None
    mixins: Optional[List[str]] = None
    metadata: Optional[AgentMetadataConfig] = None
    is_enabled: Optional[bool] = None


# ==================== Context Provider Config ====================

# ContextType imported from src.shared.enums


class ContextProviderConfigModel(BaseModel):
    """Context provider configuration model."""
    cache_ttl_seconds: int = Field(default=900, ge=0)
    fields: List[str] = Field(default_factory=list)
    requires_consent: bool = False
    max_history_messages: Optional[int] = None
    max_chunks: Optional[int] = None
    min_relevance: Optional[float] = None


class ContextProviderConfig(BaseModel):
    """
    Context Provider Configuration.
    
    Defines the configuration for a context provider stored in the database.
    """
    # Identification
    provider_id: Optional[str] = None
    provider_type: ContextType
    name: str
    description: str = ""
    
    # Context type
    context_type: ContextType
    
    # Source
    source: str  # e.g., "ricco-api", "session", "system", "qdrant"
    
    # Configuration
    config: ContextProviderConfigModel = Field(default_factory=ContextProviderConfigModel)
    
    # Priority (lower = higher priority)
    priority: int = Field(default=10, ge=0)
    
    # State
    is_enabled: bool = True
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "provider_type": "personal",
                "name": "Personal Context Provider",
                "description": "Provides user profile context",
                "context_type": "personal",
                "source": "ricco-api",
                "config": {
                    "cache_ttl_seconds": 900,
                    "fields": ["user_id", "name", "language"],
                },
                "priority": 1,
            }]
        }
    }


class ContextProviderConfigCreate(BaseModel):
    """Model for creating a new context provider config."""
    provider_type: ContextType
    name: str
    description: str = ""
    context_type: ContextType
    source: str
    config: ContextProviderConfigModel = Field(default_factory=ContextProviderConfigModel)
    priority: int = 10
    is_enabled: bool = True


class ContextProviderConfigUpdate(BaseModel):
    """Model for updating a context provider config."""
    name: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = None
    config: Optional[ContextProviderConfigModel] = None
    priority: Optional[int] = None
    is_enabled: Optional[bool] = None


# ==================== A2UI Component Config ====================

# A2UIComponentType and A2UIPlatform imported from src.shared.enums


class A2UIActionConfig(BaseModel):
    """A2UI action configuration."""
    action_type: str
    handler: str
    parameters: Dict[str, Any] = Field(default_factory=dict)


class A2UISchemaConfig(BaseModel):
    """A2UI component schema configuration."""
    properties: Dict[str, Any] = Field(default_factory=dict)
    required: List[str] = Field(default_factory=list)


class A2UIComponentConfig(BaseModel):
    """
    A2UI Component Configuration.
    
    Defines the configuration for an A2UI component stored in the database.
    """
    # Identification
    component_id: Optional[str] = None
    component_type: A2UIComponentType
    name: str
    description: str = ""
    
    # Categorization
    category: str  # e.g., "basic", "commerce", "auth", "navigation"
    
    # Schema
    schema: A2UISchemaConfig = Field(default_factory=A2UISchemaConfig)
    default_props: Dict[str, Any] = Field(default_factory=dict)
    
    # Actions
    actions: List[str] = Field(default_factory=list)
    
    # Platforms
    platforms: List[A2UIPlatform] = Field(default_factory=lambda: [A2UIPlatform.REACT])
    
    # Tags
    tags: List[str] = Field(default_factory=list)
    
    # State
    is_enabled: bool = True
    
    # Version
    version: str = "1.0.0"
    
    # Timestamps
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    model_config = {
        "json_schema_extra": {
            "examples": [{
                "component_type": "product_card",
                "name": "Product Card",
                "description": "Product display card for e-commerce",
                "category": "commerce",
                "schema": {
                    "properties": {
                        "name": {"type": "string"},
                        "price": {"type": "number"},
                    }
                },
                "actions": ["add_to_cart", "view_details"],
                "platforms": ["react", "flutter"],
            }]
        }
    }


class A2UIComponentConfigCreate(BaseModel):
    """Model for creating a new A2UI component config."""
    component_type: A2UIComponentType
    name: str
    description: str = ""
    category: str
    schema: A2UISchemaConfig = Field(default_factory=A2UISchemaConfig)
    default_props: Dict[str, Any] = Field(default_factory=dict)
    actions: List[str] = Field(default_factory=list)
    platforms: List[A2UIPlatform] = Field(default_factory=lambda: [A2UIPlatform.REACT])
    tags: List[str] = Field(default_factory=list)
    is_enabled: bool = True


class A2UIComponentConfigUpdate(BaseModel):
    """Model for updating an A2UI component config."""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    schema: Optional[A2UISchemaConfig] = None
    default_props: Optional[Dict[str, Any]] = None
    actions: Optional[List[str]] = None
    platforms: Optional[List[A2UIPlatform]] = None
    tags: Optional[List[str]] = None
    is_enabled: Optional[bool] = None
    version: Optional[str] = None


# ==================== Export all models ====================

__all__ = [
    # MCP Server Config
    "MCPCategory",
    "TransportType",
    "HealthStatus",
    "ServerMetadataConfig",
    "MCPServerConfig",
    "MCPServerConfigCreate",
    "MCPServerConfigUpdate",
    
    # Agent Config
    "AgentType",
    "AgentCapability",
    "AgentMetadataConfig",
    "AgentConfig",
    "AgentConfigCreate",
    "AgentConfigUpdate",
    
    # Context Provider Config
    "ContextType",
    "ContextProviderConfigModel",
    "ContextProviderConfig",
    "ContextProviderConfigCreate",
    "ContextProviderConfigUpdate",
    
    # A2UI Component Config
    "A2UIComponentType",
    "A2UIPlatform",
    "A2UISchemaConfig",
    "A2UIComponentConfig",
    "A2UIComponentConfigCreate",
    "A2UIComponentConfigUpdate",
]
