"""
Comprehensive Test Suite for OpenClaw Agent SaaS
50+ prompts from basic to high complexity

Tests:
- IOVBA Groups
- Lead Assistant
- HITL (Human In The Loop)
- LangGraph Integration
- Cognitive Capital
- Agent Creation
- Domain Specialization
"""

import pytest
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import modules to test
import sys
sys.path.insert(0, '/home/z/my-project/ecosystem/ricco-ai')

from src.iovba.groups import (
    IOVBAGroup,
    IOVBAGroupManager,
    IOVBARole,
    IOVBADomain,
    CapitalSyncMode,
    AgentProfile,
    CognitiveCapital,
    Engram,
    AgentStatus,
)
from src.iovba.lead_assistant import (
    LeadAssistant,
    LeadAssistantConfig,
    HITLProposal,
    ProposalType,
    ApprovalStatus,
)


# ==================== TEST DATA ====================

# 50+ Prompts for testing
BASIC_PROMPTS = [
    # Simple task assignments
    "¿Cuál es la capital de Francia?",
    "Calcula 2 + 2",
    "Define qué es una API REST",
    "Lista 5 lenguajes de programación populares",
    "Explica qué es un algoritmo",
    
    # Basic domain queries
    "Investiga sobre Python",
    "Busca información sobre JavaScript",
    "Analiza el concepto de machine learning",
    "Define qué es una base de datos",
    "Explica los principios de la programación orientada a objetos",
    
    # Simple coordination
    "Coordina una tarea simple de investigación",
    "Asigna una tarea básica al equipo",
    "Monitorea el estado del sistema",
    "Valida un resultado simple",
    "Crea un documento con información básica",
    
    # Basic creation
    "Crea un agente simple para tareas básicas",
    "Genera un reporte simple",
    "Resume un texto corto",
    "Traduce un texto básico",
    "Clasifica elementos en categorías simples",
]

MEDIUM_PROMPTS = [
    # Multi-step tasks
    "Investiga las mejores prácticas de seguridad en APIs y crea un documento de recomendaciones",
    "Analiza el código fuente de una aplicación y propone mejoras de rendimiento",
    "Diseña una arquitectura de microservicios para una aplicación de e-commerce",
    "Implementa un sistema de caching distribuido y documenta el proceso",
    "Crea una pipeline de CI/CD con testing automatizado",
    
    # Domain-specific analysis
    "Analiza el mercado de criptomonedas y genera un informe de tendencias",
    "Investiga nuevas terapias médicas para enfermedades raras",
    "Desarrolla un plan de marketing digital para una startup tecnológica",
    "Evalúa riesgos legales en un contrato de software",
    "Diseña un currículo educativo para un bootcamp de programación",
    
    # Multi-agent coordination
    "Coordina un equipo de desarrollo para crear una API REST completa",
    "Gestiona un proyecto de investigación con múltiples áreas",
    "Implementa un sistema de monitoreo con alertas inteligentes",
    "Crea un flujo de trabajo automatizado para procesamiento de datos",
    "Desarrolla un sistema de recomendaciones personalizadas",
    
    # Cognitive capital building
    "Analiza interacciones pasadas y genera nuevos engrams de aprendizaje",
    "Identifica patrones en datos históricos y propón mejoras",
    "Sincroniza conocimiento entre múltiples agentes del dominio SWE",
    "Evalúa el capital cognitivo del equipo y propón optimizaciones",
    "Implementa un ciclo de auto-mejora para el sistema",
    
    # HITL scenarios
    "Propón la creación de un nuevo agente especializado en finanzas con aprobación humana",
    "Solicita aprobación para modificar la configuración de un agente existente",
    "Genera una propuesta de cambio arquitectónico para revisión humana",
    "Crea un flujo de trabajo que requiera validación humana en puntos críticos",
    "Implementa un sistema de escalamiento para decisiones complejas",
    
    # Integration tests
    "Integra un nuevo MCP server y configura las herramientas disponibles",
    "Conecta el sistema con una base de datos vectorial para RAG",
    "Implementa un sistema de embeddings para búsqueda semántica",
    "Configura la sincronización de capital entre grupos IOVBA",
    "Establece comunicación entre agentes de diferentes dominios",
]

