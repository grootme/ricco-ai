"""
GenUI/A2UI Subscription Models
Modelos para el sistema de suscripción y uso de GenUI/A2UI
"""

from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class SubscriptionTier(str, Enum):
    """Niveles de suscripción para GenUI/A2UI"""
    FREE = "free"           # Gratuito con límites básicos
    STARTER = "starter"     # Para pequeños negocios
    PROFESSIONAL = "professional"  # Para profesionales
    BUSINESS = "business"   # Para empresas
    ENTERPRISE = "enterprise"  # Para grandes empresas
    CUSTOM = "custom"       # Plan personalizado


class UsageType(str, Enum):
    """Tipos de uso de GenUI/A2UI"""
    SURFACE_GENERATION = "surface_generation"    # Generar una superficie UI
    ACTION_PROCESSING = "action_processing"      # Procesar acción del usuario
    CATALOG_LOADING = "catalog_loading"          # Cargar catálogo de componentes
    CONTEXT_BUILDING = "context_building"        # Construir contexto personalizado
    AI_INFERENCE = "ai_inference"                # Inferencia de IA para UI
    MINI_PROGRAM_RUN = "mini_program_run"        # Ejecutar mini programa


# Límites por plan
PLAN_LIMITS = {
    SubscriptionTier.FREE: {
        "monthly_queries": 100,
        "daily_queries": 10,
        "rate_limit_per_minute": 5,
        "context_types": ["personal", "device"],
        "max_components_per_surface": 20,
        "surfaces_cache_ttl": 300,  # 5 minutos
        "support": "community",
        "price_monthly": 0,
        "price_per_extra_query": 0.05,
    },
    SubscriptionTier.STARTER: {
        "monthly_queries": 1000,
        "daily_queries": 100,
        "rate_limit_per_minute": 30,
        "context_types": ["personal", "device", "temporal", "spatial"],
        "max_components_per_surface": 50,
        "surfaces_cache_ttl": 900,  # 15 minutos
        "support": "email",
        "price_monthly": 9.99,
        "price_per_extra_query": 0.02,
    },
    SubscriptionTier.PROFESSIONAL: {
        "monthly_queries": 10000,
        "daily_queries": 1000,
        "rate_limit_per_minute": 100,
        "context_types": ["personal", "device", "temporal", "spatial", "solution", "horizontal"],
        "max_components_per_surface": 100,
        "surfaces_cache_ttl": 1800,  # 30 minutos
        "support": "priority_email",
        "price_monthly": 49.99,
        "price_per_extra_query": 0.01,
    },
    SubscriptionTier.BUSINESS: {
        "monthly_queries": 50000,
        "daily_queries": 5000,
        "rate_limit_per_minute": 300,
        "context_types": ["personal", "device", "temporal", "spatial", "solution", "horizontal", "vertical"],
        "max_components_per_surface": 200,
        "surfaces_cache_ttl": 3600,  # 1 hora
        "support": "dedicated_slack",
        "price_monthly": 199.99,
        "price_per_extra_query": 0.005,
    },
    SubscriptionTier.ENTERPRISE: {
        "monthly_queries": -1,  # Ilimitado
        "daily_queries": -1,
        "rate_limit_per_minute": 1000,
        "context_types": ["all"],
        "max_components_per_surface": -1,
        "surfaces_cache_ttl": 7200,  # 2 horas
        "support": "dedicated_team",
        "price_monthly": 499.99,
        "price_per_extra_query": 0,
    },
    SubscriptionTier.CUSTOM: {
        "monthly_queries": -1,
        "daily_queries": -1,
        "rate_limit_per_minute": -1,
        "context_types": ["all"],
        "max_components_per_surface": -1,
        "surfaces_cache_ttl": -1,
        "support": "enterprise",
        "price_monthly": "custom",
        "price_per_extra_query": "custom",
    },
}


