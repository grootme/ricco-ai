"""
RICCO Privacy Manager
Gestor de configuración de privacidad por usuario
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID
import json

from .models import PrivacySettings, DataExportRequest


class PrivacyManager:
    """Gestor de configuración de privacidad"""
    
    def __init__(self):
        self._settings_cache: Dict[str, PrivacySettings] = {}
    
    def get_privacy_settings(self, user_id: str) -> PrivacySettings:
        """
        Obtiene la configuración de privacidad de un usuario
        
        Args:
            user_id: ID del usuario (RICCO ID)
            
        Returns:
            PrivacySettings del usuario
        """
        if user_id in self._settings_cache:
            return self._settings_cache[user_id]
        
        # Crear configuración por defecto
        settings = PrivacySettings(user_id=user_id)
        self._settings_cache[user_id] = settings
        return settings
    
    def update_privacy_settings(
        self,
        user_id: str,
        updates: Dict[str, Any]
    ) -> PrivacySettings:
        """
        Actualiza la configuración de privacidad de un usuario
        
        Args:
            user_id: ID del usuario
            updates: Campos a actualizar
            
        Returns:
            PrivacySettings actualizados
        """
        settings = self.get_privacy_settings(user_id)
        
        # Aplicar actualizaciones
        for key, value in updates.items():
            if hasattr(settings, key):
                setattr(settings, key, value)
        
        settings.updated_at = datetime.utcnow()
        
        # Guardar en caché
        self._settings_cache[user_id] = settings
        
        return settings
    
    def set_ai_personalization(
        self,
        user_id: str,
        enabled: bool
    ) -> PrivacySettings:
        """Habilita o deshabilita la personalización con IA"""
        return self.update_privacy_settings(
            user_id,
            {
                "ai_personalization_enabled": enabled,
                "data_collection_enabled": enabled,  # Necesario para IA
            }
        )
    
    def set_location_sharing(
        self,
        user_id: str,
        enabled: bool,
        precision: str = "approximate"
    ) -> PrivacySettings:
        """Configura el uso compartido de ubicación"""
        return self.update_privacy_settings(
            user_id,
            {
                "location_sharing_enabled": enabled,
                "location_precision": precision,
                "show_location": enabled
            }
        )
    
    def set_marketing_preferences(
        self,
        user_id: str,
        notifications: bool = False,
        emails: bool = False,
        sms: bool = False
    ) -> PrivacySettings:
        """Configura preferencias de marketing"""
        return self.update_privacy_settings(
            user_id,
            {
                "marketing_notifications": notifications,
                "promotional_emails": emails,
                "sms_notifications": sms,
                "personalized_ads_enabled": notifications or emails
            }
        )
    
    def set_profile_visibility(
        self,
        user_id: str,
        visibility: str = "contacts"
    ) -> PrivacySettings:
        """Configura la visibilidad del perfil"""
        is_public = visibility == "public"
        return self.update_privacy_settings(
            user_id,
            {
                "profile_visibility": visibility,
                "show_profile_photo": is_public or visibility == "contacts",
                "show_online_status": is_public or visibility == "contacts",
                "show_last_seen": is_public or visibility == "contacts"
            }
        )
    
    def get_data_categories(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene las categorías de datos del usuario
        
        Returns:
            Lista de categorías con su estado de habilitación
        """
        settings = self.get_privacy_settings(user_id)
        
        return [
            {
                "category": "profile",
                "name": "Datos de perfil",
                "name_en": "Profile data",
                "description": "Nombre, foto, información de contacto",
                "enabled": True,  # Necesario para el servicio
                "required": True
            },
            {
                "category": "activity",
                "name": "Historial de actividad",
                "name_en": "Activity history",
                "description": "Búsquedas, navegación, interacciones",
                "enabled": settings.save_browsing_history,
                "required": False
            },
            {
                "category": "location",
                "name": "Ubicación",
                "name_en": "Location",
                "description": "Ubicación actual e historial",
                "enabled": settings.location_sharing_enabled,
                "required": False
            },
            {
                "category": "payments",
                "name": "Datos de pago",
                "name_en": "Payment data",
                "description": "Métodos de pago, historial de transacciones",
                "enabled": settings.save_payment_methods,
                "required": False
            },
            {
                "category": "ai_personalization",
                "name": "Personalización IA",
                "name_en": "AI Personalization",
                "description": "Preferencias para recomendaciones y GenUI",
                "enabled": settings.ai_personalization_enabled,
                "required": False
            },
            {
                "category": "marketing",
                "name": "Marketing",
                "name_en": "Marketing",
                "description": "Comunicaciones promocionales",
                "enabled": settings.marketing_notifications,
                "required": False
            },
            {
                "category": "analytics",
                "name": "Análisis",
                "name_en": "Analytics",
                "description": "Estadísticas de uso anónimas",
                "enabled": settings.analytics_enabled,
                "required": False
            }
        ]
    
    def request_data_export(
        self,
        user_id: str,
        categories: Optional[List[str]] = None
    ) -> DataExportRequest:
        """
        Crea una solicitud de exportación de datos
        
        Args:
            user_id: ID del usuario
            categories: Categorías específicas a exportar (None = todas)
            
        Returns:
            DataExportRequest creada
        """
        request = DataExportRequest(
            user_id=user_id,
            request_type="export",
            data_categories=categories or ["all"],
            status="pending"
        )
        
        # En una implementación real, esto se procesaría en background
        return request
    
    def request_data_deletion(
        self,
        user_id: str,
        categories: Optional[List[str]] = None
    ) -> DataExportRequest:
        """
        Crea una solicitud de eliminación de datos
        
        Args:
            user_id: ID del usuario
            categories: Categorías específicas a eliminar (None = todas)
            
        Returns:
            DataExportRequest creada
        """
        request = DataExportRequest(
            user_id=user_id,
            request_type="deletion",
            data_categories=categories or ["all"],
            status="pending",
            verification_method="email"
        )
        
        return request
    
    def get_privacy_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Obtiene un resumen de la configuración de privacidad
        
        Returns:
            Resumen legible de la configuración
        """
        settings = self.get_privacy_settings(user_id)
        
        return {
            "profile_visibility": {
                "level": settings.profile_visibility,
                "description": self._get_visibility_description(settings.profile_visibility)
            },
            "ai_personalization": {
                "enabled": settings.ai_personalization_enabled,
                "data_collection": settings.data_collection_enabled
            },
            "location": {
                "sharing": settings.location_sharing_enabled,
                "precision": settings.location_precision
            },
            "marketing": {
                "notifications": settings.marketing_notifications,
                "emails": settings.promotional_emails,
                "sms": settings.sms_notifications
            },
            "data_retention": {
                "search_history": settings.save_search_history,
                "browsing_history": settings.save_browsing_history,
                "payment_methods": settings.save_payment_methods
            },
            "third_party": {
                "partners": settings.share_with_partners,
                "research": settings.share_for_research
            },
            "security_score": self._calculate_privacy_score(settings)
        }
    
    def _get_visibility_description(self, level: str) -> str:
        """Obtiene descripción del nivel de visibilidad"""
        descriptions = {
            "public": "Todos pueden ver tu perfil",
            "contacts": "Solo tus contactos pueden ver tu perfil",
            "private": "Solo tú puedes ver tu perfil"
        }
        return descriptions.get(level, level)
    
    def _calculate_privacy_score(self, settings: PrivacySettings) -> int:
        """
        Calcula un puntaje de privacidad (0-100)
        Mayor puntaje = más privado
        """
        score = 50  # Base
        
        # Ajustes que aumentan privacidad
        if settings.profile_visibility == "private":
            score += 15
        elif settings.profile_visibility == "contacts":
            score += 10
        
        if not settings.ai_personalization_enabled:
            score += 10
        if not settings.location_sharing_enabled:
            score += 10
        if not settings.marketing_notifications:
            score += 5
        if not settings.share_with_partners:
            score += 10
        
        # Ajustes que disminuyen privacidad
        if settings.data_collection_enabled:
            score -= 5
        if settings.personalized_ads_enabled:
            score -= 5
        
        return max(0, min(100, score))
    
    def get_recommended_settings(self, user_id: str) -> Dict[str, Any]:
        """
        Obtiene configuración recomendada basada en uso
        
        Returns:
            Configuración recomendada
        """
        # En una implementación real, esto se basaría en análisis de uso
        return {
            "profile_visibility": "contacts",
            "ai_personalization_enabled": True,
            "location_sharing_enabled": False,
            "location_precision": "city",
            "marketing_notifications": False,
            "promotional_emails": False,
            "sms_notifications": False,
            "save_search_history": True,
            "save_browsing_history": True,
            "save_payment_methods": True,
            "share_with_partners": False,
            "share_for_research": False
        }
    
    def apply_recommended_settings(self, user_id: str) -> PrivacySettings:
        """Aplica configuración recomendada"""
        recommended = self.get_recommended_settings(user_id)
        return self.update_privacy_settings(user_id, recommended)
