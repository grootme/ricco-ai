"""
Capa O - Orquestación

Coordina sub-agentes jerárquicos y gestión de estados usando LangGraph.
Implementa la cadena de 9 middlewares de deer-flow para procesar cada turno.
"""

from .lead_agent import LeadAgent, AgentState, AgentConfig
from .middleware import (
    MiddlewareChain,
    MiddlewareBase,
    ThreadDataMiddleware,
    SandboxAcquisitionMiddleware,
    ContextSummarizationMiddleware,
    TaskListMiddleware,
    MemoryMiddleware,
    ToolAuthorizationMiddleware,
    ProgressReportingMiddleware,
    ErrorRecoveryMiddleware,
    CheckpointMiddleware
)
from .sub_agent import SubAgent, SubAgentConfig, SubAgentResult

__all__ = [
    'LeadAgent',
    'AgentState',
    'AgentConfig',
    'MiddlewareChain',
    'MiddlewareBase',
    'ThreadDataMiddleware',
    'SandboxAcquisitionMiddleware',
    'ContextSummarizationMiddleware',
    'TaskListMiddleware',
    'MemoryMiddleware',
    'ToolAuthorizationMiddleware',
    'ProgressReportingMiddleware',
    'ErrorRecoveryMiddleware',
    'CheckpointMiddleware',
    'SubAgent',
    'SubAgentConfig',
    'SubAgentResult',
]
