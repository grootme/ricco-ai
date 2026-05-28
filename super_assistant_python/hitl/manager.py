"""
Human-in-the-Loop (HITL) System
================================

Sistema de intervención humana para validación, aprobación,
corrección y entrenamiento del sistema.

Niveles de HITL:
1. APPROVAL: Requiere aprobación explícita antes de ejecutar
2. REVIEW: Requiere revisión antes de proceder
3. CORRECTION: Permite correcciones post-ejecución
4. TRAINING: Proporciona ejemplos para mejorar
5. FEEDBACK: Recopila feedback para mejoras futuras
"""

import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Awaitable
from uuid import UUID, uuid4
import json

from pydantic import BaseModel, Field


class HITLLevel(str, Enum):
    """Niveles de intervención HITL"""
    APPROVAL = "APPROVAL"           # Nivel 1: Aprobación requerida
    REVIEW = "REVIEW"               # Nivel 2: Revisión opcional
    CORRECTION = "CORRECTION"       # Nivel 3: Corrección post-ejecución
    TRAINING = "TRAINING"           # Nivel 4: Entrenamiento con ejemplos
    FEEDBACK = "FEEDBACK"           # Nivel 5: Feedback general


class HITLStatus(str, Enum):
    """Estados de una solicitud HITL"""
    PENDING = "PENDING"             # Pendiente de respuesta
    APPROVED = "APPROVED"           # Aprobada
    REJECTED = "REJECTED"           # Rechazada
    MODIFIED = "MODIFIED"           # Modificada
    ESCALATED = "ESCALATED"         # Escalada a nivel superior
    EXPIRED = "EXPIRED"             # Expirada sin respuesta
    CANCELLED = "CANCELLED"         # Cancelada


class HITLPriority(str, Enum):
    """Prioridad de solicitudes HITL"""
    CRITICAL = "CRITICAL"           # Requiere respuesta inmediata
    HIGH = "HIGH"                   # Alta prioridad
    MEDIUM = "MEDIUM"               # Prioridad media
    LOW = "LOW"                     # Baja prioridad
    INFORMATIONAL = "INFORMATIONAL" # Solo informativa


class HITLChannel(str, Enum):
    """Canales de comunicación HITL"""
    WEB = "WEB"                     # Interfaz web
    SLACK = "SLACK"                 # Slack
    TELEGRAM = "TELEGRAM"           # Telegram
    EMAIL = "EMAIL"                 # Email
    SMS = "SMS"                     # SMS
    CLI = "CLI"                     # Línea de comandos


# ============================================
# MODELOS
# ============================================

class HITLRequest(BaseModel):
    """Solicitud de intervención humana"""
    id: UUID = Field(default_factory=uuid4)
    
    # Identificación
    agent_id: UUID
    session_id: Optional[UUID] = None
    execution_id: Optional[UUID] = None
    
    # Tipo y nivel
    type: HITLLevel
    priority: HITLPriority = HITLPriority.MEDIUM
    
    # Contenido
    title: str
    description: Optional[str] = None
    content: Dict[str, Any] = Field(default_factory=dict)
    
    # Opciones de respuesta
    options: List[Dict[str, Any]] = Field(default_factory=list)
    default_option: Optional[str] = None
    allow_free_text: bool = True
    allow_modifications: bool = False
    
    # Estado
    status: HITLStatus = HITLStatus.PENDING
    
    # Respuesta
    response: Optional[str] = None
    response_data: Optional[Dict[str, Any]] = None
    responded_by: Optional[str] = None
    responded_at: Optional[datetime] = None
    response_notes: Optional[str] = None
    
    # Tiempos
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    # Canal
    channel: HITLChannel = HITLChannel.WEB
    notification_sent: bool = False
    
    # Metadatos
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)


class HITLResponse(BaseModel):
    """Respuesta a una solicitud HITL"""
    request_id: UUID
    status: HITLStatus
    response: str
    response_data: Optional[Dict[str, Any]] = None
    responded_by: str
    responded_at: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None


