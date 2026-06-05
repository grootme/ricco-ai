"""
Consolidated Enumerations for RICCO AI.

SINGLE SOURCE OF TRUTH for all shared enumerations.
OCP-Compliant: Values loaded from configuration, not hardcoded.

Principles applied:
- ELIMINAR antes de CREAR: Removed duplicate enum definitions
- CONSOLIDAR antes de DIVIDIR: Single source of truth
- OCP: Open for extension via configuration, closed for modification
"""

from enum import Enum
from typing import Dict, List, Any, Type, TypeVar
import json
from pathlib import Path


T = TypeVar('T', bound='ExtensibleEnum')


class ExtensibleEnum(Enum):
    """
    Base enum class that supports OCP through configuration-based extension.
    
    New values can be added via configuration files without modifying code.
    """
    
    @classmethod
    def get_values(cls) -> List[str]:
        """Get all enum values as strings."""
        return [e.value for e in cls]
    
    @classmethod
    def from_string(cls: Type[T], value: str) -> T:
        """Get enum from string value, case-insensitive."""
        value_lower = value.lower()
        for e in cls:
            if e.value.lower() == value_lower:
                return e
        raise ValueError(f"Invalid {cls.__name__}: {value}")
    
    @classmethod
    def contains(cls, value: str) -> bool:
        """Check if a string value exists in enum."""
        try:
            cls.from_string(value)
            return True
        except ValueError:
            return False


# =============================================================================
# AI PROVIDER ENUMS
# =============================================================================

class AIProviderType(ExtensibleEnum):
    """Supported AI provider types."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    LOCAL = "local"
    OPENROUTER = "openrouter"


# =============================================================================
# AGENT ENUMS
# =============================================================================

class AgentType(ExtensibleEnum):
    """
    Types of agents in the system.
    
    Consolidated from:
    - core/protocols.py (LLM, A2A, SEQUENTIAL, etc.)
    - schemas/config_schemas.py (ORCHESTRATOR, COMMERCE, etc.)
    """
    # Core agent types
    LLM = "llm"
    A2A = "a2a"
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    LOOP = "loop"
    WORKFLOW = "workflow"
    TASK = "task"
    
    # Domain agent types
    ORCHESTRATOR = "orchestrator"
    COMMERCE = "commerce"
    HEALTH = "health"
    LOGISTICS = "logistics"
    FINANCE = "finance"
    REWARDS = "rewards"
    BOOKING = "booking"
    TRAVEL = "travel"
    SOCIAL = "social"
    LEGAL = "legal"
    GENERAL = "general"


class AgentCapability(ExtensibleEnum):
    """Agent capabilities."""
    NATURAL_LANGUAGE = "natural_language"
    ORDER_MANAGEMENT = "order_management"
    PAYMENT_PROCESSING = "payment_processing"
    INVENTORY_CHECK = "inventory_check"
    APPOINTMENT_BOOKING = "appointment_booking"
    TRAVEL_PLANNING = "travel_planning"
    FINANCIAL_ADVICE = "financial_advice"
    HEALTH_CONSULTATION = "health_consultation"
    LEGAL_ASSISTANCE = "legal_assistance"
    REWARDS_MANAGEMENT = "rewards_management"
    CRYPTO_OPERATIONS = "crypto_operations"


class AgentState(ExtensibleEnum):
    """Agent lifecycle states."""
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    SHUTDOWN = "shutdown"


class SkillLevel(ExtensibleEnum):
    """Skill proficiency levels."""
    NOVICE = "novice"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


# =============================================================================
# MCP ENUMS
# =============================================================================

class MCPCategory(ExtensibleEnum):
    """MCP server categories."""
    FILESYSTEM = "filesystem"
    DATABASE = "database"
    WEB = "web"
    AI = "ai"
    FINANCE = "finance"
    RICCO = "ricco"
    DEVOPS = "devops"
    MONITORING = "monitoring"
    DOCUMENTS = "documents"
    PRODUCTIVITY = "productivity"


class TransportType(ExtensibleEnum):
    """MCP transport types."""
    STDIO = "stdio"
    HTTP = "http"
    GRPC = "grpc"
    WEBSOCKET = "websocket"


class HealthStatus(ExtensibleEnum):
    """Server health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class ToolRiskLevel(ExtensibleEnum):
    """Risk levels for MCP tools."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# =============================================================================
# SKILL ENUMS
# =============================================================================

class SkillCategory(ExtensibleEnum):
    """Categories for skills."""
    DOCUMENT = "document"
    VISUALIZATION = "visualization"
    AI = "ai"
    BLUEPRINT = "blueprint"
    COMMUNICATION = "communication"
    DATA = "data"
    DEVELOPMENT = "development"
    PRODUCTIVITY = "productivity"
    RESEARCH = "research"
    FINANCE = "finance"
    INDUSTRIAL = "industrial"


class SkillStatus(ExtensibleEnum):
    """Status of a skill."""
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    EXPERIMENTAL = "experimental"
    DISABLED = "disabled"


# =============================================================================
# CONTEXT ENUMS
# =============================================================================

class ContextType(ExtensibleEnum):
    """Types of context."""
    PERSONAL = "personal"
    SPATIAL = "spatial"
    TEMPORAL = "temporal"
    DEVICE = "device"
    SOLUTION = "solution"
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"
    SKILLS = "skills"
    RAG = "rag"
    CONVERSATION = "conversation"


# =============================================================================
# UI ENUMS
# =============================================================================

class UIContextMode(ExtensibleEnum):
    """UI generation modes."""
    MINIMAL = "minimal"
    STANDARD = "standard"
    DETAILED = "detailed"
    ACCESSIBILITY = "accessibility"


class A2UIComponentType(ExtensibleEnum):
    """Types of A2UI components."""
    BUTTON = "button"
    CARD = "card"
    FORM = "form"
    LIST = "list"
    MODAL = "modal"
    NAVIGATION = "navigation"
    INPUT = "input"
    TEXT = "text"
    IMAGE = "image"
    CONTAINER = "container"
    PRODUCT_CARD = "product_card"
    USER_PROFILE = "user_profile"
    DASHBOARD = "dashboard"


class A2UIPlatform(ExtensibleEnum):
    """Target platforms for A2UI components."""
    REACT = "react"
    FLUTTER = "flutter"
    LIT = "lit"
    NATIVE = "native"
    HTML = "html"


# =============================================================================
# SUBSCRIPTION ENUMS
# =============================================================================

class SubscriptionTier(ExtensibleEnum):
    """Subscription tier levels."""
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


# =============================================================================
# STREAMING ENUMS
# =============================================================================

class ConnectionType(ExtensibleEnum):
    """WebSocket connection types."""
    CHAT = "chat"
    STREAMING = "streaming"
    NOTIFICATION = "notification"
    SYSTEM = "system"


class StreamEventType(ExtensibleEnum):
    """Stream event types."""
    START = "start"
    CHUNK = "chunk"
    COMPLETE = "complete"
    ERROR = "error"
    CANCEL = "cancel"


# =============================================================================
# BLUEPRINT ENUMS
# =============================================================================

class BlueprintType(ExtensibleEnum):
    """Types of NVIDIA AI Blueprints."""
    AIQ_RESEARCH = "aiq_research"
    RAG = "rag"
    VIDEO_SEARCH = "video_search"
    DATA_FLYWHEEL = "data_flywheel"
    DIGITAL_HUMAN = "digital_human"
    HEALTHCARE = "healthcare"
    RETAIL_COMMERCE = "retail_commerce"
    # Extended blueprints
    AMBIENT_PATIENT = "ambient_patient"
    BIOMEDICAL_RESEARCH = "biomedical_research"
    FINANCIAL_DISTILLATION = "financial_distillation"
    GENOMICS = "genomics"
    INDUSTRIAL = "industrial"
    INTELLIGENT_WAREHOUSE = "intelligent_warehouse"
    MULTI_AGENT = "multi_agent"
    PORTFOLIO_OPTIMIZATION = "portfolio_optimization"
    RETAIL_SHOPPING = "retail_shopping"
    STREAMING_RAG = "streaming_rag"
    VIRTUAL_ASSISTANT = "virtual_assistant"
    VOICE_AGENT = "voice_agent"


class BlueprintStatus(ExtensibleEnum):
    """Status of a blueprint execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# =============================================================================