COMPLEX_PROMPTS = [
    # Full stack development
    "Diseña, implementa y despliega una aplicación completa de gestión de tareas con autenticación, API REST, base de datos, frontend React, testing, CI/CD y monitoreo. Coordina un equipo IOVBA completo para el proyecto.",
    
    # Multi-domain coordination
    "Coordina equipos IOVBA de SWE, Salud y Biotecnología para desarrollar un sistema de telemedicina con IA diagnóstica, cumpliendo regulaciones HIPAA, implementando seguridad avanzada, y generando documentación regulatoria completa.",
    
    # Cognitive capital evolution
    "Implementa un sistema de auto-evolución del capital cognitivo donde los agentes aprenden de interacciones pasadas, identifican gaps de conocimiento, proponen nuevas habilidades, crean nuevos agentes especializados, y sincronizan conocimiento en modo híbrido centralizado/descentralizado.",
    
    # Large scale HITL workflow
    "Diseña e implementa un workflow completo para desarrollar un sistema de trading algorítmico con múltiples puntos de HITL: aprobación de estrategias, validación de backtesting, autorización de despliegue, monitoreo de riesgos, y escalado de posiciones. Incluye rollback automático y notificaciones.",
    
    # Enterprise architecture
    "Crea una arquitectura empresarial completa para una plataforma SaaS multi-tenant con: microservicios, event-driven architecture, CQRS, event sourcing, distributed caching, message queues, API gateway, service mesh, observability stack, disaster recovery, y compliance framework.",
    
    # AI/ML pipeline
    "Desarrolla un pipeline completo de ML para detección de fraude en tiempo real: ingesta de datos, feature engineering, model training, model serving, A/B testing, monitoring de drift, retraining automático, y explicabilidad del modelo. Coordina equipos de SWE y Finanzas.",
    
    # Cross-functional product
    "Coordina equipos de SWE, Marketing, Legal y Finanzas para lanzar un producto fintech: desarrollo de app, estrategia de marketing, compliance regulatorio, modelo de ingresos, y análisis de riesgos. Incluye HITL para decisiones críticas.",
    
    # Knowledge graph construction
    "Construye un knowledge graph semántico a partir de documentos no estructurados: extracción de entidades, relación entre conceptos, enriquecimiento con fuentes externas, validación humana, visualización interactiva, y API de consulta. Actualiza capital cognitivo del sistema.",
    
    # Autonomous agent creation
    "El sistema debe detectar la necesidad de un nuevo agente especializado, crear la propuesta HITL, tras aprobación crear el agente con skills apropiadas, conectarlo a MCP servers relevantes, integrarlo en el grupo IOVBA, y monitorear su aprendizaje inicial.",
    
    # Multi-agent negotiation
    "Implementa un sistema de negociación entre agentes IOVBA donde múltiples equipos compiten por recursos limitados (computación, tokens, prioridad). Incluye mecanismos de bidding, resolución de conflictos, y optimización global con HITL para decisiones críticas.",
    
    # Self-healing infrastructure
    "Diseña un sistema de infraestructura self-healing donde agentes IOVBA detectan problemas, diagnostican causas, proponen soluciones, implementan fixes automáticamente cuando es seguro, escalan a humanos cuando es necesario, y documentan incidentes para aprendizaje futuro.",
    
    # Regulatory compliance automation
    "Implementa un sistema automatizado de compliance regulatorio para GDPR, HIPAA, SOC2: mapeo de datos, detección de violaciones, generación de reportes, gestión de consentimientos, derecho al olvido, y auditoría continua con HITL para casos ambiguos.",
    
    # Multi-modal agent
    "Crea un agente multi-modal capaz de procesar texto, imágenes, audio y video en un workflow integrado: transcripción, análisis de sentimiento, extracción de entidades, generación de resúmenes, y creación de contenido derivado. Incluye validación de calidad.",
    
    # Distributed cognitive capital
    "Implementa un sistema de capital cognitivo distribuido donde cada agente mantiene su propia base de conocimiento local, sincroniza selectivamente con pares, consolida en un repositorio central, detecta inconsistencias, y resuelve conflictos mediante consenso o HITL.",
    
    # Evolutionary optimization
    "Desarrolla un sistema de optimización evolutiva donde agentes IOVBA proponen variaciones de su configuración, las testean en ambientes sandbox, compiten por mejor performance, y las mejores se propagan a la población. HITL aprueba cambios mayores.",
]


