"""
A2UI Component Seeds for RICCO AI.

Database-managed A2UI component configurations.
"""

from typing import Any, Dict, List

# A2UI component seed data
A2UI_COMPONENT_SEEDS: List[Dict[str, Any]] = [
    # Basic Components
    {
        "component_id": "button-primary",
        "component_type": "button",
        "name": "Primary Button",
        "description": "Primary action button component",
        "category": "basic",
        "schema": {
            "properties": {
                "label": {"type": "string", "required": True},
                "variant": {"type": "string", "enum": ["primary", "secondary", "outline"], "default": "primary"},
                "size": {"type": "string", "enum": ["small", "medium", "large"], "default": "medium"},
                "disabled": {"type": "boolean", "default": False},
                "icon": {"type": "string"},
            },
        },
        "default_props": {
            "variant": "primary",
            "size": "medium",
            "disabled": False,
        },
        "actions": ["click", "hover", "focus"],
        "platforms": ["react", "flutter", "lit"],
        "is_enabled": True,
    },
    {
        "component_id": "input-text",
        "component_type": "input",
        "name": "Text Input",
        "description": "Text input field component",
        "category": "basic",
        "schema": {
            "properties": {
                "label": {"type": "string"},
                "placeholder": {"type": "string"},
                "value": {"type": "string"},
                "type": {"type": "string", "enum": ["text", "email", "password", "tel"], "default": "text"},
                "required": {"type": "boolean", "default": False},
                "disabled": {"type": "boolean", "default": False},
            },
        },
        "default_props": {
            "type": "text",
            "required": False,
            "disabled": False,
        },
        "actions": ["change", "focus", "blur"],
        "platforms": ["react", "flutter", "lit"],
        "is_enabled": True,
    },
    {
        "component_id": "text-heading",
        "component_type": "text",
        "name": "Heading Text",
        "description": "Heading text component",
        "category": "basic",
        "schema": {
            "properties": {
                "content": {"type": "string", "required": True},
                "level": {"type": "integer", "enum": [1, 2, 3, 4, 5, 6], "default": 2},
                "align": {"type": "string", "enum": ["left", "center", "right"], "default": "left"},
            },
        },
        "default_props": {
            "level": 2,
            "align": "left",
        },
        "actions": [],
        "platforms": ["react", "flutter", "lit"],
        "is_enabled": True,
    },
    
    # Card Components
    {
        "component_id": "card-basic",
        "component_type": "card",
        "name": "Basic Card",
        "description": "Basic card container component",
        "category": "container",
        "schema": {
            "properties": {
                "title": {"type": "string"},
                "subtitle": {"type": "string"},
                "image": {"type": "string"},
                "content": {"type": "string"},
                "elevation": {"type": "integer", "default": 1},
            },
        },
        "default_props": {
            "elevation": 1,
        },
        "actions": ["click"],
        "platforms": ["react", "flutter", "lit"],
        "is_enabled": True,
    },
    {
        "component_id": "card-product",
        "component_type": "product_card",
        "name": "Product Card",
        "description": "Product display card for e-commerce",
        "category": "commerce",
        "schema": {
            "properties": {
                "product_id": {"type": "string", "required": True},
                "name": {"type": "string", "required": True},
                "price": {"type": "number", "required": True},
                "currency": {"type": "string", "default": "USD"},
                "image": {"type": "string"},
                "description": {"type": "string"},
                "rating": {"type": "number"},
                "in_stock": {"type": "boolean", "default": True},
                "discount_percent": {"type": "number"},
            },
        },
        "default_props": {
            "currency": "USD",
            "in_stock": True,
        },
        "actions": ["add_to_cart", "view_details", "wishlist"],
        "platforms": ["react", "flutter", "lit"],
        "is_enabled": True,
    },
    {
        "component_id": "card-user-profile",
        "component_type": "user_profile",
        "name": "User Profile Card",
        "description": "User profile display card",
        "category": "user",
        "schema": {
            "properties": {
                "user_id": {"type": "string", "required": True},
                "name": {"type": "string", "required": True},
                "avatar": {"type": "string"},
                "trust_score": {"type": "number"},
                "energy_points": {"type": "integer"},
                "member_since": {"type": "string"},
            },
        },
        "default_props": {},
        "actions": ["view_profile", "edit_profile"],
        "platforms": ["react", "flutter", "lit"],
        "is_enabled": True,
    },
    
    # Form Components
    {
        "component_id": "form-login",
        "component_type": "form",
        "name": "Login Form",
        "description": "User login form",
        "category": "auth",
        "schema": {
            "properties": {
                "show_remember": {"type": "boolean", "default": True},
                "show_forgot": {"type": "boolean", "default": True},
                "social_logins": {"type": "array", "items": {"type": "string"}},
            },
        },
        "default_props": {
            "show_remember": True,
            "show_forgot": True,
        },
        "actions": ["submit", "social_login"],
        "platforms": ["react", "flutter", "lit"],
        "is_enabled": True,
    },
    {
        "component_id": "form-checkout",
        "component_type": "form",
        "name": "Checkout Form",
        "description": "E-commerce checkout form",
        "category": "commerce",
        "schema": {
            "properties": {
                "show_shipping": {"type": "boolean", "default": True},
                "show_billing": {"type": "boolean", "default": True},
                "payment_methods": {"type": "array", "items": {"type": "string"}},
            },
        },
        "default_props": {
            "show_shipping": True,
            "show_billing": True,
        },
        "actions": ["submit", "apply_coupon", "change_payment"],
        "platforms": ["react", "flutter", "lit"],
        "is_enabled": True,
    },
    
    # List Components
    {
        "component_id": "list-products",
        "component_type": "list",
        "name": "Product List",
        "description": "Product listing component",
        "category": "commerce",
        "schema": {
            "properties": {
                "products": {"type": "array"},
                "layout": {"type": "string", "enum": ["grid", "list"], "default": "grid"},
                "columns": {"type": "integer", "default": 3},
                "show_filters": {"type": "boolean", "default": True},
                "show_sort": {"type": "boolean", "default": True},
            },
        },
        "default_props": {
            "layout": "grid",
            "columns": 3,
            "show_filters": True,
            "show_sort": True,
        },
        "actions": ["filter", "sort", "load_more"],
        "platforms": ["react", "flutter", "lit"],
        "is_enabled": True,
    },
    
    # Dashboard Components
    {
        "component_id": "dashboard-main",
        "component_type": "dashboard",
        "name": "Main Dashboard",
        "description": "Main user dashboard component",
        "category": "dashboard",
        "schema": {
            "properties": {
                "widgets": {"type": "array"},
                "layout": {"type": "string", "enum": ["grid", "flex"], "default": "grid"},
                "refresh_interval": {"type": "integer", "default": 60},
            },
        },
        "default_props": {
            "layout": "grid",
            "refresh_interval": 60,
        },
        "actions": ["refresh", "customize", "add_widget"],
        "platforms": ["react", "flutter", "lit"],
        "is_enabled": True,
    },
    
    # Navigation Components
    {
        "component_id": "nav-main",
        "component_type": "navigation",
        "name": "Main Navigation",
        "description": "Main application navigation",
        "category": "navigation",
        "schema": {
            "properties": {
                "items": {"type": "array", "required": True},
                "orientation": {"type": "string", "enum": ["horizontal", "vertical"], "default": "horizontal"},
                "show_icons": {"type": "boolean", "default": True},
            },
        },
        "default_props": {
            "orientation": "horizontal",
            "show_icons": True,
        },
        "actions": ["navigate"],
        "platforms": ["react", "flutter", "lit"],
        "is_enabled": True,
    },
    
    # Modal Components
    {
        "component_id": "modal-basic",
        "component_type": "modal",
        "name": "Basic Modal",
        "description": "Basic modal dialog component",
        "category": "overlay",
        "schema": {
            "properties": {
                "title": {"type": "string"},
                "content": {"type": "string"},
                "size": {"type": "string", "enum": ["small", "medium", "large"], "default": "medium"},
                "closable": {"type": "boolean", "default": True},
            },
        },
        "default_props": {
            "size": "medium",
            "closable": True,
        },
        "actions": ["open", "close", "confirm"],
        "platforms": ["react", "flutter", "lit"],
        "is_enabled": True,
    },
]


def get_components_by_category(category: str) -> List[Dict[str, Any]]:
    """Get all components in a category."""
    return [
        comp for comp in A2UI_COMPONENT_SEEDS
        if comp["category"] == category
    ]


def get_components_by_type(component_type: str) -> List[Dict[str, Any]]:
    """Get all components of a specific type."""
    return [
        comp for comp in A2UI_COMPONENT_SEEDS
        if comp["component_type"] == component_type
    ]


def get_enabled_components() -> List[Dict[str, Any]]:
    """Get all enabled components."""
    return [
        comp for comp in A2UI_COMPONENT_SEEDS
        if comp.get("is_enabled", True)
    ]


def get_all_categories() -> List[str]:
    """Get all unique categories."""
    return list(set(comp["category"] for comp in A2UI_COMPONENT_SEEDS))


def get_all_component_types() -> List[str]:
    """Get all unique component types."""
    return list(set(comp["component_type"] for comp in A2UI_COMPONENT_SEEDS))
