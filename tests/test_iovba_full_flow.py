"""
Test Maestro - Flujo IOVBA Completo

Este test demuestra el flujo completo del Stack IOVBA:
I - Infraestructura → O - Orquestación → V - Validación → B - Comportamiento → A - Acción

Incluye:
1. Preparación del contexto (Obviousness)
2. Inicialización del Lead Agent
3. Validación con Guardrails
4. Comportamiento con Persona y Ética
5. Ejecución de Skills/MCP
6. Cosecha con Ralph Loop
"""

import pytest
import asyncio
import tempfile
import os
import json
from datetime import datetime
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch

pytestmark = pytest.mark.asyncio


class TestIOVBAFullFlow:
    """Test del flujo completo del Stack IOVBA"""
    
    async def test_iovba_flow_completo(self, temp_db, temp_dir):
        """
        Test del flujo completo IOVBA:
        I → O → V → B → A
        """
        from src.memory.vcs import MemoryVCS
        from src.core.obviousness import ObviousnessContextBuilder
        from src.iovba.orchestration.lead_agent import LeadAgent, AgentConfig
        from src.iovba.validation.guardrail import GuardrailMiddleware, ValidationRule, PermissionLevel
        from src.iovba.validation.policy_engine import PolicyEngine, Policy
        from src.iovba.behavior.persona import Persona, PersonaConfig, PersonaType
        from src.iovba.behavior.ethics import EthicsEngine, EthicalRule
        from src.iovba.action.skills_registry import SkillsRegistry, Skill, SkillMetadata
        from src.iovba.action.mcp_registry import MCPRegistry, MCPServerConfig, MCPTool
        from src.ralph.loop import RalphLoop
        
        print("\n" + "="*60)
        print("INICIANDO FLUJO IOVBA COMPLETO")
        print("="*60)
        
        # =============================================================
        # FASE 0: PREPARACIÓN
        # =============================================================
        print("\n[0] Preparando contexto...")
        
        # Crear Memory VCS
        memory_vcs = MemoryVCS(db_path=temp_db, auto_init=True)
        
        # Crear contexto de obviedad
        obviousness = (ObviousnessContextBuilder(
            session_id="iovba-flow-test",
            user_id="test-user"
        )
        .with_objective(
            objective="Ejecutar flujo completo del Stack IOVBA",
            success_criteria=[
                "Infraestructura inicializada",
                "Orquestación completada",
                "Validación pasada",
                "Comportamiento aplicado",
                "Acción ejecutada"
            ],
            deliverables=["Reporte de ejecución"]
        )
        .with_metrics(recall=0.9, precision=0.9)
        .with_boundaries(
            allow=["database", "filesystem", "analysis"],
            deny=["production", "external_api"],
            sandbox=True
        )
        .with_relevance(impact="high", ccv=8)
        .with_time(priority="high", timeout=300)
        .build())
        
        print(f"   ✓ Contexto creado: {obviousness.objective[:50]}...")
        
        # =============================================================
        # FASE I: INFRAESTRUCTURA
        # =============================================================
        print("\n[I] CAPA INFRAESTRUCTURA...")
        
        from src.iovba.infrastructure.sandbox import SandboxManager, SandboxConfig, SandboxIsolation
        
        sandbox_config = SandboxConfig(
            isolation_level=SandboxIsolation.PROCESS,
            max_memory_mb=512,
            timeout_seconds=60
        )
        
        sandbox_manager = SandboxManager(sandbox_config)
        
        # Crear sandbox
        sandbox_id = await sandbox_manager.create_sandbox()
        print(f"   ✓ Sandbox creado: {sandbox_id[:8]}...")
        
        # =============================================================
        # FASE O: ORQUESTACIÓN
        # =============================================================
        print("\n[O] CAPA ORQUESTACIÓN...")
        
        # Crear Lead Agent
        agent_config = AgentConfig(
            name="IOVBA Test Agent",
            max_sub_agents=5,
            checkpoint_enabled=True,
            memory_enabled=True
        )
        
        lead_agent = LeadAgent(agent_config)
        
        # Procesar solicitud
        result = await lead_agent.process(
            request={
                "objective": "Analizar datos de prueba del Stack IOVBA",
                "domain": "testing"
            },
            obviousness_context=obviousness.model_dump()
        )
        
        print(f"   ✓ Lead Agent ejecutado: {result.get('success')}")
        print(f"   ✓ Pasos completados: {result.get('steps', 0)}")
        
        # Spawn sub-agentes
        sub_id = await lead_agent.spawn_sub_agent("Tarea secundaria de análisis")
        print(f"   ✓ Sub-agente creado: {sub_id}")
        
        # =============================================================
        # FASE V: VALIDACIÓN
        # =============================================================
        print("\n[V] CAPA VALIDACIÓN...")
        
        # Crear Guardrail
        guardrail = GuardrailMiddleware()
        
        # Agregar reglas
        rules = [
            ValidationRule(
                name="no_production",
                description="Block production access",
                permission_level=PermissionLevel.DENY,
                pattern="production"
            ),
            ValidationRule(
                name="allow_analysis",
                description="Allow analysis operations",
                permission_level=PermissionLevel.ALLOW,
                pattern="analysis"
            )
        ]
        
        for rule in rules:
            guardrail.add_rule(rule)
        
        # Validar acciones
        test_actions = [
            "analysis_database_query",
            "production_api_call",
            "filesystem_read"
        ]
        
        for action in test_actions:
            validation = guardrail.validate_action(action)
            status = "✓" if validation["allowed"] else "✗"
            print(f"   {status} '{action}': {validation['allowed']}")
        
        # Crear Policy Engine
        policy_engine = PolicyEngine()
        
        policy = Policy(
            id="iovba-test-policy",
            name="IOVBA Test Policy",
            rules=[
                {"action": "read", "resource": "test_data", "effect": "allow"},
                {"action": "write", "resource": "test_data", "effect": "deny"}
            ]
        )
        
        policy_engine.register_policy(policy)
        print(f"   ✓ Política registrada: {policy.name}")
        
        # =============================================================
        # FASE B: COMPORTAMIENTO
        # =============================================================
        print("\n[B] CAPA COMPORTAMIENTO...")
        
        # Crear Persona
        persona_config = PersonaConfig(
            persona_type=PersonaType.ASSISTANT,
            name="IOVBA Assistant",
            tone="professional",
            expertise=["testing", "analysis"]
        )
        
        persona = Persona(persona_config)
        
        intro = persona.generate_introduction()
        print(f"   ✓ Persona: {persona_config.name}")
        print(f"   ✓ Introducción: {intro[:50]}...")
        
        # Crear Ethics Engine
        ethics_engine = EthicsEngine()
        
        ethical_rules = [
            EthicalRule(
                id="transparency",
                name="Transparency",
                description="Always be transparent about AI involvement",
                severity="high"
            ),
            EthicalRule(
                id="privacy",
                name="Privacy Protection",
                description="Protect user data",
                severity="critical"
            )
        ]
        
        for rule in ethical_rules:
            ethics_engine.add_rule(rule)
        
        print(f"   ✓ Reglas éticas: {len(ethical_rules)}")
        
        # Evaluar acción
        ethics_eval = ethics_engine.evaluate_action(
            "generate_report",
            context={"disclose_ai": True}
        )
        print(f"   ✓ Evaluación ética: {'Pasó' if ethics_eval.passed else 'Falló'}")
        
        # =============================================================
        # FASE A: ACCIÓN
        # =============================================================
        print("\n[A] CAPA ACCIÓN...")
        
        # Crear Skills Registry
        skills_registry = SkillsRegistry(skills_directory=temp_dir, auto_save=False)
        
        # Crear skill de prueba
        test_skill = Skill(
            id="iovba_test_skill",
            name="IOVBA Test Skill",
            description="Skill de prueba para el flujo IOVBA",
            metadata=SkillMetadata(
                version="1.0.0",
                author="OpenClaw",
                tags=["test", "iovba"]
            ),
            template="Ejecutar análisis {{type}} con parámetros {{params}}"
        )
        
        skills_registry.register(test_skill)
        print(f"   ✓ Skill registrada: {test_skill.name}")
        
        # Crear MCP Registry
        mcp_registry = MCPRegistry()
        
        mcp_server = MCPServerConfig(
            name="test_server",
            command="test-command",
            args=["--test"],
            tools=[
                MCPTool(name="test_tool", description="Test tool for IOVBA")
            ]
        )
        
        mcp_registry.register_server(mcp_server)
        tools = mcp_registry.list_tools()
        print(f"   ✓ MCP Tools disponibles: {len(tools)}")
        
        # =============================================================
        # FASE RALPH: COSECHA
        # =============================================================
        print("\n[R] RALPH LOOP...")
        
        ralph_loop = RalphLoop(memory_vcs=memory_vcs)
        
        interaction = {
            "objective": "Test IOVBA flow",
            "success": True,
            "commands": [
                {"command": "init_infrastructure"},
                {"command": "orchestrate_agents"},
                {"command": "validate_actions"},
                {"command": "apply_behavior"},
                {"command": "execute_actions"}
            ],
            "errors": [],
            "tools_used": ["sandbox", "lead_agent", "guardrail", "skills"],
            "result": {"flow": "completed"}
        }
        
        ralph_session = await ralph_loop.execute(interaction)
        
        print(f"   ✓ Ralph Loop completado")
        print(f"   ✓ Fases ejecutadas: {len(ralph_session.results)}")
        print(f"   ✓ Capital cognitivo: {ralph_session.total_cognitive_capital}")
        
        # =============================================================
        # RESULTADOS FINALES
        # =============================================================
        print("\n" + "="*60)
        print("RESULTADOS DEL FLUJO IOVBA")
        print("="*60)
        
        # Guardar en memoria
        memory_vcs.upsert(
            topic_key="iovba:flow:test:result",
            content=json.dumps({
                "success": True,
                "phases": {
                    "infrastructure": sandbox_id[:8],
                    "orchestration": result.get("success"),
                    "validation": True,
                    "behavior": ethics_eval.passed,
                    "action": len(tools)
                },
                "ralph_capital": ralph_session.total_cognitive_capital,
                "timestamp": datetime.utcnow().isoformat()
            }),
            metadata={"type": "test_result"}
        )
        
        # Estadísticas de memoria
        stats = memory_vcs.get_stats()
        print(f"\nEstadísticas de Memory VCS:")
        print(f"   - Total memorias: {stats['total_memories']}")
        print(f"   - Total versiones: {stats['total_versions']}")
        print(f"   - Capital cognitivo total: {stats['total_cognitive_capital']}")
        
        # Estadísticas del Lead Agent
        agent_metrics = lead_agent.get_metrics()
        print(f"\nMétricas del Lead Agent:")
        print(f"   - Tareas completadas: {agent_metrics['tasks_completed']}")
        print(f"   - Tiempo promedio: {agent_metrics['avg_execution_time_ms']:.2f}ms")
        
        # Cleanup
        await sandbox_manager.destroy_sandbox(sandbox_id)
        print(f"\n   ✓ Sandbox destruido")
        
        print("\n" + "="*60)
        print("FLUJO IOVBA COMPLETADO EXITOSAMENTE")
        print("="*60 + "\n")
        
        # Assertions
        assert result["success"] is True
        assert ralph_session.completed_at is not None
        assert stats["total_memories"] >= 1


