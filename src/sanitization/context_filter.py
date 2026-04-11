"""
Filtro de Contexto para Sanitización en RICCO AI
Filtrado específico por tipo de contexto

Este módulo implementa el filtrado de datos sensibles basado en
el tipo de contexto, aplicando reglas específicas para cada
categoría de información.

Autor: RICCO AI Team
Mercado objetivo: Cuba y América Latina
"""

from typing import Dict, Any, Optional, List
from enum import Enum
from datetime import datetime

from structlog import get_logger

from .models import (
    SensitiveDataType,
    SanitizationLevel,
    DataClassification,
    ContextSanitizationConfig,
)
from .sanitizer import SensitiveDataSanitizer
from .patterns import SensitiveDataPatterns

logger = get_logger(__name__)


class SubscriptionTier(str, Enum):
    """
    Niveles de suscripción del usuario.
    
    Determina el nivel de filtrado aplicado - usuarios premium
    pueden tener acceso a más datos sin filtrar.
    """
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class ContextDataFilter:
    """
    Filtro de datos sensible por tipo de contexto.
    
    Aplica reglas de sanitización específicas según el tipo
    de contexto que se está procesando. Cada tipo de contexto
    tiene diferentes requisitos de privacidad.
    
    Contextos soportados:
    - PERSONAL: Redacta email, teléfono, números de ID
    - SPATIAL: Generaliza coordenadas a ciudad/región
    - VERTICAL: Filtra datos médicos, financieros
    - CONVERSATION: Mantiene intención pero redacta PII
    
    Example:
        >>> filter = ContextDataFilter()
        >>> personal_data = {"email": "juan@example.com", "name": "Juan"}
        >>> filtered = filter.filter_personal_context(personal_data)
        >>> print(filtered["email"])
        "j***@example.com"
    """
    
    def __init__(
        self,
        default_level: SanitizationLevel = SanitizationLevel.STANDARD,
        sanitizer: Optional[SensitiveDataSanitizer] = None,
    ):
        """
        Inicializa el filtro de contexto.
        
        Args:
            default_level: Nivel de sanitización por defecto
            sanitizer: Instancia del sanitizador (se crea una si no se proporciona)
        """
        self.default_level = default_level
        self.sanitizer = sanitizer or SensitiveDataSanitizer(level=default_level)
        
        # Configuraciones por tipo de contexto
        self._context_configs: Dict[str, ContextSanitizationConfig] = {}
        self._initialize_context_configs()
        
        logger.info(
            "ContextDataFilter initialized",
            default_level=default_level.value,
        )
    
    def _initialize_context_configs(self) -> None:
        """Inicializa las configuraciones por tipo de contexto."""
        
        # PERSONAL: Datos personales del usuario
        self._context_configs["personal"] = ContextSanitizationConfig(
            context_type="personal",
            sanitization_level=SanitizationLevel.AGGRESSIVE,
            protected_fields=[
                "email", "phone", "ssn", "government_id",
                "address", "date_of_birth", "national_id",
            ],
            excluded_fields=["name", "timezone", "language", "currency"],
        )
        
        # SPATIAL: Ubicación y datos geográficos
        self._context_configs["spatial"] = ContextSanitizationConfig(
            context_type="spatial",
            sanitization_level=SanitizationLevel.STANDARD,
            protected_fields=["latitude", "longitude", "gps", "coordinates"],
            location_precision="city",  # Generalizar a ciudad
            location_redact_coords=True,
        )
        
        # VERTICAL: Datos específicos de industria
        self._context_configs["vertical"] = ContextSanitizationConfig(
            context_type="vertical",
            sanitization_level=SanitizationLevel.MAXIMUM,
            protected_fields=[
                # Salud
                "medical_records", "conditions", "medications", "diagnoses",
                # Finanzas
                "account_numbers", "transactions", "balances", "credit_score",
                # Legal
                "legal_cases", "court_records",
            ],
        )
        
        # CONVERSATION: Estado de conversación
        self._context_configs["conversation"] = ContextSanitizationConfig(
            context_type="conversation",
            sanitization_level=SanitizationLevel.STANDARD,
            protected_fields=["user_input", "message_history"],
            excluded_fields=["intent", "state", "session_id"],
        )
        
        # DEVICE: Información del dispositivo
        self._context_configs["device"] = ContextSanitizationConfig(
            context_type="device",
            sanitization_level=SanitizationLevel.MINIMAL,
            protected_fields=["device_id", "ip_address"],
            excluded_fields=["device_type", "platform", "orientation"],
        )
        
        # TEMPORAL: Información temporal
        self._context_configs["temporal"] = ContextSanitizationConfig(
            context_type="temporal",
            sanitization_level=SanitizationLevel.MINIMAL,
            protected_fields=[],  # No hay datos sensibles en temporal
        )
        
        # SOLUTION: Contexto de solución activa
        self._context_configs["solution"] = ContextSanitizationConfig(
            context_type="solution",
            sanitization_level=SanitizationLevel.STANDARD,
            protected_fields=["api_keys", "credentials", "tokens"],
            excluded_fields=["solution_id", "solution_name", "user_role"],
        )
        
        # HORIZONTAL: Datos cross-solution
        self._context_configs["horizontal"] = ContextSanitizationConfig(
            context_type="horizontal",
            sanitization_level=SanitizationLevel.STANDARD,
            protected_fields=["wallet_address", "bank_accounts"],
            excluded_fields=["energy_points_balance", "trust_score"],
        )
        
        # SKILLS: Habilidades de IA
        self._context_configs["skills"] = ContextSanitizationConfig(
            context_type="skills",
            sanitization_level=SanitizationLevel.MINIMAL,
            protected_fields=[],
        )
    
    def get_context_config(self, context_type: str) -> Optional[ContextSanitizationConfig]:
        """
        Obtiene la configuración para un tipo de contexto.
        
        Args:
            context_type: Tipo de contexto
            
        Returns:
            Configuración o None si no existe
        """
        return self._context_configs.get(context_type)
    
    def filter_context(
        self,
        context_type: str,
        data: Dict[str, Any],
        tier: SubscriptionTier = SubscriptionTier.FREE,
    ) -> Dict[str, Any]:
        """
        Filtra datos de contexto según su tipo.
        
        Método principal que enruta al filtro apropiado según
        el tipo de contexto.
        
        Args:
            context_type: Tipo de contexto
            data: Datos a filtrar
            tier: Nivel de suscripción del usuario
            
        Returns:
            Datos filtrados
        """
        # Mapear tipo de contexto a método de filtrado
        filter_methods = {
            "personal": self.filter_personal_context,
            "spatial": self.filter_spatial_context,
            "vertical": self.filter_vertical_context,
            "conversation": self.filter_conversation_context,
            "device": self.filter_device_context,
            "temporal": self.filter_temporal_context,
            "solution": self.filter_solution_context,
            "horizontal": self.filter_horizontal_context,
            "skills": self.filter_skills_context,
        }
        
        filter_method = filter_methods.get(context_type)
        
        if filter_method:
            return filter_method(data, tier)
        
        # Filtro genérico para tipos no reconocidos
        return self._filter_generic_context(context_type, data, tier)
    
    def filter_personal_context(
        self,
        data: Dict[str, Any],
        tier: SubscriptionTier = SubscriptionTier.FREE,
    ) -> Dict[str, Any]:
        """
        Filtra contexto personal.
        
        Redacta:
        - Email (redacción parcial: j***@example.com)
        - Teléfono (redacción parcial: ***-***-4567)
        - Números de identificación (completo)
        - Direcciones postales
        
        Args:
            data: Datos personales
            tier: Nivel de suscripción
            
        Returns:
            Datos personales filtrados
        """
        filtered = data.copy()
        config = self._context_configs.get("personal")
        
        if not config:
            return filtered
        
        # Ajustar nivel según tier
        level = self._get_level_for_tier(config.sanitization_level, tier)
        
        # Filtrar email
        if "email" in filtered and filtered["email"]:
            filtered["email"] = SensitiveDataPatterns.partial_redact_email(
                filtered["email"]
            )
        
        # Filtrar teléfono
        if "phone" in filtered and filtered["phone"]:
            filtered["phone"] = SensitiveDataPatterns.partial_redact_phone(
                filtered["phone"]
            )
        
        # Filtrar número de identificación
        id_fields = ["ssn", "government_id", "national_id", "dni", "ci", "curp", "rut"]
        for field in id_fields:
            if field in filtered and filtered[field]:
                filtered[field] = "[DOCUMENT_REDACTED]"
        
        # Filtrar dirección
        if "address" in filtered and filtered["address"]:
            # Mantener solo ciudad/país
            if isinstance(filtered["address"], dict):
                filtered["address"] = {
                    "city": filtered["address"].get("city"),
                    "country": filtered["address"].get("country"),
                    "_redacted": True,
                }
            else:
                filtered["address"] = "[ADDRESS_REDACTED]"
        
        # Filtrar fecha de nacimiento (mantener solo año para edad aproximada)
        if "date_of_birth" in filtered and filtered["date_of_birth"]:
            try:
                if isinstance(filtered["date_of_birth"], str):
                    year = filtered["date_of_birth"][:4]
                    filtered["birth_year"] = int(year)
                    filtered["date_of_birth"] = "[REDACTED]"
            except (ValueError, IndexError):
                filtered["date_of_birth"] = "[REDACTED]"
        
        # Marcar como filtrado
        filtered["_sanitized"] = True
        filtered["_sanitized_at"] = datetime.utcnow().isoformat()
        
        return filtered
    
    def filter_spatial_context(
        self,
        data: Dict[str, Any],
        tier: SubscriptionTier = SubscriptionTier.FREE,
    ) -> Dict[str, Any]:
        """
        Filtra contexto espacial/geográfico.
        
        Generaliza:
        - Coordenadas exactas → ciudad/región
        - Dirección exacta → ciudad
        - Lugares específicos → tipo de lugar
        
        Args:
            data: Datos espaciales
            tier: Nivel de suscripción
            
        Returns:
            Datos espaciales generalizados
        """
        filtered = data.copy()
        config = self._context_configs.get("spatial")
        
        if not config:
            return filtered
        
        # Determinar precisión según tier
        precision_map = {
            SubscriptionTier.FREE: "city",
            SubscriptionTier.BASIC: "city",
            SubscriptionTier.PRO: "region",
            SubscriptionTier.ENTERPRISE: "city",  # Enterprise puede optar por más
        }
        precision = precision_map.get(tier, "city")
        
        # Filtrar coordenadas
        lat = filtered.get("latitude")
        lon = filtered.get("longitude")
        
        if lat is not None and lon is not None:
            if config.location_redact_coords:
                generalized = SensitiveDataPatterns.generalize_coordinates(
                    lat, lon, precision
                )
                
                filtered["latitude"] = generalized["generalized_lat"]
                filtered["longitude"] = generalized["generalized_lon"]
                filtered["_coords_generalized"] = True
                filtered["_precision"] = precision
        
        # Remover coordenadas exactas de otros campos
        for key in ["gps", "coordinates", "exact_location"]:
            if key in filtered:
                del filtered[key]
        
        # Mantener información de ciudad/región
        # city, country, state ya son generalizados
        
        # Marcar como filtrado
        filtered["_sanitized"] = True
        filtered["_sanitized_at"] = datetime.utcnow().isoformat()
        
        return filtered
    
    def filter_vertical_context(
        self,
        data: Dict[str, Any],
        tier: SubscriptionTier = SubscriptionTier.FREE,
    ) -> Dict[str, Any]:
        """
        Filtra contexto vertical (específico de industria).
        
        Aplica filtrado especializado según la vertical:
        - health: Datos médicos protegidos
        - finance: Datos financieros protegidos
        - commerce: Transacciones protegidas
        
        Args:
            data: Datos de la vertical
            tier: Nivel de suscripción
            
        Returns:
            Datos de vertical filtrados
        """
        filtered = data.copy()
        
        # Determinar qué vertical está presente
        if "health" in filtered:
            filtered["health"] = self._filter_health_data(filtered["health"], tier)
        
        if "finance" in filtered:
            filtered["finance"] = self._filter_finance_data(filtered["finance"], tier)
        
        if "commerce" in filtered:
            filtered["commerce"] = self._filter_commerce_data(filtered["commerce"], tier)
        
        if "logistics" in filtered:
            filtered["logistics"] = self._filter_logistics_data(filtered["logistics"], tier)
        
        if "travel" in filtered:
            filtered["travel"] = self._filter_travel_data(filtered["travel"], tier)
        
        # Marcar como filtrado
        filtered["_sanitized"] = True
        filtered["_sanitized_at"] = datetime.utcnow().isoformat()
        
        return filtered
    
    def _filter_health_data(
        self,
        data: Dict[str, Any],
        tier: SubscriptionTier,
    ) -> Dict[str, Any]:
        """Filtra datos de salud específicos."""
        filtered = data.copy()
        
        # Redactar registros médicos
        sensitive_fields = [
            "medical_records", "conditions", "medications",
            "diagnoses", "treatments", "procedures",
            "lab_results", "prescriptions", "allergies",
        ]
        
        for field in sensitive_fields:
            if field in filtered and filtered[field]:
                # Indicar presencia sin revelar detalles
                if isinstance(filtered[field], list):
                    filtered[field] = f"[{len(filtered[field])} ITEMS REDACTED]"
                elif isinstance(filtered[field], dict):
                    filtered[field] = "[DATA REDACTED]"
                else:
                    filtered[field] = "[REDACTED]"
        
        # Mantener solo información no sensible
        safe_fields = ["providers", "insurance_verified", "has_records"]
        result = {}
        for field in safe_fields:
            if field in filtered:
                result[field] = filtered[field]
        
        result["_health_data_redacted"] = True
        
        return result
    
    def _filter_finance_data(
        self,
        data: Dict[str, Any],
        tier: SubscriptionTier,
    ) -> Dict[str, Any]:
        """Filtra datos financieros específicos."""
        filtered = data.copy()
        
        # Redactar información financiera sensible
        sensitive_fields = [
            "account_numbers", "transactions", "balances",
            "credit_score", "credit_cards", "bank_accounts",
            "investments", "loans", "debts",
        ]
        
        for field in sensitive_fields:
            if field in filtered and filtered[field]:
                if isinstance(filtered[field], list):
                    filtered[field] = f"[{len(filtered[field])} ITEMS REDACTED]"
                elif isinstance(filtered[field], dict):
                    filtered[field] = "[DATA REDACTED]"
                else:
                    filtered[field] = "[REDACTED]"
        
        # Mantener información agregada/no sensible
        safe_fields = ["currency", "has_account", "account_type"]
        result = {}
        for field in safe_fields:
            if field in filtered:
                result[field] = filtered[field]
        
        result["_financial_data_redacted"] = True
        
        return result
    
    def _filter_commerce_data(
        self,
        data: Dict[str, Any],
        tier: SubscriptionTier,
    ) -> Dict[str, Any]:
        """Filtra datos de comercio específicos."""
        filtered = data.copy()
        
        # Filtrar información de pago
        if "payment_methods" in filtered:
            filtered["payment_methods"] = "[PAYMENT_INFO_REDACTED]"
        
        # Mantener historial de compras pero sin detalles sensibles
        if "purchase_history" in filtered and isinstance(filtered["purchase_history"], list):
            # Mantener solo categorías y fechas
            sanitized_history = []
            for purchase in filtered["purchase_history"][:10]:  # Limitar a 10
                if isinstance(purchase, dict):
                    sanitized_history.append({
                        "category": purchase.get("category"),
                        "date": purchase.get("date"),
                        "store_type": purchase.get("store_type"),
                    })
            filtered["purchase_history"] = sanitized_history
        
        # Mantener preferencias de categorías
        # preferred_categories, favorite_stores son menos sensibles
        
        return filtered
    
    def _filter_logistics_data(
        self,
        data: Dict[str, Any],
        tier: SubscriptionTier,
    ) -> Dict[str, Any]:
        """Filtra datos de logística específicos."""
        filtered = data.copy()
        
        # Generalizar direcciones guardadas
        if "saved_addresses" in filtered and isinstance(filtered["saved_addresses"], list):
            sanitized_addresses = []
            for addr in filtered["saved_addresses"]:
                if isinstance(addr, dict):
                    sanitized_addresses.append({
                        "type": addr.get("type", "address"),
                        "city": addr.get("city"),
                        "country": addr.get("country"),
                    })
            filtered["saved_addresses"] = sanitized_addresses
        
        return filtered
    
    def _filter_travel_data(
        self,
        data: Dict[str, Any],
        tier: SubscriptionTier,
    ) -> Dict[str, Any]:
        """Filtra datos de viajes específicos."""
        filtered = data.copy()
        
        # Redactar números de reservación
        sensitive_fields = ["reservation_numbers", "booking_ids", "ticket_numbers"]
        for field in sensitive_fields:
            if field in filtered:
                filtered[field] = "[REDACTED]"
        
        return filtered
    
    def filter_conversation_context(
        self,
        data: Dict[str, Any],
        tier: SubscriptionTier = SubscriptionTier.FREE,
    ) -> Dict[str, Any]:
        """
        Filtra contexto de conversación.
        
        Mantiene:
        - Intención del usuario
        - Estado del flujo
        - Entidades no sensibles
        
        Redacta:
        - Contenido de mensajes con PII
        - Datos sensibles en entidades
        
        Args:
            data: Datos de conversación
            tier: Nivel de suscripción
            
        Returns:
            Datos de conversación filtrados
        """
        filtered = data.copy()
        
        # Filtrar historial de mensajes
        if "message_history" in filtered and isinstance(filtered["message_history"], list):
            sanitized_history = []
            for msg in filtered["message_history"][-10:]:  # Últimos 10 mensajes
                if isinstance(msg, dict):
                    # Sanitizar contenido del mensaje
                    content = msg.get("content", "")
                    if content:
                        sanitized_content = self.sanitizer.redact_pii(content)
                        sanitized_history.append({
                            "role": msg.get("role"),
                            "content": sanitized_content,
                            "timestamp": msg.get("timestamp"),
                        })
            filtered["message_history"] = sanitized_history
        
        # Filtrar entidades detectadas
        if "detected_entities" in filtered and isinstance(filtered["detected_entities"], dict):
            sanitized_entities = {}
            for entity_type, entity_value in filtered["detected_entities"].items():
                if entity_type in ["email", "phone", "ssn", "credit_card"]:
                    sanitized_entities[entity_type] = "[REDACTED]"
                else:
                    sanitized_entities[entity_type] = entity_value
            filtered["detected_entities"] = sanitized_entities
        
        # Mantener intent, state, etc.
        
        # Marcar como filtrado
        filtered["_sanitized"] = True
        filtered["_sanitized_at"] = datetime.utcnow().isoformat()
        
        return filtered
    
    def filter_device_context(
        self,
        data: Dict[str, Any],
        tier: SubscriptionTier = SubscriptionTier.FREE,
    ) -> Dict[str, Any]:
        """
        Filtra contexto de dispositivo.
        
        Redacta:
        - ID de dispositivo
        - Dirección IP
        
        Mantiene:
        - Tipo de dispositivo
        - Plataforma
        - Capacidades
        
        Args:
            data: Datos del dispositivo
            tier: Nivel de suscripción
            
        Returns:
            Datos de dispositivo filtrados
        """
        filtered = data.copy()
        
        # Redactar device_id
        if "device_id" in filtered:
            filtered["device_id"] = "[DEVICE_ID_REDACTED]"
        
        # Redactar IP
        if "ip_address" in filtered:
            filtered["ip_address"] = "[IP_REDACTED]"
        
        # Mantener información útil para UX
        # device_type, platform, screen_width, etc. son seguros
        
        return filtered
    
    def filter_temporal_context(
        self,
        data: Dict[str, Any],
        tier: SubscriptionTier = SubscriptionTier.FREE,
    ) -> Dict[str, Any]:
        """
        Filtra contexto temporal.
        
        El contexto temporal no contiene datos sensibles,
        pero se mantiene el método para consistencia.
        
        Args:
            data: Datos temporales
            tier: Nivel de suscripción
            
        Returns:
            Datos temporales sin cambios
        """
        # El contexto temporal no contiene datos sensibles
        return data
    
    def filter_solution_context(
        self,
        data: Dict[str, Any],
        tier: SubscriptionTier = SubscriptionTier.FREE,
    ) -> Dict[str, Any]:
        """
        Filtra contexto de solución activa.
        
        Redacta:
        - API keys
        - Tokens
        - Credenciales
        
        Args:
            data: Datos de solución
            tier: Nivel de suscripción
            
        Returns:
            Datos de solución filtrados
        """
        filtered = data.copy()
        
        # Redactar credenciales
        credential_fields = ["api_keys", "credentials", "tokens", "secrets"]
        for field in credential_fields:
            if field in filtered:
                filtered[field] = "[CREDENTIALS_REDACTED]"
        
        return filtered
    
    def filter_horizontal_context(
        self,
        data: Dict[str, Any],
        tier: SubscriptionTier = SubscriptionTier.FREE,
    ) -> Dict[str, Any]:
        """
        Filtra contexto horizontal (cross-solution).
        
        Redacta:
        - Direcciones de wallet
        - Cuentas bancarias
        
        Mantiene:
        - Balance de Energy Points (agregado)
        - Trust Score
        
        Args:
            data: Datos horizontales
            tier: Nivel de suscripción
            
        Returns:
            Datos horizontales filtrados
        """
        filtered = data.copy()
        
        # Redactar wallets
        if "wallet_address" in filtered:
            filtered["wallet_address"] = "[WALLET_REDACTED]"
        
        if "bank_accounts" in filtered:
            filtered["bank_accounts"] = "[BANK_INFO_REDACTED]"
        
        # Energy Points es seguro mantener como aggregate
        # Trust Score también es información no sensible
        
        return filtered
    
    def filter_skills_context(
        self,
        data: Dict[str, Any],
        tier: SubscriptionTier = SubscriptionTier.FREE,
    ) -> Dict[str, Any]:
        """
        Filtra contexto de skills.
        
        El contexto de skills no contiene datos sensibles del usuario.
        
        Args:
            data: Datos de skills
            tier: Nivel de suscripción
            
        Returns:
            Datos de skills sin cambios
        """
        return data
    
    def filter_for_subscription_tier(
        self,
        data: Dict[str, Any],
        tier: SubscriptionTier,
        context_type: str = "personal",
    ) -> Dict[str, Any]:
        """
        Filtra datos según el nivel de suscripción.
        
        Usuarios premium pueden tener acceso a más datos
        sin filtrar según la configuración.
        
        Args:
            data: Datos a filtrar
            tier: Nivel de suscripción
            context_type: Tipo de contexto
            
        Returns:
            Datos filtrados según el tier
        """
        # Ajustar agresividad del filtrado según tier
        tier_filters = {
            SubscriptionTier.FREE: {
                "personal": SanitizationLevel.MAXIMUM,
                "spatial": SanitizationLevel.AGGRESSIVE,
                "vertical": SanitizationLevel.MAXIMUM,
            },
            SubscriptionTier.BASIC: {
                "personal": SanitizationLevel.AGGRESSIVE,
                "spatial": SanitizationLevel.STANDARD,
                "vertical": SanitizationLevel.AGGRESSIVE,
            },
            SubscriptionTier.PRO: {
                "personal": SanitizationLevel.STANDARD,
                "spatial": SanitizationLevel.STANDARD,
                "vertical": SanitizationLevel.STANDARD,
            },
            SubscriptionTier.ENTERPRISE: {
                "personal": SanitizationLevel.STANDARD,
                "spatial": SanitizationLevel.MINIMAL,
                "vertical": SanitizationLevel.STANDARD,
            },
        }
        
        # Obtener nivel para este contexto y tier
        tier_config = tier_filters.get(tier, tier_filters[SubscriptionTier.FREE])
        level = tier_config.get(context_type, SanitizationLevel.STANDARD)
        
        # Actualizar configuración temporalmente
        original_level = self.default_level
        self.sanitizer.level = level
        
        # Aplicar filtro
        filtered = self.filter_context(context_type, data, tier)
        
        # Restaurar nivel original
        self.sanitizer.level = original_level
        
        # Añadir metadata de tier
        filtered["_tier"] = tier.value
        filtered["_sanitization_level"] = level.value
        
        return filtered
    
    def _get_level_for_tier(
        self,
        base_level: SanitizationLevel,
        tier: SubscriptionTier,
    ) -> SanitizationLevel:
        """
        Obtiene el nivel de sanitización ajustado por tier.
        
        Args:
            base_level: Nivel base configurado
            tier: Nivel de suscripción
            
        Returns:
            Nivel ajustado
        """
        # Enterprise puede tener sanitización menos agresiva
        if tier == SubscriptionTier.ENTERPRISE:
            # Reducir un nivel
            level_order = [
                SanitizationLevel.MINIMAL,
                SanitizationLevel.STANDARD,
                SanitizationLevel.AGGRESSIVE,
                SanitizationLevel.MAXIMUM,
            ]
            try:
                idx = level_order.index(base_level)
                if idx > 0:
                    return level_order[idx - 1]
            except ValueError:
                pass
        
        return base_level
    
    def _filter_generic_context(
        self,
        context_type: str,
        data: Dict[str, Any],
        tier: SubscriptionTier,
    ) -> Dict[str, Any]:
        """
        Filtro genérico para tipos de contexto no reconocidos.
        
        Args:
            context_type: Tipo de contexto
            data: Datos a filtrar
            tier: Nivel de suscripción
            
        Returns:
            Datos filtrados con sanitización estándar
        """
        filtered = data.copy()
        
        # Aplicar sanitización estándar a todos los campos de texto
        for key, value in filtered.items():
            if isinstance(value, str):
                # Verificar si parece sensible
                detection = self.sanitizer.detect_sensitive_data(value)
                if detection["has_sensitive"]:
                    filtered[key] = self.sanitizer.redact_pii(value)
        
        return filtered
    
    def get_filter_summary(
        self,
        context_type: str,
    ) -> Dict[str, Any]:
        """
        Obtiene un resumen de las reglas de filtrado para un contexto.
        
        Args:
            context_type: Tipo de contexto
            
        Returns:
            Resumen de reglas de filtrado
        """
        config = self._context_configs.get(context_type)
        
        if not config:
            return {
                "context_type": context_type,
                "found": False,
            }
        
        return {
            "context_type": context_type,
            "found": True,
            "sanitization_level": config.sanitization_level.value,
            "protected_fields": config.protected_fields,
            "excluded_fields": config.excluded_fields,
            "location_precision": config.location_precision if hasattr(config, 'location_precision') else None,
        }
