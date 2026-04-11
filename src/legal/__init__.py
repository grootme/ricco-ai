"""
Sistema Legal de RICCO
Términos, Condiciones, Privacidad y Consentimientos
"""

from .models import (
    LegalDocumentType,
    ConsentStatus,
    LegalDocument,
    UserConsent,
    ConsentRecord,
)
from .legal_service import LegalService, get_legal_service

__all__ = [
    "LegalDocumentType",
    "ConsentStatus",
    "LegalDocument",
    "UserConsent",
    "ConsentRecord",
    "LegalService",
    "get_legal_service",
]
