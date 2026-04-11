"""
RICCO AI Service - Context Engineering Service
Sistema de ingeniería de contexto para el ecosistema RICCO

Este módulo implementa el sistema de Context Engineering que fusiona múltiples
fuentes de contexto para crear agentes de IA verdaderamente personalizados:

1. Contexto Personal: Calendario, correos, contactos, preferencias
2. Contexto Espacial: Ubicación GPS, geofencing
3. Contexto Temporal: Hora del día, día de la semana, estacionalidad
4. Contexto del Dispositivo: Batería, red, apps abiertas
5. Contexto Horizontal: Cross-solution (Energy Points, Trust Score)
6. Contexto Vertical: Solution-specific deep context
7. Skills Arsenal: Available AI skills and capabilities
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from pydantic import BaseModel, Field
from structlog import get_logger

logger = get_logger(__name__)


# ============================================
# Context Types
# ============================================

class ContextType(str, Enum):
    """Types of context data"""
    PERSONAL = "personal"
    SPATIAL = "spatial"
    TEMPORAL = "temporal"
    DEVICE = "device"
    SOLUTION = "solution"
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    SKILLS = "skills"
    CONVERSATION = "conversation"


# ============================================
# Context Data Models
# ============================================

class PersonalContext(BaseModel):
    """
    Personal Context - Información personal del usuario
    
    Este contexto incluye toda la información personal que permite
    al agente de IA entender las preferencias, patrones y necesidades
    específicas del usuario.
    """
    user_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    timezone: str = "UTC"
    language: str = "es"
    currency: str = "USD"
    
    # Profile
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    
    # Preferences
    preferences: Dict[str, Any] = {}
    notification_preferences: Dict[str, bool] = {}
    theme: str = "light"
    
    # Interests and behaviors
    interests: List[str] = []
    frequent_actions: List[str] = []
    browsing_history: List[str] = []
    
    # Calendar context
    calendar_events: List[Dict[str, Any]] = []
    upcoming_appointments: List[Dict[str, Any]] = []
    reminders: List[Dict[str, Any]] = []
    
    # Communication context
    recent_emails: List[Dict[str, Any]] = []
    recent_messages: List[Dict[str, Any]] = []
    contacts: Dict[str, Any] = {}
    
    # Behavioral patterns
    activity_patterns: Dict[str, Any] = {}
    usage_history: List[Dict[str, Any]] = []
    peak_activity_hours: List[int] = []
    
    # Trust and verification
    trust_score: float = 0.0
    kyc_verified: bool = False
    kyc_level: str = "basic"  # basic, intermediate, advanced
    roles: List[str] = []
    permissions: List[str] = []
    
    # Business context
    businesses: List[Dict[str, Any]] = []
    active_business_id: Optional[str] = None


class SpatialContext(BaseModel):
    """
    Spatial Context - Contexto de ubicación y espacio
    
    Proporciona información sobre la ubicación física del usuario,
    permitiendo ofrecer servicios relevantes basados en su posición.
    """
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy: Optional[float] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    
    # Location type
    location_type: Optional[str] = None  # home, office, transit, public, retail
    place_name: Optional[str] = None
    place_category: Optional[str] = None
    
    # Nearby places
    nearby_points_of_interest: List[Dict[str, Any]] = []
    nearby_stores: List[Dict[str, Any]] = []
    nearby_providers: List[Dict[str, Any]] = []
    
    # Movement
    speed: Optional[float] = None
    heading: Optional[float] = None
    is_moving: bool = False
    mode_of_transport: Optional[str] = None  # walking, driving, transit, cycling
    
    # Geofences
    active_geofences: List[str] = []
    geofence_events: List[Dict[str, Any]] = []
    
    # Weather
    weather: Optional[Dict[str, Any]] = None
    temperature: Optional[float] = None
    weather_condition: Optional[str] = None
    
    # Saved locations
    saved_addresses: List[Dict[str, Any]] = []
    home_location: Optional[Dict[str, float]] = None
    work_location: Optional[Dict[str, float]] = None


class TemporalContext(BaseModel):
    """
    Temporal Context - Contexto temporal
    
    Incluye información sobre el momento actual, patrones temporales
    y eventos relevantes para entender el contexto de tiempo del usuario.
    """
    current_time: datetime = Field(default_factory=datetime.utcnow)
    timezone: str = "UTC"
    local_time: Optional[datetime] = None
    
    # Time categories
    time_of_day: str = "morning"  # morning, afternoon, evening, night, late_night
    day_of_week: str = "monday"
    is_weekend: bool = False
    is_holiday: bool = False
    holidays: List[str] = []
    
    # Business context
    is_business_hours: bool = True
    business_start_hour: int = 9
    business_end_hour: int = 18
    
    # Seasonal
    season: str = "spring"
    month: int = 1
    quarter: int = 1
    year_week: int = 1
    
    # User schedule
    active_events: List[Dict[str, Any]] = []
    next_event: Optional[Dict[str, Any]] = None
    current_meeting: Optional[Dict[str, Any]] = None
    focus_time: bool = False
    
    # Historical patterns
    typical_activity: Optional[str] = None
    typical_activities: Dict[str, List[str]] = {}  # day -> activities
    
    # Recurring events
    recurring_events: List[Dict[str, Any]] = []
    
    # Deadlines
    upcoming_deadlines: List[Dict[str, Any]] = []
    urgent_tasks: List[Dict[str, Any]] = []


class DeviceContext(BaseModel):
    """
    Device Context - Contexto del dispositivo
    
    Información sobre el dispositivo que el usuario está utilizando,
    incluyendo capacidades, estado y configuración.
    """
    device_id: Optional[str] = None
    device_type: str = "mobile"  # mobile, tablet, desktop, smartwatch, smarttv
    platform: str = "unknown"  # ios, android, web, windows, macos, linux
    
    # Device info
    device_name: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    
    # Screen
    screen_width: int = 375
    screen_height: int = 667
    pixel_ratio: float = 1.0
    orientation: str = "portrait"
    color_scheme: str = "light"  # light, dark, system
    
    # Device state
    battery_level: Optional[float] = None
    battery_charging: bool = False
    battery_saver: bool = False
    
    # Network
    network_type: str = "wifi"  # wifi, cellular, ethernet, offline
    network_speed: Optional[float] = None
    cellular_generation: Optional[str] = None  # 3G, 4G, 5G
    
    # App state
    app_version: Optional[str] = None
    os_version: Optional[str] = None
    app_build: Optional[str] = None
    active_apps: List[str] = []
    foreground_app: Optional[str] = None
    
    # Performance
    memory_usage: Optional[float] = None
    storage_available: Optional[float] = None
    cpu_usage: Optional[float] = None
    
    # Permissions
    permissions: Dict[str, bool] = {}
    
    # Input methods
    has_touch: bool = True
    has_keyboard: bool = False
    has_mouse: bool = False
    has_stylus: bool = False
    voice_input_available: bool = False
    biometric_available: bool = False
    
    # Connectivity
    bluetooth_enabled: bool = False
    nfc_available: bool = False
    connected_devices: List[str] = []


class SolutionContext(BaseModel):
    """
    Solution Context - Contexto específico de la solución RICCO
    
    Información específica de la solución RICCO que el usuario
    está utilizando actualmente.
    """
    solution_id: str
    solution_name: str
    solution_url: Optional[str] = None
    
    # User's role in solution
    user_role: str = "user"  # user, seller, admin, provider, staff
    role_permissions: List[str] = []
    
    # Active entities
    active_entity_id: Optional[str] = None
    active_entity_type: Optional[str] = None
    
    # Commerce specific
    cart_items: List[Dict[str, Any]] = []
    cart_total: float = 0
    pending_orders: List[Dict[str, Any]] = []
    wishlist: List[str] = []
    
    # Health specific
    active_appointments: List[Dict[str, Any]] = []
    medical_records_access: bool = False
    prescriptions: List[Dict[str, Any]] = []
    
    # Logistics specific
    active_shipments: List[Dict[str, Any]] = []
    saved_addresses: List[Dict[str, Any]] = []
    
    # Preferences
    view_preferences: Dict[str, Any] = {}
    notification_settings: Dict[str, bool] = {}
    display_settings: Dict[str, Any] = {}
    
    # Recent activities
    recent_searches: List[str] = []
    recent_views: List[Dict[str, Any]] = []
    recent_actions: List[Dict[str, Any]] = []
    bookmarks: List[str] = []
    
    # Favorites
    favorite_items: List[str] = []
    favorite_sellers: List[str] = []
    favorite_providers: List[str] = []


class HorizontalContext(BaseModel):
    """
    Horizontal Context - Contexto horizontal cross-solution
    
    Información compartida entre todas las soluciones RICCO,
    incluyendo datos financieros, permisos globales y preferencias.
    """
    # Energy Points (RPT)
    energy_points_balance: float = 0.0
    energy_points_pending: float = 0.0
    energy_points_earned_total: float = 0.0
    energy_points_spent_total: float = 0.0
    
    # Trust Score
    trust_score: float = 0.0
    trust_level: str = "basic"  # basic, intermediate, advanced, premium
    trust_factors: Dict[str, float] = {}
    
    # Subscription
    subscription_plan: str = "free"  # free, basic, premium, enterprise
    subscription_status: str = "active"
    subscription_features: List[str] = []
    
    # Business context
    active_business_id: Optional[str] = None
    active_store_id: Optional[str] = None
    businesses_owned: List[str] = []
    
    # Cross-solution permissions
    accessible_solutions: List[str] = []
    solution_permissions: Dict[str, List[str]] = {}
    admin_solutions: List[str] = []
    
    # Global preferences
    theme: str = "light"
    language: str = "es"
    currency: str = "USD"
    date_format: str = "DD/MM/YYYY"
    time_format: str = "24h"
    
    # Notifications
    unread_notifications: int = 0
    notification_badge: Dict[str, int] = {}
    
    # Tasks and reminders
    pending_tasks: List[Dict[str, Any]] = []
    reminders: List[Dict[str, Any]] = []
    
    # Rewards and achievements
    badges: List[str] = []
    achievements: List[Dict[str, Any]] = []
    streak_days: int = 0


class VerticalContext(BaseModel):
    """
    Vertical Context - Contexto vertical específico
    
    Contexto profundo para cada vertical del ecosistema RICCO,
    con información detallada y especializada.
    """
    # Commerce vertical
    commerce: Optional[Dict[str, Any]] = None
    # Includes: purchase_history, preferred_categories, spending_patterns
    
    # Health vertical
    health: Optional[Dict[str, Any]] = None
    # Includes: health_profile, conditions, medications, providers
    
    # Logistics vertical
    logistics: Optional[Dict[str, Any]] = None
    # Includes: shipping_preferences, carriers, frequent_routes
    
    # Finance vertical
    finance: Optional[Dict[str, Any]] = None
    # Includes: accounts, investments, transactions, budgets
    
    # Travel vertical
    travel: Optional[Dict[str, Any]] = None
    # Includes: trips, preferences, loyalty_programs
    
    # Real estate vertical
    real_estate: Optional[Dict[str, Any]] = None
    # Includes: properties, searches, saved_listings
    
    # Legal vertical
    legal: Optional[Dict[str, Any]] = None
    # Includes: cases, documents, lawyers
    
    # Social vertical
    social: Optional[Dict[str, Any]] = None
    # Includes: connections, communities, interests
    
    # Jobs/Connect vertical
    jobs: Optional[Dict[str, Any]] = None
    # Includes: profile, applications, skills, experience


class SkillsContext(BaseModel):
    """
    Skills Arsenal Context - Contexto del arsenal de skills
    
    Información sobre las habilidades de IA disponibles y su
    contexto específico para el usuario actual.
    """
    # Available skills
    available_skills: List[str] = []
    enabled_skills: List[str] = []
    favorite_skills: List[str] = []
    
    # Skill configurations
    skill_configs: Dict[str, Dict[str, Any]] = {}
    
    # Skill usage history
    skill_usage_history: List[Dict[str, Any]] = []
    most_used_skills: List[str] = []
    
    # Custom skills
    custom_skills: List[Dict[str, Any]] = []
    
    # Skill recommendations
    recommended_skills: List[str] = []
    
    # Skill categories
    skill_categories: Dict[str, List[str]] = {}


class ConversationContext(BaseModel):
    """
    Conversation Context - Contexto de la conversación actual
    
    Información sobre el estado actual de la conversación
    con el agente de IA.
    """
    session_id: str
    conversation_id: Optional[str] = None
    
    # History
    message_history: List[Dict[str, Any]] = []
    last_message: Optional[Dict[str, Any]] = None
    message_count: int = 0
    
    # Current intent
    current_intent: Optional[str] = None
    intent_confidence: float = 0.0
    detected_entities: Dict[str, Any] = {}
    
    # Conversation state
    state: str = "idle"  # idle, processing, waiting_input, completed
    awaiting_response: bool = False
    expected_input_type: Optional[str] = None
    
    # Context
    context_variables: Dict[str, Any] = {}
    flow_state: Optional[str] = None
    flow_data: Dict[str, Any] = {}
    
    # References
    referenced_entities: List[str] = []
    referenced_orders: List[str] = []
    referenced_products: List[str] = []


# ============================================
# Complete Context Bundle
# ============================================

class ContextBundle(BaseModel):
    """
    Context Bundle - Paquete completo de contexto
    
    Combina todos los tipos de contexto en un único bundle
    que se pasa al agente de IA para generar respuestas
    personalizadas y contextualmente relevantes.
    """
    session_id: str
    user_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    # All context types
    personal: Optional[PersonalContext] = None
    spatial: Optional[SpatialContext] = None
    temporal: Optional[TemporalContext] = None
    device: Optional[DeviceContext] = None
    solution: Optional[SolutionContext] = None
    horizontal: Optional[HorizontalContext] = None
    vertical: Optional[VerticalContext] = None
    skills: Optional[SkillsContext] = None
    conversation: Optional[ConversationContext] = None
    
    # Derived insights
    insights: Dict[str, Any] = {}
    
    # Metadata
    version: str = "1.0"
    source: str = "context_engineering_service"


# ============================================
# Context Engineering Service
# ============================================

class ContextEngineeringService:
    """
    Context Engineering Service
    
    Servicio principal para la ingeniería de contexto que:
    1. Recolecta datos de múltiples fuentes
    2. Fusiona y normaliza el contexto
    3. Genera insights derivados
    4. Proporciona contexto optimizado para agentes de IA
    """
    
    def __init__(self):
        self._context_cache: Dict[str, ContextBundle] = {}
        self._context_providers: Dict[str, callable] = {}
        self._initialized = False
    
    async def initialize(self):
        """Initialize the context engineering service"""
        if self._initialized:
            return
        
        # Register default context providers
        self._register_default_providers()
        self._initialized = True
        logger.info("Context Engineering Service initialized")
    
    def _register_default_providers(self):
        """Register default context data providers"""
        self._context_providers = {
            ContextType.PERSONAL: self._provide_personal_context,
            ContextType.SPATIAL: self._provide_spatial_context,
            ContextType.TEMPORAL: self._provide_temporal_context,
            ContextType.DEVICE: self._provide_device_context,
            ContextType.SOLUTION: self._provide_solution_context,
            ContextType.HORIZONTAL: self._provide_horizontal_context,
            ContextType.VERTICAL: self._provide_vertical_context,
            ContextType.SKILLS: self._provide_skills_context,
        }
    
    async def build_context(
        self,
        session_id: str,
        user_id: str,
        solution: str,
        request_context: Optional[Dict[str, Any]] = None,
    ) -> ContextBundle:
        """
        Build complete context bundle for a session
        
        This is the main entry point for context engineering.
        """
        await self.initialize()
        
        now = datetime.utcnow()
        request_context = request_context or {}
        
        # Build temporal context (always available)
        temporal = await self._provide_temporal_context(request_context)
        
        # Build other contexts
        personal = await self._provide_personal_context({
            "user_id": user_id,
            **request_context.get("personal", {}),
        })
        
        spatial = await self._provide_spatial_context(
            request_context.get("spatial", {})
        )
        
        device = await self._provide_device_context(
            request_context.get("device", {})
        )
        
        solution_ctx = await self._provide_solution_context({
            "solution_id": solution,
            **request_context.get("solution", {}),
        })
        
        horizontal = await self._provide_horizontal_context({
            "user_id": user_id,
            **request_context.get("horizontal", {}),
        })
        
        vertical = await self._provide_vertical_context({
            "solution": solution,
            **request_context.get("vertical", {}),
        })
        
        skills = await self._provide_skills_context({
            "user_id": user_id,
            **request_context.get("skills", {}),
        })
        
        # Create bundle
        bundle = ContextBundle(
            session_id=session_id,
            user_id=user_id,
            personal=personal,
            spatial=spatial,
            temporal=temporal,
            device=device,
            solution=solution_ctx,
            horizontal=horizontal,
            vertical=vertical,
            skills=skills,
            expires_at=now + timedelta(minutes=30),
        )
        
        # Generate insights
        bundle.insights = await self._generate_insights(bundle)
        
        # Cache the bundle
        self._context_cache[session_id] = bundle
        
        return bundle
    
    async def get_cached_context(self, session_id: str) -> Optional[ContextBundle]:
        """Get cached context bundle"""
        bundle = self._context_cache.get(session_id)
        
        if bundle and bundle.expires_at:
            if datetime.utcnow() > bundle.expires_at:
                del self._context_cache[session_id]
                return None
        
        return bundle
    
    async def update_context(
        self,
        session_id: str,
        updates: Dict[str, Any],
    ) -> Optional[ContextBundle]:
        """Update cached context with new data"""
        bundle = await self.get_cached_context(session_id)
        if not bundle:
            return None
        
        # Apply updates to relevant context types
        for key, value in updates.items():
            if hasattr(bundle, key):
                current = getattr(bundle, key)
                if isinstance(current, BaseModel):
                    # Update fields of the nested model
                    for field, val in value.items():
                        if hasattr(current, field):
                            setattr(current, field, val)
                else:
                    setattr(bundle, key, value)
        
        # Regenerate insights
        bundle.insights = await self._generate_insights(bundle)
        
        return bundle
    
    # ============================================
    # Context Providers
    # ============================================
    
    async def _provide_personal_context(
        self,
        data: Dict[str, Any],
    ) -> PersonalContext:
        """Provide personal context"""
        user_id = data.get("user_id", "anonymous")
        
        # In production, fetch from RICCO ID service
        return PersonalContext(
            user_id=user_id,
            name=data.get("name"),
            email=data.get("email"),
            language=data.get("language", "es"),
            timezone=data.get("timezone", "UTC"),
            preferences=data.get("preferences", {}),
            interests=data.get("interests", []),
            trust_score=data.get("trust_score", 0.0),
            kyc_verified=data.get("kyc_verified", False),
            roles=data.get("roles", []),
        )
    
    async def _provide_spatial_context(
        self,
        data: Dict[str, Any],
    ) -> Optional[SpatialContext]:
        """Provide spatial context"""
        if not data:
            return None
        
        return SpatialContext(
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            address=data.get("address"),
            city=data.get("city"),
            country=data.get("country"),
            location_type=data.get("location_type"),
            is_moving=data.get("is_moving", False),
            weather=data.get("weather"),
        )
    
    async def _provide_temporal_context(
        self,
        data: Dict[str, Any],
    ) -> TemporalContext:
        """Provide temporal context"""
        now = datetime.utcnow()
        timezone = data.get("timezone", "UTC")
        
        hour = now.hour
        if 6 <= hour < 12:
            time_of_day = "morning"
        elif 12 <= hour < 18:
            time_of_day = "afternoon"
        elif 18 <= hour < 22:
            time_of_day = "evening"
        else:
            time_of_day = "night"
        
        month = now.month
        if month in [12, 1, 2]:
            season = "winter"
        elif month in [3, 4, 5]:
            season = "spring"
        elif month in [6, 7, 8]:
            season = "summer"
        else:
            season = "autumn"
        
        return TemporalContext(
            current_time=now,
            timezone=timezone,
            time_of_day=time_of_day,
            day_of_week=now.strftime("%A").lower(),
            is_weekend=now.weekday() >= 5,
            season=season,
            month=month,
            quarter=(month - 1) // 3 + 1,
            is_business_hours=9 <= hour < 18,
        )
    
    async def _provide_device_context(
        self,
        data: Dict[str, Any],
    ) -> Optional[DeviceContext]:
        """Provide device context"""
        if not data:
            return None
        
        return DeviceContext(
            device_id=data.get("device_id"),
            device_type=data.get("type", "mobile"),
            platform=data.get("platform", "unknown"),
            screen_width=data.get("screen_width", 375),
            screen_height=data.get("screen_height", 667),
            battery_level=data.get("battery_level"),
            battery_charging=data.get("battery_charging", False),
            network_type=data.get("network_type", "wifi"),
            color_scheme=data.get("color_scheme", "light"),
        )
    
    async def _provide_solution_context(
        self,
        data: Dict[str, Any],
    ) -> SolutionContext:
        """Provide solution-specific context"""
        solution_id = data.get("solution_id", "ricco-unknown")
        
        return SolutionContext(
            solution_id=solution_id,
            solution_name=solution_id.replace("ricco-", "").title(),
            user_role=data.get("user_role", "user"),
            cart_items=data.get("cart_items", []),
            recent_searches=data.get("recent_searches", []),
            recent_views=data.get("recent_views", []),
        )
    
    async def _provide_horizontal_context(
        self,
        data: Dict[str, Any],
    ) -> HorizontalContext:
        """Provide horizontal context"""
        return HorizontalContext(
            energy_points_balance=data.get("energy_points_balance", 0.0),
            trust_score=data.get("trust_score", 0.0),
            subscription_plan=data.get("subscription_plan", "free"),
            accessible_solutions=data.get("accessible_solutions", []),
            language=data.get("language", "es"),
            currency=data.get("currency", "USD"),
            theme=data.get("theme", "light"),
        )
    
    async def _provide_vertical_context(
        self,
        data: Dict[str, Any],
    ) -> VerticalContext:
        """Provide vertical context"""
        solution = data.get("solution", "")
        vertical_data = data.get("vertical_data", {})
        
        context = VerticalContext()
        
        if "commerce" in solution:
            context.commerce = vertical_data.get("commerce")
        elif "health" in solution:
            context.health = vertical_data.get("health")
        elif "logistics" in solution or "cargo" in solution:
            context.logistics = vertical_data.get("logistics")
        elif "funding" in solution or "finance" in solution:
            context.finance = vertical_data.get("finance")
        elif "travel" in solution:
            context.travel = vertical_data.get("travel")
        
        return context
    
    async def _provide_skills_context(
        self,
        data: Dict[str, Any],
    ) -> SkillsContext:
        """Provide skills context"""
        return SkillsContext(
            available_skills=data.get("available_skills", []),
            enabled_skills=data.get("enabled_skills", []),
            skill_configs=data.get("skill_configs", {}),
            most_used_skills=data.get("most_used_skills", []),
        )
    
    # ============================================
    # Insight Generation
    # ============================================
    
    async def _generate_insights(
        self,
        bundle: ContextBundle,
    ) -> Dict[str, Any]:
        """Generate derived insights from context"""
        insights = {}
        
        # Activity insight
        if bundle.temporal:
            time_context = bundle.temporal.time_of_day
            if time_context == "morning":
                insights["greeting"] = "Buenos días"
            elif time_context == "afternoon":
                insights["greeting"] = "Buenas tardes"
            elif time_context == "evening":
                insights["greeting"] = "Buenas noches"
            else:
                insights["greeting"] = "Hola"
            
            insights["is_business_hours"] = bundle.temporal.is_business_hours
            insights["is_weekend"] = bundle.temporal.is_weekend
        
        # Device insight
        if bundle.device:
            insights["is_mobile"] = bundle.device.device_type == "mobile"
            insights["is_low_battery"] = (
                bundle.device.battery_level is not None and
                bundle.device.battery_level < 20
            )
            insights["is_slow_network"] = bundle.device.network_type in ["3G", "2G", "offline"]
            insights["supports_dark_mode"] = True
        
        # Location insight
        if bundle.spatial:
            insights["has_location"] = bundle.spatial.latitude is not None
            if bundle.spatial.location_type:
                insights["location_context"] = bundle.spatial.location_type
        
        # User insight
        if bundle.personal:
            insights["user_trust_level"] = bundle.personal.trust_score
            insights["is_verified"] = bundle.personal.kyc_verified
            insights["user_roles"] = bundle.personal.roles
        
        # Financial insight
        if bundle.horizontal:
            insights["energy_points"] = bundle.horizontal.energy_points_balance
            insights["subscription"] = bundle.horizontal.subscription_plan
        
        # Solution insight
        if bundle.solution:
            insights["solution"] = bundle.solution.solution_id
            insights["has_cart_items"] = len(bundle.solution.cart_items) > 0
        
        return insights
    
    # ============================================
    # Prompt Engineering Helper
    # ============================================
    
    async def generate_context_prompt(
        self,
        bundle: ContextBundle,
        intent: Optional[str] = None,
    ) -> str:
        """
        Generate a context prompt for AI models
        
        This creates a structured prompt that includes all relevant
        context for the AI agent to understand the user's situation.
        """
        sections = []
        
        # Personal context
        if bundle.personal:
            personal = bundle.personal
            sections.append(f"""CONTEXTO PERSONAL:
- Usuario: {personal.name or 'Usuario'}
- Idioma: {personal.language}
- Zona horaria: {personal.timezone}
- Trust Score: {personal.trust_score}
- Roles: {', '.join(personal.roles) if personal.roles else 'usuario estándar'}""")
        
        # Temporal context
        if bundle.temporal:
            temp = bundle.temporal
            sections.append(f"""CONTEXTO TEMPORAL:
- Hora actual: {temp.current_time.strftime('%H:%M')}
- Momento del día: {temp.time_of_day}
- Día: {temp.day_of_week}
- Es fin de semana: {'Sí' if temp.is_weekend else 'No'}
- Horario laboral: {'Sí' if temp.is_business_hours else 'No'}""")
        
        # Device context
        if bundle.device:
            device = bundle.device
            sections.append(f"""CONTEXTO DEL DISPOSITIVO:
- Tipo: {device.device_type}
- Plataforma: {device.platform}
- Tema: {device.color_scheme}
- Red: {device.network_type}""")
        
        # Spatial context
        if bundle.spatial and bundle.spatial.latitude:
            spatial = bundle.spatial
            sections.append(f"""CONTEXTO ESPACIAL:
- Ubicación: {spatial.city or 'Desconocida'}, {spatial.country or ''}
- Tipo de lugar: {spatial.location_type or 'No determinado'}""")
        
        # Solution context
        if bundle.solution:
            solution = bundle.solution
            sections.append(f"""CONTEXTO DE SOLUCIÓN:
- Solución activa: {solution.solution_name}
- Rol: {solution.user_role}""")
        
        # Horizontal context
        if bundle.horizontal:
            horiz = bundle.horizontal
            sections.append(f"""CONTEXTO HORIZONTAL:
- Energy Points: {horiz.energy_points_balance:.2f} RPT
- Plan: {horiz.subscription_plan}
- Moneda preferida: {horiz.currency}""")
        
        # Intent
        if intent:
            sections.append(f"""INTENCIÓN DETECTADA: {intent}""")
        
        # Insights
        if bundle.insights:
            insights_str = "\n".join(f"- {k}: {v}" for k, v in bundle.insights.items())
            sections.append(f"""INSIGHTS DERIVADOS:
{insights_str}""")
        
        return "\n\n".join(sections)
    
    async def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        return {
            "status": "healthy",
            "initialized": self._initialized,
            "cached_contexts": len(self._context_cache),
            "providers": list(self._context_providers.keys()),
        }


# Singleton
_context_service: Optional[ContextEngineeringService] = None

def get_context_service() -> ContextEngineeringService:
    global _context_service
    if _context_service is None:
        _context_service = ContextEngineeringService()
    return _context_service
