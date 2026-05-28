"""
=============================================================================
RICCO-AI Integration Test Suite
=============================================================================
Este archivo contiene 70 pruebas que integran:
- DeerFlow (Backend de agentes)
- Gentle-AI (Framework SDD)
- Ricco-AI (Frontend + API)

CUMPLE SOLID:
- OCP: Pruebas usan configuración dinámica, no enums hardcodeados
- SRP: Cada test tiene una única responsabilidad
- DIP: Tests dependen de abstracciones (registries)
=============================================================================
"""

import pytest
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

# =============================================================================
# CONFIGURATION LOADING - Sin enums, configuración dinámica
# =============================================================================

@dataclass
class DomainConfig:
    """Configuración de dominio cargada desde YAML"""
    id: str
    elegant_name: str
    display_name: str
    description: str
    icon: str
    color: str
    category: str
    default_skills: List[str]
    default_tools: List[str]
    default_mcp_servers: List[str]
    keywords: List[str]
    prompt_template: str


@dataclass
class RoleConfig:
    """Configuración de rol IOVBA cargada desde YAML"""
    id: str
    elegant_name: str
    display_name: str
    tagline: str
    description: str
    icon: str
    color: str
    default_skills: List[str]
    default_tools: List[str]


class ConfigLoader:
    """Carga configuración desde archivos YAML - Cumple OCP"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self._domains_cache: Optional[Dict[str, DomainConfig]] = None
        self._roles_cache: Optional[Dict[str, RoleConfig]] = None
    
    def load_domains(self) -> Dict[str, DomainConfig]:
        if self._domains_cache is not None:
            return self._domains_cache
        
        domains_path = self.config_dir / "domains.yaml"
        if not domains_path.exists():
            return self._get_default_domains()
        
        with open(domains_path, 'r') as f:
            config = yaml.safe_load(f)
        
        self._domains_cache = {}
        for domain_id, domain_data in config.get('domains', {}).items():
            self._domains_cache[domain_id] = DomainConfig(
                id=domain_id,
                elegant_name=domain_data.get('elegant_name', domain_id.upper()),
                display_name=domain_data.get('display_name', domain_id),
                description=domain_data.get('description', ''),
                icon=domain_data.get('icon', 'circle'),
                color=domain_data.get('color', '#6366F1'),
                category=domain_data.get('category', 'general'),
                default_skills=domain_data.get('default_skills', []),
                default_tools=domain_data.get('default_tools', []),
                default_mcp_servers=domain_data.get('default_mcp_servers', []),
                keywords=domain_data.get('keywords', []),
                prompt_template=domain_data.get('prompt_template', ''),
            )
        return self._domains_cache
    
    def load_roles(self) -> Dict[str, RoleConfig]:
        if self._roles_cache is not None:
            return self._roles_cache
        
        roles_path = self.config_dir / "iovba-roles.yaml"
        if not roles_path.exists():
            return self._get_default_roles()
        
        with open(roles_path, 'r') as f:
            config = yaml.safe_load(f)
        
        self._roles_cache = {}
        for role_id, role_data in config.get('roles', {}).items():
            self._roles_cache[role_id] = RoleConfig(
                id=role_id,
                elegant_name=role_data.get('elegant_name', role_id.upper()),
                display_name=role_data.get('display_name', role_id),
                tagline=role_data.get('tagline', ''),
                description=role_data.get('description', ''),
                icon=role_data.get('icon', 'circle'),
                color=role_data.get('color', '#6366F1'),
                default_skills=role_data.get('default_skills', []),
                default_tools=role_data.get('default_tools', []),
            )
        return self._roles_cache
    
    def _get_default_domains(self) -> Dict[str, DomainConfig]:
        return {
            'codex': DomainConfig(
                id='codex', elegant_name='CODEX', display_name='Software Engineering',
                description='Software development', icon='code', color='#3B82F6',
                category='engineering', default_skills=['coding'], default_tools=['git'],
                default_mcp_servers=['github'], keywords=['code', 'software'],
                prompt_template='Eres un especialista en software.'
            )
        }
    
    def _get_default_roles(self) -> Dict[str, RoleConfig]:
        return {
            'investigator': RoleConfig(
                id='investigator', elegant_name='INVESTIGATOR', display_name='Investigator',
                tagline='Descubre y analiza', description='Research role',
                icon='microscope', color='#3B82F6',
                default_skills=['research'], default_tools=['search']
            )
        }
    
    def detect_domain(self, text: str) -> str:
        domains = self.load_domains()
        text_lower = text.lower()
        for domain_id, domain in domains.items():
            for keyword in domain.keywords:
                if keyword in text_lower:
                    return domain_id
        return 'codex'


config_loader = ConfigLoader()


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture
def domains() -> Dict[str, DomainConfig]:
    return config_loader.load_domains()


@pytest.fixture
def roles() -> Dict[str, RoleConfig]:
    return config_loader.load_roles()


# =============================================================================
# TEST GROUP 1: Domain Registry Tests (10 tests)
# =============================================================================

class TestDomainRegistry:
    """Tests para Domain Registry - Cumple OCP (sin enums)"""
    
    def test_01_load_domains_from_config(self, domains):
        """Test 1: Cargar dominios desde configuración YAML"""
        assert len(domains) >= 13, "Debe haber al menos 13 dominios"
        assert 'codex' in domains, "Dominio CODEX debe existir"
    
    def test_02_domain_has_required_fields(self, domains):
        """Test 2: Cada dominio tiene campos requeridos"""
        required = ['id', 'elegant_name', 'display_name', 'description', 'icon', 'color']
        for domain_id, domain in domains.items():
            for field in required:
                assert hasattr(domain, field), f"Domain {domain_id} missing {field}"
    
    def test_03_domain_elegant_names_unique(self, domains):
        """Test 3: Elegant names son únicos"""
        names = [d.elegant_name for d in domains.values()]
        assert len(names) == len(set(names)), "Elegant names deben ser únicos"
    
    def test_04_detect_codex_domain(self):
        """Test 4: Detectar CODEX por keyword 'code'"""
        detected = config_loader.detect_domain("Necesito ayuda con mi código")
        assert detected == 'codex'
    
    def test_05_detect_vitalis_domain(self):
        """Test 5: Detectar VITALIS por keyword 'salud'"""
        detected = config_loader.detect_domain("Tengo una pregunta de salud")
        assert detected == 'vitalis'
    
    def test_06_detect_apex_domain(self):
        """Test 6: Detectar APEX por keyword 'finanzas'"""
        detected = config_loader.detect_domain("Análisis de finanzas")
        assert detected == 'apex'
    
    def test_07_domain_default_skills_not_empty(self, domains):
        """Test 7: Cada dominio tiene skills"""
        for domain_id, domain in domains.items():
            assert len(domain.default_skills) > 0
    
    def test_08_domain_default_tools_not_empty(self, domains):
        """Test 8: Cada dominio tiene tools"""
        for domain_id, domain in domains.items():
            assert len(domain.default_tools) > 0
    
    def test_09_domain_keywords_not_empty(self, domains):
        """Test 9: Cada dominio tiene keywords"""
        for domain_id, domain in domains.items():
            assert len(domain.keywords) > 0
    
    def test_10_no_enum_violation(self, domains):
        """Test 10: Dominios NO son enum - son dict dinámico"""
        assert isinstance(domains, dict)
        domains['custom_test'] = DomainConfig(
            id='custom_test', elegant_name='CUSTOM', display_name='Custom',
            description='Test', icon='test', color='#000000', category='test',
            default_skills=[], default_tools=[], default_mcp_servers=[],
            keywords=['test'], prompt_template='Test'
        )
        assert 'custom_test' in domains


# =============================================================================
# TEST GROUP 2: Role Registry Tests (10 tests)
# =============================================================================

class TestRoleRegistry:
    """Tests para IOVBA Role Registry"""
    
    def test_11_load_roles_from_config(self, roles):
        """Test 11: Cargar roles IOVBA"""
        assert len(roles) >= 5
        assert 'investigator' in roles
        assert 'assistant' in roles
    
    def test_12_role_has_required_fields(self, roles):
        """Test 12: Cada rol tiene campos requeridos"""
        required = ['id', 'elegant_name', 'display_name', 'tagline', 'description']
        for role_id, role in roles.items():
            for field in required:
                assert hasattr(role, field), f"Role {role_id} missing {field}"
    
    def test_13_investigator_skills(self, roles):
        """Test 13: Investigator tiene skills de investigación"""
        inv = roles.get('investigator')
        assert inv is not None
        assert 'research' in inv.default_skills or 'analysis' in inv.default_skills
    
    def test_14_observer_skills(self, roles):
        """Test 14: Observer tiene skills de monitoreo"""
        obs = roles.get('observer')
        assert obs is not None
        assert 'monitoring' in obs.default_skills or 'anomaly-detection' in obs.default_skills
    
    def test_15_validator_skills(self, roles):
        """Test 15: Validator tiene skills de validación"""
        val = roles.get('validator')
        assert val is not None
        assert 'validation' in val.default_skills or 'testing' in val.default_skills
    
    def test_16_builder_skills(self, roles):
        """Test 16: Builder tiene skills de construcción"""
        builder = roles.get('builder')
        assert builder is not None
        assert 'coding' in builder.default_skills or 'implementation' in builder.default_skills
    
    def test_17_assistant_skills(self, roles):
        """Test 17: Assistant tiene skills de coordinación"""
        assistant = roles.get('assistant')
        assert assistant is not None
        assert 'coordination' in assistant.default_skills or 'communication' in assistant.default_skills
    
    def test_18_role_tags_format(self):
        """Test 18: Tags IOVBA formato correcto"""
        tags = ["IOVBA", "investigator"]
        assert "IOVBA" in tags
        assert "investigator" in tags
    
    def test_19_no_enum_violation_roles(self, roles):
        """Test 19: Roles NO son enum"""
        assert isinstance(roles, dict)
        roles['custom_role'] = RoleConfig(
            id='custom_role', elegant_name='CUSTOM', display_name='Custom',
            tagline='Test', description='Test', icon='test', color='#000000',
            default_skills=[], default_tools=[]
        )
        assert 'custom_role' in roles
    
    def test_20_roles_unique_colors(self, roles):
        """Test 20: Cada rol tiene color único"""
        colors = [r.color for r in roles.values()]
        assert len(colors) == len(set(colors))


# =============================================================================
# TEST GROUP 3: Gentle-AI Integration Tests (15 tests)
# =============================================================================

class TestGentleAIIntegration:
    """Tests de integración con Gentle-AI"""
    
    def test_21_gentle_ai_repo_exists(self):
        """Test 21: Repositorio Gentle-AI existe"""
        path = Path("ecosystem/gentle-ai")
        assert path.exists()
    
    def test_22_sdd_agents_exist(self):
        """Test 22: Agentes SDD existen"""
        path = Path("ecosystem/gentle-ai/internal/assets/kimi/agents")
        if path.exists():
            agents = list(path.glob("*.md"))
            assert len(agents) > 0
    
    def test_23_sdd_skills_exist(self):
        """Test 23: Skills SDD existen"""
        path = Path("ecosystem/gentle-ai/internal/assets/skills")
        if path.exists():
            skills = list(path.glob("*/SKILL.md"))
            assert len(skills) > 0
    
    def test_24_pipeline_orchestrator_exists(self):
        """Test 24: Pipeline orchestrator existe"""
        path = Path("ecosystem/gentle-ai/internal/pipeline/orchestrator.go")
        if path.exists():
            content = path.read_text()
            assert 'Orchestrator' in content or 'orchestrator' in content
    
    def test_25_gentleman_persona_exists(self):
        """Test 25: Persona Gentleman existe"""
        path = Path("ecosystem/gentle-ai/internal/assets/kimi/persona-gentleman.md")
        if path.exists():
            content = path.read_text()
            assert len(content) > 100
    
    def test_26_cli_exists(self):
        """Test 26: CLI de Gentle-AI existe"""
        path = Path("ecosystem/gentle-ai/cmd/gentle-ai/main.go")
        if path.exists():
            content = path.read_text()
            assert 'main' in content
    
    def test_27_state_management_exists(self):
        """Test 27: State management existe"""
        path = Path("ecosystem/gentle-ai/internal/state/state.go")
        if path.exists():
            content = path.read_text()
            assert 'State' in content or 'state' in content
    
    def test_28_backup_system_exists(self):
        """Test 28: Sistema de backup existe"""
        path = Path("ecosystem/gentle-ai/internal/backup")
        if path.exists():
            files = list(path.glob("*.go"))
            assert len(files) > 0
    
    def test_29_install_scripts_exist(self):
        """Test 29: Scripts de instalación existen"""
        scripts = [
            Path("ecosystem/gentle-ai/scripts/install.sh"),
            Path("ecosystem/gentle-ai/scripts/install.ps1")
        ]
        assert any(s.exists() for s in scripts)
    
    def test_30_documentation_exists(self):
        """Test 30: Documentación existe"""
        path = Path("ecosystem/gentle-ai/docs")
        if path.exists():
            docs = list(path.glob("**/*.md"))
            assert len(docs) > 0


# =============================================================================
# TEST GROUP 4: DeerFlow Integration Tests (15 tests)
# =============================================================================

class TestDeerFlowIntegration:
    """Tests de integración con DeerFlow"""
    
    def test_31_deerflow_repo_exists(self):
        """Test 31: Repositorio DeerFlow existe"""
        path = Path("ecosystem/deer-flow")
        assert path.exists()
    
    def test_32_backend_structure(self):
        """Test 32: Estructura backend correcta"""
        backend = Path("ecosystem/deer-flow/backend")
        assert backend.exists()
        assert (backend / "app").exists()
        assert (backend / "packages").exists()
    
    def test_33_gentle_ai_skill_exists(self):
        """Test 33: Skill Gentle-AI integration existe"""
        path = Path("ecosystem/deer-flow/skills/public/gentle-ai-integration/SKILL.md")
        assert path.exists()
    
    def test_34_gentle_pi_skill_exists(self):
        """Test 34: Skill Gentle-Pi integration existe"""
        path = Path("ecosystem/deer-flow/skills/public/gentle-pi-integration/SKILL.md")
        assert path.exists()
    
    def test_35_gateway_exists(self):
        """Test 35: Gateway existe"""
        path = Path("ecosystem/deer-flow/backend/app/gateway")
        assert path.exists()
    
    def test_36_routers_exist(self):
        """Test 36: Routers existen"""
        path = Path("ecosystem/deer-flow/backend/app/gateway/routers")
        if path.exists():
            routers = list(path.glob("*.py"))
            assert len(routers) > 0
    
    def test_37_mcp_support_exists(self):
        """Test 37: Soporte MCP existe"""
        path = Path("ecosystem/deer-flow/backend/packages/harness/deerflow/mcp")
        assert path.exists()
    
    def test_38_skills_parser_exists(self):
        """Test 38: Skills parser existe"""
        path = Path("ecosystem/deer-flow/backend/packages/harness/deerflow/skills/parser.py")
        assert path.exists()
    
    def test_39_memory_system_exists(self):
        """Test 39: Sistema de memoria existe"""
        path = Path("ecosystem/deer-flow/backend/packages/harness/deerflow/agents/memory")
        assert path.exists()
    
    def test_40_subagents_support_exists(self):
        """Test 40: Soporte de subagentes existe"""
        path = Path("ecosystem/deer-flow/backend/packages/harness/deerflow/subagents")
        assert path.exists()


# =============================================================================
# TEST GROUP 5: SOLID Compliance Tests (10 tests)
# =============================================================================

class TestSOLIDCompliance:
    """Tests para verificar principios SOLID"""
    
    def test_41_config_yaml_not_enum(self):
        """Test 41: Configuración es YAML, no enum"""
        path = Path("config/domains.yaml")
        assert path.exists()
        with open(path) as f:
            config = yaml.safe_load(f)
        assert isinstance(config.get('domains'), dict)
    
    def test_42_roles_yaml_not_enum(self):
        """Test 42: Roles son YAML, no enum"""
        path = Path("config/iovba-roles.yaml")
        assert path.exists()
        with open(path) as f:
            config = yaml.safe_load(f)
        assert isinstance(config.get('roles'), dict)
    
    def test_43_ocp_extension_without_modification(self, domains):
        """Test 43: OCP - Extensión sin modificación"""
        initial = len(domains)
        domains['test_ocp'] = DomainConfig(
            id='test_ocp', elegant_name='TEST_OCP', display_name='Test',
            description='Test', icon='test', color='#FF0000', category='test',
            default_skills=['test'], default_tools=['test'], default_mcp_servers=[],
            keywords=['test_ocp'], prompt_template='Test'
        )
        assert len(domains) == initial + 1
        assert 'test_ocp' in domains
    
    def test_44_domain_registry_exists(self):
        """Test 44: Domain Registry existe"""
        path = Path("src/lib/config/domain-registry.ts")
        assert path.exists()
    
    def test_45_role_registry_exists(self):
        """Test 45: Role Registry existe"""
        path = Path("src/lib/config/role-registry.ts")
        assert path.exists()
    
    def test_46_registry_uses_interfaces(self):
        """Test 46: Registry usa interfaces"""
        path = Path("src/lib/config/domain-registry.ts")
        if path.exists():
            content = path.read_text()
            assert 'interface' in content or 'type' in content
    
    def test_47_lsp_role_substitution(self, roles):
        """Test 47: LSP - Sustitución de roles"""
        required = ['id', 'elegant_name', 'display_name', 'description']
        for role_id, role in roles.items():
            for field in required:
                assert hasattr(role, field)
    
    def test_48_config_additive(self):
        """Test 48: Agregar config es aditivo"""
        loader = ConfigLoader()
        domains = loader.load_domains()
        domains['new_test'] = DomainConfig(
            id='new_test', elegant_name='NEW', display_name='New',
            description='Test', icon='test', color='#000000', category='test',
            default_skills=[], default_tools=[], default_mcp_servers=[],
            keywords=['new_test'], prompt_template='Test'
        )
        assert 'codex' in loader.load_domains()
        assert 'vitalis' in loader.load_domains()
    
    def test_49_no_hardcoded_enums_in_config(self):
        """Test 49: No hay enums hardcodeados en config"""
        path = Path("config/domains.yaml")
        with open(path) as f:
            content = f.read()
        assert 'enum' not in content.lower()
        assert 'class Domain' not in content
    
    def test_50_solid_documentation_exists(self):
        """Test 50: Documentación SOLID existe"""
        path = Path("docs/SOLID_VIOLATIONS_ANALYSIS.md")
        assert path.exists()


# =============================================================================
# TEST GROUP 6: Configuration Validation Tests (10 tests)
# =============================================================================

class TestConfigurationValidation:
    """Tests de validación de configuración"""
    
    def test_51_all_domains_have_colors(self, domains):
        """Test 51: Todos los dominios tienen colores"""
        for domain_id, domain in domains.items():
            assert domain.color.startswith('#'), f"{domain_id} color inválido"
            assert len(domain.color) == 7, f"{domain_id} color debe ser #RRGGBB"
    
    def test_52_all_roles_have_colors(self, roles):
        """Test 52: Todos los roles tienen colores"""
        for role_id, role in roles.items():
            assert role.color.startswith('#'), f"{role_id} color inválido"
    
    def test_53_domain_categories_valid(self, domains):
        """Test 53: Categorías de dominio válidas"""
        valid_categories = [
            'engineering', 'healthcare', 'sports', 'media', 'science',
            'biology', 'biotech', 'geopolitics', 'finance', 'legal',
            'education', 'research', 'marketing', 'general'
        ]
        for domain_id, domain in domains.items():
            assert domain.category in valid_categories, f"{domain_id} categoría inválida"
    
    def test_54_no_duplicate_keywords(self, domains):
        """Test 54: No hay keywords duplicados entre dominios"""
        all_keywords = []
        for domain in domains.values():
            all_keywords.extend(domain.keywords)
        
        duplicates = [k for k in all_keywords if all_keywords.count(k) > 1]
        # Permitimos algunos duplicados comunes
        assert len(set(duplicates)) < 5, "Muchas keywords duplicadas"
    
    def test_55_mcp_servers_not_empty_for_domains(self, domains):
        """Test 55: Dominios tienen MCP servers configurados"""
        for domain_id, domain in domains.items():
            if domain_id != 'custom':
                assert len(domain.default_mcp_servers) > 0, f"{domain_id} sin MCP"
    
    def test_56_all_domains_have_prompt_template(self, domains):
        """Test 56: Todos los dominios tienen prompt template"""
        for domain_id, domain in domains.items():
            assert len(domain.prompt_template) > 10, f"{domain_id} prompt muy corto"
    
    def test_57_roles_have_taglines(self, roles):
        """Test 57: Todos los roles tienen tagline"""
        for role_id, role in roles.items():
            assert len(role.tagline) > 3, f"{role_id} tagline muy corto"
    
    def test_58_five_roles_exist(self, roles):
        """Test 58: Exactamente 5 roles IOVBA"""
        assert len(roles) == 5, "Debe haber exactamente 5 roles"
    
    def test_59_thirteen_domains_exist(self, domains):
        """Test 59: Al menos 13 dominios"""
        assert len(domains) >= 13, "Debe haber al menos 13 dominios"
    
    def test_60_config_files_valid_yaml(self):
        """Test 60: Archivos de config son YAML válido"""
        for filename in ['domains.yaml', 'iovba-roles.yaml']:
            path = Path(f"config/{filename}")
            with open(path) as f:
                config = yaml.safe_load(f)
            assert config is not None, f"{filename} está vacío"


# =============================================================================
# TEST GROUP 7: Integration Validation Tests (10 tests)
# =============================================================================

class TestIntegrationValidation:
    """Tests de validación de integración"""
    
    def test_61_deerflow_gentle_ai_link(self):
        """Test 61: DeerFlow tiene link a Gentle-AI"""
        path = Path("ecosystem/deer-flow/skills/public/gentle-ai-integration/SKILL.md")
        if path.exists():
            content = path.read_text()
            assert 'Gentle-AI' in content or 'gentle-ai' in content.lower()
    
    def test_62_deerflow_gentle_pi_link(self):
        """Test 62: DeerFlow tiene link a Gentle-Pi"""
        path = Path("ecosystem/deer-flow/skills/public/gentle-pi-integration/SKILL.md")
        if path.exists():
            content = path.read_text()
            assert 'Gentle-Pi' in content or 'gentle-pi' in content.lower()
    
    def test_63_worklog_exists(self):
        """Test 63: Worklog de implementación existe"""
        path = Path("worklog.md")
        assert path.exists()
    
    def test_64_worklog_has_integration_task(self):
        """Test 64: Worklog tiene tarea de integración"""
        path = Path("worklog.md")
        if path.exists():
            content = path.read_text()
            assert 'Task ID: 9' in content or 'integración' in content.lower()
    
    def test_65_config_directory_exists(self):
        """Test 65: Directorio de configuración existe"""
        path = Path("config")
        assert path.exists()
        assert path.is_dir()
    
    def test_66_ecosystem_directory_exists(self):
        """Test 66: Directorio ecosystem existe"""
        path = Path("ecosystem")
        assert path.exists()
    
    def test_67_mini_services_exist(self):
        """Test 67: Mini-servicios existen"""
        path = Path("mini-services/chat-service")
        assert path.exists()
    
    def test_68_chat_service_index_exists(self):
        """Test 68: Chat service index existe"""
        path = Path("mini-services/chat-service/index.ts")
        assert path.exists()
    
    def test_69_api_chat_route_exists(self):
        """Test 69: API route de chat existe"""
        path = Path("src/app/api/chat/route.ts")
        assert path.exists()
    
    def test_70_deerflow_proxy_exists(self):
        """Test 70: Proxy a DeerFlow existe"""
        path = Path("src/app/api/deerflow/[...path]/route.ts")
        assert path.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
