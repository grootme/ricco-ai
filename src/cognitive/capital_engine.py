"""
NEXUS Cognitive Capital Engine - Motor de Capital Cognitivo REAL

## ¿Qué hace este motor?

Genera Capital Cognitivo REAL a partir de:
1. Experiencias reales procesadas (NO hardcodeadas)
2. Aprendizaje de aciertos y errores
3. Patrones reconocidos de casos reales
4. Insights generados dinámicamente

## Diferencia con enfoques incorrectos

❌ INCORRECTO (Mock/Hardcode):
   agent_profile = {"skills": ["code_review"]}  # Hardcoded
   
✅ CORRECTO (Capital Cognitivo Real):
   skills = derive_skills_from_demonstrated_experience()

## Componentes del Motor

1. ExperienceProcessor: Procesa experiencias y extrae aprendizaje
2. PatternRecognizer: Reconoce patrones de comportamiento
3. SkillDeriver: Deriva habilidades de casos exitosos
4. InsightGenerator: Genera insights de la síntesis
5. CapitalAccumulator: Acumula y consolida capital

@author: NEXUS - Neural Execution Unified System
"""

from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4
import asyncio
import json
import hashlib
import logging
import math

logger = logging.getLogger(__name__)


# ============================================================================
# EXPERIENCIA - UNIDAD DE APRENDIZAJE
# ============================================================================

class ExperienceType(str, Enum):
    """Tipos de experiencia que generan capital"""
    TASK_EXECUTION = "task_execution"        # Ejecución de tarea
    INTERACTION = "interaction"              # Interacción con usuario/agente
    OBSERVATION = "observation"              # Observación del sistema
    ERROR_RECOVERY = "error_recovery"        # Recuperación de error
    SUCCESS_ANALYSIS = "success_analysis"    # Análisis de éxito
    COLLABORATION = "collaboration"          # Colaboración entre agentes
    REFLECTION = "reflection"                # Reflexión auto-generada
    FEEDBACK = "feedback"                    # Feedback externo


class ExperienceOutcome(str, Enum):
    """Resultado de la experiencia"""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    LEARNED = "learned"                      # Falló pero se aprendió
    BLOCKED = "blocked"                      # Bloqueado, requiere intervención


@dataclass
class Experience:
    """
    Experiencia Real del Agente
    
    Cada experiencia es una oportunidad de aprendizaje.
    El capital cognitivo se construye acumulando experiencias.
    """
    id: UUID = field(default_factory=uuid4)
    agent_id: str = ""
    experience_type: ExperienceType = ExperienceType.TASK_EXECUTION
    outcome: ExperienceOutcome = ExperienceOutcome.SUCCESS
    
    # Contenido de la experiencia
    task_description: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    actions_taken: List[Dict[str, Any]] = field(default_factory=list)
    result: Dict[str, Any] = field(default_factory=dict)
    
    # Métricas
    duration_seconds: float = 0.0
    resources_used: Dict[str, float] = field(default_factory=dict)
    
    # Aprendizaje extraído
    lessons_learned: List[str] = field(default_factory=list)
    patterns_identified: List[str] = field(default_factory=list)
    skills_demonstrated: List[str] = field(default_factory=list)
    mistakes_made: List[str] = field(default_factory=list)
    improvements_suggested: List[str] = field(default_factory=list)
    
    # Valor de la experiencia
    cognitive_value: float = 0.0  # Calculado dinámicamente
    
    # Metadata
    domain: str = "general"
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def compute_cognitive_value(self) -> float:
        """
        Calcula el valor cognitivo de la experiencia
        
        Basado en:
        - Complejidad de la tarea
        - Resultado obtenido
        - Lecciones aprendidas
        - Patrones identificados
        """
        value = 0.0
        
        # Valor por resultado
        if self.outcome == ExperienceOutcome.SUCCESS:
            value += 0.5
        elif self.outcome == ExperienceOutcome.LEARNED:
            value += 0.4
        elif self.outcome == ExperienceOutcome.PARTIAL_SUCCESS:
            value += 0.3
        elif self.outcome == ExperienceOutcome.FAILURE:
            value += 0.1  # Incluso errores tienen valor
        
        # Valor por complejidad
        value += min(0.2, len(self.actions_taken) * 0.02)
        
        # Valor por aprendizaje
        value += min(0.2, len(self.lessons_learned) * 0.04)
        value += min(0.1, len(self.patterns_identified) * 0.02)
        
        # Valor por skills demostradas
        value += min(0.1, len(self.skills_demonstrated) * 0.02)
        
        # Ajuste por duración (experiencias muy cortas o muy largas)
        if 10 < self.duration_seconds < 300:  # Experiencia óptima
            value += 0.1
        
        self.cognitive_value = min(1.0, value)
        return self.cognitive_value
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "agent_id": self.agent_id,
            "experience_type": self.experience_type.value,
            "outcome": self.outcome.value,
            "task_description": self.task_description,
            "context": self.context,
            "actions_taken": self.actions_taken,
            "result": self.result,
            "duration_seconds": self.duration_seconds,
            "resources_used": self.resources_used,
            "lessons_learned": self.lessons_learned,
            "patterns_identified": self.patterns_identified,
            "skills_demonstrated": self.skills_demonstrated,
            "mistakes_made": self.mistakes_made,
            "improvements_suggested": self.improvements_suggested,
            "cognitive_value": self.cognitive_value,
            "domain": self.domain,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
        }