# ==================== FIXTURES ====================

@pytest.fixture
def group_manager():
    """Create an IOVBA Group Manager"""
    return IOVBAGroupManager()


@pytest.fixture
def lead_assistant():
    """Create a Lead Assistant"""
    config = LeadAssistantConfig(
        requires_hitl_for_creation=False,  # For testing
        requires_hitl_for_modification=False,
    )
    return LeadAssistant(config=config)


@pytest.fixture
def sample_engram():
    """Create a sample Engram"""
    return Engram(
        content="Test learning content",
        source="interaction",
        tags=["test", "learning"],
        importance_score=0.8,
    )


@pytest.fixture
def sample_agent():
    """Create a sample Agent Profile"""
    return AgentProfile(
        name="Test Agent",
        description="A test agent",
        domain="swe",
        iovba_role="investigador",
    )


# ==================== BASIC TESTS ====================

class TestEngramBasics:
    """Test basic Engram functionality"""
    
    def test_engram_creation(self):
        """Test creating an engram"""
        engram = Engram(
            content="Test content",
            source="interaction",
        )
        assert engram.content == "Test content"
        assert engram.source == "interaction"
        assert engram.access_count == 0
    
    def test_engram_access(self, sample_engram):
        """Test engram access counter"""
        initial_count = sample_engram.access_count
        sample_engram.access()
        assert sample_engram.access_count == initial_count + 1
    
    def test_engram_tags(self):
        """Test engram tags"""
        engram = Engram(
            content="Tagged content",
            tags=["python", "testing", "unit"],
        )
        assert len(engram.tags) == 3
        assert "python" in engram.tags


class TestCognitiveCapitalBasics:
    """Test basic Cognitive Capital functionality"""
    
    def test_capital_creation(self):
        """Test creating cognitive capital"""
        capital = CognitiveCapital(agent_id="test-agent")
        assert capital.agent_id == "test-agent"
        assert capital.total_engrams == 0
        assert capital.capital_value == 0
    
    def test_add_engram(self):
        """Test adding engram to capital"""
        capital = CognitiveCapital(agent_id="test-agent")
        engram = Engram(content="New learning")
        
        capital.add_engram(engram)
        
        assert capital.total_engrams == 1
        assert capital.capital_value > 0
    
    def test_capital_improve(self):
        """Test capital improvement"""
        capital = CognitiveCapital(agent_id="test-agent", learning_score=0.5)
        
        capital.improve(0.1)
        
        assert capital.learning_score == 0.6
        assert capital.last_improvement is not None
    
    def test_get_top_engrams(self):
        """Test getting top engrams"""
        capital = CognitiveCapital(agent_id="test-agent")
        
        for i in range(5):
            engram = Engram(
                content=f"Content {i}",
                importance_score=i / 10,
            )
            capital.add_engram(engram)
        
        top = capital.get_top_engrams(3)
        assert len(top) == 3
        assert top[0].importance_score >= top[1].importance_score


class TestAgentProfileBasics:
    """Test basic Agent Profile functionality"""
    
    def test_agent_creation(self):
        """Test creating an agent profile"""
        agent = AgentProfile(
            name="Test Agent",
            domain="swe",
            iovba_role="investigador",
        )
        assert agent.name == "Test Agent"
        assert agent.domain == "swe"
        assert agent.status == AgentStatus.ACTIVE
    
    def test_agent_capital_initialization(self):
        """Test that agent has cognitive capital"""
        agent = AgentProfile(name="Test")
        assert agent.cognitive_capital is not None
        assert agent.cognitive_capital.agent_id == agent.id


