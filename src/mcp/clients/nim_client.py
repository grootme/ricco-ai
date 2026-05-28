"""
NVIDIA NIM API Client

Production-ready client for connecting to NVIDIA NIM APIs.
Supports authentication, retries, circuit breaker, and structured logging.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, TypeVar, Type
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import httpx
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class NIMEndpoint(Enum):
    """NVIDIA NIM API Endpoints"""
    # Warehouse endpoints
    EQUIPMENT_STATUS = "/warehouse/equipment/{asset_id}/status"
    EQUIPMENT_TELEMETRY = "/warehouse/equipment/{asset_id}/telemetry"
    EQUIPMENT_UTILIZATION = "/warehouse/equipment/{asset_id}/utilization"
    MAINTENANCE_REQUEST = "/warehouse/maintenance"
    TASK_CREATE = "/warehouse/tasks"
    PICK_PATH_OPTIMIZE = "/warehouse/pick-path/optimize"
    PERFORMANCE_METRICS = "/warehouse/metrics"
    INCIDENT_LOG = "/warehouse/incidents"
    SDS_RETRIEVE = "/warehouse/sds/{chemical_name}"
    FORECAST = "/warehouse/forecast/{sku}"
    REORDER_RECOMMENDATIONS = "/warehouse/reorder"
    DOCUMENT_UPLOAD = "/warehouse/documents"
    DOCUMENT_EXTRACT = "/warehouse/documents/{document_id}/extract"
    
    # Commerce endpoints
    CHECKOUT_CREATE = "/commerce/checkout"
    PROMOTION_APPLY = "/commerce/promotion/apply"
    RECOMMENDATIONS = "/commerce/recommendations"
    PRODUCTS_SEARCH = "/commerce/products/search"
    PAYMENT_PROCESS = "/commerce/payment"
    
    # Shopping endpoints
    PRODUCTS_SEARCH_TEXT = "/shopping/products/search"
    PRODUCTS_SEARCH_IMAGE = "/shopping/products/search/image"
    CART_ADD = "/shopping/cart/add"
    CART_GET = "/shopping/cart"
    
    # Genomics endpoints
    BWA_MEM_RUN = "/genomics/bwa-mem"
    DEEPVARIANT_RUN = "/genomics/deepvariant"
    VARIANT_EFFECT_PREDICT = "/genomics/variant-effect"
    GERMLINE_WES_RUN = "/genomics/germline-wes"
    
    # Voice endpoints
    AUDIO_TRANSCRIBE = "/voice/transcribe"
    SPEECH_SYNTHESIZE = "/voice/synthesize"
    PIPELINE_CREATE = "/voice/pipeline"
    CONVERSATION_START = "/voice/conversation"
    
    # Portfolio endpoints
    PORTFOLIO_OPTIMIZE = "/portfolio/optimize"
    EFFICIENT_FRONTIER = "/portfolio/frontier"
    BACKTEST = "/portfolio/backtest"
    SCENARIOS_GENERATE = "/portfolio/scenarios"
    
    # Streaming RAG endpoints
    INGESTION_START = "/streaming-rag/ingestion"
    RAG_QUERY = "/streaming-rag/query"
    SDR_PROCESS = "/streaming-rag/sdr"
    
    # Biomedical endpoints
    RESEARCH_PLAN_CREATE = "/biomedical/research-plan"
    MOLECULES_GENERATE = "/biomedical/molecules"
    DOCKING_PREDICT = "/biomedical/docking"
    LITERATURE_SEARCH = "/biomedical/literature"
    
    # Patient endpoints
    PATIENT_INTAKE_START = "/patient/intake"
    APPOINTMENT_SCHEDULE = "/patient/appointment"
    MEDICATION_INFO = "/patient/medication"
    VOICE_PROCESS = "/patient/voice"
    
    # Distillation endpoints
    FLYWHEEL_CREATE = "/distillation/flywheel"
    FINETUNING_LAUNCH = "/distillation/finetuning"
    EVALUATION_RUN = "/distillation/evaluation"
    NEWS_CLASSIFY = "/distillation/news/classify"


@dataclass
class NIMConfig:
    """Configuration for NVIDIA NIM client"""
    base_url: str = "https://api.nvidia.com/nim/v1"
    api_key: Optional[str] = None
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 60.0
    enable_cache: bool = True
    cache_ttl: int = 300  # 5 minutes
    
    # Model configurations
    default_model: str = "nvidia/llama-3.1-nemotron-70b"
    embedding_model: str = "nvidia/nv-embedqa-e5-v5"
    asr_model: str = "nvidia/parakeet-tdt-0.6b"
    tts_model: str = "nvidia/magpie-tts"


@dataclass
class CircuitBreakerState:
    """Circuit breaker state for fault tolerance"""
    failure_count: int = 0
    last_failure_time: Optional[datetime] = None
    state: str = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def should_allow_request(self, config: NIMConfig) -> bool:
        """Check if requests should be allowed"""
        if self.state == "CLOSED":
            return True
        if self.state == "OPEN":
            if self.last_failure_time:
                elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
                if elapsed >= config.circuit_breaker_timeout:
                    self.state = "HALF_OPEN"
                    return True
            return False
        # HALF_OPEN
        return True
    
    def record_success(self):
        """Record a successful request"""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def record_failure(self, config: NIMConfig):
        """Record a failed request"""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()
        if self.failure_count >= config.circuit_breaker_threshold:
            self.state = "OPEN"


class NIMError(Exception):
    """Base exception for NIM API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.details = details or {}


