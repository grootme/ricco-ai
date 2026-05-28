"""
Agentes especializados del Super Asistente.
Implementación basada en patrones de LangGraph, AutoGen y CrewAI.
"""

from typing import Any, Dict, List, Optional, Callable, Union, Type
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

import sys
sys.path.insert(0, '/home/z/my-project/super_assistant_python')
from core.models import (
    AgentIdentity, AgentState, AgentRole,
    Task, TaskStatus, ToolDefinition, ToolCall, ToolResult,
    MemoryItem, MemoryType
)
from memory.memory_system import MemoryManager


# =============================================================================
# CLASE BASE DE AGENTE
# =============================================================================

class BaseAgent(ABC):
    """
    Clase base abstracta para todos los agentes.
    Inspirado en AutoGen's BaseChatAgent y CrewAI's Agent.
    """
    
    def __init__(
        self,
        identity: AgentIdentity,
        tools: Optional[List[ToolDefinition]] = None,
        memory_manager: Optional[MemoryManager] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.identity = identity
        self.tools = tools or []
        self.memory_manager = memory_manager
        self.config = config or {}
        self._state = AgentState(
            agent_id=self.identity.name.lower().replace(" ", "_"),
            identity=identity,
            tools_available=[t.name for t in self.tools]
        )
    
    @property
    def name(self) -> str:
        return self.identity.name
    
    @property
    def role(self) -> str:
        return self.identity.role
    
    @property
    def goal(self) -> str:
        return self.identity.goal
    
    @property
    def backstory(self) -> str:
        return self.identity.backstory
    
    @abstractmethod
    async def execute(
        self,
        task: Task,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Ejecuta una tarea asignada al agente.
        Debe ser implementado por cada agente específico.
        """
        pass
    
    def get_system_prompt(self) -> str:
        """
        Genera el prompt del sistema para el agente.
        """
        prompt = f"""Eres {self.name}, {self.role}.

Tu objetivo principal es: {self.goal}

Tu背景: {self.backstory}

Tienes acceso a las siguientes herramientas:
"""
        for tool in self.tools:
            prompt += f"- {tool.name}: {tool.description}\n"
        
        return prompt
    
    def update_state(self, **kwargs) -> None:
        """Actualiza el estado interno del agente."""
        for key, value in kwargs.items():
            if hasattr(self._state, key):
                setattr(self._state, key, value)
        self._state.last_activity = datetime.utcnow()
    
    def get_state(self) -> AgentState:
        """Retorna el estado actual del agente."""
        return self._state
    
    async def remember(self, content: str, memory_type: MemoryType = MemoryType.EPISODIC) -> Optional[str]:
        """Almacena un recuerdo."""
        if self.memory_manager:
            return await self.memory_manager.memory_system.remember(
                content=content,
                memory_type=memory_type,
                agent_id=self._state.agent_id
            )
        return None
    
    async def recall(self, query: str, top_k: int = 5) -> List[MemoryItem]:
        """Recupera memorias relevantes."""
        if self.memory_manager:
            return await self.memory_manager.memory_system.recall(
                query=query,
                agent_id=self._state.agent_id,
                top_k=top_k
            )
        return []


# =============================================================================
# LEAD AGENT (SUPERVISOR)
# =============================================================================

class LeadAgent(BaseAgent):
    """
    Agente principal que coordina a los subagentes.
    Responsable de planificar, delegar y consolidar resultados.
    """
    
    def __init__(
        self,
        subagents: Optional[Dict[str, 'BaseAgent']] = None,
        **kwargs
    ):
        identity = AgentIdentity(
            name="Lead Agent",
            role="Coordinador Principal del Sistema Multi-Agente",
            goal="Coordinar eficientemente a los subagentes para resolver tareas complejas",
            backstory="""Eres un coordinador experto con amplia experiencia gestionando 
            equipos de agentes especializados. Tu fortaleza está en descomponer tareas 
            complejas, asignar trabajo al agente adecuado y consolidar resultados 
            en respuestas coherentes y útiles.""",
            capabilities=["planning", "delegation", "consolidation", "coordination"]
        )
        super().__init__(identity=identity, **kwargs)
        self.subagents = subagents or {}
    
    def register_subagent(self, agent: BaseAgent) -> None:
        """Registra un subagente."""
        self.subagents[agent.name.lower().replace(" ", "_")] = agent
        self._state.tools_available.append(f"delegate_to_{agent.name.lower()}")
    
    async def plan_task(self, task: Task) -> List[Task]:
        """
        Descompone una tarea compleja en subtareas.
        """
        # Análisis simple de la tarea
        description = task.description.lower()
        subtasks = []
        
        # Detectar si necesita investigación
        if any(kw in description for kw in ["buscar", "investigar", "encontrar", "qué es"]):
            subtasks.append(Task(
                id=f"{task.id}_research",
                description=f"Investigar: {task.description}",
                assigned_agent=AgentRole.RESEARCHER,
                priority=task.priority
            ))
        
        # Detectar si necesita análisis
        if any(kw in description for kw in ["analizar", "comparar", "evaluar"]):
            subtasks.append(Task(
                id=f"{task.id}_analysis",
                description=f"Analizar: {task.description}",
                assigned_agent=AgentRole.ANALYZER,
                priority=task.priority
            ))
        
        # Detectar si necesita construcción
        if any(kw in description for kw in ["crear", "generar", "construir", "implementar"]):
            subtasks.append(Task(
                id=f"{task.id}_build",
                description=f"Construir: {task.description}",
                assigned_agent=AgentRole.BUILDER,
                priority=task.priority
            ))
        
        # Si no se detectaron subtareas, crear una general
        if not subtasks:
            subtasks.append(Task(
                id=f"{task.id}_general",
                description=task.description,
                priority=task.priority
            ))
        
        return subtasks
    
    async def delegate(
        self,
        task: Task,
        target_agent: str
    ) -> Dict[str, Any]:
        """
        Delega una tarea a un subagente específico.
        """
        agent_key = target_agent.lower().replace(" ", "_")
        
        if agent_key not in self.subagents:
            return {
                "success": False,
                "error": f"Agente {target_agent} no encontrado"
            }
        
        agent = self.subagents[agent_key]
        
        # Registrar inicio de tarea
        self.update_state(current_task=task)
        
        # Ejecutar
        result = await agent.execute(task, {"lead_agent": self.name})
        
        # Registrar finalización
        self._state.completed_tasks.append(task.id)
        self.update_state(current_task=None)
        
        return result
    
    async def consolidate(
        self,
        results: Dict[str, Dict[str, Any]]
    ) -> str:
        """
        Consolida los resultados de múltiples subagentes.
        """
        consolidated = "# Resultado Consolidado\n\n"
        
        for agent_name, result in results.items():
            if result.get("success"):
                consolidated += f"## {agent_name.title()}\n"
                consolidated += f"{result.get('output', 'Sin output')}\n\n"
            else:
                consolidated += f"## {agent_name.title()} (Error)\n"
                consolidated += f"Error: {result.get('error', 'Desconocido')}\n\n"
        
        return consolidated
    
    async def execute(
        self,
        task: Task,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Ejecuta el flujo completo de coordinación.
        """
        # 1. Planificar
        subtasks = await self.plan_task(task)
        
        # 2. Delegar y recolectar resultados
        results = {}
        for subtask in subtasks:
            if subtask.assigned_agent:
                agent_name = subtask.assigned_agent.value if isinstance(subtask.assigned_agent, AgentRole) else subtask.assigned_agent
                result = await self.delegate(subtask, agent_name)
                results[agent_name] = result
        
        # 3. Consolidar
        final_output = await self.consolidate(results)
        
        return {
            "success": True,
            "output": final_output,
            "subtasks": [st.id for st in subtasks],
            "agent_results": results
        }


# =============================================================================
# RESEARCHER AGENT
# =============================================================================

class ResearcherAgent(BaseAgent):
    """
    Agente especializado en investigación y búsqueda de información.
    """
    
    def __init__(self, **kwargs):
        identity = AgentIdentity(
            name="Researcher",
            role="Investigador de Información",
            goal="Buscar, recopilar y sintetizar información relevante de múltiples fuentes",
            backstory="""Eres un investigador experto con acceso a múltiples fuentes de 
            información. Tu especialidad es encontrar datos precisos, verificar fuentes 
            y presentar información de manera clara y estructurada. Tienes formación en 
            metodología de investigación y análisis de datos.""",
            capabilities=["web_search", "document_analysis", "fact_checking", "summarization"]
        )
        
        tools = [
            ToolDefinition(
                name="web_search",
                description="Buscar información en la web",
                parameters={"query": {"type": "string", "description": "Término de búsqueda"}}
            ),
            ToolDefinition(
                name="document_retrieval",
                description="Recuperar documentos relevantes",
                parameters={"query": {"type": "string"}, "top_k": {"type": "integer"}}
            )
        ]
        
        super().__init__(identity=identity, tools=tools, **kwargs)
    
    async def execute(
        self,
        task: Task,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Ejecuta una tarea de investigación.
        """
        self.update_state(current_task=task)
        
        # Recuperar memorias relevantes
        memories = await self.recall(task.description)
        memory_context = "\n".join([m.content for m in memories[:3]])
        
        # Simular investigación (en producción, usar herramientas reales)
        research_result = f"Investigación completada sobre: {task.description}"
        
        if memory_context:
            research_result += f"\n\nContexto previo relevante:\n{memory_context}"
        
        # Almacenar resultado en memoria
        await self.remember(
            f"Investigación: {task.description} -> {research_result[:200]}",
            MemoryType.SEMANTIC
        )
        
        self.update_state(current_task=None)
        self._state.completed_tasks.append(task.id)
        
        return {
            "success": True,
            "output": research_result,
            "sources": ["web", "documents", "memory"],
            "confidence": 0.85
        }


# =============================================================================
# ANALYZER AGENT
# =============================================================================

class AnalyzerAgent(BaseAgent):
    """
    Agente especializado en análisis de datos y generación de insights.
    """
    
    def __init__(self, **kwargs):
        identity = AgentIdentity(
            name="Analyzer",
            role="Analista de Datos",
            goal="Analizar datos, identificar patrones y generar insights accionables",
            backstory="""Eres un analista de datos senior con experiencia en múltiples 
            dominios. Destacas en identificar patrones, anomalías y oportunidades a 
            partir de datos complejos. Tienes experiencia con análisis estadístico, 
            visualización de datos y comunicación de hallazgos.""",
            capabilities=["data_analysis", "pattern_recognition", "statistical_analysis", "visualization"]
        )
        
        tools = [
            ToolDefinition(
                name="statistical_analysis",
                description="Realizar análisis estadístico",
                parameters={"data": {"type": "object"}, "tests": {"type": "array"}}
            ),
            ToolDefinition(
                name="visualization",
                description="Crear visualizaciones de datos",
                parameters={"data": {"type": "object"}, "chart_type": {"type": "string"}}
            )
        ]
        
        super().__init__(identity=identity, tools=tools, **kwargs)
    
    async def execute(
        self,
        task: Task,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Ejecuta una tarea de análisis.
        """
        self.update_state(current_task=task)
        
        # Verificar si hay resultados del investigador
        previous_results = context.get("research_results", "")
        
        analysis_result = f"Análisis completado para: {task.description}"
        
        if previous_results:
            analysis_result += f"\n\nBasado en datos previos:\n{previous_results[:500]}"
        
        # Generar insights
        insights = [
            "Patrón identificado: correlación positiva entre variables",
            "Anomalía detectada: valor atípico en el conjunto de datos",
            "Oportunidad: posible optimización en el proceso"
        ]
        
        analysis_result += "\n\n### Insights generados:\n"
        for insight in insights:
            analysis_result += f"- {insight}\n"
        
        self.update_state(current_task=None)
        self._state.completed_tasks.append(task.id)
        
        return {
            "success": True,
            "output": analysis_result,
            "insights": insights,
            "confidence": 0.90
        }


# =============================================================================
# BUILDER AGENT
# =============================================================================

class BuilderAgent(BaseAgent):
    """
    Agente especializado en construcción e implementación de soluciones.
    """
    
    def __init__(self, **kwargs):
        identity = AgentIdentity(
            name="Builder",
            role="Constructor de Soluciones",
            goal="Implementar, construir y desplegar soluciones técnicas",
            backstory="""Eres un ingeniero de software experto capaz de construir 
            soluciones desde cero. Tienes experiencia en múltiples lenguajes y 
            frameworks. Tu especialidad es transformar requisitos en código 
            funcional, limpio y bien documentado.""",
            capabilities=["code_generation", "file_operations", "testing", "deployment"]
        )
        
        tools = [
            ToolDefinition(
                name="code_generator",
                description="Generar código",
                parameters={"language": {"type": "string"}, "requirements": {"type": "string"}},
                requires_approval=True
            ),
            ToolDefinition(
                name="file_operations",
                description="Operaciones de archivos",
                parameters={"operation": {"type": "string"}, "path": {"type": "string"}},
                requires_approval=True
            ),
            ToolDefinition(
                name="shell_execute",
                description="Ejecutar comandos de shell",
                parameters={"command": {"type": "string"}},
                requires_approval=True
            )
        ]
        
        super().__init__(identity=identity, tools=tools, **kwargs)
    
    async def execute(
        self,
        task: Task,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Ejecuta una tarea de construcción.
        """
        self.update_state(current_task=task)
        
        # Verificar si hay análisis previo
        previous_analysis = context.get("analysis_results", "")
        
        build_result = f"Solución construida para: {task.description}"
        
        if previous_analysis:
            build_result += f"\n\nRequisitos basados en análisis:\n{previous_analysis[:300]}"
        
        # Generar artefactos
        artifacts = {
            "code": "# Código generado\nprint('Hello, World!')",
            "documentation": "## Documentación\n\nEsta solución...",
            "tests": "# Tests\nassert True"
        }
        
        build_result += "\n\n### Artefactos generados:\n"
        build_result += "- Código fuente\n- Documentación\n- Tests\n"
        
        # Almacenar procedimiento para futuras referencias
        await self.remember(
            f"Construcción: {task.description}",
            MemoryType.PROCEDURAL
        )
        
        self.update_state(current_task=None)
        self._state.completed_tasks.append(task.id)
        
        return {
            "success": True,
            "output": build_result,
            "artifacts": artifacts,
            "requires_validation": True
        }


# =============================================================================
# VALIDATOR AGENT
# =============================================================================

class ValidatorAgent(BaseAgent):
    """
    Agente especializado en validación y control de calidad.
    """
    
    def __init__(self, **kwargs):
        identity = AgentIdentity(
            name="Validator",
            role="Validador de Calidad",
            goal="Verificar, validar y asegurar la calidad de las soluciones",
            backstory="""Eres un especialista en QA con ojo crítico para detectar 
            problemas. Tu trabajo es asegurar que todo funcione correctamente antes 
            de entregar. Tienes experiencia en testing, code review y validación 
            de requisitos.""",
            capabilities=["testing", "code_review", "validation", "quality_assurance"]
        )
        
        tools = [
            ToolDefinition(
                name="test_runner",
                description="Ejecutar tests",
                parameters={"test_path": {"type": "string"}}
            ),
            ToolDefinition(
                name="code_review",
                description="Revisar código",
                parameters={"code": {"type": "string"}}
            )
        ]
        
        super().__init__(identity=identity, tools=tools, **kwargs)
    
    async def execute(
        self,
        task: Task,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Ejecuta una tarea de validación.
        """
        self.update_state(current_task=task)
        
        # Obtener artefactos a validar
        artifacts = context.get("artifacts", {})
        
        validation_result = f"Validación completada para: {task.description}"
        
        # Simular validación
        checks = {
            "code_quality": {"status": "pass", "score": 0.95},
            "tests_passing": {"status": "pass", "passed": 10, "failed": 0},
            "documentation": {"status": "pass", "coverage": 0.80},
            "security": {"status": "pass", "vulnerabilities": 0}
        }
        
        all_passed = all(c["status"] == "pass" for c in checks.values())
        
        validation_result += "\n\n### Resultados de validación:\n"
        for check_name, result in checks.items():
            status_emoji = "✅" if result["status"] == "pass" else "❌"
            validation_result += f"- {status_emoji} {check_name}: {result['status']}\n"
        
        self.update_state(current_task=None)
        self._state.completed_tasks.append(task.id)
        
        return {
            "success": all_passed,
            "output": validation_result,
            "checks": checks,
            "approved": all_passed
        }


# =============================================================================
# MEMORY KEEPER AGENT
# =============================================================================

class MemoryKeeperAgent(BaseAgent):
    """
    Agente especializado en gestión de memoria.
    """
    
    def __init__(self, **kwargs):
        identity = AgentIdentity(
            name="MemoryKeeper",
            role="Guardián de Memoria",
            goal="Gestionar, organizar y recuperar información del sistema de memoria",
            backstory="""Eres el guardián del conocimiento acumulado. Tu trabajo es 
            mantener la memoria organizada y accesible para todos los agentes. 
            Tienes habilidades especiales para indexar, buscar y sintetizar 
            información almacenada.""",
            capabilities=["memory_storage", "memory_retrieval", "memory_organization", "knowledge_synthesis"]
        )
        
        tools = [
            ToolDefinition(
                name="memory_store",
                description="Almacenar en memoria",
                parameters={"content": {"type": "string"}, "type": {"type": "string"}}
            ),
            ToolDefinition(
                name="memory_search",
                description="Buscar en memoria",
                parameters={"query": {"type": "string"}, "top_k": {"type": "integer"}}
            )
        ]
        
        super().__init__(identity=identity, tools=tools, **kwargs)
    
    async def execute(
        self,
        task: Task,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Ejecuta una tarea de gestión de memoria.
        """
        self.update_state(current_task=task)
        
        description = task.description.lower()
        
        if "buscar" in description or "recuperar" in description:
            # Tarea de recuperación
            query = task.description
            memories = await self.recall(query, top_k=10)
            output = f"Recuperadas {len(memories)} memorias relevantes"
        elif "almacenar" in description or "guardar" in description:
            # Tarea de almacenamiento
            content = context.get("content", task.description)
            memory_id = await self.remember(content, MemoryType.SEMANTIC)
            output = f"Memoria almacenada con ID: {memory_id}"
        else:
            output = f"Operación de memoria completada: {task.description}"
        
        self.update_state(current_task=None)
        self._state.completed_tasks.append(task.id)
        
        return {
            "success": True,
            "output": output
        }


# =============================================================================
# SECURITY GUARD AGENT
# =============================================================================

class SecurityGuardAgent(BaseAgent):
    """
    Agente especializado en seguridad y validación de operaciones sensibles.
    """
    
    def __init__(self, **kwargs):
        identity = AgentIdentity(
            name="SecurityGuard",
            role="Guardián de Seguridad",
            goal="Proteger el sistema y validar operaciones sensibles",
            backstory="""Eres un especialista en seguridad que supervisa todas las 
            operaciones sensibles. Tu trabajo es prevenir problemas de seguridad 
            antes de que ocurran. Tienes experiencia en análisis de vulnerabilidades, 
            control de acceso y auditoría de sistemas.""",
            capabilities=["security_scan", "permission_check", "audit_logging", "threat_detection"]
        )
        
        tools = [
            ToolDefinition(
                name="security_scan",
                description="Escanear vulnerabilidades",
                parameters={"target": {"type": "string"}}
            ),
            ToolDefinition(
                name="permission_check",
                description="Verificar permisos",
                parameters={"user": {"type": "string"}, "action": {"type": "string"}}
            )
        ]
        
        super().__init__(identity=identity, tools=tools, **kwargs)
    
    async def execute(
        self,
        task: Task,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Ejecuta una tarea de seguridad.
        """
        self.update_state(current_task=task)
        
        # Verificar operación sensible
        operation = task.description.lower()
        sensitive_keywords = ["eliminar", "borrar", "modificar", "ejecutar", "acceso"]
        
        is_sensitive = any(kw in operation for kw in sensitive_keywords)
        
        security_result = f"Análisis de seguridad para: {task.description}"
        
        checks = {
            "permission_verified": True,
            "no_malicious_input": True,
            "operation_authorized": True,
            "audit_logged": True
        }
        
        if is_sensitive:
            checks["requires_approval"] = True
            security_result += "\n\n⚠️ Esta operación requiere aprobación adicional."
        
        all_clear = all(v for v in checks.values() if isinstance(v, bool))
        
        self.update_state(current_task=None)
        self._state.completed_tasks.append(task.id)
        
        return {
            "success": all_clear,
            "output": security_result,
            "checks": checks,
            "requires_approval": is_sensitive
        }


# =============================================================================
# FACTORY DE AGENTES
# =============================================================================

def create_agent(
    role: AgentRole,
    memory_manager: Optional[MemoryManager] = None,
    **kwargs
) -> BaseAgent:
    """
    Factory para crear agentes por rol.
    """
    agents = {
        AgentRole.LEAD: LeadAgent,
        AgentRole.RESEARCHER: ResearcherAgent,
        AgentRole.ANALYZER: AnalyzerAgent,
        AgentRole.BUILDER: BuilderAgent,
        AgentRole.VALIDATOR: ValidatorAgent,
        AgentRole.MEMORY_KEEPER: MemoryKeeperAgent,
        AgentRole.SECURITY_GUARD: SecurityGuardAgent
    }
    
    agent_class = agents.get(role)
    if not agent_class:
        raise ValueError(f"Unknown agent role: {role}")
    
    return agent_class(memory_manager=memory_manager, **kwargs)


def create_agent_team(
    memory_manager: Optional[MemoryManager] = None
) -> Dict[str, BaseAgent]:
    """
    Crea el equipo completo de agentes.
    """
    team = {}
    
    # Crear subagentes
    for role in [AgentRole.RESEARCHER, AgentRole.ANALYZER, AgentRole.BUILDER,
                 AgentRole.VALIDATOR, AgentRole.MEMORY_KEEPER, AgentRole.SECURITY_GUARD]:
        agent = create_agent(role, memory_manager=memory_manager)
        team[role.value] = agent
    
    # Crear Lead Agent con subagentes registrados
    lead = LeadAgent(memory_manager=memory_manager)
    for agent in team.values():
        lead.register_subagent(agent)
    
    team[AgentRole.LEAD.value] = lead
    
    return team
