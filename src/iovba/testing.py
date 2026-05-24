"""
NEXUS - Neural Execution Unified System
Sistema de Testing para Grupos IOVBA

Tests en caliente para validar el funcionamiento de cada grupo IOVBA.
Incluye diferentes niveles de complejidad: Basic, Intermediate, Advanced, Expert, Master
"""

from typing import Dict, List, Optional, Any, Literal, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import uuid
import re
import json
import time
from concurrent.futures import ThreadPoolExecutor

# Import from groups module
from .groups import (
    IOVBAGroup, IOVBARole, IOVBADomain, DOMAIN_BRANDING,
    AgentProfile, CognitiveCapital, Engram
)


# ============================================
# TEST LEVELS
# ============================================

class TestLevel(str, Enum):
    BASIC = "basic"           # Funcionalidad básica
    INTERMEDIATE = "intermediate"  # Casos de uso comunes
    ADVANCED = "advanced"     # Escenarios complejos
    EXPERT = "expert"         # Edge cases y estrés
    MASTER = "master"         # Integración completa y performance


# ============================================
# VALIDATION TYPES
# ============================================

class ValidationType(str, Enum):
    EXACT = "exact"           # Coincidencia exacta
    CONTAINS = "contains"     # Contiene substring
    REGEX = "regex"           # Expresión regular
    SEMANTIC = "semantic"     # Similitud semántica
    CUSTOM = "custom"         # Función personalizada
    THRESHOLD = "threshold"   # Umbral numérico
    SCHEMA = "schema"         # Validación de esquema


@dataclass
class ValidationRule:
    """Regla de validación para un test"""
    type: ValidationType
    field: str
    value: Any
    weight: float = 1.0
    message: str = ""
    
    def validate(self, output: Dict[str, Any]) -> tuple[bool, float, str]:
        """Ejecuta la validación"""
        actual = output.get(self.field)
        
        if self.type == ValidationType.EXACT:
            passed = actual == self.value
            return passed, self.weight if passed else 0, f"Expected {self.value}, got {actual}"
        
        elif self.type == ValidationType.CONTAINS:
            if isinstance(actual, str) and isinstance(self.value, str):
                passed = self.value in actual
                return passed, self.weight if passed else 0, f"'{self.value}' {'found' if passed else 'not found'}"
            return False, 0, "Invalid types for contains validation"
        
        elif self.type == ValidationType.REGEX:
            if isinstance(actual, str):
                pattern = re.compile(self.value) if isinstance(self.value, str) else self.value
                passed = bool(pattern.search(actual))
                return passed, self.weight if passed else 0, f"Regex {'matched' if passed else 'not matched'}"
            return False, 0, "Invalid type for regex validation"
        
        elif self.type == ValidationType.THRESHOLD:
            if isinstance(actual, (int, float)) and isinstance(self.value, (int, float)):
                passed = actual >= self.value
                return passed, self.weight if passed else 0, f"{actual} {'>=' if passed else '<'} {self.value}"
            return False, 0, "Invalid types for threshold validation"
        
        elif self.type == ValidationType.SCHEMA:
            # Validación de esquema JSON
            required_fields = self.value if isinstance(self.value, list) else []
            passed = all(f in output for f in required_fields)
            return passed, self.weight if passed else 0, f"Schema validation {'passed' if passed else 'failed'}"
        
        return False, 0, f"Unknown validation type: {self.type}"


