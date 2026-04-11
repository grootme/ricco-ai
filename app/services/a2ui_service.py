"""
RICCO AI Service - A2UI (Agent-to-User Interface) Integration
Integración con Google A2UI para interfaces dinámicas de agentes
https://github.com/google/A2UI

A2UI permite crear interfaces de usuario dinámicas generadas por IA:
- React Renderer: Para aplicaciones web React
- Lit Renderer: Para Web Components
- GenUI SDK (Flutter): Para aplicaciones móviles
"""

import asyncio
import json
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum

from pydantic import BaseModel, Field
from structlog import get_logger

from app.core.config import settings

logger = get_logger(__name__)


# ============================================
# A2UI Core Enums and Types
# ============================================

class ComponentType(str, Enum):
    """A2UI Component types"""
    # Layout
    CONTAINER = "container"
    GRID = "grid"
    STACK = "stack"
    FLEX = "flex"
    
    # Display
    TEXT = "text"
    HEADING = "heading"
    IMAGE = "image"
    ICON = "icon"
    CARD = "card"
    LIST = "list"
    TABLE = "table"
    
    # Input
    TEXT_FIELD = "textField"
    TEXT_AREA = "textArea"
    SELECT = "select"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    SWITCH = "switch"
    SLIDER = "slider"
    DATE_PICKER = "datePicker"
    TIME_PICKER = "timePicker"
    FILE_UPLOAD = "fileUpload"
    
    # Action
    BUTTON = "button"
    BUTTON_GROUP = "buttonGroup"
    FAB = "fab"
    
    # Feedback
    DIALOG = "dialog"
    SNACKBAR = "snackbar"
    PROGRESS = "progress"
    SKELETON = "skeleton"
    
    # Navigation
    TABS = "tabs"
    ACCORDION = "accordion"
    STEPPER = "stepper"
    BREADCRUMB = "breadcrumb"
    
    # Data
    CHART = "chart"
    MAP = "map"
    CALENDAR = "calendar"
    TIMELINE = "timeline"
    
    # RICCO Custom
    PRODUCT_CARD = "productCard"
    USER_PROFILE = "userProfile"
    ORDER_SUMMARY = "orderSummary"
    TRACKING_INFO = "trackingInfo"
    APPOINTMENT_CARD = "appointmentCard"
    PAYMENT_FORM = "paymentForm"


class InteractionType(str, Enum):
    """Types of user interactions"""
    CLICK = "click"
    SUBMIT = "submit"
    CHANGE = "change"
    FOCUS = "focus"
    BLUR = "blur"
    SCROLL = "scroll"
    HOVER = "hover"


class ResponseStatus(str, Enum):
    """UI Response status"""
    SUCCESS = "success"
    ERROR = "error"
    LOADING = "loading"
    PARTIAL = "partial"


# ============================================
# A2UI Component Models
# ============================================

class ComponentStyle(BaseModel):
    """Style properties for components"""
    width: Optional[str] = None
    height: Optional[str] = None
    padding: Optional[str] = None
    margin: Optional[str] = None
    backgroundColor: Optional[str] = None
    color: Optional[str] = None
    fontSize: Optional[str] = None
    fontWeight: Optional[str] = None
    borderRadius: Optional[str] = None
    boxShadow: Optional[str] = None
    display: Optional[str] = None
    flexDirection: Optional[str] = None
    justifyContent: Optional[str] = None
    alignItems: Optional[str] = None
    gap: Optional[str] = None
    custom: Optional[Dict[str, Any]] = None


class ComponentAction(BaseModel):
    """Action configuration for interactive components"""
    type: str  # navigate, api_call, dialog, submit, custom
    payload: Dict[str, Any] = {}
    endpoint: Optional[str] = None
    method: Optional[str] = None
    navigation: Optional[Dict[str, str]] = None
    dialog: Optional[Dict[str, Any]] = None


class ComponentValidation(BaseModel):
    """Validation rules for input components"""
    required: bool = False
    minLength: Optional[int] = None
    maxLength: Optional[int] = None
    pattern: Optional[str] = None
    min: Optional[float] = None
    max: Optional[float] = None
    custom: Optional[str] = None  # Custom validation function name


class A2UIComponent(BaseModel):
    """A2UI Component definition"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    type: ComponentType
    children: List["A2UIComponent"] = []
    properties: Dict[str, Any] = {}
    style: Optional[ComponentStyle] = None
    actions: Dict[str, ComponentAction] = {}
    validation: Optional[ComponentValidation] = None
    visible: bool = True
    enabled: bool = True
    loading: bool = False
    metadata: Dict[str, Any] = {}


class A2UIComponentInstance(A2UIComponent):
    """Extended component with rendering metadata"""
    rendered_at: Optional[datetime] = None
    interaction_count: int = 0
    last_interaction: Optional[datetime] = None


# ============================================
# A2UI Response Model
# ============================================

class A2UIResponse(BaseModel):
    """Complete A2UI response for rendering"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None
    agent_id: Optional[str] = None
    solution: Optional[str] = None
    status: ResponseStatus = ResponseStatus.SUCCESS
    components: List[A2UIComponent] = []
    context: Dict[str, Any] = {}
    suggestions: List[str] = []
    quick_actions: List[ComponentAction] = []
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)


