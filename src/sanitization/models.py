"""
Modelos de Sanitización para RICCO AI
Definiciones de tipos de datos sensibles y reglas de sanitización

Este módulo define los modelos de datos utilizados por el sistema
de sanitización para clasificar y proteger información sensible.

Autor: RICCO AI Team
Mercado objetivo: Cuba y América Latina
"""

from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any, Set
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class SensitiveDataType(str, Enum):
    """
    Tipos de datos sensibles que el sistema puede detectar y sanitizar.
    
    Cada tipo representa una categoría de información que debe ser
    protegida antes de enviarla a modelos de IA o bundles de contexto.
    
    Attributes:
        CREDIT_CARD: Números de tarjetas de crédito/débito
        SSN: Números de seguro social (SSN, CI cubano, etc.)
        EMAIL: Direcciones de correo electrónico
        PHONE: Números telefónicos
        PASSWORD: Contraseñas y secretos
        API_KEY: Claves API y tokens de autenticación
        BANK_ACCOUNT: Números de cuenta bancaria
        CRYPTO_ADDRESS: Direcciones de criptomonedas (BTC, ETH, etc.)
        MEDICAL_RECORD: Registros médicos e información de salud
        GOVERNMENT_ID: Documentos de identidad (pasaportes, licencias)
        LOCATION_EXACT: Coordenadas GPS exactas
        FINANCIAL_DATA: Datos financieros detallados
        BIOMETRIC: Datos biométricos (huellas, reconocimiento facial)
    """
    CREDIT_CARD = "credit_card"
    SSN = "ssn"
    EMAIL = "email"
    PHONE = "phone"
    PASSWORD = "password"
    API_KEY = "api_key"
    BANK_ACCOUNT = "bank_account"
    CRYPTO_ADDRESS = "crypto_address"
    MEDICAL_RECORD = "medical_record"
    GOVERNMENT_ID = "government_id"
    LOCATION_EXACT = "location_exact"
    FINANCIAL_DATA = "financial_data"
    BIOMETRIC = "biometric"
    
    def get_display_name(self) -> str:
        """Retorna el nombre para mostrar en la interfaz."""
        display_names = {
            SensitiveDataType.CREDIT_CARD: "Tarjeta de Crédito",
            SensitiveDataType.SSN: "Número de Identificación",
            SensitiveDataType.EMAIL: "Correo Electrónico",
            SensitiveDataType.PHONE: "Número Telefónico",
            SensitiveDataType.PASSWORD: "Contraseña",
            SensitiveDataType.API_KEY: "Clave API",
            SensitiveDataType.BANK_ACCOUNT: "Cuenta Bancaria",
            SensitiveDataType.CRYPTO_ADDRESS: "Dirección Cripto",
            SensitiveDataType.MEDICAL_RECORD: "Registro Médico",
            SensitiveDataType.GOVERNMENT_ID: "Documento de Identidad",
            SensitiveDataType.LOCATION_EXACT: "Ubicación Exacta",
            SensitiveDataType.FINANCIAL_DATA: "Datos Financieros",
            SensitiveDataType.BIOMETRIC: "Dato Biométrico",
        }
        return display_names[self]
    
    def get_risk_level(self) -> str:
        """
        Retorna el nivel de riesgo del tipo de dato.
        
        Returns:
            'critical': Información extremadamente sensible
            'high': Información muy sensible
            'medium': Información moderadamente sensible
            'low': Información poco sensible
        """
        risk_levels = {
            SensitiveDataType.CREDIT_CARD: "critical",
            SensitiveDataType.SSN: "critical",
            SensitiveDataType.PASSWORD: "critical",
            SensitiveDataType.API_KEY: "critical",
            SensitiveDataType.BANK_ACCOUNT: "critical",
            SensitiveDataType.CRYPTO_ADDRESS: "high",
            SensitiveDataType.MEDICAL_RECORD: "critical",
            SensitiveDataType.GOVERNMENT_ID: "high",
            SensitiveDataType.LOCATION_EXACT: "high",
            SensitiveDataType.FINANCIAL_DATA: "high",
            SensitiveDataType.BIOMETRIC: "critical",
            SensitiveDataType.EMAIL: "medium",
            SensitiveDataType.PHONE: "medium",
        }
        return risk_levels[self]
    
    def get_regulations(self) -> List[str]:
        """
        Retorna las regulaciones aplicables a este tipo de dato.
        
        Returns:
            Lista de regulaciones (GDPR, CCPA, HIPAA, etc.)
        """
        regulations_map = {
            SensitiveDataType.CREDIT_CARD: ["PCI-DSS", "GDPR"],
            SensitiveDataType.SSN: ["GDPR", "CCPA", "Ley de Protección de Datos"],
            SensitiveDataType.EMAIL: ["GDPR", "CAN-SPAM"],
            SensitiveDataType.PHONE: ["GDPR", "TCPA"],
            SensitiveDataType.PASSWORD: ["GDPR", "SOC2"],
            SensitiveDataType.API_KEY: ["SOC2", "ISO27001"],
            SensitiveDataType.BANK_ACCOUNT: ["PCI-DSS", "GDPR", "PSD2"],
            SensitiveDataType.CRYPTO_ADDRESS: ["AML", "KYC", "GDPR"],
            SensitiveDataType.MEDICAL_RECORD: ["HIPAA", "GDPR", "Ley de Salud"],
            SensitiveDataType.GOVERNMENT_ID: ["GDPR", "KYC", "AML"],
            SensitiveDataType.LOCATION_EXACT: ["GDPR", "CCPA"],
            SensitiveDataType.FINANCIAL_DATA: ["PCI-DSS", "GDPR", "SOX"],
            SensitiveDataType.BIOMETRIC: ["BIPA", "GDPR", "CCPA"],
        }
        return regulations_map.get(self, ["GDPR"])


