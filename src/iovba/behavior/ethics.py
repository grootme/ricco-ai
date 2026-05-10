"""
Ethics Engine - Motor de Evaluación Ética

Evalúa las acciones del agente contra reglas éticas
para garantizar un comportamiento responsable.
"""

from typing import Optional, Dict, Any, List, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class EthicalPrinciple(str, Enum):
    """Principios éticos fundamentales"""
    BENEFICENCE = "beneficence"        # Hacer el bien
    NON_MALEFICENCE = "non_maleficence" # No hacer daño
    AUTONOMY = "autonomy"              # Respetar la autonomía
    JUSTICE = "justice"                # Justicia y equidad
    TRANSPARENCY = "transparency"       # Transparencia
    PRIVACY = "privacy"                 # Privacidad
    ACCOUNTABILITY = "accountability"   # Responsabilidad


class RiskLevel(str, Enum):
    """Niveles de riesgo ético"""
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionType(str, Enum):
    """Tipos de acciones"""
    INFORMATION = "information"      # Proporcionar información
    RECOMMENDATION = "recommendation" # Hacer recomendaciones
    AUTOMATION = "automation"        # Ejecutar acciones automatizadas
    ANALYSIS = "analysis"            # Analizar datos
    COMMUNICATION = "communication"   # Comunicar con terceros
    DATA_ACCESS = "data_access"      # Acceder a datos
    DATA_SHARING = "data_sharing"    # Compartir datos


@dataclass
class EthicalRule:
    """
    Regla ética para evaluación de acciones.
    
    Define límites y restricciones para garantizar
    un comportamiento responsable del agente.
    """
    id: str
    name: str
    description: str
    principle: EthicalPrinciple
    action_types: List[ActionType] = field(default_factory=list)
    conditions: List[str] = field(default_factory=list)
    prohibited: bool = False
    requires_consent: bool = False
    requires_disclosure: bool = False
    risk_level: RiskLevel = RiskLevel.LOW
    exceptions: List[str] = field(default_factory=list)
    enabled: bool = True
    
    def evaluate(self, action: ActionType, context: Dict[str, Any]) -> "EthicalEvaluation":
        """Evalúa si una acción cumple con esta regla"""
        if not self.enabled:
            return EthicalEvaluation(
                rule_id=self.id,
                compliant=True,
                risk_level=RiskLevel.MINIMAL,
                notes="Rule disabled"
            )
        
        # Verificar si la acción aplica
        if self.action_types and action not in self.action_types:
            return EthicalEvaluation(
                rule_id=self.id,
                compliant=True,
                risk_level=RiskLevel.MINIMAL,
                notes="Action type not applicable"
            )
        
        # Verificar excepciones
        for exception in self.exceptions:
            if exception in str(context):
                return EthicalEvaluation(
                    rule_id=self.id,
                    compliant=True,
                    risk_level=RiskLevel.MINIMAL,
                    notes=f"Exception matched: {exception}"
                )
        
        # Verificar condiciones
        violations = []
        for condition in self.conditions:
            if condition in str(context).lower():
                violations.append(condition)
        
        if violations and self.prohibited:
            return EthicalEvaluation(
                rule_id=self.id,
                compliant=False,
                risk_level=self.risk_level,
                violations=violations,
                notes=f"Prohibited conditions detected: {violations}"
            )
        
        # Revisar requisitos
        requirements = []
        if self.requires_consent:
            requirements.append("user_consent")
        if self.requires_disclosure:
            requirements.append("disclosure")
        
        return EthicalEvaluation(
            rule_id=self.id,
            compliant=len(violations) == 0,
            risk_level=self.risk_level if violations else RiskLevel.MINIMAL,
            violations=violations,
            requirements=requirements,
            notes="Evaluated" if not violations else f"Conditions detected: {violations}"
        )


@dataclass
class EthicalEvaluation:
    """Resultado de evaluación ética"""
    rule_id: str
    compliant: bool
    risk_level: RiskLevel
    violations: List[str] = field(default_factory=list)
    requirements: List[str] = field(default_factory=list)
    notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EthicsReport:
    """Reporte completo de evaluación ética"""
    action_type: ActionType
    overall_compliant: bool
    overall_risk: RiskLevel
    evaluations: List[EthicalEvaluation] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    blocked_reasons: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)


