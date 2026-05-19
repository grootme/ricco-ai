"""
Validation Layer - Configuration-Driven Validation

This module provides guardrail and policy management for agents.
All validations are configurable.
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import uuid
import logging
import re

from ...config.agent_config import get_config

logger = logging.getLogger(__name__)


class ValidationSeverity(str, Enum):
    """Validation severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    BLOCK = "block"


@dataclass
class ValidationResult:
    """Result of a validation check."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    validator_name: str = ""
    passed: bool = True
    severity: ValidationSeverity = ValidationSeverity.INFO
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class GuardrailRule:
    """Guardrail rule configuration."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    pattern: str = ""  # Regex pattern
    action: str = "warn"  # warn, block, transform
    severity: ValidationSeverity = ValidationSeverity.WARNING
    enabled: bool = True


class GuardrailEngine:
    """
    Guardrail Engine - Configuration-driven content guardrails.
    
    Guardrails are loaded from configuration.
    """
    
    def __init__(self):
        self.config = get_config()
        self._rules: Dict[str, GuardrailRule] = {}
        self._load_rules()
    
    def _load_rules(self) -> None:
        """Load guardrail rules from configuration."""
        # Default guardrail rules
        default_rules = [
            GuardrailRule(
                name="no_pii",
                description="Prevent exposure of personally identifiable information",
                pattern=r"\b\d{3}-\d{2}-\d{4}\b",  # SSN pattern example
                action="block",
                severity=ValidationSeverity.BLOCK,
            ),
            GuardrailRule(
                name="no_secrets",
                description="Prevent exposure of secrets and API keys",
                pattern=r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*['\"]?[\w-]+",
                action="block",
                severity=ValidationSeverity.BLOCK,
            ),
            GuardrailRule(
                name="profanity_filter",
                description="Filter inappropriate language",
                action="warn",
                severity=ValidationSeverity.WARNING,
            ),
        ]
        
        for rule in default_rules:
            self._rules[rule.name] = rule
        
        logger.info(f"Loaded {len(self._rules)} guardrail rules")
    
    def validate(self, content: str, context: Optional[Dict[str, Any]] = None) -> List[ValidationResult]:
        """Validate content against all guardrail rules."""
        results = []
        
        for rule_name, rule in self._rules.items():
            if not rule.enabled:
                continue
            
            result = self._check_rule(content, rule)
            results.append(result)
        
        return results
    
    def _check_rule(self, content: str, rule: GuardrailRule) -> ValidationResult:
        """Check content against a single rule."""
        try:
            if rule.pattern:
                matches = re.findall(rule.pattern, content)
                if matches:
                    return ValidationResult(
                        validator_name=rule.name,
                        passed=False,
                        severity=rule.severity,
                        message=f"Rule '{rule.name}' violated: found {len(matches)} matches",
                        details={"matches": matches[:5]},  # Limit matches shown
                    )
            
            return ValidationResult(
                validator_name=rule.name,
                passed=True,
                message=f"Rule '{rule.name}' passed",
            )
            
        except re.error as e:
            logger.error(f"Invalid regex pattern for rule {rule.name}: {e}")
            return ValidationResult(
                validator_name=rule.name,
                passed=True,
                severity=ValidationSeverity.WARNING,
                message=f"Rule '{rule.name}' has invalid pattern",
            )
    
    def add_rule(self, rule: GuardrailRule) -> None:
        """Add a new guardrail rule."""
        self._rules[rule.name] = rule
    
    def remove_rule(self, rule_name: str) -> None:
        """Remove a guardrail rule."""
        if rule_name in self._rules:
            del self._rules[rule_name]


@dataclass
class PolicyRule:
    """Policy rule configuration."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    condition: str = ""  # Condition expression
    action: str = "allow"  # allow, deny, require_approval
    priority: int = 0
    enabled: bool = True


class PolicyEngine:
    """
    Policy Engine - Configuration-driven policy management.
    
    Policies are loaded from configuration.
    """
    
    def __init__(self):
        self.config = get_config()
        self._policies: Dict[str, PolicyRule] = {}
        self._load_policies()
    
    def _load_policies(self) -> None:
        """Load policy rules from configuration."""
        # Default policies
        default_policies = [
            PolicyRule(
                name="default_allow",
                description="Default allow policy",
                action="allow",
                priority=0,
            ),
            PolicyRule(
                name="sensitive_domain_approval",
                description="Require approval for sensitive domains",
                condition="domain in ['salud', 'legal', 'finanzas']",
                action="require_approval",
                priority=10,
            ),
        ]
        
        for policy in default_policies:
            self._policies[policy.name] = policy
        
        logger.info(f"Loaded {len(self._policies)} policy rules")
    
    def evaluate(
        self,
        context: Dict[str, Any],
        action: str = "execute",
    ) -> Dict[str, Any]:
        """Evaluate policies against a context."""
        applicable_policies = []
        
        for policy_name, policy in sorted(
            self._policies.items(),
            key=lambda x: x[1].priority,
            reverse=True
        ):
            if not policy.enabled:
                continue
            
            if self._evaluate_condition(policy.condition, context):
                applicable_policies.append({
                    "policy": policy_name,
                    "action": policy.action,
                    "description": policy.description,
                })
        
        # Determine final action
        final_action = "allow"
        if any(p["action"] == "deny" for p in applicable_policies):
            final_action = "deny"
        elif any(p["action"] == "require_approval" for p in applicable_policies):
            final_action = "require_approval"
        
        return {
            "action": final_action,
            "applicable_policies": applicable_policies,
            "context": context,
        }
    
    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Evaluate a condition expression (simplified)."""
        if not condition:
            return True
        
        try:
            # Simple condition evaluation (would use safer method in production)
            return eval(condition, {"__builtins__": {}}, context)
        except Exception as e:
            logger.warning(f"Error evaluating condition '{condition}': {e}")
            return False
    
    def add_policy(self, policy: PolicyRule) -> None:
        """Add a new policy rule."""
        self._policies[policy.name] = policy
    
    def remove_policy(self, policy_name: str) -> None:
        """Remove a policy rule."""
        if policy_name in self._policies:
            del self._policies[policy_name]


__all__ = [
    "ValidationSeverity",
    "ValidationResult",
    "GuardrailRule",
    "GuardrailEngine",
    "PolicyRule",
    "PolicyEngine",
]
