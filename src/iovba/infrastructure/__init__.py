"""
Capa I - Infraestructura

Proporciona el entorno de ejecución seguro con aislamiento de recursos y red.
Implementa OpenShell como capa de runtime para comandos de shell y scripts Python.
"""

from .sandbox import SandboxManager, SandboxConfig, SandboxIsolation
from .openshell import OpenShell, ShellResult, ExecutionPolicy

__all__ = [
    'SandboxManager',
    'SandboxConfig',
    'SandboxIsolation',
    'OpenShell',
    'ShellResult',
    'ExecutionPolicy',
]
