"""
A2UI Component Schemas - JSON Schema definitions for all components.
Provides validation and type safety for component props.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from enum import Enum
from pydantic import BaseModel, Field
import json


class JSONSchema(BaseModel):
    """JSON Schema wrapper for component props validation."""
    schema_type: str = Field(default="object", alias="$schema")
    type: str = Field(default="object")
    properties: Dict[str, Any] = Field(default_factory=dict)
    required: List[str] = Field(default_factory=list)
    definitions: Dict[str, Any] = Field(default_factory=dict, alias="$defs")
    
    class Config:
        populate_by_name = True
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "$schema": self.schema_type,
            "type": self.type,
            "properties": self.properties,
            "required": self.required,
            "$defs": self.definitions
        }


# Common type definitions
COMMON_DEFINITIONS = {
    "Price": {
        "type": "object",
        "properties": {
            "amount": {"type": "number", "minimum": 0},
            "currency": {"type": "string", "default": "USD"},
            "formatted": {"type": "string"}
        },
        "required": ["amount"]
    },
    "Image": {
        "type": "object",
        "properties": {
            "url": {"type": "string", "format": "uri"},
            "alt": {"type": "string"},
            "width": {"type": "integer"},
            "height": {"type": "integer"},
            "thumbnail": {"type": "string", "format": "uri"}
        },
        "required": ["url"]
    },
    "Rating": {
        "type": "object",
        "properties": {
            "average": {"type": "number", "minimum": 0, "maximum": 5},
            "count": {"type": "integer", "minimum": 0},
            "distribution": {
                "type": "object",
                "properties": {
                    "1": {"type": "integer"},
                    "2": {"type": "integer"},
                    "3": {"type": "integer"},
                    "4": {"type": "integer"},
                    "5": {"type": "integer"}
                }
            }
        },
        "required": ["average", "count"]
    },
    "Badge": {
        "type": "object",
        "properties": {
            "text": {"type": "string"},
            "variant": {"type": "string", "enum": ["primary", "secondary", "success", "warning", "error", "info"]},
            "position": {"type": "string", "enum": ["top-left", "top-right", "bottom-left", "bottom-right"]}
        },
        "required": ["text"]
    },
    "Action": {
        "type": "object",
        "properties": {
            "type": {"type": "string", "enum": ["navigate", "api_call", "emit", "custom"]},
            "target": {"type": "string"},
            "payload": {"type": "object"},
            "confirmation": {"type": "string"}
        },
        "required": ["type"]
    },
    "Address": {
        "type": "object",
        "properties": {
            "street": {"type": "string"},
            "city": {"type": "string"},
            "state": {"type": "string"},
            "country": {"type": "string"},
            "postal_code": {"type": "string"},
            "coordinates": {
                "type": "object",
                "properties": {
                    "lat": {"type": "number"},
                    "lng": {"type": "number"}
                }
            }
        },
        "required": ["street", "city", "country"]
    }
}


class ComponentSchemaRegistry:
    """Registry of JSON Schemas for all A2UI components."""
    
    def __init__(self):
        self._schemas: Dict[str, Dict[str, Any]] = {}
        self._initialize_schemas()
    
    def _initialize_schemas(self) -> None:
        """Initialize all component schemas."""
        # ProductCard
        self._schemas["ProductCard"] = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "$defs": COMMON_DEFINITIONS,
            "properties": {
                "product_id": {"type": "string", "description": "Unique product identifier"},
                "name": {"type": "string", "minLength": 1, "maxLength": 200},
                "description": {"type": "string", "maxLength": 2000},
                "price": {"$ref": "#/$defs/Price"},
                "original_price": {"$ref": "#/$defs/Price"},
                "discount_percentage": {"type": "number", "minimum": 0, "maximum": 100},
                "images": {
                    "type": "array",
                    "items": {"$ref": "#/$defs/Image"},
                    "maxItems": 10
                },
                "rating": {"$ref": "#/$defs/Rating"},
                "stock": {
                    "type": "object",
                    "properties": {
                        "available": {"type": "boolean"},
                        "quantity": {"type": "integer"},
                        "low_stock_threshold": {"type": "integer"}
                    }
                },
                "badges": {
                    "type": "array",
                    "items": {"$ref": "#/$defs/Badge"}
                },
                "category": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "slug": {"type": "string"}
                    }
                },
                "vendor": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "verified": {"type": "boolean"}
                    }
                },
                "actions": {
                    "type": "object",
                    "properties": {
                        "on_click": {"$ref": "#/$defs/Action"},
                        "on_add_to_cart": {"$ref": "#/$defs/Action"},
                        "on_add_to_wishlist": {"$ref": "#/$defs/Action"},
                        "on_quick_view": {"$ref": "#/$defs/Action"}
                    }
                },
                "style": {
                    "type": "object",
                    "properties": {
                        "variant": {"type": "string", "enum": ["default", "compact", "detailed", "horizontal"]},
                        "show_rating": {"type": "boolean", "default": True},
                        "show_vendor": {"type": "boolean", "default": False},
                        "show_stock": {"type": "boolean", "default": False},
                        "image_aspect_ratio": {"type": "string", "enum": ["1:1", "4:3", "16:9", "3:4"]}
                    }
                }
            },
            "required": ["product_id", "name", "price"]
        }
        
        # AppointmentCard
        self._schemas["AppointmentCard"] = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "$defs": COMMON_DEFINITIONS,
            "properties": {
                "appointment_id": {"type": "string"},
                "title": {"type": "string", "minLength": 1, "maxLength": 200},
                "description": {"type": "string", "maxLength": 1000},
                "service": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "duration_minutes": {"type": "integer", "minimum": 5},
                        "category": {"type": "string"}
                    },
                    "required": ["id", "name"]
                },
                "provider": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "avatar": {"$ref": "#/$defs/Image"},
                        "rating": {"$ref": "#/$defs/Rating"},
                        "verified": {"type": "boolean"}
                    },
                    "required": ["id", "name"]
                },
                "location": {
                    "type": "object",
                    "properties": {
                        "address": {"$ref": "#/$defs/Address"},
                        "is_virtual": {"type": "boolean"},
                        "meeting_link": {"type": "string", "format": "uri"}
                    }
                },
                "schedule": {
                    "type": "object",
                    "properties": {
                        "start_time": {"type": "string", "format": "date-time"},
                        "end_time": {"type": "string", "format": "date-time"},
                        "timezone": {"type": "string"},
                        "reminder_minutes": {"type": "integer"}
                    },
                    "required": ["start_time"]
                },
                "status": {
                    "type": "string",
                    "enum": ["pending", "confirmed", "in_progress", "completed", "cancelled", "no_show"]
                },
                "price": {"$ref": "#/$defs/Price"},
                "payment_status": {
                    "type": "string",
                    "enum": ["unpaid", "pending", "paid", "refunded", "partial"]
                },
                "notes": {"type": "string"},
                "attachments": {
                    "type": "array",
                    "items": {"$ref": "#/$defs/Image"}
                },
                "actions": {
                    "type": "object",
                    "properties": {
                        "on_reschedule": {"$ref": "#/$defs/Action"},
                        "on_cancel": {"$ref": "#/$defs/Action"},
                        "on_confirm": {"$ref": "#/$defs/Action"},
                        "on_add_to_calendar": {"$ref": "#/$defs/Action"},
                        "on_get_directions": {"$ref": "#/$defs/Action"},
                        "on_join_meeting": {"$ref": "#/$defs/Action"}
                    }
                },
                "style": {
                    "type": "object",
                    "properties": {
                        "variant": {"type": "string", "enum": ["default", "compact", "timeline", "detailed"]},
                        "show_map": {"type": "boolean"},
                        "show_qr_code": {"type": "boolean"},
                        "highlight_status": {"type": "boolean", "default": True}
                    }
                }
            },
            "required": ["appointment_id", "title", "schedule"]
        }
        
        # TrackingCard
        self._schemas["TrackingCard"] = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "$defs": COMMON_DEFINITIONS,
            "properties": {
                "tracking_id": {"type": "string"},
                "tracking_number": {"type": "string"},
                "carrier": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "logo": {"$ref": "#/$defs/Image"},
                        "tracking_url": {"type": "string", "format": "uri"}
                    },
                    "required": ["name"]
                },
                "status": {
                    "type": "object",
                    "properties": {
                        "current": {
                            "type": "string",
                            "enum": ["pending", "picked_up", "in_transit", "out_for_delivery", "delivered", "failed", "returned"]
                        },
                        "description": {"type": "string"},
                        "updated_at": {"type": "string", "format": "date-time"}
                    },
                    "required": ["current"]
                },
                "progress": {
                    "type": "object",
                    "properties": {
                        "percentage": {"type": "number", "minimum": 0, "maximum": 100},
                        "steps_completed": {"type": "integer"},
                        "steps_total": {"type": "integer"}
                    }
                },
                "timeline": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "status": {"type": "string"},
                            "location": {"type": "string"},
                            "timestamp": {"type": "string", "format": "date-time"},
                            "description": {"type": "string"},
                            "is_current": {"type": "boolean"}
                        },
                        "required": ["status", "timestamp"]
                    }
                },
                "origin": {"$ref": "#/$defs/Address"},
                "destination": {"$ref": "#/$defs/Address"},
                "estimated_delivery": {
                    "type": "object",
                    "properties": {
                        "date": {"type": "string", "format": "date"},
                        "time_range": {
                            "type": "object",
                            "properties": {
                                "start": {"type": "string"},
                                "end": {"type": "string"}
                            }
                        }
                    }
                },
                "package": {
                    "type": "object",
                    "properties": {
                        "weight": {"type": "number"},
                        "dimensions": {
                            "type": "object",
                            "properties": {
                                "length": {"type": "number"},
                                "width": {"type": "number"},
                                "height": {"type": "number"},
                                "unit": {"type": "string", "enum": ["cm", "in"]}
                            }
                        },
                        "description": {"type": "string"}
                    }
                },
                "actions": {
                    "type": "object",
                    "properties": {
                        "on_track_carrier": {"$ref": "#/$defs/Action"},
                        "on_contact_carrier": {"$ref": "#/$defs/Action"},
                        "on_report_issue": {"$ref": "#/$defs/Action"},
                        "on_share": {"$ref": "#/$defs/Action"}
                    }
                },
                "style": {
                    "type": "object",
                    "properties": {
                        "variant": {"type": "string", "enum": ["default", "compact", "timeline", "map"]},
                        "show_map": {"type": "boolean"},
                        "show_timeline": {"type": "boolean", "default": True}
                    }
                }
            },
            "required": ["tracking_id", "tracking_number", "status"]
        }
        
        # TransactionCard
        self._schemas["TransactionCard"] = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "$defs": COMMON_DEFINITIONS,
            "properties": {
                "transaction_id": {"type": "string"},
                "type": {
                    "type": "string",
                    "enum": ["payment", "refund", "withdrawal", "deposit", "transfer", "subscription", "purchase"]
                },
                "status": {
                    "type": "string",
                    "enum": ["pending", "processing", "completed", "failed", "cancelled", "reversed"]
                },
                "amount": {"$ref": "#/$defs/Price"},
                "fee": {"$ref": "#/$defs/Price"},
                "net_amount": {"$ref": "#/$defs/Price"},
                "description": {"type": "string"},
                "reference": {"type": "string"},
                "counterparty": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "type": {"type": "string", "enum": ["user", "merchant", "system"]},
                        "avatar": {"$ref": "#/$defs/Image"},
                        "account_identifier": {"type": "string"}
                    }
                },
                "payment_method": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": ["card", "bank", "wallet", "crypto", "cash"]},
                        "last_four": {"type": "string"},
                        "brand": {"type": "string"},
                        "icon": {"type": "string"}
                    }
                },
                "created_at": {"type": "string", "format": "date-time"},
                "completed_at": {"type": "string", "format": "date-time"},
                "receipt": {
                    "type": "object",
                    "properties": {
                        "number": {"type": "string"},
                        "url": {"type": "string", "format": "uri"},
                        "qr_code": {"type": "string"}
                    }
                },
                "metadata": {
                    "type": "object",
                    "additionalProperties": True
                },
                "actions": {
                    "type": "object",
                    "properties": {
                        "on_view_details": {"$ref": "#/$defs/Action"},
                        "on_download_receipt": {"$ref": "#/$defs/Action"},
                        "on_dispute": {"$ref": "#/$defs/Action"},
                        "on_repeat": {"$ref": "#/$defs/Action"},
                        "on_share": {"$ref": "#/$defs/Action"}
                    }
                },
                "style": {
                    "type": "object",
                    "properties": {
                        "variant": {"type": "string", "enum": ["default", "compact", "detailed", "statement"]},
                        "show_fee": {"type": "boolean", "default": False},
                        "highlight_amount": {"type": "boolean", "default": True}
                    }
                }
            },
            "required": ["transaction_id", "type", "amount", "status"]
        }
        
        # ProfileCard
        self._schemas["ProfileCard"] = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "$defs": COMMON_DEFINITIONS,
            "properties": {
                "profile_id": {"type": "string"},
                "user_type": {
                    "type": "string",
                    "enum": ["individual", "business", "vendor", "agent"]
                },
                "name": {
                    "type": "object",
                    "properties": {
                        "first": {"type": "string"},
                        "last": {"type": "string"},
                        "display": {"type": "string"},
                        "business": {"type": "string"}
                    },
                    "required": ["display"]
                },
                "avatar": {"$ref": "#/$defs/Image"},
                "cover_image": {"$ref": "#/$defs/Image"},
                "bio": {"type": "string", "maxLength": 500},
                "verified": {"type": "boolean"},
                "verification_badges": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string", "enum": ["email", "phone", "identity", "business", "premium"]},
                            "verified_at": {"type": "string", "format": "date-time"}
                        }
                    }
                },
                "rating": {"$ref": "#/$defs/Rating"},
                "stats": {
                    "type": "object",
                    "properties": {
                        "transactions": {"type": "integer"},
                        "reviews": {"type": "integer"},
                        "followers": {"type": "integer"},
                        "following": {"type": "integer"},
                        "listings": {"type": "integer"},
                        "sales": {"type": "integer"}
                    }
                },
                "location": {"$ref": "#/$defs/Address"},
                "contact": {
                    "type": "object",
                    "properties": {
                        "email": {"type": "string", "format": "email"},
                        "phone": {"type": "string"},
                        "whatsapp": {"type": "string"},
                        "website": {"type": "string", "format": "uri"}
                    }
                },
                "social_links": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "platform": {"type": "string"},
                            "handle": {"type": "string"},
                            "url": {"type": "string", "format": "uri"}
                        }
                    }
                },
                "membership": {
                    "type": "object",
                    "properties": {
                        "level": {"type": "string", "enum": ["free", "basic", "premium", "enterprise"]},
                        "since": {"type": "string", "format": "date"},
                        "expires": {"type": "string", "format": "date"},
                        "benefits": {"type": "array", "items": {"type": "string"}}
                    }
                },
                "actions": {
                    "type": "object",
                    "properties": {
                        "on_edit": {"$ref": "#/$defs/Action"},
                        "on_follow": {"$ref": "#/$defs/Action"},
                        "on_message": {"$ref": "#/$defs/Action"},
                        "on_view_listings": {"$ref": "#/$defs/Action"},
                        "on_share": {"$ref": "#/$defs/Action"},
                        "on_report": {"$ref": "#/$defs/Action"}
                    }
                },
                "style": {
                    "type": "object",
                    "properties": {
                        "variant": {"type": "string", "enum": ["default", "compact", "detailed", "sidebar"]},
                        "show_stats": {"type": "boolean", "default": True},
                        "show_membership": {"type": "boolean", "default": True},
                        "cover_height": {"type": "string"}
                    }
                }
            },
            "required": ["profile_id", "name"]
        }
        
        # BookingCard
        self._schemas["BookingCard"] = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "$defs": COMMON_DEFINITIONS,
            "properties": {
                "booking_id": {"type": "string"},
                "resource_type": {
                    "type": "string",
                    "enum": ["room", "table", "equipment", "vehicle", "service", "space"]
                },
                "title": {"type": "string"},
                "description": {"type": "string"},
                "resource": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "type": {"type": "string"},
                        "image": {"$ref": "#/$defs/Image"},
                        "capacity": {"type": "integer"}
                    },
                    "required": ["id", "name"]
                },
                "booking_details": {
                    "type": "object",
                    "properties": {
                        "check_in": {"type": "string", "format": "date-time"},
                        "check_out": {"type": "string", "format": "date-time"},
                        "duration_unit": {"type": "string", "enum": ["minutes", "hours", "days", "nights"]},
                        "duration_value": {"type": "number"},
                        "guests": {"type": "integer"},
                        "rooms": {"type": "integer"}
                    },
                    "required": ["check_in"]
                },
                "status": {
                    "type": "string",
                    "enum": ["pending", "confirmed", "checked_in", "checked_out", "cancelled", "no_show"]
                },
                "price": {"$ref": "#/$defs/Price"},
                "payment_status": {
                    "type": "string",
                    "enum": ["unpaid", "partial", "paid", "refunded"]
                },
                "location": {"$ref": "#/$defs/Address"},
                "amenities": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "special_requests": {"type": "string"},
                "confirmation_code": {"type": "string"},
                "qr_code": {"type": "string"},
                "actions": {
                    "type": "object",
                    "properties": {
                        "on_modify": {"$ref": "#/$defs/Action"},
                        "on_cancel": {"$ref": "#/$defs/Action"},
                        "on_view_details": {"$ref": "#/$defs/Action"},
                        "on_check_in": {"$ref": "#/$defs/Action"},
                        "on_contact": {"$ref": "#/$defs/Action"}
                    }
                },
                "style": {
                    "type": "object",
                    "properties": {
                        "variant": {"type": "string", "enum": ["default", "compact", "timeline", "ticket"]}
                    }
                }
            },
            "required": ["booking_id", "resource", "booking_details"]
        }
        
        # RewardCard
        self._schemas["RewardCard"] = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "$defs": COMMON_DEFINITIONS,
            "properties": {
                "reward_id": {"type": "string"},
                "title": {"type": "string"},
                "description": {"type": "string"},
                "type": {
                    "type": "string",
                    "enum": ["points", "cashback", "discount", "free_item", "badge", "achievement"]
                },
                "value": {"type": "number"},
                "points_required": {"type": "integer"},
                "points_balance": {"type": "integer"},
                "progress": {
                    "type": "object",
                    "properties": {
                        "current": {"type": "number"},
                        "target": {"type": "number"},
                        "percentage": {"type": "number"}
                    }
                },
                "expires_at": {"type": "string", "format": "date"},
                "image": {"$ref": "#/$defs/Image"},
                "badge": {
                    "type": "object",
                    "properties": {
                        "icon": {"type": "string"},
                        "color": {"type": "string"},
                        "tier": {"type": "string"}
                    }
                },
                "terms": {"type": "string"},
                "is_claimed": {"type": "boolean"},
                "is_available": {"type": "boolean"},
                "actions": {
                    "type": "object",
                    "properties": {
                        "on_claim": {"$ref": "#/$defs/Action"},
                        "on_view_details": {"$ref": "#/$defs/Action"},
                        "on_share": {"$ref": "#/$defs/Action"}
                    }
                },
                "style": {
                    "type": "object",
                    "properties": {
                        "variant": {"type": "string", "enum": ["default", "compact", "progress", "badge"]}
                    }
                }
            },
            "required": ["reward_id", "title", "type"]
        }
        
        # NotificationCard
        self._schemas["NotificationCard"] = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "$defs": COMMON_DEFINITIONS,
            "properties": {
                "notification_id": {"type": "string"},
                "type": {
                    "type": "string",
                    "enum": ["info", "success", "warning", "error", "promotion", "system", "message"]
                },
                "title": {"type": "string"},
                "body": {"type": "string"},
                "icon": {"type": "string"},
                "image": {"$ref": "#/$defs/Image"},
                "sender": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "avatar": {"$ref": "#/$defs/Image"}
                    }
                },
                "data": {"type": "object"},
                "read": {"type": "boolean"},
                "read_at": {"type": "string", "format": "date-time"},
                "created_at": {"type": "string", "format": "date-time"},
                "actions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "label": {"type": "string"},
                            "action": {"$ref": "#/$defs/Action"}
                        }
                    }
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "normal", "high", "urgent"]
                },
                "style": {
                    "type": "object",
                    "properties": {
                        "variant": {"type": "string", "enum": ["default", "compact", "expanded", "banner"]}
                    }
                }
            },
            "required": ["notification_id", "type", "title"]
        }
        
        # MapViewCard
        self._schemas["MapViewCard"] = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "$defs": COMMON_DEFINITIONS,
            "properties": {
                "map_id": {"type": "string"},
                "center": {
                    "type": "object",
                    "properties": {
                        "lat": {"type": "number", "minimum": -90, "maximum": 90},
                        "lng": {"type": "number", "minimum": -180, "maximum": 180}
                    },
                    "required": ["lat", "lng"]
                },
                "zoom": {"type": "number", "minimum": 1, "maximum": 20, "default": 15},
                "markers": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "position": {
                                "type": "object",
                                "properties": {
                                    "lat": {"type": "number"},
                                    "lng": {"type": "number"}
                                },
                                "required": ["lat", "lng"]
                            },
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "icon": {"type": "string"},
                            "color": {"type": "string"},
                            "cluster": {"type": "string"},
                            "data": {"type": "object"}
                        },
                        "required": ["id", "position"]
                    }
                },
                "routes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "points": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "lat": {"type": "number"},
                                        "lng": {"type": "number"}
                                    }
                                }
                            },
                            "color": {"type": "string"},
                            "width": {"type": "number"},
                            "mode": {"type": "string", "enum": ["driving", "walking", "cycling", "transit"]}
                        },
                        "required": ["id", "points"]
                    }
                },
                "bounds": {
                    "type": "object",
                    "properties": {
                        "ne": {"type": "object", "properties": {"lat": {"type": "number"}, "lng": {"type": "number"}}},
                        "sw": {"type": "object", "properties": {"lat": {"type": "number"}, "lng": {"type": "number"}}}
                    }
                },
                "user_location": {
                    "type": "object",
                    "properties": {
                        "lat": {"type": "number"},
                        "lng": {"type": "number"},
                        "accuracy": {"type": "number"},
                        "show": {"type": "boolean"}
                    }
                },
                "style_url": {"type": "string"},
                "show_controls": {
                    "type": "object",
                    "properties": {
                        "zoom": {"type": "boolean", "default": True},
                        "compass": {"type": "boolean", "default": True},
                        "scale": {"type": "boolean"},
                        "my_location": {"type": "boolean"}
                    }
                },
                "actions": {
                    "type": "object",
                    "properties": {
                        "on_marker_click": {"$ref": "#/$defs/Action"},
                        "on_map_click": {"$ref": "#/$defs/Action"},
                        "on_directions": {"$ref": "#/$defs/Action"},
                        "on_fullscreen": {"$ref": "#/$defs/Action"}
                    }
                },
                "style": {
                    "type": "object",
                    "properties": {
                        "height": {"type": "string", "default": "300px"},
                        "variant": {"type": "string", "enum": ["default", "fullscreen", "embedded", "preview"]}
                    }
                }
            },
            "required": ["map_id"]
        }
        
        # ChartCard
        self._schemas["ChartCard"] = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "$defs": COMMON_DEFINITIONS,
            "properties": {
                "chart_id": {"type": "string"},
                "title": {"type": "string"},
                "subtitle": {"type": "string"},
                "chart_type": {
                    "type": "string",
                    "enum": ["line", "area", "bar", "column", "pie", "donut", "radar", "scatter", "heatmap"]
                },
                "data": {
                    "type": "object",
                    "properties": {
                        "labels": {"type": "array", "items": {"type": "string"}},
                        "datasets": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "label": {"type": "string"},
                                    "data": {"type": "array", "items": {"type": "number"}},
                                    "color": {"type": "string"},
                                    "backgroundColor": {"type": "string"},
                                    "borderColor": {"type": "string"}
                                },
                                "required": ["data"]
                            }
                        }
                    },
                    "required": ["labels", "datasets"]
                },
                "options": {
                    "type": "object",
                    "properties": {
                        "animated": {"type": "boolean", "default": True},
                        "legend": {
                            "type": "object",
                            "properties": {
                                "show": {"type": "boolean"},
                                "position": {"type": "string", "enum": ["top", "bottom", "left", "right"]}
                            }
                        },
                        "axes": {
                            "type": "object",
                            "properties": {
                                "x": {"type": "object"},
                                "y": {"type": "object"}
                            }
                        },
                        "tooltip": {"type": "object"},
                        "zoom": {"type": "boolean"}
                    }
                },
                "summary": {
                    "type": "object",
                    "properties": {
                        "total": {"type": "number"},
                        "average": {"type": "number"},
                        "change": {"type": "number"},
                        "change_percentage": {"type": "number"},
                        "trend": {"type": "string", "enum": ["up", "down", "neutral"]}
                    }
                },
                "time_range": {
                    "type": "string",
                    "enum": ["hour", "day", "week", "month", "quarter", "year", "custom"]
                },
                "refresh_interval": {"type": "integer"},
                "actions": {
                    "type": "object",
                    "properties": {
                        "on_point_click": {"$ref": "#/$defs/Action"},
                        "on_export": {"$ref": "#/$defs/Action"},
                        "on_fullscreen": {"$ref": "#/$defs/Action"},
                        "on_time_range_change": {"$ref": "#/$defs/Action"}
                    }
                },
                "style": {
                    "type": "object",
                    "properties": {
                        "height": {"type": "string", "default": "250px"},
                        "variant": {"type": "string", "enum": ["default", "sparkline", "compact", "dashboard"]}
                    }
                }
            },
            "required": ["chart_id", "chart_type", "data"]
        }
    
    def get_schema(self, component_type: str) -> Optional[Dict[str, Any]]:
        """Get schema for a component type."""
        return self._schemas.get(component_type)
    
    def get_all_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Get all component schemas."""
        return self._schemas.copy()
    
    def register_schema(self, component_type: str, schema: Dict[str, Any]) -> None:
        """Register a new component schema."""
        self._schemas[component_type] = schema
    
    def get_component_types(self) -> List[str]:
        """Get all registered component types."""
        return list(self._schemas.keys())


# Singleton instance
_schema_registry: Optional[ComponentSchemaRegistry] = None


def get_schema_registry() -> ComponentSchemaRegistry:
    """Get the singleton schema registry instance."""
    global _schema_registry
    if _schema_registry is None:
        _schema_registry = ComponentSchemaRegistry()
    return _schema_registry