class GenUISubscription(BaseModel):
    """Suscripción a GenUI/A2UI"""
    id: UUID = Field(default_factory=uuid4)
    user_id: str  # RICCO ID del usuario
    organization_id: Optional[str] = None
    
    # Plan actual
    tier: SubscriptionTier = SubscriptionTier.FREE
    status: str = "active"  # active, suspended, cancelled, expired
    
    # Período de facturación
    billing_cycle: str = "monthly"  # monthly, yearly
    current_period_start: datetime
    current_period_end: datetime
    
    # Uso actual
    queries_used_this_month: int = 0
    queries_used_today: int = 0
    last_query_at: Optional[datetime] = None
    
    # Features habilitadas
    enabled_context_types: List[str] = Field(default_factory=lambda: ["personal", "device"])
    custom_limits: Optional[Dict[str, Any]] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True


class GenUIUsageRecord(BaseModel):
    """Registro de uso de GenUI/A2UI"""
    id: UUID = Field(default_factory=uuid4)
    subscription_id: UUID
    user_id: str
    
    # Detalles del uso
    usage_type: UsageType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Información de la consulta
    mini_program_id: Optional[str] = None
    surface_id: Optional[str] = None
    action_id: Optional[str] = None
    solution: Optional[str] = None
    
    # Métricas
    tokens_used: int = 0
    latency_ms: int = 0
    components_generated: int = 0
    
    # Contexto usado
    context_types_used: List[str] = Field(default_factory=list)
    
    # Costo
    cost_credits: float = 0.0  # Energy Points
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = None


class GenUIQuota(BaseModel):
    """Cuota de uso de GenUI/A2UI"""
    subscription_id: UUID
    period: str  # "2024-01" format
    
    # Límites
    monthly_limit: int
    daily_limit: int
    
    # Uso
    monthly_used: int = 0
    daily_used: int = 0
    
    # Extra usage (pay-per-use)
    extra_queries_used: int = 0
    extra_queries_cost: float = 0.0
    
    # Timestamps
    last_reset_daily: datetime
    last_reset_monthly: datetime
    
    def remaining_monthly(self) -> int:
        if self.monthly_limit == -1:
            return -1  # Ilimitado
        return max(0, self.monthly_limit - self.monthly_used)
    
    def remaining_daily(self) -> int:
        if self.daily_limit == -1:
            return -1  # Ilimitado
        return max(0, self.daily_limit - self.daily_used)
    
    def can_use(self, count: int = 1) -> bool:
        return (self.remaining_monthly() >= count or self.remaining_monthly() == -1) and \
               (self.remaining_daily() >= count or self.remaining_daily() == -1)


class GenUIInvoice(BaseModel):
    """Factura de GenUI/A2UI"""
    id: UUID = Field(default_factory=uuid4)
    subscription_id: UUID
    user_id: str
    
    # Período
    period_start: datetime
    period_end: datetime
    
    # Detalles de facturación
    base_amount: float  # Cargo base del plan
    extra_usage_amount: float = 0.0  # Cargo por uso extra
    total_amount: float
    
    # Uso facturado
    queries_included: int
    queries_used: int
    extra_queries: int = 0
    
    # Estado
    status: str = "pending"  # pending, paid, failed, refunded
    paid_at: Optional[datetime] = None
    
    # Payment
    payment_method_id: Optional[str] = None
    invoice_url: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


class GenUIAPIKey(BaseModel):
    """API Key para acceso a GenUI/A2UI"""
    id: UUID = Field(default_factory=uuid4)
    subscription_id: UUID
    user_id: str
    
    # Key details
    key_hash: str  # Hash de la API key
    key_prefix: str  # Primeros 8 caracteres para identificación
    
    # Permisos
    scopes: List[str] = Field(default_factory=lambda: ["read", "write"])
    
    # Límites específicos de la key
    rate_limit_per_minute: Optional[int] = None
    
    # Estado
    is_active: bool = True
    last_used_at: Optional[datetime] = None
    
    # Naming
    name: str  # Nombre descriptivo
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
