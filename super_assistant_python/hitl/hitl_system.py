"""
Sistema de Human-in-the-Loop (HITL) para el Super Asistente.
Implementa patrones de AutoGen UserProxyAgent y LangGraph interrupt.
"""

from typing import Any, Dict, List, Optional, Callable, Union, Awaitable
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
import asyncio
from dataclasses import dataclass
import uuid

import sys
sys.path.insert(0, '/home/z/my-project/super_assistant_python')
from core.models import (
    HumanApprovalRequest, ToolCall, ToolResult, ToolResultStatus,
    Task, TaskStatus
)


# =============================================================================
# TIPOS Y ENUMS
# =============================================================================

class HITLEventType(str, Enum):
    """Tipos de eventos HITL."""
    APPROVAL_REQUEST = "approval_request"
    APPROVAL_RESPONSE = "approval_response"
    USER_INPUT = "user_input"
    INTERRUPTION = "interruption"
    RESUMPTION = "resumption"


class ApprovalDecision(str, Enum):
    """Decisiones de aprobación."""
    APPROVE = "approve"
    REJECT = "reject"
    MODIFY = "modify"
    DEFER = "defer"


# =============================================================================
# MODELOS DE EVENTOS
# =============================================================================

class HITLEvent(BaseModel):
    """Evento del sistema HITL."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: HITLEventType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = Field(default_factory=dict)


class ApprovalRequest(BaseModel):
    """Solicitud de aprobación."""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tool_call: Optional[ToolCall] = None
    task: Optional[Task] = None
    reason: str
    context: Dict[str, Any] = Field(default_factory=dict)
    options: List[ApprovalDecision] = Field(
        default_factory=lambda: [
            ApprovalDecision.APPROVE,
            ApprovalDecision.REJECT,
            ApprovalDecision.MODIFY
        ]
    )
    timeout_seconds: int = 300
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    def model_post_init(self, __context: Any) -> None:
        if self.expires_at is None:
            from datetime import timedelta
            self.expires_at = self.created_at + timedelta(seconds=self.timeout_seconds)


class ApprovalResponse(BaseModel):
    """Respuesta a una solicitud de aprobación."""
    request_id: str
    decision: ApprovalDecision
    responder: str  # "human" or agent_id
    modified_data: Optional[Dict[str, Any]] = None
    reason: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# INTERFACES
# =============================================================================

class HITLHandler(ABC):
    """Interface abstracta para manejo de eventos HITL."""
    
    @abstractmethod
    async def request_approval(
        self,
        request: ApprovalRequest
    ) -> ApprovalResponse:
        """Solicita aprobación y espera respuesta."""
        pass
    
    @abstractmethod
    async def request_input(
        self,
        prompt: str,
        context: Dict[str, Any]
    ) -> str:
        """Solicita input del usuario."""
        pass


class HITLEventHandler(ABC):
    """Interface para manejar eventos HITL."""
    
    @abstractmethod
    async def on_event(self, event: HITLEvent) -> None:
        """Maneja un evento HITL."""
        pass


# =============================================================================
# IMPLEMENTACIONES
# =============================================================================

class ConsoleHITLHandler(HITLHandler):
    """
    Implementación de HITL usando la consola.
    Útil para desarrollo y testing.
    """
    
    def __init__(
        self,
        auto_approve_safe_operations: bool = False,
        safe_operations: Optional[List[str]] = None
    ):
        self.auto_approve_safe = auto_approve_safe_operations
        self.safe_operations = safe_operations or [
            "read", "search", "query", "get", "list"
        ]
        self._pending_requests: Dict[str, ApprovalRequest] = {}
    
    def _is_safe_operation(self, operation: str) -> bool:
        """Determina si una operación es considerada segura."""
        operation_lower = operation.lower()
        return any(safe in operation_lower for safe in self.safe_operations)
    
    async def request_approval(
        self,
        request: ApprovalRequest
    ) -> ApprovalResponse:
        """Solicita aprobación por consola."""
        # Auto-aprobar operaciones seguras si está habilitado
        if self.auto_approve_safe:
            operation = ""
            if request.tool_call:
                operation = request.tool_call.name
            elif request.task:
                operation = request.task.description
            
            if self._is_safe_operation(operation):
                print(f"[AUTO-APPROVED] Operación segura: {operation}")
                return ApprovalResponse(
                    request_id=request.request_id,
                    decision=ApprovalDecision.APPROVE,
                    responder="auto_approve",
                    reason="Operación considerada segura"
                )
        
        # Mostrar solicitud
        print("\n" + "="*60)
        print("⚠️  SOLICITUD DE APROBACIÓN")
        print("="*60)
        
        if request.tool_call:
            print(f"\nHerramienta: {request.tool_call.name}")
            print(f"Argumentos: {request.tool_call.arguments}")
        
        if request.task:
            print(f"\nTarea: {request.task.description}")
        
        print(f"\nRazón: {request.reason}")
        print(f"\nOpciones: {[d.value for d in request.options]}")
        
        # Esperar respuesta
        while True:
            response = input("\nTu decisión (approve/reject/modify): ").strip().lower()
            
            if response in ["approve", "a", "yes", "y", "sí", "si"]:
                return ApprovalResponse(
                    request_id=request.request_id,
                    decision=ApprovalDecision.APPROVE,
                    responder="human"
                )
            elif response in ["reject", "r", "no", "n"]:
                reason = input("Razón del rechazo (opcional): ").strip()
                return ApprovalResponse(
                    request_id=request.request_id,
                    decision=ApprovalDecision.REJECT,
                    responder="human",
                    reason=reason or None
                )
            elif response in ["modify", "m"]:
                print("Ingresa las modificaciones (JSON):")
                mod_input = input().strip()
                try:
                    import json
                    modified_data = json.loads(mod_input)
                    return ApprovalResponse(
                        request_id=request.request_id,
                        decision=ApprovalDecision.MODIFY,
                        responder="human",
                        modified_data=modified_data
                    )
                except json.JSONDecodeError:
                    print("JSON inválido. Intenta de nuevo.")
                    continue
            else:
                print("Opción no válida. Intenta de nuevo.")
    
    async def request_input(
        self,
        prompt: str,
        context: Dict[str, Any]
    ) -> str:
        """Solicita input del usuario por consola."""
        print("\n" + "-"*60)
        print(f"💬 {prompt}")
        if context:
            print(f"Contexto: {context}")
        return input("> ").strip()


class CallbackHITLHandler(HITLHandler):
    """
    Implementación de HITL usando callbacks.
    Permite integración con sistemas externos (APIs, UIs, etc.)
    """
    
    def __init__(
        self,
        approval_callback: Optional[Callable[[ApprovalRequest], Awaitable[ApprovalResponse]]] = None,
        input_callback: Optional[Callable[[str, Dict[str, Any]], Awaitable[str]]] = None
    ):
        self.approval_callback = approval_callback
        self.input_callback = input_callback
        self._pending_requests: Dict[str, asyncio.Future] = {}
    
    async def request_approval(
        self,
        request: ApprovalRequest
    ) -> ApprovalResponse:
        """Solicita aprobación usando el callback configurado."""
        if self.approval_callback:
            return await self.approval_callback(request)
        
        # Sin callback, aprobar automáticamente
        return ApprovalResponse(
            request_id=request.request_id,
            decision=ApprovalDecision.APPROVE,
            responder="auto",
            reason="Sin callback de aprobación configurado"
        )
    
    async def request_input(
        self,
        prompt: str,
        context: Dict[str, Any]
    ) -> str:
        """Solicita input usando el callback configurado."""
        if self.input_callback:
            return await self.input_callback(prompt, context)
        
        # Sin callback, retornar vacío
        return ""
    
    def submit_response(self, response: ApprovalResponse) -> None:
        """Permite enviar una respuesta externamente."""
        if response.request_id in self._pending_requests:
            future = self._pending_requests.pop(response.request_id)
            future.set_result(response)


# =============================================================================
# GESTOR HITL
# =============================================================================

class HITLManager:
    """
    Gestor central del sistema Human-in-the-Loop.
    Coordina las solicitudes y respuestas.
    """
    
    def __init__(
        self,
        handler: Optional[HITLHandler] = None,
        event_handlers: Optional[List[HITLEventHandler]] = None
    ):
        self.handler = handler or ConsoleHITLHandler()
        self.event_handlers = event_handlers or []
        self._pending_requests: Dict[str, ApprovalRequest] = {}
        self._response_queue: asyncio.Queue = asyncio.Queue()
        self._history: List[HITLEvent] = []
    
    async def _emit_event(self, event: HITLEvent) -> None:
        """Emite un evento a todos los handlers."""
        self._history.append(event)
        for handler in self.event_handlers:
            await handler.on_event(event)
    
    async def request_tool_approval(
        self,
        tool_call: ToolCall,
        reason: str = "Ejecución de herramienta sensible"
    ) -> ApprovalResponse:
        """
        Solicita aprobación para ejecutar una herramienta.
        """
        request = ApprovalRequest(
            tool_call=tool_call,
            reason=reason
        )
        
        # Emitir evento
        await self._emit_event(HITLEvent(
            event_type=HITLEventType.APPROVAL_REQUEST,
            data={
                "request_id": request.request_id,
                "tool_name": tool_call.name,
                "reason": reason
            }
        ))
        
        # Almacenar pendiente
        self._pending_requests[request.request_id] = request
        
        # Solicitar aprobación
        response = await self.handler.request_approval(request)
        
        # Limpiar pendiente
        self._pending_requests.pop(request.request_id, None)
        
        # Emitir respuesta
        await self._emit_event(HITLEvent(
            event_type=HITLEventType.APPROVAL_RESPONSE,
            data={
                "request_id": response.request_id,
                "decision": response.decision.value,
                "responder": response.responder
            }
        ))
        
        return response
    
    async def request_task_approval(
        self,
        task: Task,
        reason: str = "Tarea sensible requiere aprobación"
    ) -> ApprovalResponse:
        """
        Solicita aprobación para ejecutar una tarea.
        """
        request = ApprovalRequest(
            task=task,
            reason=reason
        )
        
        await self._emit_event(HITLEvent(
            event_type=HITLEventType.APPROVAL_REQUEST,
            data={
                "request_id": request.request_id,
                "task_id": task.id,
                "reason": reason
            }
        ))
        
        response = await self.handler.request_approval(request)
        
        await self._emit_event(HITLEvent(
            event_type=HITLEventType.APPROVAL_RESPONSE,
            data={
                "request_id": response.request_id,
                "decision": response.decision.value
            }
        ))
        
        return response
    
    async def get_user_input(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Solicita input del usuario.
        """
        await self._emit_event(HITLEvent(
            event_type=HITLEventType.USER_INPUT,
            data={"prompt": prompt}
        ))
        
        response = await self.handler.request_input(prompt, context or {})
        
        return response
    
    def get_pending_requests(self) -> List[ApprovalRequest]:
        """Retorna las solicitudes pendientes."""
        return list(self._pending_requests.values())
    
    def get_history(self) -> List[HITLEvent]:
        """Retorna el historial de eventos."""
        return self._history.copy()
    
    def requires_approval(
        self,
        tool_name: str,
        sensitive_tools: Optional[List[str]] = None
    ) -> bool:
        """
        Determina si una herramienta requiere aprobación.
        """
        sensitive = sensitive_tools or [
            "delete", "remove", "execute", "shell",
            "file_write", "email_send", "api_call"
        ]
        
        return any(s in tool_name.lower() for s in sensitive)


