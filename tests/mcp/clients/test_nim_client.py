"""
Tests for NVIDIA NIM Client

Comprehensive tests for the NIM API client including:
- Client initialization
- Request/response handling
- Circuit breaker functionality
- Error handling
- Caching
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from src.mcp.clients.nim_client import (
    NIMClient,
    NIMConfig,
    NIMEndpoint,
    NIMError,
    NIMAuthenticationError,
    NIMRateLimitError,
    NIMServerError,
    NIMValidationError,
    CircuitBreakerState,
    EquipmentStatusRequest,
    TaskCreateRequest,
    MaintenanceRequest,
)


class TestNIMConfig:
    """Tests for NIMConfig"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = NIMConfig()
        assert config.base_url == "https://api.nvidia.com/nim/v1"
        assert config.timeout == 30.0
        assert config.max_retries == 3
        assert config.circuit_breaker_threshold == 5
        assert config.enable_cache is True
    
    def test_custom_config(self):
        """Test custom configuration values"""
        config = NIMConfig(
            base_url="https://custom.api.com",
            api_key="test-key",
            timeout=60.0,
            max_retries=5
        )
        assert config.base_url == "https://custom.api.com"
        assert config.api_key == "test-key"
        assert config.timeout == 60.0
        assert config.max_retries == 5


class TestCircuitBreakerState:
    """Tests for CircuitBreakerState"""
    
    def test_initial_state(self):
        """Test initial circuit breaker state"""
        cb = CircuitBreakerState()
        assert cb.state == "CLOSED"
        assert cb.failure_count == 0
    
    def test_record_success(self):
        """Test recording success"""
        cb = CircuitBreakerState()
        cb.failure_count = 3
        cb.state = "OPEN"
        
        cb.record_success()
        
        assert cb.failure_count == 0
        assert cb.state == "CLOSED"
    
    def test_record_failure(self):
        """Test recording failure"""
        config = NIMConfig(circuit_breaker_threshold=3)
        cb = CircuitBreakerState()
        
        cb.record_failure(config)
        assert cb.failure_count == 1
        assert cb.state == "CLOSED"
        
        cb.record_failure(config)
        cb.record_failure(config)
        assert cb.failure_count == 3
        assert cb.state == "OPEN"
    
    def test_should_allow_request_closed(self):
        """Test request allowed when closed"""
        config = NIMConfig()
        cb = CircuitBreakerState()
        cb.state = "CLOSED"
        
        assert cb.should_allow_request(config) is True
    
    def test_should_allow_request_open(self):
        """Test request blocked when open"""
        config = NIMConfig(circuit_breaker_timeout=60.0)
        cb = CircuitBreakerState()
        cb.state = "OPEN"
        cb.last_failure_time = datetime.utcnow()
        
        assert cb.should_allow_request(config) is False
    
    def test_should_allow_request_half_open(self):
        """Test request allowed when half-open after timeout"""
        config = NIMConfig(circuit_breaker_timeout=0.1)
        cb = CircuitBreakerState()
        cb.state = "OPEN"
        cb.last_failure_time = datetime.utcnow() - timedelta(seconds=1)
        
        assert cb.should_allow_request(config) is True
        assert cb.state == "HALF_OPEN"


class TestInputValidation:
    """Tests for input validation models"""
    
    def test_equipment_status_request_valid(self):
        """Test valid equipment status request"""
        request = EquipmentStatusRequest(asset_id="ASSET-001")
        assert request.asset_id == "ASSET-001"
    
    def test_equipment_status_request_invalid(self):
        """Test invalid equipment status request"""
        with pytest.raises(ValueError, match="must start with"):
            EquipmentStatusRequest(asset_id="invalid-id")
    
    def test_task_create_request_valid(self):
        """Test valid task create request"""
        request = TaskCreateRequest(
            task_type="picking",
            location="Zone A",
            priority="high"
        )
        assert request.task_type == "picking"
        assert request.priority == "high"
    
    def test_task_create_request_invalid_type(self):
        """Test invalid task type"""
        with pytest.raises(ValueError, match="task_type must be one of"):
            TaskCreateRequest(task_type="invalid", location="Zone A")
    
    def test_task_create_request_invalid_priority(self):
        """Test invalid priority"""
        with pytest.raises(ValueError, match="priority must be one of"):
            TaskCreateRequest(task_type="picking", location="Zone A", priority="super-urgent")
    
    def test_maintenance_request_valid(self):
        """Test valid maintenance request"""
        request = MaintenanceRequest(
            asset_id="ASSET-001",
            issue_type="mechanical",
            description="Equipment needs repair"
        )
        assert request.issue_type == "mechanical"
    
    def test_maintenance_request_description_too_short(self):
        """Test description too short"""
        with pytest.raises(ValueError):
            MaintenanceRequest(
                asset_id="ASSET-001",
                issue_type="mechanical",
                description="short"
            )


