"""
A2UI Registry Module for RICCO AI.

Component registry with schema validation and theme management.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class ComponentStatus(str, Enum):
    """Status of a registered component."""
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class ComponentDefinition(BaseModel):
    """Definition of a registered component."""
    component_id: str
    name: str
    description: str
    category: str
    schema: Dict[str, Any] = Field(default_factory=dict)
    default_props: Dict[str, Any] = Field(default_factory=dict)
    actions: List[str] = Field(default_factory=list)
    platforms: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    status: ComponentStatus = ComponentStatus.ACTIVE
    version: str = "1.0.0"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ComponentVersion(BaseModel):
    """Version information for a component."""
    component_id: str
    version: str
    changes: List[str] = Field(default_factory=list)
    released_at: datetime = Field(default_factory=datetime.utcnow)
    deprecated: bool = False


class ThemeDefinition(BaseModel):
    """Theme definition with design tokens."""
    theme_id: str
    name: str
    description: str = ""
    
    # Design tokens
    colors: Dict[str, str] = Field(default_factory=dict)
    typography: Dict[str, Any] = Field(default_factory=dict)
    spacing: Dict[str, str] = Field(default_factory=dict)
    borders: Dict[str, Any] = Field(default_factory=dict)
    shadows: Dict[str, str] = Field(default_factory=dict)
    
    # Custom tokens
    custom: Dict[str, Any] = Field(default_factory=dict)
    
    is_default: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


class JSONSchema(BaseModel):
    """JSON Schema for component validation."""
    type: str = "object"
    properties: Dict[str, Any] = Field(default_factory=dict)
    required: List[str] = Field(default_factory=list)
    additional_properties: bool = True


class ComponentSchemaRegistry:
    """Registry for component JSON schemas."""
    
    def __init__(self):
        self._schemas: Dict[str, JSONSchema] = {}
        self._load_default_schemas()
    
    def _load_default_schemas(self) -> None:
        """Load default component schemas."""
        # Button schema
        self._schemas["button"] = JSONSchema(
            type="object",
            properties={
                "label": {"type": "string"},
                "variant": {"type": "string", "enum": ["primary", "secondary", "outline"]},
                "size": {"type": "string", "enum": ["small", "medium", "large"]},
                "disabled": {"type": "boolean"},
            },
            required=["label"],
        )
        
        # Card schema
        self._schemas["card"] = JSONSchema(
            type="object",
            properties={
                "title": {"type": "string"},
                "subtitle": {"type": "string"},
                "image": {"type": "string"},
                "content": {"type": "string"},
            },
            required=["title"],
        )
        
        # Form schema
        self._schemas["form"] = JSONSchema(
            type="object",
            properties={
                "fields": {"type": "array"},
                "submit_label": {"type": "string"},
            },
            required=["fields"],
        )
    
    def register(self, component_type: str, schema: JSONSchema) -> None:
        """Register a schema for a component type."""
        self._schemas[component_type] = schema
    
    def get(self, component_type: str) -> Optional[JSONSchema]:
        """Get schema for a component type."""
        return self._schemas.get(component_type)
    
    def validate(self, component_type: str, data: Dict[str, Any]) -> List[str]:
        """Validate data against a component schema."""
        schema = self._schemas.get(component_type)
        if not schema:
            return []
        
        errors = []
        
        # Check required fields
        for field in schema.required:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        return errors


class ComponentRegistry:
    """
    Registry for UI components.
    
    Provides:
    - Component registration and discovery
    - Schema validation
    - Version management
    """
    
    def __init__(self):
        self._components: Dict[str, ComponentDefinition] = {}
        self._versions: Dict[str, List[ComponentVersion]] = {}
        self._schema_registry = ComponentSchemaRegistry()
    
    def register(self, definition: ComponentDefinition) -> None:
        """Register a component definition."""
        self._components[definition.component_id] = definition
        logger.info(f"Registered component: {definition.name}")
    
    def unregister(self, component_id: str) -> bool:
        """Unregister a component."""
        if component_id in self._components:
            del self._components[component_id]
            return True
        return False
    
    def get(self, component_id: str) -> Optional[ComponentDefinition]:
        """Get a component by ID."""
        return self._components.get(component_id)
    
    def get_by_name(self, name: str) -> Optional[ComponentDefinition]:
        """Get a component by name."""
        for comp in self._components.values():
            if comp.name == name:
                return comp
        return None
    
    def get_by_category(self, category: str) -> List[ComponentDefinition]:
        """Get all components in a category."""
        return [
            comp for comp in self._components.values()
            if comp.category == category and comp.status == ComponentStatus.ACTIVE
        ]
    
    def search(self, query: str) -> List[ComponentDefinition]:
        """Search components by name, description, or tags."""
        query_lower = query.lower()
        results = []
        
        for comp in self._components.values():
            if comp.status != ComponentStatus.ACTIVE:
                continue
            
            if (
                query_lower in comp.name.lower() or
                query_lower in comp.description.lower() or
                any(query_lower in tag.lower() for tag in comp.tags)
            ):
                results.append(comp)
        
        return results
    
    def validate_component(
        self,
        component_type: str,
        data: Dict[str, Any],
    ) -> List[str]:
        """Validate component data against schema."""
        return self._schema_registry.validate(component_type, data)
    
    def get_all(self) -> List[ComponentDefinition]:
        """Get all registered components."""
        return list(self._components.values())
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics."""
        categories: Dict[str, int] = {}
        for comp in self._components.values():
            categories[comp.category] = categories.get(comp.category, 0) + 1
        
        return {
            "total_components": len(self._components),
            "by_category": categories,
            "by_status": {
                status.value: len([
                    c for c in self._components.values()
                    if c.status == status
                ])
                for status in ComponentStatus
            },
        }


