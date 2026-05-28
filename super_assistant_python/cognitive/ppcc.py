"""
PPCC - Proper Prompt Chat Cycle
================================

Implementación del ciclo estructurado de interacción Humano-LLM.

Basado en "Promptología Ontológica" de Mauricio Quiroga:

El PPCC tiene 4 fases:
1. PREPARACIÓN: Establecer contexto y objetivo
2. REVELACIÓN: El LLM revela su comprensión
3. EJECUCIÓN: Realizar la tarea
4. DESTILACIÓN: Extraer aprendizaje y consolidar

Este ciclo asegura que cada interacción sea:
- Estructurada
- Reproducible
- Acumulativa (contribuye al Capital Cognitivo)
"""

import asyncio
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Awaitable
from uuid import UUID, uuid4
import json

from pydantic import BaseModel, Field

from .capital import CognitiveCapital, CapitalType


class PPCCPhase(str, Enum):
    """Fases del ciclo PPCC"""
    PREPARATION = "PREPARATION"     # Preparación del contexto
    REVELATION = "REVELATION"       # Revelación de comprensión
    EXECUTION = "EXECUTION"         # Ejecución de la tarea
    DISTILLATION = "DISTILLATION"   # Destilación del aprendizaje


class PPCCContext(BaseModel):
    """Contexto de un ciclo PPCC"""
    id: UUID = Field(default_factory=uuid4)
    session_id: Optional[UUID] = None
    
    # Fase actual
    current_phase: PPCCPhase = PPCCPhase.PREPARATION
    
    # Contexto de preparación
    objective: Optional[str] = None
    constraints: List[str] = Field(default_factory=list)
    context_data: Dict[str, Any] = Field(default_factory=dict)
    obviousness_context: Dict[str, Any] = Field(default_factory=dict)
    
    # Revelación
    revealed_understanding: Optional[str] = None
    clarifications_needed: List[str] = Field(default_factory=list)
    
    # Ejecución
    execution_plan: Optional[str] = None
    execution_steps: List[Dict[str, Any]] = Field(default_factory=list)
    intermediate_results: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Resultado final
    final_result: Optional[Dict[str, Any]] = None
    
    # Destilación
    learnings: List[str] = Field(default_factory=list)
    capital_deposited: List[str] = Field(default_factory=list)
    improvements_suggested: List[str] = Field(default_factory=list)
    
    # Metadatos
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    total_tokens: int = 0
    total_duration_ms: int = 0
    
    class Config:
        use_enum_values = True


class PPCCStep(BaseModel):
    """Paso individual dentro de una fase"""
    id: UUID = Field(default_factory=uuid4)
    phase: PPCCPhase
    name: str
    description: Optional[str] = None
    input: Dict[str, Any] = Field(default_factory=dict)
    output: Optional[Dict[str, Any]] = None
    status: str = "pending"  # pending, running, completed, failed
    duration_ms: Optional[int] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PPCCResult(BaseModel):
    """Resultado de un ciclo PPCC completo"""
    context_id: UUID
    success: bool
    result: Optional[Dict[str, Any]] = None
    learnings: List[str] = Field(default_factory=list)
    capital_entries_created: int = 0
    total_duration_ms: int = 0
    phases_completed: List[str] = Field(default_factory=list)
    error: Optional[str] = None


