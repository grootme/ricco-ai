"""
A2UI UI Templates
Template Method Pattern for reusable UI component generation

Implements: Template Method Pattern, Factory Method Pattern
"""

from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod
from .models import (
    ComponentType, ComponentStyle, ComponentAction,
    A2UIComponent, ComponentBuilder
)


class UITemplate(ABC):
    """
    Abstract base class for UI templates.
    
    Implements: Template Method Pattern
    
    Subclasses implement specific UI templates while inheriting
    common structure and behavior.
    """
    
    @abstractmethod
    def create_components(self, **kwargs) -> List[A2UIComponent]:
        """Create UI components for this template"""
        pass
    
    @abstractmethod
    def get_template_name(self) -> str:
        """Get template name"""
        pass
    
    def create_surface_commands(
        self,
        surface_id: str,
        catalog_id: str = "https://a2ui.org/specification/v0_9/basic_catalog.json",
        theme: Optional[Dict[str, Any]] = None,
        send_data_model: bool = False
    ) -> Dict[str, Any]:
        """Create surface creation command"""
        return {
            "version": "v0_9",
            "createSurface": {
                "surfaceId": surface_id,
                "catalogId": catalog_id,
                "theme": theme or {},
                "sendDataModel": send_data_model
            }
        }
    
    def create_update_components_command(
        self,
        surface_id: str,
        components: List[A2UIComponent]
    ) -> Dict[str, Any]:
        """Create update components command"""
        return {
            "version": "v0_9",
            "updateComponents": {
                "surfaceId": surface_id,
                "components": [self._component_to_dict(c) for c in components]
            }
        }
    
    def create_update_data_model_command(
        self,
        surface_id: str,
        path: str,
        value: Any
    ) -> Dict[str, Any]:
        """Create update data model command"""
        return {
            "version": "v0_9",
            "updateDataModel": {
                "surfaceId": surface_id,
                "path": path,
                "value": value
            }
        }
    
    def _component_to_dict(self, component: A2UIComponent) -> Dict[str, Any]:
        """Convert component to dictionary"""
        result = {
            "id": component.id,
            "component": component.type.value,
        }
        
        if component.properties:
            result.update(component.properties)
        
        if component.children:
            if all(isinstance(c, str) for c in component.children):
                result["children"] = component.children
            else:
                result["children"] = [self._component_to_dict(c) for c in component.children]
        
        if component.style:
            result["style"] = component.style.model_dump(exclude_none=True)
        
        return result


class ChatUITemplate(UITemplate):
    """Template for chat interface - RICCO Chat"""
    
    def get_template_name(self) -> str:
        return "chat_ui"
    
    def create_components(
        self,
        surface_id: str,
        user_name: str = "User",
        assistant_name: str = "RICCO AI",
        show_context_indicator: bool = False,
        **kwargs
    ) -> List[A2UIComponent]:
        """Create chat UI components"""
        components = [
            # Root container
            ComponentBuilder(ComponentType.COLUMN)
                .with_id("root")
                .with_property("children", ["header", "messages", "input"])
                .build(),
            
            # Header
            ComponentBuilder(ComponentType.ROW)
                .with_id("header")
                .with_property("children", ["avatar", "title"])
                .with_style(padding="8px", backgroundColor="#f5f5f5")
                .build(),
            
            # Avatar icon
            ComponentBuilder(ComponentType.ICON)
                .with_id("avatar")
                .with_property("name", "smart_toy")
                .build(),
            
            # Title
            ComponentBuilder(ComponentType.TEXT)
                .with_id("title")
                .with_property("text", assistant_name)
                .with_property("variant", "h6")
                .build(),
        ]
        
        # Messages list
        messages_component = (
            ComponentBuilder(ComponentType.LIST)
                .with_id("messages")
                .with_property("children", {"path": "/messages", "componentId": "message"})
        )
        components.append(messages_component.build())
        
        # Input field
        input_component = (
            ComponentBuilder(ComponentType.TEXT_FIELD)
                .with_id("input")
                .with_property("label", "Mensaje")
                .with_property("value", {"path": "/input"})
                .with_style(padding="8px")
        )
        components.append(input_component.build())
        
        return components
    
    def create_initial_data_model(self) -> Dict[str, Any]:
        """Create initial data model for chat"""
        return {
            "messages": [],
            "input": ""
        }


