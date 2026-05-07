"""
Service Registration and Bootstrap

This module registers all services in the DI container.
Import this module early in application startup.

Usage:
    from src.core.bootstrap import bootstrap_services
    bootstrap_services()
"""

from src.core.container import get_container, ServiceLifetime
from src.config.settings import settings


def bootstrap_services() -> None:
    """
    Register all services in the DI container.
    
    This should be called during application startup.
    """
    container = get_container()
    
    # =========================================================================
    # Configuration
    # =========================================================================
    container.register_instance('Settings', settings)
    
    # =========================================================================
    # A2UI Service
    # =========================================================================
    def create_a2ui_service():
        from src.services.a2ui import A2UIService
        service = A2UIService(
            catalog_version=settings.A2UI_CATALOG_VERSION,
            enable_context=True
        )
        return service
    
    container.register_lazy('A2UIService', create_a2ui_service)
    
    # =========================================================================
    # AI Providers (lazy singletons)
    # =========================================================================
    def create_openai_provider():
        from src.ai_providers.providers.openai_provider import OpenAIProvider
        from src.ai_providers.base import AIProviderConfig
        from src.ai_providers.models import AIProviderType
        
        config = AIProviderConfig(
            provider_type=AIProviderType.OPENAI,
            api_key=settings.OPENROUTER_API_KEY,
            base_url=settings.OPENROUTER_BASE_URL,
            model=settings.DEFAULT_MODEL
        )
        return OpenAIProvider(config)
    
    container.register_lazy('OpenAIProvider', create_openai_provider)
    
    # =========================================================================
    # Session Service
    # =========================================================================
    def create_session_service():
        from src.services.service_providers import session_service
        return session_service
    
    container.register_instance('SessionService', None)  # Set after initialization
    
    # =========================================================================
    # Memory Service
    # =========================================================================
    def create_memory_service():
        from src.services.service_providers import memory_service
        return memory_service
    
    container.register_instance('MemoryService', None)  # Set after initialization
    
    # =========================================================================
    # Artifacts Service
    # =========================================================================
    def create_artifacts_service():
        from src.services.service_providers import artifacts_service
        return artifacts_service
    
    container.register_instance('ArtifactsService', None)  # Set after initialization


def get_service(service_name: str):
    """
    Convenience function to get a service from the container.
    
    Args:
        service_name: Name of the registered service
        
    Returns:
        The service instance
    """
    container = get_container()
    return container.resolve(service_name)


# Auto-bootstrap on import (optional, can be disabled)
# bootstrap_services()
