"""
RICCO AI Service - React Renderer Integration
Integración con React Renderer para soluciones frontend

Basado en: https://github.com/google/A2UI/tree/main/renderers/react

Proporciona componentes React dinámicos para:
- commerce.ricco.com
- health.ricco.com
- Todas las soluciones web del ecosistema
"""

import json
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


# ============================================
# React Component Types
# ============================================

class ReactComponentType(str, Enum):
    """React component types"""
    # Layout
    BOX = "Box"
    CONTAINER = "Container"
    GRID = "Grid"
    STACK = "Stack"
    FLEX = "Flex"
    
    # Typography
    TEXT = "Text"
    HEADING = "Heading"
    PARAGRAPH = "Paragraph"
    LINK = "Link"
    
    # Data Display
    CARD = "Card"
    TABLE = "Table"
    LIST = "List"
    BADGE = "Badge"
    AVATAR = "Avatar"
    TAG = "Tag"
    
    # Input
    INPUT = "Input"
    TEXTAREA = "Textarea"
    SELECT = "Select"
    CHECKBOX = "Checkbox"
    RADIO = "Radio"
    SWITCH = "Switch"
    SLIDER = "Slider"
    DATEPICKER = "DatePicker"
    FILEUPLOAD = "FileUpload"
    
    # Buttons
    BUTTON = "Button"
    BUTTON_GROUP = "ButtonGroup"
    ICON_BUTTON = "IconButton"
    
    # Feedback
    ALERT = "Alert"
    DIALOG = "Dialog"
    DRAWER = "Drawer"
    TOAST = "Toast"
    PROGRESS = "Progress"
    SKELETON = "Skeleton"
    SPINNER = "Spinner"
    
    # Navigation
    TABS = "Tabs"
    ACCORDION = "Accordion"
    STEPPER = "Stepper"
    BREADCRUMB = "Breadcrumb"
    MENU = "Menu"
    
    # Data Visualization
    CHART = "Chart"
    MAP = "Map"
    CALENDAR = "Calendar"
    TIMELINE = "Timeline"
    
    # RICCO Custom
    PRODUCT_CARD = "ProductCard"
    ORDER_SUMMARY = "OrderSummary"
    TRACKING_INFO = "TrackingInfo"
    APPOINTMENT_CARD = "AppointmentCard"
    PAYMENT_FORM = "PaymentForm"
    USER_PROFILE = "UserProfile"
    ENERGY_POINTS = "EnergyPoints"
    TRUST_SCORE = "TrustScore"


# ============================================
# React Component Models
# ============================================

class ReactStyle(BaseModel):
    """React inline styles or styled-components props"""
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
    gridTemplateColumns: Optional[str] = None
    position: Optional[str] = None
    top: Optional[str] = None
    right: Optional[str] = None
    bottom: Optional[str] = None
    left: Optional[str] = None
    zIndex: Optional[int] = None
    opacity: Optional[float] = None
    transition: Optional[str] = None
    transform: Optional[str] = None
    custom: Optional[Dict[str, Any]] = None


class ReactAction(BaseModel):
    """React event handler"""
    type: str  # click, change, submit, focus, blur
    handler: str  # Function name or action type
    payload: Dict[str, Any] = {}
    endpoint: Optional[str] = None
    method: Optional[str] = None
    navigation: Optional[Dict[str, str]] = None
    dialog: Optional[Dict[str, Any]] = None


class ReactValidation(BaseModel):
    """Form validation rules"""
    required: bool = False
    minLength: Optional[int] = None
    maxLength: Optional[int] = None
    pattern: Optional[str] = None
    min: Optional[float] = None
    max: Optional[float] = None
    custom: Optional[str] = None


class ReactComponent(BaseModel):
    """React component definition"""
    type: ReactComponentType
    key: Optional[str] = None
    children: List["ReactComponent"] = []
    props: Dict[str, Any] = {}
    style: Optional[ReactStyle] = None
    className: Optional[str] = None
    events: Dict[str, ReactAction] = {}
    validation: Optional[ReactValidation] = None
    visible: bool = True
    disabled: bool = False
    loading: bool = False
    metadata: Dict[str, Any] = {}


