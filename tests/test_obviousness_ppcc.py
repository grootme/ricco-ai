"""
Tests para Trasfondo de Obviedad y Ciclo PPCC

Valida que el contrato semántico y el ciclo de interacción
funcionen correctamente.
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from src.core.obviousness import (
    ObviousnessContext,
    ObviousnessContextBuilder,
    ObviousnessDimension,
    OrganizationalImpact,
    TaskPriority
)
from src.core.ppcc import (
    PPCCCycle,
    PPCCPhase,
    PPCCState,
    PPCCError,
    AlignmentRequiredError
)


class TestObviousnessContext:
    """Tests para el Trasfondo de Obviedad"""
    
    def test_create_minimal_context(self):
        """Verifica creación de contexto mínimo"""
        context = ObviousnessContext(
            session_id="test-session",
            user_id="test-user",
            objective="Analizar datos de ventas"
        )
        
        assert context.session_id == "test-session"
        assert context.user_id == "test-user"
        assert context.objective == "Analizar datos de ventas"
        assert context.sandbox_mode is True
        assert context.organizational_impact == OrganizationalImpact.MEDIUM
    
    def test_create_full_context(self):
        """Verifica creación de contexto completo"""
        context = ObviousnessContext(
            session_id="full-session",
            user_id="user-001",
            objective="Generar reporte financiero Q1",
            success_criteria=["Completar en 5 minutos", "Incluir gráficos"],
            deliverables=["PDF report", "Excel data"],
            target_recall=0.85,
            target_precision=0.80,
            positive_boundaries=["database", "api"],
            negative_boundaries=["production"],
            allowed_tools=["sql", "python"],
            organizational_impact=OrganizationalImpact.HIGH,
            cognitive_capital_value=8,
            priority=TaskPriority.HIGH,
            timeout_seconds=600
        )
        
        assert len(context.success_criteria) == 2
        assert len(context.deliverables) == 2
        assert context.target_recall == 0.85
        assert "database" in context.positive_boundaries
        assert "production" in context.negative_boundaries
        assert context.organizational_impact == OrganizationalImpact.HIGH
    
    def test_system_prompt_generation(self):
        """Verifica generación de system prompt"""
        context = ObviousnessContext(
            session_id="prompt-test",
            user_id="user-001",
            objective="Optimizar consultas SQL",
            success_criteria=["Reducir tiempo de ejecución"],
            metrics={"latency_target": 100}
        )
        
        prompt = context.to_system_prompt()
        
        assert "TRASFONDO DE OBVIEDAD" in prompt
        assert "Optimizar consultas SQL" in prompt
        assert "FINALIDAD" in prompt
        assert "MÉTRICAS DE ÉXITO" in prompt
    
    def test_compact_format(self):
        """Verifica formato compacto"""
        context = ObviousnessContext(
            session_id="compact-test",
            user_id="user-001",
            objective="Test de formato compacto",
            target_recall=0.9
        )
        
        compact = context.to_compact_format()
        
        assert "S" in compact
        assert "M" in compact
        assert "A" in compact
        assert "R" in compact
        assert "T" in compact
        assert compact["M"]["recall"] == 0.9
    
    def test_alignment_validation(self):
        """Verifica validación de alineación"""
        context = ObviousnessContext(
            session_id="alignment-test",
            user_id="user-001",
            objective="Analizar datos financieros",
            restricted_tools=["production_db"]
        )
        
        # Respuesta bien alineada
        good_response = "Voy a analizar los datos financieros según el objetivo"
        result = context.validate_alignment(good_response)
        assert result["passed"] is True
        
        # Respuesta con violación
        bad_response = "Voy a acceder a production_db para los datos"
        result = context.validate_alignment(bad_response)
        assert result["passed"] is False
    
    def test_scope_checking(self):
        """Verifica verificación de alcance"""
        context = ObviousnessContext(
            session_id="scope-test",
            user_id="user-001",
            objective="Test de alcance",
            allowed_tools=["search", "python"],
            restricted_tools=["delete", "format"]
        )
        
        assert context.is_within_scope("search for data") is True
        assert context.is_within_scope("delete all files") is False
        assert context.is_within_scope("format disk") is False


class TestObviousnessContextBuilder:
    """Tests para el builder de contexto"""
    
    def test_builder_basic(self):
        """Verifica builder básico"""
        context = (ObviousnessContextBuilder("session-1", "user-1")
            .with_objective("Test builder")
            .build())
        
        assert context.session_id == "session-1"
        assert context.user_id == "user-1"
        assert context.objective == "Test builder"
    
    def test_builder_full(self):
        """Verifica builder completo"""
        deadline = datetime.utcnow() + timedelta(hours=1)
        
        context = (ObviousnessContextBuilder("session-2", "user-2")
            .with_objective(
                "Full test",
                success_criteria=["Criterio 1"],
                deliverables=["Entregable 1"]
            )
            .with_metrics(recall=0.8, precision=0.85)
            .with_boundaries(
                allow=["tool1"],
                deny=["tool2"],
                sandbox=True
            )
            .with_relevance(
                impact="high",
                ccv=9,
                business_context="Test context"
            )
            .with_time(
                priority="urgent",
                timeout=300,
                deadline=deadline
            )
            .with_domain("retail", "analyst")
            .build())
        
        assert context.objective == "Full test"
        assert context.target_recall == 0.8
        assert context.target_precision == 0.85
        assert "tool1" in context.positive_boundaries
        assert "tool2" in context.negative_boundaries
        assert context.organizational_impact == "high"
        assert context.priority == "urgent"
        assert context.domain == "retail"


class TestPPCCCycle:
    """Tests para el ciclo PPCC"""
    
    @pytest.mark.asyncio
    async def test_preparation_phase(self):
        """Verifica fase de preparación"""
        cycle = PPCCCycle()
        
        result = await cycle.prepare({
            "session_id": "prep-test",
            "user_id": "user-1",
            "objective": "Test preparación"
        })
        
        assert result["phase"] == "preparation"
        assert result["next_step"] == "alignment"
        assert "system_prompt" in result
        assert cycle.state.current_phase == PPCCPhase.PREPARATION
    
    @pytest.mark.asyncio
    async def test_alignment_phase(self):
        """Verifica fase de alineación"""
        cycle = PPCCCycle()
        
        # Preparar primero
        await cycle.prepare({
            "session_id": "align-test",
            "user_id": "user-1",
            "objective": "Test alineación"
        })
        
        # Solicitar alineación
        result = await cycle.request_alignment()
        
        assert result["phase"] == "alignment"
        assert result["execution_blocked"] is True
        assert "alignment_prompt" in result
    
    @pytest.mark.asyncio
    async def test_alignment_confirmation(self):
        """Verifica confirmación de alineación"""
        cycle = PPCCCycle()
        
        await cycle.prepare({
            "session_id": "confirm-test",
            "user_id": "user-1",
            "objective": "Test confirmación"
        })
        
        await cycle.request_alignment()
        
        result = await cycle.confirm_alignment(
            "Entendido: voy a realizar Test confirmación",
            user_confirmed=True
        )
        
        assert result["status"] == "confirmed"
        assert cycle.state.alignment_confirmed is True
    
    @pytest.mark.asyncio
    async def test_execution_without_alignment_fails(self):
        """Verifica que ejecución sin alineación falla"""
        cycle = PPCCCycle()
        
        await cycle.prepare({
            "session_id": "exec-fail-test",
            "user_id": "user-1",
            "objective": "Test ejecución sin alineación"
        })
        
        with pytest.raises(AlignmentRequiredError):
            await cycle.execute("Ejecutar tarea")
    
    @pytest.mark.asyncio
    async def test_execution_phase(self):
        """Verifica fase de ejecución"""
        cycle = PPCCCycle()
        
        await cycle.prepare({
            "session_id": "exec-test",
            "user_id": "user-1",
            "objective": "Test ejecución"
        })
        
        await cycle.request_alignment()
        await cycle.confirm_alignment("Entendido", user_confirmed=True)
        
        result = await cycle.execute("Ejecutar tarea de prueba")
        
        assert result["phase"] == "execution"
        assert "results" in result
        assert result["next_step"] == "declaration"
    
    @pytest.mark.asyncio
    async def test_declaration_phase_satisfied(self):
        """Verifica declaración de satisfacción"""
        cycle = PPCCCycle()
        
        await cycle.prepare({
            "session_id": "declare-test",
            "user_id": "user-1",
            "objective": "Test declaración"
        })
        
        await cycle.request_alignment()
        await cycle.confirm_alignment("Entendido", user_confirmed=True)
        await cycle.execute("Ejecutar")
        
        result = await cycle.declare_result(
            satisfaction=True,
            feedback="Excelente trabajo"
        )
        
        assert result["satisfaction"] is True
        assert result["cognitive_capital_earned"] > 0
        assert cycle.state.current_phase == PPCCPhase.COMPLETED
    
    @pytest.mark.asyncio
    async def test_declaration_phase_unsatisfied(self):
        """Verifica declaración de insatisfacción"""
        cycle = PPCCCycle()
        
        await cycle.prepare({
            "session_id": "unsatisfied-test",
            "user_id": "user-1",
            "objective": "Test insatisfacción"
        })
        
        await cycle.request_alignment()
        await cycle.confirm_alignment("Entendido", user_confirmed=True)
        await cycle.execute("Ejecutar")
        
        result = await cycle.declare_result(
            satisfaction=False,
            feedback="No cumplió expectativas"
        )
        
        assert result["satisfaction"] is False
        assert "learning_opportunity" in result
        assert cycle.state.current_phase == PPCCPhase.COMPLETED
    
    @pytest.mark.asyncio
    async def test_full_cycle(self):
        """Verifica ciclo completo PPCC"""
        cycle = PPCCCycle()
        
        # 1. Preparación
        prep_result = await cycle.prepare({
            "session_id": "full-cycle-test",
            "user_id": "user-1",
            "objective": "Test ciclo completo"
        })
        assert prep_result["phase"] == "preparation"
        
        # 2. Alineación
        align_result = await cycle.request_alignment()
        assert align_result["phase"] == "alignment"
        
        confirm_result = await cycle.confirm_alignment("Entendido", True)
        assert confirm_result["status"] == "confirmed"
        
        # 3. Ejecución
        exec_result = await cycle.execute("Ejecutar tarea completa")
        assert exec_result["phase"] == "execution"
        
        # 4. Declaración
        final_result = await cycle.declare_result(True, "Completado")
        assert final_result["satisfaction"] is True
        assert cycle.state.current_phase == PPCCPhase.COMPLETED
    
    @pytest.mark.asyncio
    async def test_phase_change_callback(self):
        """Verifica callback de cambio de fase"""
        cycle = PPCCCycle()
        changes = []
        
        async def on_change(**kwargs):
            changes.append(kwargs)
        
        cycle.on_phase_change(on_change)
        
        await cycle.prepare({
            "session_id": "callback-test",
            "user_id": "user-1",
            "objective": "Test callback"
        })
        
        assert len(changes) > 0
        assert changes[0]["old_phase"] == PPCCPhase.PREPARATION


class TestPPCCState:
    """Tests para el estado del ciclo PPCC"""
    
    def test_initial_state(self):
        """Verifica estado inicial"""
        state = PPCCState()
        
        assert state.current_phase == PPCCPhase.PREPARATION
        assert state.alignment_confirmed is False
        assert state.iteration_count == 0
        assert state.satisfaction_declared is None
    
    def test_state_persistence(self):
        """Verifica persistencia del estado"""
        state = PPCCState()
        state.current_phase = PPCCPhase.EXECUTION
        state.alignment_confirmed = True
        state.iteration_count = 2
        
        state_dict = state.model_dump()
        
        assert state_dict["current_phase"] == PPCCPhase.EXECUTION.value
        assert state_dict["alignment_confirmed"] is True
        assert state_dict["iteration_count"] == 2
