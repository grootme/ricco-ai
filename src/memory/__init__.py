"""
Memory Module - Sistema de Memoria Persistente de Capital Cognitivo

Este módulo implementa el sistema de memoria con control de versiones
que permite al agente aprender y acumular conocimiento estratégico.

Componentes:
- MemoryVCS: Sistema de control de versiones para memorias
- Engram: Almacenamiento persistente con SQLite/FTS5
"""

from .vcs import (
    MemoryVCS,
    MemoryEntry,
    MemoryVersion,
    DisclosureLevel,
    get_memory_vcs,
    reset_memory_vcs
)

__all__ = [
    'MemoryVCS',
    'MemoryEntry',
    'MemoryVersion',
    'DisclosureLevel',
    'get_memory_vcs',
    'reset_memory_vcs'
]