# ============================================
# React Renderer Service
# ============================================

class ReactRendererService:
    """
    React Renderer Service for RICCO frontend solutions
    
    Converts A2UI components to React components with:
    - styled-components support
    - Material-UI / Chakra UI compatibility
    - shadcn/ui component mapping
    """
    
    def __init__(self):
        self._component_map = self._build_component_map()
        self._ui_library = "shadcn"  # shadcn, material, chakra
    
    def _build_component_map(self) -> Dict[str, str]:
        """Map A2UI types to React component names"""
        return {
            # Layout
            "container": "Box",
            "grid": "Grid",
            "stack": "Stack",
            "flex": "Flex",
            
            # Typography
            "text": "Text",
            "heading": "Heading",
            "paragraph": "Paragraph",
            
            # Display
            "card": "Card",
            "table": "Table",
            "list": "List",
            "image": "Image",
            
            # Input
            "textField": "Input",
            "textArea": "Textarea",
            "select": "Select",
            "checkbox": "Checkbox",
            "radio": "Radio",
            "switch": "Switch",
            "slider": "Slider",
            "datePicker": "DatePicker",
            "fileUpload": "FileUpload",
            
            # Buttons
            "button": "Button",
            "buttonGroup": "ButtonGroup",
            
            # Feedback
            "dialog": "Dialog",
            "snackbar": "Toast",
            "progress": "Progress",
            
            # Navigation
            "tabs": "Tabs",
            "accordion": "Accordion",
            "stepper": "Stepper",
            
            # RICCO Custom
            "productCard": "ProductCard",
            "orderSummary": "OrderSummary",
            "trackingInfo": "TrackingInfo",
            "appointmentCard": "AppointmentCard",
            "paymentForm": "PaymentForm",
        }
    
    def render_component(self, component: ReactComponent) -> Dict[str, Any]:
        """
        Render a single React component to JSON
        
        This JSON can be used by the React frontend to render components
        """
        result = {
            "type": component.type.value,
            "key": component.key,
            "props": {
                **component.props,
                "className": component.className,
                "disabled": component.disabled,
                "loading": component.loading,
            },
            "children": [self.render_component(c) for c in component.children],
        }
        
        # Add styles
        if component.style:
            result["props"]["style"] = self._style_to_object(component.style)
        
        # Add event handlers
        if component.events:
            result["events"] = {
                event: action.model_dump()
                for event, action in component.events.items()
            }
        
        # Add validation
        if component.validation:
            result["validation"] = component.validation.model_dump()
        
        # Add visibility
        if not component.visible:
            result["props"]["style"] = result["props"].get("style", {})
            result["props"]["style"]["display"] = "none"
        
        return result
    
    def _style_to_object(self, style: ReactStyle) -> Dict[str, Any]:
        """Convert style model to CSS object"""
        css = {}
        
        style_map = {
            "width": "width",
            "height": "height",
            "padding": "padding",
            "margin": "margin",
            "backgroundColor": "backgroundColor",
            "color": "color",
            "fontSize": "fontSize",
            "fontWeight": "fontWeight",
            "borderRadius": "borderRadius",
            "boxShadow": "boxShadow",
            "display": "display",
            "flexDirection": "flexDirection",
            "justifyContent": "justifyContent",
            "alignItems": "alignItems",
            "gap": "gap",
            "gridTemplateColumns": "gridTemplateColumns",
            "position": "position",
            "top": "top",
            "right": "right",
            "bottom": "bottom",
            "left": "left",
            "zIndex": "zIndex",
            "opacity": "opacity",
            "transition": "transition",
            "transform": "transform",
        }
        
        for attr, css_prop in style_map.items():
            value = getattr(style, attr, None)
            if value is not None:
                css[css_prop] = value
        
        if style.custom:
            css.update(style.custom)
        
        return css
    
    # ============================================
    # Component Builders
    # ============================================
    
    def build_text(
        self,
        content: str,
        variant: str = "body",
        style: Optional[ReactStyle] = None,
    ) -> ReactComponent:
        """Build a Text component"""
        return ReactComponent(
            type=ReactComponentType.TEXT,
            props={"content": content, "variant": variant},
            style=style,
        )
    
    def build_heading(
        self,
        content: str,
        level: int = 2,
        style: Optional[ReactStyle] = None,
    ) -> ReactComponent:
        """Build a Heading component"""
        return ReactComponent(
            type=ReactComponentType.HEADING,
            props={"content": content, "level": level},
            style=style,
        )
    
    def build_button(
        self,
        label: str,
        variant: str = "primary",
        size: str = "medium",
        onClick: Optional[ReactAction] = None,
        icon: Optional[str] = None,
        loading: bool = False,
        disabled: bool = False,
    ) -> ReactComponent:
        """Build a Button component"""
        events = {}
        if onClick:
            events["onClick"] = onClick
        
        return ReactComponent(
            type=ReactComponentType.BUTTON,
            props={
                "label": label,
                "variant": variant,
                "size": size,
                "icon": icon,
            },
            events=events,
            loading=loading,
            disabled=disabled,
        )
    
    def build_card(
        self,
        title: Optional[str] = None,
        subtitle: Optional[str] = None,
        content: List[ReactComponent] = [],
        actions: List[ReactComponent] = [],
        variant: str = "elevated",
    ) -> ReactComponent:
        """Build a Card component"""
        children = []
        
        if title:
            children.append(self.build_heading(title, level=3))
        
        if subtitle:
            children.append(self.build_text(subtitle, variant="body2"))
        
        children.extend(content)
        
        if actions:
            children.append(ReactComponent(
                type=ReactComponentType.FLEX,
                children=actions,
                style=ReactStyle(gap="8px", marginTop="16px"),
            ))
        
        return ReactComponent(
            type=ReactComponentType.CARD,
            children=children,
            props={"variant": variant},
            style=ReactStyle(padding="16px"),
        )
    
    def build_input(
        self,
        name: str,
        label: str,
        placeholder: Optional[str] = None,
        type: str = "text",
        required: bool = False,
        validation: Optional[ReactValidation] = None,
        onChange: Optional[ReactAction] = None,
    ) -> ReactComponent:
        """Build an Input component"""
        events = {}
        if onChange:
            events["onChange"] = onChange
        
        return ReactComponent(
            type=ReactComponentType.INPUT,
            props={
                "name": name,
                "label": label,
                "placeholder": placeholder,
                "type": type,
            },
            events=events,
            validation=validation or ReactValidation(required=required),
        )
    
    def build_form(
        self,
        fields: List[Dict[str, Any]],
        submit_label: str = "Enviar",
        submit_endpoint: str = "",
        method: str = "POST",
    ) -> ReactComponent:
        """Build a Form component"""
        children = []
        
        for field in fields:
            field_type = field.get("type", "text")
            
            if field_type in ["text", "email", "password", "number"]:
                children.append(self.build_input(
                    name=field.get("name", ""),
                    label=field.get("label", ""),
                    placeholder=field.get("placeholder"),
                    type=field_type,
                    required=field.get("required", False),
                    validation=ReactValidation(
                        required=field.get("required", False),
                        minLength=field.get("min_length"),
                        maxLength=field.get("max_length"),
                        pattern=field.get("pattern"),
                    ) if field.get("validation") else None,
                ))
            
            elif field_type == "select":
                children.append(ReactComponent(
                    type=ReactComponentType.SELECT,
                    props={
                        "name": field.get("name"),
                        "label": field.get("label"),
                        "options": field.get("options", []),
                        "value": field.get("value"),
                    },
                ))
            
            elif field_type == "textarea":
                children.append(ReactComponent(
                    type=ReactComponentType.TEXTAREA,
                    props={
                        "name": field.get("name"),
                        "label": field.get("label"),
                        "placeholder": field.get("placeholder"),
                        "rows": field.get("rows", 4),
                    },
                ))
        
        # Submit button
        children.append(self.build_button(
            label=submit_label,
            variant="primary",
            onClick=ReactAction(
                type="submit",
                endpoint=submit_endpoint,
                method=method,
            ),
        ))
        
        return ReactComponent(
            type=ReactComponentType.CONTAINER,
            children=children,
            props={"tag": "form"},
            style=ReactStyle(
                display="flex",
                flexDirection="column",
                gap="16px",
            ),
        )
    
    def build_product_card(
        self,
        product: Dict[str, Any],
    ) -> ReactComponent:
        """Build a Product Card component"""
        return ReactComponent(
            type=ReactComponentType.PRODUCT_CARD,
            props={
                "productId": product.get("id"),
                "name": product.get("name"),
                "price": product.get("price"),
                "currency": product.get("currency", "USD"),
                "imageUrl": product.get("image_url"),
                "rating": product.get("rating"),
                "reviewsCount": product.get("reviews_count"),
                "discount": product.get("discount"),
                "energyPoints": product.get("energy_points"),
            },
            events={
                "onClick": ReactAction(
                    type="navigate",
                    navigation={"route": f"/product/{product.get('id')}"},
                ),
                "onAddToCart": ReactAction(
                    type="api_call",
                    endpoint="/api/cart/add",
                    method="POST",
                    payload={"product_id": product.get("id")},
                ),
            },
        )
    
    def build_order_summary(
        self,
        order: Dict[str, Any],
    ) -> ReactComponent:
        """Build an Order Summary component"""
        return ReactComponent(
            type=ReactComponentType.ORDER_SUMMARY,
            props={
                "orderId": order.get("id"),
                "status": order.get("status"),
                "total": order.get("total"),
                "itemsCount": order.get("items_count"),
                "createdAt": order.get("created_at"),
                "estimatedDelivery": order.get("estimated_delivery"),
            },
            events={
                "onClick": ReactAction(
                    type="navigate",
                    navigation={"route": f"/order/{order.get('id')}"},
                ),
            },
        )
    
    def build_tracking_info(
        self,
        tracking: Dict[str, Any],
    ) -> ReactComponent:
        """Build a Tracking Info component"""
        events_data = tracking.get("events", [])
        timeline_items = []
        
        for event in events_data:
            timeline_items.append(ReactComponent(
                type=ReactComponentType.CARD,
                children=[
                    self.build_text(event.get("status", ""), variant="body2"),
                    self.build_text(event.get("date", ""), variant="caption"),
                    self.build_text(event.get("location", ""), variant="caption"),
                ],
                style=ReactStyle(padding="12px"),
            ))
        
        return ReactComponent(
            type=ReactComponentType.TRACKING_INFO,
            props={
                "trackingNumber": tracking.get("tracking_number"),
                "status": tracking.get("status"),
                "carrier": tracking.get("carrier"),
                "estimatedDelivery": tracking.get("estimated_delivery"),
            },
            children=[
                ReactComponent(
                    type=ReactComponentType.TIMELINE,
                    children=timeline_items,
                )
            ] if timeline_items else [],
        )
    
    def build_appointment_card(
        self,
        appointment: Dict[str, Any],
    ) -> ReactComponent:
        """Build an Appointment Card component"""
        return ReactComponent(
            type=ReactComponentType.APPOINTMENT_CARD,
            props={
                "appointmentId": appointment.get("id"),
                "providerName": appointment.get("provider_name"),
                "specialty": appointment.get("specialty"),
                "date": appointment.get("date"),
                "time": appointment.get("time"),
                "location": appointment.get("location"),
                "status": appointment.get("status", "confirmed"),
            },
            events={
                "onConfirm": ReactAction(
                    type="api_call",
                    endpoint=f"/api/appointments/{appointment.get('id')}/confirm",
                    method="POST",
                ),
                "onReschedule": ReactAction(
                    type="dialog",
                    dialog={"type": "reschedule", "appointmentId": appointment.get("id")},
                ),
                "onCancel": ReactAction(
                    type="dialog",
                    dialog={"type": "cancel", "appointmentId": appointment.get("id")},
                ),
            },
        )