class PPCC:
    """
    Motor del Proper Prompt Chat Cycle.
    
    Orquesta el ciclo completo de interacción Humano-LLM
    asegurando estructura, reproducibilidad y acumulación.
    """
    
    def __init__(
        self,
        capital: CognitiveCapital,
        llm_client: Optional[Any] = None
    ):
        self.capital = capital
        self.llm_client = llm_client
        
        # Contextos activos
        self._active_contexts: Dict[UUID, PPCCContext] = {}
        
        # Callbacks
        self._on_phase_start: Optional[Callable[[PPCCPhase, PPCCContext], Awaitable[None]]] = None
        self._on_phase_complete: Optional[Callable[[PPCCPhase, PPCCContext], Awaitable[None]]] = None
        self._on_step_complete: Optional[Callable[[PPCCStep], Awaitable[None]]] = None
    
    # ==========================================
    # CICLO PRINCIPAL
    # ==========================================
    
    async def execute_cycle(
        self,
        objective: str,
        context: Optional[Dict[str, Any]] = None,
        constraints: Optional[List[str]] = None,
        session_id: Optional[UUID] = None
    ) -> PPCCResult:
        """
        Ejecutar un ciclo PPCC completo.
        
        Args:
            objective: Objetivo de la interacción
            context: Contexto adicional
            constraints: Restricciones a considerar
            session_id: ID de sesión
            
        Returns:
            Resultado del ciclo
        """
        start_time = datetime.utcnow()
        ctx = PPCCContext(
            id=uuid4(),
            session_id=session_id,
            objective=objective,
            context_data=context or {},
            constraints=constraints or []
        )
        
        self._active_contexts[ctx.id] = ctx
        result = PPCCResult(
            context_id=ctx.id,
            success=False,
            phases_completed=[]
        )
        
        try:
            # FASE 1: PREPARACIÓN
            await self._execute_preparation(ctx)
            result.phases_completed.append("PREPARATION")
            
            # FASE 2: REVELACIÓN
            await self._execute_revelation(ctx)
            result.phases_completed.append("REVELATION")
            
            # FASE 3: EJECUCIÓN
            await self._execute_execution(ctx)
            result.phases_completed.append("EXECUTION")
            
            # FASE 4: DESTILACIÓN
            await self._execute_distillation(ctx)
            result.phases_completed.append("DISTILLATION")
            
            # Completar
            result.success = True
            result.result = ctx.final_result
            result.learnings = ctx.learnings
            result.capital_entries_created = len(ctx.capital_deposited)
            
        except Exception as e:
            result.error = str(e)
            ctx.final_result = {"error": str(e)}
        
        finally:
            ctx.completed_at = datetime.utcnow()
            ctx.total_duration_ms = int(
                (ctx.completed_at - start_time).total_seconds() * 1000
            )
            result.total_duration_ms = ctx.total_duration_ms
        
        return result
    
    # ==========================================
    # FASE 1: PREPARACIÓN
    # ==========================================
    
    async def _execute_preparation(self, ctx: PPCCContext) -> None:
        """
        FASE 1: Preparación
        
        Establece el contexto y prepara todo lo necesario
        para una interacción efectiva.
        
        Pasos:
        1. Definir objetivo claro
        2. Establecer restricciones
        3. Recuperar contexto relevante del capital
        4. Construir transfondo de obviedad
        """
        ctx.current_phase = PPCCPhase.PREPARATION
        
        if self._on_phase_start:
            await self._on_phase_start(PPCCPhase.PREPARATION, ctx)
        
        # Paso 1: Definir objetivo
        step1 = PPCCStep(
            phase=PPCCPhase.PREPARATION,
            name="define_objective",
            description="Definir y clarificar el objetivo",
            input={"objective": ctx.objective}
        )
        clarified_objective = await self._clarify_objective(ctx.objective)
        step1.output = {"clarified_objective": clarified_objective}
        step1.status = "completed"
        ctx.context_data["clarified_objective"] = clarified_objective
        
        # Paso 2: Recuperar contexto del capital
        step2 = PPCCStep(
            phase=PPCCPhase.PREPARATION,
            name="retrieve_context",
            description="Recuperar contexto relevante del Capital Cognitivo"
        )
        relevant_capital = await self.capital.synthesize({
            "objective": ctx.objective,
            **ctx.context_data
        })
        step2.output = relevant_capital
        step2.status = "completed"
        ctx.obviousness_context = relevant_capital.get("context", {})
        
        # Paso 3: Establecer restricciones
        step3 = PPCCStep(
            phase=PPCCPhase.PREPARATION,
            name="set_constraints",
            description="Establecer restricciones y límites",
            input={"constraints": ctx.constraints}
        )
        processed_constraints = await self._process_constraints(ctx.constraints)
        step3.output = {"processed_constraints": processed_constraints}
        step3.status = "completed"
        ctx.context_data["processed_constraints"] = processed_constraints
        
        # Paso 4: Construir transfondo de obviedad
        step4 = PPCCStep(
            phase=PPCCPhase.PREPARATION,
            name="build_obviousness",
            description="Construir transfondo de obviedad compartida"
        )
        obviousness = await self._build_obviousness(ctx)
        step4.output = obviousness
        step4.status = "completed"
        ctx.obviousness_context = obviousness
        
        ctx.execution_steps.extend([step1, step2, step3, step4])
        
        if self._on_phase_complete:
            await self._on_phase_complete(PPCCPhase.PREPARATION, ctx)
    
    # ==========================================
    # FASE 2: REVELACIÓN
    # ==========================================
    
    async def _execute_revelation(self, ctx: PPCCContext) -> None:
        """
        FASE 2: Revelación
        
        El LLM revela su comprensión del problema y contexto.
        Permite detectar malentendidos antes de ejecutar.
        
        Pasos:
        1. Sintetizar comprensión del objetivo
        2. Identificar clarificaciones necesarias
        3. Confirmar alineación con el usuario
        """
        ctx.current_phase = PPCCPhase.REVELATION
        
        if self._on_phase_start:
            await self._on_phase_start(PPCCPhase.REVELATION, ctx)
        
        # Paso 1: Sintetizar comprensión
        step1 = PPCCStep(
            phase=PPCCPhase.REVELATION,
            name="synthesize_understanding",
            description="El LLM sintetiza su comprensión del objetivo"
        )
        understanding = await self._synthesize_understanding(ctx)
        step1.output = understanding
        step1.status = "completed"
        ctx.revealed_understanding = understanding.get("understanding", "")
        
        # Paso 2: Identificar clarificaciones
        step2 = PPCCStep(
            phase=PPCCPhase.REVELATION,
            name="identify_clarifications",
            description="Identificar clarificaciones necesarias"
        )
        clarifications = await self._identify_clarifications(ctx)
        step2.output = {"clarifications": clarifications}
        step2.status = "completed"
        ctx.clarifications_needed = clarifications
        
        # Paso 3: Resolver clarificaciones si las hay
        if ctx.clarifications_needed:
            step3 = PPCCStep(
                phase=PPCCPhase.REVELATION,
                name="resolve_clarifications",
                description="Resolver clarificaciones identificadas"
            )
            resolutions = await self._resolve_clarifications(ctx)
            step3.output = {"resolutions": resolutions}
            step3.status = "completed"
            ctx.context_data["clarification_resolutions"] = resolutions
            ctx.execution_steps.append(step3)
        
        ctx.execution_steps.extend([step1, step2])
        
        if self._on_phase_complete:
            await self._on_phase_complete(PPCCPhase.REVELATION, ctx)
    
    # ==========================================
    # FASE 3: EJECUCIÓN
    # ==========================================
    
    async def _execute_execution(self, ctx: PPCCContext) -> None:
        """
        FASE 3: Ejecución
        
        Realizar la tarea con toda la preparación y revelación.
        
        Pasos:
        1. Crear plan de ejecución
        2. Ejecutar pasos del plan
        3. Recopilar resultados intermedios
        4. Integrar resultado final
        """
        ctx.current_phase = PPCCPhase.EXECUTION
        
        if self._on_phase_start:
            await self._on_phase_start(PPCCPhase.EXECUTION, ctx)
        
        # Paso 1: Crear plan de ejecución
        step1 = PPCCStep(
            phase=PPCCPhase.EXECUTION,
            name="create_plan",
            description="Crear plan de ejecución detallado"
        )
        plan = await self._create_execution_plan(ctx)
        step1.output = plan
        step1.status = "completed"
        ctx.execution_plan = plan.get("plan", "")
        
        # Paso 2: Ejecutar plan paso a paso
        plan_steps = plan.get("steps", [])
        for i, plan_step in enumerate(plan_steps):
            step = PPCCStep(
                phase=PPCCPhase.EXECUTION,
                name=f"execute_step_{i+1}",
                description=plan_step.get("description", ""),
                input=plan_step.get("input", {})
            )
            
            try:
                result = await self._execute_plan_step(ctx, plan_step)
                step.output = result
                step.status = "completed"
                ctx.intermediate_results.append(result)
            except Exception as e:
                step.status = "failed"
                step.error = str(e)
                raise
            
            ctx.execution_steps.append(step)
        
        # Paso 3: Integrar resultado final
        final_step = PPCCStep(
            phase=PPCCPhase.EXECUTION,
            name="integrate_results",
            description="Integrar resultados en producto final"
        )
        final_result = await self._integrate_results(ctx)
        final_step.output = final_result
        final_step.status = "completed"
        ctx.final_result = final_result
        
        ctx.execution_steps.extend([step1, final_step])
        
        if self._on_phase_complete:
            await self._on_phase_complete(PPCCPhase.EXECUTION, ctx)
    
    # ==========================================
    # FASE 4: DESTILACIÓN
    # ==========================================
    
    async def _execute_distillation(self, ctx: PPCCContext) -> None:
        """
        FASE 4: Destilación
        
        Extraer aprendizajes y contribuir al Capital Cognitivo.
        
        Pasos:
        1. Identificar aprendizajes
        2. Depositar nuevo capital
        3. Sugerir mejoras
        4. Consolidar sesión
        """
        ctx.current_phase = PPCCPhase.DISTILLATION
        
        if self._on_phase_start:
            await self._on_phase_start(PPCCPhase.DISTILLATION, ctx)
        
        # Paso 1: Identificar aprendizajes
        step1 = PPCCStep(
            phase=PPCCPhase.DISTILLATION,
            name="identify_learnings",
            description="Identificar aprendizajes de la interacción"
        )
        learnings = await self._identify_learnings(ctx)
        step1.output = {"learnings": learnings}
        step1.status = "completed"
        ctx.learnings = learnings
        
        # Paso 2: Depositar nuevo capital
        step2 = PPCCStep(
            phase=PPCCPhase.DISTILLATION,
            name="deposit_capital",
            description="Depositar nuevo capital cognitivo"
        )
        deposited = await self._deposit_capital(ctx)
        step2.output = {"deposited": deposited}
        step2.status = "completed"
        ctx.capital_deposited = deposited
        
        # Paso 3: Sugerir mejoras
        step3 = PPCCStep(
            phase=PPCCPhase.DISTILLATION,
            name="suggest_improvements",
            description="Sugerir mejoras al sistema"
        )
        improvements = await self._suggest_improvements(ctx)
        step3.output = {"improvements": improvements}
        step3.status = "completed"
        ctx.improvements_suggested = improvements
        
        # Paso 4: Consolidar si hay sesión
        if ctx.session_id:
            step4 = PPCCStep(
                phase=PPCCPhase.DISTILLATION,
                name="consolidate_session",
                description="Consolidar capital de la sesión"
            )
            consolidation = await self.capital.consolidate(ctx.session_id)
            step4.output = consolidation
            step4.status = "completed"
            ctx.execution_steps.append(step4)
        
        ctx.execution_steps.extend([step1, step2, step3])
        
        if self._on_phase_complete:
            await self._on_phase_complete(PPCCPhase.DISTILLATION, ctx)
    
    # ==========================================
    # MÉTODOS DE APOYO
    # ==========================================
    
    async def _clarify_objective(self, objective: str) -> str:
        """Clarificar y refinar el objetivo"""
        # TODO: Implementar con LLM real
        return objective
    
    async def _process_constraints(self, constraints: List[str]) -> List[Dict[str, Any]]:
        """Procesar y estructurar restricciones"""
        return [{"constraint": c, "priority": i+1} for i, c in enumerate(constraints)]
    
    async def _build_obviousness(self, ctx: PPCCContext) -> Dict[str, Any]:
        """Construir transfondo de obviedad"""
        return {
            "objective": ctx.objective,
            "context": ctx.context_data,
            "relevant_knowledge": ctx.obviousness_context
        }
    
    async def _synthesize_understanding(self, ctx: PPCCContext) -> Dict[str, Any]:
        """Sintetizar comprensión del LLM"""
        # TODO: Implementar con LLM real
        return {
            "understanding": f"Comprendo que el objetivo es: {ctx.objective}",
            "key_concepts": [],
            "assumptions": []
        }
    
    async def _identify_clarifications(self, ctx: PPCCContext) -> List[str]:
        """Identificar clarificaciones necesarias"""
        # TODO: Implementar con LLM real
        return []
    
    async def _resolve_clarifications(self, ctx: PPCCContext) -> List[Dict[str, Any]]:
        """Resolver clarificaciones"""
        # TODO: Implementar resolución interactiva
        return []
    
    async def _create_execution_plan(self, ctx: PPCCContext) -> Dict[str, Any]:
        """Crear plan de ejecución"""
        # TODO: Implementar con LLM real
        return {
            "plan": f"Plan para: {ctx.objective}",
            "steps": [
                {"description": "Paso 1", "input": {}},
                {"description": "Paso 2", "input": {}}
            ]
        }
    
    async def _execute_plan_step(
        self,
        ctx: PPCCContext,
        step: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Ejecutar un paso del plan"""
        # TODO: Implementar ejecución real
        return {"status": "completed", "result": "Paso ejecutado"}
    
    async def _integrate_results(self, ctx: PPCCContext) -> Dict[str, Any]:
        """Integrar resultados finales"""
        return {
            "status": "success",
            "objective": ctx.objective,
            "results": ctx.intermediate_results
        }
    
    async def _identify_learnings(self, ctx: PPCCContext) -> List[str]:
        """Identificar aprendizajes de la interacción"""
        # TODO: Implementar extracción de aprendizajes
        return [
            f"Objetivo completado: {ctx.objective[:50]}..."
        ]
    
    async def _deposit_capital(self, ctx: PPCCContext) -> List[str]:
        """Depositar nuevo capital cognitivo"""
        deposited = []
        
        # Depositar conocimiento del objetivo
        if ctx.objective:
            entry = await self.capital.deposit(
                type=CapitalType.KNOWLEDGE,
                key=f"objective:{hash(ctx.objective)}",
                value={
                    "objective": ctx.objective,
                    "result": ctx.final_result
                },
                source="ppcc_cycle",
                session_id=ctx.session_id
            )
            deposited.append(str(entry.id))
        
        # Depositar aprendizajes
        for learning in ctx.learnings:
            entry = await self.capital.deposit(
                type=CapitalType.HEURISTICS,
                key=f"learning:{hash(learning)}",
                value=learning,
                source="ppcc_distillation",
                session_id=ctx.session_id
            )
            deposited.append(str(entry.id))
        
        return deposited
    
    async def _suggest_improvements(self, ctx: PPCCContext) -> List[str]:
        """Sugerir mejoras al sistema"""
        # TODO: Implementar análisis de mejoras
        return []
    
    # ==========================================
    # GESTIÓN DE CONTEXTOS
    # ==========================================
    
    def get_context(self, context_id: UUID) -> Optional[PPCCContext]:
        """Obtener contexto por ID"""
        return self._active_contexts.get(context_id)
    
    def get_active_contexts(self) -> List[PPCCContext]:
        """Obtener todos los contextos activos"""
        return list(self._active_contexts.values())
    
    async def cancel_context(self, context_id: UUID) -> bool:
        """Cancelar un contexto activo"""
        if context_id in self._active_contexts:
            del self._active_contexts[context_id]
            return True
        return False
