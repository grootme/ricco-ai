"""
RICCO AI Service - Flutter GenUI SDK Integration
SDK de generación de UI para Flutter (we.ricco.com)

Este módulo proporciona la integración con Flutter/GenUI para:
- we.ricco.com (WeChat-style super app)
- Aplicaciones móviles del ecosistema RICCO
- Renderizado dinámico de UI desde el backend

Basado en: https://github.com/google/A2UI (GenUI SDK para Flutter)
"""

import asyncio
import json
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

# ============================================
# Flutter Widget Types
# ============================================

class FlutterWidgetType(str, Enum):
    """Flutter widget types supported by GenUI SDK"""
    # Basic widgets
    TEXT = "Text"
    IMAGE = "Image"
    ICON = "Icon"
    CONTAINER = "Container"
    CARD = "Card"
    
    # Layout widgets
    ROW = "Row"
    COLUMN = "Column"
    STACK = "Stack"
    WRAP = "Wrap"
    EXPANDED = "Expanded"
    FLEXIBLE = "Flexible"
    SPACER = "Spacer"
    DIVIDER = "Divider"
    
    # ScrollView widgets
    LIST_VIEW = "ListView"
    GRID_VIEW = "GridView"
    SINGLE_CHILD_SCROLL_VIEW = "SingleChildScrollView"
    
    # Input widgets
    TEXT_FIELD = "TextField"
    TEXT_FORM_FIELD = "TextFormField"
    DROPDOWN_BUTTON = "DropdownButton"
    CHECKBOX = "Checkbox"
    RADIO = "Radio"
    SWITCH = "Switch"
    SLIDER = "Slider"
    RANGE_SLIDER = "RangeSlider"
    CHECKBOX_LIST_TILE = "CheckboxListTile"
    SWITCH_LIST_TILE = "SwitchListTile"
    
    # Button widgets
    ELEVATED_BUTTON = "ElevatedButton"
    FILLED_BUTTON = "FilledButton"
    OUTLINED_BUTTON = "OutlinedButton"
    TEXT_BUTTON = "TextButton"
    ICON_BUTTON = "IconButton"
    FLOATING_ACTION_BUTTON = "FloatingActionButton"
    
    # Dialog & Bottom Sheet
    ALERT_DIALOG = "AlertDialog"
    BOTTOM_SHEET = "BottomSheet"
    MODAL_BOTTOM_SHEET = "ModalBottomSheet"
    
    # Navigation
    TAB_BAR = "TabBar"
    TAB_BAR_VIEW = "TabBarView"
    BOTTOM_NAVIGATION_BAR = "BottomNavigationBar"
    NAVIGATION_RAIL = "NavigationRail"
    DRAWER = "Drawer"
    
    # Info widgets
    SNACK_BAR = "SnackBar"
    TOAST = "Toast"
    PROGRESS_INDICATOR = "CircularProgressIndicator"
    LINEAR_PROGRESS_INDICATOR = "LinearProgressIndicator"
    
    # RICCO Custom Widgets
    PRODUCT_CARD = "ProductCard"
    ORDER_CARD = "OrderCard"
    TRACKING_CARD = "TrackingCard"
    APPOINTMENT_CARD = "AppointmentCard"
    USER_AVATAR = "UserAvatar"
    RATING_STARS = "RatingStars"
    PRICE_TAG = "PriceTag"
    ENERGY_POINTS_DISPLAY = "EnergyPointsDisplay"
    TRUST_SCORE_BADGE = "TrustScoreBadge"
    PAYMENT_METHOD_SELECTOR = "PaymentMethodSelector"
    DELIVERY_ADDRESS_CARD = "DeliveryAddressCard"


# ============================================
# Flutter Widget Models
# ============================================

