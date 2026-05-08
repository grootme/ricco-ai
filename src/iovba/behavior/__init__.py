"""
Capa B - Comportamiento

Define el tono, ética y modo de interacción del agente.
Basado en Gentle-AI para comportamientos éticos y responsables.
"""

from .persona import Persona, PersonaConfig, PersonaType
from .ethics import EthicsEngine, EthicalRule, EthicalEvaluation

__all__ = [
    'Persona',
    'PersonaConfig',
    'PersonaType',
    'EthicsEngine',
    'EthicalRule',
    'EthicalEvaluation',
]