# ==================== IOVBA GROUP TESTS ====================

class TestIOVBAGroup:
    """Test IOVBA Group functionality"""
    
    def test_group_creation(self, group_manager):
        """Test creating an IOVBA group"""
        group = group_manager.create_group(
            name="SWE Team",
            domain="swe",
            description="Software Engineering team",
        )
        
        assert group.name == "SWE Team"
        assert group.domain == "swe"
        assert group.investigador is not None
        assert group.observador is not None
        assert group.validador is not None
        assert group.builder is not None
        assert group.asistente is not None
    
    def test_group_has_all_roles(self, group_manager):
        """Test that group has all 5 IOVBA roles"""
        group = group_manager.create_group(
            name="Test Team",
            domain="salud",
        )
        
        agents = group.get_all_agents()
        
        assert "investigador" in agents
        assert "observador" in agents
        assert "validador" in agents
        assert "builder" in agents
        assert "asistente" in agents
    
    @pytest.mark.asyncio
    async def test_group_sync_capital(self, group_manager):
        """Test syncing capital within group"""
        group = group_manager.create_group(
            name="Sync Test",
            domain="swe",
            sync_mode=CapitalSyncMode.CENTRALIZED,
        )
        
        # Add engrams to investigator
        engram = Engram(content="Test learning")
        group.investigador.cognitive_capital.add_engram(engram)
        
        # Sync
        result = await group.sync_capital()
        
        assert "synced_agents" in result
        assert len(result["synced_agents"]) > 0
    
    @pytest.mark.asyncio
    async def test_group_auto_improve(self, group_manager):
        """Test group auto-improvement"""
        group = group_manager.create_group(
            name="Improve Test",
            domain="swe",
        )
        
        # Set some metrics
        group.investigador.success_rate = 0.9
        
        result = await group.auto_improve()
        
        assert "improvements" in result
        assert len(result["improvements"]) > 0


class TestIOVBAGroupManager:
    """Test IOVBA Group Manager"""
    
    def test_manager_creation(self):
        """Test creating a group manager"""
        manager = IOVBAGroupManager()
        assert len(manager.groups) == 0
        assert len(manager.domain_templates) > 0
    
    def test_list_groups(self, group_manager):
        """Test listing groups"""
        group_manager.create_group("Team 1", "swe")
        group_manager.create_group("Team 2", "salud")
        
        groups = group_manager.list_groups()
        assert len(groups) == 2
    
    def test_get_group(self, group_manager):
        """Test getting a specific group"""
        group = group_manager.create_group("Test", "swe")
        
        retrieved = group_manager.get_group(group.id)
        assert retrieved is not None
        assert retrieved.id == group.id
    
    @pytest.mark.asyncio
    async def test_sync_all_groups(self, group_manager):
        """Test syncing all groups"""
        group_manager.create_group("Team 1", "swe")
        group_manager.create_group("Team 2", "salud")
        
        results = await group_manager.sync_all_groups()
        
        assert len(results) == 2
    
    @pytest.mark.asyncio
    async def test_auto_improve_all(self, group_manager):
        """Test auto-improving all groups"""
        group_manager.create_group("Team 1", "swe")
        group_manager.create_group("Team 2", "salud")
        
        results = await group_manager.auto_improve_all()
        
        assert len(results) == 2


# ==================== LEAD ASSISTANT TESTS ====================