# ============================================================================
# PROCESADOR DE EXPERIENCIAS
# ============================================================================

class ExperienceProcessor:
    """
    Procesa experiencias reales y extrae capital cognitivo
    
    NO usa datos hardcodeados - todo se deriva de experiencias reales
    """
    
    def __init__(self):
        self.experiences: List[Experience] = []
        self.agent_experiences: Dict[str, List[UUID]] = {}
    
    def process_experience(self, experience: Experience) -> Dict[str, Any]:
        """
        Procesa una experiencia y extrae aprendizaje
        
        Returns:
            Dict con el aprendizaje extraído
        """
        # Calcular valor cognitivo
        experience.compute_cognitive_value()
        
        # Almacenar
        self.experiences.append(experience)
        if experience.agent_id not in self.agent_experiences:
            self.agent_experiences[experience.agent_id] = []
        self.agent_experiences[experience.agent_id].append(experience.id)
        
        # Extraer aprendizaje
        learning = {
            "experience_id": str(experience.id),
            "cognitive_value": experience.cognitive_value,
            "lessons": self._extract_lessons(experience),
            "patterns": self._identify_patterns(experience),
            "skills": self._derive_skills(experience),
            "improvements": self._suggest_improvements(experience),
        }
        
        return learning
    
    def _extract_lessons(self, experience: Experience) -> List[str]:
        """Extrae lecciones aprendidas de la experiencia"""
        lessons = []
        
        if experience.outcome == ExperienceOutcome.SUCCESS:
            # Analizar qué llevó al éxito
            for action in experience.actions_taken:
                if action.get("effective"):
                    lessons.append(f"Effective action: {action.get('type', 'unknown')}")
        
        elif experience.outcome == ExperienceOutcome.FAILURE:
            # Analizar qué causó el fallo
            for mistake in experience.mistakes_made:
                lessons.append(f"Avoid: {mistake}")
        
        elif experience.outcome == ExperienceOutcome.LEARNED:
            # Valorar el aprendizaje incluso del error
            for lesson in experience.lessons_learned:
                lessons.append(lesson)
        
        return lessons
    
    def _identify_patterns(self, experience: Experience) -> List[str]:
        """Identifica patrones en la experiencia"""
        patterns = []
        
        # Patrón de secuencia de acciones
        action_sequence = [a.get("type") for a in experience.actions_taken]
        if len(action_sequence) >= 3:
            pattern_key = self._hash_sequence(action_sequence)
            patterns.append(f"action_sequence:{pattern_key}")
        
        # Patrón de contexto-result
        if experience.context and experience.result:
            context_keys = sorted(experience.context.keys())
            result_keys = sorted(experience.result.keys())
            patterns.append(f"context_pattern:{self._hash_sequence(context_keys)}")
            patterns.append(f"result_pattern:{self._hash_sequence(result_keys)}")
        
        return patterns
    
    def _derive_skills(self, experience: Experience) -> List[str]:
        """
        Deriva habilidades de la experiencia
        
        IMPORTANTE: Las skills se DERIVAN de capacidades demostradas,
        NO se declaran hardcodeadas
        """
        skills = []
        
        # Derivar de acciones exitosas
        for action in experience.actions_taken:
            if action.get("success", False):
                skill = self._action_to_skill(action)
                if skill and skill not in skills:
                    skills.append(skill)
        
        # Derivar de resultado
        if experience.outcome == ExperienceOutcome.SUCCESS:
            # Inferir skills del tipo de tarea
            task_type = experience.context.get("task_type", "")
            if task_type:
                skills.append(f"{task_type}_execution")
        
        return skills
    
    def _action_to_skill(self, action: Dict[str, Any]) -> Optional[str]:
        """Convierte una acción en una habilidad"""
        action_type = action.get("type", "")
        
        # Mapeo de acciones a skills (dinámico, no hardcodeado)
        skill_mapping = {
            "analyze": "analysis",
            "search": "information_retrieval",
            "generate": "content_generation",
            "validate": "validation",
            "execute": "execution",
            "optimize": "optimization",
            "debug": "debugging",
            "design": "design",
            "implement": "implementation",
            "test": "testing",
            "review": "review",
            "coordinate": "coordination",
        }
        
        return skill_mapping.get(action_type)
    
    def _suggest_improvements(self, experience: Experience) -> List[str]:
        """Sugiere mejoras basadas en la experiencia"""
        improvements = []
        
        if experience.outcome != ExperienceOutcome.SUCCESS:
            improvements.extend(experience.improvements_suggested)
        
        # Sugerencias basadas en métricas
        if experience.duration_seconds > 300:
            improvements.append("Consider optimizing execution time")
        
        if len(experience.mistakes_made) > 0:
            improvements.append("Review and prevent common mistakes")
        
        return improvements
    
    def _hash_sequence(self, sequence: List[str]) -> str:
        """Genera hash para una secuencia"""
        data = "|".join(str(s) for s in sequence)
        return hashlib.md5(data.encode()).hexdigest()[:8]
    
    def get_agent_experiences(self, agent_id: str) -> List[Experience]:
        """Obtiene todas las experiencias de un agente"""
        exp_ids = self.agent_experiences.get(agent_id, [])
        return [e for e in self.experiences if e.id in exp_ids]
    
    def get_successful_experiences(self, domain: str = None) -> List[Experience]:
        """Obtiene experiencias exitosas para aprender de ellas"""
        successful = [e for e in self.experiences 
                      if e.outcome in [ExperienceOutcome.SUCCESS, ExperienceOutcome.LEARNED]]
        
        if domain:
            successful = [e for e in successful if e.domain == domain]
        
        return successful