class NIMAuthenticationError(NIMError):
    """Authentication failed"""
    pass


class NIMRateLimitError(NIMError):
    """Rate limit exceeded"""
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class NIMServerError(NIMError):
    """Server-side error"""
    pass


class NIMValidationError(NIMError):
    """Validation error"""
    pass


# Input validation models
class EquipmentStatusRequest(BaseModel):
    """Request for equipment status"""
    asset_id: str = Field(..., min_length=1, max_length=50, description="Equipment asset ID")
    
    @field_validator('asset_id')
    @classmethod
    def validate_asset_id(cls, v: str) -> str:
        if not v.startswith(('ASSET-', 'EQ-', 'WH-')):
            raise ValueError('asset_id must start with ASSET-, EQ-, or WH-')
        return v


class TaskCreateRequest(BaseModel):
    """Request for creating a warehouse task"""
    task_type: str = Field(..., description="Type of task")
    location: str = Field(..., min_length=1, description="Warehouse location")
    priority: str = Field(default="medium", description="Task priority")
    assigned_to: Optional[str] = Field(default=None, description="Operator ID")
    deadline: Optional[str] = Field(default=None, description="Task deadline")
    
    @field_validator('task_type')
    @classmethod
    def validate_task_type(cls, v: str) -> str:
        valid_types = {'picking', 'packing', 'receiving', 'shipping', 'inventory', 'maintenance'}
        if v.lower() not in valid_types:
            raise ValueError(f'task_type must be one of: {valid_types}')
        return v.lower()
    
    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v: str) -> str:
        valid_priorities = {'low', 'medium', 'high', 'urgent', 'critical'}
        if v.lower() not in valid_priorities:
            raise ValueError(f'priority must be one of: {valid_priorities}')
        return v.lower()


class MaintenanceRequest(BaseModel):
    """Request for creating a maintenance request"""
    asset_id: str = Field(..., min_length=1)
    issue_type: str = Field(..., description="Type of issue")
    description: str = Field(..., min_length=10, max_length=1000)
    priority: str = Field(default="medium")
    scheduled_date: Optional[str] = Field(default=None)
    
    @field_validator('issue_type')
    @classmethod
    def validate_issue_type(cls, v: str) -> str:
        valid_types = {'mechanical', 'electrical', 'battery', 'software', 'structural', 'other'}
        if v.lower() not in valid_types:
            raise ValueError(f'issue_type must be one of: {valid_types}')
        return v.lower()


