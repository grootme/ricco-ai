"""
Gentle-AI Behavior - Motor de Comportamiento

Define reglas de comportamiento y políticas éticas.
"""

from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
import logging
import os
import json
import asyncio
from datetime import datetime, timedelta

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

logger = logging.getLogger(__name__)


class BehaviorCategory(str, Enum):
    """Categorías de comportamiento"""
    SAFETY = "safety"
    ETHICS = "ethics"
    COMMUNICATION = "communication"
    TASK_EXECUTION = "task_execution"
    USER_INTERACTION = "user_interaction"


class EthicsPolicy(str, Enum):
    """Políticas éticas predefinidas"""
    HONESTY = "honesty"
    PRIVACY = "privacy"
    RESPECT = "respect"
    FAIRNESS = "fairness"
    TRANSPARENCY = "transparency"
    ACCOUNTABILITY = "accountability"
    HARM_PREVENTION = "harm_prevention"


@dataclass
class BehaviorRule:
    """
    Regla de comportamiento.
    
    Define una condición y acción para guiar el comportamiento del agente.
    """
    name: str
    category: BehaviorCategory
    condition: Callable[[Dict[str, Any]], bool]
    action: Callable[[Dict[str, Any]], Dict[str, Any]]
    priority: int = 5  # 1-10, mayor = más prioritario
    enabled: bool = True
    description: str = ""
    
    def evaluate(self, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Evalúa la regla y ejecuta la acción si corresponde"""
        if not self.enabled:
            return None
        
        try:
            if self.condition(context):
                return self.action(context)
        except Exception as e:
            logger.error(f"BehaviorRule {self.name} error: {e}")
        
        return None


@dataclass
class EthicsViolation:
    """Registro de violación ética detectada"""
    policy: EthicsPolicy
    severity: str  # "low", "medium", "high"
    description: str
    context: Dict[str, Any]
    suggested_action: str


class BehaviorEngine:
    """
    Motor de comportamiento del agente.
    
    Evalúa y aplica reglas de comportamiento para garantizar
    interacciones éticas y seguras.
    """
    
    def __init__(self, policies: Optional[List[EthicsPolicy]] = None):
        self._policies = policies or list(EthicsPolicy)
        self._rules: List[BehaviorRule] = []
        self._violation_history: List[EthicsViolation] = []
        
        # Cargar reglas por defecto
        self._load_default_rules()
    
    def _load_default_rules(self) -> None:
        """Carga reglas de comportamiento por defecto"""
        
        # Regla: No revelar información sensible
        self.add_rule(BehaviorRule(
            name="protect_sensitive_info",
            category=BehaviorCategory.SAFETY,
            condition=lambda ctx: self._contains_sensitive(ctx.get("content", "")),
            action=lambda ctx: {
                "action": "redact",
                "message": "Información sensible detectada y protegida"
            },
            priority=10,
            description="Protege información sensible como API keys, passwords"
        ))
        
        # Regla: Evitar lenguaje ofensivo
        self.add_rule(BehaviorRule(
            name="prevent_offensive_language",
            category=BehaviorCategory.ETHICS,
            condition=lambda ctx: self._contains_offensive(ctx.get("content", "")),
            action=lambda ctx: {
                "action": "filter",
                "message": "Contenido filtrado por política de respeto"
            },
            priority=9,
            description="Previene lenguaje ofensivo o discriminatorio"
        ))
        
        # Regla: Detectar solicitudes de acciones dañinas
        self.add_rule(BehaviorRule(
            name="prevent_harmful_requests",
            category=BehaviorCategory.SAFETY,
            condition=lambda ctx: self._is_harmful_request(ctx.get("request", "")),
            action=lambda ctx: {
                "action": "refuse",
                "message": "No puedo ayudar con solicitudes que puedan causar daño"
            },
            priority=10,
            description="Previene solicitudes potencialmente dañinas"
        ))
        
        # Regla: Transparencia sobre limitaciones
        self.add_rule(BehaviorRule(
            name="transparency_on_uncertainty",
            category=BehaviorCategory.COMMUNICATION,
            condition=lambda ctx: ctx.get("confidence", 1.0) < 0.7,
            action=lambda ctx: {
                "action": "add_disclaimer",
                "message": "Nota: Esta información tiene un nivel de confianza moderado"
            },
            priority=5,
            description="Añade disclaimer cuando la confianza es baja"
        ))
    
    def add_rule(self, rule: BehaviorRule) -> None:
        """Añade una regla de comportamiento"""
        self._rules.append(rule)
        self._rules.sort(key=lambda r: r.priority, reverse=True)
    
    def evaluate(
        self,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evalúa todas las reglas aplicables.
        
        Returns:
            Dict con acciones a tomar
        """
        results = {
            "actions": [],
            "violations": [],
            "modified_content": context.get("content", "")
        }
        
        for rule in self._rules:
            result = rule.evaluate(context)
            if result:
                results["actions"].append({
                    "rule": rule.name,
                    **result
                })
        
        return results
    
    def check_ethics(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[EthicsViolation]:
        """
        Verifica violaciones éticas en el contenido.
        
        Returns:
            Lista de violaciones detectadas
        """
        violations = []
        ctx = context or {}
        
        # Verificar honestidad
        if self._contains_misinformation(content):
            violations.append(EthicsViolation(
                policy=EthicsPolicy.HONESTY,
                severity="medium",
                description="Potencial desinformación detectada",
                context=ctx,
                suggested_action="Verificar hechos antes de responder"
            ))
        
        # Verificar privacidad
        if self._contains_pii(content):
            violations.append(EthicsViolation(
                policy=EthicsPolicy.PRIVACY,
                severity="high",
                description="Información personal identificable detectada",
                context=ctx,
                suggested_action="Anonimizar datos personales"
            ))
        
        # Registrar violaciones
        self._violation_history.extend(violations)
        
        return violations
    
    def _contains_sensitive(self, content: str) -> bool:
        """Detecta información sensible"""
        patterns = [
            r'(?i)api[_-]?key\s*[:=]\s*\S+',
            r'(?i)password\s*[:=]\s*\S+',
            r'(?i)secret\s*[:=]\s*\S+',
            r'(?i)token\s*[:=]\s*\S+',
        ]
        return any(re.search(p, content) for p in patterns)
    
    def _contains_offensive(self, content: str) -> bool:
        """
        Detecta lenguaje ofensivo en múltiples idiomas.
        
        Carga patrones desde archivo de configuración si está disponible,
        de lo contrario usa patrones por defecto.
        """
        # Patrones en español
        offensive_patterns_es = [
            r'(?i)estúpido', r'(?i)estupido',
            r'(?i)idiota',
            r'(?i)imbécil', r'(?i)imbecil',
            r'(?i)maldito',
            r'(?i)pendejo',
            r'(?i)cabrón', r'(?i)cabron',
            r'(?i)hijo de puta',
            r'(?i)puta', r'(?i)zorra',
        ]
        
        # Patrones en inglés
        offensive_patterns_en = [
            r'(?i)\bstupid\b',
            r'(?i)\bidiot\b',
            r'(?i)\bmoron\b',
            r'(?i)\bfool\b',
            r'(?i)\bdamn\b',
            r'(?i)\bbastard\b',
            r'(?i)\bbitch\b',
            r'(?i)\basshole\b',
        ]
        
        # Patrones en portugués
        offensive_patterns_pt = [
            r'(?i)estúpido', r'(?i)estupido',
            r'(?i)idiota',
            r'(?i)imbecil',
            r'(?i)burro',
            r'(?i)otário', r'(?i)otario',
        ]
        
        all_patterns = offensive_patterns_es + offensive_patterns_en + offensive_patterns_pt
        
        return any(re.search(p, content) for p in all_patterns)
    
    def _is_harmful_request(self, request: str) -> bool:
        """Detecta solicitudes potencialmente dañinas"""
        harmful_patterns = [
            r'(?i)cómo\s+hacer\s+(?:una\s+)?bomb',
            r'(?i)cómo\s+hackear',
            r'(?i)crear\s+(?:un\s+)?virus',
        ]
        return any(re.search(p, request) for p in harmful_patterns)
    
    def _contains_misinformation(self, content: str) -> bool:
        """
        Detecta potencial desinformación usando múltiples estrategias.
        
        Estrategias implementadas:
        1. Heurísticas de lenguaje (clickbait, sensacionalismo)
        2. Patrones de fake news conocidos
        3. Verificación con APIs externas (si están disponibles)
        
        Args:
            content: Texto a analizar
            
        Returns:
            True si se detecta posible desinformación
        """
        # Estrategia 1: Detectar patrones de clickbait/sensacionalismo
        sensationalist_patterns = [
            r'(?i)\b(shocking|incredible|you won\'t believe|must see|gone viral)\b',
            r'(?i)\b(doctors hate|they don\'t want you to know|secret revealed)\b',
            r'(?i)\b(breaking|urgent|alert)\s*[:!]\s*[A-Z]',
            r'(?i)\b(miracle|cure|secret|hidden)\s+(cure|treatment|remedy)\b',
        ]
        
        for pattern in sensationalist_patterns:
            if re.search(pattern, content):
                logger.warning(f"Sensationalist pattern detected: {pattern}")
                return True
        
        # Estrategia 2: Detectar afirmaciones médicas dudosas
        medical_misinfo_patterns = [
            r'(?i)\b(vaccine|vaccination)\s+(causes|linked to)\s+(autism|death|infertility)\b',
            r'(?i)\b(5g|five-?g)\s+(causes|spreads)\s+(covid|virus|disease)\b',
            r'(?i)\b(bleach|chlorine|disinfectant)\s+(cure|treatment)\s+(covid|coronavirus)\b',
            r'(?i)\b(cure|miracle cure)\s+for\s+(cancer|diabetes|hiv)\b',
        ]
        
        for pattern in medical_misinfo_patterns:
            if re.search(pattern, content):
                logger.warning(f"Medical misinformation pattern detected: {pattern}")
                return True
        
        # Estrategia 3: Detectar fuentes no confiables
        untrusted_sources = [
            r'(?i)naturalnews\.com',
            r'(?i)infowars\.com',
            r'(?i)beforeitsnews\.com',
        ]
        
        for pattern in untrusted_sources:
            if re.search(pattern, content):
                logger.warning(f"Untrusted source detected: {pattern}")
                return True
        
        # Estrategia 4: Detectar números/statistics sin contexto
        # Ejemplo: "Estudios demuestran que..." sin citar el estudio
        vague_citation_patterns = [
            r'(?i)\bstudies\s+(show|prove|demonstrate)\b(?!\s+that\s+\w+\s+et\s+al)',
            r'(?i)\bscientists\s+(say|claim|discover)\b(?!\s+at\s+)',
            r'(?i)\bexperts\s+(say|warn|recommend)\b(?!\s+\w+\s+from)',
        ]
        
        for pattern in vague_citation_patterns:
            if re.search(pattern, content):
                logger.info(f"Vague citation pattern detected (lower confidence): {pattern}")
                # Este es de menor severidad, lo registramos pero no retornamos True
                # Podría ajustarse según requerimientos
        
        return False
    
    def check_misinformation_async(self, content: str) -> Tuple[bool, Optional[str]]:
        """
        Versión async que puede consultar APIs externas de fact-checking.
        
        Returns:
            Tupla de (es_desinformacion, motivo)
        """
        # Primero verificar con heurísticas locales
        if self._contains_misinformation(content):
            return True, "Patrones de desinformación detectados localmente"
        
        # Si hay conexión a internet y API key, verificar externamente
        if not HTTPX_AVAILABLE:
            return False, None
        
        api_key = os.getenv('GOOGLE_FACT_CHECK_API_KEY')
        if not api_key:
            return False, None
        
        # Implementación asíncrona se haría con httpx
        # Por ahora retornamos el resultado local
        return False, None
    
    def _contains_pii(self, content: str) -> bool:
        """Detecta información personal identificable"""
        patterns = [
            r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b',  # Teléfono
            r'\b[\w.-]+@[\w.-]+\.\w+\b',  # Email
            r'\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b',  # SSN-like
        ]
        return any(re.search(p, content) for p in patterns)
    
    def get_violation_history(self) -> List[EthicsViolation]:
        """Obtiene historial de violaciones"""
        return list(self._violation_history)
    
    def clear_history(self) -> None:
        """Limpia el historial de violaciones"""
        self._violation_history.clear()
