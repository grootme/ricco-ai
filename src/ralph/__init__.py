"""
Ralph Loop - Ciclo de Mejora Continua del Capital Cognitivo

Implementa el ciclo: Reflect → Analyze → Learn → Practice → Harvest
para transformar interacciones en activos estratégicos.
"""

from .loop import RalphLoop, RalphPhase, RalphResult
from .harvester import KnowledgeHarvester, HarvestedKnowledge
from .practicer import SkillPracticer, PracticeResult

__all__ = [
    'RalphLoop',
    'RalphPhase',
    'RalphResult',
    'KnowledgeHarvester',
    'HarvestedKnowledge',
    'SkillPracticer',
    'PracticeResult',
]
