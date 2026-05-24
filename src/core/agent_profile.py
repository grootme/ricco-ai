"""
NEXUS Agent Profile - Perfil Completo del Agente

Implementación del perfil de agente con 8 componentes fundamentales:
- SKILLS: Qué sabe hacer
- TOOLS: Qué tiene disponible
- MCP: De dónde vienen
- MEMORY: Qué conoce (Capital Cognitivo)
- PROMPT: Cómo actúa
- DOMAIN: Etiqueta descriptiva
- EXECUTION: PATTERN (NO tipo)
- ORCHESTRATION: ROLE (NO tipo)

Patrones GOF Aplicados:
- Builder: Construcción fluida del perfil
- Strategy: Estrategias de ejecución intercambiables
- Observer: Notificación de cambios de estado
- Factory: Creación de componentes
- Singleton: Gestión de instancias únicas
- Decorator: Extensión de capacidades
- Command: Encapsulamiento de acciones
- State: Estados del ciclo de vida

@author: NEXUS - Neural Execution Unified System
"""

from typing import (
    Dict, List, Optional, Any, Callable, Set, Type, 
    Union, Protocol, runtime_checkable
)
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from uuid import UUID, uuid4
import asyncio
import json
import logging
from abc import ABC, abstractmethod
from functools import wraps
from collections import defaultdict

logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS Y TIPOS
# ============================================================================

class SkillLevel(str, Enum):
    """Niveles de habilidad"""
    NOVICE = "novice"
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    MASTER = "master"


class AgentState(str, Enum):
    """Estados del agente (Patrón State)"""
    IDLE = "idle"
    PREPARING = "preparing"
    ALIGNED = "aligned"
    EXECUTING = "executing"
    REFLECTING = "reflecting"
    LEARNING = "learning"
    ERROR = "error"
    TERMINATED = "terminated"


class Domain(str, Enum):
    """Dominios de especialización"""
    CODEX = "codex"           # Software Engineering
    VITALIS = "vitalis"       # Salud
    ATHLON = "athlon"         # Deportes
    VERITAS = "veritas"       # Noticias
    ALCHEMY = "alchemy"       # Química
    GENESIS = "genesis"       # Biología
    HELIX = "helix"           # Biotecnología
    DIPLOMAT = "diplomat"     # Geopolítica
    APEX = "apex"             # Finanzas
    JUSTITIA = "justitia"     # Legal
    MENTOR = "mentor"         # Educación
    PIONEER = "pioneer"       # Investigación
    PRISMA = "prisma"         # Marketing


class IOVBARole(str, Enum):
    """Roles IOVBA"""
    INVESTIGATOR = "investigator"   # Investiga y descubre
    OBSERVER = "observer"           # Observa y monitorea
    VALIDATOR = "validator"         # Valida y verifica
    BUILDER = "builder"             # Construye y ejecuta
    ASSISTANT = "assistant"         # Asiste y coordina


# ============================================================================
# PATRÓN STRATEGY - Estrategias de Ejecución
# ============================================================================

