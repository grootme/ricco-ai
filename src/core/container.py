"""
Dependency Injection Container for RICCO AI
Implements Dependency Injection Pattern (IoC Container)

This module provides a lightweight DI container that:
- Manages service lifecycles (singleton, transient, scoped)
- Enables loose coupling between components
- Facilitates testing through easy mocking
- Follows the Service Locator pattern for legacy compatibility

Usage:
    container = Container()
    container.register_singleton(IAIProvider, OpenAIProvider)
    provider = container.resolve(IAIProvider)
"""

from typing import (
    Any, Callable, Dict, List, Optional, Type, TypeVar, Generic,
    Protocol, runtime_checkable, get_origin, get_args
)
from enum import Enum
from dataclasses import dataclass, field
from functools import wraps
import inspect
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

T = TypeVar('T')
TService = TypeVar('TService')


class ServiceLifetime(Enum):
    """Service lifetime options"""
    SINGLETON = "singleton"      # Single instance for application lifetime
    TRANSIENT = "transient"      # New instance every request
    SCOPED = "scoped"           # Single instance per scope (request)
    LAZY = "lazy"               # Singleton but created on first access


@dataclass
class ServiceDescriptor:
    """Describes a registered service"""
    service_type: Type
    implementation: Callable[..., Any]
    lifetime: ServiceLifetime
    instance: Optional[Any] = None
    factory: Optional[Callable[..., Any]] = None
    dependencies: List[Type] = field(default_factory=list)


class ResolutionError(Exception):
    """Raised when service resolution fails"""
    pass


class RegistrationError(Exception):
    """Raised when service registration fails"""
    pass