class A2UIState(BaseModel):
    """State management for A2UI sessions"""
    session_id: str
    user_id: Optional[str] = None
    solution: Optional[str] = None
    form_data: Dict[str, Any] = {}
    navigation_stack: List[str] = []
    active_dialog: Optional[str] = None
    context: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================
# Context Engineering Models
# ============================================

class PersonalContext(BaseModel):
    """Personal user context"""
    user_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    timezone: Optional[str] = None
    language: str = "es"
    
    # Preferences
    preferences: Dict[str, Any] = {}
    interests: List[str] = []
    frequent_actions: List[str] = []
    
    # Calendar context
    calendar_events: List[Dict[str, Any]] = []
    upcoming_appointments: List[Dict[str, Any]] = []
    
    # Communication context
    recent_emails: List[Dict[str, Any]] = []
    recent_messages: List[Dict[str, Any]] = []
    contacts: Dict[str, Any] = {}
    
    # Behavioral patterns
    activity_patterns: Dict[str, Any] = {}
    usage_history: List[Dict[str, Any]] = []
    
    # Trust and verification
    trust_score: float = 0.0
    kyc_verified: bool = False
    roles: List[str] = []


class SpatialContext(BaseModel):
    """Spatial/Location context"""
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    
    # Location type
    location_type: Optional[str] = None  # home, office, transit, public
    place_name: Optional[str] = None
    
    # Nearby places
    nearby_points_of_interest: List[Dict[str, Any]] = []
    
    # Movement
    speed: Optional[float] = None
    heading: Optional[float] = None
    is_moving: bool = False
    
    # Geofences
    active_geofences: List[str] = []
    
    # Weather
    weather: Optional[Dict[str, Any]] = None


class TemporalContext(BaseModel):
    """Temporal context"""
    current_time: datetime = Field(default_factory=datetime.utcnow)
    timezone: str = "UTC"
    
    # Time categories
    time_of_day: str = "morning"  # morning, afternoon, evening, night
    day_of_week: str = "monday"
    is_weekend: bool = False
    is_holiday: bool = False
    
    # Business context
    is_business_hours: bool = True
    business_hours: Dict[str, str] = {}
    
    # Seasonal
    season: str = "spring"
    month: int = 1
    quarter: int = 1
    
    # User schedule context
    active_events: List[Dict[str, Any]] = []
    next_event: Optional[Dict[str, Any]] = None
    
    # Historical patterns
    typical_activity: Optional[str] = None


class DeviceContext(BaseModel):
    """Device context"""
    device_id: Optional[str] = None
    device_type: str = "mobile"  # mobile, tablet, desktop, smartwatch
    platform: str = "unknown"  # ios, android, web, windows, macos
    
    # Device capabilities
    screen_width: int = 375
    screen_height: int = 667
    pixel_ratio: float = 1.0
    color_scheme: str = "light"  # light, dark, system
    
    # Device state
    battery_level: Optional[float] = None
    battery_charging: bool = False
    network_type: str = "wifi"  # wifi, cellular, ethernet, offline
    network_speed: Optional[float] = None  # Mbps
    
    # App state
    app_version: Optional[str] = None
    os_version: Optional[str] = None
    active_apps: List[str] = []
    memory_usage: Optional[float] = None
    storage_available: Optional[float] = None
    
    # Permissions
    permissions: Dict[str, bool] = {}
    
    # Input methods
    has_touch: bool = True
    has_keyboard: bool = False
    has_mouse: bool = False
    voice_input: bool = False


class SolutionContext(BaseModel):
    """RICCO Solution-specific context"""
    solution_id: str
    solution_name: str
    
    # User's role in solution
    user_role: str = "user"  # user, seller, admin, provider
    
    # Active entities
    active_entity_id: Optional[str] = None
    active_entity_type: Optional[str] = None
    
    # Solution-specific data
    cart_items: List[Dict[str, Any]] = []
    pending_orders: List[Dict[str, Any]] = []
    saved_items: List[Dict[str, Any]] = []
    
    # Preferences
    view_preferences: Dict[str, Any] = {}
    notification_settings: Dict[str, bool] = {}
    
    # Recent activities
    recent_searches: List[str] = []
    recent_views: List[Dict[str, Any]] = []
    recent_actions: List[Dict[str, Any]] = []


