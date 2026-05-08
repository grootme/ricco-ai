"""
LangGraph Integration - Última versión con interrupt y command
Soporte para HITL (Human In The Loop)
"""

from typing import Dict, List, Optional, Any, Literal, TypedDict, Annotated
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import asyncio
import uuid

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt, Command
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

from .groups import IOVBAGroup, AgentProfile, IOVBARole
from .lead_assistant import HITLProposal, ProposalType


# State definitions
class AgentState(TypedDict):
    """Estado del agente en el grafo"""
    messages: Annotated[List, add_messages]
    current_role: str
    task: str
    domain: str
    context: Dict[str, Any]
    results: Dict[str, Any]
    pending_approval: Optional[Dict[str, Any]]
    approved: bool
    errors: List[str]


class IOVBAState(TypedDict):
    """Estado del grupo IOVBA"""
    group_id: str
    domain: str
    current_task: str
    workflow_step: str
    investigator_result: Optional[Dict[str, Any]]
    observer_result: Optional[Dict[str, Any]]
    validator_result: Optional[Dict[str, Any]]
    builder_result: Optional[Dict[str, Any]]
    assistant_result: Optional[Dict[str, Any]]
    final_result: Optional[Dict[str, Any]]
    errors: List[str]
    pending_hitl: Optional[Dict[str, Any]]


@dataclass
class LangGraphConfig:
    """Configuración de LangGraph"""
    model_name: str = "gpt-4o-mini"
    temperature: float = 0.7
    enable_checkpoints: bool = True
    hitl_enabled: bool = True
    max_iterations: int = 10