class Container:
    """
    Lightweight Dependency Injection Container
    
    Implements:
    - Service Locator Pattern
    - Dependency Injection Pattern
    - Inversion of Control (IoC)
    
    Features:
    - Singleton, Transient, Scoped lifetimes
    - Automatic dependency resolution
    - Factory function support
    - Async initialization support
    """
    
    def __init__(self):
        self._services: Dict[Type, ServiceDescriptor] = {}
        self._singletons: Dict[Type, Any] = {}
        self._scopes: Dict[str, Dict[Type, Any]] = {}
        self._current_scope: Optional[str] = None
        self._resolving: set = set()  # Circular dependency detection
        
    # =========================================================================
    # Registration Methods
    # =========================================================================
    
    def register_singleton(
        self,
        service_type: Type[TService],
        implementation: Optional[Type] = None,
        factory: Optional[Callable[..., TService]] = None
    ) -> 'Container':
        """
        Register a singleton service.
        
        Args:
            service_type: The service interface/protocol
            implementation: The concrete implementation class
            factory: Optional factory function for complex creation
            
        Returns:
            Container for fluent API
        """
        return self._register(
            service_type=service_type,
            implementation=implementation or service_type,
            lifetime=ServiceLifetime.SINGLETON,
            factory=factory
        )
    
    def register_transient(
        self,
        service_type: Type[TService],
        implementation: Optional[Type] = None,
        factory: Optional[Callable[..., TService]] = None
    ) -> 'Container':
        """
        Register a transient service (new instance each time).
        """
        return self._register(
            service_type=service_type,
            implementation=implementation or service_type,
            lifetime=ServiceLifetime.TRANSIENT,
            factory=factory
        )
    
    def register_scoped(
        self,
        service_type: Type[TService],
        implementation: Optional[Type] = None,
        factory: Optional[Callable[..., TService]] = None
    ) -> 'Container':
        """
        Register a scoped service (single instance per scope).
        """
        return self._register(
            service_type=service_type,
            implementation=implementation or service_type,
            lifetime=ServiceLifetime.SCOPED,
            factory=factory
        )
    
    def register_lazy(
        self,
        service_type: Type[TService],
        factory: Callable[[], TService]
    ) -> 'Container':
        """
        Register a lazy singleton (created on first access).
        """
        return self._register(
            service_type=service_type,
            implementation=None,
            lifetime=ServiceLifetime.LAZY,
            factory=factory
        )
    
    def register_instance(
        self,
        service_type: Type[TService],
        instance: TService
    ) -> 'Container':
        """
        Register an existing instance as singleton.
        """
        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation=lambda: instance,
            lifetime=ServiceLifetime.SINGLETON,
            instance=instance
        )
        self._services[service_type] = descriptor
        self._singletons[service_type] = instance
        return self
    
    def _register(
        self,
        service_type: Type,
        implementation: Optional[Type],
        lifetime: ServiceLifetime,
        factory: Optional[Callable] = None
    ) -> 'Container':
        """Internal registration method"""
        if service_type in self._services:
            logger.warning(f"Overwriting existing registration for {service_type}")
        
        descriptor = ServiceDescriptor(
            service_type=service_type,
            implementation=implementation,
            lifetime=lifetime,
            factory=factory
        )
        
        # Analyze constructor dependencies
        if implementation and not factory:
            descriptor.dependencies = self._analyze_dependencies(implementation)
        
        self._services[service_type] = descriptor
        logger.debug(f"Registered {service_type.__name__} as {lifetime.value}")
        return self
    
    # =========================================================================
    # Resolution Methods
    # =========================================================================
    
    def resolve(self, service_type: Type[TService]) -> TService:
        """
        Resolve a service by type.
        
        Args:
            service_type: The service interface/protocol to resolve
            
        Returns:
            The resolved service instance
            
        Raises:
            ResolutionError: If service cannot be resolved
        """
        if service_type not in self._services:
            raise ResolutionError(f"Service {service_type} is not registered")
        
        descriptor = self._services[service_type]
        
        # Check for circular dependencies
        if service_type in self._resolving:
            raise ResolutionError(
                f"Circular dependency detected for {service_type}"
            )
        
        return self._resolve_descriptor(descriptor)
    
    def resolve_optional(self, service_type: Type[TService]) -> Optional[TService]:
        """
        Resolve a service, returning None if not registered.
        """
        try:
            return self.resolve(service_type)
        except ResolutionError:
            return None
    
    def _resolve_descriptor(self, descriptor: ServiceDescriptor) -> Any:
        """Resolve a service descriptor"""
        service_type = descriptor.service_type
        
        # Handle different lifetimes
        if descriptor.lifetime == ServiceLifetime.SINGLETON:
            if service_type in self._singletons:
                return self._singletons[service_type]
            instance = self._create_instance(descriptor)
            self._singletons[service_type] = instance
            return instance
        
        elif descriptor.lifetime == ServiceLifetime.LAZY:
            if service_type in self._singletons:
                return self._singletons[service_type]
            if descriptor.factory:
                instance = descriptor.factory()
                self._singletons[service_type] = instance
                return instance
            raise ResolutionError(f"No factory for lazy service {service_type}")
        
        elif descriptor.lifetime == ServiceLifetime.SCOPED:
            if not self._current_scope:
                raise ResolutionError(
                    f"Cannot resolve scoped service {service_type} outside of scope"
                )
            scope = self._scopes[self._current_scope]
            if service_type in scope:
                return scope[service_type]
            instance = self._create_instance(descriptor)
            scope[service_type] = instance
            return instance
        
        else:  # TRANSIENT
            return self._create_instance(descriptor)
    
    def _create_instance(self, descriptor: ServiceDescriptor) -> Any:
        """Create a new instance"""
        service_type = descriptor.service_type
        self._resolving.add(service_type)
        
        try:
            if descriptor.factory:
                return descriptor.factory()
            
            implementation = descriptor.implementation
            if not implementation:
                raise ResolutionError(f"No implementation for {service_type}")
            
            # Resolve constructor dependencies
            kwargs = {}
            for dep_type in descriptor.dependencies:
                dep_name = self._get_dependency_name(implementation, dep_type)
                kwargs[dep_name] = self.resolve(dep_type)
            
            return implementation(**kwargs)
        
        finally:
            self._resolving.discard(service_type)
    
    # =========================================================================
    # Scope Management
    # =========================================================================
    
    @asynccontextmanager
    async def create_scope(self, scope_id: Optional[str] = None):
        """
        Create a dependency injection scope.
        
        Usage:
            async with container.create_scope() as scope:
                service = container.resolve(IService)
        """
        scope_id = scope_id or f"scope_{id(self)}"
        self._scopes[scope_id] = {}
        previous_scope = self._current_scope
        self._current_scope = scope_id
        
        try:
            yield scope_id
        finally:
            self._current_scope = previous_scope
            if scope_id in self._scopes:
                # Cleanup scoped instances
                del self._scopes[scope_id]
    
    # =========================================================================
    # Introspection
    # =========================================================================
    
    def _analyze_dependencies(self, implementation: Type) -> List[Type]:
        """Analyze constructor dependencies"""
        dependencies = []
        
        try:
            sig = inspect.signature(implementation.__init__)
            for name, param in sig.parameters.items():
                if name == 'self':
                    continue
                if param.annotation != inspect.Parameter.empty:
                    dependencies.append(param.annotation)
        except Exception as e:
            logger.debug(f"Could not analyze dependencies: {e}")
        
        return dependencies
    
    def _get_dependency_name(self, implementation: Type, dep_type: Type) -> str:
        """Get parameter name for dependency type"""
        try:
            sig = inspect.signature(implementation.__init__)
            for name, param in sig.parameters.items():
                if param.annotation == dep_type:
                    return name
        except Exception:
            pass
        return dep_type.__name__.lower()
    
    def is_registered(self, service_type: Type) -> bool:
        """Check if a service is registered"""
        return service_type in self._services
    
    def get_registrations(self) -> Dict[Type, ServiceDescriptor]:
        """Get all registered services"""
        return self._services.copy()
    
    def clear(self) -> None:
        """Clear all registrations"""
        self._services.clear()
        self._singletons.clear()
        self._scopes.clear()
    
    # =========================================================================
    # Async Support
    # =========================================================================
    
    async def resolve_async(self, service_type: Type[TService]) -> TService:
        """
        Resolve a service with async initialization support.
        
        If the service has an async `initialize` method, it will be called.
        """
        instance = self.resolve(service_type)
        
        # Call async initialize if available
        if hasattr(instance, 'initialize') and inspect.iscoroutinefunction(instance.initialize):
            await instance.initialize()
        
        return instance