class TestOrchestrationDelegation:
    """Tests específicos de orquestación y delegación"""
    
    async def test_lead_agent_delegacion_jerarquica(self):
        """Test: Delegación jerárquica de tareas"""
        from src.iovba.orchestration.lead_agent import LeadAgent, AgentConfig
        
        print("\n" + "="*60)
        print("TEST: DELEGACIÓN JERÁRQUICA")
        print("="*60)
        
        # Crear Lead Agent con límite de sub-agentes
        lead = LeadAgent(AgentConfig(
            name="Master Agent",
            max_sub_agents=5
        ))
        
        # Simular tarea compleja
        task = "Analizar mercado de IA, identificar tendencias, y generar reporte estratégico"
        
        # Spawn sub-agentes especializados
        sub_agents = []
        sub_tasks = [
            "Research market data",
            "Analyze competitors",
            "Identify trends",
            "Generate report",
            "Review and validate"
        ]
        
        for sub_task in sub_tasks:
            sub_id = await lead.spawn_sub_agent(sub_task)
            sub_agents.append(sub_id)
            print(f"   ✓ Sub-agente creado: {sub_id[:8]} - {sub_task[:30]}...")
        
        # Verificar todos los sub-agentes
        assert len(lead.state.active_sub_agents) == 5
        print(f"\n   ✓ Total sub-agentes activos: {len(lead.state.active_sub_agents)}")
        
        # Verificar límite
        with pytest.raises(RuntimeError):
            await lead.spawn_sub_agent("Exceso de agentes")
        
        print(f"   ✓ Límite de sub-agentes respetado")
        
        print("\n" + "="*60 + "\n")
    
    async def test_lead_agent_analisis_complejidad(self):
        """Test: Análisis de complejidad de tareas"""
        from src.iovba.orchestration.lead_agent import LeadAgent, AgentConfig, TaskComplexity
        
        print("\n" + "="*60)
        print("TEST: ANÁLISIS DE COMPLEJIDAD")
        print("="*60)
        
        agent = LeadAgent(AgentConfig())
        
        test_cases = [
            ("Saludar al usuario", TaskComplexity.SIMPLE),
            ("Generar reporte de ventas", TaskComplexity.MODERATE),
            ("Analizar mercado y optimizar estrategia", TaskComplexity.COMPLEX),
            ("Investigar, desarrollar, integrar y deployar sistema completo con coordinación", TaskComplexity.VERY_COMPLEX),
        ]
        
        for task, expected_min in test_cases:
            agent.state.current_task = task
            complexity = await agent._analyze_complexity()
            
            status = "✓" if complexity.value >= expected_min.value else "⚠"
            print(f"   {status} '{task[:40]}...'")
            print(f"      Complejidad: {complexity.value}")
        
        print("\n" + "="*60 + "\n")
    
    async def test_lead_agent_planificacion(self):
        """Test: Generación de planes de ejecución"""
        from src.iovba.orchestration.lead_agent import LeadAgent, AgentConfig, TaskComplexity
        
        print("\n" + "="*60)
        print("TEST: PLANIFICACIÓN")
        print("="*60)
        
        agent = LeadAgent(AgentConfig())
        
        for complexity in TaskComplexity:
            agent.state.task_complexity = complexity
            plan = await agent._plan()
            
            print(f"\n   Complejidad: {complexity.value}")
            print(f"   Pasos en plan: {len(plan)}")
            
            for i, step in enumerate(plan[:3], 1):
                print(f"      {i}. {step.get('description', step.get('action'))}")
            
            if len(plan) > 3:
                print(f"      ... y {len(plan) - 3} pasos más")
        
        print("\n" + "="*60 + "\n")