class EthicsEngine:
    """
    Motor de Evaluación Ética.
    
    Evalúa las acciones del agente contra un conjunto de reglas
    éticas para garantizar un comportamiento responsable.
    
    Usage:
        engine = EthicsEngine()
        
        # Evaluar acción
        report = engine.evaluate(
            action_type=ActionType.DATA_SHARING,
            context={"data_type": "personal", "destination": "third_party"}
        )
        
        if not report.overall_compliant:
            print(f"Acción bloqueada: {report.blocked_reasons}")
    """
    
    def __init__(self):
        """Inicializa el motor de ética"""
        self._rules: Dict[str, EthicalRule] = {}
        self._evaluations_history: List[EthicsReport] = []
        self._on_violation: Optional[callable] = None
        
        # Cargar reglas por defecto
        self._load_default_rules()
    
    def _load_default_rules(self) -> None:
        """Carga reglas éticas por defecto"""
        # No Maleficencia - No hacer daño
        self.add_rule(EthicalRule(
            id="no_harm",
            name="No Causar Daño",
            description="El agente no debe ejecutar acciones que puedan causar daño",
            principle=EthicalPrinciple.NON_MALEFICENCE,
            action_types=[ActionType.AUTOMATION],
            conditions=["delete", "destroy", "format", "wipe", "rm -rf"],
            prohibited=True,
            risk_level=RiskLevel.CRITICAL
        ))
        
        self.add_rule(EthicalRule(
            id="no_dangerous_content",
            name="Sin Contenido Peligroso",
            description="No generar contenido que facilite actividades ilegales o peligrosas",
            principle=EthicalPrinciple.NON_MALEFICENCE,
            action_types=[ActionType.INFORMATION, ActionType.RECOMMENDATION],
            conditions=["bomb", "weapon", "drug", "illegal", "hack"],
            prohibited=True,
            risk_level=RiskLevel.CRITICAL
        ))
        
        # Privacidad
        self.add_rule(EthicalRule(
            id="protect_pii",
            name="Proteger Datos Personales",
            description="Los datos personales deben ser protegidos",
            principle=EthicalPrinciple.PRIVACY,
            action_types=[ActionType.DATA_ACCESS, ActionType.DATA_SHARING],
            conditions=["ssn", "credit_card", "password", "medical_record"],
            prohibited=False,
            requires_consent=True,
            risk_level=RiskLevel.HIGH
        ))
        
        self.add_rule(EthicalRule(
            id="no_unauthorized_sharing",
            name="Sin Compartir No Autorizado",
            description="No compartir datos sin autorización explícita",
            principle=EthicalPrinciple.PRIVACY,
            action_types=[ActionType.DATA_SHARING, ActionType.COMMUNICATION],
            conditions=["personal_data", "confidential", "private"],
            prohibited=False,
            requires_consent=True,
            requires_disclosure=True,
            risk_level=RiskLevel.HIGH
        ))
        
        # Transparencia
        self.add_rule(EthicalRule(
            id="disclose_ai",
            name="Divulgar Naturaleza de IA",
            description="El agente debe identificarse como IA cuando sea relevante",
            principle=EthicalPrinciple.TRANSPARENCY,
            action_types=[ActionType.COMMUNICATION],
            conditions=["human_impersonation"],
            prohibited=True,
            risk_level=RiskLevel.MEDIUM
        ))
        
        self.add_rule(EthicalRule(
            id="explain_decisions",
            name="Explicar Decisiones",
            description="Las decisiones significativas deben ser explicables",
            principle=EthicalPrinciple.TRANSPARENCY,
            action_types=[ActionType.AUTOMATION, ActionType.RECOMMENDATION],
            conditions=["automated_decision", "recommendation"],
            prohibited=False,
            requires_disclosure=True,
            risk_level=RiskLevel.MEDIUM
        ))
        
        # Autonomía
        self.add_rule(EthicalRule(
            id="respect_consent",
            name="Respetar Consentimiento",
            description="Las acciones significativas requieren consentimiento del usuario",
            principle=EthicalPrinciple.AUTONOMY,
            action_types=[ActionType.AUTOMATION, ActionType.DATA_SHARING],
            conditions=["significant_action"],
            prohibited=False,
            requires_consent=True,
            risk_level=RiskLevel.MEDIUM
        ))
        
        # Justicia
        self.add_rule(EthicalRule(
            id="no_discrimination",
            name="Sin Discriminación",
            description="No generar contenido discriminatorio",
            principle=EthicalPrinciple.JUSTICE,
            action_types=[ActionType.INFORMATION, ActionType.RECOMMENDATION, ActionType.COMMUNICATION],
            conditions=["discriminat", "racist", "sexist", "prejudice"],
            prohibited=True,
            risk_level=RiskLevel.HIGH
        ))
        
        # Responsabilidad
        self.add_rule(EthicalRule(
            id="financial_caution",
            name="Precaución Financiera",
            description="Las acciones financieras requieren precaución especial",
            principle=EthicalPrinciple.ACCOUNTABILITY,
            action_types=[ActionType.AUTOMATION, ActionType.RECOMMENDATION],
            conditions=["financial", "payment", "transfer", "investment"],
            prohibited=False,
            requires_consent=True,
            requires_disclosure=True,
            risk_level=RiskLevel.HIGH
        ))
    
    def add_rule(self, rule: EthicalRule) -> None:
        """Añade una regla ética"""
        self._rules[rule.id] = rule
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remueve una regla por ID"""
        if rule_id in self._rules:
            del self._rules[rule_id]
            return True
        return False
    
    def evaluate(
        self,
        action_type: ActionType,
        context: Dict[str, Any]
    ) -> EthicsReport:
        """
        Evalúa una acción contra todas las reglas éticas.
        
        Args:
            action_type: Tipo de acción a evaluar
            context: Contexto de la acción
        
        Returns:
            EthicsReport con el resultado de la evaluación
        """
        evaluations = []
        violations = []
        recommendations = []
        blocked_reasons = []
        max_risk = RiskLevel.MINIMAL
        
        for rule in self._rules.values():
            evaluation = rule.evaluate(action_type, context)
            evaluations.append(evaluation)
            
            if not evaluation.compliant:
                violations.extend(evaluation.violations)
                
                if evaluation.risk_level == RiskLevel.CRITICAL:
                    blocked_reasons.append(f"Regla '{rule.name}': {evaluation.notes}")
            
            # Actualizar riesgo máximo
            risk_levels = [RiskLevel.MINIMAL, RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
            if risk_levels.index(evaluation.risk_level) > risk_levels.index(max_risk):
                max_risk = evaluation.risk_level
        
        # Generar recomendaciones
        if violations:
            recommendations.append("Revisar las condiciones detectadas antes de proceder")
        
        for eval in evaluations:
            if eval.requirements:
                recommendations.append(f"Asegurar: {', '.join(eval.requirements)}")
        
        # Determinar cumplimiento general
        overall_compliant = len(blocked_reasons) == 0
        
        report = EthicsReport(
            action_type=action_type,
            overall_compliant=overall_compliant,
            overall_risk=max_risk,
            evaluations=evaluations,
            recommendations=recommendations,
            blocked_reasons=blocked_reasons
        )
        
        # Guardar en historial
        self._evaluations_history.append(report)
        
        # Notificar violación
        if not overall_compliant and self._on_violation:
            self._on_violation(report)
        
        return report
    
    def quick_check(
        self,
        action_type: ActionType,
        context: Dict[str, Any]
    ) -> bool:
        """
        Verificación rápida de cumplimiento ético.
        
        Returns:
            True si la acción es éticamente aceptable
        """
        report = self.evaluate(action_type, context)
        return report.overall_compliant
    
    def get_risk_assessment(
        self,
        action_type: ActionType,
        context: Dict[str, Any]
    ) -> RiskLevel:
        """
        Obtiene el nivel de riesgo de una acción.
        
        Returns:
            RiskLevel de la acción
        """
        report = self.evaluate(action_type, context)
        return report.overall_risk
    
    def get_requirements(
        self,
        action_type: ActionType,
        context: Dict[str, Any]
    ) -> List[str]:
        """
        Obtiene los requisitos para ejecutar una acción.
        
        Returns:
            Lista de requisitos (consentimiento, disclosure, etc.)
        """
        report = self.evaluate(action_type, context)
        
        requirements = set()
        for eval in report.evaluations:
            requirements.update(eval.requirements)
        
        return list(requirements)
    
    def on_violation(self, callback: callable) -> None:
        """Registra callback para violaciones éticas"""
        self._on_violation = callback
    
    def get_rules(self) -> List[EthicalRule]:
        """Obtiene todas las reglas"""
        return list(self._rules.values())
    
    def get_evaluation_history(self, limit: int = 100) -> List[EthicsReport]:
        """Obtiene historial de evaluaciones"""
        return self._evaluations_history[-limit:]
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del motor"""
        total = len(self._evaluations_history)
        violations = sum(1 for r in self._evaluations_history if not r.overall_compliant)
        
        return {
            "total_evaluations": total,
            "violations": violations,
            "compliance_rate": (total - violations) / total if total > 0 else 1.0,
            "rules_count": len(self._rules)
        }
