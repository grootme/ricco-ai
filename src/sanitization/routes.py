"""
Rutas API de Sanitización para RICCO AI
Endpoints REST para el sistema de sanitización

Este módulo define los endpoints de la API para interactuar
con el sistema de sanitización de datos sensibles.

Autor: RICCO AI Team
Mercado objetivo: Cuba y América Latina
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from fastapi import (
    APIRouter,
    HTTPException,
    Depends,
    Request,
    BackgroundTasks,
    Query,
    Body,
)
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from structlog import get_logger

from .models import (
    SensitiveDataType,
    SanitizationRule,
    SanitizationResult,
    SanitizationLevel,
    DataClassification,
)
from .sanitizer import SensitiveDataSanitizer
from .context_filter import ContextDataFilter, SubscriptionTier
from .audit import SanitizationAuditLogger

logger = get_logger(__name__)

# Crear router
router = APIRouter(
    prefix="/sanitization",
    tags=["sanitization"],
    responses={
        404: {"description": "Not found"},
        400: {"description": "Bad request"},
        500: {"description": "Internal server error"},
    },
)


# ============================================
# Modelos de Request/Response
# ============================================

class CheckRequest(BaseModel):
    """Request para verificar texto sensible."""
    text: str = Field(..., description="Texto a verificar")
    include_metadata: bool = Field(
        default=True,
        description="Incluir metadata de cada detección"
    )


class SanitizeRequest(BaseModel):
    """Request para sanitizar texto."""
    text: str = Field(..., description="Texto a sanitizar")
    level: SanitizationLevel = Field(
        default=SanitizationLevel.STANDARD,
        description="Nivel de sanitización"
    )
    rules: Optional[List[str]] = Field(
        default=None,
        description="IDs de reglas específicas a aplicar"
    )
    user_id: Optional[str] = Field(
        default=None,
        description="ID del usuario (para auditoría)"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="ID de la sesión"
    )
    destination: str = Field(
        default="api_response",
        description="Destino de los datos sanitizados"
    )


class TokenizeRequest(BaseModel):
    """Request para tokenizar texto."""
    text: str = Field(..., description="Texto a tokenizar")
    expires_in_hours: int = Field(
        default=24,
        ge=1,
        le=168,
        description="Horas hasta expiración del token"
    )
    user_id: Optional[str] = Field(default=None)
    session_id: Optional[str] = Field(default=None)


class RecoverRequest(BaseModel):
    """Request para recuperar texto tokenizado."""
    text: str = Field(..., description="Texto tokenizado")
    token_map: Dict[str, str] = Field(..., description="Mapeo de tokens")


class FilterContextRequest(BaseModel):
    """Request para filtrar contexto."""
    context_type: str = Field(..., description="Tipo de contexto")
    data: Dict[str, Any] = Field(..., description="Datos a filtrar")
    tier: SubscriptionTier = Field(
        default=SubscriptionTier.FREE,
        description="Nivel de suscripción"
    )


class UpdateRuleRequest(BaseModel):
    """Request para actualizar una regla."""
    rule_id: str = Field(..., description="ID de la regla")
    enabled: Optional[bool] = Field(default=None)
    pattern: Optional[str] = Field(default=None)
    replacement: Optional[str] = Field(default=None)


class CheckResponse(BaseModel):
    """Response para verificación de texto."""
    has_sensitive: bool
    types: List[str]
    matches: List[Dict[str, Any]]
    risk_level: Optional[str]
    regulations: List[str]


class SanitizeResponse(BaseModel):
    """Response para sanitización de texto."""
    original: str
    sanitized: str
    redacted_count: int
    detected_types: List[str]
    classification: str
    processing_time_ms: float


class TokenizeResponse(BaseModel):
    """Response para tokenización."""
    tokenized_text: str
    token_map: Dict[str, str]
    expires_at: str


class RulesListResponse(BaseModel):
    """Response para lista de reglas."""
    rules: List[Dict[str, Any]]
    total_count: int
    enabled_count: int


class FilterContextResponse(BaseModel):
    """Response para filtrado de contexto."""
    filtered_data: Dict[str, Any]
    context_type: str
    tier: str
    sanitization_level: str


class ComplianceReportResponse(BaseModel):
    """Response para reporte de cumplimiento."""
    report_generated: str
    period: Dict[str, Optional[str]]
    summary: Dict[str, Any]
    by_data_type: Dict[str, int]
    by_regulation: Dict[str, int]
    compliance_status: Dict[str, Any]


# ============================================
# Dependencias
# ============================================

def get_sanitizer() -> SensitiveDataSanitizer:
    """Obtiene la instancia del sanitizador."""
    return SensitiveDataSanitizer()


def get_context_filter() -> ContextDataFilter:
    """Obtiene la instancia del filtro de contexto."""
    return ContextDataFilter()


def get_audit_logger() -> SanitizationAuditLogger:
    """Obtiene la instancia del logger de auditoría."""
    return SanitizationAuditLogger()


# ============================================
# Endpoints
# ============================================

@router.post(
    "/check",
    response_model=CheckResponse,
    summary="Verificar texto sensible",
    description="Detecta datos sensibles en el texto sin sanitizarlo.",
)
async def check_text(
    request: CheckRequest,
    sanitizer: SensitiveDataSanitizer = Depends(get_sanitizer),
) -> CheckResponse:
    """
    Verifica si el texto contiene datos sensibles.
    
    Este endpoint analiza el texto y retorna información sobre
    los tipos de datos sensibles detectados sin modificar el texto.
    
    Args:
        request: Texto a verificar y opciones
        
    Returns:
        Información sobre datos sensibles detectados
    """
    try:
        detection = sanitizer.detect_sensitive_data(
            request.text,
            include_metadata=request.include_metadata,
        )
        
        return CheckResponse(
            has_sensitive=detection["has_sensitive"],
            types=detection["types"],
            matches=detection["matches"],
            risk_level=detection["risk_level"],
            regulations=detection["regulations"],
        )
    
    except Exception as e:
        logger.error("Error checking text", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/sanitize",
    response_model=SanitizeResponse,
    summary="Sanitizar texto",
    description="Sanitiza texto removiendo o redactando datos sensibles.",
)
async def sanitize_text(
    request: SanitizeRequest,
    background_tasks: BackgroundTasks,
    sanitizer: SensitiveDataSanitizer = Depends(get_sanitizer),
    audit_logger: SanitizationAuditLogger = Depends(get_audit_logger),
    http_request: Request = None,
) -> SanitizeResponse:
    """
    Sanitiza texto removiendo datos sensibles.
    
    Este endpoint aplica las reglas de sanitización configuradas
    para detectar y redactar información sensible del texto.
    
    Args:
        request: Texto a sanitizar y opciones
        
    Returns:
        Texto sanitizado con estadísticas
    """
    try:
        # Sanitizar texto
        result = sanitizer.sanitize_text(
            request.text,
            rules=request.rules,
            level=request.level,
        )
        
        # Registrar auditoría en background
        background_tasks.add_task(
            audit_logger.log_sanitization,
            user_id=request.user_id,
            session_id=request.session_id,
            operation_type="sanitize",
            data_types_detected=[dt.value for dt in result.detected_types],
            redaction_count=result.redacted_count,
            destination=request.destination,
            processing_time_ms=result.processing_time_ms,
        )
        
        return SanitizeResponse(
            original=result.original,
            sanitized=result.sanitized,
            redacted_count=result.redacted_count,
            detected_types=[dt.value for dt in result.detected_types],
            classification=result.classification.value,
            processing_time_ms=result.processing_time_ms,
        )
    
    except Exception as e:
        logger.error("Error sanitizing text", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/tokenize",
    response_model=TokenizeResponse,
    summary="Tokenizar texto sensible",
    description="Reemplaza datos sensibles con tokens recuperables.",
)
async def tokenize_text(
    request: TokenizeRequest,
    sanitizer: SensitiveDataSanitizer = Depends(get_sanitizer),
    audit_logger: SanitizationAuditLogger = Depends(get_audit_logger),
) -> TokenizeResponse:
    """
    Tokeniza datos sensibles en el texto.
    
    Este endpoint reemplaza datos sensibles con tokens que pueden
    ser utilizados para recuperar los datos originales más tarde.
    
    Args:
        request: Texto a tokenizar y opciones
        
    Returns:
        Texto tokenizado con mapeo de tokens
    """
    try:
        tokenized_text, token_map = sanitizer.tokenize_sensitive(
            request.text,
            expires_in_hours=request.expires_in_hours,
            user_id=request.user_id,
            session_id=request.session_id,
        )
        
        expires_at = datetime.utcnow() + timedelta(hours=request.expires_in_hours)
        
        # Registrar auditoría
        audit_logger.log_sanitization(
            user_id=request.user_id,
            session_id=request.session_id,
            operation_type="tokenize",
            data_types_detected=[],  # No revelar tipos en tokenización
            redaction_count=len(token_map),
            destination="tokenized",
        )
        
        return TokenizeResponse(
            tokenized_text=tokenized_text,
            token_map=token_map,
            expires_at=expires_at.isoformat(),
        )
    
    except Exception as e:
        logger.error("Error tokenizing text", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/recover",
    summary="Recuperar texto tokenizado",
    description="Recupera valores originales a partir de tokens.",
)
async def recover_text(
    request: RecoverRequest,
    sanitizer: SensitiveDataSanitizer = Depends(get_sanitizer),
) -> Dict[str, str]:
    """
    Recupera texto original a partir de tokens.
    
    Args:
        request: Texto tokenizado y mapeo de tokens
        
    Returns:
        Texto recuperado
    """
    try:
        recovered = sanitizer.recover_tokenized(
            request.text,
            request.token_map,
        )
        
        return {"recovered_text": recovered}
    
    except Exception as e:
        logger.error("Error recovering text", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/rules",
    response_model=RulesListResponse,
    summary="Listar reglas de sanitización",
    description="Obtiene todas las reglas de sanitización configuradas.",
)
async def list_rules(
    sanitizer: SensitiveDataSanitizer = Depends(get_sanitizer),
    data_type: Optional[str] = Query(
        default=None,
        description="Filtrar por tipo de dato sensible",
    ),
    enabled_only: bool = Query(
        default=False,
        description="Solo mostrar reglas habilitadas",
    ),
) -> RulesListResponse:
    """
    Lista todas las reglas de sanitización.
    
    Args:
        data_type: Filtrar por tipo de dato
        enabled_only: Solo mostrar reglas habilitadas
        
    Returns:
        Lista de reglas de sanitización
    """
    try:
        rules = sanitizer.get_rules()
        
        # Aplicar filtros
        if data_type:
            rules = [r for r in rules if r.data_type.value == data_type]
        
        if enabled_only:
            rules = [r for r in rules if r.enabled]
        
        # Convertir a diccionarios
        rules_data = [
            {
                "id": r.id,
                "name": r.name,
                "data_type": r.data_type.value,
                "pattern": r.pattern,
                "replacement": r.replacement,
                "enabled": r.enabled,
                "risk_level": r.risk_level,
                "classification": r.classification.value,
                "priority": r.priority,
                "languages": r.languages,
                "countries": r.countries,
                "description": r.description,
            }
            for r in rules
        ]
        
        return RulesListResponse(
            rules=rules_data,
            total_count=len(sanitizer.get_rules()),
            enabled_count=sum(1 for r in sanitizer.get_rules() if r.enabled),
        )
    
    except Exception as e:
        logger.error("Error listing rules", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put(
    "/rules",
    summary="Actualizar regla de sanitización",
    description="Actualiza una regla de sanitización existente (admin).",
)
async def update_rule(
    request: UpdateRuleRequest,
    sanitizer: SensitiveDataSanitizer = Depends(get_sanitizer),
    audit_logger: SanitizationAuditLogger = Depends(get_audit_logger),
) -> Dict[str, Any]:
    """
    Actualiza una regla de sanitización.
    
    Requiere permisos de administrador.
    
    Args:
        request: ID de la regla y campos a actualizar
        
    Returns:
        Estado de la actualización
    """
    # TODO: Añadir verificación de permisos admin
    
    try:
        rules = sanitizer.get_rules()
        rule = next((r for r in rules if r.id == request.rule_id), None)
        
        if not rule:
            raise HTTPException(
                status_code=404,
                detail=f"Rule {request.rule_id} not found"
            )
        
        # Aplicar actualizaciones
        if request.enabled is not None:
            rule.enabled = request.enabled
        
        if request.pattern is not None:
            # Validar patrón regex
            import re
            try:
                re.compile(request.pattern)
                rule.pattern = request.pattern
            except re.error as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid regex pattern: {e}"
                )
        
        if request.replacement is not None:
            rule.replacement = request.replacement
        
        rule.updated_at = datetime.utcnow()
        
        # Registrar evento de cumplimiento
        audit_logger.create_compliance_event(
            event_type="rule_updated",
            description=f"Sanitization rule {request.rule_id} updated",
            metadata={"updates": request.model_dump(exclude_none=True)},
        )
        
        return {
            "success": True,
            "rule_id": request.rule_id,
            "updated_at": rule.updated_at.isoformat(),
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating rule", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/filter/context",
    response_model=FilterContextResponse,
    summary="Filtrar contexto",
    description="Filtra datos de contexto según su tipo.",
)
async def filter_context(
    request: FilterContextRequest,
    context_filter: ContextDataFilter = Depends(get_context_filter),
    audit_logger: SanitizationAuditLogger = Depends(get_audit_logger),
) -> FilterContextResponse:
    """
    Filtra datos de contexto según su tipo.
    
    Aplica reglas de sanitización específicas según el tipo
    de contexto (personal, spatial, vertical, etc.).
    
    Args:
        request: Tipo de contexto y datos a filtrar
        
    Returns:
        Datos filtrados
    """
    try:
        filtered = context_filter.filter_context(
            context_type=request.context_type,
            data=request.data,
            tier=request.tier,
        )
        
        # Obtener nivel de sanitización aplicado
        config = context_filter.get_context_config(request.context_type)
        level = config.sanitization_level.value if config else "standard"
        
        return FilterContextResponse(
            filtered_data=filtered,
            context_type=request.context_type,
            tier=request.tier.value,
            sanitization_level=level,
        )
    
    except Exception as e:
        logger.error("Error filtering context", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/filter/personal",
    summary="Filtrar contexto personal",
    description="Filtra datos personales redactando email, teléfono, etc.",
)
async def filter_personal_context(
    data: Dict[str, Any] = Body(...),
    tier: SubscriptionTier = Query(default=SubscriptionTier.FREE),
    context_filter: ContextDataFilter = Depends(get_context_filter),
) -> Dict[str, Any]:
    """
    Filtra contexto personal.
    
    Args:
        data: Datos personales a filtrar
        tier: Nivel de suscripción
        
    Returns:
        Datos personales filtrados
    """
    return context_filter.filter_personal_context(data, tier)


@router.post(
    "/filter/spatial",
    summary="Filtrar contexto espacial",
    description="Generaliza coordenadas exactas a ciudad/región.",
)
async def filter_spatial_context(
    data: Dict[str, Any] = Body(...),
    tier: SubscriptionTier = Query(default=SubscriptionTier.FREE),
    context_filter: ContextDataFilter = Depends(get_context_filter),
) -> Dict[str, Any]:
    """
    Filtra contexto espacial.
    
    Args:
        data: Datos espaciales a filtrar
        tier: Nivel de suscripción
        
    Returns:
        Datos espaciales generalizados
    """
    return context_filter.filter_spatial_context(data, tier)


@router.post(
    "/filter/vertical",
    summary="Filtrar contexto vertical",
    description="Filtra datos médicos, financieros, etc.",
)
async def filter_vertical_context(
    data: Dict[str, Any] = Body(...),
    tier: SubscriptionTier = Query(default=SubscriptionTier.FREE),
    context_filter: ContextDataFilter = Depends(get_context_filter),
) -> Dict[str, Any]:
    """
    Filtra contexto vertical.
    
    Args:
        data: Datos de vertical a filtrar
        tier: Nivel de suscripción
        
    Returns:
        Datos de vertical filtrados
    """
    return context_filter.filter_vertical_context(data, tier)


@router.get(
    "/compliance/report",
    response_model=ComplianceReportResponse,
    summary="Reporte de cumplimiento",
    description="Genera un reporte de cumplimiento normativo.",
)
async def get_compliance_report(
    start_date: Optional[datetime] = Query(default=None),
    end_date: Optional[datetime] = Query(default=None),
    audit_logger: SanitizationAuditLogger = Depends(get_audit_logger),
) -> ComplianceReportResponse:
    """
    Genera un reporte de cumplimiento normativo.
    
    Args:
        start_date: Fecha de inicio del período
        end_date: Fecha de fin del período
        
    Returns:
        Reporte de cumplimiento
    """
    try:
        report = audit_logger.get_compliance_report(
            start_date=start_date,
            end_date=end_date,
        )
        
        return ComplianceReportResponse(**report)
    
    except Exception as e:
        logger.error("Error generating compliance report", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/compliance/user/{user_id}",
    summary="Reporte de privacidad de usuario",
    description="Genera un reporte de privacidad para un usuario específico.",
)
async def get_user_privacy_report(
    user_id: str,
    audit_logger: SanitizationAuditLogger = Depends(get_audit_logger),
) -> Dict[str, Any]:
    """
    Genera un reporte de privacidad para un usuario.
    
    Útil para solicitudes GDPR de "derecho al olvido" o
    "acceso a datos personales".
    
    Args:
        user_id: ID del usuario
        
    Returns:
        Reporte de privacidad del usuario
    """
    try:
        return audit_logger.get_user_privacy_report(user_id)
    
    except Exception as e:
        logger.error("Error generating user privacy report", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/statistics",
    summary="Estadísticas de sanitización",
    description="Obtiene estadísticas del sistema de sanitización.",
)
async def get_statistics(
    audit_logger: SanitizationAuditLogger = Depends(get_audit_logger),
) -> Dict[str, Any]:
    """
    Obtiene estadísticas del sistema.
    
    Returns:
        Estadísticas de auditoría
    """
    return audit_logger.get_statistics()


@router.get(
    "/data-types",
    summary="Tipos de datos sensibles",
    description="Lista todos los tipos de datos sensibles soportados.",
)
async def list_data_types() -> List[Dict[str, Any]]:
    """
    Lista todos los tipos de datos sensibles soportados.
    
    Returns:
        Lista de tipos de datos sensibles
    """
    return [
        {
            "value": dt.value,
            "display_name": dt.get_display_name(),
            "risk_level": dt.get_risk_level(),
            "regulations": dt.get_regulations(),
        }
        for dt in SensitiveDataType
    ]


@router.get(
    "/health",
    summary="Estado de salud",
    description="Verifica que el servicio está funcionando correctamente.",
)
async def health_check() -> Dict[str, Any]:
    """
    Verifica el estado de salud del servicio.
    
    Returns:
        Estado del servicio
    """
    return {
        "status": "healthy",
        "service": "sanitization",
        "timestamp": datetime.utcnow().isoformat(),
    }


# Función para incluir el router en la app principal
def include_sanitization_routes(app) -> None:
    """
    Incluye las rutas de sanitización en la aplicación FastAPI.
    
    Args:
        app: Instancia de FastAPI
    """
    app.include_router(router)
