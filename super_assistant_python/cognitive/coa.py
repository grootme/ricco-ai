"""
Chat of Action (COA) - Metodología de Conversación para Acción
===============================================================

Implementación del modelo de conversación estructurada para 
coordinar acciones entre humanos y agentes de IA.

Basado en "Promptología Ontológica" de Mauricio Quiroga:

"Las conversaciones no son solo intercambio de información,
sino actos de coordinación que generan compromisos y acciones."

4 ETAPAS DEL COA:
1. PREPARACIÓN: Establecer contexto y condiciones de satisfacción
2. ALINEACIÓN: Lograr acuerdo sobre objetivo y método
3. EJECUCIÓN: Realizar la acción acordada
4. DECLARACIÓN DE RESULTADO: Reportar y validar resultado
"""

import asyncio
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Awaitable
from uuid import UUID, uuid4
import json

from pydantic import BaseModel, Field


class COAStage(str, Enum):
    """Etapas del Chat of Action"""
    PREPARATION = "PREPARATION"           # Preparación de la acción
    ALIGNMENT = "ALIGNMENT"               # Alineación de expectativas
    EXECUTION = "EXECUTION"               # Ejecución de la acción
    RESULT_DECLARATION = "RESULT_DECLARATION"  # Declaración de resultado


class CommitmentStatus(str, Enum):
    """Estados de un compromiso"""
    PENDING = "PENDING"                   # Pendiente de aceptación
    ACCEPTED = "ACCEPTED"                 # Aceptado por ambas partes
    IN_PROGRESS = "IN_PROGRESS"           # En ejecución
    COMPLETED = "COMPLETED"               # Completado exitosamente
    FAILED = "FAILED"                     # Fallido
    CANCELLED = "CANCELLED"               # Cancelado
    DISPUTED = "DISPUTED"                 # En disputa/revisión


class SatisfactionLevel(str, Enum):
    """Niveles de satisfacción del resultado"""
    EXCEEDED = "EXCEEDED"                 # Excede expectativas
    SATISFIED = "SATISFIED"               # Satisface condiciones
    PARTIALLY = "PARTIALLY"               # Parcialmente satisfecho
    UNSATISFIED = "UNSATISFIED"           # No satisface
    DISPUTED = "DISPUTED"                 # En disputa


class ActionCommitment(BaseModel):
    """Compromiso de acción"""
    id: UUID = Field(default_factory=uuid4)
    
    # Qué se compromete
    action: str                                    # La acción a realizar
    conditions_of_satisfaction: List[str]          # Condiciones de satisfacción
    deliverables: List[str] = Field(default_factory=list)  # Entregables
    
    # Quién se compromete
    committed_by: str                              # Quien hace el compromiso
    committed_to: Optional[str] = None             # A quien se hace el compromiso
    
    # Tiempos
    deadline: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Estado
    status: CommitmentStatus = CommitmentStatus.PENDING
    
    # Validación
    accepted_at: Optional[datetime] = None
    accepted_by: Optional[str] = None
    completion_declared_at: Optional[datetime] = None
    satisfaction_declared_at: Optional[datetime] = None
    
    # Resultado
    result: Optional[Dict[str, Any]] = None
    satisfaction_level: Optional[SatisfactionLevel] = None
    satisfaction_notes: Optional[str] = None


class COAContext(BaseModel):
    """Contexto de una conversación de acción"""
    id: UUID = Field(default_factory=uuid4)
    session_id: Optional[UUID] = None
    
    # Etapa actual
    current_stage: COAStage = COAStage.PREPARATION
    
    # Preparación
    initial_request: Optional[str] = None
    context: Dict[str, Any] = Field(default_factory=dict)
    
    # Alineación
    proposed_commitment: Optional[ActionCommitment] = None
    clarifications: List[str] = Field(default_factory=list)
    alignment_iterations: int = 0
    
    # Ejecución
    active_commitment: Optional[ActionCommitment] = None
    progress_updates: List[Dict[str, Any]] = Field(default_factory=list)
    blockers: List[str] = Field(default_factory=list)
    
    # Resultado
    declared_result: Optional[Dict[str, Any]] = None
    validation_requests: List[str] = Field(default_factory=list)
    final_satisfaction: Optional[SatisfactionLevel] = None
    
    # Historial
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Métricas
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    total_duration_ms: int = 0
    
    class Config:
        use_enum_values = True


