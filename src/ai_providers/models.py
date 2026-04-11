"""
AI Service Models
Data models for AI-powered recommendations and consultations
"""

from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any, AsyncIterator
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class AIProviderType(str, Enum):
    """AI provider types"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    OPENROUTER = "openrouter"


class RecommendationType(str, Enum):
    """Types of recommendations"""
    BUSINESS = "business"
    PRODUCT = "product"
    SERVICE = "service"
    SIMILAR = "similar"
    PERSONALIZED = "personalized"


class ConsultationStatus(str, Enum):
    """Consultation session status"""
    ACTIVE = "active"
    ENDED = "ended"
    EXPIRED = "expired"


class AIRequest(BaseModel):
    """AI request model"""
    id: UUID = Field(default_factory=uuid4)
    prompt: str
    context: Optional[Dict[str, Any]] = None
    user_id: str
    subscription_id: Optional[UUID] = None
    
    # Request configuration
    provider_preference: Optional[AIProviderType] = None
    model_preference: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    stream: bool = False
    
    # Metadata
    request_type: str = "general"  # recommendation, consultation, general
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Tracking
    session_id: Optional[UUID] = None
    conversation_history: Optional[List[Dict[str, str]]] = None
    
    class Config:
        use_enum_values = True


class AIResponse(BaseModel):
    """AI response model"""
    id: UUID = Field(default_factory=uuid4)
    request_id: UUID
    
    # Content
    content: str
    streaming: bool = False
    
    # Usage tracking
    tokens_used: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    
    # Cache info
    cached: bool = False
    cache_key: Optional[str] = None
    
    # Model info
    model_used: str
    provider: AIProviderType
    
    # Performance
    latency_ms: int = 0
    
    # Metadata
    finish_reason: str = "stop"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Additional data
    recommendations: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        use_enum_values = True


class RecommendationContext(BaseModel):
    """Context for generating recommendations"""
    user_id: str
    
    # User history
    user_history: List[Dict[str, Any]] = Field(default_factory=list)
    recent_views: List[str] = Field(default_factory=list)
    recent_searches: List[str] = Field(default_factory=list)
    past_purchases: List[str] = Field(default_factory=list)
    
    # Preferences
    preferences: Dict[str, Any] = Field(default_factory=dict)
    favorite_categories: List[str] = Field(default_factory=list)
    price_range: Optional[Dict[str, float]] = None
    
    # Location context
    location: Optional[Dict[str, Any]] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_km: float = 10.0
    
    # Time context
    time_of_day: Optional[str] = None
    day_of_week: Optional[str] = None
    
    # Current context
    current_business_id: Optional[str] = None
    current_product_id: Optional[str] = None
    current_category_id: Optional[str] = None
    
    # Subscription context
    subscription_tier: str = "free"
    enabled_features: List[str] = Field(default_factory=list)
    
    class Config:
        use_enum_values = True


class ConsultationMessage(BaseModel):
    """Message in a consultation session"""
    id: UUID = Field(default_factory=uuid4)
    session_id: UUID
    role: str  # "user" or "assistant"
    content: str
    
    # Token tracking
    tokens_used: int = 0
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None


class ConsultationSession(BaseModel):
    """AI consultation session"""
    id: UUID = Field(default_factory=uuid4)
    user_id: str
    subscription_id: Optional[UUID] = None
    
    # Session info
    topic: str
    status: ConsultationStatus = ConsultationStatus.ACTIVE
    
    # Messages
    messages: List[ConsultationMessage] = Field(default_factory=list)
    message_count: int = 0
    
    # Token tracking
    total_tokens_used: int = 0
    total_cost: float = 0.0
    
    # Context
    context: Optional[Dict[str, Any]] = None
    genui_cache_key: Optional[str] = None
    
    # AI provider used
    provider: AIProviderType = AIProviderType.OPENAI
    model_used: Optional[str] = None
    
    # Timestamps
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    last_activity_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Session metadata
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        use_enum_values = True
    
    def add_message(self, message: ConsultationMessage) -> None:
        """Add a message to the session"""
        self.messages.append(message)
        self.message_count = len(self.messages)
        self.total_tokens_used += message.tokens_used
        self.last_activity_at = datetime.utcnow()


class BusinessRecommendation(BaseModel):
    """Business recommendation model"""
    id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    rating: Optional[float] = None
    review_count: Optional[int] = None
    distance_km: Optional[float] = None
    address: Optional[str] = None
    
    # Recommendation metadata
    score: float = 0.0
    reason: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    
    # Additional data
    metadata: Optional[Dict[str, Any]] = None


class ProductRecommendation(BaseModel):
    """Product recommendation model"""
    id: str
    name: str
    description: Optional[str] = None
    price: Optional[float] = None
    currency: str = "USD"
    image_url: Optional[str] = None
    category: Optional[str] = None
    business_id: Optional[str] = None
    business_name: Optional[str] = None
    
    # Recommendation metadata
    score: float = 0.0
    reason: Optional[str] = None
    similarity_score: Optional[float] = None
    
    # Additional data
    metadata: Optional[Dict[str, Any]] = None


class PersonalizedFeed(BaseModel):
    """Personalized feed model"""
    user_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Feed items
    businesses: List[BusinessRecommendation] = Field(default_factory=list)
    products: List[ProductRecommendation] = Field(default_factory=list)
    
    # Categories
    featured_categories: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Metadata
    total_items: int = 0
    feed_version: str = "1.0"
    
    def calculate_total(self) -> int:
        """Calculate total items in feed"""
        self.total_items = len(self.businesses) + len(self.products)
        return self.total_items


class AIQuotaInfo(BaseModel):
    """AI quota information for user"""
    user_id: str
    subscription_tier: str
    
    # Daily limits
    daily_limit: int
    daily_used: int
    daily_remaining: int
    
    # Monthly limits
    monthly_limit: int
    monthly_used: int
    monthly_remaining: int
    
    # Token usage
    tokens_used_today: int = 0
    tokens_used_this_month: int = 0
    
    # Features available
    available_providers: List[AIProviderType] = Field(default_factory=list)
    available_models: List[str] = Field(default_factory=list)
    max_context_length: int = 4096
    supports_streaming: bool = True
    supports_vision: bool = False
    
    # Premium features
    priority_processing: bool = False
    advanced_context: bool = False
    custom_models: bool = False
    
    # Reset times
    daily_reset_at: Optional[datetime] = None
    monthly_reset_at: Optional[datetime] = None
    
    class Config:
        use_enum_values = True
    
    @property
    def can_make_request(self) -> bool:
        """Check if user can make a request"""
        if self.daily_limit == -1 or self.monthly_limit == -1:
            return True
        return self.daily_remaining > 0 and self.monthly_remaining > 0
    
    @property
    def usage_percentage(self) -> float:
        """Calculate daily usage percentage"""
        if self.daily_limit == -1:
            return 0.0
        return (self.daily_used / self.daily_limit) * 100