class HITLFeedback(BaseModel):
    """Feedback del usuario"""
    id: UUID = Field(default_factory=uuid4)
    
    # Referencia
    request_id: Optional[UUID] = None
    session_id: Optional[UUID] = None
    execution_id: Optional[UUID] = None
    
    # Contenido
    rating: Optional[int] = None           # 1-5
    comment: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    
    # Tipo de feedback
    type: str = "GENERAL"                  # GENERAL, POSITIVE, NEGATIVE, SUGGESTION
    
    # Metadatos
    user_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class HITLRules(BaseModel):
    """Reglas para determinar cuándo requiere HITL"""
    # Umbrales de riesgo
    high_risk_threshold: float = 0.7
    medium_risk_threshold: float = 0.4
    
    # Acciones que siempre requieren HITL
    always_require_approval: List[str] = Field(default_factory=lambda: [
        "delete_data",
        "send_email",
        "make_payment",
        "modify_system",
        "execute_code",
        "access_sensitive"
    ])
    
    # Acciones que nunca requieren HITL
    never_require_approval: List[str] = Field(default_factory=lambda: [
        "read_data",
        "search_web",
        "analyze_content"
    ])
    
    # Configuración de expiración
    default_timeout_minutes: int = 30
    critical_timeout_minutes: int = 5
    
    # Canales preferidos por prioridad
    priority_channels: Dict[str, HITLChannel] = Field(default_factory=lambda: {
        "CRITICAL": HITLChannel.SMS,
        "HIGH": HITLChannel.SLACK,
        "MEDIUM": HITLChannel.WEB,
        "LOW": HITLChannel.EMAIL,
        "INFORMATIONAL": HITLChannel.WEB
    })


# ============================================
# MANAGER
# ============================================

