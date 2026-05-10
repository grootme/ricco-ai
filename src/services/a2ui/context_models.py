"""
A2UI Context Models
Context Engineering models for A2UI service

Implements: Value Object Pattern (DDD)
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


class UIContextMode(str, Enum):
    """UI generation modes based on context"""
    MINIMAL = "minimal"          # Basic UI, few elements
    STANDARD = "standard"        # Standard UI
    DETAILED = "detailed"        # Detailed UI with more information
    ACCESSIBILITY = "accessibility"  # UI optimized for accessibility


class PersonalContext(BaseModel):
    """Personal user context - Value Object"""
    user_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    timezone: Optional[str] = None
    language: str = "es"
    
    # Preferences
    preferences: Dict[str, Any] = Field(default_factory=dict)
    interests: List[str] = Field(default_factory=list)
    frequent_actions: List[str] = Field(default_factory=list)
    
    # Calendar context
    calendar_events: List[Dict[str, Any]] = Field(default_factory=list)
    upcoming_appointments: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Communication context
    recent_emails: List[Dict[str, Any]] = Field(default_factory=list)
    recent_messages: List[Dict[str, Any]] = Field(default_factory=list)
    contacts: Dict[str, Any] = Field(default_factory=dict)
    
    # Behavioral patterns
    activity_patterns: Dict[str, Any] = Field(default_factory=dict)
    usage_history: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Trust and verification
    trust_score: float = 0.0
    kyc_verified: bool = False
    roles: List[str] = Field(default_factory=list)


class SpatialContext(BaseModel):
    """Spatial/Location context - Value Object"""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    
    # Location type
    location_type: Optional[str] = None  # home, office, transit, public
    place_name: Optional[str] = None
    
    # Nearby places
    nearby_points_of_interest: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Movement
    speed: Optional[float] = None
    heading: Optional[float] = None
    is_moving: bool = False
    
    # Geofences
    active_geofences: List[str] = Field(default_factory=list)
    
    # Weather
    weather: Optional[Dict[str, Any]] = None


class TemporalContext(BaseModel):
    """Temporal context - Value Object"""
    current_time: datetime = Field(default_factory=datetime.utcnow)
    timezone: str = "UTC"
    
    # Time categories
    time_of_day: str = "morning"  # morning, afternoon, evening, night
    day_of_week: str = "monday"
    is_weekend: bool = False
    is_holiday: bool = False
    
    # Business context
    is_business_hours: bool = True
    business_hours: Dict[str, str] = Field(default_factory=dict)
    
    # Seasonal
    season: str = "spring"
    month: int = 1
    quarter: int = 1
    
    # User schedule context
    active_events: List[Dict[str, Any]] = Field(default_factory=list)
    next_event: Optional[Dict[str, Any]] = None
    
    # Historical patterns
    typical_activity: Optional[str] = None


class DeviceContext(BaseModel):
    """Device context - Value Object"""
    device_id: Optional[str] = None
    device_type: str = "mobile"  # mobile, tablet, desktop, smartwatch
    platform: str = "unknown"    # ios, android, web, windows, macos
    
    # Device capabilities
    screen_width: int = 375
    screen_height: int = 667
    pixel_ratio: float = 1.0
    color_scheme: str = "light"  # light, dark, system
    
    # Device state
    battery_level: Optional[float] = None
    battery_charging: bool = False
    network_type: str = "wifi"   # wifi, cellular, ethernet, offline
    network_speed: Optional[float] = None  # Mbps
    
    # App state
    app_version: Optional[str] = None
    os_version: Optional[str] = None
    active_apps: List[str] = Field(default_factory=list)
    memory_usage: Optional[float] = None
    storage_available: Optional[float] = None
    
    # Permissions
    permissions: Dict[str, bool] = Field(default_factory=dict)
    
    # Input methods
    has_touch: bool = True
    has_keyboard: bool = False
    has_mouse: bool = False
    voice_input: bool = False


class SolutionContext(BaseModel):
    """RICCO Solution-specific context - Value Object"""
    solution_id: str
    solution_name: str
    
    # User's role in solution
    user_role: str = "user"  # user, seller, admin, provider
    
    # Active entities
    active_entity_id: Optional[str] = None
    active_entity_type: Optional[str] = None
    
    # Solution-specific data
    cart_items: List[Dict[str, Any]] = Field(default_factory=list)
    pending_orders: List[Dict[str, Any]] = Field(default_factory=list)
    saved_items: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Preferences
    view_preferences: Dict[str, Any] = Field(default_factory=dict)
    notification_settings: Dict[str, bool] = Field(default_factory=dict)
    
    # Recent activities
    recent_searches: List[str] = Field(default_factory=list)
    recent_views: List[Dict[str, Any]] = Field(default_factory=list)
    recent_actions: List[Dict[str, Any]] = Field(default_factory=list)


class HorizontalContext(BaseModel):
    """Horizontal context shared across solutions - Value Object"""
    # Cross-solution data
    energy_points_balance: float = 0.0
    trust_score: float = 0.0
    
    # Shared entities
    active_business_id: Optional[str] = None
    active_store_id: Optional[str] = None
    
    # Cross-solution permissions
    accessible_solutions: List[str] = Field(default_factory=list)
    solution_permissions: Dict[str, List[str]] = Field(default_factory=dict)
    
    # Global preferences
    theme: str = "light"
    language: str = "es"
    currency: str = "USD"
    
    # Notifications
    unread_notifications: int = 0
    pending_tasks: List[Dict[str, Any]] = Field(default_factory=list)


class VerticalContext(BaseModel):
    """Vertical-specific deep context - Value Object"""
    # Commerce vertical
    commerce: Optional[Dict[str, Any]] = None
    
    # Health vertical
    health: Optional[Dict[str, Any]] = None
    
    # Logistics vertical
    logistics: Optional[Dict[str, Any]] = None
    
    # Finance vertical
    finance: Optional[Dict[str, Any]] = None
    
    # Travel vertical
    travel: Optional[Dict[str, Any]] = None
    
    # Real estate vertical
    real_estate: Optional[Dict[str, Any]] = None


class ContextBundle(BaseModel):
    """
    Complete context bundle for AI agent.
    
    Implements: Facade Pattern - aggregates all context types
    into a single unified interface.
    """
    session_id: str
    user_id: str
    
    # Core contexts
    personal: Optional[PersonalContext] = None
    spatial: Optional[SpatialContext] = None
    temporal: Optional[TemporalContext] = None
    device: Optional[DeviceContext] = None
    solution: Optional[SolutionContext] = None
    horizontal: Optional[HorizontalContext] = None
    vertical: Optional[VerticalContext] = None
    
    # Conversation context
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    current_intent: Optional[str] = None
    entities: Dict[str, Any] = Field(default_factory=dict)
    
    # Skills arsenal
    available_skills: List[str] = Field(default_factory=list)
    skill_context: Dict[str, Any] = Field(default_factory=dict)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    def get_time_of_day(self) -> str:
        """Get time of day from temporal context"""
        if self.temporal:
            return self.temporal.time_of_day
        return "morning"
    
    def get_device_type(self) -> str:
        """Get device type from device context"""
        if self.device:
            return self.device.device_type
        return "mobile"
    
    def get_user_language(self) -> str:
        """Get user language from personal context"""
        if self.personal:
            return self.personal.language
        if self.horizontal:
            return self.horizontal.language
        return "es"
    
    def is_dark_mode(self) -> bool:
        """Check if user prefers dark mode"""
        if self.device:
            return self.device.color_scheme == "dark"
        if self.horizontal:
            return self.horizontal.theme == "dark"
        return False
    
    def is_low_battery(self) -> bool:
        """Check if device has low battery"""
        if self.device and self.device.battery_level is not None:
            return self.device.battery_level < 20
        return False
    
    def get_location_city(self) -> Optional[str]:
        """Get city from spatial context"""
        if self.spatial:
            return self.spatial.city
        return None
    
    def to_prompt_context(self) -> str:
        """
        Convert context to a formatted prompt string.
        
        Template Method Pattern for context formatting.
        """
        parts = []
        
        if self.personal:
            parts.append(f"User: {self.personal.name or self.user_id}")
            parts.append(f"Language: {self.personal.language}")
        
        if self.temporal:
            parts.append(f"Time: {self.temporal.time_of_day}")
            parts.append(f"Day: {self.temporal.day_of_week}")
        
        if self.spatial:
            parts.append(f"Location: {self.spatial.city or 'Unknown'}")
        
        if self.device:
            parts.append(f"Device: {self.device.device_type}")
            parts.append(f"Platform: {self.device.platform}")
        
        if self.solution:
            parts.append(f"Solution: {self.solution.solution_name}")
            parts.append(f"Role: {self.solution.user_role}")
        
        return "\n".join(parts)


# =============================================================================
# Context Builder (Builder Pattern)
# =============================================================================

class ContextBundleBuilder:
    """
    Builder for creating context bundles.
    
    Usage:
        bundle = (ContextBundleBuilder(session_id, user_id)
            .with_personal_context(personal)
            .with_device_context(device)
            .with_solution_context(solution)
            .build())
    """
    
    def __init__(self, session_id: str, user_id: str):
        self._session_id = session_id
        self._user_id = user_id
        self._personal: Optional[PersonalContext] = None
        self._spatial: Optional[SpatialContext] = None
        self._temporal: Optional[TemporalContext] = None
        self._device: Optional[DeviceContext] = None
        self._solution: Optional[SolutionContext] = None
        self._horizontal: Optional[HorizontalContext] = None
        self._vertical: Optional[VerticalContext] = None
        self._conversation_history: List[Dict[str, Any]] = []
        self._current_intent: Optional[str] = None
        self._entities: Dict[str, Any] = {}
        self._available_skills: List[str] = []
    
    def with_personal_context(self, context: PersonalContext) -> 'ContextBundleBuilder':
        self._personal = context
        return self
    
    def with_spatial_context(self, context: SpatialContext) -> 'ContextBundleBuilder':
        self._spatial = context
        return self
    
    def with_temporal_context(self, context: TemporalContext) -> 'ContextBundleBuilder':
        self._temporal = context
        return self
    
    def with_device_context(self, context: DeviceContext) -> 'ContextBundleBuilder':
        self._device = context
        return self
    
    def with_solution_context(self, context: SolutionContext) -> 'ContextBundleBuilder':
        self._solution = context
        return self
    
    def with_horizontal_context(self, context: HorizontalContext) -> 'ContextBundleBuilder':
        self._horizontal = context
        return self
    
    def with_vertical_context(self, context: VerticalContext) -> 'ContextBundleBuilder':
        self._vertical = context
        return self
    
    def with_conversation_history(self, history: List[Dict[str, Any]]) -> 'ContextBundleBuilder':
        self._conversation_history = history
        return self
    
    def with_intent(self, intent: str) -> 'ContextBundleBuilder':
        self._current_intent = intent
        return self
    
    def with_entities(self, entities: Dict[str, Any]) -> 'ContextBundleBuilder':
        self._entities = entities
        return self
    
    def with_skills(self, skills: List[str]) -> 'ContextBundleBuilder':
        self._available_skills = skills
        return self
    
    def build(self) -> ContextBundle:
        return ContextBundle(
            session_id=self._session_id,
            user_id=self._user_id,
            personal=self._personal,
            spatial=self._spatial,
            temporal=self._temporal,
            device=self._device,
            solution=self._solution,
            horizontal=self._horizontal,
            vertical=self._vertical,
            conversation_history=self._conversation_history,
            current_intent=self._current_intent,
            entities=self._entities,
            available_skills=self._available_skills
        )
