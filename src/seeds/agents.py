"""
Agent Seeds for RICCO AI.

Database-managed agent configurations.
"""

from typing import Any, Dict, List

# Agent seed data
AGENT_SEEDS: List[Dict[str, Any]] = [
    # Orchestrator
    {
        "agent_id": "orchestrator-main",
        "agent_type": "orchestrator",
        "name": "Main Orchestrator",
        "description": "Main orchestrator for coordinating agent swarm",
        "capabilities": [
            "natural_language",
            "task_routing",
            "agent_coordination",
        ],
        "system_prompt": """You are the main orchestrator for RICCO AI.
Your role is to coordinate specialist agents and route tasks appropriately.
Always consider user context and privacy when delegating tasks.""",
        "mcp_servers": ["ricco-core", "ricco-identity"],
        "max_tokens": 4096,
        "temperature": 0.7,
        "metadata": {
            "priority": 1,
            "is_primary": True,
        },
        "is_enabled": True,
    },
    
    # Commerce Agent
    {
        "agent_id": "commerce-agent",
        "agent_type": "commerce",
        "name": "Commerce Agent",
        "description": "E-commerce and order management specialist",
        "capabilities": [
            "order_management",
            "inventory_check",
            "payment_processing",
            "product_recommendations",
        ],
        "system_prompt": """You are a commerce specialist for RICCO AI.
Help users with orders, product searches, and shopping assistance.
Always verify product availability and provide accurate pricing.""",
        "mcp_servers": ["ricco-core", "payment-processor", "postgresql-main"],
        "max_tokens": 4096,
        "temperature": 0.6,
        "metadata": {
            "domain": "commerce",
            "supports_visa_payment": True,
        },
        "is_enabled": True,
    },
    
    # Health Agent
    {
        "agent_id": "health-agent",
        "agent_type": "health",
        "name": "Health Agent",
        "description": "Health consultation and appointment booking specialist",
        "capabilities": [
            "health_consultation",
            "appointment_booking",
            "medical_records",
            "symptom_analysis",
        ],
        "system_prompt": """You are a health consultation assistant for RICCO AI.
Provide general health information and help users book appointments.
Always include appropriate medical disclaimers.
Never diagnose or prescribe - recommend professional medical advice.""",
        "mcp_servers": ["ricco-core", "postgresql-main"],
        "max_tokens": 4096,
        "temperature": 0.5,
        "metadata": {
            "domain": "health",
            "requires_disclaimer": True,
        },
        "is_enabled": True,
    },
    
    # Finance Agent
    {
        "agent_id": "finance-agent",
        "agent_type": "finance",
        "name": "Finance Agent",
        "description": "Financial advisory and payment processing specialist",
        "capabilities": [
            "financial_advice",
            "payment_processing",
            "crypto_operations",
            "budget_tracking",
        ],
        "system_prompt": """You are a financial advisory assistant for RICCO AI.
Help users with financial questions, payments, and crypto operations.
Always include appropriate financial disclaimers.
Be transparent about fees and exchange rates.""",
        "mcp_servers": ["ricco-core", "crypto-wallet", "payment-processor"],
        "max_tokens": 4096,
        "temperature": 0.5,
        "metadata": {
            "domain": "finance",
            "requires_disclaimer": True,
            "supports_crypto": True,
        },
        "is_enabled": True,
    },
    
    # Logistics Agent
    {
        "agent_id": "logistics-agent",
        "agent_type": "logistics",
        "name": "Logistics Agent",
        "description": "Shipping and delivery tracking specialist",
        "capabilities": [
            "shipping_tracking",
            "delivery_estimates",
            "inventory_management",
            "route_optimization",
        ],
        "system_prompt": """You are a logistics specialist for RICCO AI.
Help users track shipments and get delivery estimates.
Provide accurate information about shipping options and costs.""",
        "mcp_servers": ["ricco-core", "postgresql-main"],
        "max_tokens": 4096,
        "temperature": 0.6,
        "metadata": {
            "domain": "logistics",
        },
        "is_enabled": True,
    },
    
    # Rewards Agent
    {
        "agent_id": "rewards-agent",
        "agent_type": "rewards",
        "name": "Rewards Agent",
        "description": "Energy Points and rewards management specialist",
        "capabilities": [
            "energy_points_management",
            "reward_redemption",
            "loyalty_programs",
        ],
        "system_prompt": """You are a rewards specialist for RICCO AI.
Help users manage their Energy Points and redeem rewards.
Explain the benefits of the loyalty program.""",
        "mcp_servers": ["ricco-core"],
        "max_tokens": 4096,
        "temperature": 0.7,
        "metadata": {
            "domain": "rewards",
        },
        "is_enabled": True,
    },
    
    # Booking Agent
    {
        "agent_id": "booking-agent",
        "agent_type": "booking",
        "name": "Booking Agent",
        "description": "Appointment and reservation booking specialist",
        "capabilities": [
            "appointment_booking",
            "reservation_management",
            "calendar_integration",
        ],
        "system_prompt": """You are a booking specialist for RICCO AI.
Help users book appointments and manage reservations.
Confirm availability before finalizing bookings.""",
        "mcp_servers": ["ricco-core", "productivity-suite"],
        "max_tokens": 4096,
        "temperature": 0.6,
        "metadata": {
            "domain": "booking",
        },
        "is_enabled": True,
    },
    
    # Travel Agent
    {
        "agent_id": "travel-agent",
        "agent_type": "travel",
        "name": "Travel Agent",
        "description": "Travel planning and booking specialist",
        "capabilities": [
            "travel_planning",
            "hotel_booking",
            "flight_search",
            "itinerary_creation",
        ],
        "system_prompt": """You are a travel specialist for RICCO AI.
Help users plan trips, find accommodations, and book flights.
Consider user preferences and budget constraints.""",
        "mcp_servers": ["ricco-core", "web-fetcher"],
        "max_tokens": 4096,
        "temperature": 0.7,
        "metadata": {
            "domain": "travel",
        },
        "is_enabled": True,
    },
    
    # Social Agent
    {
        "agent_id": "social-agent",
        "agent_type": "social",
        "name": "Social Agent",
        "description": "Social features and community management specialist",
        "capabilities": [
            "social_interactions",
            "community_management",
            "social_sharing",
        ],
        "system_prompt": """You are a social features specialist for RICCO AI.
Help users connect with others and manage their social presence.
Respect user privacy preferences.""",
        "mcp_servers": ["ricco-core"],
        "max_tokens": 4096,
        "temperature": 0.8,
        "metadata": {
            "domain": "social",
        },
        "is_enabled": True,
    },
    
    # Legal Agent
    {
        "agent_id": "legal-agent",
        "agent_type": "legal",
        "name": "Legal Agent",
        "description": "Legal information and compliance specialist",
        "capabilities": [
            "legal_information",
            "compliance_checking",
            "document_review",
        ],
        "system_prompt": """You are a legal information assistant for RICCO AI.
Provide general legal information and help with compliance questions.
Always include disclaimers that this is not legal advice.
Recommend professional legal consultation for specific cases.""",
        "mcp_servers": ["ricco-core", "document-processor"],
        "max_tokens": 4096,
        "temperature": 0.4,
        "metadata": {
            "domain": "legal",
            "requires_disclaimer": True,
        },
        "is_enabled": True,
    },
    
    # General Agent
    {
        "agent_id": "general-agent",
        "agent_type": "general",
        "name": "General Agent",
        "description": "General purpose assistant for miscellaneous queries",
        "capabilities": [
            "natural_language",
            "general_knowledge",
            "task_assistance",
        ],
        "system_prompt": """You are a general purpose assistant for RICCO AI.
Help users with a wide variety of questions and tasks.
When specialized help is needed, recommend the appropriate specialist agent.""",
        "mcp_servers": ["ricco-core", "web-fetcher", "openai-provider"],
        "max_tokens": 4096,
        "temperature": 0.7,
        "metadata": {
            "is_fallback": True,
        },
        "is_enabled": True,
    },
]


def get_agents_by_type(agent_type: str) -> List[Dict[str, Any]]:
    """Get all agents of a specific type."""
    return [
        agent for agent in AGENT_SEEDS
        if agent["agent_type"] == agent_type
    ]


def get_enabled_agents() -> List[Dict[str, Any]]:
    """Get all enabled agents."""
    return [
        agent for agent in AGENT_SEEDS
        if agent.get("is_enabled", True)
    ]


def get_primary_agent() -> Dict[str, Any]:
    """Get the primary orchestrator agent."""
    for agent in AGENT_SEEDS:
        if agent.get("metadata", {}).get("is_primary", False):
            return agent
    return AGENT_SEEDS[0]


def get_all_agent_types() -> List[str]:
    """Get all unique agent types."""
    return list(set(agent["agent_type"] for agent in AGENT_SEEDS))