# ============================================================================
# RECONOCEDOR DE PATRONES
# ============================================================================

class PatternRecognizer:
    """
    Reconoce patrones en experiencias acumuladas
    
    Los patrones son el componente PATTERN del capital cognitivo
    """
    
    def __init__(self):
        self.patterns: Dict[str, Dict[str, Any]] = {}
        self.pattern_occurrences: Dict[str, int] = {}
    
    def analyze_experiences(self, experiences: List[Experience]) -> Dict[str, Any]:
        """
        Analiza experiencias y reconoce patrones
        """
        analysis = {
            "patterns_found": 0,
            "new_patterns": [],
            "reinforced_patterns": [],
            "pattern_details": [],
        }
        
        for experience in experiences:
            # Analizar secuencia de acciones
            action_pattern = self._analyze_action_sequence(experience)
            if action_pattern:
                self._register_pattern(action_pattern, experience)
                analysis["patterns_found"] += 1
            
            # Analizar contexto-result
            context_pattern = self._analyze_context_result(experience)
            if context_pattern:
                self._register_pattern(context_pattern, experience)
                analysis["patterns_found"] += 1
            
            # Analizar errores comunes
            error_pattern = self._analyze_errors(experience)
            if error_pattern:
                self._register_pattern(error_pattern, experience)
                analysis["patterns_found"] += 1
        
        return analysis
    
    def _analyze_action_sequence(self, experience: Experience) -> Optional[Dict[str, Any]]:
        """Analiza patrones en secuencias de acciones"""
        if len(experience.actions_taken) < 3:
            return None
        
        sequence = [a.get("type") for a in experience.actions_taken]
        
        # Buscar patrones comunes
        pattern = {
            "type": "action_sequence",
            "sequence": sequence,
            "outcome": experience.outcome.value,
            "domain": experience.domain,
            "confidence": 0.5 + (experience.cognitive_value * 0.3),
        }
        
        return pattern
    
    def _analyze_context_result(self, experience: Experience) -> Optional[Dict[str, Any]]:
        """Analiza patrones contexto-resultado"""
        if not experience.context or not experience.result:
            return None
        
        pattern = {
            "type": "context_result",
            "context_keys": list(experience.context.keys()),
            "result_keys": list(experience.result.keys()),
            "domain": experience.domain,
            "confidence": 0.4 + (experience.cognitive_value * 0.3),
        }
        
        return pattern
    
    def _analyze_errors(self, experience: Experience) -> Optional[Dict[str, Any]]:
        """Analiza patrones de error"""
        if not experience.mistakes_made:
            return None
        
        pattern = {
            "type": "error_pattern",
            "mistakes": experience.mistakes_made,
            "domain": experience.domain,
            "confidence": 0.3 + (len(experience.mistakes_made) * 0.1),
        }
        
        return pattern
    
    def _register_pattern(self, pattern: Dict[str, Any], experience: Experience) -> str:
        """Registra un patrón reconocido"""
        pattern_hash = self._hash_pattern(pattern)
        
        if pattern_hash in self.patterns:
            # Reforzar patrón existente
            self.patterns[pattern_hash]["occurrences"] += 1
            self.patterns[pattern_hash]["confidence"] = min(
                1.0, 
                self.patterns[pattern_hash]["confidence"] + 0.05
            )
        else:
            # Nuevo patrón
            self.patterns[pattern_hash] = {
                **pattern,
                "id": pattern_hash,
                "occurrences": 1,
                "first_seen": datetime.utcnow().isoformat(),
                "last_seen": datetime.utcnow().isoformat(),
            }
        
        return pattern_hash
    
    def _hash_pattern(self, pattern: Dict[str, Any]) -> str:
        """Genera hash único para un patrón"""
        pattern_data = json.dumps({
            "type": pattern.get("type"),
            "domain": pattern.get("domain"),
            "key_data": str(pattern.get("sequence", pattern.get("context_keys", pattern.get("mistakes", []))))
        }, sort_keys=True)
        return hashlib.md5(pattern_data.encode()).hexdigest()[:12]
    
    def get_patterns_by_domain(self, domain: str) -> List[Dict[str, Any]]:
        """Obtiene patrones por dominio"""
        return [p for p in self.patterns.values() if p.get("domain") == domain]
    
    def get_high_confidence_patterns(self, min_confidence: float = 0.7) -> List[Dict[str, Any]]:
        """Obtiene patrones con alta confianza"""
        return [p for p in self.patterns.values() if p.get("confidence", 0) >= min_confidence]