class HorizontalContext(BaseModel):
    """Horizontal context shared across solutions"""
    # Cross-solution data
    energy_points_balance: float = 0.0
    trust_score: float = 0.0
    
    # Shared entities
    active_business_id: Optional[str] = None
    active_store_id: Optional[str] = None
    
    # Cross-solution permissions
    accessible_solutions: List[str] = []
    solution_permissions: Dict[str, List[str]] = {}
    
    # Global preferences
    theme: str = "light"
    language: str = "es"
    currency: str = "USD"
    
    # Notifications
    unread_notifications: int = 0
    pending_tasks: List[Dict[str, Any]] = []


class VerticalContext(BaseModel):
    """Vertical-specific deep context"""
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
    """Complete context bundle for AI agent"""
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
    conversation_history: List[Dict[str, Any]] = []
    current_intent: Optional[str] = None
    entities: Dict[str, Any] = {}
    
    # Skills arsenal
    available_skills: List[str] = []
    skill_context: Dict[str, Any] = {}
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None


# ============================================
# A2UI Service
# ============================================

class A2UIService:
    """
    A2UI Service - Agent-to-User Interface Generation
    
    Generates dynamic UI components based on:
    1. User context (personal, spatial, temporal, device)
    2. Solution context (horizontal and vertical)
    3. Skills arsenal context
    4. Conversation intent
    
    Supports renderers:
    - React (web)
    - Lit (web components)
    - Flutter/GenUI (mobile)
    """
    
    def __init__(self):
        self._sessions: Dict[str, A2UIState] = {}
        self._context_cache: Dict[str, ContextBundle] = {}
        
    async def create_session(
        self,
        user_id: str,
        solution: str,
        device_context: Optional[DeviceContext] = None,
    ) -> A2UIState:
        """Create a new A2UI session"""
        session_id = str(uuid.uuid4())
        
        state = A2UIState(
            session_id=session_id,
            user_id=user_id,
            solution=solution,
            context={
                "device": device_context.model_dump() if device_context else {},
            },
        )
        
        self._sessions[session_id] = state
        logger.info(f"Created A2UI session {session_id} for user {user_id}")
        
        return state
    
    async def get_session(self, session_id: str) -> Optional[A2UIState]:
        """Get session by ID"""
        return self._sessions.get(session_id)
    
    async def update_state(
        self,
        session_id: str,
        form_data: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> Optional[A2UIState]:
        """Update session state"""
        state = self._sessions.get(session_id)
        if not state:
            return None
        
        if form_data:
            state.form_data.update(form_data)
        
        if context:
            state.context.update(context)
        
        state.updated_at = datetime.utcnow()
        return state
    
    # ============================================
    # Context Engineering
    # ============================================
    
    async def build_context_bundle(
        self,
        user_id: str,
        session_id: str,
        solution: str,
        request_context: Optional[Dict[str, Any]] = None,
    ) -> ContextBundle:
        """
        Build comprehensive context bundle for AI agent
        
        This is the core of Context Engineering - combining multiple
        context sources into a unified bundle for the AI agent.
        """
        now = datetime.utcnow()
        
        # Build temporal context
        hour = now.hour
        if 6 <= hour < 12:
            time_of_day = "morning"
        elif 12 <= hour < 18:
            time_of_day = "afternoon"
        elif 18 <= hour < 22:
            time_of_day = "evening"
        else:
            time_of_day = "night"
        
        temporal = TemporalContext(
            current_time=now,
            timezone=request_context.get("timezone", "UTC") if request_context else "UTC",
            time_of_day=time_of_day,
            day_of_week=now.strftime("%A").lower(),
            is_weekend=now.weekday() >= 5,
            month=now.month,
            quarter=(now.month - 1) // 3 + 1,
        )
        
        # Build personal context (would be fetched from RICCO ID)
        personal = PersonalContext(
            user_id=user_id,
            language=request_context.get("language", "es") if request_context else "es",
            timezone=temporal.timezone,
        )
        
        # Build device context from request
        device = None
        if request_context and "device" in request_context:
            device_data = request_context["device"]
            device = DeviceContext(
                device_type=device_data.get("type", "mobile"),
                platform=device_data.get("platform", "unknown"),
                screen_width=device_data.get("screen_width", 375),
                screen_height=device_data.get("screen_height", 667),
                battery_level=device_data.get("battery_level"),
                network_type=device_data.get("network_type", "wifi"),
            )
        
        # Build spatial context from request
        spatial = None
        if request_context and "location" in request_context:
            loc_data = request_context["location"]
            spatial = SpatialContext(
                latitude=loc_data.get("latitude"),
                longitude=loc_data.get("longitude"),
                city=loc_data.get("city"),
                country=loc_data.get("country"),
            )
        
        # Build solution context
        solution_context = SolutionContext(
            solution_id=solution,
            solution_name=solution.replace("ricco-", "").title(),
        )
        
        # Build horizontal context
        horizontal = HorizontalContext(
            accessible_solutions=list(request_context.get("permissions", {}).keys()) if request_context else [],
        )
        
        # Create bundle
        bundle = ContextBundle(
            session_id=session_id,
            user_id=user_id,
            personal=personal,
            spatial=spatial,
            temporal=temporal,
            device=device,
            solution=solution_context,
            horizontal=horizontal,
            available_skills=request_context.get("skills", []) if request_context else [],
        )
        
        # Cache the bundle
        self._context_cache[session_id] = bundle
        
        return bundle
    
    async def get_context_bundle(self, session_id: str) -> Optional[ContextBundle]:
        """Get cached context bundle"""
        return self._context_cache.get(session_id)
    
    # ============================================
    # UI Generation
    # ============================================
    
    async def generate_response(
        self,
        session_id: str,
        agent_response: str,
        intent: Optional[str] = None,
        entities: Optional[Dict[str, Any]] = None,
        context_bundle: Optional[ContextBundle] = None,
    ) -> A2UIResponse:
        """
        Generate A2UI response from agent response
        
        Converts text-based agent responses into structured UI components
        optimized for the user's device and context.
        """
        state = await self.get_session(session_id)
        if not state:
            raise ValueError(f"Session {session_id} not found")
        
        # Get or use context bundle
        if not context_bundle:
            context_bundle = self._context_cache.get(session_id)
        
        # Analyze response to determine component structure
        components = await self._analyze_and_create_components(
            agent_response,
            intent,
            entities,
            context_bundle,
        )
        
        # Generate suggestions based on context
        suggestions = await self._generate_suggestions(
            intent,
            entities,
            context_bundle,
        )
        
        # Create response
        response = A2UIResponse(
            conversation_id=session_id,
            solution=state.solution,
            components=components,
            suggestions=suggestions,
            context={
                "intent": intent,
                "entities": entities or {},
            },
            metadata={
                "device_type": context_bundle.device.device_type if context_bundle and context_bundle.device else "mobile",
                "platform": context_bundle.device.platform if context_bundle and context_bundle.device else "unknown",
            },
        )
        
        return response
    
    async def _analyze_and_create_components(
        self,
        response: str,
        intent: Optional[str],
        entities: Optional[Dict[str, Any]],
        context: Optional[ContextBundle],
    ) -> List[A2UIComponent]:
        """Analyze response and create appropriate components"""
        components = []
        
        # Detect response type and create appropriate UI
        if intent:
            intent_components = await self._create_intent_based_components(
                intent, response, entities, context
            )
            components.extend(intent_components)
        else:
            # Default text response
            components.append(A2UIComponent(
                type=ComponentType.TEXT,
                properties={"content": response},
            ))
        
        return components
    
    async def _create_intent_based_components(
        self,
        intent: str,
        response: str,
        entities: Optional[Dict[str, Any]],
        context: Optional[ContextBundle],
    ) -> List[A2UIComponent]:
        """Create components based on detected intent"""
        components = []
        
        # Intent-specific component generation
        intent_handlers = {
            "product_search": self._create_product_search_components,
            "order_status": self._create_order_status_components,
            "appointment_booking": self._create_appointment_components,
            "tracking_request": self._create_tracking_components,
            "payment": self._create_payment_components,
            "form_fill": self._create_form_components,
            "navigation": self._create_navigation_components,
            "confirmation": self._create_confirmation_components,
        }
        
        handler = intent_handlers.get(intent)
        if handler:
            components = await handler(response, entities, context)
        else:
            # Default: create text component
            components.append(A2UIComponent(
                type=ComponentType.CARD,
                children=[
                    A2UIComponent(
                        type=ComponentType.TEXT,
                        properties={"content": response},
                    )
                ],
                style=ComponentStyle(
                    padding="16px",
                    borderRadius="8px",
                ),
            ))
        
        return components
    
    # ============================================
    # Intent-Specific Component Generators
    # ============================================
    
    async def _create_product_search_components(
        self,
        response: str,
        entities: Optional[Dict[str, Any]],
        context: Optional[ContextBundle],
    ) -> List[A2UIComponent]:
        """Create product search result components"""
        products = entities.get("products", []) if entities else []
        
        components = []
        
        # Header
        components.append(A2UIComponent(
            type=ComponentType.HEADING,
            properties={"level": 2, "content": "Resultados de búsqueda"},
        ))
        
        # Product grid
        if products:
            product_components = []
            for product in products[:6]:  # Limit to 6 products
                product_components.append(A2UIComponent(
                    type=ComponentType.PRODUCT_CARD,
                    properties={
                        "product_id": product.get("id"),
                        "name": product.get("name"),
                        "price": product.get("price"),
                        "image": product.get("image"),
                        "rating": product.get("rating"),
                    },
                    actions={
                        "click": ComponentAction(
                            type="navigate",
                            navigation={"route": f"/product/{product.get('id')}"},
                        ),
                        "add_to_cart": ComponentAction(
                            type="api_call",
                            endpoint="/api/cart/add",
                            method="POST",
                            payload={"product_id": product.get("id")},
                        ),
                    },
                ))
            
            components.append(A2UIComponent(
                type=ComponentType.GRID,
                children=product_components,
                properties={"columns": 2},
                style=ComponentStyle(gap="16px"),
            ))
        else:
            # No products found
            components.append(A2UIComponent(
                type=ComponentType.TEXT,
                properties={"content": "No se encontraron productos. Intenta con otros términos."},
            ))
        
        return components
    
    async def _create_order_status_components(
        self,
        response: str,
        entities: Optional[Dict[str, Any]],
        context: Optional[ContextBundle],
    ) -> List[A2UIComponent]:
        """Create order status components"""
        order = entities.get("order", {}) if entities else {}
        
        components = []
        
        # Order summary card
        components.append(A2UIComponent(
            type=ComponentType.ORDER_SUMMARY,
            properties={
                "order_id": order.get("id", "N/A"),
                "status": order.get("status", "pending"),
                "total": order.get("total", 0),
                "items_count": order.get("items_count", 0),
                "estimated_delivery": order.get("estimated_delivery"),
            },
        ))
        
        # Tracking timeline
        if order.get("tracking"):
            tracking_events = order["tracking"]
            timeline_items = []
            for event in tracking_events:
                timeline_items.append(A2UIComponent(
                    type=ComponentType.CARD,
                    properties={
                        "title": event.get("status"),
                        "subtitle": event.get("date"),
                        "description": event.get("location"),
                    },
                ))
            
            components.append(A2UIComponent(
                type=ComponentType.TIMELINE,
                children=timeline_items,
            ))
        
        return components
    
    async def _create_appointment_components(
        self,
        response: str,
        entities: Optional[Dict[str, Any]],
        context: Optional[ContextBundle],
    ) -> List[A2UIComponent]:
        """Create appointment booking components"""
        appointment = entities.get("appointment", {}) if entities else {}
        
        components = []
        
        # Appointment card
        components.append(A2UIComponent(
            type=ComponentType.APPOINTMENT_CARD,
            properties={
                "provider": appointment.get("provider"),
                "date": appointment.get("date"),
                "time": appointment.get("time"),
                "location": appointment.get("location"),
                "type": appointment.get("type"),
            },
            actions={
                "confirm": ComponentAction(
                    type="api_call",
                    endpoint="/api/appointments/confirm",
                    method="POST",
                ),
                "reschedule": ComponentAction(
                    type="dialog",
                    dialog={"type": "reschedule_form"},
                ),
                "cancel": ComponentAction(
                    type="dialog",
                    dialog={"type": "cancel_confirmation"},
                ),
            },
        ))
        
        return components
    
    async def _create_tracking_components(
        self,
        response: str,
        entities: Optional[Dict[str, Any]],
        context: Optional[ContextBundle],
    ) -> List[A2UIComponent]:
        """Create tracking info components"""
        tracking = entities.get("tracking", {}) if entities else {}
        
        components = []
        
        # Tracking info card
        components.append(A2UIComponent(
            type=ComponentType.TRACKING_INFO,
            properties={
                "tracking_number": tracking.get("tracking_number"),
                "status": tracking.get("status"),
                "origin": tracking.get("origin"),
                "destination": tracking.get("destination"),
                "estimated_delivery": tracking.get("estimated_delivery"),
                "carrier": tracking.get("carrier"),
            },
        ))
        
        # Map if location available
        if tracking.get("current_location"):
            components.append(A2UIComponent(
                type=ComponentType.MAP,
                properties={
                    "center": tracking["current_location"],
                    "markers": [tracking["current_location"]],
                    "zoom": 12,
                },
            ))
        
        return components
    
    async def _create_payment_components(
        self,
        response: str,
        entities: Optional[Dict[str, Any]],
        context: Optional[ContextBundle],
    ) -> List[A2UIComponent]:
        """Create payment form components"""
        payment = entities.get("payment", {}) if entities else {}
        
        components = []
        
        # Payment summary
        components.append(A2UIComponent(
            type=ComponentType.CARD,
            children=[
                A2UIComponent(
                    type=ComponentType.HEADING,
                    properties={"level": 3, "content": "Resumen de Pago"},
                ),
                A2UIComponent(
                    type=ComponentType.TEXT,
                    properties={"content": f"Total: ${payment.get('amount', 0):.2f}"},
                ),
            ],
        ))
        
        # Payment form
        components.append(A2UIComponent(
            type=ComponentType.PAYMENT_FORM,
            properties={
                "amount": payment.get("amount"),
                "currency": payment.get("currency", "USD"),
                "methods": payment.get("methods", ["card", "energy_points"]),
            },
            actions={
                "submit": ComponentAction(
                    type="api_call",
                    endpoint="/api/payments/process",
                    method="POST",
                ),
            },
        ))
        
        return components
    
    async def _create_form_components(
        self,
        response: str,
        entities: Optional[Dict[str, Any]],
        context: Optional[ContextBundle],
    ) -> List[A2UIComponent]:
        """Create dynamic form components"""
        form_schema = entities.get("form", {}) if entities else {}
        
        components = []
        form_children = []
        
        # Generate form fields from schema
        for field in form_schema.get("fields", []):
            field_type = field.get("type", "text")
            
            component_type = {
                "text": ComponentType.TEXT_FIELD,
                "textarea": ComponentType.TEXT_AREA,
                "select": ComponentType.SELECT,
                "checkbox": ComponentType.CHECKBOX,
                "date": ComponentType.DATE_PICKER,
            }.get(field_type, ComponentType.TEXT_FIELD)
            
            form_children.append(A2UIComponent(
                type=component_type,
                properties={
                    "name": field.get("name"),
                    "label": field.get("label"),
                    "placeholder": field.get("placeholder"),
                    "options": field.get("options", []),
                    "value": field.get("value"),
                },
                validation=ComponentValidation(
                    required=field.get("required", False),
                    minLength=field.get("min_length"),
                    maxLength=field.get("max_length"),
                    pattern=field.get("pattern"),
                ) if field.get("validation") else None,
            ))
        
        # Submit button
        form_children.append(A2UIComponent(
            type=ComponentType.BUTTON,
            properties={
                "label": form_schema.get("submit_label", "Enviar"),
                "variant": "primary",
            },
            actions={
                "click": ComponentAction(
                    type="submit",
                    endpoint=form_schema.get("endpoint"),
                    method=form_schema.get("method", "POST"),
                ),
            },
        ))
        
        components.append(A2UIComponent(
            type=ComponentType.CONTAINER,
            children=form_children,
            properties={"tag": "form"},
            style=ComponentStyle(
                display="flex",
                flexDirection="column",
                gap="16px",
            ),
        ))
        
        return components
    
    async def _create_navigation_components(
        self,
        response: str,
        entities: Optional[Dict[str, Any]],
        context: Optional[ContextBundle],
    ) -> List[A2UIComponent]:
        """Create navigation components"""
        navigation = entities.get("navigation", {}) if entities else {}
        
        components = []
        
        # Breadcrumb if applicable
        if navigation.get("breadcrumb"):
            items = navigation["breadcrumb"]
            breadcrumb_items = []
            for item in items:
                breadcrumb_items.append(A2UIComponent(
                    type=ComponentType.TEXT,
                    properties={"content": item.get("label")},
                    actions={
                        "click": ComponentAction(
                            type="navigate",
                            navigation={"route": item.get("route")},
                        ),
                    } if item.get("route") else {},
                ))
            
            components.append(A2UIComponent(
                type=ComponentType.BREADCRUMB,
                children=breadcrumb_items,
            ))
        
        # Navigation card
        components.append(A2UIComponent(
            type=ComponentType.CARD,
            children=[
                A2UIComponent(
                    type=ComponentType.TEXT,
                    properties={"content": response},
                ),
            ],
        ))
        
        return components
    
    async def _create_confirmation_components(
        self,
        response: str,
        entities: Optional[Dict[str, Any]],
        context: Optional[ContextBundle],
    ) -> List[A2UIComponent]:
        """Create confirmation dialog components"""
        confirmation = entities.get("confirmation", {}) if entities else {}
        
        components = []
        
        # Confirmation dialog
        components.append(A2UIComponent(
            type=ComponentType.DIALOG,
            properties={
                "title": confirmation.get("title", "Confirmar acción"),
                "content": response,
                "type": confirmation.get("type", "info"),
            },
            children=[
                A2UIComponent(
                    type=ComponentType.BUTTON_GROUP,
                    children=[
                        A2UIComponent(
                            type=ComponentType.BUTTON,
                            properties={"label": "Cancelar", "variant": "secondary"},
                            actions={
                                "click": ComponentAction(type="custom", payload={"action": "dismiss"}),
                            },
                        ),
                        A2UIComponent(
                            type=ComponentType.BUTTON,
                            properties={"label": "Confirmar", "variant": "primary"},
                            actions={
                                "click": ComponentAction(
                                    type="api_call",
                                    endpoint=confirmation.get("endpoint"),
                                    method="POST",
                                ),
                            },
                        ),
                    ],
                    style=ComponentStyle(gap="8px"),
                ),
            ],
        ))
        
        return components
    
    async def _generate_suggestions(
        self,
        intent: Optional[str],
        entities: Optional[Dict[str, Any]],
        context: Optional[ContextBundle],
    ) -> List[str]:
        """Generate contextual suggestions"""
        suggestions = []
        
        # Intent-based suggestions
        intent_suggestions = {
            "product_search": [
                "Ver ofertas del día",
                "Productos más vendidos",
                "Filtrar por precio",
            ],
            "order_status": [
                "Ver detalles del pedido",
                "Contactar vendedor",
                "Solicitar devolución",
            ],
            "appointment_booking": [
                "Ver próximas citas",
                "Reprogramar cita",
                "Cancelar cita",
            ],
            "tracking_request": [
                "Ver historial de envíos",
                "Contactar transportista",
                "Notificar al destinatario",
            ],
        }
        
        if intent and intent in intent_suggestions:
            suggestions.extend(intent_suggestions[intent])
        
        # Context-based suggestions
        if context and context.temporal:
            time_of_day = context.temporal.time_of_day
            if time_of_day == "morning":
                suggestions.append("Buenos días, ¿en qué puedo ayudarte?")
            elif time_of_day == "evening":
                suggestions.append("¿Necesitas algo antes de terminar el día?")
        
        return suggestions[:5]  # Limit to 5 suggestions
    
    # ============================================
    # Renderer Export Methods
    # ============================================
    
    async def export_for_react(
        self,
        response: A2UIResponse,
    ) -> Dict[str, Any]:
        """
        Export A2UI response for React renderer
        
        Format compatible with:
        https://github.com/google/A2UI/tree/main/renderers/react
        """
        return {
            "id": response.id,
            "conversationId": response.conversation_id,
            "status": response.status.value,
            "components": [self._component_to_react(c) for c in response.components],
            "suggestions": response.suggestions,
            "metadata": response.metadata,
        }
    
    def _component_to_react(self, component: A2UIComponent) -> Dict[str, Any]:
        """Convert component to React format"""
        return {
            "id": component.id,
            "type": component.type.value,
            "props": component.properties,
            "style": component.style.model_dump() if component.style else None,
            "actions": {k: v.model_dump() for k, v in component.actions.items()},
            "children": [self._component_to_react(c) for c in component.children],
            "visible": component.visible,
            "disabled": not component.enabled,
        }
    
    async def export_for_lit(
        self,
        response: A2UIResponse,
    ) -> Dict[str, Any]:
        """
        Export A2UI response for Lit renderer
        
        Format compatible with:
        https://github.com/google/A2UI/tree/main/renderers/lit
        """
        return {
            "id": response.id,
            "conversationId": response.conversation_id,
            "status": response.status.value,
            "components": [self._component_to_lit(c) for c in response.components],
            "suggestions": response.suggestions,
        }
    
    def _component_to_lit(self, component: A2UIComponent) -> Dict[str, Any]:
        """Convert component to Lit/Web Component format"""
        return {
            "id": component.id,
            "tag": f"a2ui-{component.type.value}",
            "properties": component.properties,
            "styles": self._style_to_css(component.style) if component.style else None,
            "events": {k: v.model_dump() for k, v in component.actions.items()},
            "children": [self._component_to_lit(c) for c in component.children],
        }
    
    def _style_to_css(self, style: ComponentStyle) -> str:
        """Convert style object to CSS string"""
        css_map = {
            "width": "width",
            "height": "height",
            "padding": "padding",
            "margin": "margin",
            "backgroundColor": "background-color",
            "color": "color",
            "fontSize": "font-size",
            "fontWeight": "font-weight",
            "borderRadius": "border-radius",
            "boxShadow": "box-shadow",
            "display": "display",
            "flexDirection": "flex-direction",
            "justifyContent": "justify-content",
            "alignItems": "align-items",
            "gap": "gap",
        }
        
        css_parts = []
        for key, css_key in css_map.items():
            value = getattr(style, key, None)
            if value:
                css_parts.append(f"{css_key}: {value}")
        
        if style.custom:
            for key, value in style.custom.items():
                css_parts.append(f"{key}: {value}")
        
        return "; ".join(css_parts)
    
    async def export_for_flutter(
        self,
        response: A2UIResponse,
    ) -> Dict[str, Any]:
        """
        Export A2UI response for Flutter GenUI SDK
        
        Format compatible with Flutter GenUI SDK for we.ricco.com
        """
        return {
            "sessionId": response.conversation_id,
            "status": response.status.value,
            "widgets": [self._component_to_flutter(c) for c in response.components],
            "suggestions": response.suggestions,
            "quickActions": [a.model_dump() for a in response.quick_actions],
        }
    
    def _component_to_flutter(self, component: A2UIComponent) -> Dict[str, Any]:
        """Convert component to Flutter widget format"""
        # Map A2UI types to Flutter widgets
        flutter_type_map = {
            ComponentType.CONTAINER: "Container",
            ComponentType.GRID: "GridView",
            ComponentType.STACK: "Stack",
            ComponentType.FLEX: "Flex",
            ComponentType.TEXT: "Text",
            ComponentType.HEADING: "Text",
            ComponentType.IMAGE: "Image",
            ComponentType.ICON: "Icon",
            ComponentType.CARD: "Card",
            ComponentType.LIST: "ListView",
            ComponentType.TABLE: "Table",
            ComponentType.TEXT_FIELD: "TextField",
            ComponentType.TEXT_AREA: "TextField",
            ComponentType.SELECT: "DropdownButton",
            ComponentType.CHECKBOX: "Checkbox",
            ComponentType.RADIO: "Radio",
            ComponentType.SWITCH: "Switch",
            ComponentType.SLIDER: "Slider",
            ComponentType.DATE_PICKER: "DatePicker",
            ComponentType.TIME_PICKER: "TimePicker",
            ComponentType.FILE_UPLOAD: "FilePicker",
            ComponentType.BUTTON: "ElevatedButton",
            ComponentType.BUTTON_GROUP: "Row",
            ComponentType.FAB: "FloatingActionButton",
            ComponentType.DIALOG: "AlertDialog",
            ComponentType.SNACKBAR: "SnackBar",
            ComponentType.PROGRESS: "CircularProgressIndicator",
            ComponentType.TABS: "TabBar",
            ComponentType.ACCORDION: "ExpansionTile",
            ComponentType.STEPPER: "Stepper",
            ComponentType.CHART: "Chart",
            ComponentType.MAP: "GoogleMap",
            ComponentType.CALENDAR: "TableCalendar",
            ComponentType.PRODUCT_CARD: "ProductCard",
            ComponentType.USER_PROFILE: "UserProfile",
            ComponentType.ORDER_SUMMARY: "OrderSummary",
            ComponentType.TRACKING_INFO: "TrackingInfo",
            ComponentType.APPOINTMENT_CARD: "AppointmentCard",
            ComponentType.PAYMENT_FORM: "PaymentForm",
        }
        
        return {
            "type": flutter_type_map.get(component.type, "Container"),
            "properties": self._adapt_props_for_flutter(component),
            "style": self._adapt_style_for_flutter(component.style) if component.style else None,
            "actions": {k: self._adapt_action_for_flutter(v) for k, v in component.actions.items()},
            "children": [self._component_to_flutter(c) for c in component.children],
            "visible": component.visible,
            "enabled": component.enabled,
        }
    
    def _adapt_props_for_flutter(self, component: A2UIComponent) -> Dict[str, Any]:
        """Adapt component properties for Flutter"""
        props = component.properties.copy()
        
        # Flutter-specific adaptations
        if component.type == ComponentType.TEXT:
            props["data"] = props.pop("content", "")
            if component.type == ComponentType.HEADING:
                props["style"] = f"headline{props.pop('level', 2)}"
        
        elif component.type == ComponentType.BUTTON:
            props["child"] = {"type": "Text", "data": props.pop("label", "")}
            props["style"] = props.pop("variant", "elevated")
        
        elif component.type == ComponentType.IMAGE:
            props["src"] = props.pop("src") or props.pop("url", "")
        
        return props
    
    def _adapt_style_for_flutter(self, style: ComponentStyle) -> Dict[str, Any]:
        """Adapt style for Flutter"""
        return {
            "width": style.width,
            "height": style.height,
            "padding": self._parse_edge_insets(style.padding),
            "margin": self._parse_edge_insets(style.margin),
            "decoration": {
                "color": style.backgroundColor,
                "borderRadius": style.borderRadius,
                "boxShadow": style.boxShadow,
            } if style.backgroundColor or style.borderRadius or style.boxShadow else None,
            "alignment": self._parse_alignment(style.justifyContent, style.alignItems),
        }
    
    def _parse_edge_insets(self, value: Optional[str]) -> Optional[Dict[str, float]]:
        """Parse padding/margin string to Flutter EdgeInsets"""
        if not value:
            return None
        
        # Simple parsing - in production would be more robust
        parts = value.split()
        if len(parts) == 1:
            return {"all": float(parts[0].replace("px", ""))}
        elif len(parts) == 2:
            return {
                "vertical": float(parts[0].replace("px", "")),
                "horizontal": float(parts[1].replace("px", "")),
            }
        return None
    
    def _parse_alignment(self, justify: Optional[str], align: Optional[str]) -> Optional[str]:
        """Parse CSS alignment to Flutter alignment"""
        alignment_map = {
            "center": "Alignment.center",
            "start": "Alignment.centerLeft",
            "end": "Alignment.centerRight",
            "space-between": "Alignment.center",
        }
        return alignment_map.get(justify or "", None)
    
    def _adapt_action_for_flutter(self, action: ComponentAction) -> Dict[str, Any]:
        """Adapt action for Flutter"""
        return {
            "type": action.type,
            "payload": action.payload,
            "endpoint": action.endpoint,
            "method": action.method,
            "route": action.navigation.get("route") if action.navigation else None,
        }
    
    # ============================================
    # Health Check
    # ============================================
    
    async def health_check(self) -> Dict[str, Any]:
        """Check A2UI service health"""
        return {
            "status": "healthy",
            "active_sessions": len(self._sessions),
            "cached_contexts": len(self._context_cache),
            "supported_renderers": ["react", "lit", "flutter"],
        }


# Singleton
_a2ui_service: Optional[A2UIService] = None

def get_a2ui_service() -> A2UIService:
    global _a2ui_service
    if _a2ui_service is None:
        _a2ui_service = A2UIService()
    return _a2ui_service
