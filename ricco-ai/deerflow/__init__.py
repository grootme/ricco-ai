"""
DeerFlow - Motor de Flujos de Trabajo para Agentes

Sistema de orquestación de workflows basado en grafos dirigidos.
Permite definir, ejecutar y monitorear flujos de trabajo complejos.

Características:
- Grafos de flujo con nodos y edges
- Ejecución secuencial y paralela
- Manejo de errores y reintentos
- State management persistente
- Integración con agentes IOVBA
"""

__version__ = "0.1.0"
__author__ = "RICCO AI Team"

from .core import WorkflowEngine, Workflow, Node, Edge
from .nodes import ActionNode, DecisionNode, ParallelNode, AgentNode
from .execution import ExecutionContext, ExecutionResult

__all__ = [
    "WorkflowEngine",
    "Workflow",
    "Node",
    "Edge",
    "ActionNode",
    "DecisionNode",
    "ParallelNode",
    "AgentNode",
    "ExecutionContext",
    "ExecutionResult",
]