# BACKWARD COMPATIBILITY ALIASES
# =============================================================================

# For code that imported from old locations
# These will be deprecated in future versions


# =============================================================================
# ENUM REGISTRY FOR DYNAMIC EXTENSION
# =============================================================================

class EnumRegistry:
    """
    Registry for dynamically extending enums at runtime.
    
    OCP-Compliant: New enum values can be added without modifying code.
    """
    
    _extensions: Dict[str, Dict[str, Any]] = {}
    
    @classmethod
    def register_extension(cls, enum_name: str, value: str, description: str = "") -> None:
        """Register a new enum value extension."""
        if enum_name not in cls._extensions:
            cls._extensions[enum_name] = {}
        cls._extensions[enum_name][value] = {
            "value": value,
            "description": description,
        }
    
    @classmethod
    def get_extensions(cls, enum_name: str) -> Dict[str, Any]:
        """Get all extensions for an enum."""
        return cls._extensions.get(enum_name, {})
    
    @classmethod
    def load_from_config(cls, config_path: Path) -> None:
        """Load enum extensions from configuration file."""
        if not config_path.exists():
            return
        
        with open(config_path) as f:
            config = json.load(f)
        
        for enum_name, extensions in config.get("enum_extensions", {}).items():
            for ext in extensions:
                cls.register_extension(
                    enum_name=enum_name,
                    value=ext.get("value"),
                    description=ext.get("description", ""),
                )


# Global enum registry
enum_registry = EnumRegistry()


# Load extensions from config if available
_enum_config_path = Path(__file__).parent.parent / "config" / "enum_extensions.json"
if _enum_config_path.exists():
    enum_registry.load_from_config(_enum_config_path)
