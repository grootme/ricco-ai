"""
Gentle-AI - Sistema de Comportamiento y Personalidad para Agentes

Framework para definir comportamientos éticos, tonos de comunicación
y personalidades adaptables para agentes de IA.

Características:
- Personalidades configurables y adaptables
- Tono y estilo de comunicación dinámico
- Comportamientos éticos integrados
- Adaptación contextual al usuario
- Templates de respuesta por dominio

Basado en principios de IA responsable y ética.
"""

__version__ = "0.1.0"
__author__ = "RICCO AI Team"

from .persona import Persona, PersonaConfig, PersonaType, CommunicationStyle, ToneLevel
from .behavior import BehaviorEngine, BehaviorRule, EthicsPolicy
from .adapter import ResponseAdapter, AdaptiveContext

__all__ = [
    # Persona
    "Persona",
    "PersonaConfig",
    "PersonaType",
    "CommunicationStyle",
    "ToneLevel",
    # Behavior
    "BehaviorEngine",
    "BehaviorRule",
    "EthicsPolicy",
    # Adapter
    "ResponseAdapter",
    "AdaptiveContext",
]
