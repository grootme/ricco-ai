"""Centralized Skill Registry for NVIDIA Blueprint integration.

Provides a unified registry for all skills with discovery,
categorization, and metadata management.

Consolidated: Uses shared enums and registry pattern.
Configuration-driven: Skills loaded from JSON config.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
import json
from pathlib import Path

# Import consolidated enums from single source of truth
try:
    from src.shared.enums import SkillCategory, SkillStatus
except ImportError:
    # Fallback for direct imports
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from shared.enums import SkillCategory, SkillStatus

logger = logging.getLogger(__name__)


# Enums imported from src.shared.enums


@dataclass
class SkillMetadata:
    """Metadata for a skill."""
    skill_id: str
    name: str
    description: str
    version: str = "1.0.0"
    category: SkillCategory = SkillCategory.AI
    status: SkillStatus = SkillStatus.ACTIVE
    author: str = ""
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    documentation_url: str = ""
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "category": self.category.value,
            "status": self.status.value,
            "author": self.author,
            "tags": self.tags,
            "dependencies": self.dependencies,
            "tools": self.tools,
            "examples": self.examples,
            "documentation_url": self.documentation_url,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }


class SkillRegistry:
    """
    Centralized registry for all skills.
    
    Provides:
    - Skill registration and discovery
    - Category-based organization
    - Search functionality
    - Dependency tracking
    """
    
    def __init__(self):
        self._skills: Dict[str, SkillMetadata] = {}
        self._by_category: Dict[SkillCategory, List[str]] = {
            cat: [] for cat in SkillCategory
        }
        self._by_tag: Dict[str, List[str]] = {}
        self._tool_to_skill: Dict[str, str] = {}
        
        # Initialize with skills from configuration (OCP-compliant)
        self._load_skills_from_config()
    
    def _load_skills_from_config(self) -> None:
        """
        Load skills from configuration file.
        
        OCP-Compliant: Skills defined in JSON config, not hardcoded.
        Fallback to built-in skills if config not found.
        """
        config_path = Path(__file__).parent.parent.parent / "shared" / "data" / "skills.json"
        
        if config_path.exists():
            try:
                with open(config_path) as f:
                    config = json.load(f)
                
                for skill_data in config.get("entities", []):
                    metadata = skill_data.get("metadata", {})
                    skill = SkillMetadata(
                        skill_id=skill_data.get("id"),
                        name=skill_data.get("name"),
                        description=skill_data.get("description", ""),
                        category=SkillCategory.from_string(skill_data.get("category", "ai")),
                        tags=skill_data.get("tags", []),
                        tools=metadata.get("tools", []),
                    )
                    self.register(skill)
                
                logger.info(f"Loaded {len(self._skills)} skills from config: {config_path}")
                return
            except Exception as e:
                logger.warning(f"Failed to load skills from config: {e}. Using defaults.")
        
        # Fallback to minimal built-in skills if config not found
        self._register_fallback_skills()
    
    def _register_fallback_skills(self) -> None:
        """Register minimal fallback skills if config not available."""
        fallback_skills = [
            SkillMetadata(
                skill_id="LLM",
                name="Large Language Model",
                description="Interact with large language models",
                category=SkillCategory.AI,
                tags=["ai", "llm", "chat", "generation"],
            ),
            SkillMetadata(
                skill_id="rag-blueprint",
                name="RAG Blueprint",
                description="NVIDIA RAG Blueprint for retrieval-augmented generation",
                category=SkillCategory.BLUEPRINT,
                tags=["nvidia", "rag", "retrieval", "search", "qa"],
            ),
        ]
        
        for skill in fallback_skills:
            self.register(skill)
    
    def register(self, skill: SkillMetadata) -> None:
        """Register a skill."""
        self._skills[skill.skill_id] = skill
        
        # Index by category
        if skill.skill_id not in self._by_category[skill.category]:
            self._by_category[skill.category].append(skill.skill_id)
        
        # Index by tags
        for tag in skill.tags:
            if tag not in self._by_tag:
                self._by_tag[tag] = []
            if skill.skill_id not in self._by_tag[tag]:
                self._by_tag[tag].append(skill.skill_id)
        
        # Index tools to skill
        for tool in skill.tools:
            self._tool_to_skill[tool] = skill.skill_id
        
        logger.debug(f"Registered skill: {skill.name} ({skill.skill_id})")
    
    def get(self, skill_id: str) -> Optional[SkillMetadata]:
        """Get a skill by ID."""
        return self._skills.get(skill_id)
    
    def get_by_tool(self, tool_name: str) -> Optional[SkillMetadata]:
        """Get the skill that provides a tool."""
        skill_id = self._tool_to_skill.get(tool_name)
        if skill_id:
            return self._skills.get(skill_id)
        return None
    
    def list_all(self) -> List[SkillMetadata]:
        """List all skills."""
        return list(self._skills.values())
    
    def list_by_category(self, category: SkillCategory) -> List[SkillMetadata]:
        """List skills by category."""
        return [self._skills[sid] for sid in self._by_category[category] if sid in self._skills]
    
    def list_by_tag(self, tag: str) -> List[SkillMetadata]:
        """List skills by tag."""
        if tag not in self._by_tag:
            return []
        return [self._skills[sid] for sid in self._by_tag[tag] if sid in self._skills]
    
    def search(self, query: str) -> List[SkillMetadata]:
        """Search skills by name, description, or tags."""
        query = query.lower()
        results = []
        
        for skill in self._skills.values():
            if (
                query in skill.name.lower() or
                query in skill.description.lower() or
                any(query in tag.lower() for tag in skill.tags)
            ):
                results.append(skill)
        
        return results
    
    def get_all_tools(self) -> Dict[str, str]:
        """Get mapping of all tools to their skills."""
        return dict(self._tool_to_skill)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        return {
            "total_skills": len(self._skills),
            "by_category": {
                cat.value: len(skills)
                for cat, skills in self._by_category.items()
            },
            "total_tools": len(self._tool_to_skill),
            "total_tags": len(self._by_tag),
        }


# Global registry instance
skill_registry = SkillRegistry()
