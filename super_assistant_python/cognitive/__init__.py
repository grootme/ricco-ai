"""
Super Asistente Cognitivo - Módulo Cognitivo
=============================================

Implementación del Capital Cognitivo basado en Promptología Ontológica.

Componentes:
- CognitiveCapital: Activo cognitivo acumulado
- PPCC (Proper Prompt Chat Cycle): Ciclo de interacción estructurado
- SharedObviousness: Contexto compartido de obviedad
- ChatOfAction: Metodología de conversación para acción
"""

from .capital import CognitiveCapital, CapitalType, CapitalEntry
from .ppcc import PPCC, PPCCPhase, PPCCContext
from .obviousness import SharedObviousness, ObviousnessContext
from .coa import ChatOfAction, COAStage, COAContext

__all__ = [
    # Capital Cognitivo
    "CognitiveCapital",
    "CapitalType",
    "CapitalEntry",
    # PPCC
    "PPCC",
    "PPCCPhase",
    "PPCCContext",
    # Obviedad
    "SharedObviousness",
    "ObviousnessContext",
    # Chat of Action
    "ChatOfAction",
    "COAStage",
    "COAContext",
]