class TestLeadAssistant:
    """Test Lead Assistant functionality"""
    
    def test_assistant_creation(self):
        """Test creating a lead assistant"""
        assistant = LeadAssistant()
        assert assistant.config is not None
        assert assistant.group_manager is not None
    
    @pytest.mark.asyncio
    async def test_coordinate_task(self, lead_assistant):
        """Test task coordination"""
        lead_assistant.group_manager.create_group("SWE Team", "swe")
        
        result = await lead_assistant.coordinate_task(
            task="Investiga las mejores prácticas de Python",
            domain="swe",
        )
        
        assert "task" in result
        assert result["domain"] == "swe"
    
    @pytest.mark.asyncio
    async def test_propose_create_group(self, lead_assistant):
        """Test proposing group creation"""
        proposal = await lead_assistant.propose_create_group(
            domain="finanzas",
            reason="New financial domain needed",
        )
        
        assert proposal.proposal_type == ProposalType.CREATE_GROUP
        assert proposal.domain == "finanzas" or proposal.details.get("domain") == "finanzas"
    
    @pytest.mark.asyncio
    async def test_approve_proposal(self, lead_assistant):
        """Test approving a proposal"""
        proposal = await lead_assistant.propose_create_group(
            domain="noticias",
            reason="Test approval",
        )
        
        result = await lead_assistant.approve_proposal(
            proposal.id,
            approver="test_user",
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_reject_proposal(self, lead_assistant):
        """Test rejecting a proposal"""
        proposal = await lead_assistant.propose_create_group(
            domain="custom",
            reason="Test rejection",
        )
        
        result = await lead_assistant.reject_proposal(
            proposal.id,
            reason="Not needed",
        )
        
        assert result is True
    
    def test_get_pending_proposals(self, lead_assistant):
        """Test getting pending proposals"""
        pending = lead_assistant.get_pending_proposals()
        assert isinstance(pending, list)
    
    @pytest.mark.asyncio
    async def test_sync_global_capital(self, lead_assistant):
        """Test syncing global capital"""
        lead_assistant.group_manager.create_group("Team", "swe")
        
        result = await lead_assistant.sync_global_capital()
        
        assert "groups_synced" in result
    
    def test_get_status(self, lead_assistant):
        """Test getting assistant status"""
        status = lead_assistant.get_status()
        
        assert "id" in status
        assert "name" in status
        assert "total_groups" in status


class TestHITL:
    """Test Human In The Loop functionality"""
    
    def test_proposal_creation(self):
        """Test creating a HITL proposal"""
        proposal = HITLProposal(
            proposal_type=ProposalType.CREATE_AGENT,
            title="Create New Agent",
            description="Need a specialized agent",
        )
        
        assert proposal.status == ApprovalStatus.PENDING
    
    def test_proposal_approve(self):
        """Test approving a proposal"""
        proposal = HITLProposal()
        
        proposal.approve("test_user")
        
        assert proposal.status == ApprovalStatus.APPROVED
        assert proposal.approved_by == "test_user"
    
    def test_proposal_reject(self):
        """Test rejecting a proposal"""
        proposal = HITLProposal()
        
        proposal.reject("Not approved")
        
        assert proposal.status == ApprovalStatus.REJECTED
        assert proposal.rejection_reason == "Not approved"
    
    def test_proposal_timeout(self):
        """Test proposal timeout"""
        proposal = HITLProposal(timeout_seconds=-1)  # Already timed out
        
        is_timeout = proposal.check_timeout()
        
        assert is_timeout is True
        assert proposal.status == ApprovalStatus.TIMEOUT


# ==================== PROMPT-BASED TESTS ====================

class TestBasicPrompts:
    """Test system with basic prompts"""
    
    @pytest.mark.parametrize("prompt", BASIC_PROMPTS[:5])
    @pytest.mark.asyncio
    async def test_basic_info_queries(self, lead_assistant, prompt):
        """Test basic information queries"""
        lead_assistant.group_manager.create_group("General", "swe")
        
        result = await lead_assistant.coordinate_task(
            task=prompt,
            domain="swe",
        )
        
        assert result is not None
        assert "status" in result
    
    @pytest.mark.parametrize("prompt", BASIC_PROMPTS[5:10])
    @pytest.mark.asyncio
    async def test_basic_domain_queries(self, lead_assistant, prompt):
        """Test basic domain queries"""
        lead_assistant.group_manager.create_group("Research", "investigacion")
        
        result = await lead_assistant.coordinate_task(
            task=prompt,
            domain="investigacion",
        )
        
        assert result is not None
    
    @pytest.mark.parametrize("prompt", BASIC_PROMPTS[10:15])
    @pytest.mark.asyncio
    async def test_basic_coordination(self, lead_assistant, prompt):
        """Test basic coordination tasks"""
        lead_assistant.group_manager.create_group("Coord", "swe")
        
        result = await lead_assistant.coordinate_task(
            task=prompt,
            domain="swe",
        )
        
        assert result is not None
    
    @pytest.mark.parametrize("prompt", BASIC_PROMPTS[15:20])
    @pytest.mark.asyncio
    async def test_basic_creation(self, lead_assistant, prompt):
        """Test basic creation tasks"""
        result = await lead_assistant.coordinate_task(
            task=prompt,
            domain="swe",
        )
        
        assert result is not None


class TestMediumPrompts:
    """Test system with medium complexity prompts"""
    
    @pytest.mark.parametrize("prompt", MEDIUM_PROMPTS[:5])
    @pytest.mark.asyncio
    async def test_multi_step_tasks(self, lead_assistant, prompt):
        """Test multi-step tasks"""
        lead_assistant.group_manager.create_group("SWE", "swe")
        
        result = await lead_assistant.coordinate_task(
            task=prompt,
            domain="swe",
        )
        
        assert result is not None
        assert "workflow" in result or "assigned_agents" in result
    
    @pytest.mark.parametrize("prompt", MEDIUM_PROMPTS[5:10])
    @pytest.mark.asyncio
    async def test_domain_analysis(self, lead_assistant, prompt):
        """Test domain-specific analysis"""
        # Create groups for different domains
        lead_assistant.group_manager.create_group("Finanzas", "finanzas")
        lead_assistant.group_manager.create_group("Salud", "salud")
        lead_assistant.group_manager.create_group("Marketing", "marketing")
        lead_assistant.group_manager.create_group("Legal", "legal")
        lead_assistant.group_manager.create_group("Educacion", "educacion")
        
        # Determine domain from prompt
        domain = "swe"
        if "financier" in prompt.lower() or "crypto" in prompt.lower():
            domain = "finanzas"
        elif "médic" in prompt.lower() or "salud" in prompt.lower():
            domain = "salud"
        elif "marketing" in prompt.lower():
            domain = "marketing"
        elif "legal" in prompt.lower() or "contrato" in prompt.lower():
            domain = "legal"
        elif "educat" in prompt.lower() or "currículo" in prompt.lower():
            domain = "educacion"
        
        result = await lead_assistant.coordinate_task(
            task=prompt,
            domain=domain,
        )
        
        assert result is not None
    
    @pytest.mark.parametrize("prompt", MEDIUM_PROMPTS[10:15])
    @pytest.mark.asyncio
    async def test_multi_agent_coordination(self, lead_assistant, prompt):
        """Test multi-agent coordination"""
        lead_assistant.group_manager.create_group("SWE", "swe")
        
        result = await lead_assistant.coordinate_task(
            task=prompt,
            domain="swe",
        )
        
        assert result is not None
    
    @pytest.mark.parametrize("prompt", MEDIUM_PROMPTS[15:20])
    @pytest.mark.asyncio
    async def test_cognitive_capital_building(self, lead_assistant, prompt):
        """Test cognitive capital building tasks"""
        group = lead_assistant.group_manager.create_group("Capital", "swe")
        
        # Add some learning
        engram = Engram(content="Pattern: User prefers concise responses")
        group.investigador.cognitive_capital.add_engram(engram)
        
        result = await lead_assistant.coordinate_task(
            task=prompt,
            domain="swe",
        )
        
        assert result is not None
    
    @pytest.mark.parametrize("prompt", MEDIUM_PROMPTS[20:25])
    @pytest.mark.asyncio
    async def test_hitl_scenarios(self, lead_assistant, prompt):
        """Test HITL scenarios"""
        # Enable HITL for testing
        lead_assistant.config.requires_hitl_for_creation = True
        
        result = await lead_assistant.coordinate_task(
            task=prompt,
            domain="swe",
        )
        
        assert result is not None
    
    @pytest.mark.parametrize("prompt", MEDIUM_PROMPTS[25:30])
    @pytest.mark.asyncio
    async def test_integration_tasks(self, lead_assistant, prompt):
        """Test integration tasks"""
        lead_assistant.group_manager.create_group("Integration", "swe")
        
        result = await lead_assistant.coordinate_task(
            task=prompt,
            domain="swe",
        )
        
        assert result is not None


class TestComplexPrompts:
    """Test system with high complexity prompts"""
    
    @pytest.mark.parametrize("prompt", COMPLEX_PROMPTS[:5])
    @pytest.mark.asyncio
    async def test_full_stack_development(self, lead_assistant, prompt):
        """Test full stack development tasks"""
        lead_assistant.group_manager.create_group("FullStack", "swe")
        
        result = await lead_assistant.coordinate_task(
            task=prompt,
            domain="swe",
        )
        
        assert result is not None
    
    @pytest.mark.parametrize("prompt", COMPLEX_PROMPTS[5:10])
    @pytest.mark.asyncio
    async def test_multi_domain_coordination(self, lead_assistant, prompt):
        """Test multi-domain coordination"""
        # Create multiple domain groups
        lead_assistant.group_manager.create_group("SWE", "swe")
        lead_assistant.group_manager.create_group("Salud", "salud")
        lead_assistant.group_manager.create_group("Bio", "biotecnologia")
        lead_assistant.group_manager.create_group("Finanzas", "finanzas")
        
        result = await lead_assistant.coordinate_task(
            task=prompt,
            domain="swe",  # Lead domain
        )
        
        assert result is not None
    
    @pytest.mark.parametrize("prompt", COMPLEX_PROMPTS[10:15])
    @pytest.mark.asyncio
    async def test_complex_hitl_workflows(self, lead_assistant, prompt):
        """Test complex HITL workflows"""
        lead_assistant.group_manager.create_group("Enterprise", "swe")
        
        result = await lead_assistant.coordinate_task(
            task=prompt,
            domain="swe",
        )
        
        assert result is not None


# ==================== STRESS TESTS ====================

class TestStressScenarios:
    """Stress test the system"""
    
    @pytest.mark.asyncio
    async def test_rapid_task_submission(self, lead_assistant):
        """Test submitting many tasks rapidly"""
        lead_assistant.group_manager.create_group("Stress", "swe")
        
        tasks = [f"Task {i}: Process data and generate report" for i in range(20)]
        
        results = await asyncio.gather(*[
            lead_assistant.coordinate_task(task, "swe")
            for task in tasks
        ])
        
        assert len(results) == 20
        assert all(r is not None for r in results)
    
    @pytest.mark.asyncio
    async def test_concurrent_proposals(self, lead_assistant):
        """Test concurrent proposal creation"""
        proposals = await asyncio.gather(*[
            lead_assistant.propose_create_group(
                domain=f"custom_{i}",
                reason=f"Test proposal {i}",
            )
            for i in range(10)
        ])
        
        assert len(proposals) == 10
        assert all(p is not None for p in proposals)
    
    @pytest.mark.asyncio
    async def test_capital_growth_stress(self, group_manager):
        """Test capital growth under stress"""
        group = group_manager.create_group("Stress", "swe")
        
        # Add many engrams
        for i in range(100):
            engram = Engram(
                content=f"Learning {i}",
                importance_score=i / 100,
            )
            group.investigador.cognitive_capital.add_engram(engram)
        
        # Sync and improve
        await group.sync_capital()
        await group.auto_improve()
        
        assert group.investigador.cognitive_capital.total_engrams == 100


# ==================== RUN TESTS ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
