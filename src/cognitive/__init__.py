"""
NEXUS Cognitive System - Sistema Cognitivo Completo

Este paquete implementa la infraestructura cognitiva completa de NEXUS:

## Componentes

1. **obviousness_context**: Contextos de Obviedad
   - Trasfondo de Obviedad
   - Mandatos Activos
   - Condiciones de Satisfacción
   - Red de Contextos

2. **capital_engine**: Motor de Capital Cognitivo
   - Procesador de Experiencias
   - Reconocedor de Patrones
   - Derivador de Skills
   - Generador de Insights

3. **learning_pipeline**: Pipeline de Aprendizaje
   - Motor de Refuerzo
   - Motor de Coordinación
   - Motor de Reflexión

4. **capital_infrastructure**: Infraestructura Cognitiva
   - Persistencia con Redis
   - Sincronización entre agentes
   - Memory VCS

5. **capital**: Modelos de Capital Cognitivo
   - Engrams (memorias)
   - Skills (habilidades)
   - Patterns (patrones)

## Fórmula

    INFRAESTRUCTURA COGNITIVA → genera → CAPITAL COGNITIVO → habilita → COORDINACIÓN SUPERIOR

@author: NEXUS - Neural Execution Unified System
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

from .obviousness_context import (
    ObviousnessType,
    ContextStatus,
    ActivationFunction,
    TrasfondoObviedad,
    MandatoActivo,
    CondicionesSatisfaccion,
    ContextoObviedad,
    RedContextosObviedad,
)

from .capital_engine import (
    ExperienceType,
    ExperienceOutcome,
    Experience,
    ExperienceProcessor,
    PatternRecognizer,
    SkillDeriver,
    InsightGenerator,
    CognitiveCapitalAccumulator,
)

from .learning_pipeline import (
    LearningEventType,
    LearningPriority,
    LearningEvent,
    ReinforcementEngine,
    CoordinationEngine,
    ReflectionEngine,
    LearningPipeline,
)

from .capital import (
    CapitalType,
    CapitalSource,
    CapitalStatus,
    CognitiveCapital as CognitiveCapitalModel,
    CognitiveCapitalStore,
    CognitiveCapitalGenerator,
    NVIDIABlueprintDomain,
    DOMAIN_DESCRIPTIONS,
)

from .capital_infrastructure import (
    EngramType,
    SkillLevel,
    SyncMode,
    Engram,
    Skill,
    Pattern,
    CognitiveCapital as CognitiveCapitalFull,
    CognitiveInfrastructure,
)


# ============================================================================
# COGNITIVE SYSTEM - FACADE
# ============================================================================

class CognitiveSystem:
    """
    Facade del Sistema Cognitivo Completo
    
    Proporciona una interfaz unificada para:
    1. Gestión de Contextos de Obviedad
    2. Acumulación de Capital Cognitivo
    3. Pipeline de Aprendizaje Continuo
    4. Coordinación entre Agentes
    """
    
    def __init__(self, agent_id: str, domain: str = "general"):
        self.agent_id = agent_id
        self.domain = domain
        
        # Red de contextos
        self.context_network = RedContextosObviedad()
        
        # Acumulador de capital
        self.capital_accumulator = CognitiveCapitalAccumulator(agent_id, domain)
        
        # Pipeline de aprendizaje
        self.learning_pipeline = LearningPipeline(agent_id, domain)
        
        # Infraestructura
        self.infrastructure = CognitiveInfrastructure()
        
        # Estado
        self.initialized = False
    
    async def initialize(self, redis_url: str = "redis://localhost:6379") -> None:
        """Inicializa el sistema cognitivo completo"""
        # Iniciar pipeline
        await self.learning_pipeline.start()
        
        # Crear contexto inicial del dominio
        context = ContextoObviedad(
            name=f"{self.domain}_context",
            description=f"Contexto de obviedad para dominio {self.domain}",
            domain=self.domain,
            status=ContextStatus.ACTIVE,
        )
        context.initialize_trasfondo()
        self.context_network.add_context(context)
        
        self.initialized = True
        logger.info(f"Cognitive system initialized for {self.agent_id} in {self.domain}")
    
    async def process_experience(
        self,
        experience_type: str,
        task_description: str,
        actions: List[Dict[str, Any]],
        result: Dict[str, Any],
        outcome: str = "success"
    ) -> Dict[str, Any]:
        """
        Procesa una experiencia y actualiza todo el sistema
        """
        # Crear experiencia
        experience = Experience(
            agent_id=self.agent_id,
            experience_type=ExperienceType(experience_type),
            outcome=ExperienceOutcome(outcome),
            task_description=task_description,
            actions_taken=actions,
            result=result,
            domain=self.domain,
        )
        
        # Procesar en acumulador
        capital_result = await self.capital_accumulator.process_experience(experience)
        
        # Crear evento de aprendizaje
        event = LearningEvent(
            event_type=LearningEventType.TASK_COMPLETED if outcome == "success" else LearningEventType.TASK_FAILED,
            source_agent_id=self.agent_id,
            source_domain=self.domain,
            payload={
                "experience_id": str(experience.id),
                "patterns": capital_result.get("learning", {}).get("patterns", []),
                "skills_demonstrated": capital_result.get("learning", {}).get("skills", []),
            },
            learning_value=experience.cognitive_value,
        )
        
        # Procesar en pipeline
        pipeline_result = await self.learning_pipeline.process_event(event)
        
        return {
            "experience_id": str(experience.id),
            "capital_result": capital_result,
            "pipeline_result": pipeline_result,
            "total_capital_value": self.capital_accumulator.capital_metrics["capital_value"],
        }
    
    async def reflect(self) -> Dict[str, Any]:
        """Ejecuta una reflexión del sistema"""
        capital_report = self.capital_accumulator.get_capital_report()
        return await self.learning_pipeline.run_reflection_cycle(capital_report)
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene estado completo del sistema"""
        return {
            "agent_id": self.agent_id,
            "domain": self.domain,
            "initialized": self.initialized,
            "capital_metrics": self.capital_accumulator.capital_metrics,
            "pipeline_status": self.learning_pipeline.get_pipeline_status(),
            "context_network": self.context_network.get_network_metrics(),
        }
    
    def get_capital_report(self) -> Dict[str, Any]:
        """Obtiene reporte completo del capital cognitivo"""
        return self.capital_accumulator.get_capital_report()