class HITLManager:
    """
    Gestor del sistema Human-in-the-Loop.
    
    Responsabilidades:
    1. Evaluar si una acción requiere HITL
    2. Crear y gestionar solicitudes
    3. Enviar notificaciones
    4. Procesar respuestas
    5. Recopilar feedback
    """
    
    def __init__(
        self,
        rules: Optional[HITLRules] = None,
        notification_handlers: Optional[Dict[HITLChannel, Callable]] = None
    ):
        self.rules = rules or HITLRules()
        self.notification_handlers = notification_handlers or {}
        
        # Solicitudes pendientes
        self._pending_requests: Dict[UUID, HITLRequest] = {}
        
        # Historial
        self._request_history: List[HITLRequest] = []
        
        # Feedback
        self._feedback: List[HITLFeedback] = []
        
        # Callbacks
        self._on_response: Optional[Callable[[HITLResponse], Awaitable[None]]] = None
        self._on_timeout: Optional[Callable[[HITLRequest], Awaitable[None]]] = None
    
    # ==========================================
    # EVALUACIÓN
    # ==========================================
    
    async def evaluate_action(
        self,
        action: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Evaluar si una acción requiere HITL.
        
        Args:
            action: Nombre de la acción
            context: Contexto adicional
            
        Returns:
            Evaluación con decisión y justificación
        """
        context = context or {}
        
        evaluation = {
            "action": action,
            "requires_hitl": False,
            "level": None,
            "priority": HITLPriority.MEDIUM,
            "reason": None,
            "risk_score": 0.0
        }
        
        # Verificar lista de siempre requiere
        if action in self.rules.always_require_approval:
            evaluation["requires_hitl"] = True
            evaluation["level"] = HITLLevel.APPROVAL
            evaluation["priority"] = HITLPriority.HIGH
            evaluation["reason"] = f"Action '{action}' always requires approval"
            return evaluation
        
        # Verificar lista de nunca requiere
        if action in self.rules.never_require_approval:
            evaluation["requires_hitl"] = False
            evaluation["reason"] = f"Action '{action}' does not require HITL"
            return evaluation
        
        # Calcular riesgo basado en contexto
        risk_score = await self._calculate_risk(action, context)
        evaluation["risk_score"] = risk_score
        
        if risk_score >= self.rules.high_risk_threshold:
            evaluation["requires_hitl"] = True
            evaluation["level"] = HITLLevel.APPROVAL
            evaluation["priority"] = HITLPriority.HIGH
            evaluation["reason"] = f"High risk action (score: {risk_score:.2f})"
        
        elif risk_score >= self.rules.medium_risk_threshold:
            evaluation["requires_hitl"] = True
            evaluation["level"] = HITLLevel.REVIEW
            evaluation["priority"] = HITLPriority.MEDIUM
            evaluation["reason"] = f"Medium risk action (score: {risk_score:.2f})"
        
        else:
            evaluation["requires_hitl"] = False
            evaluation["level"] = HITLLevel.FEEDBACK
            evaluation["reason"] = f"Low risk action (score: {risk_score:.2f})"
        
        return evaluation
    
    async def _calculate_risk(
        self,
        action: str,
        context: Dict[str, Any]
    ) -> float:
        """Calcular puntuación de riesgo para una acción"""
        risk = 0.0
        
        # Factores de riesgo
        risk_factors = {
            "modifies_data": 0.3,
            "external_communication": 0.2,
            "financial_impact": 0.4,
            "security_impact": 0.5,
            "irreversible": 0.3,
            "affects_multiple_users": 0.2,
            "untested_path": 0.1
        }
        
        for factor, weight in risk_factors.items():
            if context.get(factor, False):
                risk += weight
        
        # Normalizar a 0-1
        return min(1.0, risk)
    
    # ==========================================
    # SOLICITUDES
    # ==========================================
    
    async def create_request(
        self,
        agent_id: UUID,
        type: HITLLevel,
        title: str,
        content: Dict[str, Any],
        priority: HITLPriority = HITLPriority.MEDIUM,
        session_id: Optional[UUID] = None,
        execution_id: Optional[UUID] = None,
        options: Optional[List[Dict[str, Any]]] = None,
        expires_in: Optional[int] = None
    ) -> HITLRequest:
        """
        Crear una nueva solicitud HITL.
        
        Args:
            agent_id: ID del agente que solicita
            type: Tipo de solicitud
            title: Título de la solicitud
            content: Contenido detallado
            priority: Prioridad
            session_id: ID de sesión
            execution_id: ID de ejecución
            options: Opciones de respuesta
            expires_in: Tiempo de expiración en minutos
            
        Returns:
            Solicitud creada
        """
        # Calcular expiración
        expires_at = None
        if expires_in:
            expires_at = datetime.utcnow() + timedelta(minutes=expires_in)
        elif priority == HITLPriority.CRITICAL:
            expires_at = datetime.utcnow() + timedelta(
                minutes=self.rules.critical_timeout_minutes
            )
        else:
            expires_at = datetime.utcnow() + timedelta(
                minutes=self.rules.default_timeout_minutes
            )
        
        # Determinar canal
        channel = self.rules.priority_channels.get(priority.value, HITLChannel.WEB)
        
        request = HITLRequest(
            id=uuid4(),
            agent_id=agent_id,
            session_id=session_id,
            execution_id=execution_id,
            type=type,
            priority=priority,
            title=title,
            content=content,
            options=options or self._default_options(type),
            expires_at=expires_at,
            channel=channel
        )
        
        # Almacenar
        self._pending_requests[request.id] = request
        
        # Enviar notificación
        await self._send_notification(request)
        
        return request
    
    def _default_options(self, type: HITLLevel) -> List[Dict[str, Any]]:
        """Generar opciones por defecto según el tipo"""
        if type == HITLLevel.APPROVAL:
            return [
                {"id": "approve", "label": "Aprobar", "style": "primary"},
                {"id": "reject", "label": "Rechazar", "style": "danger"},
                {"id": "modify", "label": "Modificar", "style": "secondary"}
            ]
        elif type == HITLLevel.REVIEW:
            return [
                {"id": "continue", "label": "Continuar", "style": "primary"},
                {"id": "pause", "label": "Pausar", "style": "secondary"},
                {"id": "stop", "label": "Detener", "style": "danger"}
            ]
        elif type == HITLLevel.FEEDBACK:
            return [
                {"id": "positive", "label": "👍 Útil", "style": "success"},
                {"id": "neutral", "label": "😐 Neutral", "style": "secondary"},
                {"id": "negative", "label": "👎 No útil", "style": "danger"}
            ]
        return []
    
    async def get_request(self, request_id: UUID) -> Optional[HITLRequest]:
        """Obtener una solicitud por ID"""
        return self._pending_requests.get(request_id)
    
    async def get_pending_requests(
        self,
        agent_id: Optional[UUID] = None,
        priority: Optional[HITLPriority] = None
    ) -> List[HITLRequest]:
        """Obtener solicitudes pendientes"""
        requests = list(self._pending_requests.values())
        
        if agent_id:
            requests = [r for r in requests if r.agent_id == agent_id]
        if priority:
            requests = [r for r in requests if r.priority == priority]
        
        # Ordenar por prioridad y tiempo
        priority_order = {
            HITLPriority.CRITICAL: 0,
            HITLPriority.HIGH: 1,
            HITLPriority.MEDIUM: 2,
            HITLPriority.LOW: 3,
            HITLPriority.INFORMATIONAL: 4
        }
        
        requests.sort(
            key=lambda r: (priority_order.get(r.priority, 5), r.created_at)
        )
        
        return requests
    
    # ==========================================
    # RESPUESTAS
    # ==========================================
    
    async def submit_response(
        self,
        request_id: UUID,
        response: str,
        response_data: Optional[Dict[str, Any]] = None,
        responded_by: Optional[str] = None,
        notes: Optional[str] = None
    ) -> HITLResponse:
        """
        Enviar respuesta a una solicitud.
        
        Args:
            request_id: ID de la solicitud
            response: Respuesta seleccionada
            response_data: Datos adicionales de respuesta
            responded_by: ID del usuario que responde
            notes: Notas adicionales
            
        Returns:
            Respuesta registrada
        """
        request = self._pending_requests.get(request_id)
        
        if not request:
            raise ValueError(f"Request {request_id} not found")
        
        if request.status != HITLStatus.PENDING:
            raise ValueError(f"Request {request_id} is not pending")
        
        # Determinar estado basado en respuesta
        if response.lower() in ["approve", "yes", "continue", "positive"]:
            status = HITLStatus.APPROVED
        elif response.lower() in ["reject", "no", "stop", "negative"]:
            status = HITLStatus.REJECTED
        elif response.lower() in ["modify", "edit"]:
            status = HITLStatus.MODIFIED
        else:
            status = HITLStatus.APPROVED  # Asumir aprobación para respuestas custom
        
        # Crear respuesta
        hitl_response = HITLResponse(
            request_id=request_id,
            status=status,
            response=response,
            response_data=response_data,
            responded_by=responded_by or "unknown",
            notes=notes
        )
        
        # Actualizar solicitud
        request.status = status
        request.response = response
        request.response_data = response_data
        request.responded_by = responded_by
        request.responded_at = datetime.utcnow()
        request.response_notes = notes
        
        # Mover a historial
        self._request_history.append(request)
        del self._pending_requests[request_id]
        
        # Callback
        if self._on_response:
            await self._on_response(hitl_response)
        
        return hitl_response
    
    async def escalate(
        self,
        request_id: UUID,
        reason: str
    ) -> HITLRequest:
        """
        Escalar una solicitud a mayor prioridad.
        
        Args:
            request_id: ID de la solicitud
            reason: Razón de la escalación
            
        Returns:
            Solicitud actualizada
        """
        request = self._pending_requests.get(request_id)
        
        if not request:
            raise ValueError(f"Request {request_id} not found")
        
        # Incrementar prioridad
        priority_order = [
            HITLPriority.INFORMATIONAL,
            HITLPriority.LOW,
            HITLPriority.MEDIUM,
            HITLPriority.HIGH,
            HITLPriority.CRITICAL
        ]
        
        current_idx = priority_order.index(request.priority)
        if current_idx < len(priority_order) - 1:
            request.priority = priority_order[current_idx + 1]
        
        request.status = HITLStatus.ESCALATED
        request.metadata["escalation_reason"] = reason
        request.metadata["escalated_at"] = datetime.utcnow().isoformat()
        
        # Reenviar notificación con nueva prioridad
        await self._send_notification(request)
        
        return request
    
    # ==========================================
    # FEEDBACK
    # ==========================================
    
    async def submit_feedback(
        self,
        rating: Optional[int] = None,
        comment: Optional[str] = None,
        request_id: Optional[UUID] = None,
        session_id: Optional[UUID] = None,
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> HITLFeedback:
        """
        Enviar feedback sobre una interacción.
        
        Args:
            rating: Calificación 1-5
            comment: Comentario
            request_id: ID de solicitud relacionada
            session_id: ID de sesión
            user_id: ID del usuario
            tags: Etiquetas
            
        Returns:
            Feedback registrado
        """
        # Determinar tipo de feedback
        feedback_type = "GENERAL"
        if rating:
            if rating >= 4:
                feedback_type = "POSITIVE"
            elif rating <= 2:
                feedback_type = "NEGATIVE"
        
        feedback = HITLFeedback(
            id=uuid4(),
            request_id=request_id,
            session_id=session_id,
            rating=rating,
            comment=comment,
            tags=tags or [],
            type=feedback_type,
            user_id=user_id
        )
        
        self._feedback.append(feedback)
        
        return feedback
    
    async def get_feedback_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de feedback"""
        if not self._feedback:
            return {"total": 0}
        
        ratings = [f.rating for f in self._feedback if f.rating]
        
        return {
            "total": len(self._feedback),
            "with_rating": len(ratings),
            "average_rating": sum(ratings) / len(ratings) if ratings else 0,
            "positive_count": len([f for f in self._feedback if f.type == "POSITIVE"]),
            "negative_count": len([f for f in self._feedback if f.type == "NEGATIVE"]),
            "recent_comments": [
                {"comment": f.comment, "rating": f.rating}
                for f in self._feedback[-10:]
                if f.comment
            ]
        }
    
    # ==========================================
    # NOTIFICACIONES
    # ==========================================
    
    async def _send_notification(self, request: HITLRequest) -> bool:
        """Enviar notificación de la solicitud"""
        handler = self.notification_handlers.get(request.channel)
        
        if handler:
            try:
                await handler(request)
                request.notification_sent = True
                return True
            except Exception as e:
                print(f"Notification error: {e}")
                return False
        
        # Notificación por defecto (log)
        print(f"[HITL] {request.priority.value}: {request.title}")
        request.notification_sent = True
        return True
    
    def register_notification_handler(
        self,
        channel: HITLChannel,
        handler: Callable[[HITLRequest], Awaitable[None]]
    ) -> None:
        """Registrar un manejador de notificaciones para un canal"""
        self.notification_handlers[channel] = handler
    
    # ==========================================
    # TIMEOUTS
    # ==========================================
    
    async def check_timeouts(self) -> List[HITLRequest]:
        """Verificar solicitudes expiradas"""
        now = datetime.utcnow()
        expired = []
        
        for request in list(self._pending_requests.values()):
            if request.expires_at and request.expires_at < now:
                request.status = HITLStatus.EXPIRED
                expired.append(request)
                
                # Mover a historial
                self._request_history.append(request)
                del self._pending_requests[request.id]
                
                # Callback
                if self._on_timeout:
                    await self._on_timeout(request)
        
        return expired
    
    async def start_timeout_monitor(self, interval: int = 60) -> None:
        """
        Iniciar monitor de timeouts en background.
        
        Args:
            interval: Intervalo de verificación en segundos
        """
        while True:
            await self.check_timeouts()
            await asyncio.sleep(interval)
    
    # ==========================================
    # ESTADÍSTICAS
    # ==========================================
    
    async def get_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del sistema HITL"""
        total_requests = len(self._request_history) + len(self._pending_requests)
        
        if total_requests == 0:
            return {
                "total_requests": 0,
                "pending": 0,
                "approved": 0,
                "rejected": 0,
                "expired": 0
            }
        
        all_requests = list(self._pending_requests.values()) + self._request_history
        
        return {
            "total_requests": total_requests,
            "pending": len(self._pending_requests),
            "approved": len([r for r in all_requests if r.status == HITLStatus.APPROVED]),
            "rejected": len([r for r in all_requests if r.status == HITLStatus.REJECTED]),
            "expired": len([r for r in all_requests if r.status == HITLStatus.EXPIRED]),
            "escalated": len([r for r in all_requests if r.status == HITLStatus.ESCALATED]),
            "by_priority": {
                p.value: len([r for r in all_requests if r.priority == p])
                for p in HITLPriority
            },
            "average_response_time": self._calculate_avg_response_time(all_requests),
            "feedback": await self.get_feedback_stats()
        }
    
    def _calculate_avg_response_time(self, requests: List[HITLRequest]) -> float:
        """Calcular tiempo promedio de respuesta en segundos"""
        response_times = []
        
        for r in requests:
            if r.responded_at and r.created_at:
                delta = (r.responded_at - r.created_at).total_seconds()
                response_times.append(delta)
        
        if not response_times:
            return 0.0
        
        return sum(response_times) / len(response_times)
