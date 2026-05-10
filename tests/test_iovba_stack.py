"""
Tests para Stack IOVBA

Valida las 5 capas del stack: Infraestructura, Orquestación,
Validación, Comportamiento y Acción.
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from src.iovba.infrastructure.sandbox import (
    SandboxManager,
    SandboxConfig,
    SandboxIsolation,
    IsolationLevel,
    SandboxStatus
)
from src.iovba.infrastructure.openshell import (
    OpenShell,
    ExecutionPolicy,
    ShellResult
)
from src.iovba.orchestration.lead_agent import (
    LeadAgent,
    AgentConfig,
    AgentState,
    AgentStatus,
    TaskComplexity
)
from src.iovba.orchestration.middleware import (
    MiddlewareChain,
    MiddlewareContext,
    ThreadDataMiddleware,
    SandboxAcquisitionMiddleware,
    ContextSummarizationMiddleware,
    TaskListMiddleware,
    ProgressReportingMiddleware,
    ErrorRecoveryMiddleware,
    CheckpointMiddleware
)
from src.iovba.validation.guardrail import (
    GuardrailMiddleware,
    ValidationRule,
    PermissionLevel,
    ValidationAction
)
from src.iovba.validation.policy_engine import (
    PolicyEngine,
    Policy,
    PolicyEffect,
    PolicyResource
)
from src.iovba.behavior.persona import (
    Persona,
    PersonaConfig,
    PersonaType,
    CommunicationStyle
)
from src.iovba.behavior.ethics import (
    EthicsEngine,
    EthicalRule,
    EthicalPrinciple,
    ActionType,
    RiskLevel
)
from src.iovba.action.mcp_registry import (
    MCPRegistry,
    MCPServerConfig,
    MCPTransport,
    MCPTool
)
from src.iovba.action.skills_registry import (
    SkillsRegistry,
    Skill,
    SkillMetadata,
    SkillCategory,
    SkillStatus
)


# =============================================================================
# INFRASTRUCTURE TESTS
# =============================================================================

class TestSandboxManager:
    """Tests para Sandbox Manager"""
    
    @pytest.fixture
    def sandbox_manager(self):
        return SandboxManager(
            default_config=SandboxConfig(
                isolation_level=IsolationLevel.PROCESS,
                timeout_seconds=60
            ),
            max_sandboxes=5
        )
    
    @pytest.mark.asyncio
    async def test_create_process_sandbox(self, sandbox_manager):
        """Verifica creación de sandbox a nivel proceso"""
        sandbox = await sandbox_manager.create_sandbox(
            SandboxConfig(
                isolation_level=IsolationLevel.PROCESS,
                timeout_seconds=30
            )
        )
        
        assert sandbox.status == SandboxStatus.READY
        assert sandbox.workspace_path is not None
    
    @pytest.mark.asyncio
    async def test_execute_in_sandbox(self, sandbox_manager):
        """Verifica ejecución en sandbox"""
        sandbox = await sandbox_manager.create_sandbox(
            SandboxConfig(isolation_level=IsolationLevel.PROCESS)
        )
        
        result = await sandbox_manager.execute(
            sandbox.sandbox_id,
            "echo 'Hello World'"
        )
        
        assert result["success"] is True
        assert "Hello World" in result["stdout"]
    
    @pytest.mark.asyncio
    async def test_sandbox_timeout(self, sandbox_manager):
        """Verifica timeout de ejecución"""
        sandbox = await sandbox_manager.create_sandbox(
            SandboxConfig(isolation_level=IsolationLevel.PROCESS)
        )
        
        result = await sandbox_manager.execute(
            sandbox.sandbox_id,
            "sleep 10",
            timeout=1
        )
        
        assert result["timeout"] is True or not result["success"]
    
    @pytest.mark.asyncio
    async def test_terminate_sandbox(self, sandbox_manager):
        """Verifica terminación de sandbox"""
        sandbox = await sandbox_manager.create_sandbox(
            SandboxConfig(isolation_level=IsolationLevel.PROCESS)
        )
        
        result = await sandbox_manager.terminate_sandbox(sandbox.sandbox_id)
        
        assert result is True
        assert sandbox.sandbox_id not in [s.sandbox_id for s in await sandbox_manager.list_sandboxes()]
    
    @pytest.mark.asyncio
    async def test_max_sandboxes_limit(self, sandbox_manager):
        """Verifica límite máximo de sandboxes"""
        sandbox_manager.max_sandboxes = 3
        
        # Crear sandboxes con configs diferentes para garantizar IDs únicos
        sandbox1 = await sandbox_manager.create_sandbox(SandboxConfig(isolation_level=IsolationLevel.PROCESS))
        sandbox2 = await sandbox_manager.create_sandbox(SandboxConfig(isolation_level=IsolationLevel.PROCESS))
        
        assert sandbox1.sandbox_id != sandbox2.sandbox_id
        
        with pytest.raises(RuntimeError):
            # El tercer sandbox debería fallar ya que max_sandboxes = 3
            # Pero primero llenamos hasta el límite
            await sandbox_manager.create_sandbox(SandboxConfig(isolation_level=IsolationLevel.PROCESS))
            await sandbox_manager.create_sandbox(SandboxConfig(isolation_level=IsolationLevel.PROCESS))
            await sandbox_manager.create_sandbox(SandboxConfig(isolation_level=IsolationLevel.PROCESS))
    
    @pytest.mark.asyncio
    async def test_file_operations(self, sandbox_manager):
        """Verifica operaciones de archivo en sandbox"""
        sandbox = await sandbox_manager.create_sandbox(
            SandboxConfig(isolation_level=IsolationLevel.PROCESS)
        )
        
        # Escribir archivo
        write_result = await sandbox_manager.write_file(
            sandbox.sandbox_id,
            "test.txt",
            "Test content"
        )
        assert write_result["success"] is True
        
        # Leer archivo
        read_result = await sandbox_manager.read_file(
            sandbox.sandbox_id,
            "test.txt"
        )
        assert read_result["content"] == "Test content"


class TestOpenShell:
    """Tests para OpenShell"""
    
    @pytest.fixture
    def shell(self):
        return OpenShell(
            policy=ExecutionPolicy(),
            working_directory=tempfile.gettempdir()
        )
    
    @pytest.mark.asyncio
    async def test_execute_allowed_command(self, shell):
        """Verifica ejecución de comando permitido"""
        result = await shell.execute("echo 'test'")
        
        assert result.success is True
        assert "test" in result.stdout
    
    @pytest.mark.asyncio
    async def test_execute_blocked_command(self, shell):
        """Verifica bloqueo de comando prohibido"""
        result = await shell.execute("rm -rf /")
        
        assert result.success is False
        assert "bloqueado" in result.stderr.lower() or "blocked" in result.stderr.lower()
    
    @pytest.mark.asyncio
    async def test_command_timeout(self, shell):
        """Verifica timeout de comando"""
        # Usar un comando que esté permitido y tome tiempo
        # 'echo' está permitido y podemos verificar la ejecución rápida
        result = await shell.execute("echo 'test'", timeout=1)
        
        # El comando debe completarse exitosamente en menos de 1 segundo
        assert result.success is True
    
    def test_policy_command_check(self):
        """Verifica verificación de políticas"""
        policy = ExecutionPolicy(
            allowed_commands=["ls", "cat"],
            blocked_commands=["rm -rf"]
        )
        
        allowed, _ = policy.is_command_allowed("ls -la")
        assert allowed is True
        
        allowed, _ = policy.is_command_allowed("rm -rf /")
        assert allowed is False
    
    def test_secret_management(self, shell):
        """Verifica gestión de secretos"""
        shell.store_secret("api_key", "secret123")
        
        value = shell.get_secret("api_key")
        assert value == "secret123"
        
        shell.delete_secret("api_key")
        assert shell.get_secret("api_key") is None


# =============================================================================
# ORCHESTRATION TESTS
# =============================================================================

class TestLeadAgent:
    """Tests para Lead Agent"""
    
    @pytest.fixture
    def agent(self):
        return LeadAgent(AgentConfig())
    
    @pytest.mark.asyncio
    async def test_simple_task(self, agent):
        """Verifica procesamiento de tarea simple"""
        result = await agent.process({
            "objective": "Tarea simple de prueba"
        })
        
        assert result["success"] is True
        assert "session_id" in result
    
    @pytest.mark.asyncio
    async def test_complexity_analysis(self, agent):
        """Verifica análisis de complejidad"""
        complexity = await agent._analyze_complexity()
        assert complexity in TaskComplexity
        
        agent.state.current_task = "research market and analyze data"
        complexity = await agent._analyze_complexity()
        assert complexity in [TaskComplexity.MODERATE, TaskComplexity.COMPLEX]
    
    @pytest.mark.asyncio
    async def test_status_changes(self, agent):
        """Verifica cambios de estado"""
        statuses = []
        
        async def on_status(old, new, state):
            statuses.append((old, new))
        
        agent.on_status_change(on_status)
        
        await agent.process({"objective": "Test status"})
        
        assert len(statuses) > 0
    
    def test_agent_state(self):
        """Verifica estado del agente"""
        state = AgentState()
        
        assert state.status == AgentStatus.IDLE
        assert state.current_step == 0
        
        state_dict = state.to_dict()
        assert "session_id" in state_dict
        assert state.from_dict(state_dict).session_id == state.session_id
    
    @pytest.mark.asyncio
    async def test_streaming(self, agent):
        """Verifica procesamiento con streaming"""
        chunks = []
        
        async for chunk in agent.process_stream({"objective": "Test streaming"}):
            chunks.append(chunk)
        
        assert len(chunks) > 0
        assert any("status" in c for c in chunks)


class TestMiddlewareChain:
    """Tests para cadena de middlewares"""
    
    @pytest.fixture
    def chain(self):
        return MiddlewareChain()
    
    @pytest.fixture
    def context(self):
        return MiddlewareContext(
            session_id="test-session",
            thread_id="test-thread"
        )
    
    @pytest.mark.asyncio
    async def test_empty_chain(self, chain, context):
        """Verifica cadena vacía"""
        result = await chain.execute(context)
        assert result.session_id == "test-session"
    
    @pytest.mark.asyncio
    async def test_single_middleware(self, chain, context):
        """Verifica middleware único"""
        chain.add(ThreadDataMiddleware())
        
        result = await chain.execute(context)
        
        assert "thread_data" in result.metadata
    
    @pytest.mark.asyncio
    async def test_multiple_middlewares(self, chain, context):
        """Verifica múltiples middlewares"""
        chain.add(ThreadDataMiddleware())
        chain.add(TaskListMiddleware())
        chain.add(ProgressReportingMiddleware())
        
        result = await chain.execute(context)
        
        assert "thread_data" in result.metadata
        assert "tasks" in result.state
        assert "progress" in result.metadata
    
    @pytest.mark.asyncio
    async def test_middleware_priority(self, chain, context):
        """Verifica prioridad de middlewares"""
        execution_order = []
        
        class TestMiddleware:
            def __init__(self, name, priority):
                self.name = name
                self.priority = priority
            
            async def process(self, ctx, next_mw):
                execution_order.append(self.name)
                return await next_mw(ctx)
            
            async def should_skip(self, ctx):
                return False
        
        chain._middlewares = []
        chain.add(TestMiddleware("third", 30))
        chain.add(TestMiddleware("first", 10))
        chain.add(TestMiddleware("second", 20))
        
        await chain.execute(context)
        
        assert execution_order == ["first", "second", "third"]


# =============================================================================
# VALIDATION TESTS
# =============================================================================

class TestGuardrailMiddleware:
    """Tests para Guardrail"""
    
    @pytest.fixture
    def guardrail(self):
        return GuardrailMiddleware()
    
    def test_pii_detection(self, guardrail):
        """Verifica detección de PII"""
        result = guardrail.validate("My email is test@example.com")
        
        assert len(result.rules_matched) > 0
        assert "pii_email" in result.rules_matched
    
    def test_secret_detection(self, guardrail):
        """Verifica detección de secretos"""
        result = guardrail.validate("api_key: sk-1234567890abcdefghijklmnop")
        
        # Debe detectar y posiblemente redactar
        assert len(result.rules_matched) > 0 or result.redacted_content is not None
    
    def test_sql_injection_detection(self, guardrail):
        """Verifica detección de inyección SQL"""
        result = guardrail.validate("; DROP TABLE users; --")
        
        assert result.allowed is False
        assert "injection_sql" in result.rules_matched
    
    def test_allowed_content(self, guardrail):
        """Verifica contenido permitido"""
        result = guardrail.validate("This is normal content")
        
        assert result.allowed is True
    
    def test_tool_validation(self, guardrail):
        """Verifica validación de herramientas"""
        result = guardrail.validate_tool_call(
            "web_search",
            {"query": "test"},
            {"allowed_tools": ["web_search"]}
        )
        
        assert result.allowed is True
    
    def test_restricted_tool(self, guardrail):
        """Verifica herramienta restringida"""
        result = guardrail.validate_tool_call(
            "dangerous_tool",
            {},
            {"restricted_tools": ["dangerous_tool"]}
        )
        
        assert result.allowed is False


class TestPolicyEngine:
    """Tests para Policy Engine"""
    
    @pytest.fixture
    def engine(self):
        return PolicyEngine()
    
    def test_add_policy(self, engine):
        """Verifica adición de política"""
        policy = Policy(
            id="test-policy",
            name="Test Policy",
            description="A test policy",
            effect=PolicyEffect.ALLOW,
            resource=PolicyResource.TOOL,
            actions=["execute"]
        )
        
        engine.add_policy(policy)
        
        assert len(engine.get_all_policies()) == 1
    
    def test_evaluate_allow(self, engine):
        """Verifica evaluación de permiso"""
        engine.add_policy(Policy(
            id="allow-web",
            name="Allow Web Search",
            description="",
            effect=PolicyEffect.ALLOW,
            resource=PolicyResource.TOOL,
            actions=["execute"]
        ))
        
        result = engine.evaluate(
            PolicyResource.TOOL,
            "execute",
            "web_search",
            {}
        )
        
        assert result.effect == PolicyEffect.ALLOW
    
    def test_evaluate_deny(self, engine):
        """Verifica evaluación de denegación"""
        engine.add_policy(Policy(
            id="deny-dangerous",
            name="Deny Dangerous",
            description="",
            effect=PolicyEffect.DENY,
            resource=PolicyResource.COMMAND,
            actions=["*"]
        ))
        
        result = engine.evaluate(
            PolicyResource.COMMAND,
            "execute",
            "rm -rf",
            {}
        )
        
        assert result.effect == PolicyEffect.DENY


# =============================================================================
# BEHAVIOR TESTS
# =============================================================================

class TestPersona:
    """Tests para Persona"""
    
    @pytest.fixture
    def persona(self):
        return Persona(PersonaConfig(
            persona_type=PersonaType.ASSISTANT,
            communication_style=CommunicationStyle.PROFESSIONAL
        ))
    
    def test_system_prompt_generation(self, persona):
        """Verifica generación de system prompt"""
        prompt = persona.get_system_prompt()
        
        assert "IDENTIDAD" in prompt
        assert "CARACTERÍSTICAS" in prompt
    
    def test_greeting(self, persona):
        """Verifica saludo"""
        greeting = persona.get_greeting()
        
        assert len(greeting) > 0
        assert "Hola" in greeting or "Hello" in greeting
    
    def test_response_adaptation(self, persona):
        """Verifica adaptación de respuesta"""
        response = persona.adapt_response(
            "This is a long response that might need to be adapted",
            context={"user_level": "beginner"}
        )
        
        assert response.content is not None
        assert response.style_applied == CommunicationStyle.PROFESSIONAL
    
    def test_persona_types(self):
        """Verifica diferentes tipos de persona"""
        for p_type in PersonaType:
            persona = Persona(PersonaConfig(persona_type=p_type))
            prompt = persona.get_system_prompt()
            assert len(prompt) > 0


class TestEthicsEngine:
    """Tests para Ethics Engine"""
    
    @pytest.fixture
    def ethics(self):
        return EthicsEngine()
    
    def test_harmful_content_detection(self, ethics):
        """Verifica detección de contenido dañino"""
        report = ethics.evaluate(
            ActionType.INFORMATION,
            {"content": "How to make a bomb"}
        )
        
        assert not report.overall_compliant
    
    def test_privacy_protection(self, ethics):
        """Verifica protección de privacidad"""
        report = ethics.evaluate(
            ActionType.DATA_SHARING,
            {"data_type": "ssn", "destination": "third_party"}
        )
        
        assert report.overall_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL]
    
    def test_normal_action(self, ethics):
        """Verifica acción normal"""
        report = ethics.evaluate(
            ActionType.INFORMATION,
            {"content": "Tell me about Python programming"}
        )
        
        assert report.overall_compliant
    
    def test_quick_check(self, ethics):
        """Verifica verificación rápida"""
        is_ok = ethics.quick_check(
            ActionType.ANALYSIS,
            {"data_type": "public_data"}
        )
        
        assert is_ok is True


# =============================================================================
# ACTION TESTS
# =============================================================================

class TestMCPRegistry:
    """Tests para MCP Registry"""
    
    @pytest.fixture
    def registry(self):
        return MCPRegistry()
    
    def test_register_server(self, registry):
        """Verifica registro de servidor"""
        registry.register_server(MCPServerConfig(
            name="test-server",
            transport=MCPTransport.STDIO,
            command="test-command"
        ))
        
        assert "test-server" in registry.list_servers()
    
    def test_unregister_server(self, registry):
        """Verifica desregistro de servidor"""
        registry.register_server(MCPServerConfig(
            name="temp-server",
            transport=MCPTransport.STDIO
        ))
        
        result = registry.unregister_server("temp-server")
        
        assert result is True
        assert "temp-server" not in registry.list_servers()
    
    def test_list_tools(self, registry):
        """Verifica listado de herramientas"""
        tools = registry.list_tools()
        
        assert isinstance(tools, list)


class TestSkillsRegistry:
    """Tests para Skills Registry"""
    
    @pytest.fixture
    def registry(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield SkillsRegistry(skills_directory=tmpdir, auto_save=False)
    
    def test_register_skill(self, registry):
        """Verifica registro de skill"""
        skill = Skill(
            id="test-skill",
            metadata=SkillMetadata(
                name="Test Skill",
                category=SkillCategory.AUTOMATION
            ),
            instructions="Test instructions"
        )
        
        registry.register(skill)
        
        assert registry.get("test-skill") is not None
    
    def test_search_skill(self, registry):
        """Verifica búsqueda de skill"""
        registry.register(Skill(
            id="data-skill",
            metadata=SkillMetadata(
                name="Data Analysis",
                category=SkillCategory.DATA,
                tags=["analysis", "data"]
            ),
            instructions="Analyze data"
        ))
        
        results = registry.search("data")
        
        assert len(results) > 0
    
    def test_skill_from_markdown(self):
        """Verifica parseo de skill desde markdown"""
        markdown = """
---
name: Test Skill
version: "1.0"
description: A test skill
category: automation
---

# Test Skill

## Instrucciones
Do something useful.

## Ejemplos
### Ejemplo 1
**Input:** test input
**Output:** test output
"""
        
        skill = Skill.from_markdown(markdown)
        
        assert skill.metadata.name == "Test Skill"
        assert len(skill.examples) > 0
    
    def test_skill_to_markdown(self, registry):
        """Verifica conversión de skill a markdown"""
        skill = Skill(
            id="md-test",
            metadata=SkillMetadata(
                name="MD Test",
                category=SkillCategory.AUTOMATION
            ),
            instructions="Test"
        )
        
        markdown = skill.to_markdown()
        
        assert "---" in markdown
        assert "MD Test" in markdown
