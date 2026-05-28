"""
Orquestación del Super Asistente usando LangGraph.
Define el grafo de estados y el flujo entre agentes.
"""

from typing import Any, Dict, List, Optional, TypedDict, Annotated, Literal, Callable
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, Send, interrupt
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.store.memory import InMemoryStore
import operator
from datetime import datetime
import sqlite3

import sys
sys.path.insert(0, '/home/z/my-project/super_assistant_python')
from core.models import (
    SuperAssistantState, AgentRole, TaskStatus,
    MemoryItem, Task, HandoffMessage
)
from memory.memory_system import MemoryManager, create_memory_system


# =============================================================================
# REDUCERS PARA EL ESTADO
# =============================================================================

def merge_dict(left: Dict[str, Any], right: Dict[str, Any]) -> Dict[str, Any]:
    """Merge dictionaries for state updates."""
    return {**left, **right}


def append_to_list(left: List[Any], right: List[Any]) -> List[Any]:
    """Append lists for state updates."""
    return left + right


# =============================================================================
# NODOS DEL GRAFO
# =============================================================================

class GraphNodes:
    """
    Nodos del grafo de orquestación.
    Cada nodo representa una etapa en el flujo del Super Asistente.
    """
    
    def __init__(
        self,
        memory_manager: Optional[MemoryManager] = None,
        llm_client: Optional[Any] = None
    ):
        self.memory_manager = memory_manager or MemoryManager()
        self.llm_client = llm_client
    
    async def entry_node(
        self, 
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Nodo de entrada: inicializa el estado y recupera contexto.
        """
        updates = {
            "start_time": datetime.utcnow().isoformat(),
            "last_update": datetime.utcnow().isoformat(),
            "iteration_count": 0,
            "should_continue": True
        }
        
        # Recuperar memorias relevantes
        if state.get("messages"):
            query = state["messages"][-1].get("content", "") if state["messages"] else ""
            if query:
                memories = await self.memory_manager.retrieve_for_context(
                    SuperAssistantState(**state),
                    query=query
                )
                updates["retrieved_memories"] = [
                    {"content": m.content, "type": m.memory_type}
                    for m in memories
                ]
        
        return updates
    
    async def classify_intent_node(
        self,
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Clasifica la intención del usuario para routing.
        """
        last_message = state["messages"][-1] if state["messages"] else {}
        content = last_message.get("content", "").lower()
        
        # Clasificación simple basada en palabras clave
        # En producción, usar un modelo de clasificación
        intent = "general"
        
        research_keywords = ["buscar", "investigar", "encontrar", "qué es", "información sobre"]
        analysis_keywords = ["analizar", "comparar", "evaluar", "revisar", "estadísticas"]
        build_keywords = ["crear", "generar", "construir", "implementar", "desarrollar", "código"]
        validate_keywords = ["verificar", "validar", "probar", "test", "revisar"]
        
        if any(kw in content for kw in research_keywords):
            intent = "research"
        elif any(kw in content for kw in analysis_keywords):
            intent = "analysis"
        elif any(kw in content for kw in build_keywords):
            intent = "build"
        elif any(kw in content for kw in validate_keywords):
            intent = "validate"
        
        return {
            "current_intent": intent,
            "last_update": datetime.utcnow().isoformat()
        }
    
    async def supervisor_node(
        self,
        state: Dict[str, Any]
    ) -> Command[Literal["researcher", "analyzer", "builder", "validator", "respond", "end"]]:
        """
        Nodo supervisor: decide qué agente debe manejar la tarea.
        """
        intent = state.get("current_intent", "general")
        
        # Mapear intención a agente
        agent_mapping = {
            "research": "researcher",
            "analysis": "analyzer",
            "build": "builder",
            "validate": "validator",
            "general": "respond"
        }
        
        next_agent = agent_mapping.get(intent, "respond")
        
        # Verificar si debemos terminar
        if state.get("iteration_count", 0) >= state.get("max_iterations", 20):
            return Command(goto="end")
        
        return Command(
            update={
                "current_agent": "supervisor",
                "next_agent": next_agent,
                "iteration_count": state.get("iteration_count", 0) + 1,
                "last_update": datetime.utcnow().isoformat()
            },
            goto=next_agent
        )
    
    async def researcher_node(
        self,
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Nodo del agente investigador.
        """
        # Aquí iría la lógica real del investigador
        # Por ahora, simulamos una respuesta
        
        last_message = state["messages"][-1] if state["messages"] else {}
        query = last_message.get("content", "")
        
        result = f"[Researcher] Investigando: {query}"
        
        # Usar memorias recuperadas si están disponibles
        if state.get("retrieved_memories"):
            memories_str = "\n".join([
                f"- {m['content']}" 
                for m in state["retrieved_memories"][:3]
            ])
            result += f"\n\nContexto de memoria:\n{memories_str}"
        
        return {
            "current_agent": "researcher",
            "subagent_results": {
                **state.get("subagent_results", {}),
                "researcher": result
            },
            "messages": [{"role": "assistant", "content": result, "agent": "researcher"}],
            "last_update": datetime.utcnow().isoformat()
        }
    
    async def analyzer_node(
        self,
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Nodo del agente analista.
        """
        last_message = state["messages"][-1] if state["messages"] else {}
        query = last_message.get("content", "")
        
        result = f"[Analyzer] Analizando: {query}"
        
        # Si hay resultados de otros agentes, analizarlos
        if state.get("subagent_results", {}).get("researcher"):
            result += f"\nBasado en investigación previa: {state['subagent_results']['researcher'][:100]}..."
        
        return {
            "current_agent": "analyzer",
            "subagent_results": {
                **state.get("subagent_results", {}),
                "analyzer": result
            },
            "messages": [{"role": "assistant", "content": result, "agent": "analyzer"}],
            "last_update": datetime.utcnow().isoformat()
        }
    
    async def builder_node(
        self,
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Nodo del agente constructor.
        """
        last_message = state["messages"][-1] if state["messages"] else {}
        query = last_message.get("content", "")
        
        result = f"[Builder] Construyendo solución para: {query}"
        
        return {
            "current_agent": "builder",
            "subagent_results": {
                **state.get("subagent_results", {}),
                "builder": result
            },
            "messages": [{"role": "assistant", "content": result, "agent": "builder"}],
            "artifacts": {
                **state.get("artifacts", {}),
                "code": "# Generated code placeholder"
            },
            "last_update": datetime.utcnow().isoformat()
        }
    
    async def validator_node(
        self,
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Nodo del agente validador.
        """
        results = state.get("subagent_results", {})
        
        validation_result = "[Validator] Validando resultados:\n"
        for agent, result in results.items():
            validation_result += f"- {agent}: OK\n"
        
        return {
            "current_agent": "validator",
            "subagent_results": {
                **results,
                "validator": validation_result
            },
            "messages": [{"role": "assistant", "content": validation_result, "agent": "validator"}],
            "last_update": datetime.utcnow().isoformat()
        }
    
    async def respond_node(
        self,
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Nodo de respuesta final.
        """
        results = state.get("subagent_results", {})
        messages = state.get("messages", [])
        
        # Construir respuesta consolidada
        response_parts = []
        
        if results:
            response_parts.append("## Resultados de los agentes:")
            for agent, result in results.items():
                response_parts.append(f"### {agent.title()}\n{result}")
        else:
            # Respuesta directa si no hubo subagentes
            last_user_msg = next(
                (m for m in reversed(messages) if m.get("role") == "user"),
                {"content": ""}
            )
            response_parts.append(f"Respondiendo a: {last_user_msg.get('content', '')}")
        
        final_response = "\n\n".join(response_parts)
        
        # Almacenar en memoria
        await self.memory_manager.store_interaction(
            SuperAssistantState(**state),
            messages[-1].get("content", "") if messages else "",
            final_response
        )
        
        return {
            "current_agent": "respond",
            "messages": [{"role": "assistant", "content": final_response}],
            "should_continue": False,
            "last_update": datetime.utcnow().isoformat()
        }
    
    async def hitl_node(
        self,
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Nodo de Human-in-the-Loop.
        Interrumpe la ejecución para solicitar input humano.
        """
        # Verificar si hay herramientas pendientes de aprobación
        pending = state.get("pending_tool_calls", [])
        
        if pending:
            # Solicitar aprobación para la primera herramienta pendiente
            tool_call = pending[0]
            
            approval = interrupt({
                "type": "tool_approval",
                "tool_name": tool_call.get("name"),
                "arguments": tool_call.get("arguments"),
                "message": f"¿Aprobar ejecución de {tool_call.get('name')}?"
            })
            
            if approval:
                # Mover a tool_results como aprobado
                return {
                    "pending_tool_calls": pending[1:],
                    "tool_results": {
                        **state.get("tool_results", {}),
                        tool_call.get("id"): {
                            "status": "approved",
                            "approved_by": "human"
                        }
                    }
                }
            else:
                return {
                    "pending_tool_calls": pending[1:],
                    "tool_results": {
                        **state.get("tool_results", {}),
                        tool_call.get("id"): {
                            "status": "rejected"
                        }
                    }
                }
        
        return {}


# =============================================================================
# ROUTING FUNCTIONS
# =============================================================================

def route_after_classification(state: Dict[str, Any]) -> str:
    """Determina el siguiente paso después de clasificación."""
    # Siempre ir al supervisor primero
    return "supervisor"


def should_continue(state: Dict[str, Any]) -> str:
    """Determina si el flujo debe continuar."""
    if not state.get("should_continue", True):
        return "end"
    if state.get("iteration_count", 0) >= state.get("max_iterations", 20):
        return "end"
    return "continue"


def route_from_agent(state: Dict[str, Any]) -> str:
    """Determina el siguiente paso desde un agente."""
    current = state.get("current_agent", "")
    
    # Si el validador terminó, ir a responder
    if current == "validator":
        return "respond"
    
    # Si el builder terminó, validar
    if current == "builder":
        return "validator"
    
    # Por defecto, ir a responder
    return "respond"


# =============================================================================
# CONSTRUCCIÓN DEL GRAFO
# =============================================================================

def build_super_assistant_graph(
    memory_manager: Optional[MemoryManager] = None,
    enable_checkpoints: bool = True,
    checkpoint_db_path: str = ":memory:"
) -> StateGraph:
    """
    Construye el grafo de estados del Super Asistente.
    """
    # Crear nodos
    nodes = GraphNodes(memory_manager=memory_manager)
    
    # Crear el grafo
    builder = StateGraph(SuperAssistantState)
    
    # Agregar nodos
    builder.add_node("entry", nodes.entry_node)
    builder.add_node("classify", nodes.classify_intent_node)
    builder.add_node("supervisor", nodes.supervisor_node)
    builder.add_node("researcher", nodes.researcher_node)
    builder.add_node("analyzer", nodes.analyzer_node)
    builder.add_node("builder", nodes.builder_node)
    builder.add_node("validator", nodes.validator_node)
    builder.add_node("respond", nodes.respond_node)
    builder.add_node("hitl", nodes.hitl_node)
    
    # Definir flujo
    builder.add_edge(START, "entry")
    builder.add_edge("entry", "classify")
    builder.add_edge("classify", "supervisor")
    
    # Edges condicionales desde supervisor
    builder.add_conditional_edges(
        "supervisor",
        lambda state: state.get("next_agent", "respond"),
        {
            "researcher": "researcher",
            "analyzer": "analyzer",
            "builder": "builder",
            "validator": "validator",
            "respond": "respond",
            "end": END
        }
    )
    
    # Edges desde subagentes
    builder.add_edge("researcher", "respond")
    builder.add_edge("analyzer", "respond")
    builder.add_conditional_edges(
        "builder",
        route_from_agent,
        {"validator": "validator", "respond": "respond"}
    )
    builder.add_edge("validator", "respond")
    
    # Edge desde respond
    builder.add_edge("respond", END)
    
    return builder


def compile_graph(
    builder: StateGraph,
    enable_checkpoints: bool = True,
    checkpoint_db_path: str = ":memory:"
):
    """
    Compila el grafo con checkpointing opcional.
    """
    checkpointer = None
    if enable_checkpoints:
        if checkpoint_db_path == ":memory:":
            checkpointer = MemorySaver()
        else:
            conn = sqlite3.connect(checkpoint_db_path, check_same_thread=False)
            checkpointer = SqliteSaver(conn)
    
    # Store para memoria cross-thread
    store = InMemoryStore()
    
    return builder.compile(
        checkpointer=checkpointer,
        store=store
    )


# =============================================================================
# CLASE PRINCIPAL DEL ORQUESTADOR
# =============================================================================

class SuperAssistantOrchestrator:
    """
    Orquestador principal del Super Asistente.
    Maneja la ejecución del grafo y la comunicación entre componentes.
    """
    
    def __init__(
        self,
        memory_manager: Optional[MemoryManager] = None,
        enable_checkpoints: bool = True,
        checkpoint_db_path: str = ":memory:"
    ):
        self.memory_manager = memory_manager or MemoryManager()
        
        # Construir y compilar el grafo
        builder = build_super_assistant_graph(
            memory_manager=self.memory_manager,
            enable_checkpoints=enable_checkpoints,
            checkpoint_db_path=checkpoint_db_path
        )
        
        self.graph = compile_graph(
            builder,
            enable_checkpoints=enable_checkpoints,
            checkpoint_db_path=checkpoint_db_path
        )
    
    async def process(
        self,
        message: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        thread_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Procesa un mensaje del usuario.
        """
        # Estado inicial
        initial_state = {
            "messages": [{"role": "user", "content": message}],
            "user_id": user_id,
            "session_id": session_id,
            "iteration_count": 0,
            "max_iterations": 20
        }
        
        # Configuración para el thread
        config = {
            "configurable": {
                "thread_id": thread_id or session_id or "default"
            }
        }
        
        # Ejecutar el grafo
        result = await self.graph.ainvoke(initial_state, config)
        
        return result
    
    async def stream(
        self,
        message: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        thread_id: Optional[str] = None
    ):
        """
        Stream de la ejecución del grafo.
        """
        initial_state = {
            "messages": [{"role": "user", "content": message}],
            "user_id": user_id,
            "session_id": session_id,
            "iteration_count": 0,
            "max_iterations": 20
        }
        
        config = {
            "configurable": {
                "thread_id": thread_id or session_id or "default"
            }
        }
        
        async for event in self.graph.astream(initial_state, config):
            yield event
    
    def get_state(self, thread_id: str) -> Dict[str, Any]:
        """Obtiene el estado actual de un thread."""
        config = {"configurable": {"thread_id": thread_id}}
        return self.graph.get_state(config)
    
    def update_state(
        self, 
        thread_id: str, 
        updates: Dict[str, Any]
    ) -> None:
        """Actualiza el estado de un thread."""
        config = {"configurable": {"thread_id": thread_id}}
        self.graph.update_state(config, updates)


# =============================================================================
# FACTORY
# =============================================================================

def create_orchestrator(
    memory_backend: str = "in_memory",
    enable_checkpoints: bool = True,
    checkpoint_db_path: str = ":memory:"
) -> SuperAssistantOrchestrator:
    """
    Factory para crear el orquestador.
    """
    memory_system = create_memory_system(backend=memory_backend)
    memory_manager = MemoryManager(memory_system=memory_system)
    
    return SuperAssistantOrchestrator(
        memory_manager=memory_manager,
        enable_checkpoints=enable_checkpoints,
        checkpoint_db_path=checkpoint_db_path
    )
