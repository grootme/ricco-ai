"""
Ciclo PPCC (Proper Prompt Chat Cycle)

Implementación del proceso iterativo que asegura la coordinación efectiva
entre el usuario humano y el agente.

Fases:
1. Preparación: Definir pre-trasfondo de obviedad
2. Alineación (Revelación): Agente reformula y confirma entendimiento
3. Ejecución: Agente opera en sandbox con razonamiento visible
4. Declaración: Cierre formal con satisfacción/insatisfacción
"""

from typing import Optional, Dict, Any, Callable, List
from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime
import asyncio
import uuid

from .obviousness import ObviousnessContext, ObviousnessContextBuilder


class PPCCPhase(str, Enum):
    """Fases del ciclo PPCC"""
    PREPARATION = "preparation"
    ALIGNMENT = "alignment"
    EXECUTION = "execution"
    DECLARATION = "declaration"
    COMPLETED = "completed"


class PPCCState(BaseModel):
    """Estado del ciclo PPCC"""
    cycle_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    current_phase: PPCCPhase = PPCCPhase.PREPARATION
    obviousness_context: Optional[Dict[str, Any]] = None
    alignment_confirmed: bool = False
    agent_understanding: Optional[str] = None
    execution_results: Optional[Dict[str, Any]] = None
    satisfaction_declared: Optional[bool] = None
    satisfaction_feedback: Optional[str] = None
    iteration_count: int = 0
    max_iterations: int = 5
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    errors: List[str] = Field(default_factory=list)


class PPCCError(Exception):
    """Error en el ciclo PPCC"""
    def __init__(self, message: str, phase: PPCCPhase, state: PPCCState):
        self.message = message
        self.phase = phase
        self.state = state
        super().__init__(message)


class AlignmentRequiredError(PPCCError):
    """Se requiere alineación antes de ejecutar"""
    pass


class ExecutionBlockedError(PPCCError):
    """Ejecución bloqueada - requiere confirmación"""
    pass