class ThemeManager:
    """
    Manager for UI themes.
    
    Provides:
    - Theme registration and retrieval
    - Design token management
    - Theme inheritance
    """
    
    def __init__(self):
        self._themes: Dict[str, ThemeDefinition] = {}
        self._load_default_themes()
    
    def _load_default_themes(self) -> None:
        """Load default themes."""
        # Light theme
        self._themes["light"] = ThemeDefinition(
            theme_id="light",
            name="Light Theme",
            is_default=True,
            colors={
                "primary": "#3B82F6",
                "secondary": "#6B7280",
                "background": "#FFFFFF",
                "surface": "#F3F4F6",
                "text": "#1F2937",
                "text_secondary": "#6B7280",
                "border": "#E5E7EB",
                "error": "#EF4444",
                "success": "#10B981",
                "warning": "#F59E0B",
            },
            typography={
                "font_family": "Inter, sans-serif",
                "heading_size": "24px",
                "body_size": "16px",
                "small_size": "14px",
            },
            spacing={
                "xs": "4px",
                "sm": "8px",
                "md": "16px",
                "lg": "24px",
                "xl": "32px",
            },
        )
        
        # Dark theme
        self._themes["dark"] = ThemeDefinition(
            theme_id="dark",
            name="Dark Theme",
            colors={
                "primary": "#60A5FA",
                "secondary": "#9CA3AF",
                "background": "#111827",
                "surface": "#1F2937",
                "text": "#F9FAFB",
                "text_secondary": "#9CA3AF",
                "border": "#374151",
                "error": "#F87171",
                "success": "#34D399",
                "warning": "#FBBF24",
            },
        )
    
    def register(self, theme: ThemeDefinition) -> None:
        """Register a theme."""
        self._themes[theme.theme_id] = theme
        logger.info(f"Registered theme: {theme.name}")
    
    def get(self, theme_id: str) -> Optional[ThemeDefinition]:
        """Get a theme by ID."""
        return self._themes.get(theme_id)
    
    def get_default(self) -> ThemeDefinition:
        """Get the default theme."""
        for theme in self._themes.values():
            if theme.is_default:
                return theme
        return list(self._themes.values())[0]
    
    def get_all(self) -> List[ThemeDefinition]:
        """Get all registered themes."""
        return list(self._themes.values())
    
    def apply_overrides(
        self,
        base_theme_id: str,
        overrides: Dict[str, Any],
    ) -> ThemeDefinition:
        """Create a new theme with overrides."""
        base = self._themes.get(base_theme_id)
        if not base:
            raise ValueError(f"Base theme not found: {base_theme_id}")
        
        # Create new theme with overrides
        new_theme = base.model_copy()
        new_theme.theme_id = f"{base_theme_id}_custom"
        new_theme.name = f"{base.name} (Custom)"
        new_theme.is_default = False
        
        # Apply overrides
        if "colors" in overrides:
            new_theme.colors.update(overrides["colors"])
        if "typography" in overrides:
            new_theme.typography.update(overrides["typography"])
        if "spacing" in overrides:
            new_theme.spacing.update(overrides["spacing"])
        
        return new_theme
