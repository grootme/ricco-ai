"""
Context Bundles Module for RICCO AI.

Provides context bundle selection and management.
"""

from typing import Any, Dict, List, Optional
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class ContextType(str, Enum):
    """Types of context available."""
    PERSONAL = "personal"
    SPATIAL = "spatial"
    TEMPORAL = "temporal"
    DEVICE = "device"
    SOLUTION = "solution"
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    SKILLS = "skills"
    CONVERSATION = "conversation"


class BundleCategory(str, Enum):
    """Categories of context bundles."""
    MINIMAL = "minimal"
    STANDARD = "standard"
    COMPLETE = "complete"
    PRIVACY_FOCUSED = "privacy_focused"
    DOMAIN_SPECIFIC = "domain_specific"


class ContextBundlePreset(BaseModel):
    """Predefined context bundle preset."""
    preset_id: str
    name: str
    description: str
    category: BundleCategory
    context_types: List[ContextType]
    is_default: bool = False
    privacy_level: int = 1  # 1-5, 5 being most private
    tags: List[str] = Field(default_factory=list)


# Predefined presets
MINIMAL_PRESET = ContextBundlePreset(
    preset_id="minimal",
    name="Minimal",
    description="Minimal context for fast responses",
    category=BundleCategory.MINIMAL,
    context_types=[ContextType.TEMPORAL],
    privacy_level=5,
)

PERSONALIZED_PRESET = ContextBundlePreset(
    preset_id="personalized",
    name="Personalized",
    description="Personal context with temporal data",
    category=BundleCategory.STANDARD,
    context_types=[ContextType.PERSONAL, ContextType.TEMPORAL],
    is_default=True,
    privacy_level=3,
)

COMMERCE_PRESET = ContextBundlePreset(
    preset_id="commerce",
    name="Commerce",
    description="Context for e-commerce interactions",
    category=BundleCategory.DOMAIN_SPECIFIC,
    context_types=[
        ContextType.PERSONAL,
        ContextType.SOLUTION,
        ContextType.HORIZONTAL,
    ],
    privacy_level=2,
    tags=["commerce", "shopping"],
)

LOCATION_PRESET = ContextBundlePreset(
    preset_id="location",
    name="Location-Aware",
    description="Context with location data",
    category=BundleCategory.STANDARD,
    context_types=[
        ContextType.PERSONAL,
        ContextType.SPATIAL,
        ContextType.TEMPORAL,
    ],
    privacy_level=2,
    tags=["location", "gps"],
)

COMPLETE_PRESET = ContextBundlePreset(
    preset_id="complete",
    name="Complete",
    description="Full context for comprehensive responses",
    category=BundleCategory.COMPLETE,
    context_types=[
        ContextType.PERSONAL,
        ContextType.SPATIAL,
        ContextType.TEMPORAL,
        ContextType.DEVICE,
        ContextType.SOLUTION,
        ContextType.HORIZONTAL,
        ContextType.SKILLS,
        ContextType.CONVERSATION,
    ],
    privacy_level=1,
)

PRIVACY_FOCUSED_PRESET = ContextBundlePreset(
    preset_id="privacy_focused",
    name="Privacy-Focused",
    description="Minimal personal data for privacy",
    category=BundleCategory.PRIVACY_FOCUSED,
    context_types=[ContextType.TEMPORAL, ContextType.DEVICE],
    privacy_level=5,
    tags=["privacy"],
)


class UserContextSelection(BaseModel):
    """User's context selection preferences."""
    user_id: str
    selected_preset_id: str
    custom_types: Optional[List[ContextType]] = None
    excluded_types: List[ContextType] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ContextBundleConfiguration(BaseModel):
    """Configuration for a context bundle."""
    config_id: str
    user_id: str
    session_id: Optional[str] = None
    context_types: List[ContextType]
    cache_ttl_seconds: int = 900
    privacy_level: int = 3
    custom_settings: Dict[str, Any] = Field(default_factory=dict)


class ContextBundleRecommendation(BaseModel):
    """Recommendation for context bundle."""
    recommended_preset: ContextBundlePreset
    confidence: float
    reason: str
    alternatives: List[ContextBundlePreset] = Field(default_factory=list)


# All presets
ALL_PRESETS = {
    "minimal": MINIMAL_PRESET,
    "personalized": PERSONALIZED_PRESET,
    "commerce": COMMERCE_PRESET,
    "location": LOCATION_PRESET,
    "complete": COMPLETE_PRESET,
    "privacy_focused": PRIVACY_FOCUSED_PRESET,
}


