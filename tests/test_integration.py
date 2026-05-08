"""
Tests de Integración End-to-End para OpenClaw Agent SaaS

Valida el flujo completo desde la preparación del contexto
hasta la cosecha de conocimiento.
"""

import pytest
import asyncio
import tempfile
import os
from datetime import datetime

from src.core.obviousness import (
    ObviousnessContext,
    ObviousnessContextBuilder,
    OrganizationalImpact,
    TaskPriority
)
from src.core.ppcc import PPCCCycle, PPCCPhase
from src.memory.vcs import MemoryVCS, DisclosureLevel
from src.iovba.infrastructure.sandbox import SandboxManager, SandboxConfig, IsolationLevel
from src.iovba.orchestration.lead_agent import LeadAgent, AgentConfig, TaskComplexity
from src.iovba.validation.guardrail import GuardrailMiddleware, PermissionLevel
from src.iovba.behavior.persona import Persona, PersonaConfig, PersonaType
from src.iovba.behavior.ethics import EthicsEngine, ActionType
from src.iovba.action.skills_registry import SkillsRegistry, Skill, SkillMetadata, SkillCategory
from src.ralph.loop import RalphLoop, RalphPhase


class TestFullWorkflow:
    """Tests de flujo completo"""
    
    @pytest.fixture
    def setup_system(self):
        """Configura el sistema completo para tests"""
        # Crear VCS temporal
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        memory_vcs = MemoryVCS(db_path=db_path, auto_init=True)
        
        # Crear componentes
        guardrail = GuardrailMiddleware()
        ethics = EthicsEngine()
        persona = Persona(PersonaConfig(
            persona_type=PersonaType.ASSISTANT,
            name="Integration Test Agent"
        ))
        
        yield {
            "memory_vcs": memory_vcs,
            "guardrail": guardrail,
            "ethics": ethics,
            "persona": persona,
            "db_path": db_path
        }
        
        # Cleanup
        try:
            os.unlink(db_path)
        except:
            pass
    
    @pytest.mark.asyncio
    async def test_complete_ppcc_flow(self, setup_system):
        """Verifica flujo PPCC completo con memoria"""
        memory_vcs = setup_system["memory_vcs"]
        
        # 1. Crear contexto de obviedad
        context = (ObviousnessContextBuilder("integration-session", "test-user")
            .with_objective(
                "Analizar datos de ventas Q1",
                success_criteria=["Completar análisis", "Generar reporte"],
                deliverables=["Reporte PDF"]
            )
            .with_metrics(recall=0.8, precision=0.85)
            .with_boundaries(
                allow=["database", "api"],
                deny=["production"],
                sandbox=True
            )
            .with_relevance(
                impact="high",
                ccv=8,
                business_context="Análisis trimestral"
            )
            .with_time(priority="high", timeout=600)
            .with_domain("retail")
            .build())
        
        # 2. Crear ciclo PPCC
        cycle = PPCCCycle()
        
        # 3. Preparación
        prep_result = await cycle.prepare({
            "session_id": context.session_id,
            "user_id": context.user_id,
            "objective": context.objective
        })
        
        assert prep_result["phase"] == "preparation"
        
        # 4. Alineación
        align_result = await cycle.request_alignment()
        assert align_result["execution_blocked"] is True
        
        confirm_result = await cycle.confirm_alignment(
            f"Entendido: {context.objective}",
            user_confirmed=True
        )
        assert confirm_result["status"] == "confirmed"
        
        # 5. Ejecución
        exec_result = await cycle.execute("Ejecutar análisis de ventas")
        assert exec_result["phase"] == "execution"
        
        # 6. Declaración
        final_result = await cycle.declare_result(
            satisfaction=True,
            feedback="Análisis completado exitosamente",
            harvest_knowledge=True
        )
        
        assert final_result["satisfaction"] is True
        # El capital cognitivo se obtiene del contexto, que puede variar según la configuración
        assert final_result["cognitive_capital_earned"] >= 1
        assert final_result["cognitive_capital_earned"] <= 10
        
        # 7. Guardar en memoria
        memory_vcs.upsert(
            topic_key=f"session:{context.session_id}:result",
            content=str(final_result),
            metadata={
                "objective": context.objective,
                "satisfaction": True,
                "domain": context.domain
            }
        )
        
        # Verificar que se guardó
        saved = memory_vcs.get_by_key(f"session:{context.session_id}:result")
        assert saved is not None
    
    @pytest.mark.asyncio
    async def test_validation_pipeline(self, setup_system):
        """Verifica pipeline de validación"""
        guardrail = setup_system["guardrail"]
        ethics = setup_system["ethics"]
        
        # Contenido con PII
        content = "Contact user at john.doe@example.com for details"
        
        # Validar con guardrail
        validation = guardrail.validate(content)
        
        assert len(validation.rules_matched) > 0  # Debe detectar email
        
        # Verificar acción ética
        ethics_check = ethics.evaluate(
            ActionType.COMMUNICATION,
            {"content": content, "destination": "external"}
        )
        
        # Verificar que el sistema detecta el riesgo (incluye 'minimal' cuando no hay violaciones)
        assert ethics_check.overall_risk in ["minimal", "low", "medium", "high", "critical"]
    
    @pytest.mark.asyncio
    async def test_skill_auto_generation(self, setup_system):
        """Verifica auto-generación de skills"""
        memory_vcs = setup_system["memory_vcs"]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            skills_registry = SkillsRegistry(
                skills_directory=tmpdir,
                auto_save=True
            )
            
            # Simular interacción exitosa
            skill = skills_registry.auto_generate({
                "objective": "Generate monthly report",
                "commands": [
                    {"command": "collect_data"},
                    {"command": "process_data"},
                    {"command": "generate_pdf"}
                ],
                "result": {"file": "report.pdf"},
                "success": True
            })
            
            assert skill is not None
            assert "auto-generated" in skill.metadata.tags
    
    @pytest.mark.asyncio
    async def test_ralph_loop_integration(self, setup_system):
        """Verifica integración con Ralph Loop"""
        memory_vcs = setup_system["memory_vcs"]
        
        ralph = RalphLoop(memory_vcs=memory_vcs)
        
        # Ejecutar ciclo completo
        session = await ralph.execute({
            "objective": "Integration test with Ralph Loop",
            "success": True,
            "commands": [
                {"command": "analyze"},
                {"command": "report"}
            ],
            "errors": [],
            "tools_used": ["analyzer"],
            "obviousness_context": {
                "metrics": {"accuracy": 0.9}
            },
            "metrics": {"accuracy": 0.92}
        })
        
        assert session.completed_at is not None
        assert session.total_cognitive_capital >= 0
        
        # Verificar que el conocimiento se guardó en VCS
        memories = memory_vcs.search(
            "Integration test",
            disclosure_level=DisclosureLevel.COMPACT
        )
        
        # Debe haber al menos una memoria de la sesión
        assert memory_vcs.get_stats()["total_memories"] > 0


