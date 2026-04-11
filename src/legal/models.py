"""
Sistema de Documentos Legales para RICCO
Términos y Condiciones, Políticas de Privacidad, etc.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import structlog

logger = structlog.get_logger(__name__)


class LegalDocumentType(str, Enum):
    """Tipos de documentos legales"""
    TERMS_CONDITIONS = "terms_conditions"
    PRIVACY_POLICY = "privacy_policy"
    COOKIE_POLICY = "cookie_policy"
    DISCLAIMER = "disclaimer"
    EULA = "eula"
    GDPR_NOTICE = "gdpr_notice"
    AML_POLICY = "aml_policy"  # Anti-Money Laundering
    REFUND_POLICY = "refund_policy"
    ACCEPTABLE_USE = "acceptable_use"


class ConsentStatus(str, Enum):
    """Estado de consentimiento"""
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"


@dataclass
class LegalDocument:
    """Documento legal"""
    id: str
    type: LegalDocumentType
    version: str
    title: str
    content: str
    language: str = "es"
    country: str = "CU"
    effective_date: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True
    summary: Optional[str] = None
    sections: List[Dict[str, str]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "version": self.version,
            "title": self.title,
            "content": self.content,
            "language": self.language,
            "country": self.country,
            "effective_date": self.effective_date.isoformat(),
            "is_active": self.is_active,
            "summary": self.summary,
            "sections": self.sections,
        }


@dataclass
class UserConsent:
    """Consentimiento de usuario"""
    id: str
    user_id: str
    document_type: LegalDocumentType
    document_version: str
    status: ConsentStatus = ConsentStatus.PENDING
    consented_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    withdrawn_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def accept(self, ip_address: str = None, user_agent: str = None):
        """Registra aceptación del consentimiento"""
        self.status = ConsentStatus.ACCEPTED
        self.consented_at = datetime.utcnow()
        self.ip_address = ip_address
        self.user_agent = user_agent
        logger.info(
            "consent_accepted",
            user_id=self.user_id,
            document_type=self.document_type.value,
            version=self.document_version
        )
    
    def withdraw(self):
        """Retira el consentimiento"""
        self.status = ConsentStatus.WITHDRAWN
        self.withdrawn_at = datetime.utcnow()
        logger.info(
            "consent_withdrawn",
            user_id=self.user_id,
            document_type=self.document_type.value
        )
    
    def is_valid(self) -> bool:
        """Verifica si el consentimiento es válido"""
        return self.status == ConsentStatus.ACCEPTED
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "document_type": self.document_type.value,
            "document_version": self.document_version,
            "status": self.status.value,
            "consented_at": self.consented_at.isoformat() if self.consented_at else None,
            "ip_address": self.ip_address,
            "withdrawn_at": self.withdrawn_at.isoformat() if self.withdrawn_at else None,
        }


@dataclass  
class ConsentRecord:
    """Registro de auditoría de consentimientos"""
    id: str
    user_id: str
    action: str  # accepted, rejected, withdrawn, viewed
    document_type: LegalDocumentType
    document_version: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    additional_info: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "document_type": self.document_type.value,
            "document_version": self.document_version,
            "timestamp": self.timestamp.isoformat(),
            "ip_address": self.ip_address,
            "additional_info": self.additional_info,
        }
