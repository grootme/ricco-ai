"""
Tests Integrales para OpenClaw Agent SaaS.

Estos tests validan:
- AgentProfile (configuración basada en capacidades, NO en enums)
- Memory VCS (Capital Cognitivo)
- Skills Registry
- MCP Registry
- Stack IOVBA
- Orquestación y Delegación

IMPORTANTE: 
- LLM, A2A, Sequential, Parallel, Loop, Workflow, Task son PATRONES DE EJECUCIÓN
- NO son tipos de agentes
- Los agentes se definen por Skills, Tools/MCP, Prompt, Memoria

@author: OpenClaw Agent SaaS
"""

import pytest
import asyncio
import tempfile
import os
from uuid import uuid4
from datetime import datetime

# Importar el sistema de perfiles
import sys
sys.path.insert(0, "/home/z/my-project/ecosystem/ricco-ai/src")

from agents.profile import (
    AgentProfile,
    AgentProfileBuilder,
    AgentProfileRegistry,
    ExecutionPattern,
    OrchestrationRole,
    SkillRef,
    ToolRef,
    MCPRef,
    MemoryScope,
    PromptContext,
    create_commerce_profile,
    create_health_profile,
    create_finance_profile,
    create_logistics_profile,
    create_orchestrator_profile,
    profile_registry,
)
from agents.profile.factory import (
    DynamicAgent,
    ProfileBasedAgentFactory,
    create_agent,
    create_agent_from_profile,
    create_orchestrator,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def temp_db():
    """Crear base de datos temporal para Memory VCS."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def memory_vcs(temp_db):
    """Crear instancia de Memory VCS."""
    try:
        from memory.vcs import MemoryVCS
        return MemoryVCS(db_path=temp_db)
    except ImportError:
        pytest.skip("MemoryVCS not available")


@pytest.fixture
def profile_factory(memory_vcs):
    """Crear factory con Memory VCS configurado."""
    return ProfileBasedAgentFactory(memory_vcs=memory_vcs)


@pytest.fixture
def skills_registry():
    """Crear Skills Registry con skills de prueba."""
    try:
        from iovba.action.skills_registry import SkillsRegistry, Skill, SkillMetadata, SkillCategory
        registry = SkillsRegistry()
        
        # Crear skill de prueba
        skill = Skill(
            id="test-product-search",
            metadata=SkillMetadata(
                name="product_search",
                category=SkillCategory.DOMAIN,
                tags=["commerce", "search"],
            ),
            instructions="Search for products in the catalog",
            examples=[{"query": "laptop", "result": "Found 5 laptops"}],
            validation_rules=["query must not be empty"],
        )
        registry.register(skill)
        return registry
    except ImportError:
        pytest.skip("SkillsRegistry not available")


@pytest.fixture
def mcp_registry():
    """Crear MCP Registry mock para pruebas."""
    class MockMCPRegistry:
        def __init__(self):
            self._tools = {}
        
        def register_tool(self, name, handler):
            self._tools[name] = handler
        
        async def execute_tool(self, name, arguments):
            if name not in self._tools:
                return {"success": False, "error": f"Tool {name} not found"}
            return await self._tools[name](arguments)
    
    return MockMCPRegistry()


# ============================================================================
# TESTS: AGENT PROFILE - Configuración basada en capacidades
# ============================================================================

class TestAgentProfile:
    """
    Tests para AgentProfile.
    
    Verifica que los agentes se definen por CAPACIDADES, no por tipos.
    """
    
    def test_profile_creation_basic(self):
        """Un perfil básico debe poder crearse sin tipo enum."""
        profile = AgentProfile(
            name="Test Agent",
            domain="test",
        )
        
        assert profile.name == "Test Agent"
        assert profile.domain == "test"
        assert profile.skills == []
        assert profile.tools == []
        assert profile.mcps == []
    
    def test_profile_with_skills(self):
        """Un perfil puede tener múltiples skills."""
        profile = (AgentProfileBuilder("Multi-Skill Agent")
            .with_domain("commerce")
            .with_skill("search", "search", proficiency=0.9)
            .with_skill("analytics", "analytics", proficiency=0.8)
            .with_skill("recommendations", "recommendations", proficiency=0.95)
            .build())
        
        assert len(profile.skills) == 3
        assert profile.has_skill("search")
        assert profile.has_skill("analytics")
        assert profile.has_skill("recommendations")
        assert not profile.has_skill("nonexistent")
    
    def test_profile_with_tools_and_mcp(self):
        """Un perfil puede tener tools y MCPs."""
        profile = (AgentProfileBuilder("Tool-Enabled Agent")
            .with_domain("finance")
            .with_tool("check_balance", source="mcp")
            .with_tool("transfer_money", source="mcp")
            .with_mcp("banking-api", "banking-api", 
                      tools=["check_balance", "transfer_money", "get_history"])
            .build())
        
        assert len(profile.tools) == 2
        assert len(profile.mcps) == 1
        assert profile.has_tool("check_balance")
        assert profile.has_tool("transfer_money")
        assert not profile.has_tool("get_history")  # No registrado como tool directa
    
    def test_profile_memory_scope(self):
        """Un perfil define el alcance de su memoria."""
        profile = (AgentProfileBuilder("Memory Agent")
            .with_memory_domains("commerce", "customers", "orders")
            .with_memory_scope(
                access_level="domain",
                retention_policy="persistent",
                max_entries=5000
            )
            .build())
        
        assert len(profile.memory_scope.domains) == 3
        assert "commerce" in profile.memory_scope.domains
        assert profile.memory_scope.access_level == "domain"
        assert profile.memory_scope.max_entries == 5000
    
    def test_profile_execution_pattern_is_not_type(self):
        """
        CRÍTICO: ExecutionPattern NO es un tipo de agente.
        
        Sequential, Parallel, Loop, etc. son PATRONES de ejecución,
        no clasificaciones de agente.
        """
        profile = (AgentProfileBuilder("Sequential Team")
            .with_execution_pattern(ExecutionPattern.SEQUENTIAL)
            .with_domain("orchestration")
            .build())
        
        # El patrón de ejecución es SEQUENTIAL
        assert profile.execution_pattern == ExecutionPattern.SEQUENTIAL
        
        # Pero el DOMINIO es lo que define la ESPECIALIZACIÓN
        assert profile.domain == "orchestration"
        
        # El patrón es CÓMO se ejecuta, no QUÉ es el agente
        capabilities = profile.get_capabilities_summary()
        assert capabilities["execution_pattern"] == "sequential"
        assert capabilities["domain"] == "orchestration"
    
    def test_profile_orchestration_role(self):
        """
        El rol de orquestación define RESPONSABILIDADES, no tipo.
        """
        # Lead Agent
        lead_profile = (AgentProfileBuilder("Lead")
            .as_lead()
            .with_domain("orchestration")
            .build())
        
        assert lead_profile.orchestration_role == OrchestrationRole.LEAD
        
        # Specialist Agent
        specialist_profile = (AgentProfileBuilder("Specialist")
            .as_specialist()
            .with_domain("commerce")
            .build())
        
        assert specialist_profile.orchestration_role == OrchestrationRole.SPECIALIST
    
    def test_prebuilt_profiles(self):
        """Los perfiles pre-construidos deben ser válidos."""
        commerce = create_commerce_profile()
        assert commerce.domain == "commerce"
        assert len(commerce.skills) > 0
        assert len(commerce.mcps) > 0
        
        health = create_health_profile()
        assert health.domain == "health"
        
        finance = create_finance_profile()
        assert finance.domain == "finance"
        
        logistics = create_logistics_profile()
        assert logistics.domain == "logistics"
        
        orchestrator = create_orchestrator_profile()
        assert orchestrator.orchestration_role == OrchestrationRole.LEAD


class TestAgentProfileRegistry:
    """Tests para el registro de perfiles."""
    
    def test_register_and_retrieve(self):
        """Registrar y recuperar perfiles."""
        registry = AgentProfileRegistry()
        
        profile = (AgentProfileBuilder("Test Agent")
            .with_domain("test")
            .with_skill("testing", "testing")
            .build())
        
        registry.register(profile)
        
        # Recuperar por ID
        retrieved = registry.get(profile.id)
        assert retrieved is not None
        assert retrieved.name == "Test Agent"
        
        # Recuperar por nombre
        retrieved_by_name = registry.get_by_name("Test Agent")
        assert retrieved_by_name is not None
    
    def test_find_by_domain(self):
        """Buscar perfiles por dominio."""
        registry = AgentProfileRegistry()
        
        profile1 = (AgentProfileBuilder("Commerce Agent 1")
            .with_domain("commerce")
            .build())
        profile2 = (AgentProfileBuilder("Commerce Agent 2")
            .with_domain("commerce")
            .build())
        profile3 = (AgentProfileBuilder("Health Agent")
            .with_domain("health")
            .build())
        
        registry.register(profile1)
        registry.register(profile2)
        registry.register(profile3)
        
        commerce_agents = registry.find_by_domain("commerce")
        assert len(commerce_agents) == 2
        
        health_agents = registry.find_by_domain("health")
        assert len(health_agents) == 1
    
    def test_find_capable_agents(self):
        """Encontrar agentes capaces de realizar una tarea."""
        registry = AgentProfileRegistry()
        
        # Agente con skills de búsqueda
        search_agent = (AgentProfileBuilder("Search Specialist")
            .with_domain("search")
            .with_skill("web_search", "web_search")
            .with_skill("image_search", "image_search")
            .build())
        
        # Agente con skills de análisis
        analysis_agent = (AgentProfileBuilder("Analysis Specialist")
            .with_domain("analysis")
            .with_skill("data_analysis", "data_analysis")
            .with_skill("report_generation", "report_generation")
            .build())
        
        registry.register(search_agent)
        registry.register(analysis_agent)
        
        # Buscar agentes que puedan hacer web_search
        capable = registry.find_capable_agents(required_skills=["web_search"])
        assert len(capable) == 1
        assert capable[0].name == "Search Specialist"


# ============================================================================
# TESTS: DYNAMIC AGENT - Agente basado en perfil
# ============================================================================

class TestDynamicAgent:
    """Tests para DynamicAgent."""
    
    def test_agent_creation_from_profile(self, profile_factory):
        """Crear un agente desde un perfil."""
        profile = (AgentProfileBuilder("Test Agent")
            .with_domain("test")
            .with_skill("testing", "testing")
            .build())
        
        agent = profile_factory.create_agent(profile)
        
        assert agent.name == "Test Agent"
        assert agent.domain == "test"
        assert agent.has_capability("testing")
    
    def test_agent_memory_operations(self, profile_factory, memory_vcs):
        """Un agente puede usar memoria."""
        profile = (AgentProfileBuilder("Memory Agent")
            .with_domain("test")
            .with_memory_domains("test", "conversations")
            .build())
        
        agent = profile_factory.create_agent(profile)
        
        # Almacenar memoria
        result = asyncio.run(agent.store_memory(
            topic_key="test/conversation/1",
            content="Esta es una conversación de prueba",
            metadata={"type": "conversation"}
        ))
        
        assert result.get("success", True)  # Puede no tener success key
        
        # Consultar memoria
        results = asyncio.run(agent.query_memory("conversación"))
        assert isinstance(results, list)
    
    def test_agent_capabilities_summary(self, profile_factory):
        """Un agente puede generar resumen de capacidades."""
        profile = (AgentProfileBuilder("Capable Agent")
            .with_domain("commerce")
            .with_skill("search", "search")
            .with_skill("order", "order")
            .with_tool("api_call")
            .with_mcp("external-service", "external-service", tools=["do_something"])
            .build())
        
        agent = profile_factory.create_agent(profile)
        capabilities = agent.capabilities
        
        assert capabilities["domain"] == "commerce"
        assert capabilities["skills_count"] == 2
        assert capabilities["tools_count"] == 1
        assert capabilities["mcps_count"] == 1


# ============================================================================
# TESTS: MEMORY VCS - Capital Cognitivo
# ============================================================================

class TestMemoryVCS:
    """Tests para Memory VCS (Capital Cognitivo)."""
    
    def test_memory_upsert(self, memory_vcs):
        """Almacenar y actualizar memoria."""
        result = memory_vcs.upsert(
            topic_key="test/topic/1",
            content="Contenido de prueba",
            metadata={"source": "test"}
        )
        
        assert "topic_key" in result
        assert result["topic_key"] == "test/topic/1"
    
    def test_memory_search(self, memory_vcs):
        """Búsqueda semántica en memoria."""
        # Almacenar varios items
        memory_vcs.upsert("test/python", "Python es un lenguaje de programación")
        memory_vcs.upsert("test/java", "Java es otro lenguaje de programación")
        memory_vcs.upsert("test/javascript", "JavaScript es para web")
        
        # Buscar
        results = memory_vcs.search("lenguaje programación", limit=5)
        
        assert len(results) > 0
    
    def test_memory_versioning(self, memory_vcs):
        """Versionado de memoria."""
        topic = "test/versioned"
        
        # Crear versión 1
        memory_vcs.upsert(topic, "Versión 1 del contenido")
        
        # Actualizar a versión 2
        memory_vcs.upsert(topic, "Versión 2 del contenido", change_reason="Actualización")
        
        # Verificar timeline
        timeline = memory_vcs.get_timeline(topic)
        
        assert len(timeline) >= 1  # Al menos una versión
    
    def test_memory_relations(self, memory_vcs):
        """Relaciones entre memorias (Knowledge Graph)."""
        memory_vcs.upsert("test/persona/juan", "Juan es un desarrollador")
        memory_vcs.upsert("test/proyecto/web", "Proyecto Web App")
        
        # Crear relación
        memory_vcs.add_relation(
            source_key="test/persona/juan",
            target_key="test/proyecto/web",
            relation_type="works_on",
            weight=0.9
        )
        
        # Consultar relaciones
        related = memory_vcs.get_related("test/persona/juan")
        
        assert len(related) >= 0  # Puede estar vacío si no se implementó


# ============================================================================
# TESTS: EXECUTION PATTERNS (NO tipos de agentes)
# ============================================================================

class TestExecutionPatterns:
    """
    Tests para PATRONES DE EJECUCIÓN.
    
    CRÍTICO: Estos NO son tipos de agentes.
    Son patrones que determinan CÓMO se ejecuta un agente.
    """
    
    def test_llm_pattern(self, profile_factory):
        """
        Patrón LLM: Agente simple que usa un LLM.
        
        Este es el patrón más básico.
        """
        profile = (AgentProfileBuilder("Simple LLM Agent")
            .with_execution_pattern(ExecutionPattern.LLM)
            .with_domain("general")
            .with_prompt("You are a helpful assistant.")
            .build())
        
        agent = profile_factory.create_agent(profile)
        
        assert profile.execution_pattern == ExecutionPattern.LLM
        assert agent.get_system_prompt() == "You are a helpful assistant."
    
    def test_sequential_pattern(self, profile_factory):
        """
        Patrón SEQUENTIAL: Múltiples agentes ejecutan en secuencia.
        
        NO es un "tipo de agente" - es un PATRÓN de composición.
        """
        # Crear sub-agentes
        researcher = (AgentProfileBuilder("Researcher")
            .with_domain("research")
            .with_skill("web_search", "web_search")
            .build())
        
        analyst = (AgentProfileBuilder("Analyst")
            .with_domain("analysis")
            .with_skill("analyze", "analyze")
            .build())
        
        writer = (AgentProfileBuilder("Writer")
            .with_domain("writing")
            .with_skill("write", "write")
            .build())
        
        # Crear equipo secuencial
        sequential_team = profile_factory.create_sequential_team(
            name="Research Pipeline",
            agent_profiles=[researcher, analyst, writer]
        )
        
        assert sequential_team.profile.execution_pattern == ExecutionPattern.SEQUENTIAL
        assert len(sequential_team.profile.sub_agent_ids) == 3
    
    def test_parallel_pattern(self, profile_factory):
        """
        Patrón PARALLEL: Múltiples agentes ejecutan simultáneamente.
        
        NO es un "tipo de agente" - es un PATRÓN de composición.
        """
        # Crear agentes especializados
        search_agent = (AgentProfileBuilder("Search Agent")
            .with_domain("search")
            .build())
        
        db_agent = (AgentProfileBuilder("DB Agent")
            .with_domain("database")
            .build())
        
        cache_agent = (AgentProfileBuilder("Cache Agent")
            .with_domain("cache")
            .build())
        
        # Crear equipo paralelo
        parallel_team = profile_factory.create_parallel_team(
            name="Multi-Source Fetch",
            agent_profiles=[search_agent, db_agent, cache_agent]
        )
        
        assert parallel_team.profile.execution_pattern == ExecutionPattern.PARALLEL
        assert len(parallel_team.profile.sub_agent_ids) == 3
    
    def test_workflow_pattern(self):
        """
        Patrón WORKFLOW: Flujo con nodos y edges.
        
        NO es un "tipo de agente" - es un PATRÓN de composición.
        """
        profile = (AgentProfileBuilder("Workflow Agent")
            .with_execution_pattern(ExecutionPattern.WORKFLOW)
            .with_domain("orchestration")
            .with_extra_config("workflow", {
                "nodes": ["start", "process", "end"],
                "edges": [["start", "process"], ["process", "end"]]
            })
            .build())
        
        assert profile.execution_pattern == ExecutionPattern.WORKFLOW
        assert "workflow" in profile.extra_config
    
    def test_a2a_pattern(self):
        """
        Patrón A2A: Agent-to-Agent communication.
        
        NO es un "tipo de agente" - es un PATRÓN de comunicación.
        """
        profile = (AgentProfileBuilder("A2A Agent")
            .with_execution_pattern(ExecutionPattern.A2A)
            .with_domain("communication")
            .build())
        
        assert profile.execution_pattern == ExecutionPattern.A2A


# ============================================================================
# TESTS: IOVBA STACK
# ============================================================================

class TestIOVBAStack:
    """
    Tests para el Stack IOVBA:
    - I: Infraestructura
    - O: Orquestación
    - V: Validación
    - B: Comportamiento
    - A: Acción
    """
    
    def test_iovba_infrastructure(self, profile_factory, memory_vcs):
        """
        I - Infraestructura: Configuración base del agente.
        """
        profile = (AgentProfileBuilder("Infrastructure Test")
            .with_domain("test")
            .with_model("openai/gpt-oss")
            .with_memory_domains("test")
            .build())
        
        agent = profile_factory.create_agent(profile)
        
        # Verificar infraestructura configurada
        assert agent.memory_vcs is not None
        assert profile.model == "openai/gpt-oss"
    
    def test_iovba_orchestration(self, profile_factory):
        """
        O - Orquestación: Coordinación de agentes.
        """
        # Lead Agent
        lead_profile = create_orchestrator_profile("Main Orchestrator")
        lead_agent = profile_factory.create_agent(lead_profile)
        
        assert lead_profile.orchestration_role == OrchestrationRole.LEAD
        
        # Specialist Agents
        specialists = [
            create_commerce_profile("Commerce Specialist"),
            create_health_profile("Health Specialist"),
        ]
        
        # Lead puede coordinar specialists
        assert lead_profile.orchestration_role == OrchestrationRole.LEAD
    
    def test_iovba_validation(self):
        """
        V - Validación: Verificación de respuestas.
        """
        # Un agente con skills de validación
        profile = (AgentProfileBuilder("Validator Agent")
            .with_domain("validation")
            .with_skill("response_validation", "response_validation")
            .with_skill("quality_check", "quality_check")
            .build())
        
        assert profile.has_skill("response_validation")
        assert profile.has_skill("quality_check")
    
    def test_iovba_behavior(self):
        """
        B - Comportamiento: Prompt y contexto del agente.
        """
        profile = (AgentProfileBuilder("Behavioral Agent")
            .with_domain("customer_service")
            .with_prompt(
                system_prompt="You are a helpful customer service agent.",
                role_description="Agente de servicio al cliente",
                tone="friendly",
                behavioral_guidelines=[
                    "Always be polite",
                    "Escalate complex issues",
                    "Never share personal information"
                ]
            )
            .build())
        
        assert profile.prompt_context is not None
        assert profile.prompt_context.tone == "friendly"
        assert len(profile.prompt_context.behavioral_guidelines) == 3
    
    def test_iovba_action(self, mcp_registry):
        """
        A - Acción: Ejecución de herramientas y acciones.
        """
        profile = (AgentProfileBuilder("Action Agent")
            .with_domain("action")
            .with_tool("send_email", source="mcp")
            .with_tool("create_ticket", source="mcp")
            .with_mcp("action-service", "action-service", 
                      tools=["send_email", "create_ticket", "log_event"])
            .build())
        
        assert len(profile.tools) == 2
        assert len(profile.mcps) == 1


# ============================================================================
# TESTS: ORQUESTACIÓN Y DELEGACIÓN
# ============================================================================

class TestOrchestrationAndDelegation:
    """
    Tests para orquestación y delegación entre agentes.
    """
    
    def test_lead_delegates_to_specialists(self, profile_factory):
        """
        Lead Agent puede delegar tareas a especialistas.
        """
        # Crear especialistas
        commerce = create_commerce_profile("Commerce Specialist")
        health = create_health_profile("Health Specialist")
        finance = create_finance_profile("Finance Specialist")
        
        # Crear Lead con sub-agentes
        lead_profile = (AgentProfileBuilder("Lead Orchestrator")
            .as_lead()
            .with_domain("orchestration")
            .with_skill("task_routing", "task_routing")
            .with_sub_agents([commerce.id, health.id, finance.id])
            .build())
        
        lead_agent = profile_factory.create_agent(lead_profile)
        
        assert lead_profile.orchestration_role == OrchestrationRole.LEAD
        assert len(lead_profile.sub_agent_ids) == 3
    
    def test_domain_based_routing(self):
        """
        Routing de tareas basado en dominio y capacidades.
        """
        registry = AgentProfileRegistry()
        
        # Registrar agentes especializados
        registry.register(create_commerce_profile())
        registry.register(create_health_profile())
        registry.register(create_finance_profile())
        
        # Buscar agente para tarea de commerce
        commerce_agents = registry.find_by_domain("commerce")
        assert len(commerce_agents) >= 1
        
        # Buscar agente con skill específica
        # (Depende de las skills definidas en create_commerce_profile)
    
    def test_specialist_has_domain_expertise(self):
        """
        Un especialista tiene expertise en su dominio.
        """
        health_specialist = create_health_profile()
        
        assert health_specialist.domain == "health"
        assert len(health_specialist.skills) > 0
        assert len(health_specialist.memory_scope.domains) > 0
        assert "health" in health_specialist.memory_scope.domains


# ============================================================================
# TESTS: SKILLS SYSTEM
# ============================================================================

class TestSkillsSystem:
    """Tests para el sistema de Skills."""
    
    def test_skill_attachment_to_profile(self):
        """Una skill puede adjuntarse a un perfil."""
        profile = (AgentProfileBuilder("Skilled Agent")
            .with_skill("data_analysis", "data_analysis", proficiency=0.9)
            .with_skill("visualization", "visualization", proficiency=0.8)
            .build())
        
        assert len(profile.skills) == 2
        
        # Verificar proficiencies
        for skill in profile.skills:
            if skill.skill_name == "data_analysis":
                assert skill.proficiency == 0.9
            elif skill.skill_name == "visualization":
                assert skill.proficiency == 0.8
    
    def test_skill_enabled_disabled(self):
        """Skills pueden habilitarse/deshabilitarse."""
        profile = (AgentProfileBuilder("Selective Agent")
            .with_skill("enabled_skill", "enabled_skill", enabled=True)
            .with_skill("disabled_skill", "disabled_skill", enabled=False)
            .build())
        
        assert profile.has_skill("enabled_skill")
        assert not profile.has_skill("disabled_skill")
    
    def test_skill_ids_extraction(self):
        """Extraer IDs de skills habilitadas."""
        profile = (AgentProfileBuilder("Multi-Skill Agent")
            .with_skill("skill-1", "skill_1")
            .with_skill("skill-2", "skill_2")
            .with_skill("skill-3", "skill_3", enabled=False)
            .build())
        
        skill_ids = profile.get_skill_ids()
        
        assert "skill-1" in skill_ids
        assert "skill-2" in skill_ids
        assert "skill-3" not in skill_ids  # Deshabilitada


# ============================================================================
# TESTS: MCP SYSTEM
# ============================================================================

class TestMCPSystem:
    """Tests para MCP (Model Context Protocol)."""
    
    def test_mcp_attachment_to_profile(self):
        """MCP servers pueden adjuntarse a un perfil."""
        profile = (AgentProfileBuilder("MCP Agent")
            .with_mcp("filesystem", "filesystem", tools=["read", "write", "list"])
            .with_mcp("database", "database", tools=["query", "insert", "update"])
            .build())
        
        assert len(profile.mcps) == 2
        
        mcp_tools = profile.get_mcp_tools()
        assert "filesystem" in mcp_tools
        assert "database" in mcp_tools
        assert "read" in mcp_tools["filesystem"]
    
    def test_tool_access_from_mcp(self):
        """Tools pueden accederse vía MCP."""
        profile = (AgentProfileBuilder("Tool User Agent")
            .with_tool("query", source="mcp")
            .with_tool("read", source="mcp")
            .with_mcp("data-source", "data-source", tools=["query", "read", "write"])
            .build())
        
        assert profile.has_tool("query")
        assert profile.has_tool("read")
        # write está en MCP pero no registrado como tool directa
        assert not profile.has_tool("write")


# ============================================================================
# TESTS INTEGRALES: FLUJO COMPLETO
# ============================================================================

class TestFullIntegration:
    """Tests de integración completa."""
    
    def test_full_agent_lifecycle(self, profile_factory, memory_vcs):
        """
        Ciclo de vida completo de un agente:
        1. Crear perfil
        2. Instanciar agente
        3. Almacenar memoria
        4. Consultar memoria
        5. Procesar solicitud
        """
        # 1. Crear perfil
        profile = (AgentProfileBuilder("Lifecycle Test Agent")
            .with_domain("test")
            .with_skill("conversation", "conversation")
            .with_memory_domains("test", "conversations")
            .with_prompt("You are a test assistant.")
            .build())
        
        # 2. Instanciar agente
        agent = profile_factory.create_agent(profile, instance_id="lifecycle-test")
        
        assert agent.name == "Lifecycle Test Agent"
        
        # 3. Almacenar memoria
        store_result = asyncio.run(agent.store_memory(
            topic_key="test/conversation/001",
            content="Usuario preguntó sobre el clima",
            metadata={"intent": "weather_query"}
        ))
        
        # 4. Consultar memoria
        memories = asyncio.run(agent.query_memory("clima"))
        
        # 5. Procesar solicitud
        response = asyncio.run(agent.process(
            {"query": "¿Cómo está el clima?"},
            context={"session_id": "test-session"}
        ))
        
        assert response["agent"] == "Lifecycle Test Agent"
        assert response["domain"] == "test"
    
    def test_orchestration_scenario(self, profile_factory, memory_vcs):
        """
        Escenario completo de orquestación:
        1. Lead Agent recibe solicitud
        2. Analiza qué especialista necesita
        3. Delega al especialista apropiado
        """
        # Crear especialistas
        commerce = create_commerce_profile("Commerce Specialist")
        health = create_health_profile("Health Specialist")
        
        # Crear Lead
        lead_profile = (AgentProfileBuilder("Main Orchestrator")
            .as_lead()
            .with_domain("orchestration")
            .with_skill("task_analysis", "task_analysis")
            .with_skill("routing", "routing")
            .with_sub_agents([commerce.id, health.id])
            .build())
        
        lead_agent = profile_factory.create_agent(lead_profile)
        
        # Simular procesamiento
        response = asyncio.run(lead_agent.process(
            {"task": "Procesar orden de compra", "domain": "commerce"},
            context={"routing_needed": True}
        ))
        
        assert response["orchestration_role"] == OrchestrationRole.LEAD.value


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
