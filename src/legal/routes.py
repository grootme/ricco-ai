"""
API Routes para Sistema Legal
Endpoints para documentos legales y consentimientos
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from .models import LegalDocumentType, UserConsent
from .legal_service import get_legal_service

router = APIRouter(prefix="/legal", tags=["Legal"])


class ConsentRequest(BaseModel):
    """Request para registrar consentimiento"""
    user_id: str
    document_type: str
    document_version: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ConsentStatusResponse(BaseModel):
    """Response de estado de consentimientos"""
    user_id: str
    required_consents: Dict[str, bool]
    all_accepted: bool
    pending: list
    last_consent: Optional[str]
    total_records: int


@router.get("/{document_type}")
async def get_legal_document(
    document_type: str,
    language: str = "es",
    country: str = "CU"
):
    """
    Obtiene un documento legal
    
    Args:
        document_type: Tipo de documento (terms_conditions, privacy_policy)
        language: Idioma (es, en)
        country: País (CU, MX, US)
    """
    service = get_legal_service()
    
    try:
        doc_type = LegalDocumentType(document_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de documento inválido: {document_type}"
        )
    
    document = await service.get_latest_document(doc_type, language, country)
    
    if not document:
        raise HTTPException(
            status_code=404,
            detail="Documento no encontrado"
        )
    
    return document.to_dict()


@router.get("/documents/{document_id}")
async def get_document_by_id(document_id: str):
    """Obtiene un documento por su ID"""
    service = get_legal_service()
    document = await service.get_document_by_id(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    
    return document.to_dict()


@router.post("/consent")
async def record_consent(request: Request, consent: ConsentRequest):
    """
    Registra el consentimiento de un usuario
    
    Body:
        - user_id: ID del usuario
        - document_type: Tipo de documento
        - document_version: Versión (opcional, usa la última si no se especifica)
        - metadata: Información adicional
    """
    service = get_legal_service()
    
    try:
        doc_type = LegalDocumentType(consent.document_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de documento inválido: {consent.document_type}"
        )
    
    # Obtener última versión si no se especifica
    version = consent.document_version
    if not version:
        doc = await service.get_latest_document(doc_type)
        if doc:
            version = doc.version
        else:
            version = "1.0.0"
    
    # Obtener IP y User-Agent
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    recorded = await service.record_consent(
        user_id=consent.user_id,
        document_type=doc_type,
        document_version=version,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata=consent.metadata
    )
    
    return {
        "success": True,
        "consent": recorded.to_dict()
    }


@router.get("/consent/status/{user_id}", response_model=ConsentStatusResponse)
async def get_consent_status(user_id: str):
    """
    Obtiene el estado de consentimientos de un usuario
    
    Returns:
        Estado de cada consentimiento requerido
    """
    service = get_legal_service()
    summary = await service.get_consent_summary(user_id)
    return ConsentStatusResponse(**summary)


@router.get("/consents/pending/{user_id}")
async def get_pending_consents(user_id: str):
    """
    Obtiene consentimientos pendientes para un usuario
    
    Returns:
        Lista de documentos que requieren consentimiento
    """
    service = get_legal_service()
    status = await service.check_required_consents(user_id)
    
    pending = []
    for doc_type, accepted in status.items():
        if not accepted:
            doc = await service.get_latest_document(
                LegalDocumentType(doc_type)
            )
            if doc:
                pending.append({
                    "type": doc_type,
                    "title": doc.title,
                    "version": doc.version,
                    "summary": doc.summary
                })
    
    return {
        "user_id": user_id,
        "pending_count": len(pending),
        "pending": pending
    }


@router.get("/consents/history/{user_id}")
async def get_consent_history(
    user_id: str,
    document_type: Optional[str] = None
):
    """
    Obtiene historial de consentimientos de un usuario
    
    Args:
        user_id: ID del usuario
        document_type: Filtrar por tipo (opcional)
    """
    service = get_legal_service()
    
    doc_type = None
    if document_type:
        try:
            doc_type = LegalDocumentType(document_type)
        except ValueError:
            pass
    
    history = await service.get_consent_history(user_id, doc_type)
    
    return {
        "user_id": user_id,
        "count": len(history),
        "records": [r.to_dict() for r in history]
    }


@router.delete("/consent/{user_id}/{document_type}")
async def withdraw_consent(user_id: str, document_type: str):
    """
    Retira un consentimiento
    
    Args:
        user_id: ID del usuario
        document_type: Tipo de documento
    """
    service = get_legal_service()
    
    try:
        doc_type = LegalDocumentType(document_type)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de documento inválido: {document_type}"
        )
    
    consent = await service.withdraw_consent(user_id, doc_type)
    
    if not consent:
        raise HTTPException(
            status_code=404,
            detail="Consentimiento no encontrado"
        )
    
    return {
        "success": True,
        "message": "Consentimiento retirado",
        "consent": consent.to_dict()
    }