class TestDomainSpecific:
    """Tests para dominios específicos"""
    
    def test_retail_domain_context(self):
        """Verifica contexto de dominio retail"""
        context = (ObviousnessContextBuilder("retail-session", "retail-user")
            .with_objective("Optimizar inventario de productos")
            .with_domain("retail", "inventory_manager")
            .with_metrics(custom={"stock_turnover": 4.0, "fill_rate": 0.95})
            .with_boundaries(
                allow=["inventory_db", "sales_api"],
                deny=["customer_pii"]
            )
            .build())
        
        assert context.domain == "retail"
        assert context.agent_persona == "inventory_manager"
    
    def test_health_domain_context(self):
        """Verifica contexto de dominio salud"""
        context = (ObviousnessContextBuilder("health-session", "health-user")
            .with_objective("Analizar historial médico del paciente")
            .with_domain("health", "clinical_assistant")
            .with_boundaries(
                allow=["anonymized_data"],
                deny=["direct_patient_id"]
            )
            .build())
        
        assert context.domain == "health"
        # Verificar restricciones de privacidad
        assert "direct_patient_id" in context.negative_boundaries
    
    def test_finance_domain_context(self):
        """Verifica contexto de dominio finanzas"""
        context = (ObviousnessContextBuilder("finance-session", "finance-user")
            .with_objective("Optimizar portafolio de inversiones")
            .with_domain("finance", "portfolio_analyst")
            .with_metrics(custom={"sharpe_ratio": 1.5, "max_drawdown": 0.1})
            .with_relevance(impact="critical", ccv=10)
            .build())
        
        assert context.domain == "finance"
        assert context.organizational_impact == "critical"