class DataClassification(str, Enum):
    """
    Clasificación de nivel de sensibilidad de los datos.
    
    Determina cómo deben ser tratados los datos en términos de
    acceso, almacenamiento y transmisión.
    
    Attributes:
        PUBLIC: Datos públicos, sin restricciones
        INTERNAL: Datos internos, uso dentro de la organización
        CONFIDENTIAL: Datos confidenciales, acceso restringido
        RESTRICTED: Datos restringidos, máximo nivel de protección
    """
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"
    
    def get_description(self) -> str:
        """Retorna la descripción de la clasificación."""
        descriptions = {
            DataClassification.PUBLIC: "Información pública sin restricciones de acceso",
            DataClassification.INTERNAL: "Información para uso interno de la organización",
            DataClassification.CONFIDENTIAL: "Información confidencial con acceso restringido",
            DataClassification.RESTRICTED: "Información altamente sensible con acceso muy limitado",
        }
        return descriptions[self]


class SanitizationLevel(str, Enum):
    """
    Nivel de sanitización a aplicar.
    
    Determina qué tan agresiva es la sanitización aplicada
    a los datos sensibles.
    
    Attributes:
        MINIMAL: Sanitización mínima, solo datos críticos
        STANDARD: Sanitización estándar, datos críticos y altos
        AGGRESSIVE: Sanitización agresiva, incluye datos medios
        MAXIMUM: Sanitización máxima, todos los datos sensibles
    """
    MINIMAL = "minimal"
    STANDARD = "standard"
    AGGRESSIVE = "aggressive"
    MAXIMUM = "maximum"
    
    def get_risk_threshold(self) -> List[str]:
        """
        Retorna los niveles de riesgo a sanitizar.
        
        Returns:
            Lista de niveles de riesgo a incluir
        """
        thresholds = {
            SanitizationLevel.MINIMAL: ["critical"],
            SanitizationLevel.STANDARD: ["critical", "high"],
            SanitizationLevel.AGGRESSIVE: ["critical", "high", "medium"],
            SanitizationLevel.MAXIMUM: ["critical", "high", "medium", "low"],
        }
        return thresholds[self]