# =============================================================================
# Global Container Instance (Service Locator Pattern)
# =============================================================================

_container: Optional[Container] = None


def get_container() -> Container:
    """Get the global container instance"""
    global _container
    if _container is None:
        _container = Container()
    return _container


def set_container(container: Container) -> None:
    """Set the global container instance"""
    global _container
    _container = container


def reset_container() -> None:
    """Reset the global container"""
    global _container
    _container = None


# =============================================================================
# Decorator for Automatic Injection
# =============================================================================

def inject(*services: Type):
    """
    Decorator for automatic dependency injection.
    
    Usage:
        @inject(IAIProvider, IMemoryService)
        def my_function(ai_provider, memory, user_input):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            container = get_container()
            injected = [container.resolve(s) for s in services]
            return func(*injected, *args, **kwargs)
        return wrapper
    return decorator


def async_inject(*services: Type):
    """
    Decorator for async automatic dependency injection.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            container = get_container()
            injected = [await container.resolve_async(s) for s in services]
            return await func(*injected, *args, **kwargs)
        return wrapper
    return decorator


# =============================================================================
# Provider Classes for Delayed Resolution
# =============================================================================

class ServiceProvider(Generic[T]):
    """
    Provider for lazy service resolution.
    
    Useful when you need to defer service creation.
    """
    
    def __init__(self, service_type: Type[T]):
        self._service_type = service_type
        self._instance: Optional[T] = None
    
    def get(self) -> T:
        """Get the service instance"""
        if self._instance is None:
            self._instance = get_container().resolve(self._service_type)
        return self._instance
    
    def reset(self) -> None:
        """Reset the cached instance"""
        self._instance = None


# =============================================================================
# ALIASES FOR BACKWARD COMPATIBILITY
# =============================================================================

# Alias for backward compatibility
ServiceContainer = Container

__all__ = [
    "Container",
    "ServiceContainer",  # Alias
    "ServiceLifetime",
    "ServiceDescriptor",
    "ResolutionError",
    "RegistrationError",
    "ServiceProvider",
    "get_container",
    "set_container",
    "reset_container",
    "inject",
    "async_inject",
]
