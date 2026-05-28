"""
Patrones de Diseño GOF para la arquitectura del Super Asistente.
Implementa patrones creacionales, estructurales y de comportamiento.
"""

from typing import Any, Dict, List, Optional, Callable, TypeVar, Generic, Type
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
import asyncio
from functools import wraps
import inspect


# =============================================================================
# PATRONES CREACIONALES
# =============================================================================

# 1. ABSTRACT FACTORY PATTERN
# ----------------------------

class AgentComponentFactory(ABC):
    """Abstract Factory para componentes de agentes."""
    
    @abstractmethod
    def create_agent(self, config: Dict[str, Any]) -> 'BaseAgent':
        pass
    
    @abstractmethod
    def create_tool(self, name: str, config: Dict[str, Any]) -> 'BaseTool':
        pass
    
    @abstractmethod
    def create_memory(self, config: Dict[str, Any]) -> 'BaseMemory':
        pass


class ResearcherAgentFactory(AgentComponentFactory):
    """Factory para crear componentes de Researcher."""
    
    def create_agent(self, config: Dict[str, Any]) -> 'BaseAgent':
        from agents.base import ResearcherAgent
        return ResearcherAgent(**config)
    
    def create_tool(self, name: str, config: Dict[str, Any]) -> 'BaseTool':
        # Herramientas específicas de investigación
        pass
    
    def create_memory(self, config: Dict[str, Any]) -> 'BaseMemory':
        # Memoria para investigador
        pass


class BuilderAgentFactory(AgentComponentFactory):
    """Factory para crear componentes de Builder."""
    
    def create_agent(self, config: Dict[str, Any]) -> 'BaseAgent':
        from agents.base import BuilderAgent
        return BuilderAgent(**config)
    
    def create_tool(self, name: str, config: Dict[str, Any]) -> 'BaseTool':
        # Herramientas de construcción
        pass
    
    def create_memory(self, config: Dict[str, Any]) -> 'BaseMemory':
        # Memoria para builder
        pass


# 2. BUILDER PATTERN
# -------------------

class AgentBuilder:
    """Builder para construir agentes complejos paso a paso."""
    
    def __init__(self):
        self._name: str = "DefaultAgent"
        self._role: str = "assistant"
        self._tools: List[Any] = []
        self._memory: Optional[Any] = None
        self._llm_config: Optional[Dict[str, Any]] = None
        self._system_prompt: Optional[str] = None
        self._max_iterations: int = 10
        self._hooks: Dict[str, List[Callable]] = {}
    
    def with_name(self, name: str) -> 'AgentBuilder':
        self._name = name
        return self
    
    def with_role(self, role: str) -> 'AgentBuilder':
        self._role = role
        return self
    
    def with_tools(self, tools: List[Any]) -> 'AgentBuilder':
        self._tools = tools
        return self
    
    def add_tool(self, tool: Any) -> 'AgentBuilder':
        self._tools.append(tool)
        return self
    
    def with_memory(self, memory: Any) -> 'AgentBuilder':
        self._memory = memory
        return self
    
    def with_llm(self, config: Dict[str, Any]) -> 'AgentBuilder':
        self._llm_config = config
        return self
    
    def with_system_prompt(self, prompt: str) -> 'AgentBuilder':
        self._system_prompt = prompt
        return self
    
    def with_max_iterations(self, max_iter: int) -> 'AgentBuilder':
        self._max_iterations = max_iter
        return self
    
    def with_hook(self, event: str, callback: Callable) -> 'AgentBuilder':
        if event not in self._hooks:
            self._hooks[event] = []
        self._hooks[event].append(callback)
        return self
    
    def build(self) -> Dict[str, Any]:
        """Construye la configuración del agente."""
        return {
            "name": self._name,
            "role": self._role,
            "tools": self._tools,
            "memory": self._memory,
            "llm_config": self._llm_config,
            "system_prompt": self._system_prompt,
            "max_iterations": self._max_iterations,
            "hooks": self._hooks
        }


