"""
Servicio de Gestión Legal
Manejo de documentos legales y consentimientos
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid
import structlog

from .models import (
    LegalDocumentType,
    ConsentStatus,
    LegalDocument,
    UserConsent,
    ConsentRecord,
)

# Import templates
from .templates.terms_conditions import TERMS_CONDITIONS
from .templates.privacy_policy import PRIVACY_POLICIES

logger = structlog.get_logger(__name__)


class LegalService:
    """
    Servicio de gestión de documentos legales
    
    Maneja términos, condiciones, políticas de privacidad
    y registro de consentimientos de usuarios.
    """
    
    def __init__(self, db=None):
        self.db = db
        self._documents_cache: Dict[str, LegalDocument] = {}
        self._consents: Dict[str, UserConsent] = {}
        self._consent_records: List[ConsentRecord] = []
        self._initialize_default_documents()
    
    def _initialize_default_documents(self):
        """Inicializa documentos legales por defecto"""
        # Términos y Condiciones
        for locale, content in TERMS_CONDITIONS.items():
            lang, country = locale.split("_")
            doc = LegalDocument(
                id=f"terms_{locale}_1.0.0",
                type=LegalDocumentType.TERMS_CONDITIONS,
                version="1.0.0",
                title=f"Términos y Condiciones - {country}",
                content=content,
                language=lang,
                country=country,
                effective_date=datetime(2024, 1, 1),
                is_active=True,
                summary="Términos y condiciones de uso de la plataforma RICCO",
            )
            self._documents_cache[doc.id] = doc
        
        # Políticas de Privacidad
        for locale, content in PRIVACY_POLICIES.items():
            lang, country = locale.split("_")
            doc = LegalDocument(
                id=f"privacy_{locale}_1.0.0",
                type=LegalDocumentType.PRIVACY_POLICY,
                version="1.0.0",
                title=f"Política de Privacidad - {country}",
                content=content,
                language=lang,
                country=country,
                effective_date=datetime(2024, 1, 1),
                is_active=True,
                summary="Política de privacidad y tratamiento de datos",
            )
            self._documents_cache[doc.id] = doc
        
        logger.info("legal_documents_initialized", count=len(self._documents_cache))
    
    async def get_latest_document(
        self,
        document_type: LegalDocumentType,
        language: str = "es",
        country: str = "CU"
    ) -> Optional[LegalDocument]:
        """
        Obtiene la versión más reciente de un documento legal
        
        Args:
            document_type: Tipo de documento
            language: Código de idioma (es, en)
            country: Código de país (CU, MX, US)
            
        Returns:
            Documento legal más reciente
        """
        locale = f"{language}_{country}"
        
        # Buscar en cache
        for doc in self._documents_cache.values():
            if (doc.type == document_type and 
                doc.language == language and 
                doc.country == country and 
                doc.is_active):
                return doc
        
        # Fallback a español si no hay en el idioma solicitado
        if language != "es":
            return await self.get_latest_document(document_type, "es", country)
        
        # Fallback a Cuba si no hay para el país
        if country != "CU":
            return await self.get_latest_document(document_type, language, "CU")
        
        return None
    
    async def get_document_by_id(self, document_id: str) -> Optional[LegalDocument]:
        """Obtiene un documento por su ID"""
        return self._documents_cache.get(document_id)
    
    async def record_consent(
        self,
        user_id: str,
        document_type: LegalDocumentType,
        document_version: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UserConsent:
        """
        Registra el consentimiento de un usuario
        
        Args:
            user_id: ID del usuario
            document_type: Tipo de documento aceptado
            document_version: Versión del documento
            ip_address: Dirección IP desde donde aceptó
            user_agent: User agent del navegador
            metadata: Información adicional
            
        Returns:
            Registro de consentimiento
        """
        consent_id = f"consent_{user_id}_{document_type.value}_{uuid.uuid4().hex[:8]}"
        
        consent = UserConsent(
            id=consent_id,
            user_id=user_id,
            document_type=document_type,
            document_version=document_version,
            status=ConsentStatus.PENDING,
            metadata=metadata or {}
        )
        
        # Registrar aceptación
        consent.accept(ip_address, user_agent)
        
        # Guardar
        self._consents[consent_id] = consent
        
        # Registrar en auditoría
        record = ConsentRecord(
            id=f"record_{uuid.uuid4().hex}",
            user_id=user_id,
            action="accepted",
            document_type=document_type,
            document_version=document_version,
            ip_address=ip_address,
            user_agent=user_agent,
            additional_info=metadata or {}
        )
        self._consent_records.append(record)
        
        logger.info(
            "consent_recorded",
            user_id=user_id,
            document_type=document_type.value,
            version=document_version
        )
        
        return consent
    
    async def has_user_consented(
        self,
        user_id: str,
        document_type: LegalDocumentType,
        min_version: Optional[str] = None
    ) -> bool:
        """
        Verifica si un usuario ha consentido un documento
        
        Args:
            user_id: ID del usuario
            document_type: Tipo de documento
            min_version: Versión mínima requerida
            
        Returns:
            True si el usuario ha consentido
        """
        for consent in self._consents.values():
            if (consent.user_id == user_id and 
                consent.document_type == document_type and
                consent.is_valid()):
                
                if min_version:
                    # Verificar versión
                    if consent.document_version >= min_version:
                        return True
                else:
                    return True
        
        return False
    
    async def get_user_consents(self, user_id: str) -> List[UserConsent]:
        """Obtiene todos los consentimientos de un usuario"""
        return [
            c for c in self._consents.values()
            if c.user_id == user_id
        ]
    
    async def get_consent_history(
        self,
        user_id: str,
        document_type: Optional[LegalDocumentType] = None
    ) -> List[ConsentRecord]:
        """
        Obtiene el historial de consentimientos de un usuario
        
        Args:
            user_id: ID del usuario
            document_type: Filtrar por tipo (opcional)
            
        Returns:
            Lista de registros de consentimiento
        """
        records = [
            r for r in self._consent_records
            if r.user_id == user_id
        ]
        
        if document_type:
            records = [r for r in records if r.document_type == document_type]
        
        return sorted(records, key=lambda r: r.timestamp, reverse=True)
    
    async def check_required_consents(
        self,
        user_id: str
    ) -> Dict[str, bool]:
        """
        Verifica qué consentimientos faltan
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Diccionario con estado de cada tipo de consentimiento
        """
        required = [
            LegalDocumentType.TERMS_CONDITIONS,
            LegalDocumentType.PRIVACY_POLICY,
        ]
        
        status = {}
        for doc_type in required:
            status[doc_type.value] = await self.has_user_consented(user_id, doc_type)
        
        return status
    
    async def withdraw_consent(
        self,
        user_id: str,
        document_type: LegalDocumentType
    ) -> Optional[UserConsent]:
        """
        Retira un consentimiento
        
        Args:
            user_id: ID del usuario
            document_type: Tipo de documento
            
        Returns:
            Consentimiento retirado o None si no existía
        """
        for consent in self._consents.values():
            if (consent.user_id == user_id and 
                consent.document_type == document_type and
                consent.is_valid()):
                
                consent.withdraw()
                
                # Registrar en auditoría
                record = ConsentRecord(
                    id=f"record_{uuid.uuid4().hex}",
                    user_id=user_id,
                    action="withdrawn",
                    document_type=document_type,
                    document_version=consent.document_version,
                )
                self._consent_records.append(record)
                
                return consent
        
        return None
    
    async def get_consent_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Obtiene resumen de estado de consentimientos
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Resumen de consentimientos
        """
        required_status = await self.check_required_consents(user_id)
        history = await self.get_consent_history(user_id)
        
        return {
            "user_id": user_id,
            "required_consents": required_status,
            "all_accepted": all(required_status.values()),
            "pending": [
                k for k, v in required_status.items() if not v
            ],
            "last_consent": history[0].timestamp.isoformat() if history else None,
            "total_records": len(history),
        }


# Singleton
_legal_service: Optional[LegalService] = None

def get_legal_service() -> LegalService:
    """Obtiene la instancia singleton del servicio legal"""
    global _legal_service
    if _legal_service is None:
        _legal_service = LegalService()
    return _legal_service
