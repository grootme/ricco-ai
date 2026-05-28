"""
Sistema de Seguridad y Guardrails para el Super Asistente.
Implementa patrones de NeMo Guardrails para input/output validation.
"""

from typing import Any, Dict, List, Optional, Callable, Union, Set
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
import re
import hashlib
from dataclasses import dataclass


# =============================================================================
# ENUMS Y TIPOS
# =============================================================================

class RailStatus(str, Enum):
    """Estados de un rail."""
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    MODIFIED = "modified"


class RailType(str, Enum):
    """Tipos de rails."""
    INPUT = "input"
    OUTPUT = "output"
    TOOL_INPUT = "tool_input"
    TOOL_OUTPUT = "tool_output"
    RETRIEVAL = "retrieval"


class SeverityLevel(str, Enum):
    """Niveles de severidad."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# =============================================================================
# MODELOS
# =============================================================================

class RailResult(BaseModel):
    """Resultado de aplicar un rail."""
    status: RailStatus
    original_content: str
    modified_content: Optional[str] = None
    reason: Optional[str] = None
    severity: SeverityLevel = SeverityLevel.LOW
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SecurityAlert(BaseModel):
    """Alerta de seguridad."""
    alert_id: str
    alert_type: str
    severity: SeverityLevel
    content: str
    reason: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    action_taken: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# INTERFACES BASE
# =============================================================================

class BaseRail(ABC):
    """
    Clase base abstracta para todos los rails.
    Inspirado en NeMo Guardrails.
    """
    
    def __init__(
        self,
        name: str,
        enabled: bool = True,
        action: str = "block"  # "block", "modify", "warn"
    ):
        self.name = name
        self.enabled = enabled
        self.action = action
    
    @abstractmethod
    async def check(self, content: str, context: Dict[str, Any]) -> RailResult:
        """
        Verifica el contenido contra este rail.
        """
        pass
    
    async def apply(self, content: str, context: Dict[str, Any]) -> RailResult:
        """
        Aplica el rail al contenido.
        """
        if not self.enabled:
            return RailResult(
                status=RailStatus.ALLOWED,
                original_content=content,
                reason="Rail disabled"
            )
        
        result = await self.check(content, context)
        
        # Aplicar acción según configuración
        if result.status == RailStatus.BLOCKED and self.action == "warn":
            # Solo advertir, no bloquear
            result.status = RailStatus.ALLOWED
            result.metadata["warning"] = True
        
        return result


# =============================================================================
# RAILS DE ENTRADA (INPUT RAILS)
# =============================================================================

class JailbreakDetectionRail(BaseRail):
    """
    Detecta intentos de jailbreak en el input.
    """
    
    JAILBREAK_PATTERNS = [
        r"ignore\s+(all\s+)?(previous|above)\s+(instructions|rules)",
        r"disregard\s+(all\s+)?(previous|above)\s+(instructions|rules)",
        r"you\s+are\s+now\s+(a|an)\s+\w+",
        r"pretend\s+(you\s+are|to\s+be)",
        r"act\s+as\s+(if|a|an)",
        r"bypass\s+(all\s+)?(security|filters|rules)",
        r"override\s+(all\s+)?(previous|default)\s+(instructions|settings)",
        r"<\|.*?\|>",  # Special tokens
        r"\[SYSTEM\]",
        r"\[INST\]",
    ]
    
    def __init__(self, **kwargs):
        super().__init__(name="jailbreak_detection", **kwargs)
        self.patterns = [
            re.compile(p, re.IGNORECASE) for p in self.JAILBREAK_PATTERNS
        ]
    
    async def check(self, content: str, context: Dict[str, Any]) -> RailResult:
        detected_patterns = []
        
        for pattern in self.patterns:
            if pattern.search(content):
                detected_patterns.append(pattern.pattern)
        
        if detected_patterns:
            return RailResult(
                status=RailStatus.BLOCKED,
                original_content=content,
                reason=f"Patrones de jailbreak detectados: {detected_patterns}",
                severity=SeverityLevel.HIGH,
                metadata={"patterns": detected_patterns}
            )
        
        return RailResult(
            status=RailStatus.ALLOWED,
            original_content=content
        )


class ContentSafetyRail(BaseRail):
    """
    Verifica seguridad del contenido.
    """
    
    UNSAFE_KEYWORDS = [
        # Violencia
        "kill", "murder", "attack", "bomb", "terrorist",
        # Contenido ilegal
        "illegal", "drug trafficking", "child abuse",
        # Self-harm
        "suicide", "self-harm", "kill myself",
    ]
    
    def __init__(self, custom_keywords: Optional[List[str]] = None, **kwargs):
        super().__init__(name="content_safety", **kwargs)
        self.unsafe_keywords = set(self.UNSAFE_KEYWORDS)
        if custom_keywords:
            self.unsafe_keywords.update(k.lower() for k in custom_keywords)
    
    async def check(self, content: str, context: Dict[str, Any]) -> RailResult:
        content_lower = content.lower()
        detected = []
        
        for keyword in self.unsafe_keywords:
            if keyword in content_lower:
                detected.append(keyword)
        
        if detected:
            return RailResult(
                status=RailStatus.BLOCKED,
                original_content=content,
                reason=f"Contenido potencialmente inseguro detectado",
                severity=SeverityLevel.HIGH,
                metadata={"keywords": detected}
            )
        
        return RailResult(
            status=RailStatus.ALLOWED,
            original_content=content
        )


class SensitiveDataMaskingRail(BaseRail):
    """
    Enmascara datos sensibles (PII, API keys, etc.)
    """
    
    PATTERNS = {
        "email": (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_REDACTED]'),
        "phone": (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE_REDACTED]'),
        "ssn": (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN_REDACTED]'),
        "credit_card": (r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CARD_REDACTED]'),
        "api_key": (r'\b(api[_-]?key|apikey|token|secret)[\s:=]+["\']?[\w-]{20,}["\']?', '[API_KEY_REDACTED]'),
        "password": (r'\b(password|passwd|pwd)[\s:=]+["\']?[^"\s\'"\'"\'"\']+["\']?', '[PASSWORD_REDACTED]'),
    }
    
    def __init__(self, mask_types: Optional[List[str]] = None, **kwargs):
        super().__init__(name="sensitive_data_masking", action="modify", **kwargs)
        self.mask_types = mask_types or list(self.PATTERNS.keys())
    
    async def check(self, content: str, context: Dict[str, Any]) -> RailResult:
        modified = content
        masked_items = []
        
        for data_type, (pattern, replacement) in self.PATTERNS.items():
            if data_type in self.mask_types:
                regex = re.compile(pattern, re.IGNORECASE)
                matches = regex.findall(content)
                if matches:
                    modified = regex.sub(replacement, modified)
                    masked_items.append(data_type)
        
        if masked_items:
            return RailResult(
                status=RailStatus.MODIFIED,
                original_content=content,
                modified_content=modified,
                reason=f"Datos sensibles enmascarados: {masked_items}",
                severity=SeverityLevel.MEDIUM,
                metadata={"masked_types": masked_items}
            )
        
        return RailResult(
            status=RailStatus.ALLOWED,
            original_content=content
        )


class InjectionDetectionRail(BaseRail):
    """
    Detecta intentos de inyección (SQL, código, etc.)
    """
    
    INJECTION_PATTERNS = {
        "sql": [
            r"('\s*(OR|AND)\s*')", 
            r"(UNION\s+SELECT)",
            r"(;\s*DROP\s+TABLE)",
            r"(--\s*$)",
            r"('\s*=\s*')",
        ],
        "xss": [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
        ],
        "code": [
            r"__import__\s*\(",
            r"eval\s*\(",
            r"exec\s*\(",
            r"subprocess\.",
            r"os\.system",
        ],
        "template": [
            r"\{\{.*?\}\}",
            r"\$\{.*?\}",
            r"<%.*?%>",
        ]
    }
    
    def __init__(self, injection_types: Optional[List[str]] = None, **kwargs):
        super().__init__(name="injection_detection", **kwargs)
        self.injection_types = injection_types or list(self.INJECTION_PATTERNS.keys())
        self._compile_patterns()
    
    def _compile_patterns(self):
        self.compiled_patterns = {}
        for inj_type in self.injection_types:
            if inj_type in self.INJECTION_PATTERNS:
                self.compiled_patterns[inj_type] = [
                    re.compile(p, re.IGNORECASE) 
                    for p in self.INJECTION_PATTERNS[inj_type]
                ]
    
    async def check(self, content: str, context: Dict[str, Any]) -> RailResult:
        detected = {}
        
        for inj_type, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(content):
                    if inj_type not in detected:
                        detected[inj_type] = []
                    detected[inj_type].append(pattern.pattern)
        
        if detected:
            return RailResult(
                status=RailStatus.BLOCKED,
                original_content=content,
                reason=f"Inyección detectada: {list(detected.keys())}",
                severity=SeverityLevel.HIGH,
                metadata={"injection_types": detected}
            )
        
        return RailResult(
            status=RailStatus.ALLOWED,
            original_content=content
        )


# =============================================================================
# RAILS DE SALIDA (OUTPUT RAILS)
# =============================================================================

class HallucinationDetectionRail(BaseRail):
    """
    Detecta posibles alucinaciones en las respuestas.
    """
    
    HALLUCINATION_INDICATORS = [
        r"I'm not sure, but",
        r"I think (it|that|maybe)",
        r"(probably|possibly|might be|could be)",
        r"I don't have (access to|information about)",
        r"as of my (last|current) knowledge",
    ]
    
    def __init__(self, **kwargs):
        super().__init__(name="hallucination_detection", action="warn", **kwargs)
        self.patterns = [
            re.compile(p, re.IGNORECASE) 
            for p in self.HALLUCINATION_INDICATORS
        ]
    
    async def check(self, content: str, context: Dict[str, Any]) -> RailResult:
        warnings = []
        
        for pattern in self.patterns:
            if pattern.search(content):
                warnings.append(pattern.pattern)
        
        if warnings:
            return RailResult(
                status=RailStatus.ALLOWED,
                original_content=content,
                severity=SeverityLevel.MEDIUM,
                reason="Posible indicador de alucinación detectado",
                metadata={"warnings": warnings}
            )
        
        return RailResult(
            status=RailStatus.ALLOWED,
            original_content=content
        )


class FactCheckingRail(BaseRail):
    """
    Rail para verificación de hechos (placeholder).
    En producción, integraría con servicios de fact-checking.
    """
    
    def __init__(self, **kwargs):
        super().__init__(name="fact_checking", action="warn", **kwargs)
    
    async def check(self, content: str, context: Dict[str, Any]) -> RailResult:
        # Placeholder - en producción usar servicios de fact-checking
        # como ClaimBuster, Google Fact Check API, etc.
        
        # Por ahora, solo verificar claims numéricos simples
        # que puedan ser verificados
        
        return RailResult(
            status=RailStatus.ALLOWED,
            original_content=content
        )


# =============================================================================
# GESTOR DE GUARDRAILS
# =============================================================================

class GuardrailsManager:
    """
    Gestor central de todos los guardrails.
    Coordina la aplicación de rails de entrada, salida y herramientas.
    """
    
    def __init__(
        self,
        input_rails: Optional[List[BaseRail]] = None,
        output_rails: Optional[List[BaseRail]] = None,
        tool_input_rails: Optional[List[BaseRail]] = None,
        tool_output_rails: Optional[List[BaseRail]] = None,
        parallel_execution: bool = True
    ):
        self.input_rails = input_rails or []
        self.output_rails = output_rails or []
        self.tool_input_rails = tool_input_rails or []
        self.tool_output_rails = tool_output_rails or []
        self.parallel = parallel_execution
        
        self._alerts: List[SecurityAlert] = []
    
    async def _apply_rails(
        self,
        content: str,
        rails: List[BaseRail],
        context: Dict[str, Any]
    ) -> RailResult:
        """
        Aplica una lista de rails al contenido.
        """
        import asyncio
        
        current_content = content
        
        if self.parallel:
            # Ejecutar todos los rails en paralelo
            tasks = [rail.apply(current_content, context) for rail in rails]
            results = await asyncio.gather(*tasks)
            
            # Revisar resultados
            for result in results:
                if result.status == RailStatus.BLOCKED:
                    self._log_alert(result, context)
                    return result
                elif result.status == RailStatus.MODIFIED:
                    current_content = result.modified_content or current_content
            
            # Si hubo modificaciones, retornar el contenido modificado
            if current_content != content:
                return RailResult(
                    status=RailStatus.MODIFIED,
                    original_content=content,
                    modified_content=current_content,
                    reason="Contenido modificado por rails"
                )
            
            return RailResult(
                status=RailStatus.ALLOWED,
                original_content=content
            )
        else:
            # Ejecutar rails secuencialmente
            for rail in rails:
                result = await rail.apply(current_content, context)
                
                if result.status == RailStatus.BLOCKED:
                    self._log_alert(result, context)
                    return result
                elif result.status == RailStatus.MODIFIED:
                    current_content = result.modified_content or current_content
            
            if current_content != content:
                return RailResult(
                    status=RailStatus.MODIFIED,
                    original_content=content,
                    modified_content=current_content
                )
            
            return RailResult(
                status=RailStatus.ALLOWED,
                original_content=content
            )
    
    def _log_alert(self, result: RailResult, context: Dict[str, Any]) -> None:
        """Registra una alerta de seguridad."""
        alert = SecurityAlert(
            alert_id=hashlib.md5(
                f"{result.original_content}{datetime.utcnow()}".encode()
            ).hexdigest()[:12],
            alert_type="rail_violation",
            severity=result.severity,
            content=result.original_content[:200],
            reason=result.reason or "Unknown",
            action_taken="blocked" if result.status == RailStatus.BLOCKED else "modified",
            metadata=result.metadata
        )
        self._alerts.append(alert)
    
    async def check_input(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> RailResult:
        """Verifica el contenido de entrada."""
        return await self._apply_rails(
            content,
            self.input_rails,
            context or {}
        )
    
    async def check_output(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> RailResult:
        """Verifica el contenido de salida."""
        return await self._apply_rails(
            content,
            self.output_rails,
            context or {}
        )
    
    async def check_tool_input(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> RailResult:
        """Verifica los argumentos de entrada de una herramienta."""
        import json
        content = json.dumps({"tool": tool_name, "args": arguments})
        return await self._apply_rails(
            content,
            self.tool_input_rails,
            context or {}
        )
    
    async def check_tool_output(
        self,
        tool_name: str,
        output: str,
        context: Optional[Dict[str, Any]] = None
    ) -> RailResult:
        """Verifica la salida de una herramienta."""
        content = f"{tool_name}: {output}"
        return await self._apply_rails(
            content,
            self.tool_output_rails,
            context or {}
        )
    
    def get_alerts(
        self,
        severity: Optional[SeverityLevel] = None,
        limit: int = 100
    ) -> List[SecurityAlert]:
        """Obtiene alertas de seguridad."""
        alerts = self._alerts
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        return alerts[-limit:]
    
    def clear_alerts(self) -> None:
        """Limpia el historial de alertas."""
        self._alerts.clear()
    
    def add_input_rail(self, rail: BaseRail) -> None:
        """Agrega un rail de entrada."""
        self.input_rails.append(rail)
    
    def add_output_rail(self, rail: BaseRail) -> None:
        """Agrega un rail de salida."""
        self.output_rails.append(rail)


# =============================================================================
# FACTORY
# =============================================================================

def create_default_guardrails(
    enable_jailbreak: bool = True,
    enable_content_safety: bool = True,
    enable_pii_masking: bool = True,
    enable_injection: bool = True,
    enable_hallucination: bool = True,
    parallel: bool = True
) -> GuardrailsManager:
    """
    Factory para crear el gestor de guardrails con configuración por defecto.
    """
    input_rails = []
    output_rails = []
    
    if enable_jailbreak:
        input_rails.append(JailbreakDetectionRail())
    
    if enable_content_safety:
        input_rails.append(ContentSafetyRail())
        output_rails.append(ContentSafetyRail())
    
    if enable_pii_masking:
        input_rails.append(SensitiveDataMaskingRail())
    
    if enable_injection:
        input_rails.append(InjectionDetectionRail())
    
    if enable_hallucination:
        output_rails.append(HallucinationDetectionRail())
    
    return GuardrailsManager(
        input_rails=input_rails,
        output_rails=output_rails,
        parallel_execution=parallel
    )
