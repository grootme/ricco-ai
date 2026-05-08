"""
Policy Engine - Motor de Políticas Declarativas

Control granular de qué comandos y herramientas son permitidos
mediante reglas declarativas YAML/JSON.
"""

import yaml
import json
from typing import Optional, Dict, Any, List, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from pathlib import Path
import re
import logging

logger = logging.getLogger(__name__)


class PolicyEffect(str, Enum):
    """Efecto de una política"""
    ALLOW = "allow"
    DENY = "deny"
    ALLOW_WITH_CONDITIONS = "allow_with_conditions"


class PolicyResource(str, Enum):
    """Tipos de recursos"""
    TOOL = "tool"
    COMMAND = "command"
    FILE = "file"
    NETWORK = "network"
    API = "api"
    DATABASE = "database"
    SANDBOX = "sandbox"


@dataclass
class PolicyCondition:
    """Condición de una política"""
    type: str  # time, ip, user_role, etc.
    operator: str  # eq, neq, in, not_in, regex, etc.
    value: Any
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evalúa la condición contra el contexto"""
        context_value = context.get(self.type)
        
        if context_value is None:
            return False
        
        if self.operator == "eq":
            return context_value == self.value
        elif self.operator == "neq":
            return context_value != self.value
        elif self.operator == "in":
            return context_value in self.value
        elif self.operator == "not_in":
            return context_value not in self.value
        elif self.operator == "regex":
            return bool(re.match(self.value, str(context_value)))
        elif self.operator == "contains":
            return self.value in context_value
        elif self.operator == "starts_with":
            return str(context_value).startswith(self.value)
        elif self.operator == "ends_with":
            return str(context_value).endswith(self.value)
        elif self.operator == "gt":
            return context_value > self.value
        elif self.operator == "lt":
            return context_value < self.value
        elif self.operator == "gte":
            return context_value >= self.value
        elif self.operator == "lte":
            return context_value <= self.value
        
        return False


@dataclass
class Policy:
    """
    Política de control de acceso.
    
    Define reglas declarativas para controlar qué acciones
    están permitidas bajo qué condiciones.
    """
    id: str
    name: str
    description: str
    effect: PolicyEffect
    resource: PolicyResource
    actions: List[str] = field(default_factory=list)
    conditions: List[PolicyCondition] = field(default_factory=list)
    exceptions: List[str] = field(default_factory=list)
    priority: int = 100
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def evaluate(
        self,
        action: str,
        resource_id: str,
        context: Dict[str, Any]
    ) -> "PolicyResult":
        """
        Evalúa si la acción está permitida por esta política.
        
        Args:
            action: Acción a evaluar
            resource_id: ID del recurso
            context: Contexto de evaluación
        
        Returns:
            PolicyResult con el resultado
        """
        if not self.enabled:
            return PolicyResult(
                policy_id=self.id,
                applicable=False,
                effect=PolicyEffect.DENY,
                reason="Policy disabled"
            )
        
        # Verificar si la acción aplica
        if self.actions and action not in self.actions and "*" not in self.actions:
            return PolicyResult(
                policy_id=self.id,
                applicable=False,
                effect=PolicyEffect.DENY,
                reason=f"Action {action} not in policy actions"
            )
        
        # Verificar excepciones
        for exception in self.exceptions:
            if exception in resource_id:
                return PolicyResult(
                    policy_id=self.id,
                    applicable=True,
                    effect=PolicyEffect.ALLOW,
                    reason="Matched exception"
                )
        
        # Evaluar condiciones
        if self.conditions:
            all_conditions_met = all(
                cond.evaluate(context) for cond in self.conditions
            )
            
            if not all_conditions_met:
                return PolicyResult(
                    policy_id=self.id,
                    applicable=True,
                    effect=PolicyEffect.DENY,
                    reason="Conditions not met"
                )
        
        return PolicyResult(
            policy_id=self.id,
            applicable=True,
            effect=self.effect,
            reason="Policy matched"
        )


@dataclass
class PolicyResult:
    """Resultado de evaluación de política"""
    policy_id: str
    applicable: bool
    effect: PolicyEffect
    reason: str
    conditions_applied: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class PolicyEngine:
    """
    Motor de Políticas Declarativas.
    
    Carga y evalúa políticas desde archivos YAML/JSON,
    determinando si una acción está permitida.
    
    Usage:
        engine = PolicyEngine()
        
        # Cargar políticas
        engine.load_from_file("policies.yaml")
        
        # Evaluar
        result = engine.evaluate(
            resource=PolicyResource.TOOL,
            action="execute",
            resource_id="web_search",
            context={"user_role": "admin"}
        )
    """
    
    def __init__(self, default_effect: PolicyEffect = PolicyEffect.DENY):
        """
        Inicializa el motor de políticas.
        
        Args:
            default_effect: Efecto por defecto cuando no hay políticas que apliquen
        """
        self.default_effect = default_effect
        self._policies: Dict[str, Policy] = {}
        self._policy_cache: Dict[str, PolicyResult] = {}
    
    def load_from_file(self, file_path: str) -> int:
        """
        Carga políticas desde un archivo YAML o JSON.
        
        Args:
            file_path: Ruta al archivo de políticas
        
        Returns:
            Número de políticas cargadas
        """
        path = Path(file_path)
        
        if not path.exists():
            logger.warning(f"Archivo de políticas no encontrado: {file_path}")
            return 0
        
        content = path.read_text()
        
        if path.suffix in [".yaml", ".yml"]:
            data = yaml.safe_load(content)
        else:
            data = json.loads(content)
        
        if not isinstance(data, dict) or "policies" not in data:
            logger.error(f"Formato de archivo de políticas inválido: {file_path}")
            return 0
        
        count = 0
        for policy_data in data["policies"]:
            try:
                policy = self._parse_policy(policy_data)
                self._policies[policy.id] = policy
                count += 1
            except Exception as e:
                logger.error(f"Error parseando política: {e}")
        
        # Invalidar caché
        self._policy_cache.clear()
        
        logger.info(f"Cargadas {count} políticas desde {file_path}")
        return count
    
    def _parse_policy(self, data: Dict[str, Any]) -> Policy:
        """Parsea una política desde diccionario"""
        conditions = []
        for cond_data in data.get("conditions", []):
            conditions.append(PolicyCondition(
                type=cond_data["type"],
                operator=cond_data["operator"],
                value=cond_data["value"]
            ))
        
        return Policy(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            effect=PolicyEffect(data["effect"]),
            resource=PolicyResource(data["resource"]),
            actions=data.get("actions", ["*"]),
            conditions=conditions,
            exceptions=data.get("exceptions", []),
            priority=data.get("priority", 100),
            enabled=data.get("enabled", True),
            metadata=data.get("metadata", {})
        )
    
    def add_policy(self, policy: Policy) -> None:
        """Añade una política directamente"""
        self._policies[policy.id] = policy
        self._policy_cache.clear()
    
    def remove_policy(self, policy_id: str) -> bool:
        """Remueve una política por ID"""
        if policy_id in self._policies:
            del self._policies[policy_id]
            self._policy_cache.clear()
            return True
        return False
    
    def evaluate(
        self,
        resource: PolicyResource,
        action: str,
        resource_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> PolicyResult:
        """
        Evalúa si una acción está permitida.
        
        Args:
            resource: Tipo de recurso
            action: Acción a evaluar
            resource_id: ID específico del recurso
            context: Contexto de evaluación (usuario, rol, etc.)
        
        Returns:
            PolicyResult con el resultado de la evaluación
        """
        context = context or {}
        
        # Clave de caché
        cache_key = f"{resource.value}:{action}:{resource_id}:{hash(frozenset(context.items()))}"
        
        if cache_key in self._policy_cache:
            return self._policy_cache[cache_key]
        
        # Obtener políticas aplicables ordenadas por prioridad
        applicable_policies = [
            p for p in self._policies.values()
            if p.resource == resource and p.enabled
        ]
        applicable_policies.sort(key=lambda p: p.priority)
        
        # Evaluar cada política
        results = []
        for policy in applicable_policies:
            result = policy.evaluate(action, resource_id, context)
            if result.applicable:
                results.append(result)
        
        # Determinar resultado final
        if not results:
            final_result = PolicyResult(
                policy_id="default",
                applicable=True,
                effect=self.default_effect,
                reason="No applicable policies found"
            )
        else:
            # La política con mayor prioridad (menor número) gana
            final_result = results[0]
        
        # Cachear resultado
        self._policy_cache[cache_key] = final_result
        
        return final_result
    
    def check_permission(
        self,
        session_id: str,
        resource: str,
        action: str,
        resource_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> PolicyResult:
        """
        Verifica permisos para una sesión específica.
        
        Método de conveniencia que añade session_id al contexto.
        """
        context = context or {}
        context["session_id"] = session_id
        
        try:
            resource_enum = PolicyResource(resource)
        except ValueError:
            return PolicyResult(
                policy_id="error",
                applicable=False,
                effect=PolicyEffect.DENY,
                reason=f"Unknown resource type: {resource}"
            )
        
        return self.evaluate(resource_enum, action, resource_id, context)
    
    def get_policies_for_resource(
        self,
        resource: PolicyResource
    ) -> List[Policy]:
        """Obtiene todas las políticas para un tipo de recurso"""
        return [p for p in self._policies.values() if p.resource == resource]
    
    def get_all_policies(self) -> List[Policy]:
        """Obtiene todas las políticas"""
        return list(self._policies.values())
    
    def clear_policies(self) -> None:
        """Limpia todas las políticas"""
        self._policies.clear()
        self._policy_cache.clear()
    
    def export_policies(self, format: str = "yaml") -> str:
        """
        Exporta todas las políticas a formato YAML o JSON.
        
        Args:
            format: "yaml" o "json"
        
        Returns:
            String con las políticas exportadas
        """
        policies_data = {
            "policies": [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "effect": p.effect.value,
                    "resource": p.resource.value,
                    "actions": p.actions,
                    "conditions": [
                        {"type": c.type, "operator": c.operator, "value": c.value}
                        for c in p.conditions
                    ],
                    "exceptions": p.exceptions,
                    "priority": p.priority,
                    "enabled": p.enabled,
                    "metadata": p.metadata
                }
                for p in self._policies.values()
            ]
        }
        
        if format == "yaml":
            return yaml.dump(policies_data, default_flow_style=False)
        else:
            return json.dumps(policies_data, indent=2)