class LangGraphIOVBA:
    """
    Implementación de IOVBA con LangGraph
    Usa interrupt para HITL y Command para control de flujo
    """
    
    def __init__(
        self,
        config: Optional[LangGraphConfig] = None,
        openai_api_key: Optional[str] = None,
    ):
        self.config = config or LangGraphConfig()
        self.llm = ChatOpenAI(
            model=self.config.model_name,
            temperature=self.config.temperature,
            api_key=openai_api_key,
        )
        
        # Memory saver para checkpoints
        self.checkpointer = MemorySaver() if self.config.enable_checkpoints else None
        
        # Build the graph
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Construye el grafo de LangGraph para IOVBA"""
        
        # Create the graph
        workflow = StateGraph(IOVBAState)
        
        # Add nodes for each IOVBA role
        workflow.add_node("investigator", self._investigator_node)
        workflow.add_node("observer", self._observer_node)
        workflow.add_node("validator", self._validator_node)
        workflow.add_node("builder", self._builder_node)
        workflow.add_node("assistant", self._assistant_node)
        workflow.add_node("hitl_approval", self._hitl_approval_node)
        workflow.add_node("finalizer", self._finalizer_node)
        
        # Set entry point
        workflow.set_entry_point("investigator")
        
        # Add edges
        workflow.add_edge("investigator", "observer")
        workflow.add_edge("observer", "validator")
        
        # Conditional edge after validator
        workflow.add_conditional_edges(
            "validator",
            self._should_build_or_approve,
            {
                "build": "builder",
                "approve": "hitl_approval",
                "retry": "investigator",
            }
        )
        
        workflow.add_edge("builder", "hitl_approval")
        
        # Conditional edge after HITL
        workflow.add_conditional_edges(
            "hitl_approval",
            self._check_approval,
            {
                "approved": "finalizer",
                "rejected": "investigator",
                "pending": END,  # Wait for human input
            }
        )
        
        workflow.add_edge("finalizer", END)
        
        # Compile with checkpointer
        return workflow.compile(checkpointer=self.checkpointer)
    
    async def _investigator_node(self, state: IOVBAState) -> Command[IOVBAState]:
        """Nodo del Investigador"""
        prompt = f"""
        Eres el Investigador del equipo IOVBA para el dominio {state['domain']}.
        
        Tu tarea es investigar y analizar:
        {state['current_task']}
        
        Proporciona:
        1. Análisis del problema
        2. Información relevante encontrada
        3. Recomendaciones iniciales
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=prompt),
                HumanMessage(content=state['current_task'])
            ])
            
            return Command(
                update={
                    "investigator_result": {
                        "analysis": response.content,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                    "workflow_step": "investigator_complete",
                }
            )
        except Exception as e:
            return Command(
                update={
                    "errors": state.get("errors", []) + [f"Investigator error: {str(e)}"],
                }
            )
    
    async def _observer_node(self, state: IOVBAState) -> Command[IOVBAState]:
        """Nodo del Observador"""
        if not state.get("investigator_result"):
            return Command(update={"workflow_step": "waiting_investigator"})
        
        prompt = f"""
        Eres el Observador del equipo IOVBA para el dominio {state['domain']}.
        
        Revisa el análisis del Investigador:
        {state['investigator_result']['analysis']}
        
        Tu tarea es:
        1. Identificar patrones y anomalías
        2. Detectar posibles problemas
        3. Monitorear riesgos
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=prompt),
                HumanMessage(content="Proporciona tus observaciones.")
            ])
            
            return Command(
                update={
                    "observer_result": {
                        "observations": response.content,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                    "workflow_step": "observer_complete",
                }
            )
        except Exception as e:
            return Command(
                update={
                    "errors": state.get("errors", []) + [f"Observer error: {str(e)}"],
                }
            )
    
    async def _validator_node(self, state: IOVBAState) -> Command[IOVBAState]:
        """Nodo del Validador"""
        investigator = state.get("investigator_result", {})
        observer = state.get("observer_result", {})
        
        prompt = f"""
        Eres el Validador del equipo IOVBA para el dominio {state['domain']}.
        
        Análisis del Investigador:
        {investigator.get('analysis', 'N/A')}
        
        Observaciones del Observador:
        {observer.get('observations', 'N/A')}
        
        Tu tarea es:
        1. Validar la calidad del análisis
        2. Verificar las observaciones
        3. Decidir si proceder con la construcción o solicitar revisión
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=prompt),
                HumanMessage(content="Proporciona tu validación y decisión.")
            ])
            
            # Parse decision
            content = response.content.lower()
            if "proceder" in content or "aprobar" in content:
                decision = "build"
            elif "revisar" in content or "rechazar" in content:
                decision = "retry"
            else:
                decision = "approve"  # Need HITL
            
            return Command(
                update={
                    "validator_result": {
                        "validation": response.content,
                        "decision": decision,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                    "workflow_step": "validator_complete",
                }
            )
        except Exception as e:
            return Command(
                update={
                    "errors": state.get("errors", []) + [f"Validator error: {str(e)}"],
                }
            )
    
    async def _builder_node(self, state: IOVBAState) -> Command[IOVBAState]:
        """Nodo del Builder"""
        prompt = f"""
        Eres el Builder del equipo IOVBA para el dominio {state['domain']}.
        
        Tarea original: {state['current_task']}
        
        Análisis validado:
        {state.get('validator_result', {}).get('validation', 'N/A')}
        
        Tu tarea es:
        1. Implementar la solución
        2. Crear el artefacto solicitado
        3. Documentar el resultado
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=prompt),
                HumanMessage(content="Construye la solución.")
            ])
            
            return Command(
                update={
                    "builder_result": {
                        "artifact": response.content,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                    "workflow_step": "builder_complete",
                }
            )
        except Exception as e:
            return Command(
                update={
                    "errors": state.get("errors", []) + [f"Builder error: {str(e)}"],
                }
            )
    
    async def _assistant_node(self, state: IOVBAState) -> Command[IOVBAState]:
        """Nodo del Asistente"""
        prompt = f"""
        Eres el Asistente coordinador del equipo IOVBA para el dominio {state['domain']}.
        
        Resumen del workflow:
        - Investigador: {bool(state.get('investigator_result'))}
        - Observador: {bool(state.get('observer_result'))}
        - Validador: {bool(state.get('validator_result'))}
        - Builder: {bool(state.get('builder_result'))}
        
        Tu tarea es coordinar y documentar el progreso.
        """
        
        try:
            response = await self.llm.ainvoke([
                SystemMessage(content=prompt),
                HumanMessage(content="Proporciona el resumen de coordinación.")
            ])
            
            return Command(
                update={
                    "assistant_result": {
                        "coordination": response.content,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                    "workflow_step": "assistant_complete",
                }
            )
        except Exception as e:
            return Command(
                update={
                    "errors": state.get("errors", []) + [f"Assistant error: {str(e)}"],
                }
            )
    
    async def _hitl_approval_node(self, state: IOVBAState) -> Command[IOVBAState]:
        """
        Nodo de aprobación HITL
        Usa interrupt para pausar y esperar aprobación humana
        """
        if not self.config.hitl_enabled:
            return Command(update={"workflow_step": "hitl_skipped"})
        
        # Crear propuesta de aprobación
        proposal = {
            "id": str(uuid.uuid4()),
            "type": "workflow_approval",
            "task": state["current_task"],
            "domain": state["domain"],
            "investigator_result": state.get("investigator_result"),
            "observer_result": state.get("observer_result"),
            "validator_result": state.get("validator_result"),
            "builder_result": state.get("builder_result"),
            "created_at": datetime.utcnow().isoformat(),
        }
        
        # INTERRUPT - Pausa la ejecución y espera input humano
        approval = interrupt({
            "type": "approval_required",
            "proposal": proposal,
            "message": "Se requiere aprobación humana para continuar con el workflow.",
        })
        
        return Command(
            update={
                "pending_hitl": proposal,
                "workflow_step": "hitl_complete",
            }
        )
    
    async def _finalizer_node(self, state: IOVBAState) -> Command[IOVBAState]:
        """Nodo finalizador"""
        final_result = {
            "task": state["current_task"],
            "domain": state["domain"],
            "investigator": state.get("investigator_result"),
            "observer": state.get("observer_result"),
            "validator": state.get("validator_result"),
            "builder": state.get("builder_result"),
            "assistant": state.get("assistant_result"),
            "completed_at": datetime.utcnow().isoformat(),
            "status": "completed",
        }
        
        return Command(
            update={
                "final_result": final_result,
                "workflow_step": "completed",
            }
        )
    
    def _should_build_or_approve(self, state: IOVBAState) -> str:
        """Determina el siguiente paso después de validación"""
        validator_result = state.get("validator_result", {})
        decision = validator_result.get("decision", "approve")
        
        if decision == "build":
            return "build"
        elif decision == "retry":
            return "retry"
        else:
            return "approve"
    
    def _check_approval(self, state: IOVBAState) -> str:
        """Verifica el estado de la aprobación HITL"""
        pending = state.get("pending_hitl")
        
        if not pending:
            return "approved"
        
        # Si hay pending_hitl, verificar si fue aprobado
        # Esto se actualiza externamente via resume
        if pending.get("approved") is True:
            return "approved"
        elif pending.get("approved") is False:
            return "rejected"
        else:
            return "pending"
    
    async def run_workflow(
        self,
        task: str,
        domain: str,
        thread_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Ejecuta el workflow IOVBA completo"""
        initial_state: IOVBAState = {
            "group_id": str(uuid.uuid4()),
            "domain": domain,
            "current_task": task,
            "workflow_step": "init",
            "investigator_result": None,
            "observer_result": None,
            "validator_result": None,
            "builder_result": None,
            "assistant_result": None,
            "final_result": None,
            "errors": [],
            "pending_hitl": None,
        }
        
        config = {"configurable": {"thread_id": thread_id or str(uuid.uuid4())}}
        
        result = await self.graph.ainvoke(initial_state, config)
        return result
    
    async def resume_with_approval(
        self,
        thread_id: str,
        approved: bool,
        feedback: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Resume el workflow con una decisión de aprobación
        """
        config = {"configurable": {"thread_id": thread_id}}
        
        # Proporcionar la aprobación al interrupt
        approval_data = {
            "approved": approved,
            "feedback": feedback,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        result = await self.graph.ainvoke(
            {"pending_hitl": {"approved": approved, "feedback": feedback}},
            config,
        )
        return result
    
    def get_graph_visualization(self) -> str:
        """Retorna la visualización del grafo en formato ASCII"""
        try:
            return self.graph.get_graph().draw_ascii()
        except Exception:
            return "Graph visualization not available"


class LangGraphLeadAssistant:
    """
    Lead Assistant implementado con LangGraph
    Coordina múltiples grupos IOVBA
    """
    
    def __init__(
        self,
        config: Optional[LangGraphConfig] = None,
        openai_api_key: Optional[str] = None,
    ):
        self.config = config or LangGraphConfig()
        self.llm = ChatOpenAI(
            model=self.config.model_name,
            temperature=self.config.temperature,
            api_key=openai_api_key,
        )
        self.checkpointer = MemorySaver()
        self.graph = self._build_lead_graph()
    
    def _build_lead_graph(self) -> StateGraph:
        """Construye el grafo del Lead Assistant"""
        
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("analyze", self._analyze_node)
        workflow.add_node("plan", self._plan_node)
        workflow.add_node("delegate", self._delegate_node)
        workflow.add_node("hitl_create_approval", self._hitl_create_approval_node)
        workflow.add_node("execute", self._execute_node)
        workflow.add_node("synthesize", self._synthesize_node)
        
        # Entry point
        workflow.set_entry_point("analyze")
        
        # Edges
        workflow.add_edge("analyze", "plan")
        
        workflow.add_conditional_edges(
            "plan",
            self._should_create_agent,
            {
                "delegate": "delegate",
                "create": "hitl_create_approval",
            }
        )
        
        workflow.add_conditional_edges(
            "hitl_create_approval",
            self._check_creation_approval,
            {
                "approved": "delegate",
                "rejected": END,
                "pending": END,
            }
        )
        
        workflow.add_edge("delegate", "execute")
        workflow.add_edge("execute", "synthesize")
        workflow.add_edge("synthesize", END)
        
        return workflow.compile(checkpointer=self.checkpointer)
    
    async def _analyze_node(self, state: AgentState) -> Command[AgentState]:
        """Analiza la tarea entrante"""
        prompt = f"""
        Analiza la siguiente tarea y determina:
        1. Dominio principal
        2. Complejidad (baja, media, alta)
        3. Agentes necesarios
        4. Posible necesidad de crear nuevos agentes
        
        Tarea: {state['task']}
        Contexto: {state['context']}
        """
        
        response = await self.llm.ainvoke([
            SystemMessage(content=prompt),
            HumanMessage(content=state['task'])
        ])
        
        return Command(
            update={
                "results": {"analysis": response.content},
                "current_role": "analyzer",
            }
        )
    
    async def _plan_node(self, state: AgentState) -> Command[AgentState]:
        """Planifica la ejecución"""
        prompt = f"""
        Basado en el análisis anterior, crea un plan de ejecución detallado.
        
        Análisis: {state['results'].get('analysis', 'N/A')}
        
        Incluye:
        1. Pasos a seguir
        2. Agentes a utilizar
        3. Dependencias
        4. Estimación de tiempo
        """
        
        response = await self.llm.ainvoke([
            SystemMessage(content=prompt),
            HumanMessage(content="Proporciona el plan de ejecución.")
        ])
        
        return Command(
            update={
                "results": {**state['results'], "plan": response.content},
                "current_role": "planner",
            }
        )
    
    async def _delegate_node(self, state: AgentState) -> Command[AgentState]:
        """Delega tareas a los agentes"""
        return Command(
            update={
                "current_role": "delegator",
                "results": {**state['results'], "delegation": "Tasks delegated to IOVBA groups"},
            }
        )
    
    async def _hitl_create_approval_node(self, state: AgentState) -> Command[AgentState]:
        """Solicita aprobación para crear nuevo agente/grupo"""
        proposal = interrupt({
            "type": "create_agent_approval",
            "task": state["task"],
            "context": state["context"],
            "message": "Se detectó la necesidad de crear un nuevo agente o grupo. ¿Desea aprobar?",
        })
        
        return Command(
            update={
                "pending_approval": proposal,
                "current_role": "hitl_awaiting",
            }
        )
    
    async def _execute_node(self, state: AgentState) -> Command[AgentState]:
        """Ejecuta las tareas delegadas"""
        return Command(
            update={
                "current_role": "executor",
                "results": {**state['results'], "execution": "Tasks executed"},
            }
        )
    
    async def _synthesize_node(self, state: AgentState) -> Command[AgentState]:
        """Sintetiza los resultados"""
        prompt = f"""
        Sintetiza los siguientes resultados en una respuesta coherente:
        
        Análisis: {state['results'].get('analysis', 'N/A')}
        Plan: {state['results'].get('plan', 'N/A')}
        Ejecución: {state['results'].get('execution', 'N/A')}
        
        Proporciona una respuesta final clara y estructurada.
        """
        
        response = await self.llm.ainvoke([
            SystemMessage(content=prompt),
            HumanMessage(content="Proporciona la síntesis final.")
        ])
        
        return Command(
            update={
                "current_role": "synthesizer",
                "results": {**state['results'], "synthesis": response.content},
            }
        )
    
    def _should_create_agent(self, state: AgentState) -> str:
        """Determina si se necesita crear un nuevo agente"""
        analysis = state['results'].get('analysis', '').lower()
        
        if "nuevo agente" in analysis or "crear agente" in analysis:
            return "create"
        return "delegate"
    
    def _check_creation_approval(self, state: AgentState) -> str:
        """Verifica si la creación fue aprobada"""
        pending = state.get('pending_approval')
        
        if not pending:
            return "delegate"
        
        if pending.get('approved') is True:
            return "approved"
        elif pending.get('approved') is False:
            return "rejected"
        return "pending"
    
    async def coordinate(
        self,
        task: str,
        domain: str,
        context: Optional[Dict[str, Any]] = None,
        thread_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Coordina una tarea completa"""
        initial_state: AgentState = {
            "messages": [],
            "current_role": "init",
            "task": task,
            "domain": domain,
            "context": context or {},
            "results": {},
            "pending_approval": None,
            "approved": False,
            "errors": [],
        }
        
        config = {"configurable": {"thread_id": thread_id or str(uuid.uuid4())}}
        
        result = await self.graph.ainvoke(initial_state, config)
        return result
    
    async def resume_with_creation_approval(
        self,
        thread_id: str,
        approved: bool,
        agent_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Resume con aprobación de creación"""
        config = {"configurable": {"thread_id": thread_id}}
        
        approval_data = {
            "approved": approved,
            "agent_config": agent_config,
        }
        
        result = await self.graph.ainvoke(
            {"pending_approval": approval_data},
            config,
        )
        return result