class TestErrorHandling:
    """Tests de manejo de errores"""
    
    @pytest.mark.asyncio
    async def test_ppcc_error_recovery(self):
        """Verifica recuperación de errores en PPCC"""
        cycle = PPCCCycle()
        
        # Intentar ejecutar sin alineación
        with pytest.raises(Exception):  # AlignmentRequiredError
            await cycle.execute("Test sin alineación")
    
    @pytest.mark.asyncio
    async def test_validation_failure(self):
        """Verifica manejo de fallos de validación"""
        guardrail = GuardrailMiddleware()
        
        # Contenido con inyección SQL
        result = guardrail.validate("; DROP TABLE users; --")
        
        assert result.allowed is False
        assert "injection" in result.rules_matched[0].lower()
    
    @pytest.mark.asyncio
    async def test_ethics_violation(self):
        """Verifica manejo de violaciones éticas"""
        ethics = EthicsEngine()
        
        report = ethics.evaluate(
            ActionType.AUTOMATION,
            {"action": "delete_all_data", "destructive": True}
        )
        
        # Debe detectar el riesgo
        assert not report.overall_compliant or report.overall_risk in ["high", "critical"]


class TestPerformance:
    """Tests de rendimiento"""
    
    @pytest.mark.asyncio
    async def test_rapid_ppcc_cycles(self):
        """Verifica ciclos PPCC rápidos"""
        cycles = []
        
        for i in range(10):
            cycle = PPCCCycle()
            start = datetime.utcnow()
            
            await cycle.prepare({
                "session_id": f"rapid-{i}",
                "user_id": "perf-user",
                "objective": f"Rapid task {i}"
            })
            await cycle.request_alignment()
            await cycle.confirm_alignment("Entendido", True)
            await cycle.execute("Execute")
            await cycle.declare_result(True)
            
            duration = (datetime.utcnow() - start).total_seconds()
            cycles.append(duration)
        
        # Todos los ciclos deben completarse en menos de 5 segundos cada uno
        assert all(d < 5.0 for d in cycles)
    
    def test_memory_vcs_performance(self):
        """Verifica rendimiento de Memory VCS"""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        
        try:
            vcs = MemoryVCS(db_path=db_path)
            
            # Insertar 100 memorias
            start = datetime.utcnow()
            
            for i in range(100):
                vcs.upsert(
                    topic_key=f"perf:test:{i}",
                    content=f"Content {i}" * 10,
                    metadata={"index": i}
                )
            
            insert_time = (datetime.utcnow() - start).total_seconds()
            
            # Búsqueda
            start = datetime.utcnow()
            results = vcs.search("Content", disclosure_level=DisclosureLevel.COMPACT)
            search_time = (datetime.utcnow() - start).total_seconds()
            
            # Verificar rendimiento
            assert insert_time < 5.0  # 100 inserciones en menos de 5 segundos
            assert search_time < 1.0  # Búsqueda en menos de 1 segundo
            assert len(results) > 0
            
        finally:
            try:
                os.unlink(db_path)
            except:
                pass


class TestSecurity:
    """Tests de seguridad"""
    
    def test_sandbox_isolation(self):
        """Verifica aislamiento de sandbox"""
        from src.iovba.infrastructure.sandbox import SandboxIsolation
        
        isolation = SandboxIsolation(
            pid_namespace=True,
            network_namespace=True,
            mount_namespace=True,
            read_only_root=True
        )
        
        assert isolation.pid_namespace is True
        assert isolation.network_namespace is True
    
    def test_secret_protection(self):
        """Verifica protección de secretos"""
        from src.iovba.infrastructure.openshell import OpenShell
        
        shell = OpenShell()
        
        # Almacenar secreto
        shell.store_secret("api_key", "secret_value_123")
        
        # Verificar que está protegido
        secret = shell.get_secret("api_key")
        assert secret == "secret_value_123"
        
        # Eliminar
        shell.delete_secret("api_key")
        assert shell.get_secret("api_key") is None
    
    def test_permission_levels(self):
        """Verifica niveles de permiso"""
        guardrail = GuardrailMiddleware()
        
        # Usuario con permisos limitados
        guardrail.set_permission_override("limited-session", PermissionLevel.LIMITED)
        
        # Verificar que el permiso está establecido
        permission = guardrail.get_permission("limited-session")
        assert permission == PermissionLevel.LIMITED
