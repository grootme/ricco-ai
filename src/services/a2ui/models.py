"""
A2UI Component Models
Pydantic models for A2UI component definitions

Implements: Data Transfer Object Pattern (DTO)
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
import uuid


class ComponentType(str, Enum):
    """A2UI Component types"""
    # Layout
    CONTAINER = "container"
    GRID = "grid"
    STACK = "stack"
    FLEX = "flex"
    COLUMN = "column"
    ROW = "row"
    
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
    ICON_BUTTON = "iconButton"
    
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
    APP_BAR = "appBar"
    BOTTOM_BAR = "bottomBar"
    
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
    MESSAGE_BUBBLE = "messageBubble"
    CHIP = "chip"


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


class ComponentStyle(BaseModel):
    """Style properties for components - Builder Pattern friendly"""
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
    
    class Config:
        use_enum_values = True


class ComponentAction(BaseModel):
    """Action configuration for interactive components"""
    type: str  # navigate, api_call, dialog, submit, custom
    payload: Dict[str, Any] = Field(default_factory=dict)
    endpoint: Optional[str] = None
    method: Optional[str] = None
    navigation: Optional[Dict[str, str]] = None
    dialog: Optional[Dict[str, Any]] = None
    event: Optional[Dict[str, Any]] = None
    
    class Config:
        use_enum_values = True


class ComponentValidation(BaseModel):
    """Validation rules for input components"""
    required: bool = False
    minLength: Optional[int] = None
    maxLength: Optional[int] = None
    pattern: Optional[str] = None
    min: Optional[float] = None
    max: Optional[float] = None
    custom: Optional[str] = None  # Custom validation function name
    
    class Config:
        use_enum_values = True


class A2UIComponent(BaseModel):
    """A2UI Component definition - Composite Pattern"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    type: ComponentType
    children: List["A2UIComponent"] = Field(default_factory=list)
    properties: Dict[str, Any] = Field(default_factory=dict)
    style: Optional[ComponentStyle] = None
    actions: Dict[str, ComponentAction] = Field(default_factory=dict)
    validation: Optional[ComponentValidation] = None
    visible: bool = True
    enabled: bool = True
    loading: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
    semanticLabel: Optional[str] = None  # For accessibility
    
    class Config:
        use_enum_values = True


class A2UIComponentInstance(A2UIComponent):
    """Extended component with rendering metadata"""
    rendered_at: Optional[datetime] = None
    interaction_count: int = 0
    last_interaction: Optional[datetime] = None