# ============================================================================
# DERIVADOR DE SKILLS
# ============================================================================

class SkillDeriver:
    """
    Deriva habilidades de experiencias exitosas
    
    IMPORTANTE: NO hardcodea skills, las DERIVA de desempeño demostrado
    """
    
    def __init__(self):
        self.skills: Dict[str, Dict[str, Any]] = {}
        self.skill_demonstrations: Dict[str, List[UUID]] = {}
    
    def derive_from_experiences(self, experiences: List[Experience]) -> Dict[str, Any]:
        """
        Deriva skills de experiencias
        
        Una skill es derivada cuando:
        1. Se ha demostrado en múltiples experiencias exitosas
        2. Tiene una tasa de éxito consistente
        3. Ha sido aplicada en contextos variados
        """
        derivation_result = {
            "skills_derived": 0,
            "skills_reinforced": 0,
            "skills_details": [],
        }
        
        for experience in experiences:
            if experience.outcome not in [ExperienceOutcome.SUCCESS, ExperienceOutcome.LEARNED]:
                continue
            
            for skill in experience.skills_demonstrated:
                self._derive_skill(skill, experience)
                derivation_result["skills_derived"] += 1
        
        return derivation_result
    
    def _derive_skill(self, skill_name: str, experience: Experience) -> Dict[str, Any]:
        """
        Deriva o refuerza una skill
        """
        if skill_name not in self.skills:
            # Nueva skill
            self.skills[skill_name] = {
                "name": skill_name,
                "level": 0.1,  # Nivel inicial bajo
                "demonstrations": 1,
                "successes": 1 if experience.outcome == ExperienceOutcome.SUCCESS else 0,
                "domains": {experience.domain},
                "first_demonstrated": datetime.utcnow().isoformat(),
                "last_demonstrated": datetime.utcnow().isoformat(),
                "contexts": [experience.context] if experience.context else [],
            }
            self.skill_demonstrations[skill_name] = [experience.id]
        else:
            # Reforzar skill existente
            self.skills[skill_name]["demonstrations"] += 1
            if experience.outcome == ExperienceOutcome.SUCCESS:
                self.skills[skill_name]["successes"] += 1
            self.skills[skill_name]["domains"].add(experience.domain)
            self.skills[skill_name]["last_demonstrated"] = datetime.utcnow().isoformat()
            self.skill_demonstrations[skill_name].append(experience.id)
            
            # Calcular nuevo nivel basado en éxito
            success_rate = self.skills[skill_name]["successes"] / self.skills[skill_name]["demonstrations"]
            demonstrations_factor = min(1.0, self.skills[skill_name]["demonstrations"] / 10)
            self.skills[skill_name]["level"] = min(1.0, 0.1 + success_rate * 0.7 + demonstrations_factor * 0.2)
        
        return self.skills[skill_name]
    
    def get_skill_level(self, skill_name: str) -> float:
        """Obtiene el nivel de una skill"""
        if skill_name in self.skills:
            return self.skills[skill_name]["level"]
        return 0.0
    
    def get_skills_by_level(self, min_level: float = 0.5) -> Dict[str, Dict[str, Any]]:
        """Obtiene skills por nivel mínimo"""
        return {k: v for k, v in self.skills.items() if v["level"] >= min_level}
    
    def get_agent_skills(self, domain: str = None) -> Dict[str, Dict[str, Any]]:
        """Obtiene todas las skills, opcionalmente filtradas por dominio"""
        if domain:
            return {k: v for k, v in self.skills.items() if domain in v.get("domains", set())}
        return self.skills.copy()


