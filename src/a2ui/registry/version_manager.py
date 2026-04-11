"""
A2UI Version Manager - Component versioning and backward compatibility.
Implements semantic versioning and migration strategies.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
from pydantic import BaseModel, Field
import structlog

logger = structlog.get_logger(__name__)


class VersionChange(str, Enum):
    """Type of version change."""
    MAJOR = "major"      # Breaking changes
    MINOR = "minor"      # New features, backward compatible
    PATCH = "patch"      # Bug fixes, backward compatible
    PRERELEASE = "prerelease"  # Pre-release version


class MigrationType(str, Enum):
    """Type of migration."""
    PROPS_TRANSFORM = "props_transform"
    DEPRECATION_NOTICE = "deprecation_notice"
    BREAKING_CHANGE = "breaking_change"


@dataclass
class SemanticVersion:
    """Semantic version representation."""
    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None
    
    def __str__(self) -> str:
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        return version
    
    def __lt__(self, other: SemanticVersion) -> bool:
        if self.major != other.major:
            return self.major < other.major
        if self.minor != other.minor:
            return self.minor < other.minor
        return self.patch < other.patch
    
    def __le__(self, other: SemanticVersion) -> bool:
        return self == other or self < other
    
    def __gt__(self, other: SemanticVersion) -> bool:
        return not self <= other
    
    def __ge__(self, other: SemanticVersion) -> bool:
        return not self < other
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SemanticVersion):
            return False
        return (
            self.major == other.major and
            self.minor == other.minor and
            self.patch == other.patch
        )
    
    def __hash__(self) -> int:
        return hash((self.major, self.minor, self.patch))
    
    @classmethod
    def parse(cls, version_str: str) -> "SemanticVersion":
        """Parse version string into SemanticVersion."""
        prerelease = None
        if "-" in version_str:
            version_str, prerelease = version_str.split("-", 1)
        
        # Handle 'v' prefix
        if version_str.startswith("v"):
            version_str = version_str[1:]
        
        parts = version_str.split(".")
        return cls(
            major=int(parts[0]) if len(parts) > 0 else 0,
            minor=int(parts[1]) if len(parts) > 1 else 0,
            patch=int(parts[2]) if len(parts) > 2 else 0,
            prerelease=prerelease
        )
    
    def bump(self, change_type: VersionChange) -> "SemanticVersion":
        """Create a new version with the specified bump type."""
        if change_type == VersionChange.MAJOR:
            return SemanticVersion(self.major + 1, 0, 0)
        elif change_type == VersionChange.MINOR:
            return SemanticVersion(self.major, self.minor + 1, 0)
        elif change_type == VersionChange.PATCH:
            return SemanticVersion(self.major, self.minor, self.patch + 1)
        else:
            return self
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "major": self.major,
            "minor": self.minor,
            "patch": self.patch,
            "prerelease": self.prerelease,
            "full": str(self)
        }


class MigrationStep(BaseModel):
    """A single migration step."""
    from_version: str
    to_version: str
    migration_type: MigrationType
    description: str
    props_mapping: Dict[str, Any] = Field(default_factory=dict)
    deprecation_warnings: List[str] = Field(default_factory=list)
    breaking_changes: List[str] = Field(default_factory=list)
    
    def apply(self, props: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """
        Apply migration to props.
        
        Args:
            props: Original props
            
        Returns:
            Tuple of (migrated_props, warnings)
        """
        warnings = []
        migrated = props.copy()
        
        # Apply prop mappings
        for old_key, new_key in self.props_mapping.items():
            if old_key in migrated:
                if isinstance(new_key, str):
                    migrated[new_key] = migrated.pop(old_key)
                elif isinstance(new_key, dict):
                    # Complex mapping with transformation
                    target_key = new_key.get("target", old_key)
                    transform = new_key.get("transform")
                    value = migrated.pop(old_key)
                    
                    if transform == "rename":
                        migrated[target_key] = value
                    elif transform == "flatten" and isinstance(value, dict):
                        migrated.update(value)
                    elif transform == "wrap":
                        migrated[target_key] = {"value": value}
        
        # Add deprecation warnings
        warnings.extend(self.deprecation_warnings)
        
        return migrated, warnings


class ComponentVersion(BaseModel):
    """Version record for a component."""
    component_id: str
    version: str
    released_at: datetime = Field(default_factory=datetime.utcnow)
    changelog: str = ""
    changes: List[str] = Field(default_factory=list)
    deprecations: List[str] = Field(default_factory=list)
    breaking_changes: List[str] = Field(default_factory=list)
    min_compatible_version: Optional[str] = None
    migrations: List[MigrationStep] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "component_id": self.component_id,
            "version": self.version,
            "released_at": self.released_at.isoformat(),
            "changelog": self.changelog,
            "changes": self.changes,
            "deprecations": self.deprecations,
            "breaking_changes": self.breaking_changes,
            "min_compatible_version": self.min_compatible_version,
            "has_migrations": len(self.migrations) > 0
        }


class VersionManager:
    """
    Manages component versions and migrations.
    Implements semantic versioning with backward compatibility.
    """
    
    def __init__(self):
        self._versions: Dict[str, List[ComponentVersion]] = {}
        self._migrations: Dict[str, Dict[str, MigrationStep]] = {}  # component_id -> {from_to: Migration}
        self._compatibility_matrix: Dict[str, Dict[str, List[str]]] = {}
    
    def register_version(self, version: ComponentVersion) -> bool:
        """
        Register a new component version.
        
        Args:
            version: ComponentVersion to register
            
        Returns:
            True if registration successful
        """
        try:
            component_id = version.component_id
            
            if component_id not in self._versions:
                self._versions[component_id] = []
            
            # Check version doesn't already exist
            existing_versions = [v.version for v in self._versions[component_id]]
            if version.version in existing_versions:
                logger.warning(
                    "version_already_exists",
                    component_id=component_id,
                    version=version.version
                )
                return False
            
            # Validate semver
            semver = SemanticVersion.parse(version.version)
            
            # Add to registry
            self._versions[component_id].append(version)
            self._versions[component_id].sort(
                key=lambda v: SemanticVersion.parse(v.version),
                reverse=True
            )
            
            # Register migrations
            for migration in version.migrations:
                self._register_migration(component_id, migration)
            
            logger.info(
                "version_registered",
                component_id=component_id,
                version=version.version
            )
            return True
            
        except Exception as e:
            logger.error("version_registration_failed", error=str(e))
            return False
    
    def _register_migration(self, component_id: str, migration: MigrationStep) -> None:
        """Register a migration step."""
        if component_id not in self._migrations:
            self._migrations[component_id] = {}
        
        key = f"{migration.from_version}->{migration.to_version}"
        self._migrations[component_id][key] = migration
    
    def get_latest_version(self, component_id: str) -> Optional[ComponentVersion]:
        """Get the latest version of a component."""
        versions = self._versions.get(component_id, [])
        return versions[0] if versions else None
    
    def get_version(self, component_id: str, version: str) -> Optional[ComponentVersion]:
        """Get a specific version of a component."""
        versions = self._versions.get(component_id, [])
        for v in versions:
            if v.version == version:
                return v
        return None
    
    def get_all_versions(self, component_id: str) -> List[ComponentVersion]:
        """Get all versions of a component."""
        return self._versions.get(component_id, [])
    
    def is_compatible(
        self,
        component_id: str,
        requested_version: str,
        current_version: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if a requested version is compatible with current version.
        
        Args:
            component_id: Component identifier
            requested_version: Version being requested
            current_version: Currently installed version
            
        Returns:
            Tuple of (is_compatible, error_message)
        """
        requested = SemanticVersion.parse(requested_version)
        current = SemanticVersion.parse(current_version)
        
        # Same version is always compatible
        if requested == current:
            return True, None
        
        # Get min compatible version
        version_record = self.get_version(component_id, requested_version)
        if version_record and version_record.min_compatible_version:
            min_compatible = SemanticVersion.parse(version_record.min_compatible_version)
            if current < min_compatible:
                return False, (
                    f"Version {requested_version} requires minimum version "
                    f"{version_record.min_compatible_version}, but current is {current_version}"
                )
        
        # Major version difference indicates breaking changes
        if requested.major != current.major:
            # Check if there's a migration path
            migration_path = self._find_migration_path(component_id, current_version, requested_version)
            if not migration_path:
                return False, (
                    f"Major version difference ({current_version} -> {requested_version}) "
                    "requires manual migration"
                )
        
        return True, None
    
    def _find_migration_path(
        self,
        component_id: str,
        from_version: str,
        to_version: str
    ) -> Optional[List[MigrationStep]]:
        """Find migration path between two versions."""
        component_migrations = self._migrations.get(component_id, {})
        
        # Direct migration
        key = f"{from_version}->{to_version}"
        if key in component_migrations:
            return [component_migrations[key]]
        
        # TODO: Implement path finding through intermediate versions
        return None
    
    def migrate_props(
        self,
        component_id: str,
        props: Dict[str, Any],
        from_version: str,
        to_version: str
    ) -> Tuple[Dict[str, Any], List[str]]:
        """
        Migrate props from one version to another.
        
        Args:
            component_id: Component identifier
            props: Props to migrate
            from_version: Source version
            to_version: Target version
            
        Returns:
            Tuple of (migrated_props, warnings)
        """
        migration_path = self._find_migration_path(component_id, from_version, to_version)
        
        if not migration_path:
            logger.warning(
                "no_migration_path",
                component_id=component_id,
                from_version=from_version,
                to_version=to_version
            )
            return props, [f"No migration path from {from_version} to {to_version}"]
        
        migrated_props = props.copy()
        all_warnings = []
        
        for migration in migration_path:
            migrated_props, warnings = migration.apply(migrated_props)
            all_warnings.extend(warnings)
        
        return migrated_props, all_warnings
    
    def bump_version(
        self,
        component_id: str,
        change_type: VersionChange,
        changelog: str = "",
        changes: Optional[List[str]] = None,
        breaking_changes: Optional[List[str]] = None,
        deprecations: Optional[List[str]] = None
    ) -> Optional[ComponentVersion]:
        """
        Create a new version by bumping the existing one.
        
        Args:
            component_id: Component to version
            change_type: Type of version bump
            changelog: Version changelog
            changes: List of changes
            breaking_changes: List of breaking changes
            deprecations: List of deprecations
            
        Returns:
            New ComponentVersion or None if failed
        """
        latest = self.get_latest_version(component_id)
        
        if not latest:
            logger.warning("component_not_found", component_id=component_id)
            return None
        
        current = SemanticVersion.parse(latest.version)
        new_version = current.bump(change_type)
        
        new_version_record = ComponentVersion(
            component_id=component_id,
            version=str(new_version),
            changelog=changelog,
            changes=changes or [],
            breaking_changes=breaking_changes or [],
            deprecations=deprecations or [],
            min_compatible_version=str(current) if change_type == VersionChange.MAJOR else None
        )
        
        if self.register_version(new_version_record):
            return new_version_record
        return None
    
    def get_version_history(self, component_id: str) -> List[Dict[str, Any]]:
        """Get version history for a component."""
        versions = self.get_all_versions(component_id)
        return [v.to_dict() for v in versions]
    
    def get_changelog(self, component_id: str, from_version: Optional[str] = None) -> str:
        """
        Get changelog for a component.
        
        Args:
            component_id: Component identifier
            from_version: Optional starting version (returns all if not specified)
            
        Returns:
            Formatted changelog string
        """
        versions = self.get_all_versions(component_id)
        
        if not versions:
            return f"No versions found for {component_id}"
        
        lines = [f"# Changelog for {component_id}\n"]
        
        include_all = from_version is None
        found_start = False
        
        for v in versions:
            if not include_all:
                if v.version == from_version:
                    found_start = True
                    continue
                if not found_start:
                    continue
            
            lines.append(f"\n## [{v.version}] - {v.released_at.strftime('%Y-%m-%d')}\n")
            
            if v.changelog:
                lines.append(f"{v.changelog}\n")
            
            if v.changes:
                lines.append("### Changes\n")
                for change in v.changes:
                    lines.append(f"- {change}")
                lines.append("")
            
            if v.deprecations:
                lines.append("### Deprecations\n")
                for dep in v.deprecations:
                    lines.append(f"- ⚠️ {dep}")
                lines.append("")
            
            if v.breaking_changes:
                lines.append("### Breaking Changes\n")
                for bc in v.breaking_changes:
                    lines.append(f"- 💥 {bc}")
                lines.append("")
        
        return "\n".join(lines)


# Singleton instance
_version_manager: Optional[VersionManager] = None


def get_version_manager() -> VersionManager:
    """Get the singleton version manager instance."""
    global _version_manager
    if _version_manager is None:
        _version_manager = VersionManager()
    return _version_manager
