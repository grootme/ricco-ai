"""
Red Neuronal de Obviedades (RNO) - Large Obviousness-Context Model (LOCM)

Modelo que no razona sobre palabras generales, sino sobre la
arquitectura normativa del negocio real. Cada Trasfondo de
Obviedad se modela como una neurona artificial.
"""

from .network import ObviousnessNetwork, ObviousnessNeuron, NetworkState
from .locm import LOCM, LOCMConfig, ReasoningResult

__all__ = [
    'ObviousnessNetwork',
    'ObviousnessNeuron',
    'NetworkState',
    'LOCM',
    'LOCMConfig',
    'ReasoningResult',
]