class EdgeInsets(BaseModel):
    """Flutter EdgeInsets"""
    left: float = 0
    top: float = 0
    right: float = 0
    bottom: float = 0
    
    @classmethod
    def all(cls, value: float) -> "EdgeInsets":
        return cls(left=value, top=value, right=value, bottom=value)
    
    @classmethod
    def symmetric(cls, vertical: float = 0, horizontal: float = 0) -> "EdgeInsets":
        return cls(left=horizontal, top=vertical, right=horizontal, bottom=vertical)
    
    @classmethod
    def only(cls, left: float = 0, top: float = 0, right: float = 0, bottom: float = 0) -> "EdgeInsets":
        return cls(left=left, top=top, right=right, bottom=bottom)


class BorderRadius(BaseModel):
    """Flutter BorderRadius"""
    topLeft: float = 0
    topRight: float = 0
    bottomLeft: float = 0
    bottomRight: float = 0
    
    @classmethod
    def circular(cls, radius: float) -> "BorderRadius":
        return cls(topLeft=radius, topRight=radius, bottomLeft=radius, bottomRight=radius)


class BoxDecoration(BaseModel):
    """Flutter BoxDecoration"""
    color: Optional[str] = None
    borderRadius: Optional[BorderRadius] = None
    border: Optional[Dict[str, Any]] = None
    boxShadow: Optional[List[Dict[str, Any]]] = None
    gradient: Optional[Dict[str, Any]] = None
    image: Optional[Dict[str, Any]] = None


class TextStyle(BaseModel):
    """Flutter TextStyle"""
    color: Optional[str] = None
    fontSize: Optional[float] = None
    fontWeight: Optional[str] = None
    fontFamily: Optional[str] = None
    fontStyle: Optional[str] = None
    letterSpacing: Optional[float] = None
    height: Optional[float] = None
    decoration: Optional[str] = None


class FlutterAction(BaseModel):
    """Action callback for Flutter widgets"""
    type: str
    route: Optional[str] = None
    endpoint: Optional[str] = None
    method: Optional[str] = None
    payload: Dict[str, Any] = {}
    dialog_config: Optional[Dict[str, Any]] = None
    custom_action: Optional[str] = None


class FlutterWidget(BaseModel):
    """Base Flutter widget model"""
    type: FlutterWidgetType
    key: Optional[str] = None
    children: List["FlutterWidget"] = []
    padding: Optional[EdgeInsets] = None
    margin: Optional[EdgeInsets] = None
    width: Optional[float] = None
    height: Optional[float] = None
    decoration: Optional[BoxDecoration] = None
    alignment: Optional[str] = None
    onTap: Optional[FlutterAction] = None
    onLongPress: Optional[FlutterAction] = None
    visible: bool = True
    enabled: bool = True
    properties: Dict[str, Any] = {}
    id: Optional[str] = None
    analytics_event: Optional[str] = None


# ============================================
# GenUI SDK Service
# ============================================

