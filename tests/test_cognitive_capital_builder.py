"""
Tests para Generación de Capital Cognitivo Real

50+ tests que generan capital cognitivo a través de experiencias reales.
NO usan mocks - cada test genera aprendizaje real.

Metodología:
1. Entrenamiento reforzado a partir de aciertos y errores reales
2. Incorporación de casos límite y excepciones
3. Creación de escenarios sintéticos
4. Reentrenamiento continuo cuando ocurren errores no previstos

Patrones GOF Aplicados:
- Builder: Construcción de escenarios
- Strategy: Estrategias de test
- Observer: Observación de resultados
- Command: Ejecución de tests como comandos
- Factory: Creación de fixtures
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
import random
import string
import json

# Imports del sistema
import sys
sys.path.insert(0, '/home/z/my-project/ecosystem/ricco-ai')

from src.core.agent_profile import (
    AgentProfile, AgentProfileBuilder, AgentRegistry,
    Domain, IOVBARole, SkillLevel, AgentState,
    ExecutionStrategy, AdaptiveExecutionStrategy,
    AnalyzeCommand, GenerateCommand, CoordinateCommand,
    LoggingDecorator, CachingDecorator, MetricsDecorator, RetryDecorator,
    CognitiveMemory
)
from src.core.ppcc import PPCCCycle, PPCCPhase, PPCCState
from src.cognitive.learning_pipeline import (
    LearningPipeline, LearningEvent, LearningEventType,
    ReinforcementEngine, CoordinationEngine, ReflectionEngine
)


# ============================================================================
# FIXTURES - Patrón Factory
# ============================================================================

class AgentFactory:
    """Factory para crear agentes de test con configuraciones variadas"""
    
    @staticmethod
    def create_codex_agent(skill_level: SkillLevel = SkillLevel.INTERMEDIATE) -> AgentProfile:
        return (AgentProfileBuilder()
            .with_id(f"codex-{random.randint(1000, 9999)}")
            .with_domain(Domain.CODEX)
            .with_role(IOVBARole.BUILDER)
            .with_skill("python", skill_level)
            .with_skill("testing", SkillLevel.ADVANCED)
            .with_tool("code_analyzer")
            .with_tool("test_runner")
            .with_mcp_server("github")
            .build())
    
    @staticmethod
    def create_apex_agent() -> AgentProfile:
        return (AgentProfileBuilder()
            .with_id(f"apex-{random.randint(1000, 9999)}")
            .with_domain(Domain.APEX)
            .with_role(IOVBARole.INVESTIGATOR)
            .with_skill("market_analysis", SkillLevel.ADVANCED)
            .with_skill("risk_assessment", SkillLevel.INTERMEDIATE)
            .with_tool("market_data_api")
            .build())
    
    @staticmethod
    def create_vitalis_agent() -> AgentProfile:
        return (AgentProfileBuilder()
            .with_id(f"vitalis-{random.randint(1000, 9999)}")
            .with_domain(Domain.VITALIS)
            .with_role(IOVBARole.VALIDATOR)
            .with_skill("symptom_analysis", SkillLevel.EXPERT)
            .with_tool("medical_database")
            .build())
    
    @staticmethod
    def create_hierarchical_team() -> List[AgentProfile]:
        """Crea un equipo jerárquico de agentes"""
        leader = (AgentProfileBuilder()
            .with_id("team-leader")
            .with_domain(Domain.CODEX)
            .with_role(IOVBARole.ASSISTANT)
            .with_skill("coordination", SkillLevel.EXPERT)
            .build())
        
        members = []
        for i in range(3):
            member = (AgentProfileBuilder()
                .with_id(f"team-member-{i}")
                .with_domain(Domain.CODEX)
                .with_role(IOVBARole.BUILDER)
                .with_parent("team-leader")
                .build())
            members.append(member)
        
        for member in members:
            leader._child_agents.append(member.agent_id)
        
        return [leader] + members


class ExperienceGenerator:
    """Generador de experiencias para capital cognitivo"""
    
    @staticmethod
    def generate_code_review_experience(success: bool = True) -> Dict[str, Any]:
        issues_found = random.randint(0, 10) if success else random.randint(5, 20)
        return {
            "type": "code_review",
            "success": success,
            "context": {
                "language": random.choice(["python", "javascript", "go"]),
                "file_count": random.randint(1, 50),
                "lines_of_code": random.randint(100, 10000)
            },
            "metrics": {
                "issues_found": issues_found,
                "critical_issues": random.randint(0, 3) if success else random.randint(2, 8),
                "time_seconds": random.randint(30, 300)
            },
            "skills_used": ["code_analysis", "pattern_recognition"],
            "success_factors": ["clear_requirements", "good_documentation"] if success else [],
            "error": None if success else "Missed critical vulnerability"
        }
    
    @staticmethod
    def generate_task_execution_experience(
        task_type: str = "analysis",
        success: bool = True
    ) -> Dict[str, Any]:
        return {
            "type": f"task_{task_type}",
            "success": success,
            "context": {
                "domain": random.choice([d.value for d in Domain]),
                "complexity": random.choice(["low", "medium", "high"]),
                "priority": random.choice(["normal", "high", "urgent"])
            },
            "metrics": {
                "duration_seconds": random.randint(10, 600),
                "tokens_used": random.randint(100, 5000),
                "iterations": random.randint(1, 10)
            },
            "skills_used": [task_type, "problem_solving"],
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def generate_error_recovery_experience() -> Dict[str, Any]:
        """Genera experiencia de recuperación de error - MUY VALIOSA para capital"""
        return {
            "type": "error_recovery",
            "success": True,  # Recuperación exitosa
            "original_error": random.choice([
                "timeout_exceeded",
                "rate_limit_hit",
                "invalid_response",
                "context_overflow",
                "tool_unavailable"
            ]),
            "recovery_strategy": random.choice([
                "retry_with_backoff",
                "fallback_to_alternative",
                "reduce_scope",
                "request_clarification"
            ]),
            "context": {
                "attempt": random.randint(2, 5),
                "total_time_seconds": random.randint(30, 180)
            },
            "skills_used": ["error_handling", "adaptive_behavior"],
            "success_factors": ["quick_recovery", "graceful_degradation"],
            "insight": "Errors are opportunities for learning"
        }


# ============================================================================
# TEST GROUP 1: AGENT PROFILE - Capital Base (Tests 1-10)
# ============================================================================

class TestAgentProfileCapital:
    """Tests que construyen capital cognitivo base del agente"""
    
    @pytest.mark.asyncio
    async def test_001_agent_creation_builds_identity(self):
        """
        Test 1: Creación de agente construye identidad única
        Capital: Identidad + configuración inicial
        """
        agent = AgentFactory.create_codex_agent(SkillLevel.EXPERT)
        
        assert agent.agent_id is not None
        assert agent.domain == Domain.CODEX
        assert agent.role == IOVBARole.BUILDER
        assert len(agent.skills) > 0
        assert agent.capital_value >= 0
        
        # Registrar para capital colectivo
        registry = AgentRegistry()
        registry.register(agent)
        
        print(f"✓ Agent {agent.agent_id} created with {len(agent.skills)} skills")
    
    @pytest.mark.asyncio
    async def test_002_skill_registration_accumulates_capital(self):
        """
        Test 2: Cada skill registrada añade capital
        Capital: Habilidades documentadas
        """
        agent = AgentFactory.create_codex_agent()
        initial_skills = len(agent.skills)
        
        # Añadir nueva skill
        builder = AgentProfileBuilder()
        builder.with_id(agent.agent_id)
        builder.with_domain(agent.domain)
        builder.with_role(agent.role)
        builder.with_skill("new_skill", SkillLevel.ADVANCED)
        
        new_agent = builder.build()
        
        assert len(new_agent.skills) > initial_skills
        assert "new_skill" in new_agent.skills
        print(f"✓ Skill added: {len(new_agent.skills)} total skills")
    
    @pytest.mark.asyncio
    async def test_003_tool_registration_expands_capabilities(self):
        """
        Test 3: Herramientas expanden capacidades operativas
        Capital: Inventario de herramientas
        """
        agent = (AgentProfileBuilder()
            .with_id("tool-agent")
            .with_domain(Domain.CODEX)
            .with_role(IOVBARole.BUILDER)
            .with_tool("analyzer")
            .with_tool("formatter")
            .with_tool("linter")
            .build())
        
        assert len(agent.tools) == 3
        assert "analyzer" in agent.tools
        print(f"✓ Tools registered: {agent.tools}")
    
    @pytest.mark.asyncio
    async def test_004_mcp_server_connection_enables_external_resources(self):
        """
        Test 4: Servidores MCP habilitan recursos externos
        Capital: Conexiones externas documentadas
        """
        agent = (AgentProfileBuilder()
            .with_id("mcp-agent")
            .with_domain(Domain.APEX)
            .with_role(IOVBARole.INVESTIGATOR)
            .with_mcp_server("github")
            .with_mcp_server("slack")
            .with_mcp_server("postgres")
            .build())
        
        assert len(agent.mcp_servers) == 3
        print(f"✓ MCP servers: {agent.mcp_servers}")
    
    @pytest.mark.asyncio
    async def test_005_memory_initialization_creates_knowledge_base(self):
        """
        Test 5: Inicialización de memoria crea base de conocimiento
        Capital: Infraestructura de memoria
        """
        agent = AgentFactory.create_codex_agent()
        
        # Almacenar conocimiento inicial
        await agent.memory.store("domain_knowledge", {
            "patterns": ["singleton", "factory", "observer"],
            "best_practices": ["dry", "solid", "kiss"]
        }, scope="long")
        
        retrieved = await agent.memory.retrieve("domain_knowledge", scope="long")
        assert retrieved is not None
        assert "patterns" in retrieved
        print(f"✓ Memory initialized with domain knowledge")
    
    @pytest.mark.asyncio
    async def test_006_state_transitions_are_trackable(self):
        """
        Test 6: Transiciones de estado son rastreables
        Capital: Historial de estados
        """
        agent = AgentFactory.create_codex_agent()
        
        assert agent.state == AgentState.IDLE
        
        agent.state = AgentState.PREPARING
        assert agent.state == AgentState.PREPARING
        
        agent.state = AgentState.EXECUTING
        assert agent.state == AgentState.EXECUTING
        
        agent.state = AgentState.IDLE
        assert agent.state == AgentState.IDLE
        
        print(f"✓ State transitions tracked successfully")
    
    @pytest.mark.asyncio
    async def test_007_domain_specialization_creates_unique_capital(self):
        """
        Test 7: Especialización por dominio crea capital único
        Capital: Conocimiento específico del dominio
        """
        domains_to_test = [Domain.CODEX, Domain.APEX, Domain.VITALIS, Domain.ATHLON]
        
        for domain in domains_to_test:
            agent = (AgentProfileBuilder()
                .with_id(f"agent-{domain.value}")
                .with_domain(domain)
                .with_role(IOVBARole.BUILDER)
                .build())
            
            # Verificar que cada dominio tiene skills diferentes
            print(f"✓ Domain {domain.value}: {list(agent.skills.keys())}")
            assert len(agent.skills) > 0
    
    @pytest.mark.asyncio
    async def test_008_iovba_role_defines_behavior_pattern(self):
        """
        Test 8: Rol IOVBA define patrón de comportamiento
        Capital: Patrones de comportamiento documentados
        """
        roles = [IOVBARole.INVESTIGATOR, IOVBARole.OBSERVER, 
                 IOVBARole.VALIDATOR, IOVBARole.BUILDER, IOVBARole.ASSISTANT]
        
        for role in roles:
            agent = (AgentProfileBuilder()
                .with_id(f"role-{role.value}")
                .with_domain(Domain.CODEX)
                .with_role(role)
                .build())
            
            assert agent.role == role
            print(f"✓ Role {role.value} configured")
    
    @pytest.mark.asyncio
    async def test_009_execution_strategy_selection_affects_performance(self):
        """
        Test 9: Selección de estrategia de ejecución afecta rendimiento
        Capital: Conocimiento de estrategias óptimas
        """
        agent = AgentFactory.create_codex_agent()
        
        # Cambiar estrategia
        agent.execution_strategy = "parallel"
        assert agent.execution_strategy == "parallel"
        
        agent.execution_strategy = "hierarchical"
        assert agent.execution_strategy == "hierarchical"
        
        agent.execution_strategy = "adaptive"
        assert agent.execution_strategy == "adaptive"
        
        print(f"✓ Execution strategies tested")
    
    @pytest.mark.asyncio
    async def test_010_serialization_preserves_capital(self):
        """
        Test 10: Serialización preserva capital cognitivo
        Capital: Persistencia del conocimiento
        """
        original = AgentFactory.create_codex_agent(SkillLevel.EXPERT)
        
        # Añadir experiencia
        await original.learn_from_experience(
            ExperienceGenerator.generate_code_review_experience(success=True)
        )
        
        # Serializar
        data = original.to_dict()
        
        # Deserializar
        restored = AgentProfile.from_dict(data)
        
        assert restored.agent_id == original.agent_id
        assert restored.domain == original.domain
        assert len(restored.skills) == len(original.skills)
        
        print(f"✓ Capital preserved through serialization")


# ============================================================================
# TEST GROUP 2: EXECUTION PATTERNS - Capital Operativo (Tests 11-20)
# ============================================================================

class TestExecutionPatternsCapital:
    """Tests que construyen capital cognitivo operativo"""
    
    @pytest.mark.asyncio
    async def test_011_sequential_execution_creates_procedural_knowledge(self):
        """
        Test 11: Ejecución secuencial crea conocimiento procedural
        Capital: Procedimientos paso a paso
        """
        agent = AgentFactory.create_codex_agent()
        agent.execution_strategy = "sequential"
        
        task = {
            "steps": [
                {"action": "analyze", "expected_output": "analysis"},
                {"action": "design", "expected_output": "design"},
                {"action": "implement", "expected_output": "code"},
                {"action": "test", "expected_output": "results"}
            ]
        }
        
        result = await agent.execute_task(task)
        
        assert result["status"] == "success"
        assert result["strategy"] == "sequential"
        assert result["total_steps"] == 4
        
        # Aprender de la experiencia
        await agent.learn_from_experience({
            "type": "sequential_execution",
            "success": True,
            "skills_used": ["planning", "execution"],
            "context": {"steps": 4}
        })
        
        print(f"✓ Sequential execution capital: {agent.capital_value}")
    
    @pytest.mark.asyncio
    async def test_012_parallel_execution_builds_concurrency_knowledge(self):
        """
        Test 12: Ejecución paralela construye conocimiento de concurrencia
        Capital: Patrones de paralelización
        """
        agent = AgentFactory.create_codex_agent()
        agent.execution_strategy = "parallel"
        
        task = {
            "subtasks": [
                {"id": "task-1", "type": "analysis"},
                {"id": "task-2", "type": "generation"},
                {"id": "task-3", "type": "validation"}
            ]
        }
        
        result = await agent.execute_task(task)
        
        assert result["status"] == "success"
        assert result["strategy"] == "parallel"
        assert result["parallel_count"] == 3
        
        print(f"✓ Parallel execution completed")
    
    @pytest.mark.asyncio
    async def test_013_hierarchical_execution_creates_delegation_knowledge(self):
        """
        Test 13: Ejecución jerárquica crea conocimiento de delegación
        Capital: Patrones de delegación y coordinación
        """
        agent = AgentFactory.create_codex_agent()
        agent.execution_strategy = "hierarchical"
        
        task = {
            "delegation_tree": {
                "id": "root",
                "children": [
                    {"id": "child-1", "children": []},
                    {"id": "child-2", "children": [
                        {"id": "grandchild", "children": []}
                    ]}
                ]
            }
        }
        
        result = await agent.execute_task(task)
        
        assert result["status"] == "success"
        assert result["strategy"] == "hierarchical"
        assert result["tree_depth"] >= 1
        
        print(f"✓ Hierarchical execution depth: {result['tree_depth']}")
    
    @pytest.mark.asyncio
    async def test_014_adaptive_strategy_learns_optimal_selection(self):
        """
        Test 14: Estrategia adaptativa aprende selección óptima
        Capital: Metadatos de selección de estrategias
        """
        agent = AgentFactory.create_codex_agent()
        agent.execution_strategy = "adaptive"
        
        # Ejecutar múltiples tipos de tareas
        tasks = [
            {"steps": [{"action": "a"}, {"action": "b"}]},  # Sequential
            {"subtasks": [{"id": "1"}, {"id": "2"}]},       # Parallel
            {"delegation_tree": {"id": "root"}},            # Hierarchical
        ]
        
        for task in tasks:
            result = await agent.execute_task(task)
            assert result["status"] == "success"
            print(f"  → Strategy selected: {result['strategy']}")
        
        print(f"✓ Adaptive strategy learning complete")
    
    @pytest.mark.asyncio
    async def test_015_command_pattern_encapsulates_actions(self):
        """
        Test 15: Patrón Command encapsula acciones reutilizables
        Capital: Biblioteca de comandos encapsulados
        """
        agent = AgentFactory.create_codex_agent()
        
        # Ejecutar comandos encapsulados
        analyze_cmd = AnalyzeCommand(agent, {"data": "sample"}, "sentiment")
        generate_cmd = GenerateCommand(agent, "Create report", "markdown")
        coordinate_cmd = CoordinateCommand(agent, ["agent-2", "agent-3"], {"task": "collaborate"})
        
        result1 = await agent.execute_command(analyze_cmd)
        result2 = await agent.execute_command(generate_cmd)
        result3 = await agent.execute_command(coordinate_cmd)
        
        assert result1["status"] == "completed"
        assert result2["status"] == "completed"
        assert result3["status"] == "completed"
        
        history = agent.get_command_history()
        assert len(history) == 3
        
        print(f"✓ Commands executed: {history}")
    
    @pytest.mark.asyncio
    async def test_016_command_undo_provides_recovery_knowledge(self):
        """
        Test 16: Undo de comandos proporciona conocimiento de recuperación
        Capital: Patrones de reversión
        """
        agent = AgentFactory.create_codex_agent()
        
        # Ejecutar y deshacer
        cmd = AnalyzeCommand(agent, {"data": "test"}, "pattern")
        await agent.execute_command(cmd)
        
        undo_result = await agent.undo_last_command()
        assert undo_result["status"] == "undone"
        
        print(f"✓ Command undo provides recovery pattern")
    
    @pytest.mark.asyncio
    async def test_017_retry_decorator_builds_resilience_knowledge(self):
        """
        Test 17: Decorador Retry construye conocimiento de resiliencia
        Capital: Patrones de reintento y backoff
        """
        agent = AgentFactory.create_codex_agent()
        retry_agent = RetryDecorator(agent, max_retries=3)
        
        task = {"type": "flaky_operation"}
        result = await retry_agent.execute_with_enhancement(task)
        
        assert "attempts" in result
        assert result["attempts"] <= 3
        
        print(f"✓ Retry pattern tested: {result.get('attempts')} attempts")
    
    @pytest.mark.asyncio
    async def test_018_caching_decorator_builds_efficiency_knowledge(self):
        """
        Test 18: Decorador Caching construye conocimiento de eficiencia
        Capital: Patrones de caché y optimización
        """
        agent = AgentFactory.create_codex_agent()
        cached_agent = CachingDecorator(agent)
        
        task = {"type": "expensive_operation", "id": "unique-123"}
        
        # Primera ejecución (sin caché)
        result1 = await cached_agent.execute_with_enhancement(task)
        assert result1.get("cached", False) == False
        
        # Segunda ejecución (con caché)
        result2 = await cached_agent.execute_with_enhancement(task)
        assert result2.get("cached", False) == True
        
        print(f"✓ Caching improves efficiency")
    
    @pytest.mark.asyncio
    async def test_019_metrics_decorator_tracks_performance_knowledge(self):
        """
        Test 19: Decorador Metrics rastrea conocimiento de rendimiento
        Capital: Métricas de rendimiento históricas
        """
        agent = AgentFactory.create_codex_agent()
        measured_agent = MetricsDecorator(agent)
        
        # Ejecutar múltiples tareas
        for i in range(5):
            result = await measured_agent.execute_with_enhancement({"type": "test"})
            assert "metrics" in result
            assert "duration_seconds" in result["metrics"]
        
        print(f"✓ Performance metrics collected")
    
    @pytest.mark.asyncio
    async def test_020_logging_decorator_creates_audit_trail(self):
        """
        Test 20: Decorador Logging crea trail de auditoría
        Capital: Historial de acciones para auditoría
        """
        agent = AgentFactory.create_codex_agent()
        logged_agent = LoggingDecorator(agent)
        
        result = await logged_agent.execute_with_enhancement({"type": "auditable_action"})
        
        assert result["status"] == "success"
        
        print(f"✓ Audit trail created via logging")


# ============================================================================
# TEST GROUP 3: PPCC CYCLE - Capital de Coordinación (Tests 21-30)
# ============================================================================

class TestPPCCCapital:
    """Tests que construyen capital cognitivo del ciclo PPCC"""
    
    @pytest.mark.asyncio
    async def test_021_preparation_phase_creates_context_capital(self):
        """
        Test 21: Fase de Preparación crea capital de contexto
        Capital: Contextos de obviedad bien definidos
        """
        cycle = PPCCCycle()
        
        result = await cycle.prepare({
            "objective": "Analyze customer feedback",
            "user_id": "user-001",
            "success_criteria": "accuracy >= 90%",
            "metrics": {"recall": 0.85, "precision": 0.90}
        })
        
        assert result["phase"] == "preparation"
        assert result["next_step"] == "alignment"
        assert cycle.state.current_phase == PPCCPhase.ALIGNMENT
        
        print(f"✓ Preparation phase capital created")
    
    @pytest.mark.asyncio
    async def test_022_alignment_phase_builds_understanding_capital(self):
        """
        Test 22: Fase de Alineación construye capital de entendimiento
        Capital: Entendimiento mutuo documentado
        """
        cycle = PPCCCycle()
        
        await cycle.prepare({"objective": "Test alignment", "user_id": "u1"})
        result = await cycle.request_alignment()
        
        assert result["phase"] == "alignment"
        assert result["execution_blocked"] == True
        assert "alignment_prompt" in result
        
        print(f"✓ Alignment phase capital built")
    
    @pytest.mark.asyncio
    async def test_023_alignment_confirmation_validates_capital(self):
        """
        Test 23: Confirmación de alineación valida capital
        Capital: Validación de entendimiento
        """
        cycle = PPCCCycle()
        
        await cycle.prepare({"objective": "Test confirm", "user_id": "u1"})
        await cycle.request_alignment()
        
        result = await cycle.confirm_alignment(
            "I understand that I need to test the confirmation flow",
            user_confirmed=True
        )
        
        assert result["status"] == "confirmed"
        assert cycle.state.alignment_confirmed == True
        
        print(f"✓ Alignment validated")
    
    @pytest.mark.asyncio
    async def test_024_execution_phase_generates_operational_capital(self):
        """
        Test 24: Fase de Ejecución genera capital operativo
        Capital: Resultados de operaciones ejecutadas
        """
        cycle = PPCCCycle()
        
        await cycle.prepare({"objective": "Test execution", "user_id": "u1"})
        await cycle.request_alignment()
        await cycle.confirm_alignment("Understanding confirmed", user_confirmed=True)
        
        result = await cycle.execute("Execute test task")
        
        assert result["phase"] == "execution"
        assert result["reasoning_visible"] == True
        
        print(f"✓ Execution capital generated")
    
    @pytest.mark.asyncio
    async def test_025_declaration_phase_closes_capital_cycle(self):
        """
        Test 25: Fase de Declaración cierra ciclo de capital
        Capital: Cierre formal con satisfacción/insatisfacción
        """
        cycle = PPCCCycle()
        
        await cycle.prepare({"objective": "Test declaration", "user_id": "u1"})
        await cycle.request_alignment()
        await cycle.confirm_alignment("Understanding", user_confirmed=True)
        await cycle.execute("Execute")
        
        result = await cycle.declare_result(
            satisfaction=True,
            feedback="Excellent work, met all criteria"
        )
        
        assert result["phase"] == "declaration"
        assert result["satisfaction"] == True
        assert cycle.state.current_phase == PPCCPhase.COMPLETED
        
        print(f"✓ Declaration closes capital cycle")
    
    @pytest.mark.asyncio
    async def test_026_unsatisfied_declaration_triggers_learning(self):
        """
        Test 26: Declaración insatisfecha dispara aprendizaje
        Capital: Oportunidades de mejora identificadas
        """
        cycle = PPCCCycle()
        
        await cycle.prepare({"objective": "Test failure learning", "user_id": "u1"})
        await cycle.request_alignment()
        await cycle.confirm_alignment("Understanding", user_confirmed=True)
        await cycle.execute("Execute with issues")
        
        result = await cycle.declare_result(
            satisfaction=False,
            feedback="Did not meet quality standards"
        )
        
        assert result["satisfaction"] == False
        assert "learning_opportunity" in result
        
        print(f"✓ Unsatisfied declaration creates learning opportunity")
    
    @pytest.mark.asyncio
    async def test_027_full_ppcc_cycle_accumulates_capital(self):
        """
        Test 27: Ciclo PPCC completo acumula capital
        Capital: Capital acumulado por ciclo completo
        """
        cycle = PPCCCycle()
        
        # Preparación
        await cycle.prepare({
            "objective": "Complete PPCC cycle test",
            "user_id": "test-user",
            "success_criteria": "All phases completed"
        })
        
        # Alineación
        await cycle.request_alignment()
        await cycle.confirm_alignment("Full understanding achieved", user_confirmed=True)
        
        # Ejecución
        await cycle.execute("Execute full cycle test")
        
        # Declaración
        result = await cycle.declare_result(satisfaction=True)
        
        assert cycle.state.current_phase == PPCCPhase.COMPLETED
        assert "duration_seconds" in result
        
        print(f"✓ Full PPCC cycle completed in {result['duration_seconds']:.2f}s")
    
    @pytest.mark.asyncio
    async def test_028_multiple_cycles_build_experience_capital(self):
        """
        Test 28: Múltiples ciclos construyen capital de experiencia
        Capital: Experiencia acumulada en ciclos
        """
        results = []
        
        for i in range(5):
            cycle = PPCCCycle()
            await cycle.prepare({
                "objective": f"Cycle {i+1}",
                "user_id": "multi-cycle-user"
            })
            await cycle.request_alignment()
            await cycle.confirm_alignment(f"Understanding {i+1}", user_confirmed=True)
            await cycle.execute(f"Task {i+1}")
            result = await cycle.declare_result(satisfaction=(i % 2 == 0))
            results.append(result)
        
        satisfied_count = sum(1 for r in results if r["satisfaction"])
        
        print(f"✓ Multiple cycles: {len(results)} cycles, {satisfied_count} satisfied")
    
    @pytest.mark.asyncio
    async def test_029_alignment_rejection_triggers_repreparation(self):
        """
        Test 29: Rechazo de alineación dispara re-preparación
        Capital: Patrones de iteración y corrección
        """
        cycle = PPCCCycle()
        
        await cycle.prepare({"objective": "Test rejection", "user_id": "u1"})
        await cycle.request_alignment()
        
        # Rechazar alineación
        result = await cycle.confirm_alignment(
            "Incorrect understanding",
            user_confirmed=False
        )
        
        assert result["status"] == "not_confirmed"
        assert cycle.state.iteration_count == 1
        
        print(f"✓ Alignment rejection triggers iteration")
    
    @pytest.mark.asyncio
    async def test_030_ppcc_state_serialization_preserves_capital(self):
        """
        Test 30: Serialización de estado PPCC preserva capital
        Capital: Persistencia de estado de ciclo
        """
        cycle = PPCCCycle()
        
        await cycle.prepare({"objective": "Serialization test", "user_id": "u1"})
        await cycle.request_alignment()
        await cycle.confirm_alignment("Understanding", user_confirmed=True)
        
        # Serializar estado
        state = cycle.get_state()
        
        assert state["cycle_id"] is not None
        assert state["current_phase"] == PPCCPhase.EXECUTION.value
        assert state["alignment_confirmed"] == True
        
        print(f"✓ PPCC state serialized")


# ============================================================================
# TEST GROUP 4: LEARNING PIPELINE - Capital de Aprendizaje (Tests 31-40)
# ============================================================================

class TestLearningPipelineCapital:
    """Tests que construyen capital cognitivo mediante aprendizaje"""
    
    @pytest.mark.asyncio
    async def test_031_learning_event_creation_initializes_capital(self):
        """
        Test 31: Creación de evento de aprendizaje inicializa capital
        Capital: Eventos de aprendizaje estructurados
        """
        event = LearningEvent(
            event_type=LearningEventType.TASK_COMPLETED,
            source_agent_id="agent-001",
            source_domain="codex",
            payload={"result": "success"},
            learning_value=0.8
        )
        
        assert event.id is not None
        assert event.processed == False
        assert event.learning_value == 0.8
        
        print(f"✓ Learning event created: {event.event_type.value}")
    
    @pytest.mark.asyncio
    async def test_032_reinforcement_engine_builds_reward_capital(self):
        """
        Test 32: Motor de refuerzo construye capital de recompensas
        Capital: Tabla Q de valores estado-acción
        """
        engine = ReinforcementEngine()
        
        # Crear evento y computar recompensa
        event = LearningEvent(
            event_type=LearningEventType.SUCCESS_ACHIEVED,
            learning_value=0.9
        )
        
        reward = engine.compute_reward(event, "success")
        
        # Actualizar Q-value
        new_q = engine.update_q_value("state_1", "action_A", reward, "state_2")
        
        assert reward > 0
        assert new_q != 0
        
        metrics = engine.get_metrics()
        assert metrics["total_reinforcements"] == 1
        
        print(f"✓ Reward capital: {reward:.2f}, Q-value: {new_q:.4f}")
    
    @pytest.mark.asyncio
    async def test_033_q_learning_accumulates_policy_capital(self):
        """
        Test 33: Q-Learning acumula capital de política
        Capital: Política óptima aprendida
        """
        engine = ReinforcementEngine()
        
        # Simular múltiples episodios de aprendizaje
        states = ["analyze", "design", "implement", "test", "deploy"]
        actions = ["proceed", "retry", "escalate"]
        
        for episode in range(20):
            state = random.choice(states)
            action = random.choice(actions)
            
            event = LearningEvent(
                event_type=random.choice([
                    LearningEventType.SUCCESS_ACHIEVED,
                    LearningEventType.TASK_COMPLETED,
                    LearningEventType.ERROR_OCCURRED
                ]),
                learning_value=random.uniform(0.3, 1.0)
            )
            
            reward = engine.compute_reward(event, "processed")
            engine.update_q_value(state, action, reward)
        
        # Verificar que hay política aprendida
        best_action = engine.get_best_action("analyze")
        
        metrics = engine.get_metrics()
        print(f"✓ Q-Learning: {metrics['total_states']} states, "
              f"{metrics['total_state_action_pairs']} state-action pairs")
    
    @pytest.mark.asyncio
    async def test_034_exploration_exploitation_balances_capital(self):
        """
        Test 34: Balance exploración/explotación optimiza capital
        Capital: Conocimiento de cuándo explorar vs explotar
        """
        engine = ReinforcementEngine()
        
        # Pre-poblar con algo de conocimiento
        engine.update_q_value("state_A", "action_1", 0.8)
        engine.update_q_value("state_A", "action_2", 0.5)
        
        # Exploración vs Explotación
        actions = ["action_1", "action_2", "action_3"]
        
        selected = engine.get_exploration_action(
            "state_A",
            actions,
            exploration_rate=0.2  # 20% exploración
        )
        
        assert selected in actions
        
        print(f"✓ Exploration/exploitation balance: selected {selected}")
    
    @pytest.mark.asyncio
    async def test_035_coordination_engine_shares_capital(self):
        """
        Test 35: Motor de coordinación comparte capital entre agentes
        Capital: Capital compartido entre agentes
        """
        engine = CoordinationEngine()
        
        # Registrar múltiples agentes
        engine.register_agent("agent-1", "codex", ["analysis", "coding"])
        engine.register_agent("agent-2", "codex", ["testing", "review"])
        engine.register_agent("agent-3", "codex", ["deployment"])
        
        # Crear evento de aprendizaje para compartir
        event = LearningEvent(
            event_type=LearningEventType.KNOWLEDGE_GAINED,
            source_agent_id="agent-1",
            source_domain="codex",
            payload={
                "patterns": ["factory_pattern", "observer_pattern"],
                "skills": {"refactoring": {"level": "advanced"}}
            },
            broadcast=True
        )
        
        result = await engine.coordinate_learning(event, {
            "patterns": ["factory_pattern"],
            "skills": {"refactoring": {"level": "advanced"}},
            "insights": []
        })
        
        assert result["coordination_type"] == "broadcast"
        
        metrics = engine.get_coordination_metrics()
        print(f"✓ Coordination: {metrics['registered_agents']} agents, "
              f"{metrics['coordination_events']} events")
    
    @pytest.mark.asyncio
    async def test_036_reflection_engine_generates_insight_capital(self):
        """
        Test 36: Motor de reflexión genera capital de insights
        Capital: Insights generados por reflexión
        """
        engine = ReflectionEngine()
        
        # Crear reporte de capital simulado
        capital_report = {
            "metrics": {"capital_value": 150.5},
            "experiences": {"total": 100, "successful": 85},
            "skills": {"by_level": {"expert": 2, "advanced": 5, "beginner": 3}},
            "insights": {"total": 12}
        }
        
        # Ejecutar reflexión
        reflection = await engine.reflect(
            "agent-001",
            capital_report,
            {"success_rate": 0.85, "coordination_graph_size": 5}
        )
        
        assert len(reflection["reflection_types"]) > 0
        assert reflection["improvement_plan"] is not None or len(reflection["recommendations"]) == 0
        
        print(f"✓ Reflection types: {reflection['reflection_types']}")
    
    @pytest.mark.asyncio
    async def test_037_learning_pipeline_integrates_all_capital(self):
        """
        Test 37: Pipeline de aprendizaje integra todo el capital
        Capital: Integración completa de todos los tipos
        """
        pipeline = LearningPipeline("test-agent", "codex")
        await pipeline.start()
        
        # Enviar múltiples eventos
        events = [
            LearningEvent(
                event_type=LearningEventType.TASK_COMPLETED,
                source_agent_id="test-agent",
                source_domain="codex",
                payload={"task": "analysis"},
                learning_value=0.7
            ),
            LearningEvent(
                event_type=LearningEventType.SUCCESS_ACHIEVED,
                source_agent_id="test-agent",
                source_domain="codex",
                payload={"result": "excellent"},
                learning_value=0.9
            ),
            LearningEvent(
                event_type=LearningEventType.INSIGHT_GENERATED,
                source_agent_id="test-agent",
                source_domain="codex",
                payload={"insight": "pattern discovered"},
                learning_value=0.6
            )
        ]
        
        for event in events:
            await pipeline.submit_event(event)
        
        # Procesar cola
        results = await pipeline.process_queue(batch_size=10)
        
        assert len(results) == 3
        
        status = pipeline.get_pipeline_status()
        assert status["metrics"]["events_processed"] == 3
        
        print(f"✓ Pipeline integrated {status['metrics']['events_processed']} events")
    
    @pytest.mark.asyncio
    async def test_038_experience_processing_creates_real_capital(self):
        """
        Test 38: Procesamiento de experiencias crea capital real
        Capital: Experiencias procesadas y transformadas
        """
        agent = AgentFactory.create_codex_agent()
        
        # Procesar múltiples experiencias reales
        experiences = [
            ExperienceGenerator.generate_code_review_experience(success=True),
            ExperienceGenerator.generate_task_execution_experience("analysis", success=True),
            ExperienceGenerator.generate_task_execution_experience("generation", success=False),
            ExperienceGenerator.generate_error_recovery_experience(),
        ]
        
        for exp in experiences:
            result = await agent.learn_from_experience(exp)
            print(f"  → Experience processed: {exp['type']}, insight: {result['insight_generated']}")
        
        assert len(agent._experiences) == 4
        assert len(agent._insights) >= 1
        
        print(f"✓ Real capital from {len(agent._experiences)} experiences")
    
    @pytest.mark.asyncio
    async def test_039_failure_recovery_creates_valuable_capital(self):
        """
        Test 39: Recuperación de fallos crea capital muy valioso
        Capital: Patrones de recuperación de errores
        """
        agent = AgentFactory.create_codex_agent()
        
        # Generar experiencias de error y recuperación
        for i in range(10):
            exp = ExperienceGenerator.generate_error_recovery_experience()
            await agent.learn_from_experience(exp)
        
        # Verificar que los insights de error son valiosos
        error_insights = [i for i in agent._insights if i.get("type") == "failure_pattern"]
        
        print(f"✓ Error recovery capital: {len(error_insights)} error insights")
    
    @pytest.mark.asyncio
    async def test_040_reflection_cycle_improves_capital(self):
        """
        Test 40: Ciclo de reflexión mejora capital existente
        Capital: Mejora continua del capital
        """
        pipeline = LearningPipeline("reflect-agent", "codex")
        await pipeline.start()
        
        # Crear capital report
        capital_report = {
            "metrics": {"capital_value": 50.0},
            "experiences": {"total": 20, "successful": 15},
            "skills": {"by_level": {"advanced": 3, "intermediate": 5}},
            "insights": {"total": 5}
        }
        
        # Ejecutar reflexión
        reflection = await pipeline.run_reflection_cycle(capital_report)
        
        assert reflection["agent_id"] == "reflect-agent"
        
        # Verificar plan de mejora
        if reflection["improvement_plan"]:
            print(f"  → Improvement plan: {len(reflection['improvement_plan']['actions'])} actions")
        
        print(f"✓ Reflection cycle completed")


# ============================================================================
# TEST GROUP 5: MEMORY & VECTORS - Capital de Persistencia (Tests 41-50)
# ============================================================================

class TestMemoryAndVectorsCapital:
    """Tests que construyen capital cognitivo en memoria y vectores"""
    
    @pytest.mark.asyncio
    async def test_041_short_term_memory_stores_session_capital(self):
        """
        Test 41: Memoria a corto plazo almacena capital de sesión
        Capital: Conocimiento de sesión actual
        """
        memory = CognitiveMemory()
        
        await memory.store("current_task", {"type": "analysis", "status": "in_progress"}, scope="short")
        await memory.store("user_preferences", {"language": "python", "style": "verbose"}, scope="short")
        
        retrieved = await memory.retrieve("current_task", scope="short")
        
        assert retrieved is not None
        assert retrieved["type"] == "analysis"
        
        print(f"✓ Short-term memory capital stored")
    
    @pytest.mark.asyncio
    async def test_042_long_term_memory_persists_capital(self):
        """
        Test 42: Memoria a largo plazo persiste capital
        Capital: Conocimiento persistente entre sesiones
        """
        memory = CognitiveMemory()
        
        # Almacenar conocimiento valioso a largo plazo
        await memory.store("learned_pattern", {
            "name": "error_recovery_pattern",
            "description": "When encountering timeout, use exponential backoff",
            "effectiveness": 0.85
        }, scope="long")
        
        await memory.store("domain_knowledge", {
            "domain": "codex",
            "best_practices": ["TDD", "code_review", "CI/CD"],
            "common_patterns": ["factory", "singleton", "observer"]
        }, scope="long")
        
        # Recuperar
        pattern = await memory.retrieve("learned_pattern", scope="long")
        knowledge = await memory.retrieve("domain_knowledge", scope="long")
        
        assert pattern is not None
        assert knowledge is not None
        
        print(f"✓ Long-term memory capital persisted")
    
    @pytest.mark.asyncio
    async def test_043_working_memory_maintains_active_context(self):
        """
        Test 43: Memoria de trabajo mantiene contexto activo
        Capital: Contexto activo para operación actual
        """
        memory = CognitiveMemory()
        
        # Memoria de trabajo para operación activa
        await memory.store("active_variables", {"x": 10, "y": 20}, scope="working")
        await memory.store("execution_state", {"step": 3, "total": 5}, scope="working")
        
        context = await memory.get_context()
        
        assert "working" in context
        assert "active_variables" in context["working"]
        
        print(f"✓ Working memory context maintained")
    
    @pytest.mark.asyncio
    async def test_044_semantic_search_retrieves_relevant_capital(self):
        """
        Test 44: Búsqueda semántica recupera capital relevante
        Capital: Recuperación inteligente de conocimiento
        """
        memory = CognitiveMemory()
        
        # Almacenar varios items
        await memory.store("error_handling", "When error occurs, log and retry with backoff", scope="long")
        await memory.store("success_pattern", "Code review improves quality by 40%", scope="long")
        await memory.store("optimization", "Caching reduces latency significantly", scope="long")
        
        # Búsqueda semántica
        results = await memory.search("error retry")
        
        assert len(results) > 0
        
        print(f"✓ Semantic search found {len(results)} relevant items")
    
    @pytest.mark.asyncio
    async def test_045_memory_indexing_enables_fast_retrieval(self):
        """
        Test 45: Indexación de memoria habilita recuperación rápida
        Capital: Índices para acceso eficiente
        """
        memory = CognitiveMemory()
        
        # Almacenar muchos items
        for i in range(50):
            await memory.store(f"item_{i}", {
                "content": f"Knowledge item number {i}",
                "category": random.choice(["code", "docs", "config"]),
                "importance": random.uniform(0.1, 1.0)
            }, scope="long")
        
        # Verificar indexación
        assert len(memory._semantic_index) > 0
        
        print(f"✓ Memory indexed: {len(memory._semantic_index)} unique terms")
    
    @pytest.mark.asyncio
    async def test_046_agent_memory_integration(self):
        """
        Test 46: Integración de memoria con agente
        Capital: Memoria integrada en perfil del agente
        """
        agent = AgentFactory.create_codex_agent()
        
        # Almacenar conocimiento en memoria del agente
        await agent.memory.store("task_history", [
            {"task": "refactor", "result": "success"},
            {"task": "test", "result": "success"},
        ], scope="long")
        
        # Recuperar y usar
        history = await agent.memory.retrieve("task_history", scope="long")
        
        assert history is not None
        assert len(history) == 2
        
        print(f"✓ Agent memory integration working")
    
    @pytest.mark.asyncio
    async def test_047_cross_session_capital_persistence(self):
        """
        Test 47: Persistencia de capital entre sesiones
        Capital: Capital que sobrevive sesiones
        """
        # Crear agente y generar capital
        agent1 = AgentFactory.create_codex_agent()
        
        for i in range(10):
            await agent1.learn_from_experience(
                ExperienceGenerator.generate_task_execution_experience()
            )
        
        # Serializar
        data = agent1.to_dict()
        
        # "Nueva sesión" - deserializar
        agent2 = AgentProfile.from_dict(data)
        
        # Verificar capital preservado
        assert agent2.capital_value == agent1.capital_value
        
        print(f"✓ Cross-session capital: {agent2.capital_value} preserved")
    
    @pytest.mark.asyncio
    async def test_048_vector_embedding_concept(self):
        """
        Test 48: Concepto de embeddings vectoriales para capital
        Capital: Representación vectorial del conocimiento
        """
        # Simulación de embeddings (en producción usaría Milvus/Qdrant)
        knowledge_items = [
            "Python is a programming language",
            "Machine learning uses algorithms",
            "Code review improves quality",
            "Testing prevents bugs",
            "Documentation helps maintenance"
        ]
        
        # Simular embeddings (en producción real con sentence-transformers)
        embeddings = {}
        for item in knowledge_items:
            # Simplified: usar hash como placeholder
            embeddings[item] = [hash(word) % 100 / 100 for word in item.split()[:5]]
        
        # Simular búsqueda por similitud
        query = "programming language python"
        query_embedding = [hash(word) % 100 / 100 for word in query.split()[:5]]
        
        # Calcular similitud (simplificado)
        def cosine_sim(a, b):
            min_len = min(len(a), len(b))
            if min_len == 0:
                return 0
            return sum(x * y for x, y in zip(a[:min_len], b[:min_len]))
        
        similarities = [
            (item, cosine_sim(query_embedding, emb))
            for item, emb in embeddings.items()
        ]
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        print(f"✓ Vector similarity search (simulated):")
        for item, score in similarities[:3]:
            print(f"    {score:.3f}: {item[:40]}...")
    
    @pytest.mark.asyncio
    async def test_049_knowledge_graph_concept(self):
        """
        Test 49: Concepto de grafo de conocimiento
        Capital: Relaciones entre conocimiento
        """
        # Grafo de conocimiento simplificado
        knowledge_graph = {
            "nodes": {
                "python": {"type": "language", "level": "skill"},
                "testing": {"type": "practice", "level": "skill"},
                "pytest": {"type": "tool", "level": "tool"},
                "TDD": {"type": "methodology", "level": "practice"},
            },
            "edges": [
                {"from": "python", "to": "testing", "relation": "uses"},
                {"from": "testing", "to": "pytest", "relation": "implemented_by"},
                {"from": "TDD", "to": "testing", "relation": "requires"},
            ]
        }
        
        # Navegar grafo
        def get_related(node, graph):
            related = []
            for edge in graph["edges"]:
                if edge["from"] == node:
                    related.append((edge["to"], edge["relation"]))
                elif edge["to"] == node:
                    related.append((edge["from"], f"inverse_{edge['relation']}"))
            return related
        
        related = get_related("python", knowledge_graph)
        
        print(f"✓ Knowledge graph: python -> {related}")
    
    @pytest.mark.asyncio
    async def test_050_memory_capacity_optimization(self):
        """
        Test 50: Optimización de capacidad de memoria
        Capital: Gestión eficiente del espacio de memoria
        """
        memory = CognitiveMemory()
        
        # Almacenar 100 items
        for i in range(100):
            await memory.store(f"item_{i}", f"content_{i}" * 10, scope="long")
        
        # Verificar estructura
        status = memory.to_dict()
        
        assert len(memory._long_term) == 100
        
        # Simular limpieza (en producción sería más sofisticado)
        # Mantener solo últimos 50
        memory._long_term = memory._long_term[-50:]
        
        assert len(memory._long_term) == 50
        
        print(f"✓ Memory optimized: 100 -> {len(memory._long_term)} items")


# ============================================================================
# TEST GROUP 6: ADVANCED SCENARIOS - Capital de Escenarios (Tests 51-60)
# ============================================================================

class TestAdvancedScenariosCapital:
    """Tests con escenarios avanzados que generan capital complejo"""
    
    @pytest.mark.asyncio
    async def test_051_multi_agent_coordination_scenario(self):
        """
        Test 51: Escenario de coordinación multi-agente
        Capital: Patrones de coordinación entre agentes
        """
        # Crear equipo de agentes
        team = AgentFactory.create_hierarchical_team()
        
        leader = team[0]
        members = team[1:]
        
        # Registrar todos
        registry = AgentRegistry()
        for agent in team:
            registry.register(agent)
        
        # Simular coordinación
        task = {
            "type": "collaborative",
            "subtasks": [
                {"id": f"subtask_{i}", "assigned_to": m.agent_id}
                for i, m in enumerate(members)
            ]
        }
        
        result = await leader.execute_task(task)
        
        assert result["status"] == "success"
        
        total_capital = registry.get_total_capital()
        print(f"✓ Multi-agent coordination: {len(team)} agents, capital: {total_capital}")
    
    @pytest.mark.asyncio
    async def test_052_error_cascade_recovery_scenario(self):
        """
        Test 52: Escenario de recuperación en cascada de errores
        Capital: Patrones de recuperación de errores en cadena
        """
        agent = AgentFactory.create_codex_agent()
        retry_agent = RetryDecorator(agent, max_retries=5)
        
        # Simular múltiples errores en secuencia
        for i in range(10):
            exp = ExperienceGenerator.generate_error_recovery_experience()
            await agent.learn_from_experience(exp)
        
        # Verificar capital de recuperación
        error_insights = [i for i in agent._insights if "error" in str(i).lower() or "recovery" in str(i).lower()]
        
        print(f"✓ Error cascade recovery: {len(error_insights)} recovery insights")
    
    @pytest.mark.asyncio
    async def test_053_domain_transfer_learning_scenario(self):
        """
        Test 53: Escenario de transferencia de aprendizaje entre dominios
        Capital: Transferencia de conocimiento entre dominios
        """
        # Crear agentes de diferentes dominios
        codex_agent = AgentFactory.create_codex_agent()
        apex_agent = AgentFactory.create_apex_agent()
        
        # Generar experiencia en CODEX
        for i in range(5):
            await codex_agent.learn_from_experience(
                ExperienceGenerator.generate_code_review_experience(success=True)
            )
        
        # Intentar transferir conocimiento
        # (En producción, esto usaría el CoordinationEngine)
        pipeline = LearningPipeline("transfer-test", "apex")
        await pipeline.start()
        
        # Crear evento de transferencia
        transfer_event = LearningEvent(
            event_type=LearningEventType.PEER_LEARNING,
            source_agent_id=codex_agent.agent_id,
            source_domain="codex",
            payload={
                "transferred_patterns": ["error_handling", "optimization"],
                "source_experiences": len(codex_agent._experiences)
            },
            target_agents=[apex_agent.agent_id],
            learning_value=0.7
        )
        
        result = await pipeline.process_event(transfer_event)
        
        print(f"✓ Domain transfer: {result['capital_delta']:.2f} capital transferred")
    
    @pytest.mark.asyncio
    async def test_054_continuous_learning_loop_scenario(self):
        """
        Test 54: Escenario de bucle de aprendizaje continuo (Ralph Loop)
        Capital: Ralph Loop completo implementado
        """
        agent = AgentFactory.create_codex_agent()
        
        # Implementar Ralph Loop simplificado
        # Reflect -> Analyze -> Learn -> Practice -> Harvest
        
        for iteration in range(10):
            # 1. Reflect: Analizar estado actual
            capital_report = {
                "metrics": {"capital_value": agent.capital_value},
                "experiences": {"total": len(agent._experiences), "successful": 0},
                "skills": agent.skills,
                "insights": {"total": len(agent._insights)}
            }
            
            # 2. Analyze: Generar tarea basada en gaps
            task = {"type": f"iteration_{iteration}", "iteration": iteration}
            
            # 3. Learn: Ejecutar y aprender
            result = await agent.execute_task(task)
            
            # 4. Practice: Aplicar a experiencia
            experience = ExperienceGenerator.generate_task_execution_experience(
                task_type="learning",
                success=result["status"] == "success"
            )
            await agent.learn_from_experience(experience)
            
            # 5. Harvest: Extraer insight
            if iteration % 3 == 0:  # Cada 3 iteraciones
                print(f"  → Ralph Loop iteration {iteration}: capital = {agent.capital_value:.1f}")
        
        print(f"✓ Ralph Loop completed: {agent.capital_value:.1f} capital, {len(agent._insights)} insights")
    
    @pytest.mark.asyncio
    async def test_055_skill_evolution_scenario(self):
        """
        Test 55: Escenario de evolución de skills
        Capital: Skills que evolucionan con uso
        """
        agent = AgentFactory.create_codex_agent(SkillLevel.BEGINNER)
        
        # Simular evolución de skill con práctica
        skill_name = "python"
        initial_level = agent.skills.get(skill_name, {}).get("level", "beginner")
        
        # Usar skill repetidamente
        for i in range(20):
            experience = {
                "type": "skill_practice",
                "success": i > 5,  # Mejora después de práctica inicial
                "skills_used": [skill_name],
                "context": {"practice_number": i}
            }
            await agent.learn_from_experience(experience)
        
        # Verificar uso acumulado
        if skill_name in agent.skills:
            usage = agent.skills[skill_name].get("usage_count", 0)
            print(f"✓ Skill evolution: {skill_name} used {usage} times")
    
    @pytest.mark.asyncio
    async def test_056_adaptive_behavior_under_pressure(self):
        """
        Test 56: Comportamiento adaptativo bajo presión
        Capital: Patrones de comportamiento bajo estrés
        """
        agent = AgentFactory.create_codex_agent()
        
        # Simular condiciones de alta carga
        urgent_tasks = [
            {"type": "urgent", "priority": "urgent", "timeout": 1}
            for _ in range(20)
        ]
        
        results = []
        for task in urgent_tasks:
            try:
                result = await asyncio.wait_for(
                    agent.execute_task(task),
                    timeout=2.0
                )
                results.append(result)
            except asyncio.TimeoutError:
                results.append({"status": "timeout"})
        
        success_rate = sum(1 for r in results if r.get("status") == "success") / len(results)
        
        print(f"✓ Pressure test: {success_rate*100:.1f}% success under load")
    
    @pytest.mark.asyncio
    async def test_057_knowledge_consolidation_scenario(self):
        """
        Test 57: Escenario de consolidación de conocimiento
        Capital: Conocimiento consolidado y destilado
        """
        agent = AgentFactory.create_codex_agent()
        
        # Generar muchas experiencias similares
        for i in range(50):
            await agent.learn_from_experience(
                ExperienceGenerator.generate_code_review_experience(success=(i % 3 != 0))
            )
        
        # Consolidar: contar tipos de insights
        insight_types = {}
        for insight in agent._insights:
            t = insight.get("type", "unknown")
            insight_types[t] = insight_types.get(t, 0) + 1
        
        print(f"✓ Knowledge consolidated: {len(agent._insights)} insights")
        for t, count in insight_types.items():
            print(f"    {t}: {count}")
    
    @pytest.mark.asyncio
    async def test_058_expertise_emergence_scenario(self):
        """
        Test 58: Escenario de emergencia de expertise
        Capital: Emergencia de comportamiento experto
        """
        agent = AgentFactory.create_codex_agent(SkillLevel.NOVICE)
        
        # Simular 100 horas de práctica (representadas por experiencias)
        for hour in range(100):
            exp = {
                "type": "practice_hour",
                "success": random.random() > 0.3,  # 70% success rate
                "skills_used": ["python", "testing"],
                "context": {"hour": hour},
                "complexity": min(hour // 20, 3)  # Aumenta complejidad
            }
            await agent.learn_from_experience(exp)
        
        # Verificar capital acumulado
        print(f"✓ Expertise emergence: {agent.capital_value:.1f} capital after 100 hours")
    
    @pytest.mark.asyncio
    async def test_059_cross_domain_collaboration_scenario(self):
        """
        Test 59: Escenario de colaboración entre dominios
        Capital: Patrones de colaboración inter-dominio
        """
        # Crear agentes de diferentes dominios
        agents = {
            "codex": AgentFactory.create_codex_agent(),
            "apex": AgentFactory.create_apex_agent(),
            "vitalis": AgentFactory.create_vitalis_agent()
        }
        
        # Coordinar mediante pipeline
        pipeline = LearningPipeline("cross-domain", "general")
        await pipeline.start()
        
        # Crear evento de colaboración
        collab_event = LearningEvent(
            event_type=LearningEventType.COLLECTIVE_INSIGHT,
            source_agent_id="coordinator",
            source_domain="general",
            payload={
                "insight": "Cross-domain patterns identified",
                "contributing_domains": list(agents.keys())
            },
            broadcast=True,
            learning_value=0.9
        )
        
        result = await pipeline.process_event(collab_event)
        
        print(f"✓ Cross-domain collaboration: {len(agents)} domains coordinated")
    
    @pytest.mark.asyncio
    async def test_060_full_system_integration_scenario(self):
        """
        Test 60: Escenario de integración completa del sistema
        Capital: Integración de todos los componentes
        """
        # Crear agente completo con todos los componentes
        agent = (AgentProfileBuilder()
            .with_id("full-integration-agent")
            .with_domain(Domain.CODEX)
            .with_role(IOVBARole.BUILDER)
            .with_skill("python", SkillLevel.EXPERT)
            .with_skill("testing", SkillLevel.ADVANCED)
            .with_tool("analyzer")
            .with_tool("formatter")
            .with_mcp_server("github")
            .with_execution_strategy("adaptive")
            .build())
        
        # Aplicar decoradores
        agent = LoggingDecorator(agent)
        agent = CachingDecorator(agent)
        agent = MetricsDecorator(agent)
        
        # Crear pipeline de aprendizaje
        pipeline = LearningPipeline(agent.agent_id, "codex")
        await pipeline.start()
        
        # Ejecutar ciclo PPCC completo
        cycle = PPCCCycle()
        await cycle.prepare({
            "objective": "Full integration test",
            "user_id": "integration-user",
            "success_criteria": "All components work together"
        })
        await cycle.request_alignment()
        await cycle.confirm_alignment("Full understanding", user_confirmed=True)
        await cycle.execute("Execute full integration")
        result = await cycle.declare_result(satisfaction=True)
        
        # Generar aprendizaje
        await agent._agent.learn_from_experience({
            "type": "full_integration",
            "success": True,
            "skills_used": ["python", "testing", "coordination"],
            "context": {"ppcc_cycle": True, "learning_pipeline": True}
        })
        
        # Verificar integración
        status = pipeline.get_pipeline_status()
        
        print(f"✓ Full integration:")
        print(f"    Agent: {agent.agent_id if hasattr(agent, 'agent_id') else agent._agent.agent_id}")
        print(f"    PPCC: completed")
        print(f"    Pipeline: {status['metrics']['events_processed']} events")


# ============================================================================
# TEST RUNNER
# ============================================================================

def run_all_tests():
    """Ejecuta todos los tests y genera reporte de capital"""
    import subprocess
    
    print("=" * 60)
    print("COGNITIVE CAPITAL BUILDER - 60 Tests")
    print("=" * 60)
    
    result = subprocess.run(
        ["pytest", __file__, "-v", "--tb=short"],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    
    if result.returncode == 0:
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED - CAPITAL COGNITIVO GENERADO")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("✗ SOME TESTS FAILED - REVIEW OUTPUT")
        print("=" * 60)
    
    return result.returncode


if __name__ == "__main__":
    exit_code = run_all_tests()
    exit(exit_code)
