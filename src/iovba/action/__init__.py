"""
Capa A - Acción

Ejecución de comandos, navegación web y acceso a APIs externas.
Implementa MCP (Model Context Protocol) y Sistema de Skills.
"""

from .mcp_registry import MCPRegistry, MCPServerConfig, MCPTool
from .skills_registry import SkillsRegistry, Skill, SkillMetadata
from .executor import ActionExecutor, ExecutionResult, ExecutionStatus

__all__ = [
    'MCPRegistry',
    'MCPServerConfig',
    'MCPTool',
    'SkillsRegistry',
    'Skill',
    'SkillMetadata',
    'ActionExecutor',
    'ExecutionResult',
    'ExecutionStatus',
]