class SanitizationRule(BaseModel):
    """
    Regla de sanitización para un tipo específico de dato sensible.
    
    Define cómo detectar y reemplazar un tipo de dato sensible
    en el texto procesado por el sistema.
    
    Attributes:
        id: Identificador único de la regla
        name: Nombre descriptivo de la regla
        data_type: Tipo de dato sensible que detecta
        pattern: Patrón regex para detectar el dato
        replacement: Plantilla de reemplazo (puede usar $1, $2, etc.)
        enabled: Si la regla está activa
        risk_level: Nivel de riesgo del dato
        classification: Clasificación de datos aplicable
        priority: Prioridad de aplicación (mayor = más importante)
        languages: Idiomas soportados por la regla
        countries: Países donde aplica el formato
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    data_type: SensitiveDataType
    pattern: str
    replacement: str = "[REDACTED]"
    enabled: bool = True
    risk_level: str = "high"
    classification: DataClassification = DataClassification.CONFIDENTIAL
    priority: int = 100
    
    # Soporte multilingüe
    languages: List[str] = Field(default_factory=lambda: ["es", "en"])
    countries: List[str] = Field(default_factory=lambda: ["CU", "US", "MX", "ES"])
    
    # Metadatos
    description: Optional[str] = None
    examples: List[str] = Field(default_factory=list)
    
    # Configuración de reemplazo
    preserve_format: bool = False  # Mantener formato original
    partial_redaction: bool = False  # Redacción parcial (ej: j***@example.com)
    redaction_char: str = "*"
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True
    
    def should_apply(self, level: SanitizationLevel) -> bool:
        """
        Determina si esta regla debe aplicarse según el nivel de sanitización.
        
        Args:
            level: Nivel de sanitización solicitado
            
        Returns:
            True si la regla debe aplicarse
        """
        if not self.enabled:
            return False
        
        risk_threshold = level.get_risk_threshold()
        return self.risk_level in risk_threshold


class SanitizationResult(BaseModel):
    """
    Resultado de una operación de sanitización.
    
    Contiene el texto original, el texto sanitizado y
    estadísticas sobre los datos detectados y redactados.
    
    Attributes:
        id: Identificador único del resultado
        original: Texto original antes de sanitizar
        sanitized: Texto después de sanitizar
        redacted_count: Número total de redacciones
        detected_types: Tipos de datos sensibles detectados
        redactions: Lista de redacciones realizadas
        classification: Clasificación final del contenido
        processing_time_ms: Tiempo de procesamiento en milisegundos
    """
    id: UUID = Field(default_factory=uuid4)
    original: str
    sanitized: str
    redacted_count: int = 0
    detected_types: Set[SensitiveDataType] = Field(default_factory=set)
    redactions: List[Dict[str, Any]] = Field(default_factory=list)
    classification: DataClassification = DataClassification.PUBLIC
    processing_time_ms: float = 0.0
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    rules_applied: List[str] = Field(default_factory=list)
    
    class Config:
        use_enum_values = True
    
    def add_redaction(
        self,
        data_type: SensitiveDataType,
        original_value: str,
        redacted_value: str,
        position: tuple,
        rule_id: str
    ) -> None:
        """
        Añade una redacción al resultado.
        
        Args:
            data_type: Tipo de dato redactado
            original_value: Valor original
            redacted_value: Valor después de redactar
            position: Tupla (start, end) con la posición en el texto
            rule_id: ID de la regla aplicada
        """
        self.redactions.append({
            "data_type": data_type.value if isinstance(data_type, SensitiveDataType) else data_type,
            "original_length": len(original_value),
            "redacted_value": redacted_value,
            "position": position,
            "rule_id": rule_id,
        })
        self.detected_types.add(data_type)
        self.redacted_count += 1
    
    def get_redaction_summary(self) -> Dict[str, int]:
        """
        Retorna un resumen de redacciones por tipo.
        
        Returns:
            Diccionario con conteo por tipo de dato
        """
        summary: Dict[str, int] = {}
        for redaction in self.redactions:
            data_type = redaction["data_type"]
            summary[data_type] = summary.get(data_type, 0) + 1
        return summary
    
    def has_sensitive_data(self) -> bool:
        """
        Verifica si se detectaron datos sensibles.
        
        Returns:
            True si se detectaron datos sensibles
        """
        return self.redacted_count > 0
    
    def get_highest_risk(self) -> Optional[str]:
        """
        Obtiene el nivel de riesgo más alto detectado.
        
        Returns:
            Nivel de riesgo más alto o None si no hay datos sensibles
        """
        if not self.detected_types:
            return None
        
        risk_order = ["critical", "high", "medium", "low"]
        for risk in risk_order:
            for dt in self.detected_types:
                if dt.get_risk_level() == risk:
                    return risk
        return None


class ContextSanitizationConfig(BaseModel):
    """
    Configuración de sanitización por tipo de contexto.
    
    Define qué reglas aplicar para cada tipo de contexto
    en el sistema de bundles de contexto de RICCO AI.
    
    Attributes:
        id: Identificador único de la configuración
        context_type: Tipo de contexto al que aplica
        enabled_rules: Reglas habilitadas para este contexto
        disabled_rules: Reglas deshabilitadas para este contexto
        sanitization_level: Nivel de sanitización para este contexto
        custom_replacements: Reemplazos personalizados
    """
    id: UUID = Field(default_factory=uuid4)
    context_type: str  # ContextType value
    enabled_rules: List[str] = Field(default_factory=list)
    disabled_rules: List[str] = Field(default_factory=list)
    sanitization_level: SanitizationLevel = SanitizationLevel.STANDARD
    
    # Configuración específica por tipo de contexto
    custom_replacements: Dict[str, str] = Field(default_factory=dict)
    
    # Campos específicos a proteger
    protected_fields: List[str] = Field(default_factory=list)
    
    # Campos a excluir de sanitización
    excluded_fields: List[str] = Field(default_factory=list)
    
    # Configuración de ubicación
    location_precision: str = "city"  # exact, city, region, country
    location_redact_coords: bool = True
    
    # Metadatos
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = True
    
    def get_sanitization_level_for_field(self, field_name: str) -> SanitizationLevel:
        """
        Obtiene el nivel de sanitización para un campo específico.
        
        Args:
            field_name: Nombre del campo
            
        Returns:
            Nivel de sanitización aplicable
        """
        if field_name in self.excluded_fields:
            return SanitizationLevel.MINIMAL
        if field_name in self.protected_fields:
            return SanitizationLevel.MAXIMUM
        return self.sanitization_level


class SanitizationAuditRecord(BaseModel):
    """
    Registro de auditoría para operaciones de sanitización.
    
    Almacena información sobre cada operación de sanitización
    para cumplimiento normativo y análisis de seguridad.
    
    Attributes:
        id: Identificador único del registro
        user_id: ID del usuario que originó la operación
        session_id: ID de la sesión
        operation_type: Tipo de operación realizada
        data_types_detected: Tipos de datos sensibles detectados
        redaction_count: Número de redacciones realizadas
        context_type: Tipo de contexto procesado
        destination: Destino de los datos (AI model, context bundle, etc.)
        timestamp: Marca de tiempo de la operación
    """
    id: UUID = Field(default_factory=uuid4)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    operation_type: str  # sanitize, detect, tokenize
    data_types_detected: List[str] = Field(default_factory=list)
    redaction_count: int = 0
    context_type: Optional[str] = None
    destination: str = "unknown"  # ai_model, context_bundle, api_response
    
    # Información adicional
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    
    # Compliance
    regulations_applicable: List[str] = Field(default_factory=list)
    compliance_notes: Optional[str] = None
    
    # Timestamps
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    processing_time_ms: float = 0.0
    
    class Config:
        use_enum_values = True
    
    def to_compliance_report(self) -> Dict[str, Any]:
        """
        Genera un reporte de cumplimiento a partir del registro.
        
        Returns:
            Diccionario con información de cumplimiento
        """
        return {
            "record_id": str(self.id),
            "timestamp": self.timestamp.isoformat(),
            "operation": self.operation_type,
            "data_types": self.data_types_detected,
            "redaction_count": self.redaction_count,
            "regulations": self.regulations_applicable,
            "destination": self.destination,
        }


class TokenizedData(BaseModel):
    """
    Datos tokenizados para recuperación posterior.
    
    Permite reemplazar datos sensibles con tokens que pueden
    ser recuperados posteriormente si es necesario.
    
    Attributes:
        token: Token único para identificar los datos
        original_data: Datos originales cifrados
        data_type: Tipo de dato sensible
        created_at: Fecha de creación
        expires_at: Fecha de expiración
    """
    token: str = Field(default_factory=lambda: str(uuid4()))
    original_data: str  # Datos cifrados
    data_type: SensitiveDataType
    encryption_key_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    # Metadata
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    class Config:
        use_enum_values = True
    
    def is_expired(self) -> bool:
        """Verifica si el token ha expirado."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
