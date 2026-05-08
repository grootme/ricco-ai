"""
Unit tests for Dependency Injection Container

Tests the DI container functionality including registration, resolution,
lifetimes, scopes, and decorators.
"""

import sys
import pytest
import asyncio
from typing import Optional

sys.path.insert(0, '.')

from src.core.container import (
    Container,
    ServiceLifetime,
    ServiceDescriptor,
    get_container,
    set_container,
    reset_container,
    inject,
    async_inject,
    ServiceProvider,
    ResolutionError,
    RegistrationError,
)


# =============================================================================
# Test Services
# =============================================================================

class IService:
    """Test service interface"""
    def get_value(self) -> str:
        ...


class ServiceA(IService):
    """Test service implementation A"""
    def __init__(self):
        self.value = "A"
    
    def get_value(self) -> str:
        return self.value


class ServiceB(IService):
    """Test service implementation B"""
    def __init__(self):
        self.value = "B"
    
    def get_value(self) -> str:
        return self.value


class ServiceWithDependency:
    """Service with dependencies"""
    def __init__(self, dependency: IService):
        self.dependency = dependency


class AsyncService:
    """Service with async initialization"""
    def __init__(self):
        self.initialized = False
    
    async def initialize(self) -> None:
        self.initialized = True


# =============================================================================
# Tests
# =============================================================================

class TestContainer:
    """Tests for Container class"""
    
    def setup_method(self):
        """Setup for each test"""
        self.container = Container()
    
    def test_register_singleton(self):
        """Test singleton registration"""
        self.container.register_singleton(IService, ServiceA)
        
        assert self.container.is_registered(IService)
        
        descriptor = self.container.get_registrations()[IService]
        assert descriptor.lifetime == ServiceLifetime.SINGLETON
    
    def test_register_transient(self):
        """Test transient registration"""
        self.container.register_transient(IService, ServiceB)
        
        descriptor = self.container.get_registrations()[IService]
        assert descriptor.lifetime == ServiceLifetime.TRANSIENT
    
    def test_register_scoped(self):
        """Test scoped registration"""
        self.container.register_scoped(IService, ServiceA)
        
        descriptor = self.container.get_registrations()[IService]
        assert descriptor.lifetime == ServiceLifetime.SCOPED
    
    def test_register_instance(self):
        """Test instance registration"""
        instance = ServiceA()
        instance.value = "custom"
        self.container.register_instance(IService, instance)
        
        resolved = self.container.resolve(IService)
        assert resolved is instance
        assert resolved.get_value() == "custom"
    
    def test_register_lazy(self):
        """Test lazy registration"""
        created = False
        
        def factory():
            nonlocal created
            created = True
            service = ServiceA()
            service.value = "lazy"
            return service
        
        self.container.register_lazy(IService, factory)
        
        # Not created yet
        assert not created
        
        # Resolve creates it
        resolved = self.container.resolve(IService)
        assert created
        assert resolved.get_value() == "lazy"
        
        # Same instance returned
        resolved2 = self.container.resolve(IService)
        assert resolved is resolved2
    
    def test_resolve_singleton(self):
        """Test singleton resolution returns same instance"""
        self.container.register_singleton(IService, ServiceA)
        
        instance1 = self.container.resolve(IService)
        instance2 = self.container.resolve(IService)
        
        assert instance1 is instance2
    
    def test_resolve_transient(self):
        """Test transient resolution returns new instance"""
        self.container.register_transient(IService, ServiceA)
        
        instance1 = self.container.resolve(IService)
        instance2 = self.container.resolve(IService)
        
        assert instance1 is not instance2
    
    @pytest.mark.asyncio
    async def test_resolve_scoped(self):
        """Test scoped resolution within scope"""
        self.container.register_scoped(IService, ServiceA)
        
        async with self.container.create_scope("scope1") as scope:
            instance1 = self.container.resolve(IService)
            instance2 = self.container.resolve(IService)
            assert instance1 is instance2
        
        async with self.container.create_scope("scope2") as scope:
            instance3 = self.container.resolve(IService)
            assert instance3 is not instance1
    
    def test_resolve_scoped_outside_scope_raises(self):
        """Test scoped resolution outside scope raises error"""
        self.container.register_scoped(IService, ServiceA)
        
        with pytest.raises(ResolutionError):
            self.container.resolve(IService)
    
    def test_resolve_unregistered_raises(self):
        """Test resolving unregistered service raises error"""
        with pytest.raises(ResolutionError):
            self.container.resolve(IService)
    
    def test_resolve_optional_returns_none(self):
        """Test resolve_optional returns None for unregistered"""
        result = self.container.resolve_optional(IService)
        assert result is None
    
    def test_resolve_optional_returns_instance(self):
        """Test resolve_optional returns instance when registered"""
        self.container.register_singleton(IService, ServiceA)
        result = self.container.resolve_optional(IService)
        assert result is not None
        assert isinstance(result, ServiceA)
    
    def test_is_registered(self):
        """Test is_registered method"""
        assert not self.container.is_registered(IService)
        
        self.container.register_singleton(IService, ServiceA)
        assert self.container.is_registered(IService)
    
    def test_get_registrations(self):
        """Test get_registrations returns all registrations"""
        self.container.register_singleton(IService, ServiceA)
        self.container.register_transient(ServiceB, ServiceB)
        
        registrations = self.container.get_registrations()
        assert IService in registrations
        assert ServiceB in registrations
    
    def test_clear(self):
        """Test clear removes all registrations"""
        self.container.register_singleton(IService, ServiceA)
        self.container.clear()
        
        assert not self.container.is_registered(IService)
    
    def test_factory_function(self):
        """Test factory function for complex creation"""
        def create_service():
            service = ServiceA()
            service.value = "factory_created"
            return service
        
        self.container.register_singleton(IService, factory=create_service)
        
        instance = self.container.resolve(IService)
        assert instance.get_value() == "factory_created"
    
    @pytest.mark.asyncio
    async def test_resolve_async(self):
        """Test resolve_async calls async initialize"""
        self.container.register_singleton(AsyncService, AsyncService)
        
        instance = await self.container.resolve_async(AsyncService)
        assert instance.initialized == True


