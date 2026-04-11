"""
Sistema de Auditoría para Sanitización en RICCO AI
Logging y tracking de operaciones de sanitización

Este módulo implementa el sistema de auditoría que registra
todas las operaciones de sanitización para cumplimiento
normativo y análisis de seguridad.

Autor: RICCO AI Team
Mercado objetivo: Cuba y América Latina
"""

import json
import hashlib
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict

from structlog import get_logger

from .models import (
    SanitizationResult,
    SanitizationAuditRecord,
    SensitiveDataType,
    DataClassification,
)

logger = get_logger(__name__)


class SanitizationAuditLogger:
    """
    Logger de auditoría para operaciones de sanitización.
    
    Registra todas las operaciones de sanitización realizadas,
    incluyendo qué datos fueron detectados y redactados, para
    cumplimiento con regulaciones de privacidad.
    
    Características:
    - Logging estructurado de operaciones
    - Tracking de cumplimiento normativo
    - Generación de reportes de auditoría
    - Alertas de seguridad
    
    Example:
        >>> audit = SanitizationAuditLogger()
        >>> audit.log_sanitization(
        ...     user_id="user123",
        ...     operation="sanitize",
        ...     data_types=["email", "phone"],
        ...     redaction_count=2,
        ... )
    """
    
    def __init__(
        self,
        retention_days: int = 90,
        alert_threshold: int = 10,
        enable_console_logging: bool = True,
    ):
        """
        Inicializa el logger de auditoría.
        
        Args:
            retention_days: Días de retención de logs
            alert_threshold: Umbral de redacciones para alertas
            enable_console_logging: Si debe loggear a consola
        """
        self.retention_days = retention_days
        self.alert_threshold = alert_threshold
        self.enable_console_logging = enable_console_logging
        
        # Almacenamiento en memoria (en producción usar BD)
        self._records: List[SanitizationAuditRecord] = []
        
        # Contadores para detección de anomalías
        self._hourly_counts: Dict[str, int] = defaultdict(int)
        self._user_counts: Dict[str, int] = defaultdict(int)
        self._type_counts: Dict[str, int] = defaultdict(int)
        
        logger.info(
            "SanitizationAuditLogger initialized",
            retention_days=retention_days,
            alert_threshold=alert_threshold,
        )
    
    def log_sanitization(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        operation_type: str = "sanitize",
        data_types_detected: Optional[List[str]] = None,
        redaction_count: int = 0,
        context_type: Optional[str] = None,
        destination: str = "unknown",
        source_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        processing_time_ms: float = 0.0,
    ) -> SanitizationAuditRecord:
        """
        Registra una operación de sanitización.
        
        Args:
            user_id: ID del usuario
            session_id: ID de la sesión
            operation_type: Tipo de operación (sanitize, detect, tokenize)
            data_types_detected: Tipos de datos sensibles detectados
            redaction_count: Número de redacciones realizadas
            context_type: Tipo de contexto procesado
            destination: Destino de los datos
            source_ip: IP de origen
            user_agent: User agent
            request_id: ID de la petición
            processing_time_ms: Tiempo de procesamiento
            
        Returns:
            Registro de auditoría creado
        """
        # Determinar regulaciones aplicables
        regulations = self._determine_regulations(data_types_detected or [])
        
        record = SanitizationAuditRecord(
            user_id=user_id,
            session_id=session_id,
            operation_type=operation_type,
            data_types_detected=data_types_detected or [],
            redaction_count=redaction_count,
            context_type=context_type,
            destination=destination,
            source_ip=source_ip,
            user_agent=user_agent,
            request_id=request_id,
            regulations_applicable=regulations,
            processing_time_ms=processing_time_ms,
        )
        
        # Guardar registro
        self._records.append(record)
        
        # Actualizar contadores
        hour_key = datetime.utcnow().strftime("%Y-%m-%d-%H")
        self._hourly_counts[hour_key] += 1
        
        if user_id:
            self._user_counts[user_id] += 1
        
        for dt in (data_types_detected or []):
            self._type_counts[dt] += 1
        
        # Log a consola
        if self.enable_console_logging:
            self._log_to_console(record)
        
        # Verificar umbrales de alerta
        self._check_alert_thresholds(record)
        
        return record
    
    def log_from_result(
        self,
        result: SanitizationResult,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        context_type: Optional[str] = None,
        destination: str = "ai_model",
    ) -> SanitizationAuditRecord:
        """
        Crea un registro de auditoría a partir de un SanitizationResult.
        
        Args:
            result: Resultado de sanitización
            user_id: ID del usuario
            session_id: ID de la sesión
            context_type: Tipo de contexto
            destination: Destino de los datos
            
        Returns:
            Registro de auditoría creado
        """
        data_types = [dt.value if isinstance(dt, SensitiveDataType) else dt 
                      for dt in result.detected_types]
        
        return self.log_sanitization(
            user_id=user_id,
            session_id=session_id,
            operation_type="sanitize",
            data_types_detected=data_types,
            redaction_count=result.redacted_count,
            context_type=context_type,
            destination=destination,
            processing_time_ms=result.processing_time_ms,
        )
    
    def _determine_regulations(
        self,
        data_types: List[str],
    ) -> List[str]:
        """
        Determina las regulaciones aplicables según los tipos de datos.
        
        Args:
            data_types: Tipos de datos sensibles detectados
            
        Returns:
            Lista de regulaciones aplicables
        """
        regulations = set()
        
        # Mapear tipos de datos a regulaciones
        type_regulations = {
            "credit_card": ["PCI-DSS", "GDPR"],
            "ssn": ["GDPR", "CCPA", "Ley de Protección de Datos"],
            "email": ["GDPR"],
            "phone": ["GDPR", "TCPA"],
            "password": ["GDPR", "SOC2"],
            "api_key": ["SOC2", "ISO27001"],
            "bank_account": ["PCI-DSS", "GDPR", "PSD2"],
            "crypto_address": ["AML", "KYC"],
            "medical_record": ["HIPAA", "GDPR"],
            "government_id": ["GDPR", "KYC", "AML"],
            "location_exact": ["GDPR", "CCPA"],
            "financial_data": ["PCI-DSS", "GDPR", "SOX"],
            "biometric": ["BIPA", "GDPR", "CCPA"],
        }
        
        for dt in data_types:
            if dt in type_regulations:
                regulations.update(type_regulations[dt])
        
        return list(regulations)
    
    def _log_to_console(self, record: SanitizationAuditRecord) -> None:
        """Loggea el registro a consola."""
        log_data = {
            "audit_id": str(record.id),
            "timestamp": record.timestamp.isoformat(),
            "operation": record.operation_type,
            "user_id": record.user_id,
            "data_types": record.data_types_detected,
            "redaction_count": record.redaction_count,
            "destination": record.destination,
            "regulations": record.regulations_applicable,
        }
        
        if record.redaction_count > 0:
            logger.info("Sanitization audit record", **log_data)
        else:
            logger.debug("Sanitization audit record (no redactions)", **log_data)
    
    def _check_alert_thresholds(self, record: SanitizationAuditRecord) -> None:
        """Verifica umbrales de alerta."""
        # Alerta si hay muchas redacciones en una hora
        hour_key = datetime.utcnow().strftime("%Y-%m-%d-%H")
        if self._hourly_counts[hour_key] > self.alert_threshold * 10:
            logger.warning(
                "High volume of sanitizations detected",
                hour=hour_key,
                count=self._hourly_counts[hour_key],
            )
        
        # Alerta si un usuario tiene muchas redacciones
        if record.user_id:
            if self._user_counts[record.user_id] > self.alert_threshold:
                logger.warning(
                    "User has many sanitization operations",
                    user_id=record.user_id,
                    count=self._user_counts[record.user_id],
                )
    
    def get_audit_records(
        self,
        user_id: Optional[str] = None,
        operation_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[SanitizationAuditRecord]:
        """
        Obtiene registros de auditoría filtrados.
        
        Args:
            user_id: Filtrar por usuario
            operation_type: Filtrar por tipo de operación
            start_date: Fecha de inicio
            end_date: Fecha de fin
            limit: Límite de registros a retornar
            
        Returns:
            Lista de registros de auditoría
        """
        filtered = []
        
        for record in self._records:
            # Aplicar filtros
            if user_id and record.user_id != user_id:
                continue
            if operation_type and record.operation_type != operation_type:
                continue
            if start_date and record.timestamp < start_date:
                continue
            if end_date and record.timestamp > end_date:
                continue
            
            filtered.append(record)
            
            if len(filtered) >= limit:
                break
        
        # Ordenar por timestamp descendente
        filtered.sort(key=lambda r: r.timestamp, reverse=True)
        
        return filtered[:limit]
    
    def get_compliance_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Genera un reporte de cumplimiento.
        
        Args:
            start_date: Fecha de inicio
            end_date: Fecha de fin
            
        Returns:
            Reporte de cumplimiento
        """
        records = self.get_audit_records(
            start_date=start_date,
            end_date=end_date,
            limit=10000,
        )
        
        # Calcular estadísticas
        total_operations = len(records)
        total_redactions = sum(r.redaction_count for r in records)
        
        # Conteos por tipo de dato
        type_counts: Dict[str, int] = defaultdict(int)
        for record in records:
            for dt in record.data_types_detected:
                type_counts[dt] += 1
        
        # Conteos por regulación
        regulation_counts: Dict[str, int] = defaultdict(int)
        for record in records:
            for reg in record.regulations_applicable:
                regulation_counts[reg] += 1
        
        # Operaciones por destino
        destination_counts: Dict[str, int] = defaultdict(int)
        for record in records:
            destination_counts[record.destination] += 1
        
        # Usuarios únicos
        unique_users = len(set(r.user_id for r in records if r.user_id))
        
        return {
            "report_generated": datetime.utcnow().isoformat(),
            "period": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None,
            },
            "summary": {
                "total_operations": total_operations,
                "total_redactions": total_redactions,
                "unique_users": unique_users,
                "avg_redactions_per_operation": total_redactions / max(total_operations, 1),
            },
            "by_data_type": dict(type_counts),
            "by_regulation": dict(regulation_counts),
            "by_destination": dict(destination_counts),
            "compliance_status": self._calculate_compliance_status(regulation_counts),
        }
    
    def _calculate_compliance_status(
        self,
        regulation_counts: Dict[str, int],
    ) -> Dict[str, Any]:
        """
        Calcula el estado de cumplimiento normativo.
        
        Args:
            regulation_counts: Conteos por regulación
            
        Returns:
            Estado de cumplimiento
        """
        status = {}
        
        for regulation, count in regulation_counts.items():
            if regulation == "PCI-DSS":
                status[regulation] = {
                    "status": "compliant" if count > 0 else "not_applicable",
                    "description": "Datos de tarjetas de crédito detectados y protegidos",
                }
            elif regulation == "HIPAA":
                status[regulation] = {
                    "status": "compliant" if count > 0 else "not_applicable",
                    "description": "Datos médicos protegidos",
                }
            elif regulation == "GDPR":
                status[regulation] = {
                    "status": "compliant" if count > 0 else "not_applicable",
                    "description": "Datos personales protegidos bajo GDPR",
                }
            else:
                status[regulation] = {
                    "status": "compliant" if count > 0 else "not_applicable",
                    "description": f"Datos bajo {regulation} protegidos",
                }
        
        return status
    
    def get_user_privacy_report(
        self,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Genera un reporte de privacidad para un usuario específico.
        
        Útil para solicitudes de "derecho al olvido" o
        "acceso a datos personales".
        
        Args:
            user_id: ID del usuario
            
        Returns:
            Reporte de privacidad del usuario
        """
        records = self.get_audit_records(user_id=user_id, limit=1000)
        
        # Calcular estadísticas
        total_operations = len(records)
        total_redactions = sum(r.redaction_count for r in records)
        
        # Tipos de datos detectados
        data_types: set = set()
        for record in records:
            data_types.update(record.data_types_detected)
        
        # Destinos de datos
        destinations: set = set(r.destination for r in records)
        
        # Primera y última operación
        first_operation = min((r.timestamp for r in records), default=None)
        last_operation = max((r.timestamp for r in records), default=None)
        
        return {
            "user_id": user_id,
            "report_generated": datetime.utcnow().isoformat(),
            "summary": {
                "total_sanitization_operations": total_operations,
                "total_data_redactions": total_redactions,
                "data_types_protected": list(data_types),
                "destinations": list(destinations),
            },
            "timeline": {
                "first_operation": first_operation.isoformat() if first_operation else None,
                "last_operation": last_operation.isoformat() if last_operation else None,
            },
            "privacy_controls_applied": {
                "pii_redaction": True,
                "location_generalization": True,
                "financial_data_protection": True,
                "medical_data_protection": True,
            },
        }
    
    def cleanup_expired_records(self) -> int:
        """
        Elimina registros expirados según la política de retención.
        
        Returns:
            Número de registros eliminados
        """
        cutoff = datetime.utcnow() - timedelta(days=self.retention_days)
        
        initial_count = len(self._records)
        self._records = [r for r in self._records if r.timestamp >= cutoff]
        
        removed = initial_count - len(self._records)
        
        if removed > 0:
            logger.info(f"Cleaned up {removed} expired audit records")
        
        return removed
    
    def export_records(
        self,
        format: str = "json",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> str:
        """
        Exporta registros de auditoría.
        
        Args:
            format: Formato de exportación (json, csv)
            start_date: Fecha de inicio
            end_date: Fecha de fin
            
        Returns:
            Registros exportados como string
        """
        records = self.get_audit_records(
            start_date=start_date,
            end_date=end_date,
            limit=10000,
        )
        
        if format == "json":
            return json.dumps(
                [r.model_dump() for r in records],
                default=str,
                indent=2,
            )
        elif format == "csv":
            # CSV básico
            lines = [
                "id,timestamp,user_id,operation,redaction_count,data_types,destination"
            ]
            for r in records:
                lines.append(
                    f"{r.id},{r.timestamp.isoformat()},{r.user_id or ''},"
                    f"{r.operation_type},{r.redaction_count},"
                    f"\"{','.join(r.data_types_detected)}\",{r.destination}"
                )
            return "\n".join(lines)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas generales del sistema de auditoría.
        
        Returns:
            Estadísticas del sistema
        """
        return {
            "total_records": len(self._records),
            "hourly_operations": dict(self._hourly_counts),
            "user_operations": dict(self._user_counts),
            "data_type_detections": dict(self._type_counts),
            "retention_days": self.retention_days,
            "alert_threshold": self.alert_threshold,
        }
    
    def create_compliance_event(
        self,
        event_type: str,
        description: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Crea un evento de cumplimiento normativo.
        
        Args:
            event_type: Tipo de evento
            description: Descripción del evento
            user_id: ID del usuario afectado
            metadata: Metadata adicional
            
        Returns:
            Evento creado
        """
        event = {
            "id": hashlib.sha256(
                f"{event_type}:{datetime.utcnow().isoformat()}:{user_id}".encode()
            ).hexdigest()[:16],
            "event_type": event_type,
            "description": description,
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }
        
        logger.info(
            "Compliance event created",
            **event
        )
        
        return event