class KYCFormTemplate(UITemplate):
    """Template for KYC verification forms"""
    
    def get_template_name(self) -> str:
        return "kyc_form"
    
    def create_components(
        self,
        surface_id: str,
        kyc_type: str = "individual",  # individual, business
        fields: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> List[A2UIComponent]:
        """Create KYC form components"""
        title_text = "Verificación Individual" if kyc_type == "individual" else "Verificación Empresarial"
        
        default_fields = fields or [
            {"id": "name_field", "label": "Nombre Completo", "path": "/kyc/name"},
            {"id": "id_field", "label": "Número de Identificación", "path": "/kyc/idNumber"},
            {"id": "email_field", "label": "Correo Electrónico", "path": "/kyc/email"},
            {"id": "phone_field", "label": "Teléfono", "path": "/kyc/phone"},
        ]
        
        components = [
            # Root card
            ComponentBuilder(ComponentType.CARD)
                .with_id("root")
                .with_property("child", "form")
                .with_style(padding="16px", borderRadius="8px")
                .build(),
            
            # Form container
            ComponentBuilder(ComponentType.COLUMN)
                .with_id("form")
                .with_property("children", ["title", "fields", "submit"])
                .build(),
            
            # Title
            ComponentBuilder(ComponentType.TEXT)
                .with_id("title")
                .with_property("text", title_text)
                .with_property("variant", "h5")
                .build(),
            
            # Fields container
            ComponentBuilder(ComponentType.COLUMN)
                .with_id("fields")
                .with_property("children", [f["id"] for f in default_fields])
                .build(),
        ]
        
        # Add form fields
        for field in default_fields:
            field_component = (
                ComponentBuilder(ComponentType.TEXT_FIELD)
                    .with_id(field["id"])
                    .with_property("label", field["label"])
                    .with_property("value", {"path": field["path"]})
                    .with_style(padding="8px 0")
            )
            components.append(field_component.build())
        
        # Submit button
        submit_component = (
            ComponentBuilder(ComponentType.BUTTON)
                .with_id("submit")
                .with_property("child", "submit_text")
                .with_property("variant", "primary")
                .with_action("click", ComponentAction(
                    type="submit",
                    endpoint="/api/kyc/submit",
                    method="POST"
                ))
        )
        components.append(submit_component.build())
        
        # Submit button text
        components.append(
            ComponentBuilder(ComponentType.TEXT)
                .with_id("submit_text")
                .with_property("text", "Enviar")
                .build()
        )
        
        return components
    
    def create_initial_data_model(self) -> Dict[str, Any]:
        """Create initial data model for KYC form"""
        return {
            "kyc": {
                "name": "",
                "idNumber": "",
                "email": "",
                "phone": ""
            }
        }


class ProductSearchTemplate(UITemplate):
    """Template for product search results"""
    
    def get_template_name(self) -> str:
        return "product_search"
    
    def create_components(
        self,
        surface_id: str,
        products: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ) -> List[A2UIComponent]:
        """Create product search components"""
        products = products or []
        
        components = [
            # Heading
            ComponentBuilder(ComponentType.HEADING)
                .with_id("title")
                .with_property("level", 2)
                .with_property("content", "Resultados de búsqueda")
                .build(),
        ]
        
        if products:
            # Product grid
            product_components = []
            for i, product in enumerate(products[:6]):  # Limit to 6
                product_card = self._create_product_card(product, i)
                product_components.append(product_card)
            
            grid = (
                ComponentBuilder(ComponentType.GRID)
                    .with_id("product_grid")
                    .with_children(product_components)
                    .with_property("columns", 2)
                    .with_style(gap="16px")
            )
            components.append(grid.build())
        else:
            # No results
            components.append(
                ComponentBuilder(ComponentType.TEXT)
                    .with_id("no_results")
                    .with_property("content", "No se encontraron productos. Intenta con otros términos.")
                    .build()
            )
        
        return components
    
    def _create_product_card(self, product: Dict[str, Any], index: int) -> A2UIComponent:
        """Create a single product card"""
        product_id = product.get("id", f"product_{index}")
        
        return (
            ComponentBuilder(ComponentType.PRODUCT_CARD)
                .with_id(f"product_{index}")
                .with_properties({
                    "productId": product_id,
                    "name": product.get("name", ""),
                    "price": product.get("price", 0),
                    "image": product.get("image", ""),
                    "rating": product.get("rating", 0),
                })
                .with_action("click", ComponentAction(
                    type="navigate",
                    navigation={"route": f"/product/{product_id}"}
                ))
                .with_action("add_to_cart", ComponentAction(
                    type="api_call",
                    endpoint="/api/cart/add",
                    method="POST",
                    payload={"product_id": product_id}
                ))
                .build()
        )


class OrderStatusTemplate(UITemplate):
    """Template for order status display"""
    
    def get_template_name(self) -> str:
        return "order_status"
    
    def create_components(
        self,
        surface_id: str,
        order: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[A2UIComponent]:
        """Create order status components"""
        order = order or {}
        
        components = [
            # Order summary card
            ComponentBuilder(ComponentType.ORDER_SUMMARY)
                .with_id("order_summary")
                .with_properties({
                    "orderId": order.get("id", "N/A"),
                    "status": order.get("status", "pending"),
                    "total": order.get("total", 0),
                    "itemsCount": order.get("items_count", 0),
                    "estimatedDelivery": order.get("estimated_delivery"),
                })
                .build(),
        ]
        
        # Tracking timeline if available
        if order.get("tracking"):
            timeline_items = []
            for i, event in enumerate(order["tracking"]):
                event_card = (
                    ComponentBuilder(ComponentType.CARD)
                        .with_id(f"tracking_event_{i}")
                        .with_properties({
                            "title": event.get("status", ""),
                            "subtitle": event.get("date", ""),
                            "description": event.get("location", ""),
                        })
                        .build()
                )
                timeline_items.append(event_card)
            
            timeline = (
                ComponentBuilder(ComponentType.TIMELINE)
                    .with_id("tracking_timeline")
                    .with_children(timeline_items)
            )
            components.append(timeline.build())
        
        return components


class TrackingTemplate(UITemplate):
    """Template for shipment tracking"""
    
    def get_template_name(self) -> str:
        return "tracking"
    
    def create_components(
        self,
        surface_id: str,
        tracking: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[A2UIComponent]:
        """Create tracking components"""
        tracking = tracking or {}
        
        components = [
            # Tracking info card
            ComponentBuilder(ComponentType.TRACKING_INFO)
                .with_id("tracking_info")
                .with_properties({
                    "trackingNumber": tracking.get("tracking_number", ""),
                    "status": tracking.get("status", ""),
                    "origin": tracking.get("origin", ""),
                    "destination": tracking.get("destination", ""),
                    "estimatedDelivery": tracking.get("estimated_delivery", ""),
                    "carrier": tracking.get("carrier", ""),
                })
                .build(),
        ]
        
        # Map if location available
        if tracking.get("current_location"):
            map_component = (
                ComponentBuilder(ComponentType.MAP)
                    .with_id("tracking_map")
                    .with_properties({
                        "center": tracking["current_location"],
                        "markers": [tracking["current_location"]],
                        "zoom": 12,
                    })
            )
            components.append(map_component.build())
        
        return components


class AppointmentTemplate(UITemplate):
    """Template for appointment booking/display"""
    
    def get_template_name(self) -> str:
        return "appointment"
    
    def create_components(
        self,
        surface_id: str,
        appointment: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> List[A2UIComponent]:
        """Create appointment components"""
        appointment = appointment or {}
        
        return [
            ComponentBuilder(ComponentType.APPOINTMENT_CARD)
                .with_id("appointment_card")
                .with_properties({
                    "provider": appointment.get("provider", ""),
                    "date": appointment.get("date", ""),
                    "time": appointment.get("time", ""),
                    "location": appointment.get("location", ""),
                    "type": appointment.get("type", ""),
                })
                .with_action("confirm", ComponentAction(
                    type="api_call",
                    endpoint="/api/appointments/confirm",
                    method="POST"
                ))
                .with_action("reschedule", ComponentAction(
                    type="dialog",
                    dialog={"type": "reschedule_form"}
                ))
                .with_action("cancel", ComponentAction(
                    type="dialog",
                    dialog={"type": "cancel_confirmation"}
                ))
                .build(),
        ]


# =============================================================================
# Template Registry (Factory Pattern)
# =============================================================================

class TemplateRegistry:
    """
    Registry for UI templates.
    
    Implements: Factory Pattern, Registry Pattern
    """
    
    _templates: Dict[str, type] = {}
    
    @classmethod
    def register(cls, template_class: type) -> None:
        """Register a template class"""
        instance = template_class()
        cls._templates[instance.get_template_name()] = template_class
    
    @classmethod
    def get_template(cls, name: str) -> Optional[UITemplate]:
        """Get template instance by name"""
        template_class = cls._templates.get(name)
        if template_class:
            return template_class()
        return None
    
    @classmethod
    def list_templates(cls) -> List[str]:
        """List available template names"""
        return list(cls._templates.keys())


# Register default templates
TemplateRegistry.register(ChatUITemplate)
TemplateRegistry.register(KYCFormTemplate)
TemplateRegistry.register(ProductSearchTemplate)
TemplateRegistry.register(OrderStatusTemplate)
TemplateRegistry.register(TrackingTemplate)
TemplateRegistry.register(AppointmentTemplate)