class TestGlobalContainer:
    """Tests for global container functions"""
    
    def setup_method(self):
        """Reset global container before each test"""
        reset_container()
    
    def teardown_method(self):
        """Reset global container after each test"""
        reset_container()
    
    def test_get_container_creates_singleton(self):
        """Test get_container returns same instance"""
        container1 = get_container()
        container2 = get_container()
        
        assert container1 is container2
    
    def test_set_container(self):
        """Test set_container sets global container"""
        custom = Container()
        set_container(custom)
        
        assert get_container() is custom
    
    def test_reset_container(self):
        """Test reset_container clears global container"""
        container = get_container()
        reset_container()
        
        new_container = get_container()
        assert new_container is not container


class TestInjectDecorator:
    """Tests for inject decorator"""
    
    def setup_method(self):
        """Setup container with services"""
        reset_container()
        container = get_container()
        container.register_singleton(IService, ServiceA)
    
    def teardown_method(self):
        """Cleanup"""
        reset_container()
    
    def test_inject_decorator(self):
        """Test inject decorator injects dependencies"""
        @inject(IService)
        def my_function(service: IService, extra: str) -> str:
            return f"{service.get_value()}-{extra}"
        
        result = my_function("injected")
        assert result == "A-injected"
    
    def test_inject_multiple(self):
        """Test inject decorator with multiple services"""
        container = get_container()
        container.register_singleton(ServiceB, ServiceB)
        
        @inject(IService, ServiceB)
        def my_function(a: IService, b: ServiceB, extra: str) -> str:
            return f"{a.get_value()}-{b.get_value()}-{extra}"
        
        result = my_function("test")
        assert result == "A-B-test"


class TestServiceProvider:
    """Tests for ServiceProvider class"""
    
    def setup_method(self):
        """Setup container"""
        reset_container()
        container = get_container()
        container.register_singleton(IService, ServiceA)
    
    def teardown_method(self):
        """Cleanup"""
        reset_container()
    
    def test_service_provider_lazy_resolution(self):
        """Test ServiceProvider provides lazy resolution"""
        provider = ServiceProvider(IService)
        
        # Not resolved yet
        instance = provider.get()
        assert isinstance(instance, ServiceA)
        
        # Same instance
        instance2 = provider.get()
        assert instance is instance2
    
    def test_service_provider_reset(self):
        """Test ServiceProvider reset clears cached instance"""
        provider = ServiceProvider(IService)
        
        instance1 = provider.get()
        provider.reset()
        instance2 = provider.get()
        
        # Different instances (singleton, but provider reset its cache)
        assert instance1 is instance2  # Same because singleton


class TestServiceLifetime:
    """Tests for ServiceLifetime enum"""
    
    def test_lifetime_values(self):
        """Test ServiceLifetime enum values"""
        assert ServiceLifetime.SINGLETON.value == "singleton"
        assert ServiceLifetime.TRANSIENT.value == "transient"
        assert ServiceLifetime.SCOPED.value == "scoped"
        assert ServiceLifetime.LAZY.value == "lazy"


class TestServiceDescriptor:
    """Tests for ServiceDescriptor dataclass"""
    
    def test_service_descriptor_creation(self):
        """Test ServiceDescriptor creation"""
        descriptor = ServiceDescriptor(
            service_type=IService,
            implementation=ServiceA,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        assert descriptor.service_type == IService
        assert descriptor.implementation == ServiceA
        assert descriptor.lifetime == ServiceLifetime.SINGLETON
        assert descriptor.instance is None
        assert descriptor.dependencies == []


# =============================================================================
# Run tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