class PPCCCycle:
    """
    Implementación del ciclo PPCC (Proper Prompt Chat Cycle)
    
    Este ciclo transforma la interacción en un flujo de compromisos verificables,
    previniendo la ejecución ciega y haciendo visibles los supuestos implícitos.
    
    Usage:
        cycle = PPCCCycle(agent_executor)
        
        # Fase 1: Preparación
        await cycle.prepare({
            "objective": "Analizar datos de ventas",
            "user_id": "user-001"
        })
        
        # Fase 2: Alineación
        understanding = await cycle.request_alignment()
        confirmed = await cycle.confirm_alignment(understanding)
        
        # Fase 3: Ejecución
        result = await cycle.execute("Ejecutar análisis")
        
        # Fase 4: Declaración
        final = await cycle.declare_result(satisfaction=True)
    """
    
    def __init__(
        self,
        agent_executor: Optional[Callable] = None,
        max_iterations: int = 5
    ):
        """
        Inicializa el ciclo PPCC.
        
        Args:
            agent_executor: Función async que ejecuta tareas del agente
            max_iterations: Máximo de iteraciones antes de forzar cierre
        """
        self.agent_executor = agent_executor
        self.state = PPCCState(max_iterations=max_iterations)
        self._on_phase_change: Optional[Callable] = None
        self._on_alignment_request: Optional[Callable] = None
    
    def on_phase_change(self, callback: Callable) -> 'PPCCCycle':
        """Registra callback para cambios de fase"""
        self._on_phase_change = callback
        return self
    
    def on_alignment_request(self, callback: Callable) -> 'PPCCCycle':
        """Registra callback para solicitudes de alineación"""
        self._on_alignment_request = callback
        return self
    
    async def _emit_phase_change(self, old_phase: PPCCPhase, new_phase: PPCCPhase):
        """Emite evento de cambio de fase"""
        if self._on_phase_change:
            await self._on_phase_change(
                cycle_id=self.state.cycle_id,
                old_phase=old_phase,
                new_phase=new_phase,
                state=self.state
            )
    
    # =========================================================================
    # FASE 1: PREPARACIÓN
    # =========================================================================
    
    async def prepare(
        self,
        user_request: Dict[str, Any],
        context_builder: Optional[ObviousnessContextBuilder] = None
    ) -> Dict[str, Any]:
        """
        Fase 1: Preparación del Trasfondo de Obviedad
        
        Este paso es crucial para fijar el mundo en el que el problema
        será resuelto antes de que el modelo comience a generar tokens.
        
        Args:
            user_request: Request del usuario con objetivo, métricas, etc.
            context_builder: Builder opcional para contexto pre-configurado
        
        Returns:
            Dict con el contexto preparado y system_prompt generado
        """
        old_phase = self.state.current_phase
        self.state.current_phase = PPCCPhase.PREPARATION
        
        # Construir contexto SMART+R+T
        if context_builder:
            context = context_builder.build()
        else:
            builder = ObviousnessContextBuilder(
                session_id=user_request.get("session_id", str(uuid.uuid4())),
                user_id=user_request.get("user_id", "unknown")
            )
            
            # Configurar desde request
            if "objective" in user_request:
                builder.with_objective(
                    user_request["objective"],
                    user_request.get("success_criteria"),
                    user_request.get("deliverables")
                )
            
            if any(k in user_request for k in ["recall", "precision", "f1"]):
                builder.with_metrics(
                    recall=user_request.get("recall"),
                    precision=user_request.get("precision"),
                    f1=user_request.get("f1")
                )
            
            if "boundaries" in user_request:
                b = user_request["boundaries"]
                builder.with_boundaries(
                    allow=b.get("allow"),
                    deny=b.get("deny"),
                    tools=b.get("tools"),
                    sandbox=b.get("sandbox", True)
                )
            
            if "relevance" in user_request:
                r = user_request["relevance"]
                builder.with_relevance(
                    impact=r.get("impact", "medium"),
                    ccv=r.get("ccv", 5)
                )
            
            if "time" in user_request:
                t = user_request["time"]
                builder.with_time(
                    priority=t.get("priority", "normal"),
                    timeout=t.get("timeout"),
                    latency=t.get("latency")
                )
            
            context = builder.build()
        
        self.state.obviousness_context = context.model_dump()
        
        await self._emit_phase_change(old_phase, self.state.current_phase)
        
        return {
            "phase": "preparation",
            "cycle_id": self.state.cycle_id,
            "context": context.to_compact_format(),
            "system_prompt": context.to_system_prompt(),
            "next_step": "alignment"
        }
    
    # =========================================================================
    # FASE 2: ALINEACIÓN (REVELACIÓN)
    # =========================================================================
    
    async def request_alignment(self) -> Dict[str, Any]:
        """
        Fase 2: Solicitar Alineación
        
        El agente debe reformular el objetivo en sus propias palabras y
        proponer mejoras o identificar inconsistencias.
        
        IMPORTANTE: El sistema prohíbe la ejecución hasta que exista
        una declaración de entendimiento mutuo.
        
        Returns:
            Dict con prompt de alineación y estado
        """
        if not self.state.obviousness_context:
            raise PPCCError(
                "Preparación requerida antes de alineación",
                PPCCPhase.PREPARATION,
                self.state
            )
        
        old_phase = self.state.current_phase
        self.state.current_phase = PPCCPhase.ALIGNMENT
        
        context = ObviousnessContext(**self.state.obviousness_context)
        
        # Generar prompt de alineación
        alignment_prompt = self._generate_alignment_prompt(context)
        
        # Emitir evento de solicitud de alineación
        if self._on_alignment_request:
            await self._on_alignment_request(
                cycle_id=self.state.cycle_id,
                prompt=alignment_prompt,
                context=context
            )
        
        await self._emit_phase_change(old_phase, self.state.current_phase)
        
        return {
            "phase": "alignment",
            "cycle_id": self.state.cycle_id,
            "alignment_prompt": alignment_prompt,
            "execution_blocked": True,
            "blocked_reason": "Alineación requerida antes de ejecutar",
            "instructions": [
                "Reformula el objetivo en tus propias palabras",
                "Identifica posibles inconsistencias o ambigüedades",
                "Propón mejoras si las encuentras",
                "Confirma tu entendimiento explícitamente"
            ]
        }
    
    def _generate_alignment_prompt(self, context: ObviousnessContext) -> str:
        """Genera el prompt de solicitud de alineación"""
        return f"""
# SOLICITUD DE ALINEACIÓN SEMÁNTICA

Antes de proceder con la ejecución, debes confirmar tu entendimiento del objetivo.

## Contexto del Objetivo

{context.to_system_prompt()}

## Tu Tarea

1. **Reformula** el objetivo en tus propias palabras
2. **Identifica** cualquier ambigüedad o inconsistencia
3. **Propón** mejoras si las consideras necesarias
4. **Confirma** explícitamente tu entendimiento

## Formato de Respuesta Esperado

```
ENTENDIMIENTO:
[Reformulación del objetivo en tus palabras]

AMBIGÜEDADES DETECTADAS:
- [Lista de ambigüedades o "Ninguna"]

MEJORAS PROPUESTAS:
- [Lista de mejoras o "Ninguna"]

CONFIRMACIÓN: [ENTENDIDO / NECESITO ACLARACIÓN]
```

⚠️ **IMPORTANTE**: No procedas con la ejecución hasta que exista 
confirmación mutua del entendimiento.
"""
    
    async def confirm_alignment(
        self,
        agent_understanding: str,
        user_confirmed: bool = True
    ) -> Dict[str, Any]:
        """
        Confirma la alineación del agente con el objetivo.
        
        Este paso previene la ejecución ciega y hace visibles los
        supuestos implícitos.
        
        Args:
            agent_understanding: Declaración del agente de su entendimiento
            user_confirmed: Si el usuario confirma la alineación
        
        Returns:
            Dict con estado de alineación
        """
        self.state.agent_understanding = agent_understanding
        
        if not user_confirmed:
            # Usuario no confirma - volver a preparación
            self.state.current_phase = PPCCPhase.PREPARATION
            self.state.iteration_count += 1
            
            if self.state.iteration_count >= self.state.max_iterations:
                raise PPCCError(
                    "Máximo de iteraciones de alineación alcanzado",
                    PPCCPhase.ALIGNMENT,
                    self.state
                )
            
            return {
                "phase": "alignment",
                "status": "not_confirmed",
                "iteration": self.state.iteration_count,
                "next_step": "reprepare"
            }
        
        self.state.alignment_confirmed = True
        self.state.current_phase = PPCCPhase.EXECUTION
        
        return {
            "phase": "alignment",
            "status": "confirmed",
            "agent_understanding": agent_understanding,
            "next_step": "execution"
        }
    
    # =========================================================================
    # FASE 3: EJECUCIÓN
    # =========================================================================
    
    async def execute(
        self,
        task: str,
        visible_reasoning: bool = True,
        checkpoint_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Fase 3: Ejecución con razonamiento visible
        
        El agente opera dentro de su sandbox, haciendo visible su razonamiento.
        La ejecución no es opaca; es explícita y auditable.
        
        Args:
            task: Tarea específica a ejecutar
            visible_reasoning: Si el razonamiento debe ser visible
            checkpoint_callback: Callback para checkpoints durante ejecución
        
        Returns:
            Dict con resultados de la ejecución
        """
        if not self.state.alignment_confirmed:
            raise AlignmentRequiredError(
                "Alineación requerida antes de ejecutar",
                PPCCPhase.ALIGNMENT,
                self.state
            )
        
        old_phase = self.state.current_phase
        self.state.current_phase = PPCCPhase.EXECUTION
        
        if not self.agent_executor:
            # Sin executor - modo simulación
            self.state.execution_results = {
                "status": "simulated",
                "task": task,
                "visible_reasoning": visible_reasoning
            }
        else:
            # Ejecutar con el agente
            try:
                result = await self.agent_executor(
                    task=task,
                    context=self.state.obviousness_context,
                    visible_reasoning=visible_reasoning,
                    checkpoint_callback=checkpoint_callback
                )
                self.state.execution_results = result
            except Exception as e:
                self.state.errors.append(str(e))
                self.state.execution_results = {
                    "status": "error",
                    "error": str(e)
                }
        
        await self._emit_phase_change(old_phase, self.state.current_phase)
        
        return {
            "phase": "execution",
            "cycle_id": self.state.cycle_id,
            "results": self.state.execution_results,
            "reasoning_visible": visible_reasoning,
            "next_step": "declaration"
        }
    
    # =========================================================================
    # FASE 4: DECLARACIÓN DE RESULTADO
    # =========================================================================
    
    async def declare_result(
        self,
        satisfaction: bool,
        feedback: str = "",
        harvest_knowledge: bool = True
    ) -> Dict[str, Any]:
        """
        Fase 4: Declaración de Resultado
        
        El ciclo solo se cierra con una declaración formal de satisfacción
        o insatisfacción. La insatisfacción no se trata como un error,
        sino como información estructural para reentrenamiento.
        
        Args:
            satisfaction: Si el usuario está satisfecho con el resultado
            feedback: Feedback opcional del usuario
            harvest_knowledge: Si se debe cosechar conocimiento (Ralph Loop)
        
        Returns:
            Dict con estado final y métricas
        """
        old_phase = self.state.current_phase
        self.state.current_phase = PPCCPhase.DECLARATION
        self.state.satisfaction_declared = satisfaction
        self.state.satisfaction_feedback = feedback
        
        result = {
            "phase": "declaration",
            "cycle_id": self.state.cycle_id,
            "satisfaction": satisfaction,
            "feedback": feedback,
            "iterations": self.state.iteration_count,
            "duration_seconds": (
                datetime.utcnow() - self.state.started_at
            ).total_seconds()
        }
        
        if not satisfaction:
            # Insatisfacción = información estructural para mejora
            result["action"] = "ralph_loop_harvest" if harvest_knowledge else "retry"
            result["errors"] = self.state.errors
            result["learning_opportunity"] = {
                "objective": self.state.obviousness_context.get("objective"),
                "agent_understanding": self.state.agent_understanding,
                "execution_result": self.state.execution_results,
                "user_feedback": feedback
            }
        else:
            # Satisfacción = Capital Cognitivo ganado
            ccv = self.state.obviousness_context.get("cognitive_capital_value", 5)
            result["cognitive_capital_earned"] = ccv
            result["harvest_recommended"] = harvest_knowledge
        
        # Cerrar ciclo
        self.state.current_phase = PPCCPhase.COMPLETED
        self.state.completed_at = datetime.utcnow()
        
        await self._emit_phase_change(old_phase, self.state.current_phase)
        
        return result
    
    # =========================================================================
    # UTILIDADES
    # =========================================================================
    
    def get_state(self) -> Dict[str, Any]:
        """Obtiene el estado actual del ciclo"""
        return self.state.model_dump()
    
    def can_execute(self) -> bool:
        """Verifica si el ciclo puede proceder a ejecución"""
        return (
            self.state.current_phase == PPCCPhase.EXECUTION and
            self.state.alignment_confirmed and
            self.state.obviousness_context is not None
        )
    
    def get_system_prompt(self) -> Optional[str]:
        """Obtiene el system prompt del contexto actual"""
        if not self.state.obviousness_context:
            return None
        context = ObviousnessContext(**self.state.obviousness_context)
        return context.to_system_prompt()
    
    async def abort(self, reason: str) -> Dict[str, Any]:
        """Aborta el ciclo"""
        self.state.current_phase = PPCCPhase.COMPLETED
        self.state.completed_at = datetime.utcnow()
        self.state.errors.append(f"Aborted: {reason}")
        
        return {
            "phase": "aborted",
            "cycle_id": self.state.cycle_id,
            "reason": reason,
            "state": self.state.model_dump()
        }