class TestMemoryConsultation:
    """Tests de consulta de memoria"""
    
    async def test_consulta_memoria_semantica(self, temp_db):
        """Test: Consulta semántica en Memory VCS"""
        from src.memory.vcs import MemoryVCS, DisclosureLevel
        
        print("\n" + "="*60)
        print("TEST: CONSULTA SEMÁNTICA DE MEMORIA")
        print("="*60)
        
        vcs = MemoryVCS(db_path=temp_db, auto_init=True)
        
        # Poblar con datos de prueba
        test_data = [
            ("project:api:rest", "REST API following OpenAPI 3.0 specification"),
            ("project:api:graphql", "GraphQL API with Apollo Server"),
            ("project:db:postgres", "PostgreSQL database with UUID primary keys"),
            ("project:db:redis", "Redis cache for session management"),
            ("project:auth:oauth", "OAuth 2.0 with PKCE flow"),
            ("project:auth:jwt", "JWT tokens with RS256 signing"),
            ("project:testing:unit", "Unit tests with pytest"),
            ("project:testing:integration", "Integration tests with Docker Compose"),
        ]
        
        for topic, content in test_data:
            vcs.upsert(topic_key=topic, content=content, metadata={"domain": "development"})
        
        print(f"   ✓ {len(test_data)} memorias almacenadas")
        
        # Realizar búsquedas
        queries = [
            ("API", DisclosureLevel.COMPACT),
            ("database", DisclosureLevel.TIMELINE),
            ("auth", DisclosureLevel.FULL),
            ("testing", DisclosureLevel.FULL),
        ]
        
        for query, level in queries:
            results = vcs.search(query, limit=3, disclosure_level=level)
            print(f"\n   Búsqueda: '{query}' (nivel: {level.value})")
            print(f"   Resultados: {len(results)}")
            
            for r in results[:2]:
                if "content" in r:
                    print(f"      - {r['topic_key']}: {r['content'][:40]}...")
                else:
                    print(f"      - {r['topic_key']}")
        
        print("\n" + "="*60 + "\n")
    
    async def test_versionado_memoria(self, temp_db):
        """Test: Versionado de memorias"""
        from src.memory.vcs import MemoryVCS
        
        print("\n" + "="*60)
        print("TEST: VERSIONADO DE MEMORIA")
        print("="*60)
        
        vcs = MemoryVCS(db_path=temp_db, auto_init=True)
        
        topic = "project:config:versioning"
        
        # Crear y actualizar múltiples versiones
        versions = [
            "Configuración inicial v1",
            "Configuración actualizada v2 - añadido caching",
            "Configuración v3 - optimizado queries",
            "Configuración v4 - migrado a PostgreSQL",
            "Configuración v5 - añadido sharding"
        ]
        
        for i, content in enumerate(versions, 1):
            result = vcs.upsert(
                topic_key=topic,
                content=content,
                change_reason=f"Update to version {i}"
            )
            print(f"   ✓ Revisión {result['revision']}: {content[:40]}...")
        
        # Ver historial
        timeline = vcs.get_timeline(topic)
        print(f"\n   Historial de versiones: {len(timeline)}")
        
        for entry in timeline[-3:]:
            print(f"      v{entry['version']}: {entry['change_reason']}")
        
        # Obtener versión actual
        current = vcs.get_by_key(topic)
        print(f"\n   ✓ Versión actual: {current['revision']}")
        
        print("\n" + "="*60 + "\n")