def get_all_presets() -> List[ContextBundlePreset]:
    """Get all available presets."""
    return list(ALL_PRESETS.values())


def get_preset_by_id(preset_id: str) -> Optional[ContextBundlePreset]:
    """Get a preset by ID."""
    return ALL_PRESETS.get(preset_id)


def get_default_preset() -> ContextBundlePreset:
    """Get the default preset."""
    return PERSONALIZED_PRESET


def get_recommended_bundle_for_intent(intent: str) -> ContextBundlePreset:
    """Get recommended bundle for an intent."""
    intent_lower = intent.lower()
    
    if any(kw in intent_lower for kw in ["buy", "order", "shop", "product"]):
        return COMMERCE_PRESET
    elif any(kw in intent_lower for kw in ["where", "location", "near", "map"]):
        return LOCATION_PRESET
    elif any(kw in intent_lower for kw in ["private", "secure", "anonymous"]):
        return PRIVACY_FOCUSED_PRESET
    else:
        return PERSONALIZED_PRESET


class ContextBundleService:
    """
    Service for managing context bundles.
    
    Provides:
    - Bundle selection and configuration
    - User preference management
    - Bundle recommendations
    """
    
    def __init__(self):
        self._user_selections: Dict[str, UserContextSelection] = {}
        self._configurations: Dict[str, ContextBundleConfiguration] = {}
    
    async def get_available_bundles(self) -> List[ContextBundlePreset]:
        """Get all available bundle presets."""
        return get_all_presets()
    
    async def get_user_selection(self, user_id: str) -> UserContextSelection:
        """Get a user's context selection."""
        if user_id not in self._user_selections:
            self._user_selections[user_id] = UserContextSelection(
                user_id=user_id,
                selected_preset_id=get_default_preset().preset_id,
            )
        return self._user_selections[user_id]
    
    async def set_user_selection(
        self,
        user_id: str,
        preset_id: str,
        excluded_types: Optional[List[ContextType]] = None,
    ) -> UserContextSelection:
        """Set a user's context selection."""
        selection = UserContextSelection(
            user_id=user_id,
            selected_preset_id=preset_id,
            excluded_types=excluded_types or [],
            updated_at=datetime.utcnow(),
        )
        self._user_selections[user_id] = selection
        return selection
    
    async def get_recommended_bundle(
        self,
        user_id: str,
        intent: Optional[str] = None,
    ) -> ContextBundleRecommendation:
        """Get recommended bundle for a user."""
        # Get user's current selection
        selection = await self.get_user_selection(user_id)
        
        # Get recommendation based on intent
        if intent:
            recommended = get_recommended_bundle_for_intent(intent)
        else:
            recommended = get_preset_by_id(selection.selected_preset_id) or get_default_preset()
        
        # Build alternatives
        alternatives = [
            p for p in get_all_presets()
            if p.preset_id != recommended.preset_id
        ][:3]
        
        return ContextBundleRecommendation(
            recommended_preset=recommended,
            confidence=0.85 if intent else 0.6,
            reason="Based on user intent" if intent else "Based on user preferences",
            alternatives=alternatives,
        )
    
    async def apply_bundle_to_session(
        self,
        session_id: str,
        bundle: ContextBundlePreset,
        user_id: str,
    ) -> ContextBundleConfiguration:
        """Apply a bundle to a session."""
        import uuid
        
        config = ContextBundleConfiguration(
            config_id=str(uuid.uuid4()),
            user_id=user_id,
            session_id=session_id,
            context_types=bundle.context_types,
            privacy_level=bundle.privacy_level,
        )
        
        self._configurations[config.config_id] = config
        return config
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get service statistics."""
        preset_counts: Dict[str, int] = {}
        for selection in self._user_selections.values():
            preset_id = selection.selected_preset_id
            preset_counts[preset_id] = preset_counts.get(preset_id, 0) + 1
        
        return {
            "total_users": len(self._user_selections),
            "total_configurations": len(self._configurations),
            "preset_distribution": preset_counts,
        }


# Singleton instance
_context_bundle_service: Optional[ContextBundleService] = None


def get_context_bundle_service() -> ContextBundleService:
    """Get the singleton context bundle service."""
    global _context_bundle_service
    if _context_bundle_service is None:
        _context_bundle_service = ContextBundleService()
    return _context_bundle_service