# 3. FACTORY METHOD PATTERN
# --------------------------

class AgentCreator(ABC):
    """Factory Method para crear agentes."""
    
    @abstractmethod
    def factory_method(self) -> 'BaseAgent':
        """Método factory que las subclases implementan."""
        pass
    
    def create_and_configure(self, config: Dict[str, Any]) -> 'BaseAgent':
        """Template method que usa el factory method."""
        agent = self.factory_method()
        # Configuración común
        return agent


# 4. PROTOTYPE PATTERN
# ---------------------

class AgentPrototype:
    """Prototype para clonar configuraciones de agentes."""
    
    _prototypes: Dict[str, Dict[str, Any]] = {}
    
    @classmethod
    def register(cls, name: str, prototype: Dict[str, Any]) -> None:
        """Registra un prototipo."""
        cls._prototypes[name] = prototype.copy()
    
    @classmethod
    def clone(cls, name: str) -> Optional[Dict[str, Any]]:
        """Clona un prototipo."""
        if name in cls._prototypes:
            return cls._prototypes[name].copy()
        return None
    
    @classmethod
    def clone_with_modifications(
        cls,
        name: str,
        modifications: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Clona con modificaciones."""
        prototype = cls.clone(name)
        if prototype:
            prototype.update(modifications)
        return prototype


# 5. SINGLETON PATTERN
# ---------------------

class AgentRegistry:
    """Singleton para registro global de agentes."""
    
    _instance: Optional['AgentRegistry'] = None
    _agents: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def register_agent(self, name: str, agent: Any) -> None:
        self._agents[name] = agent
    
    def get_agent(self, name: str) -> Optional[Any]:
        return self._agents.get(name)
    
    def list_agents(self) -> List[str]:
        return list(self._agents.keys())


# =============================================================================
# PATRONES ESTRUCTURALES
# =============================================================================

# 1. ADAPTER PATTERN
# -------------------

class ToolAdapter(ABC):
    """Adapter para convertir herramientas externas al formato interno."""
    
    @abstractmethod
    def adapt(self, external_tool: Any) -> Dict[str, Any]:
        """Convierte herramienta externa a formato interno."""
        pass


class LangChainToolAdapter(ToolAdapter):
    """Adapter para herramientas LangChain."""
    
    def adapt(self, external_tool: Any) -> Dict[str, Any]:
        return {
            "name": external_tool.name,
            "description": external_tool.description,
            "parameters": external_tool.args_schema.schema() if hasattr(external_tool, 'args_schema') else {},
            "executor": external_tool
        }


class MCPToolAdapter(ToolAdapter):
    """Adapter para herramientas MCP."""
    
    def adapt(self, external_tool: Any) -> Dict[str, Any]:
        return {
            "name": external_tool.get("name", ""),
            "description": external_tool.get("description", ""),
            "parameters": external_tool.get("input_schema", {}),
            "source": "mcp"
        }


# 2. BRIDGE PATTERN
# ------------------

class LLMInterface(ABC):
    """Abstracción del Bridge para LLMs."""
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        pass
    
    @abstractmethod
    async def generate_with_tools(
        self,
        prompt: str,
        tools: List[Dict[str, Any]],
        **kwargs
    ) -> Dict[str, Any]:
        pass


class OpenAIImplementation(LLMInterface):
    """Implementación concreta para OpenAI."""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.api_key = api_key
        self.model = model
    
    async def generate(self, prompt: str, **kwargs) -> str:
        # Placeholder
        return f"OpenAI response to: {prompt[:50]}..."
    
    async def generate_with_tools(
        self,
        prompt: str,
        tools: List[Dict[str, Any]],
        **kwargs
    ) -> Dict[str, Any]:
        return {"response": "Tool-enabled response", "tool_calls": []}


class AnthropicImplementation(LLMInterface):
    """Implementación concreta para Anthropic."""
    
    def __init__(self, api_key: str, model: str = "claude-3"):
        self.api_key = api_key
        self.model = model
    
    async def generate(self, prompt: str, **kwargs) -> str:
        return f"Anthropic response to: {prompt[:50]}..."
    
    async def generate_with_tools(
        self,
        prompt: str,
        tools: List[Dict[str, Any]],
        **kwargs
    ) -> Dict[str, Any]:
        return {"response": "Tool-enabled response", "tool_calls": []}


# 3. COMPOSITE PATTERN
# ---------------------

class TaskComponent(ABC):
    """Component del Composite para tareas."""
    
    @abstractmethod
    async def execute(self) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    def add(self, component: 'TaskComponent') -> None:
        pass
    
    @abstractmethod
    def remove(self, component: 'TaskComponent') -> None:
        pass


class SimpleTask(TaskComponent):
    """Tarea simple (Leaf)."""
    
    def __init__(self, name: str, executor: Callable):
        self.name = name
        self.executor = executor
    
    async def execute(self) -> Dict[str, Any]:
        result = await self.executor() if asyncio.iscoroutinefunction(self.executor) else self.executor()
        return {"task": self.name, "result": result}
    
    def add(self, component: TaskComponent) -> None:
        raise NotImplementedError("Cannot add to leaf")
    
    def remove(self, component: TaskComponent) -> None:
        raise NotImplementedError("Cannot remove from leaf")


class CompositeTask(TaskComponent):
    """Tarea compuesta (Composite)."""
    
    def __init__(self, name: str):
        self.name = name
        self._children: List[TaskComponent] = []
    
    async def execute(self) -> Dict[str, Any]:
        results = []
        for child in self._children:
            result = await child.execute()
            results.append(result)
        
        return {
            "task": self.name,
            "type": "composite",
            "children_results": results
        }
    
    def add(self, component: TaskComponent) -> None:
        self._children.append(component)
    
    def remove(self, component: TaskComponent) -> None:
        self._children.remove(component)


# 4. DECORATOR PATTERN
# ---------------------

class AgentDecorator(ABC):
    """Decorator para agregar funcionalidad a agentes."""
    
    def __init__(self, agent: Any):
        self._agent = agent
    
    async def execute(self, *args, **kwargs) -> Any:
        return await self._agent.execute(*args, **kwargs)


class LoggingDecorator(AgentDecorator):
    """Decorator para logging."""
    
    async def execute(self, *args, **kwargs) -> Any:
        print(f"[{datetime.utcnow()}] Executing {self._agent.name}...")
        result = await super().execute(*args, **kwargs)
        print(f"[{datetime.utcnow()}] Completed {self._agent.name}")
        return result


class CachingDecorator(AgentDecorator):
    """Decorator para caching."""
    
    def __init__(self, agent: Any):
        super().__init__(agent)
        self._cache: Dict[str, Any] = {}
    
    async def execute(self, *args, **kwargs) -> Any:
        cache_key = str(args) + str(kwargs)
        
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        result = await super().execute(*args, **kwargs)
        self._cache[cache_key] = result
        return result


class RetryDecorator(AgentDecorator):
    """Decorator para reintentos."""
    
    def __init__(self, agent: Any, max_retries: int = 3):
        super().__init__(agent)
        self.max_retries = max_retries
    
    async def execute(self, *args, **kwargs) -> Any:
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                return await super().execute(*args, **kwargs)
            except Exception as e:
                last_error = e
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        raise last_error


# 5. FACADE PATTERN
# ------------------

class AgentOrchestratorFacade:
    """Facade para simplificar la orquestación de agentes."""
    
    def __init__(self):
        self._registry = AgentRegistry()
        self._adapters: Dict[str, ToolAdapter] = {
            "langchain": LangChainToolAdapter(),
            "mcp": MCPToolAdapter()
        }
    
    async def execute_task(
        self,
        task: str,
        agent_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Ejecuta una tarea de forma simplificada."""
        if agent_name:
            agent = self._registry.get_agent(agent_name)
            if agent:
                return await agent.execute(task)
        
        # Seleccionar agente automáticamente
        return {"task": task, "status": "delegated"}
    
    def register_tool(
        self,
        tool: Any,
        adapter_type: str = "langchain"
    ) -> None:
        """Registra una herramienta usando el adapter apropiado."""
        adapter = self._adapters.get(adapter_type)
        if adapter:
            adapted = adapter.adapt(tool)
            # Registrar herramienta adaptada


# =============================================================================
# PATRONES DE COMPORTAMIENTO
# =============================================================================

# 1. CHAIN OF RESPONSIBILITY
# ---------------------------

class RequestHandler(ABC):
    """Handler base para Chain of Responsibility."""
    
    def __init__(self):
        self._next: Optional[RequestHandler] = None
    
    def set_next(self, handler: 'RequestHandler') -> 'RequestHandler':
        self._next = handler
        return handler
    
    async def handle(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        result = await self._process(request)
        
        if result is None and self._next:
            return await self._next.handle(request)
        
        return result
    
    @abstractmethod
    async def _process(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        pass


class SecurityHandler(RequestHandler):
    """Handler de seguridad."""
    
    async def _process(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        content = request.get("content", "")
        
        # Verificar contenido peligroso
        dangerous_patterns = ["ignore instructions", "bypass", "jailbreak"]
        for pattern in dangerous_patterns:
            if pattern in content.lower():
                return {"error": "Security violation detected", "blocked": True}
        
        return None


class ValidationHandler(RequestHandler):
    """Handler de validación."""
    
    async def _process(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not request.get("content"):
            return {"error": "Empty request"}
        
        return None


class ProcessingHandler(RequestHandler):
    """Handler de procesamiento."""
    
    async def _process(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return {
            "processed": True,
            "content": request.get("content"),
            "timestamp": datetime.utcnow().isoformat()
        }


# 2. COMMAND PATTERN
# -------------------

class Command(ABC):
    """Command base."""
    
    @abstractmethod
    async def execute(self) -> Any:
        pass
    
    @abstractmethod
    async def undo(self) -> None:
        pass


class CreateAgentCommand(Command):
    """Comando para crear agente."""
    
    def __init__(self, registry: AgentRegistry, name: str, config: Dict[str, Any]):
        self._registry = registry
        self._name = name
        self._config = config
        self._executed = False
    
    async def execute(self) -> Any:
        # Crear agente
        self._registry.register_agent(self._name, self._config)
        self._executed = True
        return self._config
    
    async def undo(self) -> None:
        if self._executed:
            del self._registry._agents[self._name]


class CommandInvoker:
    """Invoker del Command pattern."""
    
    def __init__(self):
        self._history: List[Command] = []
    
    async def execute_command(self, command: Command) -> Any:
        result = await command.execute()
        self._history.append(command)
        return result
    
    async def undo_last(self) -> None:
        if self._history:
            command = self._history.pop()
            await command.undo()


# 3. OBSERVER PATTERN
# --------------------

class Event:
    """Evento para Observer pattern."""
    
    def __init__(self, type: str, data: Dict[str, Any]):
        self.type = type
        self.data = data
        self.timestamp = datetime.utcnow()


class Observer(ABC):
    """Observer base."""
    
    @abstractmethod
    async def update(self, event: Event) -> None:
        pass


class Subject:
    """Subject para Observer pattern."""
    
    def __init__(self):
        self._observers: List[Observer] = []
    
    def attach(self, observer: Observer) -> None:
        self._observers.append(observer)
    
    def detach(self, observer: Observer) -> None:
        self._observers.remove(observer)
    
    async def notify(self, event: Event) -> None:
        for observer in self._observers:
            await observer.update(event)


class LoggingObserver(Observer):
    """Observer para logging."""
    
    async def update(self, event: Event) -> None:
        print(f"[{event.timestamp}] {event.type}: {event.data}")


# 4. STRATEGY PATTERN
# --------------------

class ExecutionStrategy(ABC):
    """Strategy para ejecución de tareas."""
    
    @abstractmethod
    async def execute(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        pass


class SequentialStrategy(ExecutionStrategy):
    """Ejecución secuencial."""
    
    async def execute(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for task in tasks:
            # Ejecutar tarea
            results.append({"task": task, "status": "completed"})
        return results


class ParallelStrategy(ExecutionStrategy):
    """Ejecución paralela."""
    
    async def execute(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        # Ejecutar todas en paralelo
        return [{"task": t, "status": "completed"} for t in tasks]


class PriorityStrategy(ExecutionStrategy):
    """Ejecución por prioridad."""
    
    async def execute(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        sorted_tasks = sorted(tasks, key=lambda t: t.get("priority", 5))
        return [{"task": t, "status": "completed"} for t in sorted_tasks]


# 5. TEMPLATE METHOD PATTERN
# ---------------------------

class AgentTemplate(ABC):
    """Template Method para agentes."""
    
    async def execute(self, task: str) -> Dict[str, Any]:
        """Template method."""
        # 1. Pre-procesamiento
        context = await self._pre_process(task)
        
        # 2. Validación
        if not await self._validate(context):
            return {"error": "Validation failed"}
        
        # 3. Ejecución principal
        result = await self._execute_main(context)
        
        # 4. Post-procesamiento
        final_result = await self._post_process(result)
        
        return final_result
    
    @abstractmethod
    async def _pre_process(self, task: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def _validate(self, context: Dict[str, Any]) -> bool:
        pass
    
    @abstractmethod
    async def _execute_main(self, context: Dict[str, Any]) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def _post_process(self, result: Dict[str, Any]) -> Dict[str, Any]:
        pass


# 6. STATE PATTERN
# -----------------

class AgentState(ABC):
    """State para agentes."""
    
    @abstractmethod
    async def handle(self, agent: Any, input: str) -> str:
        pass


class IdleState(AgentState):
    """Estado idle."""
    
    async def handle(self, agent: Any, input: str) -> str:
        agent.set_state(ProcessingState())
        return "Starting processing..."


class ProcessingState(AgentState):
    """Estado procesando."""
    
    async def handle(self, agent: Any, input: str) -> str:
        # Procesar
        agent.set_state(IdleState())
        return "Processing complete"


class WaitingForInputState(AgentState):
    """Estado esperando input."""
    
    async def handle(self, agent: Any, input: str) -> str:
        if input:
            agent.set_state(ProcessingState())
            return "Input received, processing..."
        return "Still waiting for input"


# =============================================================================
# PATRONES ADICIONALES
# =============================================================================

# NULL OBJECT PATTERN
# -------------------

class NullAgent:
    """Null Object para agentes."""
    
    name = "NullAgent"
    
    async def execute(self, *args, **kwargs) -> Dict[str, Any]:
        return {"result": None, "message": "No agent available"}
    
    def add_tool(self, *args, **kwargs) -> None:
        pass


# SPECIFICATION PATTERN
# ----------------------

class Specification(ABC):
    """Specification pattern para consultas."""
    
    @abstractmethod
    def is_satisfied_by(self, candidate: Any) -> bool:
        pass


class AndSpecification(Specification):
    """AND de specifications."""
    
    def __init__(self, *specs: Specification):
        self._specs = specs
    
    def is_satisfied_by(self, candidate: Any) -> bool:
        return all(spec.is_satisfied_by(candidate) for spec in self._specs)


class OrSpecification(Specification):
    """OR de specifications."""
    
    def __init__(self, *specs: Specification):
        self._specs = specs
    
    def is_satisfied_by(self, candidate: Any) -> bool:
        return any(spec.is_satisfied_by(candidate) for spec in self._specs)