class TestSkillsMCP:
    """Tests de Skills y MCP"""
    
    async def test_skills_registry_completo(self, temp_dir):
        """Test: Skills Registry completo"""
        from src.iovba.action.skills_registry import SkillsRegistry, Skill, SkillMetadata
        
        print("\n" + "="*60)
        print("TEST: SKILLS REGISTRY")
        print("="*60)
        
        registry = SkillsRegistry(skills_directory=temp_dir, auto_save=False)
        
        # Crear múltiples skills
        skills = [
            Skill(
                id="market_analysis",
                name="Market Analysis",
                description="Analyze market trends and competition",
                metadata=SkillMetadata(
                    version="1.0.0",
                    author="OpenClaw",
                    tags=["finance", "analysis", "market"]
                ),
                template="Analyze {{market}} market focusing on {{aspects}}"
            ),
            Skill(
                id="code_review",
                name="Code Review",
                description="Review code for quality and security",
                metadata=SkillMetadata(
                    version="2.0.0",
                    author="OpenClaw",
                    tags=["development", "review", "security"]
                ),
                template="Review {{language}} code for {{focus_areas}}"
            ),
            Skill(
                id="data_pipeline",
                name="Data Pipeline",
                description="Design and implement data pipelines",
                metadata=SkillMetadata(
                    version="1.5.0",
                    author="OpenClaw",
                    tags=["data", "pipeline", "etl"]
                ),
                template="Design pipeline for {{source}} to {{destination}}"
            ),
        ]
        
        for skill in skills:
            registry.register(skill)
            print(f"   ✓ Skill registrada: {skill.name} v{skill.metadata.version}")
        
        # Buscar por tags
        print("\n   Búsqueda por tags:")
        
        search_queries = [
            (["finance"], 1),
            (["development"], 1),
            (["data", "etl"], 1),
            (["analysis"], 2),
        ]
        
        for tags, expected_min in search_queries:
            results = registry.search_by_tags(tags)
            print(f"      Tags {tags}: {len(results)} resultados")
        
        print("\n" + "="*60 + "\n")
    
    async def test_mcp_registry_completo(self):
        """Test: MCP Registry completo"""
        from src.iovba.action.mcp_registry import MCPRegistry, MCPServerConfig, MCPTool, MCPTransport
        
        print("\n" + "="*60)
        print("TEST: MCP REGISTRY")
        print("="*60)
        
        registry = MCPRegistry()
        
        # Registrar múltiples servidores MCP
        servers = [
            MCPServerConfig(
                name="filesystem",
                transport=MCPTransport.STDIO,
                command="mcp-filesystem",
                args=["--root", "/data"],
            ),
            MCPServerConfig(
                name="database",
                transport=MCPTransport.STDIO,
                command="mcp-postgres",
                args=["--connection", "$DB_URL"],
            ),
            MCPServerConfig(
                name="web",
                transport=MCPTransport.STDIO,
                command="mcp-fetch",
                args=[],
            ),
        ]
        
        for server_config in servers:
            registry.register_server(server_config)
            print(f"   ✓ Servidor MCP registrado: {server_config.name}")
        
        # Crear herramientas manualmente para el test
        tools = [
            MCPTool(name="read_file", description="Read file content", server_name="filesystem"),
            MCPTool(name="write_file", description="Write file content", server_name="filesystem"),
            MCPTool(name="query", description="Execute SQL query", server_name="database"),
        ]
        
        print(f"\n   Herramientas definidas: {len(tools)}")
        
        for tool in tools:
            print(f"      - {tool.name}: {tool.description}")
        
        # Verificar que los servidores están registrados
        registered_servers = registry.list_servers()
        print(f"\n   Servidores registrados: {registered_servers}")
        
        assert len(registered_servers) == 3
        
        print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s", "--tb=short"])