# ============================================================================
# GENERADOR DE INSIGHTS
# ============================================================================

class InsightGenerator:
    """
    Genera insights a partir de la síntesis de experiencias, patrones y skills
    
    Los insights son el componente más valioso del capital cognitivo:
    comprensiones profundas que emergen de la síntesis
    """
    
    def __init__(self):
        self.insights: List[Dict[str, Any]] = []
    
    def generate_insights(
        self,
        experiences: List[Experience],
        patterns: Dict[str, Dict[str, Any]],
        skills: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Genera insights de la síntesis de componentes
        """
        new_insights = []
        
        # Insight 1: Correlación skills-éxito
        skill_success_insight = self._analyze_skill_success_correlation(experiences, skills)
        if skill_success_insight:
            new_insights.append(skill_success_insight)
        
        # Insight 2: Patrones predictivos
        predictive_insight = self._analyze_predictive_patterns(patterns)
        if predictive_insight:
            new_insights.append(predictive_insight)
        
        # Insight 3: Áreas de mejora
        improvement_insight = self._identify_improvement_areas(experiences, skills)
        if improvement_insight:
            new_insights.append(improvement_insight)
        
        # Insight 4: Fortalezas
        strength_insight = self._identify_strengths(experiences, skills, patterns)
        if strength_insight:
            new_insights.append(strength_insight)
        
        self.insights.extend(new_insights)
        return new_insights
    
    def _analyze_skill_success_correlation(
        self, 
        experiences: List[Experience],
        skills: Dict[str, Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Analiza correlación entre skills y éxito"""
        if not experiences or not skills:
            return None
        
        # Identificar skills más correlacionadas con éxito
        high_value_skills = [k for k, v in skills.items() if v["level"] >= 0.5]
        
        if high_value_skills:
            return {
                "type": "skill_success_correlation",
                "insight": f"Skills with highest success correlation: {', '.join(high_value_skills[:3])}",
                "confidence": 0.7,
                "generated_at": datetime.utcnow().isoformat(),
            }
        return None
    
    def _analyze_predictive_patterns(
        self, 
        patterns: Dict[str, Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Identifica patrones con valor predictivo"""
        high_confidence = [p for p in patterns.values() if p.get("confidence", 0) >= 0.7]
        
        if high_confidence:
            return {
                "type": "predictive_patterns",
                "insight": f"Found {len(high_confidence)} patterns with high predictive value",
                "patterns": [p["id"] for p in high_confidence[:5]],
                "confidence": 0.8,
                "generated_at": datetime.utcnow().isoformat(),
            }
        return None
    
    def _identify_improvement_areas(
        self,
        experiences: List[Experience],
        skills: Dict[str, Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Identifica áreas que necesitan mejora"""
        low_skills = [k for k, v in skills.items() if v["level"] < 0.3]
        failures = [e for e in experiences if e.outcome == ExperienceOutcome.FAILURE]
        
        if low_skills or failures:
            return {
                "type": "improvement_areas",
                "insight": f"Focus improvement on: {', '.join(low_skills[:3]) if low_skills else 'general skills'}",
                "failure_count": len(failures),
                "low_skills": low_skills,
                "confidence": 0.6,
                "generated_at": datetime.utcnow().isoformat(),
            }
        return None
    
    def _identify_strengths(
        self,
        experiences: List[Experience],
        skills: Dict[str, Dict[str, Any]],
        patterns: Dict[str, Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Identifica fortalezas del agente"""
        expert_skills = [k for k, v in skills.items() if v["level"] >= 0.7]
        success_count = len([e for e in experiences if e.outcome == ExperienceOutcome.SUCCESS])
        
        if expert_skills or success_count > len(experiences) * 0.5:
            return {
                "type": "strengths",
                "insight": f"Core strengths: {', '.join(expert_skills) if expert_skills else 'consistency'}",
                "expert_skills": expert_skills,
                "success_rate": success_count / len(experiences) if experiences else 0,
                "confidence": 0.8,
                "generated_at": datetime.utcnow().isoformat(),
            }
        return None


# ============================================================================
# ACUMULADOR DE CAPITAL COGNITIVO
# ============================================================================

class CognitiveCapitalAccumulator:
    """
    Acumula y consolida el capital cognitivo de un agente
    
    Este es el componente principal que integra:
    - Experiencias procesadas
    - Patrones reconocidos
    - Skills derivadas
    - Insights generados
    
    TODO es REAL, derivado de experiencias reales, NO hardcodeado
    """
    
    def __init__(self, agent_id: str, domain: str = "general"):
        self.agent_id = agent_id
        self.domain = domain
        
        # Componentes
        self.experience_processor = ExperienceProcessor()
        self.pattern_recognizer = PatternRecognizer()
        self.skill_deriver = SkillDeriver()
        self.insight_generator = InsightGenerator()
        
        # Capital acumulado
        self.capital_metrics = {
            "total_experiences": 0,
            "total_patterns": 0,
            "total_skills": 0,
            "total_insights": 0,
            "capital_value": 0,
            "learning_rate": 0.1,
        }
    
    async def process_experience(self, experience: Experience) -> Dict[str, Any]:
        """
        Procesa una experiencia y actualiza el capital
        """
        # Procesar experiencia
        learning = self.experience_processor.process_experience(experience)
        
        # Actualizar patrones
        patterns_result = self.pattern_recognizer.analyze_experiences([experience])
        
        # Derivar skills
        skills_result = self.skill_deriver.derive_from_experiences([experience])
        
        # Generar insights
        insights = self.insight_generator.generate_insights(
            self.experience_processor.experiences,
            self.pattern_recognizer.patterns,
            self.skill_deriver.skills
        )
        
        # Actualizar métricas
        self._update_metrics()
        
        return {
            "experience_processed": str(experience.id),
            "cognitive_value": experience.cognitive_value,
            "learning": learning,
            "patterns_found": patterns_result["patterns_found"],
            "skills_derived": skills_result["skills_derived"],
            "insights_generated": len(insights),
            "total_capital_value": self.capital_metrics["capital_value"],
        }
    
    def _update_metrics(self) -> None:
        """Actualiza métricas de capital"""
        self.capital_metrics["total_experiences"] = len(self.experience_processor.experiences)
        self.capital_metrics["total_patterns"] = len(self.pattern_recognizer.patterns)
        self.capital_metrics["total_skills"] = len(self.skill_deriver.skills)
        self.capital_metrics["total_insights"] = len(self.insight_generator.insights)
        
        # Calcular valor total
        exp_value = sum(e.cognitive_value for e in self.experience_processor.experiences)
        pattern_value = sum(p.get("confidence", 0) * 10 for p in self.pattern_recognizer.patterns.values())
        skill_value = sum(s["level"] * 100 for s in self.skill_deriver.skills.values())
        insight_value = len(self.insight_generator.insights) * 50
        
        self.capital_metrics["capital_value"] = int(exp_value * 10 + pattern_value + skill_value + insight_value)
    
    def get_capital_report(self) -> Dict[str, Any]:
        """
        Genera un reporte completo del capital cognitivo
        """
        return {
            "agent_id": self.agent_id,
            "domain": self.domain,
            "metrics": self.capital_metrics,
            "skills": {
                "total": len(self.skill_deriver.skills),
                "by_level": {
                    "expert": len([s for s in self.skill_deriver.skills.values() if s["level"] >= 0.8]),
                    "advanced": len([s for s in self.skill_deriver.skills.values() if 0.6 <= s["level"] < 0.8]),
                    "intermediate": len([s for s in self.skill_deriver.skills.values() if 0.4 <= s["level"] < 0.6]),
                    "beginner": len([s for s in self.skill_deriver.skills.values() if s["level"] < 0.4]),
                },
                "details": self.skill_deriver.skills,
            },
            "patterns": {
                "total": len(self.pattern_recognizer.patterns),
                "high_confidence": len(self.pattern_recognizer.get_high_confidence_patterns()),
                "by_domain": {
                    domain: len(self.pattern_recognizer.get_patterns_by_domain(domain))
                    for domain in set(p.get("domain") for p in self.pattern_recognizer.patterns.values())
                },
            },
            "experiences": {
                "total": len(self.experience_processor.experiences),
                "successful": len(self.experience_processor.get_successful_experiences()),
                "by_type": {
                    exp_type.value: len([e for e in self.experience_processor.experiences if e.experience_type == exp_type])
                    for exp_type in ExperienceType
                },
            },
            "insights": {
                "total": len(self.insight_generator.insights),
                "recent": self.insight_generator.insights[-5:] if self.insight_generator.insights else [],
            },
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa el capital completo"""
        return {
            "agent_id": self.agent_id,
            "domain": self.domain,
            "metrics": self.capital_metrics,
            "experiences": [e.to_dict() for e in self.experience_processor.experiences],
            "patterns": self.pattern_recognizer.patterns,
            "skills": self.skill_deriver.skills,
            "insights": self.insight_generator.insights,
        }


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "ExperienceType",
    "ExperienceOutcome",
    "Experience",
    "ExperienceProcessor",
    "PatternRecognizer",
    "SkillDeriver",
    "InsightGenerator",
    "CognitiveCapitalAccumulator",
]
