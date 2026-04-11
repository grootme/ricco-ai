"""
RICCO Consent Service
Servicio de gestión de consentimientos de usuario
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
import hashlib
import json

from .models import (
    UserConsent,
    ConsentType,
    ConsentStatus,
    ConsentBatch,
    LegalUpdateNotification,
    DocumentType
)


class ConsentService:
    """Servicio de gestión de consentimientos"""
    
    # Consentimientos requeridos para usar la app
    REQUIRED_CONSENTS = [
        ConsentType.TERMS_REQUIRED,
        ConsentType.PRIVACY_REQUIRED
    ]
    
    # Consentimientos opcionales
    OPTIONAL_CONSENTS = [
        ConsentType.MARKETING_OPTIONAL,
        ConsentType.AI_PERSONALIZATION,
        ConsentType.LOCATION_SERVICES,
        ConsentType.COOKIES_ANALYTICS,
        ConsentType.COOKIES_MARKETING,
        ConsentType.DATA_SHARING_PARTNERS
    ]
    
    def __init__(self):
        self._consents_cache: Dict[str, List[UserConsent]] = {}
        self._notifications_cache: Dict[str, List[LegalUpdateNotification]] = {}
    
    def record_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
        document_id: UUID,
        document_version: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_id: Optional[str] = None,
        app_version: Optional[str] = None,
        platform: Optional[str] = None
    ) -> UserConsent:
        """
        Registra un nuevo consentimiento
        
        Args:
            user_id: ID del usuario
            consent_type: Tipo de consentimiento
            document_id: ID del documento legal aceptado
            document_version: Versión del documento
            ip_address: Dirección IP del usuario
            user_agent: User agent del navegador/app
            device_id: ID del dispositivo
            app_version: Versión de la app
            platform: Plataforma (ios, android, web)
            
        Returns:
            UserConsent registrado
        """
        # Verificar si ya existe un consentimiento previo
        existing = self._get_existing_consent(user_id, consent_type)
        if existing and existing.is_valid():
            # Actualizar el existente
            existing.status = ConsentStatus.GRANTED
            existing.granted_at = datetime.utcnow()
            existing.document_version = document_version
            existing.ip_address = ip_address
            existing.user_agent = user_agent
            existing.device_id = device_id
            existing.app_version = app_version
            existing.platform = platform
            existing.updated_at = datetime.utcnow()
            return existing
        
        # Crear nuevo consentimiento
        consent = UserConsent(
            user_id=user_id,
            consent_type=consent_type,
            document_id=document_id,
            document_version=document_version,
            status=ConsentStatus.GRANTED,
            granted_at=datetime.utcnow(),
            ip_address=ip_address,
            user_agent=user_agent,
            device_id=device_id,
            app_version=app_version,
            platform=platform,
            consent_method="in_app",
            evidence_data=self._generate_evidence(ip_address, user_agent, device_id)
        )
        
        # Guardar en caché
        if user_id not in self._consents_cache:
            self._consents_cache[user_id] = []
        self._consents_cache[user_id].append(consent)
        
        return consent
    
    def record_batch_consent(
        self,
        batch: ConsentBatch,
        document_ids: Dict[str, UUID]
    ) -> List[UserConsent]:
        """
        Registra múltiples consentimientos en lote (flujo inicial)
        
        Args:
            batch: Lote de consentimientos
            document_ids: IDs de documentos por tipo
            
        Returns:
            Lista de UserConsent registrados
        """
        consents = []
        
        # Consentimientos requeridos
        if batch.terms_accepted:
            consent = self.record_consent(
                user_id=batch.user_id,
                consent_type=ConsentType.TERMS_REQUIRED,
                document_id=document_ids.get("terms", uuid4()),
                document_version="1.0.0",
                ip_address=batch.ip_address,
                user_agent=batch.user_agent,
                device_id=batch.device_id,
                app_version=batch.app_version,
                platform=batch.platform
            )
            consents.append(consent)
        
        if batch.privacy_accepted:
            consent = self.record_consent(
                user_id=batch.user_id,
                consent_type=ConsentType.PRIVACY_REQUIRED,
                document_id=document_ids.get("privacy", uuid4()),
                document_version="1.0.0",
                ip_address=batch.ip_address,
                user_agent=batch.user_agent,
                device_id=batch.device_id,
                app_version=batch.app_version,
                platform=batch.platform
            )
            consents.append(consent)
        
        # Consentimientos opcionales
        if batch.marketing_accepted:
            consent = self.record_consent(
                user_id=batch.user_id,
                consent_type=ConsentType.MARKETING_OPTIONAL,
                document_id=document_ids.get("marketing", uuid4()),
                document_version="1.0.0",
                ip_address=batch.ip_address,
                user_agent=batch.user_agent,
                device_id=batch.device_id,
                app_version=batch.app_version,
                platform=batch.platform
            )
            consents.append(consent)
        
        if batch.ai_personalization_accepted:
            consent = self.record_consent(
                user_id=batch.user_id,
                consent_type=ConsentType.AI_PERSONALIZATION,
                document_id=document_ids.get("ai", uuid4()),
                document_version="1.0.0",
                ip_address=batch.ip_address,
                user_agent=batch.user_agent,
                device_id=batch.device_id,
                app_version=batch.app_version,
                platform=batch.platform
            )
            consents.append(consent)
        
        if batch.location_accepted:
            consent = self.record_consent(
                user_id=batch.user_id,
                consent_type=ConsentType.LOCATION_SERVICES,
                document_id=document_ids.get("location", uuid4()),
                document_version="1.0.0",
                ip_address=batch.ip_address,
                user_agent=batch.user_agent,
                device_id=batch.device_id,
                app_version=batch.app_version,
                platform=batch.platform
            )
            consents.append(consent)
        
        if batch.cookies_analytics_accepted:
            consent = self.record_consent(
                user_id=batch.user_id,
                consent_type=ConsentType.COOKIES_ANALYTICS,
                document_id=document_ids.get("cookies", uuid4()),
                document_version="1.0.0",
                ip_address=batch.ip_address,
                user_agent=batch.user_agent,
                device_id=batch.device_id,
                app_version=batch.app_version,
                platform=batch.platform
            )
            consents.append(consent)
        
        if batch.cookies_marketing_accepted:
            consent = self.record_consent(
                user_id=batch.user_id,
                consent_type=ConsentType.COOKIES_MARKETING,
                document_id=document_ids.get("cookies_marketing", uuid4()),
                document_version="1.0.0",
                ip_address=batch.ip_address,
                user_agent=batch.user_agent,
                device_id=batch.device_id,
                app_version=batch.app_version,
                platform=batch.platform
            )
            consents.append(consent)
        
        return consents
    
    def withdraw_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
        reason: Optional[str] = None
    ) -> Optional[UserConsent]:
        """
        Retira un consentimiento previamente otorgado
        
        Args:
            user_id: ID del usuario
            consent_type: Tipo de consentimiento a retirar
            reason: Razón del retiro (opcional)
            
        Returns:
            UserConsent actualizado o None si no existe
        """
        consent = self._get_existing_consent(user_id, consent_type)
        if not consent:
            return None
        
        consent.status = ConsentStatus.WITHDRAWN
        consent.withdrawn_at = datetime.utcnow()
        consent.updated_at = datetime.utcnow()
        
        if reason:
            if not consent.evidence_data:
                consent.evidence_data = {}
            consent.evidence_data["withdrawal_reason"] = reason
        
        return consent
    
    def get_user_consents(self, user_id: str) -> List[UserConsent]:
        """Obtiene todos los consentimientos de un usuario"""
        return self._consents_cache.get(user_id, [])
    
    def get_consent_status(
        self,
        user_id: str,
        consent_type: ConsentType
    ) -> Optional[ConsentStatus]:
        """Obtiene el estado de un consentimiento específico"""
        consent = self._get_existing_consent(user_id, consent_type)
        if not consent:
            return None
        return consent.status if consent.is_valid() else ConsentStatus.EXPIRED
    
    def has_required_consents(self, user_id: str) -> bool:
        """Verifica si el usuario tiene todos los consentimientos requeridos"""
        for consent_type in self.REQUIRED_CONSENTS:
            consent = self._get_existing_consent(user_id, consent_type)
            if not consent or not consent.is_valid():
                return False
        return True
    
    def get_missing_consents(self, user_id: str) -> List[ConsentType]:
        """Obtiene lista de consentimientos faltantes"""
        missing = []
        for consent_type in self.REQUIRED_CONSENTS:
            consent = self._get_existing_consent(user_id, consent_type)
            if not consent or not consent.is_valid():
                missing.append(consent_type)
        return missing
    
    def get_consent_summary(self, user_id: str) -> Dict[str, Any]:
        """Obtiene resumen del estado de consentimientos"""
        all_consents = self.get_user_consents(user_id)
        
        summary = {
            "required": {},
            "optional": {},
            "all_accepted": True,
            "last_updated": None
        }
        
        # Procesar consentimientos
        for consent_type in ConsentType:
            consent = self._get_existing_consent(user_id, consent_type)
            
            status_info = {
                "accepted": consent.is_valid() if consent else False,
                "granted_at": consent.granted_at.isoformat() if consent and consent.granted_at else None,
                "version": consent.document_version if consent else None
            }
            
            if consent_type in self.REQUIRED_CONSENTS:
                summary["required"][consent_type.value] = status_info
                if not status_info["accepted"]:
                    summary["all_accepted"] = False
            else:
                summary["optional"][consent_type.value] = status_info
            
            # Actualizar última modificación
            if consent and consent.updated_at:
                if not summary["last_updated"] or consent.updated_at > datetime.fromisoformat(summary["last_updated"]):
                    summary["last_updated"] = consent.updated_at.isoformat()
        
        return summary
    
    def notify_legal_update(
        self,
        user_id: str,
        document_type: DocumentType,
        old_version: str,
        new_version: str,
        requires_reconsent: bool = False
    ) -> LegalUpdateNotification:
        """Notifica a un usuario sobre actualización legal"""
        notification = LegalUpdateNotification(
            user_id=user_id,
            document_type=document_type,
            old_version=old_version,
            new_version=new_version,
            reconsent_required=requires_reconsent,
            notification_sent=False
        )
        
        if user_id not in self._notifications_cache:
            self._notifications_cache[user_id] = []
        self._notifications_cache[user_id].append(notification)
        
        return notification
    
    def get_pending_reconsents(self, user_id: str) -> List[LegalUpdateNotification]:
        """Obtiene notificaciones pendientes de re-consentimiento"""
        notifications = self._notifications_cache.get(user_id, [])
        return [
            n for n in notifications
            if n.reconsent_required and not n.reconsent_given
        ]
    
    def _get_existing_consent(
        self,
        user_id: str,
        consent_type: ConsentType
    ) -> Optional[UserConsent]:
        """Obtiene el consentimiento más reciente de un tipo"""
        consents = self._consents_cache.get(user_id, [])
        
        matching = [
            c for c in consents
            if c.consent_type == consent_type
        ]
        
        if not matching:
            return None
        
        # Retornar el más reciente
        return max(matching, key=lambda c: c.updated_at)
    
    def _generate_evidence(
        self,
        ip_address: Optional[str],
        user_agent: Optional[str],
        device_id: Optional[str]
    ) -> Dict[str, Any]:
        """Genera evidencia del consentimiento"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "ip_hash": hashlib.sha256(ip_address.encode()).hexdigest()[:16] if ip_address else None,
            "user_agent": user_agent,
            "device_id": device_id,
            "consent_flow_version": "1.0"
        }
    
    def get_consent_history(
        self,
        user_id: str,
        consent_type: Optional[ConsentType] = None
    ) -> List[Dict[str, Any]]:
        """Obtiene historial de consentimientos"""
        consents = self.get_user_consents(user_id)
        
        if consent_type:
            consents = [c for c in consents if c.consent_type == consent_type]
        
        return [
            {
                "id": str(c.id),
                "type": c.consent_type,
                "status": c.status,
                "document_version": c.document_version,
                "granted_at": c.granted_at.isoformat() if c.granted_at else None,
                "withdrawn_at": c.withdrawn_at.isoformat() if c.withdrawn_at else None,
                "platform": c.platform,
                "app_version": c.app_version
            }
            for c in sorted(consents, key=lambda x: x.updated_at, reverse=True)
        ]