# =============================================================================
# INTEGRACIÓN CON LANGGRAPH
# =============================================================================

class HITLNode:
    """
    Nodo HITL para integrar con LangGraph.
    """
    
    def __init__(
        self,
        hitl_manager: HITLManager,
        auto_approve_safe: bool = True
    ):
        self.hitl_manager = hitl_manager
        self.auto_approve_safe = auto_approve_safe
    
    async def __call__(
        self,
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Procesa el estado y solicita aprobaciones si es necesario.
        """
        pending_tools = state.get("pending_tool_calls", [])
        
        if not pending_tools:
            return state
        
        # Procesar cada herramienta pendiente
        approved_calls = []
        rejected_calls = []
        
        for tool_call in pending_tools:
            tool_name = tool_call.get("name", "")
            
            # Verificar si requiere aprobación
            if self.hitl_manager.requires_approval(tool_name):
                # Crear ToolCall
                tc = ToolCall(
                    id=tool_call.get("id", ""),
                    name=tool_name,
                    arguments=tool_call.get("arguments", {}),
                    requested_by=tool_call.get("requested_by", "unknown")
                )
                
                # Solicitar aprobación
                response = await self.hitl_manager.request_tool_approval(tc)
                
                if response.decision == ApprovalDecision.APPROVE:
                    approved_calls.append(tool_call)
                elif response.decision == ApprovalDecision.MODIFY:
                    # Aplicar modificaciones
                    modified = {**tool_call, "arguments": response.modified_data}
                    approved_calls.append(modified)
                else:
                    rejected_calls.append(tool_call)
            else:
                # No requiere aprobación
                if self.auto_approve_safe:
                    approved_calls.append(tool_call)
                else:
                    # Aún así solicitar aprobación simple
                    tc = ToolCall(
                        id=tool_call.get("id", ""),
                        name=tool_name,
                        arguments=tool_call.get("arguments", {}),
                        requested_by=tool_call.get("requested_by", "unknown")
                    )
                    response = await self.hitl_manager.request_tool_approval(tc)
                    if response.decision == ApprovalDecision.APPROVE:
                        approved_calls.append(tool_call)
                    else:
                        rejected_calls.append(tool_call)
        
        # Actualizar estado
        tool_results = state.get("tool_results", {})
        
        for call in approved_calls:
            tool_results[call.get("id")] = {
                "status": "approved",
                "approved": True
            }
        
        for call in rejected_calls:
            tool_results[call.get("id")] = {
                "status": "rejected",
                "approved": False
            }
        
        return {
            "pending_tool_calls": [],
            "tool_results": tool_results,
            "awaiting_human": False
        }


# =============================================================================
# DECORADORES
# =============================================================================

def requires_approval(reason: str = "Esta operación requiere aprobación"):
    """
    Decorador para marcar funciones que requieren aprobación humana.
    """
    def decorator(func):
        func._requires_approval = True
        func._approval_reason = reason
        return func
    return decorator


def human_input(prompt: str):
    """
    Decorador para funciones que necesitan input humano.
    """
    def decorator(func):
        func._requires_human_input = True
        func._human_input_prompt = prompt
        return func
    return decorator


# =============================================================================
# FACTORY
# =============================================================================

def create_hitl_manager(
    mode: str = "console",
    auto_approve_safe: bool = False,
    approval_callback: Optional[Callable] = None
) -> HITLManager:
    """
    Factory para crear el gestor HITL.
    """
    if mode == "console":
        handler = ConsoleHITLHandler(
            auto_approve_safe_operations=auto_approve_safe
        )
    elif mode == "callback":
        handler = CallbackHITLHandler(
            approval_callback=approval_callback
        )
    else:
        handler = ConsoleHITLHandler()
    
    return HITLManager(handler=handler)