# ============================================
# Solution-Specific UI Templates
# ============================================

async def generate_commerce_homepage(context: Dict[str, Any]) -> Dict[str, Any]:
    """Generate Commerce homepage components"""
    renderer = ReactRendererService()
    components = []
    
    # Search bar
    components.append(renderer.build_input(
        name="search",
        label="",
        placeholder="Buscar productos...",
        onChange=ReactAction(type="search", endpoint="/api/products/search"),
    ))
    
    # Categories
    categories = context.get("categories", [])
    if categories:
        category_cards = [
            renderer.build_card(
                title=cat.get("name"),
                content=[],
                actions=[renderer.build_button(
                    label="Ver",
                    variant="text",
                    size="small",
                    onClick=ReactAction(
                        type="navigate",
                        navigation={"route": f"/category/{cat.get('id')}"},
                    ),
                )],
            )
            for cat in categories[:6]
        ]
        components.append(ReactComponent(
            type=ReactComponentType.GRID,
            children=category_cards,
            props={"columns": 3},
            style=ReactStyle(gap="16px", marginTop="24px"),
        ))
    
    # Featured products
    products = context.get("featured_products", [])
    if products:
        product_cards = [renderer.build_product_card(p) for p in products[:4)]
        components.append(ReactComponent(
            type=ReactComponentType.GRID,
            children=product_cards,
            props={"columns": 2},
            style=ReactStyle(gap="16px", marginTop="24px"),
        ))
    
    return {
        "page": "home",
        "components": [renderer.render_component(c) for c in components],
    }