class ExecutionStrategy(ABC):
    """
    Patrón Strategy - Estrategia de ejecución intercambiable
    
    Permite cambiar el comportamiento de ejecución en runtime
    sin modificar el agente.
    """
    
    @abstractmethod
    async def execute(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta una tarea según la estrategia"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Retorna el nombre de la estrategia"""
        pass


class SequentialExecutionStrategy(ExecutionStrategy):
    """Ejecución secuencial paso a paso"""
    
    async def execute(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        steps = task.get("steps", [])
        results = []
        
        for i, step in enumerate(steps):
            step_result = {
                "step": i + 1,
                "action": step.get("action"),
                "status": "completed",
                "output": step.get("expected_output")
            }
            results.append(step_result)
        
        return {
            "strategy": self.get_name(),
            "total_steps": len(steps),
            "results": results,
            "status": "success"
        }
    
    def get_name(self) -> str:
        return "sequential"


class ParallelExecutionStrategy(ExecutionStrategy):
    """Ejecución paralela de tareas independientes"""
    
    async def execute(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        subtasks = task.get("subtasks", [])
        
        # Simular ejecución paralela
        results = await asyncio.gather(*[
            self._execute_subtask(st, context) for st in subtasks
        ])
        
        return {
            "strategy": self.get_name(),
            "parallel_count": len(subtasks),
            "results": list(results),
            "status": "success"
        }
    
    async def _execute_subtask(self, subtask: Dict, context: Dict) -> Dict:
        return {
            "subtask": subtask.get("id", "unknown"),
            "status": "completed"
        }
    
    def get_name(self) -> str:
        return "parallel"


class HierarchicalExecutionStrategy(ExecutionStrategy):
    """Ejecución jerárquica con delegación a sub-agentes"""
    
    async def execute(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        delegation_tree = task.get("delegation_tree", {})
        
        results = await self._process_tree(delegation_tree, context)
        
        return {
            "strategy": self.get_name(),
            "tree_depth": self._calculate_depth(delegation_tree),
            "results": results,
            "status": "success"
        }
    
    async def _process_tree(self, tree: Dict, context: Dict) -> Dict:
        if not tree:
            return {}
        
        return {
            "node": tree.get("id", "root"),
            "children_processed": len(tree.get("children", []))
        }
    
    def _calculate_depth(self, tree: Dict, depth: int = 0) -> int:
        if not tree or "children" not in tree:
            return depth
        return max(self._calculate_depth(c, depth + 1) for c in tree["children"])
    
    def get_name(self) -> str:
        return "hierarchical"


class AdaptiveExecutionStrategy(ExecutionStrategy):
    """
    Ejecución adaptativa que selecciona la mejor estrategia
    basándose en las características de la tarea
    """
    
    def __init__(self):
        self.strategies = {
            "sequential": SequentialExecutionStrategy(),
            "parallel": ParallelExecutionStrategy(),
            "hierarchical": HierarchicalExecutionStrategy()
        }
    
    async def execute(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        best_strategy = self._select_strategy(task)
        return await self.strategies[best_strategy].execute(task, context)
    
    def _select_strategy(self, task: Dict[str, Any]) -> str:
        if "delegation_tree" in task:
            return "hierarchical"
        elif "subtasks" in task and len(task.get("subtasks", [])) > 1:
            return "parallel"
        else:
            return "sequential"
    
    def get_name(self) -> str:
        return "adaptive"


# ============================================================================
# PATRÓN OBSERVER - Observadores del Agente
# ============================================================================

@runtime_checkable
class AgentObserver(Protocol):
    """Protocolo para observadores del agente"""
    
    async def on_state_change(self, agent_id: str, old_state: AgentState, new_state: AgentState) -> None:
        ...
    
    async def on_task_started(self, agent_id: str, task: Dict[str, Any]) -> None:
        ...
    
    async def on_task_completed(self, agent_id: str, result: Dict[str, Any]) -> None:
        ...
    
    async def on_learning_event(self, agent_id: str, event: Dict[str, Any]) -> None:
        ...


class AgentObservable:
    """
    Mixin para hacer observable al agente (Patrón Observer)
    """
    
    def __init__(self):
        self._observers: List[AgentObserver] = []
        self._event_history: List[Dict[str, Any]] = []
    
    def add_observer(self, observer: AgentObserver) -> None:
        self._observers.append(observer)
    
    def remove_observer(self, observer: AgentObserver) -> None:
        if observer in self._observers:
            self._observers.remove(observer)
    
    async def notify_state_change(self, agent_id: str, old_state: AgentState, new_state: AgentState) -> None:
        event = {
            "type": "state_change",
            "agent_id": agent_id,
            "old_state": old_state.value,
            "new_state": new_state.value,
            "timestamp": datetime.utcnow().isoformat()
        }
        self._event_history.append(event)
        
        for observer in self._observers:
            await observer.on_state_change(agent_id, old_state, new_state)
    
    async def notify_task_started(self, agent_id: str, task: Dict[str, Any]) -> None:
        for observer in self._observers:
            await observer.on_task_started(agent_id, task)
    
    async def notify_task_completed(self, agent_id: str, result: Dict[str, Any]) -> None:
        for observer in self._observers:
            await observer.on_task_completed(agent_id, result)
    
    async def notify_learning_event(self, agent_id: str, event: Dict[str, Any]) -> None:
        for observer in self._observers:
            await observer.on_learning_event(agent_id, event)


# ============================================================================
# PATRÓN COMMAND - Comandos del Agente
# ============================================================================

class AgentCommand(ABC):
    """
    Patrón Command - Encapsula una acción del agente
    """
    
    @abstractmethod
    async def execute(self) -> Dict[str, Any]:
        """Ejecuta el comando"""
        pass
    
    @abstractmethod
    def undo(self) -> None:
        """Deshace el comando (si es posible)"""
        pass


class AnalyzeCommand(AgentCommand):
    """Comando: Analizar datos o situación"""
    
    def __init__(self, agent: 'AgentProfile', data: Any, analysis_type: str):
        self.agent = agent
        self.data = data
        self.analysis_type = analysis_type
        self._result = None
    
    async def execute(self) -> Dict[str, Any]:
        self._result = {
            "command": "analyze",
            "type": self.analysis_type,
            "status": "completed",
            "insights": []
        }
        return self._result
    
    def undo(self) -> None:
        self._result = None


class GenerateCommand(AgentCommand):
    """Comando: Generar contenido o artefactos"""
    
    def __init__(self, agent: 'AgentProfile', prompt: str, output_type: str):
        self.agent = agent
        self.prompt = prompt
        self.output_type = output_type
        self._result = None
    
    async def execute(self) -> Dict[str, Any]:
        self._result = {
            "command": "generate",
            "output_type": self.output_type,
            "status": "completed",
            "content": f"Generated {self.output_type} based on: {self.prompt[:50]}..."
        }
        return self._result
    
    def undo(self) -> None:
        self._result = None


class CoordinateCommand(AgentCommand):
    """Comando: Coordinar con otros agentes"""
    
    def __init__(self, agent: 'AgentProfile', target_agents: List[str], task: Dict):
        self.agent = agent
        self.target_agents = target_agents
        self.task = task
        self._result = None
    
    async def execute(self) -> Dict[str, Any]:
        self._result = {
            "command": "coordinate",
            "targets": self.target_agents,
            "status": "completed",
            "coordination_result": "Multi-agent task completed"
        }
        return self._result
    
    def undo(self) -> None:
        self._result = None


class CommandInvoker:
    """
    Invocador de comandos (Patrón Command)
    """
    
    def __init__(self):
        self._command_history: List[AgentCommand] = []
        self._undo_stack: List[AgentCommand] = []
    
    async def execute_command(self, command: AgentCommand) -> Dict[str, Any]:
        result = await command.execute()
        self._command_history.append(command)
        self._undo_stack.append(command)
        return result
    
    async def undo_last(self) -> Optional[Dict[str, Any]]:
        if self._undo_stack:
            command = self._undo_stack.pop()
            command.undo()
            return {"status": "undone", "command": command.__class__.__name__}
        return None
    
    def get_history(self) -> List[str]:
        return [cmd.__class__.__name__ for cmd in self._command_history]


# ============================================================================
# PATRÓN STATE - Estados del Agente
# ============================================================================

class AgentStateHandler(ABC):
    """
    Patrón State - Manejador de estado
    """
    
    @abstractmethod
    async def handle(self, agent: 'AgentProfile') -> None:
        pass
    
    @abstractmethod
    def get_next_state(self) -> Optional[AgentState]:
        pass


class IdleStateHandler(AgentStateHandler):
    async def handle(self, agent: 'AgentProfile') -> None:
        logger.info(f"Agent {agent.agent_id} is idle, waiting for tasks")
    
    def get_next_state(self) -> Optional[AgentState]:
        return AgentState.PREPARING


class PreparingStateHandler(AgentStateHandler):
    async def handle(self, agent: 'AgentProfile') -> None:
        logger.info(f"Agent {agent.agent_id} preparing context")
    
    def get_next_state(self) -> Optional[AgentState]:
        return AgentState.ALIGNED


class ExecutingStateHandler(AgentStateHandler):
    async def handle(self, agent: 'AgentProfile') -> None:
        logger.info(f"Agent {agent.agent_id} executing task")
    
    def get_next_state(self) -> Optional[AgentState]:
        return AgentState.REFLECTING


class LearningStateHandler(AgentStateHandler):
    async def handle(self, agent: 'AgentProfile') -> None:
        logger.info(f"Agent {agent.agent_id} learning from experience")
    
    def get_next_state(self) -> Optional[AgentState]:
        return AgentState.IDLE


# ============================================================================
# PATRÓN DECORATOR - Extensión de Capacidades
# ============================================================================

class SkillDecorator:
    """
    Patrón Decorator - Extiende capacidades del agente dinámicamente
    """
    
    def __init__(self, agent: 'AgentProfile'):
        self._agent = agent
    
    @property
    def agent_id(self) -> str:
        return self._agent.agent_id
    
    def get_skills(self) -> Dict[str, Any]:
        return self._agent.skills
    
    async def execute_with_enhancement(self, task: Dict[str, Any]) -> Dict[str, Any]:
        return await self._agent.execute_task(task)


class LoggingDecorator(SkillDecorator):
    """Decorator: Añade logging detallado"""
    
    async def execute_with_enhancement(self, task: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"[{self.agent_id}] Starting task: {task.get('type', 'unknown')}")
        result = await super().execute_with_enhancement(task)
        logger.info(f"[{self.agent_id}] Task completed with status: {result.get('status')}")
        return result


class CachingDecorator(SkillDecorator):
    """Decorator: Añade caché de resultados"""
    
    def __init__(self, agent: 'AgentProfile'):
        super().__init__(agent)
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    async def execute_with_enhancement(self, task: Dict[str, Any]) -> Dict[str, Any]:
        cache_key = self._make_cache_key(task)
        
        if cache_key in self._cache:
            logger.info(f"[{self.agent_id}] Cache hit for task")
            return {**self._cache[cache_key], "cached": True}
        
        result = await super().execute_with_enhancement(task)
        self._cache[cache_key] = result
        return result
    
    def _make_cache_key(self, task: Dict[str, Any]) -> str:
        return json.dumps(task, sort_keys=True, default=str)[:100]


class MetricsDecorator(SkillDecorator):
    """Decorator: Añade métricas de rendimiento"""
    
    def __init__(self, agent: 'AgentProfile'):
        super().__init__(agent)
        self._metrics: Dict[str, List[float]] = defaultdict(list)
    
    async def execute_with_enhancement(self, task: Dict[str, Any]) -> Dict[str, Any]:
        start_time = datetime.utcnow()
        result = await super().execute_with_enhancement(task)
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        task_type = task.get("type", "unknown")
        self._metrics[task_type].append(duration)
        
        result["metrics"] = {
            "duration_seconds": duration,
            "avg_duration": sum(self._metrics[task_type]) / len(self._metrics[task_type])
        }
        return result


class RetryDecorator(SkillDecorator):
    """Decorator: Añade lógica de reintento"""
    
    def __init__(self, agent: 'AgentProfile', max_retries: int = 3):
        super().__init__(agent)
        self.max_retries = max_retries
    
    async def execute_with_enhancement(self, task: Dict[str, Any]) -> Dict[str, Any]:
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                result = await super().execute_with_enhancement(task)
                result["attempts"] = attempt + 1
                return result
            except Exception as e:
                last_error = e
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        return {
            "status": "failed",
            "error": str(last_error),
            "attempts": self.max_retries
        }


# ============================================================================
# PATRÓN FACTORY - Creación de Componentes
# ============================================================================

class SkillFactory:
    """
    Patrón Factory - Crea skills basándose en el dominio
    """
    
    _skill_templates = {
        Domain.CODEX: [
            {"name": "code_analysis", "level": SkillLevel.ADVANCED},
            {"name": "code_generation", "level": SkillLevel.ADVANCED},
            {"name": "refactoring", "level": SkillLevel.INTERMEDIATE},
            {"name": "debugging", "level": SkillLevel.EXPERT},
            {"name": "testing", "level": SkillLevel.ADVANCED},
        ],
        Domain.VITALIS: [
            {"name": "symptom_analysis", "level": SkillLevel.ADVANCED},
            {"name": "diagnostic_support", "level": SkillLevel.ADVANCED},
            {"name": "medical_research", "level": SkillLevel.INTERMEDIATE},
        ],
        Domain.ATHLON: [
            {"name": "performance_analysis", "level": SkillLevel.ADVANCED},
            {"name": "training_planning", "level": SkillLevel.INTERMEDIATE},
        ],
        Domain.APEX: [
            {"name": "market_analysis", "level": SkillLevel.ADVANCED},
            {"name": "risk_assessment", "level": SkillLevel.ADVANCED},
            {"name": "portfolio_optimization", "level": SkillLevel.EXPERT},
        ],
    }
    
    @classmethod
    def create_skills_for_domain(cls, domain: Domain) -> Dict[str, Dict[str, Any]]:
        """Crea skills para un dominio específico"""
        templates = cls._skill_templates.get(domain, [])
        skills = {}
        
        for template in templates:
            skills[template["name"]] = {
                "level": template["level"].value,
                "acquired_at": datetime.utcnow().isoformat(),
                "usage_count": 0,
                "success_rate": 0.0,
                "last_used": None,
            }
        
        return skills
    
    @classmethod
    def create_execution_strategy(cls, strategy_type: str) -> ExecutionStrategy:
        """Crea una estrategia de ejecución"""
        strategies = {
            "sequential": SequentialExecutionStrategy(),
            "parallel": ParallelExecutionStrategy(),
            "hierarchical": HierarchicalExecutionStrategy(),
            "adaptive": AdaptiveExecutionStrategy(),
        }
        return strategies.get(strategy_type, AdaptiveExecutionStrategy())


# ============================================================================
# PATRÓN BUILDER - Construcción Fluida del Perfil
# ============================================================================

class AgentProfileBuilder:
    """
    Patrón Builder - Construcción fluida del perfil del agente
    
    Usage:
        profile = (AgentProfileBuilder()
            .with_id("agent-001")
            .with_domain(Domain.CODEX)
            .with_role(IOVBARole.BUILDER)
            .with_skill("python", SkillLevel.EXPERT)
            .with_tool("code_analyzer")
            .build())
    """
    
    def __init__(self):
        self._agent_id: str = str(uuid4())[:8]
        self._domain: Domain = Domain.CODEX
        self._role: IOVBARole = IOVBARole.BUILDER
        self._skills: Dict[str, Dict] = {}
        self._tools: List[str] = []
        self._mcp_servers: List[str] = []
        self._memory_config: Dict[str, Any] = {}
        self._prompt_template: str = ""
        self._execution_strategy: str = "adaptive"
        self._parent_agent: Optional[str] = None
        self._child_agents: List[str] = []
    
    def with_id(self, agent_id: str) -> 'AgentProfileBuilder':
        self._agent_id = agent_id
        return self
    
    def with_domain(self, domain: Domain) -> 'AgentProfileBuilder':
        self._domain = domain
        # Auto-populate skills for domain
        self._skills.update(SkillFactory.create_skills_for_domain(domain))
        return self
    
    def with_role(self, role: IOVBARole) -> 'AgentProfileBuilder':
        self._role = role
        return self
    
    def with_skill(self, name: str, level: SkillLevel) -> 'AgentProfileBuilder':
        self._skills[name] = {
            "level": level.value,
            "acquired_at": datetime.utcnow().isoformat(),
            "usage_count": 0,
            "success_rate": 0.0,
        }
        return self
    
    def with_tool(self, tool_name: str) -> 'AgentProfileBuilder':
        self._tools.append(tool_name)
        return self
    
    def with_mcp_server(self, server: str) -> 'AgentProfileBuilder':
        self._mcp_servers.append(server)
        return self
    
    def with_memory(self, config: Dict[str, Any]) -> 'AgentProfileBuilder':
        self._memory_config = config
        return self
    
    def with_prompt(self, template: str) -> 'AgentProfileBuilder':
        self._prompt_template = template
        return self
    
    def with_execution_strategy(self, strategy: str) -> 'AgentProfileBuilder':
        self._execution_strategy = strategy
        return self
    
    def with_parent(self, parent_id: str) -> 'AgentProfileBuilder':
        self._parent_agent = parent_id
        return self
    
    def with_child(self, child_id: str) -> 'AgentProfileBuilder':
        self._child_agents.append(child_id)
        return self
    
    def build(self) -> 'AgentProfile':
        """Construye el perfil del agente"""
        return AgentProfile(
            agent_id=self._agent_id,
            domain=self._domain,
            role=self._role,
            skills=self._skills,
            tools=self._tools,
            mcp_servers=self._mcp_servers,
            memory_config=self._memory_config,
            prompt_template=self._prompt_template,
            execution_strategy_name=self._execution_strategy,
            parent_agent=self._parent_agent,
            child_agents=self._child_agents
        )


# ============================================================================
# AGENT PROFILE - Perfil Completo del Agente
# ============================================================================

class AgentProfile(AgentObservable):
    """
    Perfil Completo del Agente
    
    ┌─────────────────────────────────────────────────────────────────┐
    │                      AGENT PROFILE                              │
    ├─────────────────────────────────────────────────────────────────┤
    │  SKILLS       │  TOOLS       │  MCP         │  MEMORY          │
    │  Qué sabe     │  Qué tiene   │  De dónde    │  Qué conoce      │
    │  hacer        │  disponible  │  vienen      │  (Capital Cogn.) │
    ├─────────────────────────────────────────────────────────────────┤
    │  PROMPT       │  DOMAIN      │  EXECUTION   │  ORCHESTRATION   │
    │  Cómo actúa   │  Etiqueta    │  PATTERN     │  ROLE            │
    │               │  descriptiva │  (NO tipo)   │  (NO tipo)       │
    └─────────────────────────────────────────────────────────────────┘
    
    Patrones GOF Implementados:
    - Builder: Construcción fluida
    - Strategy: Estrategias de ejecución intercambiables
    - Observer: Notificación de eventos
    - Command: Encapsulamiento de acciones
    - State: Manejo de estados
    - Decorator: Extensión de capacidades
    - Factory: Creación de componentes
    """
    
    def __init__(
        self,
        agent_id: str,
        domain: Domain,
        role: IOVBARole,
        skills: Dict[str, Dict],
        tools: List[str],
        mcp_servers: List[str],
        memory_config: Dict[str, Any],
        prompt_template: str,
        execution_strategy_name: str,
        parent_agent: Optional[str] = None,
        child_agents: List[str] = None
    ):
        super().__init__()
        
        # Identidad
        self.agent_id = agent_id
        self.domain = domain
        self.role = role
        
        # 8 Componentes del Perfil
        self.skills = skills                    # SKILLS: Qué sabe hacer
        self.tools = tools                      # TOOLS: Qué tiene disponible
        self.mcp_servers = mcp_servers          # MCP: De dónde vienen
        self.memory = CognitiveMemory(memory_config)  # MEMORY: Qué conoce
        self.prompt_template = prompt_template  # PROMPT: Cómo actúa
        self._execution_strategy_name = execution_strategy_name
        self._parent_agent = parent_agent       # ORCHESTRATION: Padre
        self._child_agents = child_agents or [] # ORCHESTRATION: Hijos
        
        # Estado interno
        self._state = AgentState.IDLE
        self._execution_strategy = SkillFactory.create_execution_strategy(execution_strategy_name)
        self._command_invoker = CommandInvoker()
        
        # Capital Cognitivo
        self._capital_value = 0.0
        self._experiences: List[Dict[str, Any]] = []
        self._insights: List[Dict[str, Any]] = []
        
        # Timestamps
        self.created_at = datetime.utcnow()
        self.last_active = datetime.utcnow()
    
    # ========================================================================
    # PROPIEDADES
    # ========================================================================
    
    @property
    def state(self) -> AgentState:
        return self._state
    
    @state.setter
    def state(self, new_state: AgentState) -> None:
        old_state = self._state
        self._state = new_state
        asyncio.create_task(self.notify_state_change(self.agent_id, old_state, new_state))
    
    @property
    def execution_strategy(self) -> str:
        return self._execution_strategy_name
    
    @execution_strategy.setter
    def execution_strategy(self, strategy_name: str) -> None:
        self._execution_strategy = SkillFactory.create_execution_strategy(strategy_name)
        self._execution_strategy_name = strategy_name
    
    @property
    def capital_value(self) -> float:
        return self._capital_value
    
    # ========================================================================
    # MÉTODOS PRINCIPALES
    # ========================================================================
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta una tarea usando la estrategia configurada"""
        old_state = self._state
        self.state = AgentState.EXECUTING
        self.last_active = datetime.utcnow()
        
        await self.notify_task_started(self.agent_id, task)
        
        try:
            # Usar contexto de memoria
            context = await self.memory.get_context()
            
            # Ejecutar con estrategia
            result = await self._execution_strategy.execute(task, context)
            
            # Actualizar capital cognitivo
            self._update_capital(result)
            
            # Notificar completado
            await self.notify_task_completed(self.agent_id, result)
            
            return result
            
        except Exception as e:
            self.state = AgentState.ERROR
            return {
                "status": "error",
                "error": str(e),
                "agent_id": self.agent_id
            }
        finally:
            if self._state == AgentState.EXECUTING:
                self.state = AgentState.IDLE
    
    async def learn_from_experience(self, experience: Dict[str, Any]) -> Dict[str, Any]:
        """Aprende de una experiencia (Ralph Loop)"""
        self.state = AgentState.LEARNING
        
        # Almacenar experiencia
        self._experiences.append({
            **experience,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Extraer insight
        insight = await self._extract_insight(experience)
        if insight:
            self._insights.append(insight)
            
            # Notificar evento de aprendizaje
            await self.notify_learning_event(self.agent_id, {
                "type": "insight_generated",
                "insight": insight
            })
        
        # Actualizar skills si corresponde
        if "skills_used" in experience:
            for skill_name in experience["skills_used"]:
                if skill_name in self.skills:
                    self.skills[skill_name]["usage_count"] += 1
        
        self.state = AgentState.IDLE
        
        return {
            "experience_processed": True,
            "insight_generated": insight is not None,
            "total_experiences": len(self._experiences),
            "total_insights": len(self._insights)
        }
    
    async def _extract_insight(self, experience: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extrae un insight de una experiencia"""
        if experience.get("success", False):
            return {
                "type": "success_pattern",
                "context": experience.get("context", {}),
                "factors": experience.get("success_factors", []),
                "confidence": 0.8
            }
        elif experience.get("error"):
            return {
                "type": "failure_pattern",
                "error": experience.get("error"),
                "mitigation": "Review similar contexts before execution",
                "confidence": 0.6
            }
        return None
    
    def _update_capital(self, result: Dict[str, Any]) -> None:
        """Actualiza el capital cognitivo basado en resultado"""
        if result.get("status") == "success":
            self._capital_value += 1.0
        elif result.get("cached"):
            self._capital_value += 0.5  # Menor valor para cached
        else:
            self._capital_value += 0.1  # Valor mínimo por intento
    
    # ========================================================================
    # COMMAND PATTERN
    # ========================================================================
    
    async def execute_command(self, command: AgentCommand) -> Dict[str, Any]:
        """Ejecuta un comando encapsulado"""
        return await self._command_invoker.execute_command(command)
    
    async def undo_last_command(self) -> Optional[Dict[str, Any]]:
        """Deshace el último comando"""
        return await self._command_invoker.undo_last()
    
    def get_command_history(self) -> List[str]:
        """Obtiene historial de comandos"""
        return self._command_invoker.get_history()
    
    # ========================================================================
    # SERIALIZACIÓN
    # ========================================================================
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa el perfil a diccionario"""
        return {
            "agent_id": self.agent_id,
            "domain": self.domain.value,
            "role": self.role.value,
            "skills": self.skills,
            "tools": self.tools,
            "mcp_servers": self.mcp_servers,
            "memory": self.memory.to_dict(),
            "prompt_template": self.prompt_template,
            "execution_strategy": self._execution_strategy_name,
            "parent_agent": self._parent_agent,
            "child_agents": self._child_agents,
            "state": self._state.value,
            "capital_value": self._capital_value,
            "experiences_count": len(self._experiences),
            "insights_count": len(self._insights),
            "created_at": self.created_at.isoformat(),
            "last_active": self.last_active.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentProfile':
        """Deserializa desde diccionario"""
        builder = AgentProfileBuilder()
        
        builder.with_id(data["agent_id"])
        builder.with_domain(Domain(data["domain"]))
        builder.with_role(IOVBARole(data["role"]))
        
        for skill_name, skill_data in data.get("skills", {}).items():
            builder.with_skill(skill_name, SkillLevel(skill_data.get("level", "beginner")))
        
        for tool in data.get("tools", []):
            builder.with_tool(tool)
        
        for server in data.get("mcp_servers", []):
            builder.with_mcp_server(server)
        
        if data.get("memory"):
            builder.with_memory(data["memory"])
        
        if data.get("prompt_template"):
            builder.with_prompt(data["prompt_template"])
        
        if data.get("execution_strategy"):
            builder.with_execution_strategy(data["execution_strategy"])
        
        if data.get("parent_agent"):
            builder.with_parent(data["parent_agent"])
        
        for child in data.get("child_agents", []):
            builder.with_child(child)
        
        return builder.build()


# ============================================================================
# COGNITIVE MEMORY - Memoria del Agente
# ============================================================================

class CognitiveMemory:
    """
    Memoria Cognitiva del Agente
    
    Implementa:
    - Short-term memory (sesión actual)
    - Long-term memory (persistente)
    - Working memory (contexto activo)
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Memoria a corto plazo (sesión)
        self._short_term: Dict[str, Any] = {}
        
        # Memoria a largo plazo (capital cognitivo)
        self._long_term: List[Dict[str, Any]] = []
        
        # Memoria de trabajo
        self._working: Dict[str, Any] = {}
        
        # Índice semántico (simplificado)
        self._semantic_index: Dict[str, List[int]] = defaultdict(list)
    
    async def store(self, key: str, value: Any, scope: str = "short") -> None:
        """Almacena un valor en memoria"""
        if scope == "short":
            self._short_term[key] = {
                "value": value,
                "timestamp": datetime.utcnow().isoformat()
            }
        elif scope == "long":
            idx = len(self._long_term)
            self._long_term.append({
                "key": key,
                "value": value,
                "timestamp": datetime.utcnow().isoformat()
            })
            # Indexar
            for word in str(value).lower().split():
                self._semantic_index[word].append(idx)
        elif scope == "working":
            self._working[key] = value
    
    async def retrieve(self, key: str, scope: str = "all") -> Optional[Any]:
        """Recupera un valor de memoria"""
        if scope in ["all", "working"] and key in self._working:
            return self._working[key]
        if scope in ["all", "short"] and key in self._short_term:
            return self._short_term[key].get("value")
        if scope in ["all", "long"]:
            for item in self._long_term:
                if item["key"] == key:
                    return item["value"]
        return None
    
    async def search(self, query: str) -> List[Dict[str, Any]]:
        """Búsqueda semántica simplificada"""
        results = []
        words = query.lower().split()
        
        indices = set()
        for word in words:
            indices.update(self._semantic_index.get(word, []))
        
        for idx in indices:
            if idx < len(self._long_term):
                results.append(self._long_term[idx])
        
        return results
    
    async def get_context(self) -> Dict[str, Any]:
        """Obtiene contexto completo de memoria"""
        return {
            "working": self._working,
            "short_term_keys": list(self._short_term.keys()),
            "long_term_count": len(self._long_term),
        }
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "short_term": self._short_term,
            "long_term": self._long_term[-100:],  # Last 100
            "working": self._working
        }


# ============================================================================
# SINGLETON - Gestor de Agentes
# ============================================================================

class AgentRegistry:
    """
    Patrón Singleton - Registro global de agentes
    """
    
    _instance: Optional['AgentRegistry'] = None
    _agents: Dict[str, AgentProfile] = {}
    
    def __new__(cls) -> 'AgentRegistry':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def register(self, agent: AgentProfile) -> None:
        self._agents[agent.agent_id] = agent
    
    def unregister(self, agent_id: str) -> None:
        if agent_id in self._agents:
            del self._agents[agent_id]
    
    def get(self, agent_id: str) -> Optional[AgentProfile]:
        return self._agents.get(agent_id)
    
    def get_all(self) -> List[AgentProfile]:
        return list(self._agents.values())
    
    def get_by_domain(self, domain: Domain) -> List[AgentProfile]:
        return [a for a in self._agents.values() if a.domain == domain]
    
    def get_by_role(self, role: IOVBARole) -> List[AgentProfile]:
        return [a for a in self._agents.values() if a.role == role]
    
    def get_total_capital(self) -> float:
        return sum(a.capital_value for a in self._agents.values())


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Enums
    "SkillLevel",
    "AgentState",
    "Domain",
    "IOVBARole",
    
    # Strategy Pattern
    "ExecutionStrategy",
    "SequentialExecutionStrategy",
    "ParallelExecutionStrategy",
    "HierarchicalExecutionStrategy",
    "AdaptiveExecutionStrategy",
    
    # Observer Pattern
    "AgentObserver",
    "AgentObservable",
    
    # Command Pattern
    "AgentCommand",
    "AnalyzeCommand",
    "GenerateCommand",
    "CoordinateCommand",
    "CommandInvoker",
    
    # State Pattern
    "AgentStateHandler",
    "IdleStateHandler",
    "PreparingStateHandler",
    "ExecutingStateHandler",
    "LearningStateHandler",
    
    # Decorator Pattern
    "SkillDecorator",
    "LoggingDecorator",
    "CachingDecorator",
    "MetricsDecorator",
    "RetryDecorator",
    
    # Factory Pattern
    "SkillFactory",
    
    # Builder Pattern
    "AgentProfileBuilder",
    
    # Main Classes
    "AgentProfile",
    "CognitiveMemory",
    "AgentRegistry",
]