@dataclass
class IOVBATestCase:
    """Caso de test para un grupo IOVBA"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: str = ""
    level: TestLevel = TestLevel.BASIC
    domain: Optional[IOVBADomain] = None
    role: Optional[IOVBARole] = None  # Si es None, testea todo el grupo
    input_data: Dict[str, Any] = field(default_factory=dict)
    expected_output: Dict[str, Any] = field(default_factory=dict)
    validation_rules: List[ValidationRule] = field(default_factory=list)
    timeout_ms: int = 30000  # 30 segundos por defecto
    tags: List[str] = field(default_factory=list)
    setup_fn: Optional[Callable] = None
    teardown_fn: Optional[Callable] = None


@dataclass
class IOVBATestResult:
    """Resultado de un test"""
    test_id: str
    test_name: str
    group_id: str
    agent_role: Optional[IOVBARole]
    passed: bool
    score: float
    max_score: float
    execution_time_ms: float
    output: Dict[str, Any]
    validation_results: List[Dict[str, Any]]
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class IOVBATestSuite:
    """Suite de tests para un dominio"""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: str = ""
    domain: Optional[IOVBADomain] = None
    level: TestLevel = TestLevel.BASIC
    test_cases: List[IOVBATestCase] = field(default_factory=list)
    
    @property
    def total_tests(self) -> int:
        return len(self.test_cases)
    
    @property
    def estimated_duration_ms(self) -> int:
        return sum(tc.timeout_ms for tc in self.test_cases)


@dataclass
class IOVBATestReport:
    """Reporte completo de tests"""
    suite_id: str
    suite_name: str
    group_id: str
    domain: IOVBADomain
    elegant_name: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    score: float
    max_score: float
    level_achieved: TestLevel
    execution_time_ms: float
    results: List[IOVBATestResult]
    recommendations: List[str]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    @property
    def success_rate(self) -> float:
        return self.passed / self.total_tests if self.total_tests > 0 else 0.0


# ============================================
# TEST POOLS BY DOMAIN
# ============================================

class IOVBATestPool:
    """
    Pool de tests para cada dominio IOVBA
    Genera tests específicos para cada grupo según su dominio
    """
    
    def __init__(self):
        self.test_suites: Dict[IOVBADomain, List[IOVBATestSuite]] = self._init_test_pools()
    
    def _init_test_pools(self) -> Dict[IOVBADomain, List[IOVBATestSuite]]:
        """Inicializa los pools de tests para cada dominio"""
        return {
            "swe": self._create_swe_tests(),
            "salud": self._create_salud_tests(),
            "deportes": self._create_deportes_tests(),
            "noticias": self._create_noticias_tests(),
            "quimica": self._create_quimica_tests(),
            "biologia": self._create_biologia_tests(),
            "biotecnologia": self._create_biotecnologia_tests(),
            "geopolitica": self._create_geopolitica_tests(),
            "finanzas": self._create_finanzas_tests(),
            "legal": self._create_legal_tests(),
            "educacion": self._create_educacion_tests(),
            "investigacion": self._create_investigacion_tests(),
            "marketing": self._create_marketing_tests(),
            "custom": self._create_custom_tests(),
        }
    
    # ============================================
    # SWE (CODEX) TESTS
    # ============================================
    
    def _create_swe_tests(self) -> List[IOVBATestSuite]:
        """Tests para Software Engineering (CODEX)"""
        return [
            # BASIC
            IOVBATestSuite(
                name="CODEX Basic Operations",
                description="Tests básicos de ingeniería de software",
                domain="swe",
                level=TestLevel.BASIC,
                test_cases=[
                    IOVBATestCase(
                        name="Code Review Detection",
                        description="Detectar problemas en código simple",
                        level=TestLevel.BASIC,
                        domain="swe",
                        role="validador",
                        input_data={
                            "code": "def add(a, b):\n    return a + b",
                            "language": "python"
                        },
                        validation_rules=[
                            ValidationRule(ValidationType.SCHEMA, "analysis", ["issues", "suggestions"]),
                            ValidationRule(ValidationType.THRESHOLD, "issues_count", 0),
                        ],
                        tags=["code-review", "python", "basic"]
                    ),
                    IOVBATestCase(
                        name="Documentation Generation",
                        description="Generar documentación para función",
                        level=TestLevel.BASIC,
                        domain="swe",
                        role="builder",
                        input_data={
                            "code": "def calculate_discount(price, rate):\n    return price * (1 - rate)",
                            "language": "python"
                        },
                        validation_rules=[
                            ValidationRule(ValidationType.CONTAINS, "documentation", "calculate_discount"),
                            ValidationRule(ValidationType.CONTAINS, "documentation", "price"),
                        ],
                        tags=["documentation", "python", "basic"]
                    ),
                    IOVBATestCase(
                        name="Simple Bug Analysis",
                        description="Analizar y explicar un bug simple",
                        level=TestLevel.BASIC,
                        domain="swe",
                        role="investigador",
                        input_data={
                            "error": "TypeError: 'NoneType' object is not iterable",
                            "context": "for item in get_items():"
                        },
                        validation_rules=[
                            ValidationRule(ValidationType.CONTAINS, "analysis", "None"),
                            ValidationRule(ValidationType.CONTAINS, "solution", "check"),
                        ],
                        tags=["debugging", "error-analysis", "basic"]
                    ),
                ]
            ),
            # INTERMEDIATE
            IOVBATestSuite(
                name="CODEX Integration Tests",
                description="Tests de integración y funcionalidad completa",
                domain="swe",
                level=TestLevel.INTERMEDIATE,
                test_cases=[
                    IOVBATestCase(
                        name="API Design Review",
                        description="Diseñar y validar API REST",
                        level=TestLevel.INTERMEDIATE,
                        domain="swe",
                        input_data={
                            "requirements": "API para gestión de usuarios con CRUD",
                            "constraints": ["REST", "JSON", "Authentication"]
                        },
                        validation_rules=[
                            ValidationRule(ValidationType.SCHEMA, "endpoints", ["create", "read", "update", "delete"]),
                            ValidationRule(ValidationType.THRESHOLD, "endpoints_count", 4),
                        ],
                        tags=["api", "rest", "design"],
                        timeout_ms=45000
                    ),
                    IOVBATestCase(
                        name="Code Refactoring",
                        description="Refactorizar código legacy",
                        level=TestLevel.INTERMEDIATE,
                        domain="swe",
                        role="builder",
                        input_data={
                            "code": "def process(d):\n    r=[]\n    for i in d:\n        if i>0:r.append(i*2)\n    return r",
                            "goals": ["readability", "type-hints", "documentation"]
                        },
                        validation_rules=[
                            ValidationRule(ValidationType.CONTAINS, "refactored", "def "),
                            ValidationRule(ValidationType.CONTAINS, "refactored", "List"),
                        ],
                        tags=["refactoring", "python", "clean-code"]
                    ),
                ]
            ),
            # ADVANCED
            IOVBATestSuite(
                name="CODEX Architecture Tests",
                description="Tests de arquitectura y diseño de sistemas",
                domain="swe",
                level=TestLevel.ADVANCED,
                test_cases=[
                    IOVBATestCase(
                        name="Microservices Design",
                        description="Diseñar arquitectura de microservicios",
                        level=TestLevel.ADVANCED,
                        domain="swe",
                        input_data={
                            "system": "E-commerce platform",
                            "requirements": ["scalability", "fault-tolerance", "event-driven"]
                        },
                        validation_rules=[
                            ValidationRule(ValidationType.THRESHOLD, "services_count", 3),
                            ValidationRule(ValidationType.CONTAINS, "architecture", "service"),
                        ],
                        tags=["architecture", "microservices", "design"],
                        timeout_ms=60000
                    ),
                    IOVBATestCase(
                        name="Performance Optimization",
                        description="Optimizar algoritmo ineficiente",
                        level=TestLevel.ADVANCED,
                        domain="swe",
                        role="builder",
                        input_data={
                            "code": "def find_duplicates(arr):\n    result = []\n    for i in range(len(arr)):\n        for j in range(i+1, len(arr)):\n            if arr[i] == arr[j] and arr[i] not in result:\n                result.append(arr[i])\n    return result",
                            "constraints": ["O(n)", "memory-efficient"]
                        },
                        validation_rules=[
                            ValidationRule(ValidationType.CONTAINS, "optimized", "set"),
                            ValidationRule(ValidationType.REGEX, "complexity", r"O\(n\)"),
                        ],
                        tags=["optimization", "algorithms", "performance"]
                    ),
                ]
            ),
            # EXPERT
            IOVBATestSuite(
                name="CODEX Expert Challenges",
                description="Desafíos de nivel experto",
                domain="swe",
                level=TestLevel.EXPERT,
                test_cases=[
                    IOVBATestCase(
                        name="Distributed System Design",
                        description="Diseñar sistema distribuido complejo",
                        level=TestLevel.EXPERT,
                        domain="swe",
                        input_data={
                            "requirements": "Global distributed cache with consistency guarantees",
                            "constraints": ["CAP theorem", "eventual consistency", "partition tolerance"]
                        },
                        validation_rules=[
                            ValidationRule(ValidationType.THRESHOLD, "components_count", 4),
                            ValidationRule(ValidationType.CONTAINS, "consensus", "raft"),
                        ],
                        tags=["distributed", "consensus", "caching"],
                        timeout_ms=90000
                    ),
                ]
            ),
            # MASTER
            IOVBATestSuite(
                name="CODEX Master Integration",
                description="Integración completa del grupo CODEX",
                domain="swe",
                level=TestLevel.MASTER,
                test_cases=[
                    IOVBATestCase(
                        name="Full Stack Development Pipeline",
                        description="Pipeline completo de desarrollo con todos los roles",
                        level=TestLevel.MASTER,
                        domain="swe",
                        input_data={
                            "project": "Real-time collaborative code editor",
                            "tech_stack": ["React", "Node.js", "WebSocket", "Redis"],
                            "timeline": "2 weeks"
                        },
                        validation_rules=[
                            ValidationRule(ValidationType.SCHEMA, "deliverables", ["frontend", "backend", "tests", "docs"]),
                            ValidationRule(ValidationType.THRESHOLD, "test_coverage", 80),
                            ValidationRule(ValidationType.THRESHOLD, "performance_score", 85),
                        ],
                        tags=["full-stack", "real-time", "collaboration"],
                        timeout_ms=120000
                    ),
                ]
            ),
        ]
    
    # ============================================
    # SALUD (VITALIS) TESTS
    # ============================================
    
    def _create_salud_tests(self) -> List[IOVBATestSuite]:
        """Tests para Salud y Medicina (VITALIS)"""
        return [
            IOVBATestSuite(
                name="VITALIS Basic Diagnostics",
                description="Tests básicos de diagnóstico médico",
                domain="salud",
                level=TestLevel.BASIC,
                test_cases=[
                    IOVBATestCase(
                        name="Symptom Analysis",
                        description="Analizar síntomas básicos",
                        level=TestLevel.BASIC,
                        domain="salud",
                        role="investigador",
                        input_data={
                            "symptoms": ["fiebre", "tos", "dolor de garganta"],
                            "patient_age": 35
                        },
                        validation_rules=[
                            ValidationRule(ValidationType.SCHEMA, "conditions", ["possible", "recommended_tests"]),
                            ValidationRule(ValidationType.THRESHOLD, "confidence", 0.5),
                        ],
                        tags=["diagnosis", "symptoms", "basic"],
                        timeout_ms=20000
                    ),
                    IOVBATestCase(
                        name="Medication Interaction Check",
                        description="Verificar interacciones medicamentosas",
                        level=TestLevel.BASIC,
                        domain="salud",
                        role="validador",
                        input_data={
                            "medications": ["ibuprofeno", "aspirina"],
                            "patient_conditions": ["gastritis"]
                        },
                        validation_rules=[
                            ValidationRule(ValidationType.SCHEMA, "interactions", ["severity", "description"]),
                        ],
                        tags=["medication", "interactions", "safety"]
                    ),
                ]
            ),
            IOVBATestSuite(
                name="VITALIS Clinical Analysis",
                description="Análisis clínico avanzado",
                domain="salud",
                level=TestLevel.INTERMEDIATE,
                test_cases=[
                    IOVBATestCase(
                        name="Lab Results Interpretation",
                        description="Interpretar resultados de laboratorio",
                        level=TestLevel.INTERMEDIATE,
                        domain="salud",
                        role="observador",
                        input_data={
                            "results": {
                                "glucose": 145,
                                "hba1c": 7.2,
                                "cholesterol": 220
                            },
                            "reference_ranges": {
                                "glucose": [70, 100],
                                "hba1c": [4, 5.6],
                                "cholesterol": [0, 200]
                            }
                        },
                        validation_rules=[
                            ValidationRule(ValidationType.CONTAINS, "analysis", "elevated"),
                            ValidationRule(ValidationType.CONTAINS, "recommendations", "diabetes"),
                        ],
                        tags=["lab", "diagnosis", "metabolic"]
                    ),
                ]
            ),
            IOVBATestSuite(
                name="VITALIS Advanced Diagnostics",
                description="Diagnósticos avanzados",
                domain="salud",
                level=TestLevel.ADVANCED,
                test_cases=[
                    IOVBATestCase(
                        name="Differential Diagnosis",
                        description="Diagnóstico diferencial complejo",
                        level=TestLevel.ADVANCED,
                        domain="salud",
                        input_data={
                            "symptoms": ["chest pain", "shortness of breath", "fatigue"],
                            "history": ["hypertension", "smoker"],
                            "age": 58
                        },
                        validation_rules=[
                            ValidationRule(ValidationType.THRESHOLD, "differential_count", 3),
                            ValidationRule(ValidationType.CONTAINS, "urgent_considerations", "cardiac"),
                        ],
                        tags=["differential", "cardiac", "emergency"],
                        timeout_ms=45000
                    ),
                ]
            ),
        ]
    
    # ============================================
    # DEPORTES (ATHLON) TESTS
    # ============================================
    
    def _create_deportes_tests(self) -> List[IOVBATestSuite]:
        """Tests para Deportes (ATHLON)"""
        return [
            IOVBATestSuite(
                name="ATHLON Performance Analysis",
                description="Análisis de rendimiento deportivo",
                domain="deportes",
                level=TestLevel.BASIC,
                test_cases=[
                    IOVBATestCase(
                        name="Player Stats Analysis",
                        description="Analizar estadísticas de jugador",
                        level=TestLevel.BASIC,
                        domain="deportes",
                        role="observador",
                        input_data={
                            "player": "Forward",
                            "stats": {"goals": 15, "assists": 8, "minutes_played": 2100},
                            "league_avg": {"goals": 10, "assists": 5}
                        },
                        validation_rules=[
                            ValidationRule(ValidationType.SCHEMA, "analysis", ["performance_rating", "strengths"]),
                            ValidationRule(ValidationType.THRESHOLD, "performance_rating", 70),
                        ],
                        tags=["stats", "analysis", "player"]
                    ),
                    IOVBATestCase(
                        name="Training Plan Generation",
                        description="Generar plan de entrenamiento",
                        level=TestLevel.BASIC,
                        domain="deportes",
                        role="builder",
                        input_data={
                            "sport": "marathon",
                            "level": "intermediate",
                            "goal": "finish under 4 hours"
                        },
                        validation_rules=[
                            ValidationRule(ValidationType.CONTAINS, "plan", "week"),
                            ValidationRule(ValidationType.CONTAINS, "plan", "run"),
                        ],
                        tags=["training", "plan", "endurance"]
                    ),
                ]
            ),
            IOVBATestSuite(
                name="ATHLON Advanced Analytics",
                description="Analytics avanzados deportivos",
                domain="deportes",
                level=TestLevel.ADVANCED,
                test_cases=[
                    IOVBATestCase(
                        name="Match Prediction",
                        description="Predicción de resultado",
                        level=TestLevel.ADVANCED,
                        domain="deportes",
                        input_data={
                            "team_a": {"wins": 12, "draws": 5, "losses": 3, "goals_for": 35},
                            "team_b": {"wins": 8, "draws": 7, "losses": 5, "goals_for": 28},
                            "venue": "team_a_home"
                        },
                        validation_rules=[
                            ValidationRule(ValidationType.SCHEMA, "prediction", ["probabilities", "analysis"]),
                            ValidationRule(ValidationType.THRESHOLD, "confidence", 0.6),
                        ],
                        tags=["prediction", "match", "probability"]
                    ),
                ]
            ),
        ]
    
    # ============================================
    # NOTICIAS (VERITAS) TESTS
    # ============================================
    
    def _create_noticias_tests(self) -> List[IOVBATestSuite]:
        """Tests para Noticias y Periodismo (VERITAS)"""
        return [
            IOVBATestSuite(
                name="VERITAS Fact Checking",
                description="Verificación de hechos y noticias",
                domain="noticias",
                level=TestLevel.BASIC,
                test_cases=[
                    IOVBATestCase(
                        name="Claim Verification",
                        description="Verificar afirmación factual",
                        level=TestLevel.BASIC,
                        domain="noticias",
                        role="validador",
                        input_data={
                            "claim": "The Earth is approximately 4.5 billion years old",
                            "context": "science"
                        },
                        validation_rules=[
                            ValidationRule(ValidationType.SCHEMA, "verification", ["verdict", "sources"]),
                            ValidationRule(ValidationType.CONTAINS, "verdict", "true"),
                        ],
                        tags=["fact-check", "science", "verification"]
                    ),
                    IOVBATestCase(
                        name="Source Credibility Analysis",
                        description="Analizar credibilidad de fuente",
                        level=TestLevel.BASIC,
                        domain="noticias",
                        role="investigador",
                        input_data={
                            "source": "Example News Site",
                            "article": "Breaking: Scientists discover..."
                        },
                        validation_rules=[
                            ValidationRule(ValidationType.SCHEMA, "credibility", ["score", "factors"]),
                            ValidationRule(ValidationType.THRESHOLD, "credibility_score", 0),
                        ],
                        tags=["source", "credibility", "analysis"]
                    ),
                ]
            ),
            IOVBATestSuite(
                name="VERITAS Deep Investigation",
                description="Investigación periodística profunda",
                domain="noticias",
                level=TestLevel.ADVANCED,
                test_cases=[
                    IOVBATestCase(
                        name="Cross-Reference Multiple Sources",
                        description="Cruzar información de múltiples fuentes",
                        level=TestLevel.ADVANCED,
                        domain="noticias",
                        input_data={
                            "event": "Policy announcement",
                            "sources": [
                                {"type": "official", "content": "..."},
                                {"type": "news", "content": "..."},
                                {"type": "social", "content": "..."}
                            ]
                        },
                        validation_rules=[
                            ValidationRule(ValidationType.THRESHOLD, "source_count", 3),
                            ValidationRule(ValidationType.SCHEMA, "synthesis", ["key_facts", "contradictions"]),
                        ],
                        tags=["investigation", "sources", "synthesis"]
                    ),
                ]
            ),
        ]
    
    # ============================================
    # FINANZAS (APEX) TESTS
    # ============================================
    
    def _create_finanzas_tests(self) -> List[IOVBATestSuite]:
        """Tests para Finanzas (APEX)"""
        return [
            IOVBATestSuite(
                name="APEX Financial Analysis",
                description="Análisis financiero básico",
                domain="finanzas",
                level=TestLevel.BASIC,
                test_cases=[
                    IOVBATestCase(
                        name="Portfolio Analysis",
                        description="Analizar cartera de inversiones",
                        level=TestLevel.BASIC,
                        domain="finanzas",
                        role="observador",
                        input_data={
                            "portfolio": [
                                {"symbol": "AAPL", "shares": 100, "buy_price": 150},
                                {"symbol": "GOOGL", "shares": 50, "buy_price": 2800}
                            ],
                            "current_prices": {"AAPL": 175, "GOOGL": 3000}
                        },
                        validation_rules=[
                            ValidationRule(ValidationType.SCHEMA, "analysis", ["total_value", "total_gain_loss"]),
                            ValidationRule(ValidationType.THRESHOLD, "total_value", 0),
                        ],
                        tags=["portfolio", "analysis", "stocks"]
                    ),
                    IOVBATestCase(
                        name="Risk Assessment",
                        description="Evaluar perfil de riesgo",
                        level=TestLevel.BASIC,
                        domain="finanzas",
                        role="validador",
                        input_data={
                            "age": 35,
                            "income": 75000,
                            "investment_horizon": "long-term",
                            "risk_tolerance": "moderate"
                        },
                        validation_rules=[
                            ValidationRule(ValidationType.SCHEMA, "assessment", ["risk_profile", "recommended_allocation"]),
                            ValidationRule(ValidationType.CONTAINS, "risk_profile", "moderate"),
                        ],
                        tags=["risk", "profile", "assessment"]
                    ),
                ]
            ),
            IOVBATestSuite(
                name="APEX Market Analysis",
                description="Análisis de mercado avanzado",
                domain="finanzas",
                level=TestLevel.ADVANCED,
                test_cases=[
                    IOVBATestCase(
                        name="Market Trend Prediction",
                        description="Predecir tendencia de mercado",
                        level=TestLevel.ADVANCED,
                        domain="finanzas",
                        input_data={
                            "symbol": "SPY",
                            "historical_data": [{"date": "2024-01", "close": 470}, {"date": "2024-02", "close": 485}],
                            "indicators": ["RSI", "MACD", "MA50"]
                        },
                        validation_rules=[
                            ValidationRule(ValidationType.SCHEMA, "prediction", ["trend", "confidence", "signals"]),
                            ValidationRule(ValidationType.THRESHOLD, "confidence", 0.5),
                        ],
                        tags=["market", "prediction", "technical"]
                    ),
                ]
            ),
        ]
    
    # ============================================
    # LEGAL (JUSTITIA) TESTS
    # ============================================
    
    def _create_legal_tests(self) -> List[IOVBATestSuite]:
        """Tests para Legal (JUSTITIA)"""
        return [
            IOVBATestSuite(
                name="JUSTITIA Legal Analysis",
                description="Análisis legal básico",
                domain="legal",
                level=TestLevel.BASIC,
                test_cases=[
                    IOVBATestCase(
                        name="Contract Review",
                        description="Revisar cláusulas contractuales",
                        level=TestLevel.BASIC,
                        domain="legal",
                        role="validador",
                        input_data={
                            "contract_type": "employment",
                            "clauses": ["non-compete", "confidentiality", "termination"],
                            "jurisdiction": "US"
                        },
                        validation_rules=[
                            ValidationRule(ValidationType.SCHEMA, "review", ["issues", "recommendations"]),
                            ValidationRule(ValidationType.THRESHOLD, "completeness", 0.8),
                        ],
                        tags=["contract", "review", "employment"]
                    ),
                    IOVBATestCase(
                        name="Legal Research",
                        description="Investigar jurisprudencia",
                        level=TestLevel.BASIC,
                        domain="legal",
                        role="investigador",
                        input_data={
                            "issue": "intellectual property infringement",
                            "jurisdiction": "US Federal",
                            "relevant_statutes": ["Copyright Act"]
                        },
                        validation_rules=[
                            ValidationRule(ValidationType.SCHEMA, "research", ["relevant_cases", "analysis"]),
                            ValidationRule(ValidationType.THRESHOLD, "case_count", 1),
                        ],
                        tags=["research", "jurisprudence", "IP"]
                    ),
                ]
            ),
        ]
    
    # ============================================
    # EDUCACION (MENTOR) TESTS
    # ============================================
    
    def _create_educacion_tests(self) -> List[IOVBATestSuite]:
        """Tests para Educación (MENTOR)"""
        return [
            IOVBATestSuite(
                name="MENTOR Educational Tests",
                description="Tests educativos básicos",
                domain="educacion",
                level=TestLevel.BASIC,
                test_cases=[
                    IOVBATestCase(
                        name="Lesson Plan Creation",
                        description="Crear plan de lección",
                        level=TestLevel.BASIC,
                        domain="educacion",
                        role="builder",
                        input_data={
                            "subject": "Mathematics",
                            "topic": "Quadratic Equations",
                            "grade_level": 10,
                            "duration": "45 minutes"
                        },
                        validation_rules=[
                            ValidationRule(ValidationType.SCHEMA, "lesson_plan", ["objectives", "activities", "assessment"]),
                            ValidationRule(ValidationType.CONTAINS, "objectives", "quadratic"),
                        ],
                        tags=["lesson", "plan", "mathematics"]
                    ),
                    IOVBATestCase(
                        name="Student Progress Analysis",
                        description="Analizar progreso estudiantil",
                        level=TestLevel.BASIC,
                        domain="educacion",
                        role="observador",
                        input_data={
                            "student_id": "STU001",
                            "grades": [85, 78, 92, 88, 75],
                            "subjects": ["Math", "Science", "History", "English", "Art"]
                        },
                        validation_rules=[
                            ValidationRule(ValidationType.SCHEMA, "analysis", ["average", "trend", "recommendations"]),
                            ValidationRule(ValidationType.THRESHOLD, "average", 70),
                        ],
                        tags=["student", "progress", "analysis"]
                    ),
                ]
            ),
        ]
    
    # ============================================
    # QUIMICA (ALCHEMY) TESTS
    # ============================================
    
    def _create_quimica_tests(self) -> List[IOVBATestSuite]:
        """Tests para Química (ALCHEMY)"""
        return [
            IOVBATestSuite(
                name="ALCHEMY Chemistry Tests",
                description="Tests de química básica",
                domain="quimica",
                level=TestLevel.BASIC,
                test_cases=[
                    IOVBATestCase(
                        name="Molecular Analysis",
                        description="Analizar estructura molecular",
                        level=TestLevel.BASIC,
                        domain="quimica",
                        role="investigador",
                        input_data={
                            "compound": "C6H12O6",
                            "analysis_type": "structure"
                        },
                        validation_rules=[
                            ValidationRule(ValidationType.CONTAINS, "analysis", "glucose"),
                            ValidationRule(ValidationType.SCHEMA, "properties", ["molecular_weight", "formula"]),
                        ],
                        tags=["molecular", "structure", "organic"]
                    ),
                ]
            ),
        ]
    
    # ============================================
    # BIOLOGIA (GENESIS) TESTS
    # ============================================
    
    def _create_biologia_tests(self) -> List[IOVBATestSuite]:
        """Tests para Biología (GENESIS)"""
        return [
            IOVBATestSuite(
                name="GENESIS Biology Tests",
                description="Tests de biología básica",
                domain="biologia",
                level=TestLevel.BASIC,
                test_cases=[
                    IOVBATestCase(
                        name="Gene Analysis",
                        description="Analizar secuencia génica",
                        level=TestLevel.BASIC,
                        domain="biologia",
                        role="investigador",
                        input_data={
                            "sequence": "ATGCGATCGATCG",
                            "analysis_type": "basic"
                        },
                        validation_rules=[
                            ValidationRule(ValidationType.SCHEMA, "analysis", ["length", "gc_content"]),
                            ValidationRule(ValidationType.THRESHOLD, "length", 10),
                        ],
                        tags=["gene", "sequence", "analysis"]
                    ),
                ]
            ),
        ]
    
    # ============================================
    # BIOTECNOLOGIA (HELIX) TESTS
    # ============================================
    
    def _create_biotecnologia_tests(self) -> List[IOVBATestSuite]:
        """Tests para Biotecnología (HELIX)"""
        return [
            IOVBATestSuite(
                name="HELIX Biotech Tests",
                description="Tests de biotecnología",
                domain="biotecnologia",
                level=TestLevel.BASIC,
                test_cases=[
                    IOVBATestCase(
                        name="Protein Structure Prediction",
                        description="Predecir estructura de proteína",
                        level=TestLevel.BASIC,
                        domain="biotecnologia",
                        role="investigador",
                        input_data={
                            "protein_sequence": "MVLSPADKTNVKAAWGKVGAHAGEYGAEALERMFLSFPTTKTYFPHFDLSHGSAQVKGHGKKVADALTNAVAHVDDMPNALSALSDLHAHKLRVDPVNFKLLSHCLLVTLAAHLPAEFTPAVHASLDKFLASVSTVLTSKYR",
                            "prediction_type": "secondary"
                        },
                        validation_rules=[
                            ValidationRule(ValidationType.SCHEMA, "prediction", ["structure", "confidence"]),
                            ValidationRule(ValidationType.THRESHOLD, "confidence", 0.6),
                        ],
                        tags=["protein", "structure", "prediction"]
                    ),
                ]
            ),
        ]
    
    # ============================================
    # GEOPOLITICA (DIPLOMAT) TESTS
    # ============================================
    
    def _create_geopolitica_tests(self) -> List[IOVBATestSuite]:
        """Tests para Geopolítica (DIPLOMAT)"""
        return [
            IOVBATestSuite(
                name="DIPLOMAT Geopolitical Tests",
                description="Tests de análisis geopolítico",
                domain="geopolitica",
                level=TestLevel.BASIC,
                test_cases=[
                    IOVBATestCase(
                        name="Country Risk Assessment",
                        description="Evaluar riesgo país",
                        level=TestLevel.BASIC,
                        domain="geopolitica",
                        role="observador",
                        input_data={
                            "country": "Example Country",
                            "factors": ["political_stability", "economic_outlook", "security"]
                        },
                        validation_rules=[
                            ValidationRule(ValidationType.SCHEMA, "assessment", ["risk_level", "factors_analysis"]),
                            ValidationRule(ValidationType.THRESHOLD, "confidence", 0.5),
                        ],
                        tags=["risk", "country", "assessment"]
                    ),
                ]
            ),
        ]
    
    # ============================================
    # INVESTIGACION (PIONEER) TESTS
    # ============================================
    
    def _create_investigacion_tests(self) -> List[IOVBATestSuite]:
        """Tests para Investigación (PIONEER)"""
        return [
            IOVBATestSuite(
                name="PIONEER Research Tests",
                description="Tests de investigación científica",
                domain="investigacion",
                level=TestLevel.BASIC,
                test_cases=[
                    IOVBATestCase(
                        name="Literature Review",
                        description="Realizar revisión bibliográfica",
                        level=TestLevel.BASIC,
                        domain="investigacion",
                        role="investigador",
                        input_data={
                            "topic": "Machine Learning in Healthcare",
                            "scope": "recent advances",
                            "max_papers": 10
                        },
                        validation_rules=[
                            ValidationRule(ValidationType.SCHEMA, "review", ["papers", "themes", "gaps"]),
                            ValidationRule(ValidationType.THRESHOLD, "papers_count", 3),
                        ],
                        tags=["literature", "review", "research"]
                    ),
                ]
            ),
        ]
    
    # ============================================
    # MARKETING (PRISMA) TESTS
    # ============================================
    
    def _create_marketing_tests(self) -> List[IOVBATestSuite]:
        """Tests para Marketing (PRISMA)"""
        return [
            IOVBATestSuite(
                name="PRISMA Marketing Tests",
                description="Tests de marketing",
                domain="marketing",
                level=TestLevel.BASIC,
                test_cases=[
                    IOVBATestCase(
                        name="Campaign Strategy",
                        description="Crear estrategia de campaña",
                        level=TestLevel.BASIC,
                        domain="marketing",
                        role="builder",
                        input_data={
                            "product": "SaaS Platform",
                            "target_audience": "Tech startups",
                            "budget": "medium",
                            "goals": ["awareness", "leads"]
                        },
                        validation_rules=[
                            ValidationRule(ValidationType.SCHEMA, "strategy", ["channels", "timeline", "metrics"]),
                            ValidationRule(ValidationType.THRESHOLD, "channels_count", 2),
                        ],
                        tags=["campaign", "strategy", "marketing"]
                    ),
                ]
            ),
        ]
    
    # ============================================
    # CUSTOM TESTS
    # ============================================
    
    def _create_custom_tests(self) -> List[IOVBATestSuite]:
        """Tests para dominios personalizados"""
        return [
            IOVBATestSuite(
                name="Custom Domain Tests",
                description="Tests base para dominios personalizados",
                domain="custom",
                level=TestLevel.BASIC,
                test_cases=[
                    IOVBATestCase(
                        name="Generic Task Processing",
                        description="Procesar tarea genérica",
                        level=TestLevel.BASIC,
                        domain="custom",
                        input_data={
                            "task": "Analyze the provided data",
                            "data": {"key": "value"}
                        },
                        validation_rules=[
                            ValidationRule(ValidationType.SCHEMA, "result", ["status", "output"]),
                        ],
                        tags=["generic", "custom", "basic"]
                    ),
                ]
            ),
        ]
    
    def get_test_suites(self, domain: IOVBADomain, level: Optional[TestLevel] = None) -> List[IOVBATestSuite]:
        """Obtiene suites de test para un dominio"""
        suites = self.test_suites.get(domain, [])
        if level:
            suites = [s for s in suites if s.level == level]
        return suites
    
    def get_all_tests(self, domain: IOVBADomain) -> List[IOVBATestCase]:
        """Obtiene todos los tests de un dominio"""
        suites = self.test_suites.get(domain, [])
        return [tc for suite in suites for tc in suite.test_cases]


# ============================================
# TEST RUNNER
# ============================================

class IOVBATestRunner:
    """
    Ejecutor de tests para grupos IOVBA
    Ejecuta tests en caliente y genera reportes
    """
    
    def __init__(self, test_pool: Optional[IOVBATestPool] = None):
        self.test_pool = test_pool or IOVBATestPool()
    
    async def run_test(
        self,
        test_case: IOVBATestCase,
        group: IOVBAGroup,
        agent_executor: Optional[Callable] = None
    ) -> IOVBATestResult:
        """Ejecuta un test individual"""
        start_time = time.time()
        
        try:
            # Determinar qué agente usar
            if test_case.role:
                agents = group.get_all_agents()
                agent = agents.get(test_case.role)
                if not agent:
                    return IOVBATestResult(
                        test_id=test_case.id,
                        test_name=test_case.name,
                        group_id=group.id,
                        agent_role=test_case.role,
                        passed=False,
                        score=0,
                        max_score=sum(vr.weight for vr in test_case.validation_rules),
                        execution_time_ms=0,
                        output={},
                        validation_results=[],
                        error=f"Agent role {test_case.role} not found"
                    )
            else:
                agent = None  # Test grupal
            
            # Ejecutar test (simulado o con executor real)
            if agent_executor:
                output = await agent_executor(test_case, group, agent)
            else:
                # Simulación de output
                output = self._simulate_output(test_case, group, agent)
            
            # Validar resultados
            validation_results = []
            total_score = 0
            max_score = sum(vr.weight for vr in test_case.validation_rules)
            
            for rule in test_case.validation_rules:
                passed, score, message = rule.validate(output)
                validation_results.append({
                    "type": rule.type.value,
                    "field": rule.field,
                    "passed": passed,
                    "score": score,
                    "max_score": rule.weight,
                    "message": message
                })
                total_score += score
            
            execution_time = (time.time() - start_time) * 1000
            
            return IOVBATestResult(
                test_id=test_case.id,
                test_name=test_case.name,
                group_id=group.id,
                agent_role=test_case.role,
                passed=total_score >= max_score * 0.7,  # 70% threshold
                score=total_score,
                max_score=max_score,
                execution_time_ms=execution_time,
                output=output,
                validation_results=validation_results
            )
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return IOVBATestResult(
                test_id=test_case.id,
                test_name=test_case.name,
                group_id=group.id,
                agent_role=test_case.role,
                passed=False,
                score=0,
                max_score=sum(vr.weight for vr in test_case.validation_rules),
                execution_time_ms=execution_time,
                output={},
                validation_results=[],
                error=str(e)
            )
    
    def _simulate_output(self, test_case: IOVBATestCase, group: IOVBAGroup, agent: Optional[AgentProfile]) -> Dict[str, Any]:
        """Simula output para testing"""
        domain = test_case.domain or group.domain
        role = test_case.role or "group"
        
        # Outputs simulados por dominio
        simulated = {
            "swe": {
                "analysis": {"issues": [], "suggestions": ["Add type hints"]},
                "issues_count": 0,
                "documentation": f"Documentation for {test_case.input_data.get('language', 'code')}",
                "refactored": "def process(data: List[int]) -> List[int]:\n    return [x * 2 for x in data if x > 0]",
                "endpoints": {"create": {}, "read": {}, "update": {}, "delete": {}},
                "endpoints_count": 4,
            },
            "salud": {
                "conditions": {"possible": ["Common cold", "Flu"], "recommended_tests": ["Rapid flu test"]},
                "confidence": 0.75,
                "interactions": {"severity": "moderate", "description": "Increased bleeding risk"},
                "analysis": "Elevated glucose and HbA1c indicate prediabetes",
                "recommendations": ["Monitor blood sugar", "Lifestyle changes"],
            },
            "deportes": {
                "analysis": {"performance_rating": 85, "strengths": ["Goal scoring"]},
                "performance_rating": 85,
                "plan": "Week 1: Base building\nWeek 2: Tempo runs\nWeek 3: Long run",
            },
            "finanzas": {
                "analysis": {"total_value": 33750, "total_gain_loss": 4500},
                "total_value": 33750,
                "assessment": {"risk_profile": "moderate", "recommended_allocation": {"stocks": 60, "bonds": 40}},
                "risk_profile": "moderate",
            },
            "legal": {
                "review": {"issues": ["Non-compete may be unenforceable"], "recommendations": ["Review state law"]},
                "completeness": 0.85,
                "research": {"relevant_cases": ["Case v. Example"], "analysis": "Key precedents identified"},
                "case_count": 2,
            },
            "educacion": {
                "lesson_plan": {"objectives": ["Understand quadratic equations"], "activities": [], "assessment": []},
                "objectives": ["Solve quadratic equations using the quadratic formula"],
                "analysis": {"average": 83.6, "trend": "improving", "recommendations": ["Focus on Science"]},
                "average": 83.6,
            },
            "noticias": {
                "verification": {"verdict": "true", "sources": ["NASA", "Scientific papers"]},
                "verdict": "verified",
                "credibility": {"score": 0.8, "factors": ["Established source"]},
                "credibility_score": 0.8,
            },
        }
        
        return simulated.get(domain, {"status": "completed", "output": {}})
    
    async def run_suite(
        self,
        suite: IOVBATestSuite,
        group: IOVBAGroup,
        agent_executor: Optional[Callable] = None
    ) -> IOVBATestReport:
        """Ejecuta una suite completa de tests"""
        start_time = time.time()
        results = []
        
        for test_case in suite.test_cases:
            result = await self.run_test(test_case, group, agent_executor)
            results.append(result)
        
        execution_time = (time.time() - start_time) * 1000
        
        passed = sum(1 for r in results if r.passed)
        failed = sum(1 for r in results if not r.passed and not r.error)
        skipped = sum(1 for r in results if r.error)
        
        total_score = sum(r.score for r in results)
        max_score = sum(r.max_score for r in results)
        
        # Generar recomendaciones
        recommendations = self._generate_recommendations(results, suite.level)
        
        return IOVBATestReport(
            suite_id=suite.id,
            suite_name=suite.name,
            group_id=group.id,
            domain=group.domain,
            elegant_name=group.elegant_name,
            total_tests=len(results),
            passed=passed,
            failed=failed,
            skipped=skipped,
            score=total_score,
            max_score=max_score,
            level_achieved=suite.level,
            execution_time_ms=execution_time,
            results=results,
            recommendations=recommendations
        )
    
    async def run_all_tests(
        self,
        group: IOVBAGroup,
        levels: Optional[List[TestLevel]] = None,
        agent_executor: Optional[Callable] = None
    ) -> List[IOVBATestReport]:
        """Ejecuta todos los tests para un grupo"""
        reports = []
        suites = self.test_pool.get_test_suites(group.domain)
        
        if levels:
            suites = [s for s in suites if s.level in levels]
        
        for suite in suites:
            report = await self.run_suite(suite, group, agent_executor)
            reports.append(report)
        
        return reports
    
    def _generate_recommendations(self, results: List[IOVBATestResult], level: TestLevel) -> List[str]:
        """Genera recomendaciones basadas en resultados"""
        recommendations = []
        
        failed_tests = [r for r in results if not r.passed]
        if failed_tests:
            recommendations.append(f"Review and fix {len(failed_tests)} failed tests")
        
        slow_tests = [r for r in results if r.execution_time_ms > 5000]
        if slow_tests:
            recommendations.append(f"Optimize {len(slow_tests)} slow tests (>5s)")
        
        if level == TestLevel.BASIC and all(r.passed for r in results):
            recommendations.append("Ready to proceed to Intermediate level tests")
        elif level == TestLevel.INTERMEDIATE and all(r.passed for r in results):
            recommendations.append("Ready to proceed to Advanced level tests")
        elif level == TestLevel.ADVANCED and all(r.passed for r in results):
            recommendations.append("Ready to proceed to Expert level tests")
        elif level == TestLevel.EXPERT and all(r.passed for r in results):
            recommendations.append("Ready for Master level certification")
        elif level == TestLevel.MASTER and all(r.passed for r in results):
            recommendations.append("Excellent! All tests passed. Group is fully certified.")
        
        return recommendations


# ============================================
# CONVENIENCE FUNCTIONS
# ============================================

def create_test_pool() -> IOVBATestPool:
    """Crea un pool de tests"""
    return IOVBATestPool()


def create_test_runner(pool: Optional[IOVBATestPool] = None) -> IOVBATestRunner:
    """Crea un runner de tests"""
    return IOVBATestRunner(pool)


async def test_iovba_group(
    group: IOVBAGroup,
    levels: Optional[List[TestLevel]] = None
) -> List[IOVBATestReport]:
    """Función de conveniencia para testear un grupo"""
    runner = create_test_runner()
    return await runner.run_all_tests(group, levels)
