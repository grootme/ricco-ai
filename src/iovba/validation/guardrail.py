"""
Guardrail Middleware - Validación en tiempo real

Verifica permisos y autorización de herramientas en tiempo real,
implementando el principio de Zero Trust.
"""

from typing import Optional, Dict, Any, List, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)


class PermissionLevel(str, Enum):
    """Niveles de permiso"""
    DENY = "deny"
    READ_ONLY = "read_only"
    LIMITED = "limited"
    STANDARD = "standard"
    ELEVATED = "elevated"
    ADMIN = "admin"


class ValidationAction(str, Enum):
    """Acciones de validación"""
    ALLOW = "allow"
    WARN = "warn"
    BLOCK = "block"
    REDACT = "redact"
    LOG_ONLY = "log_only"


@dataclass
class ValidationRule:
    """
    Regla de validación para el guardrail.
    
    Define condiciones y acciones para diferentes tipos de contenido.
    """
    name: str
    description: str
    condition: str  # Regex o expresión
    action: ValidationAction
    permission_required: PermissionLevel = PermissionLevel.STANDARD
    message: Optional[str] = None
    redact_pattern: Optional[str] = None
    exceptions: List[str] = field(default_factory=list)
    enabled: bool = True
    priority: int = 100
    
    def evaluate(self, content: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evalúa la regla contra el contenido"""
        if not self.enabled:
            return {"matched": False}
        
        # Buscar pattern
        if re.search(self.condition, content, re.IGNORECASE):
            # Verificar excepciones
            for exception in self.exceptions:
                if exception in content:
                    return {"matched": False, "exception": exception}
            
            result = {
                "matched": True,
                "rule": self.name,
                "action": self.action.value,
                "message": self.message
            }
            
            # Redacción si aplica
            if self.action == ValidationAction.REDACT and self.redact_pattern:
                result["redacted"] = re.sub(
                    self.redact_pattern,
                    "[REDACTED]",
                    content
                )
            
            return result
        
        return {"matched": False}


@dataclass
class ValidationResult:
    """Resultado de validación"""
    allowed: bool
    action: ValidationAction
    rules_matched: List[str]
    warnings: List[str] = field(default_factory=list)
    redacted_content: Optional[str] = None
    required_permission: Optional[PermissionLevel] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class GuardrailMiddleware:
    """
    Middleware de Guardrail para validación en tiempo real.
    
    Implementa el principio de Zero Trust verificando cada acción
    y contenido antes de permitir su ejecución.
    
    Usage:
        guardrail = GuardrailMiddleware()
        
        # Añadir reglas
        guardrail.add_rule(ValidationRule(
            name="no_secrets",
            condition=r"(password|api_key|secret)\\s*[:=]",
            action=ValidationAction.BLOCK,
            message="Posible secreto detectado"
        ))
        
        # Validar
        result = guardrail.validate(content, context)
    """
    
    def __init__(
        self,
        default_permission: PermissionLevel = PermissionLevel.STANDARD
    ):
        """
        Inicializa el guardrail.
        
        Args:
            default_permission: Nivel de permiso por defecto
        """
        self.default_permission = default_permission
        self._rules: List[ValidationRule] = []
        self._permission_overrides: Dict[str, PermissionLevel] = {}
        self._on_validation: Optional[Callable] = None
        
        # Cargar reglas por defecto
        self._load_default_rules()
    
    def _load_default_rules(self) -> None:
        """Carga reglas de seguridad por defecto"""
        # PII - Información personal
        self.add_rule(ValidationRule(
            name="pii_email",
            description="Detecta emails en contenido",
            condition=r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
            action=ValidationAction.WARN,
            message="Posible email detectado",
            priority=50
        ))
        
        self.add_rule(ValidationRule(
            name="pii_phone",
            description="Detecta números de teléfono",
            condition=r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
            action=ValidationAction.WARN,
            message="Posible número de teléfono detectado",
            priority=50
        ))
        
        self.add_rule(ValidationRule(
            name="pii_ssn",
            description="Detecta números de seguro social",
            condition=r"\b\d{3}-\d{2}-\d{4}\b",
            action=ValidationAction.BLOCK,
            message="Número de SSN detectado - bloqueado",
            priority=10
        ))
        
        # Secretos y credenciales
        self.add_rule(ValidationRule(
            name="secrets_api_key",
            description="Detecta posibles API keys",
            condition=r"(api[_-]?key|apikey)\s*[:=]\s*['\"]?[a-zA-Z0-9_-]{10,}",
            action=ValidationAction.REDACT,
            redact_pattern=r"(api[_-]?key|apikey)\s*[:=]\s*['\"]?[a-zA-Z0-9_-]{10,}",
            message="API key detectada y redactada",
            priority=10
        ))
        
        self.add_rule(ValidationRule(
            name="secrets_sk_key",
            description="Detecta posibles secret keys (sk-)",
            condition=r"sk-[a-zA-Z0-9]{20,}",
            action=ValidationAction.REDACT,
            redact_pattern=r"sk-[a-zA-Z0-9]{20,}",
            message="Secret key detectada y redactada",
            priority=10
        ))
        
        self.add_rule(ValidationRule(
            name="secrets_password",
            description="Detecta posibles contraseñas",
            condition=r"(password|passwd|pwd)\s*[:=]\s*['\"]?[^\s]{8,}",
            action=ValidationAction.BLOCK,
            message="Posible contraseña detectada",
            priority=10
        ))
        
        # Comandos peligrosos
        self.add_rule(ValidationRule(
            name="dangerous_rm",
            description="Detecta comandos rm peligrosos",
            condition=r"rm\s+(-[rf]+\s+|/|~)",
            action=ValidationAction.BLOCK,
            message="Comando rm peligroso detectado",
            permission_required=PermissionLevel.ADMIN,
            priority=5
        ))
        
        self.add_rule(ValidationRule(
            name="dangerous_sudo",
            description="Detecta uso de sudo",
            condition=r"\bsudo\b",
            action=ValidationAction.WARN,
            message="Uso de sudo detectado",
            permission_required=PermissionLevel.ELEVATED,
            priority=20
        ))
        
        # Inyección de código
        self.add_rule(ValidationRule(
            name="injection_sql",
            description="Detecta posibles inyecciones SQL",
            condition=r"(;\s*(drop|delete|truncate|insert|update)\s|--|\/\*|\*\/)",
            action=ValidationAction.BLOCK,
            message="Posible inyección SQL detectada",
            priority=5
        ))
        
        self.add_rule(ValidationRule(
            name="injection_script",
            description="Detecta posibles inyecciones de script",
            condition=r"(<script|javascript:|on\w+\s*=)",
            action=ValidationAction.BLOCK,
            message="Posible inyección de script detectada",
            priority=5
        ))
    
    def add_rule(self, rule: ValidationRule) -> None:
        """Añade una regla de validación"""
        self._rules.append(rule)
        self._rules.sort(key=lambda r: r.priority)
    
    def remove_rule(self, name: str) -> bool:
        """Remueve una regla por nombre"""
        for i, rule in enumerate(self._rules):
            if rule.name == name:
                self._rules.pop(i)
                return True
        return False
    
    def validate(
        self,
        content: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Valida contenido contra todas las reglas.
        
        Args:
            content: Contenido a validar
            context: Contexto adicional (usuario, sesión, etc.)
        
        Returns:
            ValidationResult con el resultado de la validación
        """
        context = context or {}
        user_permission = context.get(
            "permission_level",
            self.default_permission
        )
        
        if isinstance(user_permission, str):
            user_permission = PermissionLevel(user_permission)
        
        rules_matched = []
        warnings = []
        redacted_content = content
        highest_action = ValidationAction.ALLOW
        required_permission = None
        
        for rule in self._rules:
            result = rule.evaluate(content, context)
            
            if result.get("matched"):
                rules_matched.append(rule.name)
                
                # Verificar permisos
                if rule.permission_required != PermissionLevel.DENY:
                    if not self._has_permission(
                        user_permission,
                        rule.permission_required
                    ):
                        required_permission = rule.permission_required
                
                # Procesar acción
                if rule.action == ValidationAction.BLOCK:
                    highest_action = ValidationAction.BLOCK
                elif rule.action == ValidationAction.REDACT:
                    if "redacted" in result:
                        redacted_content = result["redacted"]
                    if highest_action != ValidationAction.BLOCK:
                        highest_action = ValidationAction.REDACT
                elif rule.action == ValidationAction.WARN:
                    warnings.append(rule.message or f"Regla {rule.name} activada")
                    if highest_action == ValidationAction.ALLOW:
                        highest_action = ValidationAction.WARN
        
        # Determinar si está permitido
        allowed = highest_action not in [ValidationAction.BLOCK]
        
        result = ValidationResult(
            allowed=allowed,
            action=highest_action,
            rules_matched=rules_matched,
            warnings=warnings,
            redacted_content=redacted_content if highest_action == ValidationAction.REDACT else None,
            required_permission=required_permission
        )
        
        # Emitir evento
        if self._on_validation:
            self._on_validation(result, context)
        
        return result
    
    def validate_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Valida una llamada a herramienta"""
        context = context or {}
        
        # Verificar si la herramienta está en la lista de permitidas
        allowed_tools = context.get("allowed_tools", [])
        restricted_tools = context.get("restricted_tools", [])
        
        if restricted_tools and tool_name in restricted_tools:
            return ValidationResult(
                allowed=False,
                action=ValidationAction.BLOCK,
                rules_matched=["restricted_tool"],
                warnings=[],
                metadata={"reason": f"Herramienta {tool_name} está restringida"}
            )
        
        if allowed_tools and tool_name not in allowed_tools:
            return ValidationResult(
                allowed=False,
                action=ValidationAction.BLOCK,
                rules_matched=["not_in_allowed_list"],
                warnings=[],
                metadata={"reason": f"Herramienta {tool_name} no está en la lista de permitidas"}
            )
        
        # Validar argumentos
        args_str = str(arguments)
        return self.validate(args_str, context)
    
    def validate_file_access(
        self,
        file_path: str,
        operation: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Valida acceso a archivo"""
        context = context or {}
        
        allowed_paths = context.get("allowed_paths", [])
        restricted_paths = context.get("restricted_paths", [])
        
        # Verificar rutas restringidas
        for restricted in restricted_paths:
            if file_path.startswith(restricted):
                return ValidationResult(
                    allowed=False,
                    action=ValidationAction.BLOCK,
                    rules_matched=["restricted_path"],
                    metadata={"reason": f"Ruta {file_path} está restringida"}
                )
        
        # Verificar rutas permitidas
        if allowed_paths:
            for allowed in allowed_paths:
                if file_path.startswith(allowed):
                    return ValidationResult(
                        allowed=True,
                        action=ValidationAction.ALLOW,
                        rules_matched=[]
                    )
            
            return ValidationResult(
                allowed=False,
                action=ValidationAction.BLOCK,
                rules_matched=["not_in_allowed_paths"],
                metadata={"reason": f"Ruta {file_path} no está permitida"}
            )
        
        return ValidationResult(
            allowed=True,
            action=ValidationAction.ALLOW,
            rules_matched=[]
        )
    
    def _has_permission(
        self,
        user_level: PermissionLevel,
        required_level: PermissionLevel
    ) -> bool:
        """Verifica si el usuario tiene el permiso requerido"""
        levels = [
            PermissionLevel.DENY,
            PermissionLevel.READ_ONLY,
            PermissionLevel.LIMITED,
            PermissionLevel.STANDARD,
            PermissionLevel.ELEVATED,
            PermissionLevel.ADMIN
        ]
        
        try:
            return levels.index(user_level) >= levels.index(required_level)
        except ValueError:
            return False
    
    def set_permission_override(
        self,
        session_id: str,
        permission: PermissionLevel
    ) -> None:
        """Establece un override de permiso para una sesión"""
        self._permission_overrides[session_id] = permission
    
    def get_permission(
        self,
        session_id: str,
        default: Optional[PermissionLevel] = None
    ) -> PermissionLevel:
        """Obtiene el nivel de permiso para una sesión"""
        return self._permission_overrides.get(
            session_id,
            default or self.default_permission
        )
    
    def on_validation(self, callback: Callable) -> None:
        """Registra callback para eventos de validación"""
        self._on_validation = callback
    
    def get_rules(self) -> List[Dict[str, Any]]:
        """Obtiene lista de reglas configuradas"""
        return [
            {
                "name": r.name,
                "description": r.description,
                "action": r.action.value,
                "enabled": r.enabled,
                "priority": r.priority
            }
            for r in self._rules
        ]