class TestNIMClient:
    """Tests for NIMClient"""
    
    @pytest.fixture
    def client(self):
        """Create a NIM client for testing"""
        return NIMClient(NIMConfig(api_key="test-api-key"))
    
    def test_client_initialization(self, client):
        """Test client initialization"""
        assert client.config.api_key == "test-api-key"
        assert client._client is None
        assert client._circuit_breaker.state == "CLOSED"
    
    @pytest.mark.asyncio
    async def test_client_context_manager(self, client):
        """Test async context manager"""
        async with client as c:
            assert c._client is not None
        
        assert client._client is None
    
    def test_get_cache_key(self, client):
        """Test cache key generation"""
        key1 = client._get_cache_key("/test/endpoint", {"param": "value"})
        key2 = client._get_cache_key("/test/endpoint", {"param": "value"})
        key3 = client._get_cache_key("/test/endpoint", {"param": "other"})
        
        assert key1 == key2
        assert key1 != key3
    
    def test_cache_operations(self, client):
        """Test cache set and get"""
        client.config.enable_cache = True
        
        key = "test-key"
        data = {"result": "test"}
        
        client._set_cache(key, data)
        cached = client._get_from_cache(key)
        
        assert cached == data
    
    def test_cache_disabled(self, client):
        """Test cache when disabled"""
        client.config.enable_cache = False
        
        key = "test-key"
        data = {"result": "test"}
        
        client._set_cache(key, data)
        cached = client._get_from_cache(key)
        
        assert cached is None
    
    def test_cache_expiry(self, client):
        """Test cache expiry"""
        client.config.enable_cache = True
        client.config.cache_ttl = 0
        
        key = "test-key"
        data = {"result": "test"}
        
        client._set_cache(key, data)
        # Wait for cache to expire
        import time
        time.sleep(0.1)
        cached = client._get_from_cache(key)
        
        assert cached is None


class TestNIMErrors:
    """Tests for NIM error classes"""
    
    def test_nim_error(self):
        """Test base NIM error"""
        error = NIMError("Test error", status_code=500, details={"key": "value"})
        assert str(error) == "Test error"
        assert error.status_code == 500
        assert error.details == {"key": "value"}
    
    def test_authentication_error(self):
        """Test authentication error"""
        error = NIMAuthenticationError("Invalid API key")
        assert error.status_code == 401
    
    def test_rate_limit_error(self):
        """Test rate limit error"""
        error = NIMRateLimitError("Rate limit exceeded", retry_after=60)
        assert error.status_code == 429
        assert error.retry_after == 60
    
    def test_server_error(self):
        """Test server error"""
        error = NIMServerError("Internal server error", status_code=503)
        assert error.status_code == 503
    
    def test_validation_error(self):
        """Test validation error"""
        error = NIMValidationError("Invalid input", details={"field": "required"})
        assert error.status_code == 422


class TestNIMEndpoints:
    """Tests for NIM endpoint enum"""
    
    def test_warehouse_endpoints(self):
        """Test warehouse endpoints"""
        assert "/warehouse/equipment/{asset_id}/status" in NIMEndpoint.EQUIPMENT_STATUS.value
        assert "/warehouse/maintenance" in NIMEndpoint.MAINTENANCE_REQUEST.value
    
    def test_commerce_endpoints(self):
        """Test commerce endpoints"""
        assert "/commerce/checkout" in NIMEndpoint.CHECKOUT_CREATE.value
        assert "/commerce/products/search" in NIMEndpoint.PRODUCTS_SEARCH.value
    
    def test_genomics_endpoints(self):
        """Test genomics endpoints"""
        assert "/genomics/bwa-mem" in NIMEndpoint.BWA_MEM_RUN.value
        assert "/genomics/deepvariant" in NIMEndpoint.DEEPVARIANT_RUN.value
    
    def test_voice_endpoints(self):
        """Test voice endpoints"""
        assert "/voice/transcribe" in NIMEndpoint.AUDIO_TRANSCRIBE.value
        assert "/voice/synthesize" in NIMEndpoint.SPEECH_SYNTHESIZE.value