class NIMClient:
    """
    Production-ready NVIDIA NIM API Client
    
    Features:
    - Async HTTP client with connection pooling
    - Automatic retry with exponential backoff
    - Circuit breaker pattern for fault tolerance
    - Request/response caching
    - Structured logging
    - Input validation with Pydantic
    """
    
    def __init__(self, config: Optional[NIMConfig] = None):
        self.config = config or NIMConfig()
        self._client: Optional[httpx.AsyncClient] = None
        self._circuit_breaker = CircuitBreakerState()
        self._cache: Dict[str, tuple[Any, datetime]] = {}
        
    async def __aenter__(self) -> "NIMClient":
        """Async context manager entry"""
        await self._initialize_client()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def _initialize_client(self):
        """Initialize HTTP client"""
        if self._client is None:
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
            if self.config.api_key:
                headers["Authorization"] = f"Bearer {self.config.api_key}"
            
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                headers=headers,
                timeout=self.config.timeout,
                follow_redirects=True,
            )
            logger.info(
                "NIM client initialized",
                extra={
                    "base_url": self.config.base_url,
                    "timeout": self.config.timeout,
                    "circuit_breaker_threshold": self.config.circuit_breaker_threshold,
                }
            )
    
    async def close(self):
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("NIM client closed")
    
    def _get_cache_key(self, endpoint: str, params: Optional[Dict] = None) -> str:
        """Generate cache key"""
        import hashlib
        key_data = f"{endpoint}:{sorted(params.items()) if params else ''}"
        return hashlib.sha256(key_data.encode()).hexdigest()
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get cached response"""
        if not self.config.enable_cache:
            return None
        if key in self._cache:
            data, timestamp = self._cache[key]
            if datetime.utcnow() - timestamp < timedelta(seconds=self.config.cache_ttl):
                logger.debug(f"Cache hit for key: {key[:16]}...")
                return data
            else:
                del self._cache[key]
        return None
    
    def _set_cache(self, key: str, data: Any):
        """Set cache entry"""
        if self.config.enable_cache:
            self._cache[key] = (data, datetime.utcnow())
    
    async def _request_with_retry(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Dict] = None,
        response_model: Optional[Type[T]] = None,
    ) -> Dict[str, Any]:
        """Make request with retry logic"""
        if not self._circuit_breaker.should_allow_request(self.config):
            raise NIMServerError(
                "Circuit breaker is OPEN - service unavailable",
                details={"state": self._circuit_breaker.state}
            )
        
        # Check cache for GET requests
        if method == "GET":
            cache_key = self._get_cache_key(endpoint, params)
            cached = self._get_from_cache(cache_key)
            if cached:
                return cached
        
        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                response = await self._client.request(
                    method=method,
                    url=endpoint,
                    params=params,
                    json=json_data,
                )
                
                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After", "60")
                    raise NIMRateLimitError(
                        "Rate limit exceeded",
                        retry_after=int(retry_after)
                    )
                
                # Handle authentication errors
                if response.status_code == 401:
                    raise NIMAuthenticationError(
                        "Authentication failed - check API key"
                    )
                
                # Handle validation errors
                if response.status_code == 422:
                    details = response.json()
                    raise NIMValidationError(
                        f"Validation error: {details}",
                        status_code=422,
                        details=details
                    )
                
                # Handle server errors
                if response.status_code >= 500:
                    raise NIMServerError(
                        f"Server error: {response.status_code}",
                        status_code=response.status_code
                    )
                
                # Raise for other errors
                response.raise_for_status()
                
                # Parse response
                data = response.json()
                
                # Cache successful GET requests
                if method == "GET":
                    self._set_cache(cache_key, data)
                
                self._circuit_breaker.record_success()
                
                logger.info(
                    "NIM API request successful",
                    extra={
                        "endpoint": endpoint,
                        "method": method,
                        "status_code": response.status_code,
                        "attempt": attempt + 1,
                    }
                )
                
                if response_model:
                    return response_model(**data).model_dump()
                return data
                
            except (NIMRateLimitError, NIMAuthenticationError, NIMValidationError):
                # Don't retry these errors
                raise
            except Exception as e:
                last_error = e
                logger.warning(
                    f"NIM API request failed (attempt {attempt + 1}/{self.config.max_retries})",
                    extra={
                        "endpoint": endpoint,
                        "method": method,
                        "error": str(e),
                    }
                )
                
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
        
        # All retries failed
        self._circuit_breaker.record_failure(self.config)
        raise NIMServerError(
            f"Request failed after {self.config.max_retries} attempts: {last_error}",
            details={"last_error": str(last_error)}
        )
    
    # ==================== WAREHOUSE API METHODS ====================
    
    async def get_equipment_status(self, asset_id: str) -> Dict[str, Any]:
        """Get real-time equipment status"""
        # Validate input
        request = EquipmentStatusRequest(asset_id=asset_id)
        
        endpoint = NIMEndpoint.EQUIPMENT_STATUS.value.format(asset_id=request.asset_id)
        return await self._request_with_retry("GET", endpoint)
    
    async def get_equipment_telemetry(
        self,
        asset_id: str,
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get equipment telemetry data"""
        endpoint = NIMEndpoint.EQUIPMENT_TELEMETRY.value.format(asset_id=asset_id)
        return await self._request_with_retry(
            "GET",
            endpoint,
            params={"metrics": ",".join(metrics)} if metrics else None
        )
    
    async def assign_equipment(
        self,
        asset_id: str,
        operator_id: str,
        task_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Assign equipment to an operator"""
        endpoint = NIMEndpoint.EQUIPMENT_STATUS.value.format(asset_id=asset_id)
        return await self._request_with_retry(
            "PATCH",
            endpoint,
            json_data={
                "operator_id": operator_id,
                "task_id": task_id,
                "assigned_at": datetime.utcnow().isoformat(),
            }
        )
    
    async def create_maintenance_request(
        self,
        asset_id: str,
        issue_type: str,
        description: str,
        priority: str = "medium",
        scheduled_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create maintenance request"""
        # Validate input
        request = MaintenanceRequest(
            asset_id=asset_id,
            issue_type=issue_type,
            description=description,
            priority=priority,
            scheduled_date=scheduled_date
        )
        
        return await self._request_with_retry(
            "POST",
            NIMEndpoint.MAINTENANCE_REQUEST.value,
            json_data=request.model_dump()
        )
    
    async def create_task(
        self,
        task_type: str,
        location: str,
        priority: str = "medium",
        assigned_to: Optional[str] = None,
        deadline: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create warehouse task"""
        request = TaskCreateRequest(
            task_type=task_type,
            location=location,
            priority=priority,
            assigned_to=assigned_to,
            deadline=deadline
        )
        
        return await self._request_with_retry(
            "POST",
            NIMEndpoint.TASK_CREATE.value,
            json_data=request.model_dump()
        )
    
    async def optimize_pick_path(
        self,
        order_items: List[str],
        start_location: str = "dock",
        end_location: str = "packaging"
    ) -> Dict[str, Any]:
        """Optimize pick path for order"""
        return await self._request_with_retry(
            "POST",
            NIMEndpoint.PICK_PATH_OPTIMIZE.value,
            json_data={
                "order_items": order_items,
                "start_location": start_location,
                "end_location": end_location,
            }
        )
    
    async def get_performance_metrics(
        self,
        department: str = "all",
        period: str = "day"
    ) -> Dict[str, Any]:
        """Get KPI metrics"""
        return await self._request_with_retry(
            "GET",
            NIMEndpoint.PERFORMANCE_METRICS.value,
            params={"department": department, "period": period}
        )
    
    async def log_incident(
        self,
        incident_type: str,
        location: str,
        description: str,
        severity: str = "low",
        involved_parties: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Log safety incident"""
        return await self._request_with_retry(
            "POST",
            NIMEndpoint.INCIDENT_LOG.value,
            json_data={
                "incident_type": incident_type,
                "location": location,
                "description": description,
                "severity": severity,
                "involved_parties": involved_parties,
                "reported_at": datetime.utcnow().isoformat(),
            }
        )
    
    async def retrieve_sds(self, chemical_name: str) -> Dict[str, Any]:
        """Retrieve Safety Data Sheet"""
        endpoint = NIMEndpoint.SDS_RETRIEVE.value.format(chemical_name=chemical_name)
        return await self._request_with_retry("GET", endpoint)
    
    async def get_forecast(
        self,
        sku: str,
        forecast_days: int = 30,
        model: str = "ensemble"
    ) -> Dict[str, Any]:
        """Get demand forecast"""
        endpoint = NIMEndpoint.FORECAST.value.format(sku=sku)
        return await self._request_with_retry(
            "GET",
            endpoint,
            params={"forecast_days": forecast_days, "model": model}
        )
    
    async def get_reorder_recommendations(
        self,
        category: str = "all"
    ) -> List[Dict[str, Any]]:
        """Get reorder recommendations"""
        return await self._request_with_retry(
            "GET",
            NIMEndpoint.REORDER_RECOMMENDATIONS.value,
            params={"category": category}
        )
    
    # ==================== DOCUMENT PROCESSING ====================
    
    async def upload_document(
        self,
        file_path: str,
        document_type: str = "general",
        extract_fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Upload document for OCR processing"""
        return await self._request_with_retry(
            "POST",
            NIMEndpoint.DOCUMENT_UPLOAD.value,
            json_data={
                "file_path": file_path,
                "document_type": document_type,
                "extract_fields": extract_fields,
            }
        )
    
    async def get_extraction_results(self, document_id: str) -> Dict[str, Any]:
        """Get document extraction results"""
        endpoint = NIMEndpoint.DOCUMENT_EXTRACT.value.format(document_id=document_id)
        return await self._request_with_retry("GET", endpoint)
    
    # ==================== COMMERCE API METHODS ====================
    
    async def create_checkout_session(
        self,
        cart_items: List[Dict],
        user_id: str,
        currency: str = "USD"
    ) -> Dict[str, Any]:
        """Create checkout session"""
        return await self._request_with_retry(
            "POST",
            NIMEndpoint.CHECKOUT_CREATE.value,
            json_data={
                "cart_items": cart_items,
                "user_id": user_id,
                "currency": currency,
            }
        )
    
    async def apply_promotion(
        self,
        session_id: str,
        promo_code: str
    ) -> Dict[str, Any]:
        """Apply promotion code"""
        return await self._request_with_retry(
            "POST",
            NIMEndpoint.PROMOTION_APPLY.value,
            json_data={
                "session_id": session_id,
                "promo_code": promo_code,
            }
        )
    
    async def get_recommendations(
        self,
        user_id: str,
        context: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get personalized recommendations"""
        return await self._request_with_retry(
            "GET",
            NIMEndpoint.RECOMMENDATIONS.value,
            params={
                "user_id": user_id,
                "context": context,
                "limit": limit,
            }
        )
    
    async def search_products(
        self,
        query: str,
        filters: Optional[Dict] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search products"""
        return await self._request_with_retry(
            "GET",
            NIMEndpoint.PRODUCTS_SEARCH.value,
            params={
                "query": query,
                "filters": filters,
                "limit": limit,
            }
        )
    
    async def process_payment(
        self,
        session_id: str,
        payment_method: str
    ) -> Dict[str, Any]:
        """Process payment"""
        return await self._request_with_retry(
            "POST",
            NIMEndpoint.PAYMENT_PROCESS.value,
            json_data={
                "session_id": session_id,
                "payment_method": payment_method,
            }
        )
    
    # ==================== SHOPPING API METHODS ====================
    
    async def search_products_text(
        self,
        query: str,
        filters: Optional[Dict] = None,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Search products by text"""
        return await self._request_with_retry(
            "GET",
            NIMEndpoint.PRODUCTS_SEARCH_TEXT.value,
            params={"query": query, "filters": filters, "limit": limit}
        )
    
    async def search_products_image(
        self,
        image_url: str,
        category_hint: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search products by image"""
        return await self._request_with_retry(
            "POST",
            NIMEndpoint.PRODUCTS_SEARCH_IMAGE.value,
            json_data={"image_url": image_url, "category_hint": category_hint}
        )
    
    async def add_to_cart(
        self,
        product_id: str,
        quantity: int = 1
    ) -> Dict[str, Any]:
        """Add product to cart"""
        return await self._request_with_retry(
            "POST",
            NIMEndpoint.CART_ADD.value,
            json_data={"product_id": product_id, "quantity": quantity}
        )
    
    async def get_cart(self) -> Dict[str, Any]:
        """Get shopping cart"""
        return await self._request_with_retry("GET", NIMEndpoint.CART_GET.value)
    
    # ==================== GENOMICS API METHODS ====================
    
    async def run_bwa_mem(
        self,
        fastq1: str,
        reference: str,
        fastq2: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run GPU-accelerated BWA-MEM alignment"""
        return await self._request_with_retry(
            "POST",
            NIMEndpoint.BWA_MEM_RUN.value,
            json_data={
                "fastq1": fastq1,
                "reference": reference,
                "fastq2": fastq2,
            }
        )
    
    async def run_deepvariant(
        self,
        bam_file: str,
        reference: str,
        model_type: str = "WGS"
    ) -> Dict[str, Any]:
        """Run DeepVariant variant calling"""
        return await self._request_with_retry(
            "POST",
            NIMEndpoint.DEEPVARIANT_RUN.value,
            json_data={
                "bam_file": bam_file,
                "reference": reference,
                "model_type": model_type,
            }
        )
    
    async def predict_variant_effect(
        self,
        vcf_file: str,
        gene_annotations: str
    ) -> Dict[str, Any]:
        """Predict variant functional impact"""
        return await self._request_with_retry(
            "POST",
            NIMEndpoint.VARIANT_EFFECT_PREDICT.value,
            json_data={
                "vcf_file": vcf_file,
                "gene_annotations": gene_annotations,
            }
        )
    
    # ==================== VOICE API METHODS ====================
    
    async def transcribe_audio(
        self,
        audio_path: str,
        language: str = "en-US"
    ) -> Dict[str, Any]:
        """Transcribe audio with Parakeet ASR"""
        return await self._request_with_retry(
            "POST",
            NIMEndpoint.AUDIO_TRANSCRIBE.value,
            json_data={"audio_path": audio_path, "language": language}
        )
    
    async def synthesize_speech(
        self,
        text: str,
        voice: str = "default",
        language: str = "en-US"
    ) -> Dict[str, Any]:
        """Synthesize speech with Magpie TTS"""
        return await self._request_with_retry(
            "POST",
            NIMEndpoint.SPEECH_SYNTHESIZE.value,
            json_data={"text": text, "voice": voice, "language": language}
        )
    
    async def create_voice_pipeline(
        self,
        asr_model: Optional[str] = None,
        llm_model: Optional[str] = None,
        tts_model: Optional[str] = None,
        enable_interruption: bool = True
    ) -> Dict[str, Any]:
        """Create voice agent pipeline"""
        return await self._request_with_retry(
            "POST",
            NIMEndpoint.PIPELINE_CREATE.value,
            json_data={
                "asr_model": asr_model or self.config.asr_model,
                "llm_model": llm_model or self.config.default_model,
                "tts_model": tts_model or self.config.tts_model,
                "enable_interruption": enable_interruption,
            }
        )
    
    # ==================== PORTFOLIO API METHODS ====================
    
    async def optimize_mean_cvar(
        self,
        expected_returns: List[float],
        covariance_matrix: List[List[float]],
        alpha: float = 0.05
    ) -> Dict[str, Any]:
        """Mean-CVaR portfolio optimization"""
        return await self._request_with_retry(
            "POST",
            NIMEndpoint.PORTFOLIO_OPTIMIZE.value,
            json_data={
                "expected_returns": expected_returns,
                "covariance_matrix": covariance_matrix,
                "alpha": alpha,
                "method": "mean_cvar",
            }
        )
    
    async def compute_efficient_frontier(
        self,
        expected_returns: List[float],
        covariance_matrix: List[List[float]],
        n_points: int = 100
    ) -> Dict[str, Any]:
        """Compute efficient frontier"""
        return await self._request_with_retry(
            "POST",
            NIMEndpoint.EFFICIENT_FRONTIER.value,
            json_data={
                "expected_returns": expected_returns,
                "covariance_matrix": covariance_matrix,
                "n_points": n_points,
            }
        )
    
    async def backtest_strategy(
        self,
        strategy: Dict[str, Any],
        start_date: str,
        end_date: str
    ) -> Dict[str, Any]:
        """Backtest trading strategy"""
        return await self._request_with_retry(
            "POST",
            NIMEndpoint.BACKTEST.value,
            json_data={
                "strategy": strategy,
                "start_date": start_date,
                "end_date": end_date,
            }
        )
    
    # ==================== BIOMEDICAL API METHODS ====================
    
    async def create_research_plan(
        self,
        topic: str,
        enable_virtual_screening: bool = True
    ) -> Dict[str, Any]:
        """Create structured research plan"""
        return await self._request_with_retry(
            "POST",
            NIMEndpoint.RESEARCH_PLAN_CREATE.value,
            json_data={
                "topic": topic,
                "enable_virtual_screening": enable_virtual_screening,
            }
        )
    
    async def generate_molecules(
        self,
        seed_smiles: str,
        target_properties: Optional[Dict] = None,
        num_molecules: int = 100
    ) -> Dict[str, Any]:
        """Generate molecules with MolMIM"""
        return await self._request_with_retry(
            "POST",
            NIMEndpoint.MOLECULES_GENERATE.value,
            json_data={
                "seed_smiles": seed_smiles,
                "target_properties": target_properties,
                "num_molecules": num_molecules,
            }
        )
    
    async def predict_docking(
        self,
        protein_pdb: str,
        molecule_smiles: str
    ) -> Dict[str, Any]:
        """Predict protein-ligand docking"""
        return await self._request_with_retry(
            "POST",
            NIMEndpoint.DOCKING_PREDICT.value,
            json_data={
                "protein_pdb": protein_pdb,
                "molecule_smiles": molecule_smiles,
            }
        )
    
    async def search_literature(
        self,
        query: str,
        sources: Optional[List[str]] = None,
        max_results: int = 50
    ) -> Dict[str, Any]:
        """Search biomedical literature"""
        return await self._request_with_retry(
            "GET",
            NIMEndpoint.LITERATURE_SEARCH.value,
            params={
                "query": query,
                "sources": ",".join(sources) if sources else None,
                "max_results": max_results,
            }
        )
    
    # ==================== PATIENT API METHODS ====================
    
    async def start_patient_intake(
        self,
        session_type: str = "new_patient",
        language: str = "en-US"
    ) -> Dict[str, Any]:
        """Initialize patient intake session"""
        return await self._request_with_retry(
            "POST",
            NIMEndpoint.PATIENT_INTAKE_START.value,
            json_data={
                "session_type": session_type,
                "language": language,
                "initiated_at": datetime.utcnow().isoformat(),
            }
        )
    
    async def schedule_appointment(
        self,
        patient_id: str,
        provider_id: str,
        date: str,
        time: str
    ) -> Dict[str, Any]:
        """Schedule medical appointment"""
        return await self._request_with_retry(
            "POST",
            NIMEndpoint.APPOINTMENT_SCHEDULE.value,
            json_data={
                "patient_id": patient_id,
                "provider_id": provider_id,
                "date": date,
                "time": time,
            }
        )
    
    async def get_medication_info(
        self,
        medication_name: str,
        include_interactions: bool = True
    ) -> Dict[str, Any]:
        """Get medication information"""
        return await self._request_with_retry(
            "GET",
            NIMEndpoint.MEDICATION_INFO.value,
            params={
                "medication_name": medication_name,
                "include_interactions": include_interactions,
            }
        )
    
    # ==================== DISTILLATION API METHODS ====================
    
    async def create_flywheel_run(
        self,
        dataset_id: str,
        student_model: str,
        teacher_model: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create Data Flywheel experiment"""
        return await self._request_with_retry(
            "POST",
            NIMEndpoint.FLYWHEEL_CREATE.value,
            json_data={
                "dataset_id": dataset_id,
                "student_model": student_model,
                "teacher_model": teacher_model or self.config.default_model,
            }
        )
    
    async def launch_finetuning(
        self,
        dataset_id: str,
        model: str,
        method: str = "lora"
    ) -> Dict[str, Any]:
        """Launch LoRA fine-tuning job"""
        return await self._request_with_retry(
            "POST",
            NIMEndpoint.FINETUNING_LAUNCH.value,
            json_data={
                "dataset_id": dataset_id,
                "model": model,
                "method": method,
            }
        )
    
    async def run_evaluation(
        self,
        model_id: str,
        test_dataset: str,
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Run model evaluation"""
        return await self._request_with_retry(
            "POST",
            NIMEndpoint.EVALUATION_RUN.value,
            json_data={
                "model_id": model_id,
                "test_dataset": test_dataset,
                "metrics": metrics or ["accuracy", "f1", "precision", "recall"],
            }
        )
    
    async def classify_financial_news(
        self,
        headline: str,
        model_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Classify financial news headline"""
        return await self._request_with_retry(
            "POST",
            NIMEndpoint.NEWS_CLASSIFY.value,
            json_data={
                "headline": headline,
                "model_id": model_id or self.config.default_model,
            }
        )
    
    # ==================== HEALTH CHECK ====================
    
    async def health_check(self) -> Dict[str, Any]:
        """Check API health status"""
        try:
            response = await self._client.get("/health")
            return {
                "status": "healthy",
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "circuit_breaker_state": self._circuit_breaker.state,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "circuit_breaker_state": self._circuit_breaker.state,
            }


# Singleton instance for convenience
_nim_client: Optional[NIMClient] = None


def get_nim_client(config: Optional[NIMConfig] = None) -> NIMClient:
    """Get or create NIM client singleton"""
    global _nim_client
    if _nim_client is None:
        _nim_client = NIMClient(config)
    return _nim_client


async def close_nim_client():
    """Close NIM client singleton"""
    global _nim_client
    if _nim_client:
        await _nim_client.close()
        _nim_client = None