# ============================================================================
# DOMAIN-SPECIFIC COGNITIVE PROFILES
# ============================================================================

def create_domain_cognitive_profile(domain: str) -> Dict[str, Any]:
    """
    Crea un perfil cognitivo específico para un dominio
    
    IMPORTANTE: No hardcodea datos, define la ESTRUCTURA
    del capital cognitivo que se construirá dinámicamente
    """
    domain_configs = {
        "swe": {
            "name": "CODEX",
            "description": "Software Engineering Cognitive Profile",
            "initial_skill_areas": ["analysis", "design", "implementation", "testing"],
            "context_priorities": ["code_quality", "performance", "maintainability"],
            "learning_focus": ["patterns", "best_practices", "optimization"],
        },
        "salud": {
            "name": "VITALIS",
            "description": "Healthcare Cognitive Profile",
            "initial_skill_areas": ["diagnosis", "treatment_planning", "research"],
            "context_priorities": ["accuracy", "patient_safety", "evidence_based"],
            "learning_focus": ["medical_knowledge", "clinical_patterns", "treatments"],
        },
        "finanzas": {
            "name": "APEX",
            "description": "Financial Analysis Cognitive Profile",
            "initial_skill_areas": ["market_analysis", "risk_assessment", "forecasting"],
            "context_priorities": ["accuracy", "compliance", "risk_management"],
            "learning_focus": ["market_patterns", "risk_factors", "trends"],
        },
        "legal": {
            "name": "JUSTITIA",
            "description": "Legal Analysis Cognitive Profile",
            "initial_skill_areas": ["legal_research", "document_analysis", "compliance"],
            "context_priorities": ["accuracy", "compliance", "precedent"],
            "learning_focus": ["legal_patterns", "case_law", "regulations"],
        },
        "geopolitica": {
            "name": "DIPLOMAT",
            "description": "Geopolitical Analysis Cognitive Profile",
            "initial_skill_areas": ["analysis", "forecasting", "risk_assessment"],
            "context_priorities": ["accuracy", "context", "temporal"],
            "learning_focus": ["geopolitical_patterns", "trends", "relationships"],
        },
    }
    
    # Default config
    default_config = {
        "name": domain.upper(),
        "description": f"{domain} Cognitive Profile",
        "initial_skill_areas": ["analysis", "communication", "problem_solving"],
        "context_priorities": ["accuracy", "efficiency", "quality"],
        "learning_focus": ["domain_patterns", "best_practices"],
    }
    
    return domain_configs.get(domain, default_config)


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Contextos de Obviedad
    "ObviousnessType",
    "ContextStatus",
    "ActivationFunction",
    "TrasfondoObviedad",
    "MandatoActivo",
    "CondicionesSatisfaccion",
    "ContextoObviedad",
    "RedContextosObviedad",
    
    # Motor de Capital
    "ExperienceType",
    "ExperienceOutcome",
    "Experience",
    "ExperienceProcessor",
    "PatternRecognizer",
    "SkillDeriver",
    "InsightGenerator",
    "CognitiveCapitalAccumulator",
    
    # Pipeline de Aprendizaje
    "LearningEventType",
    "LearningPriority",
    "LearningEvent",
    "ReinforcementEngine",
    "CoordinationEngine",
    "ReflectionEngine",
    "LearningPipeline",
    
    # Modelos de Capital
    "CapitalType",
    "CapitalSource",
    "CapitalStatus",
    "CognitiveCapitalModel",
    "CognitiveCapitalStore",
    "CognitiveCapitalGenerator",
    "NVIDIABlueprintDomain",
    "DOMAIN_DESCRIPTIONS",
    
    # Infraestructura
    "EngramType",
    "SkillLevel",
    "SyncMode",
    "Engram",
    "Skill",
    "Pattern",
    "CognitiveCapitalFull",
    "CognitiveInfrastructure",
    
    # Facade
    "CognitiveSystem",
    "create_domain_cognitive_profile",
]