class COAResult(BaseModel):
    """Resultado de una conversación de acción"""
    context_id: UUID
    success: bool
    satisfaction_level: Optional[SatisfactionLevel] = None
    result: Optional[Dict[str, Any]] = None
    stages_completed: List[str] = Field(default_factory=list)
    commitment_fulfilled: bool = False
    total_duration_ms: int = 0
    learnings: List[str] = Field(default_factory=list)
    error: Optional[str] = None


class ChatOfAction:
    """
    Motor del Chat of Action.
    
    Coordina conversaciones que generan acciones y compromisos.
    
    Principios (basados en Promptología Ontológica y C4A de Flores):
    1. Las conversaciones generan compromisos
    2. Los compromisos tienen condiciones de satisfacción
    3. La ejecución sigue a la alineación
    4. El resultado debe ser declarado y validado
    5. La satisfacción es mutua (no unilateral)
    """
    
    def __init__(
        self,
        agent_id: UUID,
        llm_client: Optional[Any] = None,
        hitl_callback: Optional[Callable[[Dict[str, Any]], Awaitable[Dict[str, Any]]]] = None
    ):
        self.agent_id = agent_id
        self.llm_client = llm_client
        self.hitl_callback = hitl_callback
        
        # Contextos activos
        self._active_contexts: Dict[UUID, COAContext] = {}
        
        # Compromisos
        self._commitments: Dict[UUID, ActionCommitment] = {}
        
        # Callbacks
        self._on_stage_change: Optional[Callable[[COAStage, COAContext], Awaitable[None]]] = None
        self._on_commitment_created: Optional[Callable[[ActionCommitment], Awaitable[None]]] = None
    
    # ==========================================
    # CICLO PRINCIPAL
    # ==========================================
    
    async def initiate_conversation(
        self,
        request: str,
        context: Optional[Dict[str, Any]] = None,
        session_id: Optional[UUID] = None
    ) -> COAContext:
        """
        Iniciar una nueva conversación de acción.
        
        Args:
            request: Solicitud inicial del usuario
            context: Contexto adicional
            session_id: ID de sesión
            
        Returns:
            Contexto COA creado
        """
        ctx = COAContext(
            id=uuid4(),
            session_id=session_id,
            initial_request=request,
            context=context or {},
            current_stage=COAStage.PREPARATION
        )
        
        self._active_contexts[ctx.id] = ctx
        
        # Registrar en historial
        ctx.conversation_history.append({
            "role": "user",
            "content": request,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return ctx
    
    async def process_response(
        self,
        ctx_id: UUID,
        response: str,
        role: str = "assistant"
    ) -> Dict[str, Any]:
        """
        Procesar una respuesta en la conversación.
        
        Args:
            ctx_id: ID del contexto
            response: Contenido de la respuesta
            role: Rol del emisor
            
        Returns:
            Estado actualizado
        """
        ctx = self._active_contexts.get(ctx_id)
        if not ctx:
            return {"error": "Context not found"}
        
        # Registrar en historial
        ctx.conversation_history.append({
            "role": role,
            "content": response,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Procesar según etapa actual
        if ctx.current_stage == COAStage.PREPARATION:
            return await self._process_preparation_response(ctx, response, role)
        elif ctx.current_stage == COAStage.ALIGNMENT:
            return await self._process_alignment_response(ctx, response, role)
        elif ctx.current_stage == COAStage.EXECUTION:
            return await self._process_execution_response(ctx, response, role)
        elif ctx.current_stage == COAStage.RESULT_DECLARATION:
            return await self._process_result_response(ctx, response, role)
        
        return {"stage": ctx.current_stage}
    
    async def advance_stage(
        self,
        ctx_id: UUID
    ) -> Optional[COAStage]:
        """Avanzar a la siguiente etapa"""
        ctx = self._active_contexts.get(ctx_id)
        if not ctx:
            return None
        
        stages = list(COAStage)
        current_idx = stages.index(COAStage(ctx.current_stage))
        
        if current_idx < len(stages) - 1:
            next_stage = stages[current_idx + 1]
            ctx.current_stage = next_stage
            
            if self._on_stage_change:
                await self._on_stage_change(next_stage, ctx)
            
            return next_stage
        
        return None
    
    # ==========================================
    # ETAPA 1: PREPARACIÓN
    # ==========================================
    
    async def _process_preparation_response(
        self,
        ctx: COAContext,
        response: str,
        role: str
    ) -> Dict[str, Any]:
        """
        Procesar respuesta en etapa de preparación.
        
        Objetivo: Entender completamente la solicitud y
        establecer las condiciones para la alineación.
        """
        if role == "user":
            # Analizar solicitud del usuario
            analysis = await self._analyze_request(response)
            ctx.context["request_analysis"] = analysis
            
            # Proponer compromiso inicial
            commitment = await self._propose_commitment(ctx, analysis)
            ctx.proposed_commitment = commitment
            
            # Avanzar a alineación
            await self.advance_stage(ctx.id)
            
            return {
                "stage": "ALIGNMENT",
                "proposed_commitment": commitment.model_dump(),
                "clarifications_needed": analysis.get("clarifications", [])
            }
        
        return {"stage": ctx.current_stage}
    
    async def _analyze_request(self, request: str) -> Dict[str, Any]:
        """Analizar solicitud del usuario"""
        # TODO: Implementar con LLM real
        return {
            "action": request,
            "conditions": [],
            "clarifications": [],
            "complexity": "medium"
        }
    
    async def _propose_commitment(
        self,
        ctx: COAContext,
        analysis: Dict[str, Any]
    ) -> ActionCommitment:
        """Proponer un compromiso basado en el análisis"""
        commitment = ActionCommitment(
            id=uuid4(),
            action=analysis.get("action", ctx.initial_request),
            conditions_of_satisfaction=analysis.get("conditions", ["Completar la tarea solicitada"]),
            committed_by=str(self.agent_id),
            committed_to=ctx.context.get("user_id"),
            status=CommitmentStatus.PENDING
        )
        
        self._commitments[commitment.id] = commitment
        
        if self._on_commitment_created:
            await self._on_commitment_created(commitment)
        
        return commitment
    
    # ==========================================
    # ETAPA 2: ALINEACIÓN
    # ==========================================
    
    async def _process_alignment_response(
        self,
        ctx: COAContext,
        response: str,
        role: str
    ) -> Dict[str, Any]:
        """
        Procesar respuesta en etapa de alineación.
        
        Objetivo: Lograr acuerdo sobre el compromiso y
        las condiciones de satisfacción.
        """
        if not ctx.proposed_commitment:
            return {"error": "No proposed commitment"}
        
        if role == "user":
            # Verificar si el usuario acepta, rechaza o pide clarificación
            response_lower = response.lower()
            
            if any(word in response_lower for word in ["sí", "acepto", "ok", "de acuerdo", "adelante"]):
                # Aceptar compromiso
                ctx.proposed_commitment.status = CommitmentStatus.ACCEPTED
                ctx.proposed_commitment.accepted_at = datetime.utcnow()
                ctx.proposed_commitment.accepted_by = ctx.context.get("user_id")
                
                ctx.active_commitment = ctx.proposed_commitment
                
                # Avanzar a ejecución
                await self.advance_stage(ctx.id)
                
                return {
                    "stage": "EXECUTION",
                    "commitment_accepted": True,
                    "commitment_id": str(ctx.active_commitment.id)
                }
            
            elif any(word in response_lower for word in ["no", "rechazo", "espera"]):
                # Solicitar modificación
                ctx.alignment_iterations += 1
                
                # Re-analizar y proponer nuevo compromiso
                if ctx.alignment_iterations < 3:
                    analysis = await self._analyze_request(response)
                    commitment = await self._propose_commitment(ctx, analysis)
                    ctx.proposed_commitment = commitment
                    
                    return {
                        "stage": "ALIGNMENT",
                        "commitment_revised": True,
                        "new_proposal": commitment.model_dump()
                    }
                else:
                    # Demasiadas iteraciones, cancelar
                    ctx.proposed_commitment.status = CommitmentStatus.CANCELLED
                    return {
                        "stage": "CANCELLED",
                        "reason": "Alignment failed after multiple attempts"
                    }
            
            else:
                # Clarificación
                ctx.clarifications.append(response)
                return {
                    "stage": "ALIGNMENT",
                    "clarification_registered": True
                }
        
        return {"stage": ctx.current_stage}
    
    # ==========================================
    # ETAPA 3: EJECUCIÓN
    # ==========================================
    
    async def _process_execution_response(
        self,
        ctx: COAContext,
        response: str,
        role: str
    ) -> Dict[str, Any]:
        """
        Procesar respuesta en etapa de ejecución.
        
        Objetivo: Ejecutar la acción y reportar progreso.
        """
        if role == "assistant" and ctx.active_commitment:
            # Registrar progreso
            progress = {
                "content": response,
                "timestamp": datetime.utcnow().isoformat(),
                "commitment_id": str(ctx.active_commitment.id)
            }
            ctx.progress_updates.append(progress)
            
            # Verificar si la ejecución está completa
            if self._is_execution_complete(response):
                ctx.active_commitment.status = CommitmentStatus.COMPLETED
                ctx.active_commitment.completion_declared_at = datetime.utcnow()
                
                # Avanzar a declaración de resultado
                await self.advance_stage(ctx.id)
                
                return {
                    "stage": "RESULT_DECLARATION",
                    "execution_complete": True
                }
            
            return {
                "stage": "EXECUTION",
                "progress_registered": True
            }
        
        return {"stage": ctx.current_stage}
    
    def _is_execution_complete(self, response: str) -> bool:
        """Verificar si la ejecución está completa"""
        # TODO: Implementar detección más sofisticada
        completion_markers = ["completado", "terminado", "listo", "finalizado", "hecho"]
        return any(marker in response.lower() for marker in completion_markers)
    
    async def declare_result(
        self,
        ctx_id: UUID,
        result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Declarar resultado de la ejecución.
        
        Args:
            ctx_id: ID del contexto
            result: Resultado a declarar
            
        Returns:
            Estado de la declaración
        """
        ctx = self._active_contexts.get(ctx_id)
        if not ctx:
            return {"error": "Context not found"}
        
        ctx.declared_result = result
        
        if ctx.active_commitment:
            ctx.active_commitment.result = result
        
        return {
            "result_declared": True,
            "awaiting_validation": True
        }
    
    # ==========================================
    # ETAPA 4: DECLARACIÓN DE RESULTADO
    # ==========================================
    
    async def _process_result_response(
        self,
        ctx: COAContext,
        response: str,
        role: str
    ) -> Dict[str, Any]:
        """
        Procesar respuesta en etapa de declaración de resultado.
        
        Objetivo: Validar el resultado y declarar satisfacción.
        """
        if role == "user" and ctx.active_commitment:
            response_lower = response.lower()
            
            # Determinar nivel de satisfacción
            if any(word in response_lower for word in ["excelente", "perfecto", "genial", "increíble"]):
                satisfaction = SatisfactionLevel.EXCEEDED
            elif any(word in response_lower for word in ["bien", "correcto", "sí", "ok"]):
                satisfaction = SatisfactionLevel.SATISFIED
            elif any(word in response_lower for word in ["parcial", "más o menos", "casi"]):
                satisfaction = SatisfactionLevel.PARTIALLY
            elif any(word in response_lower for word in ["mal", "incorrecto", "no", "error"]):
                satisfaction = SatisfactionLevel.UNSATISFIED
            else:
                satisfaction = SatisfactionLevel.SATISFIED
            
            ctx.final_satisfaction = satisfaction
            ctx.active_commitment.satisfaction_level = satisfaction
            ctx.active_commitment.satisfaction_notes = response
            ctx.active_commitment.satisfaction_declared_at = datetime.utcnow()
            
            # Finalizar conversación
            ctx.completed_at = datetime.utcnow()
            ctx.total_duration_ms = int(
                (ctx.completed_at - ctx.created_at).total_seconds() * 1000
            )
            
            return {
                "stage": "COMPLETED",
                "satisfaction": satisfaction.value,
                "commitment_fulfilled": satisfaction in [
                    SatisfactionLevel.EXCEEDED,
                    SatisfactionLevel.SATISFIED
                ]
            }
        
        return {"stage": ctx.current_stage}
    
    # ==========================================
    # GESTIÓN DE COMPROMISOS
    # ==========================================
    
    async def get_commitment(self, commitment_id: UUID) -> Optional[ActionCommitment]:
        """Obtener un compromiso por ID"""
        return self._commitments.get(commitment_id)
    
    async def get_active_commitments(self) -> List[ActionCommitment]:
        """Obtener todos los compromisos activos"""
        return [
            c for c in self._commitments.values()
            if c.status in [CommitmentStatus.ACCEPTED, CommitmentStatus.IN_PROGRESS]
        ]
    
    async def cancel_commitment(
        self,
        commitment_id: UUID,
        reason: str
    ) -> bool:
        """Cancelar un compromiso"""
        commitment = self._commitments.get(commitment_id)
        if not commitment:
            return False
        
        commitment.status = CommitmentStatus.CANCELLED
        commitment.satisfaction_notes = f"Cancelled: {reason}"
        
        return True
    
    # ==========================================
    # UTILIDADES
    # ==========================================
    
    def get_context(self, ctx_id: UUID) -> Optional[COAContext]:
        """Obtener contexto por ID"""
        return self._active_contexts.get(ctx_id)
    
    async def get_conversation_summary(self, ctx_id: UUID) -> Optional[Dict[str, Any]]:
        """Obtener resumen de la conversación"""
        ctx = self._active_contexts.get(ctx_id)
        if not ctx:
            return None
        
        return {
            "context_id": str(ctx.id),
            "session_id": str(ctx.session_id) if ctx.session_id else None,
            "current_stage": ctx.current_stage,
            "initial_request": ctx.initial_request,
            "commitment": ctx.active_commitment.model_dump() if ctx.active_commitment else None,
            "satisfaction": ctx.final_satisfaction.value if ctx.final_satisfaction else None,
            "messages_count": len(ctx.conversation_history),
            "duration_ms": ctx.total_duration_ms
        }
    
    async def export_conversation(
        self,
        ctx_id: UUID,
        format: str = "json"
    ) -> Optional[str]:
        """Exportar conversación a formato específico"""
        ctx = self._active_contexts.get(ctx_id)
        if not ctx:
            return None
        
        if format == "json":
            return ctx.model_dump_json(indent=2)
        else:
            # Formato texto legible
            lines = [
                f"=== Chat of Action ===",
                f"Request: {ctx.initial_request}",
                f"Stage: {ctx.current_stage}",
                "",
                "=== Conversation ==="
            ]
            
            for msg in ctx.conversation_history:
                lines.append(f"[{msg['role']}]: {msg['content']}")
            
            if ctx.final_satisfaction:
                lines.append(f"\nSatisfaction: {ctx.final_satisfaction.value}")
            
            return "\n".join(lines)