class A2UIResponse(BaseModel):
    """Complete A2UI response for rendering"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: Optional[str] = None
    message_id: Optional[str] = None
    agent_id: Optional[str] = None
    solution: Optional[str] = None
    status: ResponseStatus = ResponseStatus.SUCCESS
    components: List[A2UIComponent] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    suggestions: List[str] = Field(default_factory=list)
    quick_actions: List[ComponentAction] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True


class A2UIState(BaseModel):
    """State management for A2UI sessions - State Pattern"""
    session_id: str
    user_id: Optional[str] = None
    solution: Optional[str] = None
    form_data: Dict[str, Any] = Field(default_factory=dict)
    navigation_stack: List[str] = Field(default_factory=list)
    active_dialog: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True


# Resolve forward reference
A2UIComponent.model_rebuild()


# =============================================================================
# Component Builder (Builder Pattern)
# =============================================================================

class ComponentBuilder:
    """
    Builder for creating A2UI components fluently.
    
    Implements the Builder Pattern for complex component construction.
    
    Usage:
        component = (ComponentBuilder(ComponentType.CARD)
            .with_id("my-card")
            .with_property("title", "Hello")
            .with_style(padding="16px")
            .with_action("click", ComponentAction(type="navigate", navigation={"route": "/home"}))
            .add_child(ComponentBuilder(ComponentType.TEXT).with_property("content", "World").build())
            .build())
    """
    
    def __init__(self, component_type: ComponentType):
        self._type = component_type
        self._id: Optional[str] = None
        self._properties: Dict[str, Any] = {}
        self._style: Optional[ComponentStyle] = None
        self._actions: Dict[str, ComponentAction] = {}
        self._validation: Optional[ComponentValidation] = None
        self._children: List[A2UIComponent] = []
        self._visible: bool = True
        self._enabled: bool = True
        self._metadata: Dict[str, Any] = {}
        self._semantic_label: Optional[str] = None
    
    def with_id(self, id: str) -> 'ComponentBuilder':
        """Set component ID"""
        self._id = id
        return self
    
    def with_property(self, key: str, value: Any) -> 'ComponentBuilder':
        """Add a property"""
        self._properties[key] = value
        return self
    
    def with_properties(self, properties: Dict[str, Any]) -> 'ComponentBuilder':
        """Add multiple properties"""
        self._properties.update(properties)
        return self
    
    def with_style(self, **style_kwargs) -> 'ComponentBuilder':
        """Set style properties"""
        if self._style is None:
            self._style = ComponentStyle()
        for key, value in style_kwargs.items():
            if hasattr(self._style, key):
                setattr(self._style, key, value)
        return self
    
    def with_action(self, event: str, action: ComponentAction) -> 'ComponentBuilder':
        """Add an action for an event"""
        self._actions[event] = action
        return self
    
    def with_validation(self, **validation_kwargs) -> 'ComponentBuilder':
        """Set validation rules"""
        self._validation = ComponentValidation(**validation_kwargs)
        return self
    
    def add_child(self, child: A2UIComponent) -> 'ComponentBuilder':
        """Add a child component"""
        self._children.append(child)
        return self
    
    def with_children(self, children: List[A2UIComponent]) -> 'ComponentBuilder':
        """Set all children"""
        self._children = children
        return self
    
    def with_visibility(self, visible: bool) -> 'ComponentBuilder':
        """Set visibility"""
        self._visible = visible
        return self
    
    def with_enabled(self, enabled: bool) -> 'ComponentBuilder':
        """Set enabled state"""
        self._enabled = enabled
        return self
    
    def with_metadata(self, key: str, value: Any) -> 'ComponentBuilder':
        """Add metadata"""
        self._metadata[key] = value
        return self
    
    def with_semantic_label(self, label: str) -> 'ComponentBuilder':
        """Set accessibility label"""
        self._semantic_label = label
        return self
    
    def build(self) -> A2UIComponent:
        """Build the component"""
        return A2UIComponent(
            id=self._id or str(uuid.uuid4())[:8],
            type=self._type,
            children=self._children,
            properties=self._properties,
            style=self._style,
            actions=self._actions,
            validation=self._validation,
            visible=self._visible,
            enabled=self._enabled,
            metadata=self._metadata,
            semanticLabel=self._semantic_label
        )


# =============================================================================
# Response Builder (Builder Pattern)
# =============================================================================

class ResponseBuilder:
    """
    Builder for creating A2UI responses fluently.
    
    Usage:
        response = (ResponseBuilder()
            .with_conversation_id(conv_id)
            .with_component(my_component)
            .with_suggestion("Try this")
            .build())
    """
    
    def __init__(self):
        self._conversation_id: Optional[str] = None
        self._message_id: Optional[str] = None
        self._agent_id: Optional[str] = None
        self._solution: Optional[str] = None
        self._status: ResponseStatus = ResponseStatus.SUCCESS
        self._components: List[A2UIComponent] = []
        self._context: Dict[str, Any] = {}
        self._suggestions: List[str] = []
        self._quick_actions: List[ComponentAction] = []
        self._metadata: Dict[str, Any] = {}
    
    def with_conversation_id(self, id: str) -> 'ResponseBuilder':
        self._conversation_id = id
        return self
    
    def with_message_id(self, id: str) -> 'ResponseBuilder':
        self._message_id = id
        return self
    
    def with_agent_id(self, id: str) -> 'ResponseBuilder':
        self._agent_id = id
        return self
    
    def with_solution(self, solution: str) -> 'ResponseBuilder':
        self._solution = solution
        return self
    
    def with_status(self, status: ResponseStatus) -> 'ResponseBuilder':
        self._status = status
        return self
    
    def with_component(self, component: A2UIComponent) -> 'ResponseBuilder':
        self._components.append(component)
        return self
    
    def with_components(self, components: List[A2UIComponent]) -> 'ResponseBuilder':
        self._components.extend(components)
        return self
    
    def with_context(self, key: str, value: Any) -> 'ResponseBuilder':
        self._context[key] = value
        return self
    
    def with_suggestion(self, suggestion: str) -> 'ResponseBuilder':
        self._suggestions.append(suggestion)
        return self
    
    def with_quick_action(self, action: ComponentAction) -> 'ResponseBuilder':
        self._quick_actions.append(action)
        return self
    
    def with_metadata(self, key: str, value: Any) -> 'ResponseBuilder':
        self._metadata[key] = value
        return self
    
    def build(self) -> A2UIResponse:
        return A2UIResponse(
            conversation_id=self._conversation_id,
            message_id=self._message_id,
            agent_id=self._agent_id,
            solution=self._solution,
            status=self._status,
            components=self._components,
            context=self._context,
            suggestions=self._suggestions,
            quick_actions=self._quick_actions,
            metadata=self._metadata
        )
