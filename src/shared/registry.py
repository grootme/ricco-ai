"""
Consolidated Entity Registry for RICCO AI.

UNIFIED REGISTRY PATTERN - Single source of truth for all registries.

Principles applied:
- ELIMINAR antes de CREAR: Removed duplicate registry implementations
- CONSOLIDAR antes de DIVIDIR: Single registry pattern for all entities
- OCP: Entities defined in configuration, not hardcoded

This replaces fragmented registries:
- mcp/registry/skill_registry.py -> SkillsRegistry
- mcp/registry/tool_registry.py -> ToolsRegistry
- mcp/registry/server_registry.py -> ServersRegistry
- iovba/action/skills_registry.py -> SkillsRegistry (duplicate)
- iovba/action/mcp_registry.py -> MCPRegistry (duplicate)
- blueprints/registry.py -> BlueprintRegistry
- a2ui/registry/ -> ComponentRegistry, ThemeRegistry, VersionRegistry
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar, Callable, Protocol
from enum import Enum
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)


# Type variable for entity
T = TypeVar('T')


@dataclass
class RegistryEntry:
    """
    Base entry for all registry items.
    
    Consolidates common fields from:
    - SkillMetadata
    - ServerConfig
    - AgentConfig
    - ComponentConfig
    """
    id: str
    name: str
    description: str = ""
    category: Optional[str] = None
    version: str = "1.0.0"
    status: str = "active"
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "version": self.version,
            "status": self.status,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class EntityRegistry(Generic[T]):
    """
    Generic, OCP-compliant registry for any entity type.
    
    Features:
    - Configuration-driven registration
    - Category-based organization
    - Tag-based indexing
    - Search functionality
    - Event hooks for registration
    
    OCP-Compliant: Entities loaded from configuration files.
    """
    
    def __init__(self, entity_type: str):
        self._entity_type = entity_type
        self._entities: Dict[str, RegistryEntry] = {}
        self._by_category: Dict[str, List[str]] = {}
        self._by_tag: Dict[str, List[str]] = {}
        self._hooks: Dict[str, List[Callable]] = {
            "on_register": [],
            "on_unregister": [],
        }
    
    def register(self, entry: RegistryEntry) -> None:
        """Register an entity."""
        self._entities[entry.id] = entry
        
        # Index by category
        if entry.category:
            if entry.category not in self._by_category:
                self._by_category[entry.category] = []
            if entry.id not in self._by_category[entry.category]:
                self._by_category[entry.category].append(entry.id)
        
        # Index by tags
        for tag in entry.tags:
            if tag not in self._by_tag:
                self._by_tag[tag] = []
            if entry.id not in self._by_tag[tag]:
                self._by_tag[tag].append(entry.id)
        
        # Trigger hooks
        for hook in self._hooks["on_register"]:
            try:
                hook(entry)
            except Exception as e:
                logger.error(f"Hook error for {entry.id}: {e}")
        
        logger.debug(f"Registered {self._entity_type}: {entry.name} ({entry.id})")
    
    def unregister(self, entity_id: str) -> bool:
        """Unregister an entity."""
        if entity_id not in self._entities:
            return False
        
        entry = self._entities[entity_id]
        
        # Remove from category index
        if entry.category and entry.category in self._by_category:
            self._by_category[entry.category] = [
                id for id in self._by_category[entry.category] if id != entity_id
            ]
        
        # Remove from tag indexes
        for tag in entry.tags:
            if tag in self._by_tag:
                self._by_tag[tag] = [
                    id for id in self._by_tag[tag] if id != entity_id
                ]
        
        # Trigger hooks
        for hook in self._hooks["on_unregister"]:
            try:
                hook(entry)
            except Exception as e:
                logger.error(f"Hook error for {entity_id}: {e}")
        
        del self._entities[entity_id]
        logger.debug(f"Unregistered {self._entity_type}: {entity_id}")
        return True
    
    def get(self, entity_id: str) -> Optional[RegistryEntry]:
        """Get an entity by ID."""
        return self._entities.get(entity_id)
    
    def get_by_name(self, name: str) -> Optional[RegistryEntry]:
        """Get an entity by name."""
        for entry in self._entities.values():
            if entry.name.lower() == name.lower():
                return entry
        return None
    
    def list_all(self) -> List[RegistryEntry]:
        """List all entities."""
        return list(self._entities.values())
    
    def list_by_category(self, category: str) -> List[RegistryEntry]:
        """List entities by category."""
        ids = self._by_category.get(category, [])
        return [self._entities[id] for id in ids if id in self._entities]
    
    def list_by_tag(self, tag: str) -> List[RegistryEntry]:
        """List entities by tag."""
        ids = self._by_tag.get(tag, [])
        return [self._entities[id] for id in ids if id in self._entities]
    
    def search(self, query: str) -> List[RegistryEntry]:
        """Search entities by name, description, or tags."""
        query = query.lower()
        results = []
        
        for entry in self._entities.values():
            if (
                query in entry.name.lower() or
                query in entry.description.lower() or
                any(query in tag.lower() for tag in entry.tags)
            ):
                results.append(entry)
        
        return results
    
    def add_hook(self, event: str, callback: Callable) -> None:
        """Add a callback hook for events."""
        if event in self._hooks:
            self._hooks[event].append(callback)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        return {
            "entity_type": self._entity_type,
            "total_entities": len(self._entities),
            "by_category": {
                cat: len(ids) for cat, ids in self._by_category.items()
            },
            "total_tags": len(self._by_tag),
        }
    
    def load_from_config(self, config_path: Path) -> int:
        """
        Load entities from configuration file.
        
        OCP-Compliant: Entities defined in JSON/YAML, not hardcoded.
        
        Returns number of entities loaded.
        """
        if not config_path.exists():
            logger.warning(f"Config file not found: {config_path}")
            return 0
        
        with open(config_path) as f:
            if config_path.suffix == ".json":
                config = json.load(f)
            else:
                # Assume YAML
                import yaml
                config = yaml.safe_load(f)
        
        entities = config.get("entities", [])
        count = 0
        
        for entity_data in entities:
            try:
                entry = RegistryEntry(
                    id=entity_data.get("id"),
                    name=entity_data.get("name"),
                    description=entity_data.get("description", ""),
                    category=entity_data.get("category"),
                    version=entity_data.get("version", "1.0.0"),
                    status=entity_data.get("status", "active"),
                    tags=entity_data.get("tags", []),
                    metadata=entity_data.get("metadata", {}),
                )
                self.register(entry)
                count += 1
            except Exception as e:
                logger.error(f"Error loading entity: {e}")
        
        logger.info(f"Loaded {count} {self._entity_type} entities from {config_path}")
        return count
    
    def export_to_config(self, config_path: Path) -> None:
        """Export entities to configuration file."""
        config = {
            "entity_type": self._entity_type,
            "entities": [entry.to_dict() for entry in self._entities.values()],
        }
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2, default=str)
        
        logger.info(f"Exported {len(self._entities)} {self._entity_type} entities to {config_path}")


# =============================================================================
# GLOBAL REGISTRIES - Single source of truth
# =============================================================================

# Main unified registry that holds all sub-registries
class GlobalRegistry:
    """
    Global registry container for all entity types.
    
    Single point of access for all registries.
    """
    
    _instance: Optional['GlobalRegistry'] = None
    
    def __new__(cls) -> 'GlobalRegistry':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._registries: Dict[str, EntityRegistry] = {}
            cls._instance._initialized = False
        return cls._instance
    
    def get_registry(self, entity_type: str) -> EntityRegistry:
        """Get or create a registry for an entity type."""
        if entity_type not in self._registries:
            self._registries[entity_type] = EntityRegistry(entity_type)
        return self._registries[entity_type]
    
    @property
    def skills(self) -> EntityRegistry:
        """Skills registry."""
        return self.get_registry("skill")
    
    @property
    def tools(self) -> EntityRegistry:
        """Tools registry."""
        return self.get_registry("tool")
    
    @property
    def servers(self) -> EntityRegistry:
        """MCP servers registry."""
        return self.get_registry("server")
    
    @property
    def agents(self) -> EntityRegistry:
        """Agents registry."""
        return self.get_registry("agent")
    
    @property
    def blueprints(self) -> EntityRegistry:
        """Blueprints registry."""
        return self.get_registry("blueprint")
    
    @property
    def components(self) -> EntityRegistry:
        """A2UI components registry."""
        return self.get_registry("component")
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get statistics for all registries."""
        return {
            entity_type: registry.get_stats()
            for entity_type, registry in self._registries.items()
        }
    
    def load_all_from_config(self, config_dir: Path) -> None:
        """Load all registries from configuration directory."""
        config_files = {
            "skill": config_dir / "skills.json",
            "tool": config_dir / "tools.json",
            "server": config_dir / "servers.json",
            "agent": config_dir / "agents.json",
            "blueprint": config_dir / "blueprints.json",
            "component": config_dir / "components.json",
        }
        
        for entity_type, config_path in config_files.items():
            if config_path.exists():
                registry = self.get_registry(entity_type)
                registry.load_from_config(config_path)


# Global registry instance
registry = GlobalRegistry()


__all__ = [
    "RegistryEntry",
    "EntityRegistry",
    "GlobalRegistry",
    "registry",
]