async def generate_health_dashboard(context: Dict[str, Any]) -> Dict[str, Any]:
    """Generate Health dashboard components"""
    renderer = ReactRendererService()
    components = []
    
    # Greeting
    user_name = context.get("user_name", "Usuario")
    components.append(renderer.build_heading(
        f"Hola, {user_name}",
        level=1,
    ))
    
    # Next appointment
    next_appointment = context.get("next_appointment")
    if next_appointment:
        components.append(ReactComponent(
            type=ReactComponentType.CARD,
            children=[
                renderer.build_heading("Próxima Cita", level=3),
                renderer.build_appointment_card(next_appointment),
            ],
            style=ReactStyle(padding="16px", marginTop="24px"),
        ))
    
    # Quick actions
    actions = [
        {"icon": "calendar", "label": "Citas", "route": "/appointments"},
        {"icon": "description", "label": "Recetas", "route": "/prescriptions"},
        {"icon": "chat", "label": "Consulta", "route": "/consultation"},
    ]
    
    action_buttons = [
        renderer.build_button(
            label=action["label"],
            variant="outlined",
            onClick=ReactAction(type="navigate", navigation={"route": action["route"]}),
        )
        for action in actions
    ]
    
    components.append(ReactComponent(
        type=ReactComponentType.FLEX,
        children=action_buttons,
        style=ReactStyle(gap="12px", marginTop="24px"),
    ))
    
    return {
        "page": "dashboard",
        "components": [renderer.render_component(c) for c in components],
    }


async def generate_order_tracking(order: Dict[str, Any]) -> Dict[str, Any]:
    """Generate order tracking page"""
    renderer = ReactRendererService()
    components = []
    
    # Order summary
    components.append(renderer.build_order_summary(order))
    
    # Tracking info
    if order.get("tracking"):
        components.append(renderer.build_tracking_info(order["tracking"]))
    
    return {
        "page": "tracking",
        "components": [renderer.render_component(c) for c in components],
    }


# Singleton
_react_renderer: Optional[ReactRendererService] = None

def get_react_renderer() -> ReactRendererService:
    global _react_renderer
    if _react_renderer is None:
        _react_renderer = ReactRendererService()
    return _react_renderer


def create_react_response(
    components: List[ReactComponent],
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a complete React response"""
    renderer = get_react_renderer()
    return {
        "version": "1.0",
        "generatedAt": datetime.utcnow().isoformat(),
        "components": [renderer.render_component(c) for c in components],
        "metadata": metadata or {},
    }
