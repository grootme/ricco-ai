"""
Behavior Layer - Configuration-Driven Agent Behavior

This module provides persona and ethics management for agents.
All behaviors are configurable and not hardcoded.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import logging

from ...config.agent_config import get_config

logger = logging.getLogger(__name__)


@dataclass
class PersonaConfig:
    """Persona configuration - loaded from role configuration."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    role: str = ""
    name: str = ""
    description: str = ""
    tone: str = "professional"
    style: str = "structured"
    traits: List[str] = field(default_factory=list)
    
    @classmethod
    def from_role_config(cls, role_id: str, role_config: Dict[str, Any]) -> 'PersonaConfig':
        """Create persona from role configuration."""
        return cls(
            role=role_id,
            name=role_config.get("elegant_name", role_id.upper()),
            description=role_config.get("description", ""),
            traits=role_config.get("skills", []),
        )


class PersonaManager:
    """
    Persona Manager - Configuration-driven persona management.
    
    Personas are derived from role configurations, not hardcoded.
    """
    
    def __init__(self):
        self.config = get_config()
        self._personas: Dict[str, PersonaConfig] = {}
        self._load_personas()
    
    def _load_personas(self) -> None:
        """Load personas from role configuration."""
        roles = self.config.get_roles()
        
        for role_id, role_config in roles.items():
            persona = PersonaConfig.from_role_config(role_id, role_config)
            self._personas[role_id] = persona
        
        logger.info(f"Loaded {len(self._personas)} personas from configuration")
    
    def get_persona(self, role_id: str) -> Optional[PersonaConfig]:
        """Get persona for a role."""
        return self._personas.get(role_id)
    
    def get_all_personas(self) -> Dict[str, PersonaConfig]:
        """Get all personas."""
        return self._personas
    
    def get_persona_prompt(self, role_id: str) -> str:
        """Get system prompt addition for a persona."""
        persona = self.get_persona(role_id)
        if not persona:
            return ""
        
        return f"""
## Persona: {persona.name}
{persona.description}

Traits: {', '.join(persona.traits)}
Tone: {persona.tone}
Style: {persona.style}
"""


@dataclass
class EthicsRule:
    """Ethics rule configuration."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    severity: str = "warning"  # warning, error, block
    enabled: bool = True


class EthicsEngine:
    """
    Ethics Engine - Configuration-driven ethics management.
    
    Ethics rules are loaded from configuration.
    """
    
    def __init__(self):
        self.config = get_config()
        self._rules: Dict[str, EthicsRule] = {}
        self._load_rules()
    
    def _load_rules(self) -> None:
        """Load ethics rules from configuration."""
        # Default ethics rules (could be loaded from a separate config file)
        default_rules = [
            EthicsRule(
                name="no_harm",
                description="Do not generate content that could cause harm",
                severity="block",
            ),
            EthicsRule(
                name="no_bias",
                description="Avoid biased or discriminatory content",
                severity="warning",
            ),
            EthicsRule(
                name="privacy",
                description="Protect user privacy and sensitive information",
                severity="block",
            ),
            EthicsRule(
                name="accuracy",
                description="Strive for accuracy and avoid misinformation",
                severity="warning",
            ),
        ]
        
        for rule in default_rules:
            self._rules[rule.name] = rule
        
        logger.info(f"Loaded {len(self._rules)} ethics rules")
    
    def validate(self, content: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Validate content against ethics rules."""
        violations = []
        
        for rule_name, rule in self._rules.items():
            if not rule.enabled:
                continue
            
            # Simple validation (would be more sophisticated in production)
            if self._check_violation(content, rule):
                violations.append({
                    "rule": rule_name,
                    "severity": rule.severity,
                    "description": rule.description,
                })
        
        return {
            "valid": len([v for v in violations if v["severity"] == "block"]) == 0,
            "violations": violations,
            "warnings": [v for v in violations if v["severity"] == "warning"],
            "blocked": [v for v in violations if v["severity"] == "block"],
        }
    
    def _check_violation(self, content: str, rule: EthicsRule) -> bool:
        """Check if content violates a rule (simplified)."""
        # This is a placeholder - real implementation would use more sophisticated checks
        return False
    
    def add_rule(self, rule: EthicsRule) -> None:
        """Add a new ethics rule."""
        self._rules[rule.name] = rule
    
    def remove_rule(self, rule_name: str) -> None:
        """Remove an ethics rule."""
        if rule_name in self._rules:
            del self._rules[rule_name]


__all__ = [
    "PersonaConfig",
    "PersonaManager",
    "EthicsRule",
    "EthicsEngine",
]