class GenUIService:
    """
    Flutter GenUI SDK Service for we.ricco.com
    
    Generates dynamic Flutter widgets from backend definitions,
    enabling real-time UI updates without app redeployment.
    """
    
    def __init__(self):
        self._widget_builders: Dict[str, callable] = {}
        self._register_default_builders()
    
    def _register_default_builders(self):
        """Register default widget builders"""
        self._widget_builders = {
            "text": self._build_text_widget,
            "button": self._build_button_widget,
            "card": self._build_card_widget,
            "list": self._build_list_widget,
            "form": self._build_form_widget,
            "product": self._build_product_widget,
            "order": self._build_order_widget,
            "tracking": self._build_tracking_widget,
            "appointment": self._build_appointment_widget,
        }
    
    def _build_text_widget(
        self,
        content: str,
        style: Optional[TextStyle] = None,
        max_lines: Optional[int] = None,
        overflow: str = "ellipsis",
    ) -> FlutterWidget:
        """Build a Text widget"""
        return FlutterWidget(
            type=FlutterWidgetType.TEXT,
            properties={
                "data": content,
                "maxLines": max_lines,
                "overflow": overflow,
                "style": style.model_dump() if style else None,
            },
        )
    
    def _build_button_widget(
        self,
        label: str,
        action: FlutterAction,
        variant: str = "elevated",
        icon: Optional[str] = None,
        enabled: bool = True,
        loading: bool = False,
    ) -> FlutterWidget:
        """Build a Button widget"""
        button_type = {
            "elevated": FlutterWidgetType.ELEVATED_BUTTON,
            "filled": FlutterWidgetType.FILLED_BUTTON,
            "outlined": FlutterWidgetType.OUTLINED_BUTTON,
            "text": FlutterWidgetType.TEXT_BUTTON,
        }.get(variant, FlutterWidgetType.ELEVATED_BUTTON)
        
        return FlutterWidget(
            type=button_type,
            properties={
                "label": label,
                "icon": icon,
                "loading": loading,
            },
            onTap=action,
            enabled=enabled,
        )
    
    def _build_card_widget(
        self,
        title: Optional[str] = None,
        subtitle: Optional[str] = None,
        content: List[FlutterWidget] = [],
        actions: List[Dict[str, Any]] = [],
        elevation: float = 1.0,
    ) -> FlutterWidget:
        """Build a Card widget"""
        children = []
        
        if title:
            children.append(self._build_text_widget(
                title,
                style=TextStyle(fontSize=18, fontWeight="w600"),
            ))
        
        if subtitle:
            children.append(self._build_text_widget(
                subtitle,
                style=TextStyle(fontSize=14, color="#666666"),
            ))
        
        children.extend(content)
        
        return FlutterWidget(
            type=FlutterWidgetType.CARD,
            children=children,
            decoration=BoxDecoration(
                borderRadius=BorderRadius.circular(12),
                boxShadow=[{
                    "color": "#0000001A",
                    "blurRadius": elevation * 4,
                    "offset": {"dx": 0, "dy": elevation},
                }],
            ),
            properties={"actions": actions},
        )
    
    def _build_list_widget(
        self,
        items: List[Dict[str, Any]],
        item_builder: str = "default",
    ) -> FlutterWidget:
        """Build a ListView widget"""
        list_items = []
        
        for item in items:
            if item_builder == "product":
                list_items.append(self._build_product_widget(item))
            elif item_builder == "order":
                list_items.append(self._build_order_widget(item))
            else:
                list_items.append(self._build_card_widget(
                    title=item.get("title"),
                    subtitle=item.get("subtitle"),
                ))
        
        return FlutterWidget(
            type=FlutterWidgetType.LIST_VIEW,
            children=list_items,
            properties={
                "shrinkWrap": True,
                "physics": "alwaysScrollableScrollPhysics",
            },
        )
    
    def _build_form_widget(
        self,
        fields: List[Dict[str, Any]],
        submit_action: FlutterAction,
        submit_label: str = "Enviar",
    ) -> FlutterWidget:
        """Build a Form widget"""
        form_fields = []
        
        for field in fields:
            field_type = field.get("type", "text")
            
            if field_type in ["text", "email", "password"]:
                form_fields.append(FlutterWidget(
                    type=FlutterWidgetType.TEXT_FORM_FIELD,
                    properties={
                        "name": field.get("name"),
                        "label": field.get("label"),
                        "hintText": field.get("placeholder"),
                        "obscureText": field_type == "password",
                        "keyboardType": "emailAddress" if field_type == "email" else "text",
                    },
                ))
            
            elif field_type == "select":
                form_fields.append(FlutterWidget(
                    type=FlutterWidgetType.DROPDOWN_BUTTON,
                    properties={
                        "name": field.get("name"),
                        "label": field.get("label"),
                        "items": field.get("options", []),
                        "value": field.get("value"),
                    },
                ))
        
        form_fields.append(self._build_button_widget(
            label=submit_label,
            action=submit_action,
            variant="filled",
        ))
        
        return FlutterWidget(
            type=FlutterWidgetType.COLUMN,
            children=form_fields,
        )
    
    def _build_product_widget(self, data: Dict[str, Any]) -> FlutterWidget:
        """Build a Product Card widget"""
        return FlutterWidget(
            type=FlutterWidgetType.PRODUCT_CARD,
            properties={
                "productId": data.get("id", ""),
                "name": data.get("name", ""),
                "price": data.get("price", 0),
                "currency": data.get("currency", "USD"),
                "imageUrl": data.get("image_url"),
                "rating": data.get("rating"),
                "reviewsCount": data.get("reviews_count"),
                "discount": data.get("discount"),
                "energyPoints": data.get("energy_points"),
            },
            onTap=FlutterAction(
                type="navigate",
                route=f"/product/{data.get('id')}",
            ),
        )
    
    def _build_order_widget(self, data: Dict[str, Any]) -> FlutterWidget:
        """Build an Order Card widget"""
        return FlutterWidget(
            type=FlutterWidgetType.ORDER_CARD,
            properties={
                "orderId": data.get("id", ""),
                "status": data.get("status", "pending"),
                "total": data.get("total", 0),
                "itemsCount": data.get("items_count", 0),
                "createdAt": data.get("created_at", ""),
                "estimatedDelivery": data.get("estimated_delivery"),
                "trackingNumber": data.get("tracking_number"),
            },
            onTap=FlutterAction(
                type="navigate",
                route=f"/order/{data.get('id')}",
            ),
        )
    
    def _build_tracking_widget(self, data: Dict[str, Any]) -> FlutterWidget:
        """Build a Tracking Card widget"""
        return FlutterWidget(
            type=FlutterWidgetType.TRACKING_CARD,
            properties={
                "trackingNumber": data.get("tracking_number", ""),
                "status": data.get("status", ""),
                "carrier": data.get("carrier", ""),
                "events": data.get("events", []),
                "estimatedDelivery": data.get("estimated_delivery"),
            },
        )
    
    def _build_appointment_widget(self, data: Dict[str, Any]) -> FlutterWidget:
        """Build an Appointment Card widget"""
        return FlutterWidget(
            type=FlutterWidgetType.APPOINTMENT_CARD,
            properties={
                "appointmentId": data.get("id", ""),
                "providerName": data.get("provider_name", ""),
                "specialty": data.get("specialty", ""),
                "date": data.get("date", ""),
                "time": data.get("time", ""),
                "location": data.get("location"),
                "status": data.get("status", "confirmed"),
            },
            onTap=FlutterAction(
                type="navigate",
                route=f"/appointment/{data.get('id')}",
            ),
        )
    
    def _widget_to_json(self, widget: FlutterWidget) -> Dict[str, Any]:
        """Convert widget to JSON for Flutter parsing"""
        result = {
            "type": widget.type.value,
            "properties": widget.properties,
            "children": [self._widget_to_json(c) for c in widget.children],
            "visible": widget.visible,
            "enabled": widget.enabled,
        }
        
        if widget.key:
            result["key"] = widget.key
        if widget.padding:
            result["padding"] = widget.padding.model_dump()
        if widget.margin:
            result["margin"] = widget.margin.model_dump()
        if widget.width:
            result["width"] = widget.width
        if widget.height:
            result["height"] = widget.height
        if widget.decoration:
            result["decoration"] = widget.decoration.model_dump()
        if widget.onTap:
            result["onTap"] = widget.onTap.model_dump()
        if widget.id:
            result["id"] = widget.id
        
        return result
    
    async def generate_ui_response(
        self,
        intent: str,
        data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Generate UI response for Flutter app"""
        builder = self._widget_builders.get(intent)
        
        if builder:
            widget = builder(data) if not isinstance(data, list) else self._build_list_widget(data, intent)
        else:
            widget = self._build_card_widget(
                title=data.get("title"),
                subtitle=data.get("subtitle"),
                content=[self._build_text_widget(data.get("message", ""))],
            )
        
        return self._widget_to_json(widget)


# Singleton
_genui_service: Optional[GenUIService] = None

def get_genui_service() -> GenUIService:
    global _genui_service
    if _genui_service is None:
        _genui_service = GenUIService()
    return _genui_service


def create_flutter_response(
    widgets: List[FlutterWidget],
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a complete Flutter response"""
    service = get_genui_service()
    return {
        "version": "1.0",
        "generatedAt": datetime.utcnow().isoformat(),
        "widgets": [service._widget_to_json(w) for w in widgets],
        "metadata": metadata or {},
    }
