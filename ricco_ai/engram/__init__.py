"""
Engram - Sistema de Memoria con Control de Versiones

Sistema de memoria persistente para agentes basado en SQLite con FTS5.

Características:
- Topic Keys: Identificadores únicos para memorias
- Versionado: Historial completo de cambios
- FTS5: Búsqueda semántica full-text
- Divulgación Progresiva: Tres niveles de acceso
- Grafo de Conocimiento: Relaciones entre memorias

Basado en principios de gestión de conocimiento cognitivo.
"""

__version__ = "0.1.0"
__author__ = "RICCO AI Team"

from .vcs import MemoryVCS, MemoryEntry, MemoryVersion, DisclosureLevel
from .store import EngramStore, EngramQuery
from .index import MemoryIndex, IndexConfig

__all__ = [
    # VCS
    "MemoryVCS",
    "MemoryEntry",
    "MemoryVersion",
    "DisclosureLevel",
    # Store
    "EngramStore",
    "EngramQuery",
    # Index
    "MemoryIndex",
    "IndexConfig",
]