class TestClientMethods:
    """Tests for NIMClient API methods"""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mocked NIM client"""
        client = NIMClient(NIMConfig(api_key="test-key"))
        client._client = AsyncMock(spec=httpx.AsyncClient)
        return client
    
    @pytest.mark.asyncio
    async def test_get_equipment_status(self, mock_client):
        """Test get equipment status"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "asset_id": "ASSET-001",
            "status": "operational",
            "location": "Zone A"
        }
        mock_response.raise_for_status = MagicMock()
        mock_client._client.request = AsyncMock(return_value=mock_response)
        
        await mock_client._initialize_client()
        result = await mock_client.get_equipment_status("ASSET-001")
        
        assert result["asset_id"] == "ASSET-001"
    
    @pytest.mark.asyncio
    async def test_create_task(self, mock_client):
        """Test create task"""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "success": True,
            "task_id": "TASK-001",
            "task_type": "picking"
        }
        mock_response.raise_for_status = MagicMock()
        mock_client._client.request = AsyncMock(return_value=mock_response)
        
        await mock_client._initialize_client()
        result = await mock_client.create_task(
            task_type="picking",
            location="Zone A"
        )
        
        assert result["success"] is True
    
    @pytest.mark.asyncio
    async def test_rate_limit_handling(self, mock_client):
        """Test rate limit error handling"""
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "60"}
        mock_client._client.request = AsyncMock(return_value=mock_response)
        
        await mock_client._initialize_client()
        
        with pytest.raises(NIMRateLimitError) as exc_info:
            await mock_client._request_with_retry("GET", "/test")
        
        assert exc_info.value.retry_after == 60
    
    @pytest.mark.asyncio
    async def test_authentication_error_handling(self, mock_client):
        """Test authentication error handling"""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_client._client.request = AsyncMock(return_value=mock_response)
        
        await mock_client._initialize_client()
        
        with pytest.raises(NIMAuthenticationError):
            await mock_client._request_with_retry("GET", "/test")


class TestRetryLogic:
    """Tests for retry logic"""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mocked NIM client"""
        client = NIMClient(NIMConfig(api_key="test-key", max_retries=3, retry_delay=0.1))
        client._client = AsyncMock(spec=httpx.AsyncClient)
        return client
    
    @pytest.mark.asyncio
    async def test_retry_on_server_error(self, mock_client):
        """Test retry on server error"""
        mock_response_fail = MagicMock()
        mock_response_fail.status_code = 500
        mock_response_fail.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server error", request=MagicMock(), response=mock_response_fail
        )
        
        mock_response_success = MagicMock()
        mock_response_success.status_code = 200
        mock_response_success.json.return_value = {"success": True}
        mock_response_success.raise_for_status = MagicMock()
        
        mock_client._client.request = AsyncMock(
            side_effect=[
                mock_response_fail,
                mock_response_fail,
                mock_response_success
            ]
        )
        
        await mock_client._initialize_client()
        result = await mock_client._request_with_retry("GET", "/test")
        
        assert result["success"] is True
        assert mock_client._client.request.call_count == 3
    
    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, mock_client):
        """Test max retries exceeded"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server error", request=MagicMock(), response=mock_response
        )
        mock_client._client.request = AsyncMock(return_value=mock_response)
        
        await mock_client._initialize_client()
        
        with pytest.raises(NIMServerError):
            await mock_client._request_with_retry("GET", "/test")
        
        assert mock_client._circuit_breaker.state == "OPEN"


class TestHealthCheck:
    """Tests for health check functionality"""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mocked NIM client"""
        client = NIMClient(NIMConfig(api_key="test-key"))
        client._client = AsyncMock(spec=httpx.AsyncClient)
        return client
    
    @pytest.mark.asyncio
    async def test_health_check_healthy(self, mock_client):
        """Test health check when healthy"""
        mock_response = MagicMock()
        mock_response.elapsed = timedelta(milliseconds=50)
        mock_client._client.get = AsyncMock(return_value=mock_response)
        
        await mock_client._initialize_client()
        result = await mock_client.health_check()
        
        assert result["status"] == "healthy"
        assert "response_time_ms" in result
    
    @pytest.mark.asyncio
    async def test_health_check_unhealthy(self, mock_client):
        """Test health check when unhealthy"""
        mock_client._client.get = AsyncMock(side_effect=Exception("Connection refused"))
        
        await mock_client._initialize_client()
        result = await mock_client.health_check()
        
        assert result["status"] == "unhealthy"
        assert "error" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
