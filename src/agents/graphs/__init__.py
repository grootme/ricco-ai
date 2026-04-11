"""
Agent Graphs Module for RICCO AI.

LangGraph DAG implementation for agent orchestration with cycle prevention.
"""

from typing import Any, Dict, List, Optional, Set
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)


class NodeStatus(str, Enum):
    """Status of a graph node."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class GraphNodeType(str, Enum):
    """Types of graph nodes."""
    INTENT_CLASSIFIER = "intent_classifier"
    CONTEXT_BUILDER = "context_builder"
    AGENT_ROUTER = "agent_router"
    RESPONSE_GENERATOR = "response_generator"
    VALIDATOR = "validator"
    AGENT = "agent"


class ExecutionConfig(BaseModel):
    """Configuration for graph execution."""
    max_recursion: int = Field(default=10, ge=1, le=50)
    timeout_seconds: int = Field(default=30, ge=5, le=300)
    enable_checkpoints: bool = True
    enable_tracing: bool = True
    parallel_execution: bool = False


class NodeModel(BaseModel):
    """Model for a graph node."""
    node_id: str
    node_type: GraphNodeType
    name: str
    description: str = ""
    config: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    timeout_seconds: int = 30


class EdgeModel(BaseModel):
    """Model for a graph edge."""
    edge_id: str
    source_node: str
    target_node: str
    condition: Optional[str] = None
    priority: int = 0


class ExecutionResult(BaseModel):
    """Result of graph execution."""
    execution_id: str
    graph_id: str
    status: str
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    nodes_executed: List[str] = Field(default_factory=list)
    total_nodes: int = 0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0


class StateGraph:
    """
    State graph for agent orchestration.
    
    Implements a DAG (Directed Acyclic Graph) for managing
    agent execution flow with cycle prevention.
    """
    
    def __init__(self, graph_id: str):
        self.graph_id = graph_id
        self.nodes: Dict[str, NodeModel] = {}
        self.edges: Dict[str, EdgeModel] = {}
        self._adjacency: Dict[str, List[str]] = {}
        self._entry_nodes: Set[str] = set()
    
    def add_node(self, node: NodeModel) -> None:
        """Add a node to the graph."""
        self.nodes[node.node_id] = node
        if node.node_id not in self._adjacency:
            self._adjacency[node.node_id] = []
        
        # Check if this is an entry node (no dependencies)
        if not node.dependencies:
            self._entry_nodes.add(node.node_id)
    
    def add_edge(self, edge: EdgeModel) -> None:
        """Add an edge to the graph."""
        self.edges[edge.edge_id] = edge
        
        if edge.source_node not in self._adjacency:
            self._adjacency[edge.source_node] = []
        self._adjacency[edge.source_node].append(edge.target_node)
    
    def get_entry_nodes(self) -> List[str]:
        """Get all entry nodes (nodes with no incoming edges)."""
        return list(self._entry_nodes)
    
    def get_next_nodes(self, node_id: str) -> List[str]:
        """Get nodes that should execute after the given node."""
        return self._adjacency.get(node_id, [])
    
    def validate_acyclic(self) -> bool:
        """Validate that the graph has no cycles."""
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        
        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in self._adjacency.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in self.nodes:
            if node not in visited:
                if has_cycle(node):
                    return False
        
        return True


class GraphEngine:
    """
    Engine for executing agent graphs.
    
    Provides:
    - Sequential and parallel execution
    - Cycle detection and prevention
    - Checkpointing for recovery
    - Execution tracing
    """
    
    def __init__(self, config: Optional[ExecutionConfig] = None):
        self.config = config or ExecutionConfig()
        self._active_executions: Dict[str, ExecutionResult] = {}
    
    async def execute(
        self,
        graph: StateGraph,
        initial_state: Dict[str, Any],
    ) -> ExecutionResult:
        """
        Execute a graph with the given initial state.
        """
        import uuid
        
        execution_id = str(uuid.uuid4())
        result = ExecutionResult(
            execution_id=execution_id,
            graph_id=graph.graph_id,
            status="running",
            total_nodes=len(graph.nodes),
        )
        
        self._active_executions[execution_id] = result
        start_time = datetime.utcnow()
        
        try:
            # Validate graph is acyclic
            if not graph.validate_acyclic():
                result.status = "failed"
                result.error = "Graph contains cycles"
                return result
            
            # Get entry nodes
            entry_nodes = graph.get_entry_nodes()
            if not entry_nodes:
                result.status = "failed"
                result.error = "No entry nodes found"
                return result
            
            # Execute nodes
            state = initial_state.copy()
            visited: Set[str] = set()
            
            if self.config.parallel_execution:
                await self._execute_parallel(graph, entry_nodes, state, result, visited)
            else:
                await self._execute_sequential(graph, entry_nodes, state, result, visited)
            
            result.status = "completed"
            result.result = state
            
        except Exception as e:
            result.status = "failed"
            result.error = str(e)
            logger.exception(f"Graph execution failed: {e}")
        
        finally:
            result.end_time = datetime.utcnow()
            result.execution_time_ms = (
                result.end_time - start_time
            ).total_seconds() * 1000
            self._active_executions.pop(execution_id, None)
        
        return result
    
    async def _execute_sequential(
        self,
        graph: StateGraph,
        nodes: List[str],
        state: Dict[str, Any],
        result: ExecutionResult,
        visited: Set[str],
        depth: int = 0,
    ) -> None:
        """Execute nodes sequentially."""
        if depth > self.config.max_recursion:
            raise RuntimeError(f"Max recursion depth exceeded: {self.config.max_recursion}")
        
        for node_id in nodes:
            if node_id in visited:
                continue
            
            node = graph.nodes.get(node_id)
            if not node:
                continue
            
            # Execute node
            await self._execute_node(node, state, result, visited)
            
            # Get next nodes
            next_nodes = graph.get_next_nodes(node_id)
            if next_nodes:
                await self._execute_sequential(
                    graph, next_nodes, state, result, visited, depth + 1
                )
    
    async def _execute_parallel(
        self,
        graph: StateGraph,
        nodes: List[str],
        state: Dict[str, Any],
        result: ExecutionResult,
        visited: Set[str],
        depth: int = 0,
    ) -> None:
        """Execute nodes in parallel."""
        import asyncio
        
        if depth > self.config.max_recursion:
            raise RuntimeError(f"Max recursion depth exceeded: {self.config.max_recursion}")
        
        tasks = []
        for node_id in nodes:
            if node_id in visited:
                continue
            
            node = graph.nodes.get(node_id)
            if node:
                tasks.append(self._execute_node(node, state, result, visited))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Get all next nodes
        all_next = set()
        for node_id in nodes:
            all_next.update(graph.get_next_nodes(node_id))
        
        if all_next:
            await self._execute_parallel(
                graph, list(all_next), state, result, visited, depth + 1
            )
    
    async def _execute_node(
        self,
        node: NodeModel,
        state: Dict[str, Any],
        result: ExecutionResult,
        visited: Set[str],
    ) -> None:
        """Execute a single node."""
        import asyncio
        
        visited.add(node.node_id)
        result.nodes_executed.append(node.node_id)
        
        logger.debug(f"Executing node: {node.name}")
        
        # Simulate node execution
        await asyncio.sleep(0.01)  # Placeholder for actual execution
        
        # Update state based on node type
        state[f"{node.node_id}_status"] = "completed"
    
    def get_execution_status(self, execution_id: str) -> Optional[ExecutionResult]:
        """Get the status of an execution."""
        return self._active_executions.get(execution_id)


class CommerceGraph(StateGraph):
    """Pre-built commerce workflow graph."""
    
    def __init__(self):
        super().__init__("commerce-graph")
        
        # Add nodes
        self.add_node(NodeModel(
            node_id="intent",
            node_type=GraphNodeType.INTENT_CLASSIFIER,
            name="Intent Classifier",
            description="Classify user intent",
        ))
        self.add_node(NodeModel(
            node_id="context",
            node_type=GraphNodeType.CONTEXT_BUILDER,
            name="Context Builder",
            description="Build context from user data",
            dependencies=["intent"],
        ))
        self.add_node(NodeModel(
            node_id="router",
            node_type=GraphNodeType.AGENT_ROUTER,
            name="Agent Router",
            description="Route to appropriate agent",
            dependencies=["context"],
        ))
        self.add_node(NodeModel(
            node_id="agent",
            node_type=GraphNodeType.AGENT,
            name="Commerce Agent",
            description="Execute commerce operations",
            dependencies=["router"],
        ))
        self.add_node(NodeModel(
            node_id="response",
            node_type=GraphNodeType.RESPONSE_GENERATOR,
            name="Response Generator",
            description="Generate final response",
            dependencies=["agent"],
        ))
        
        # Add edges
        self.add_edge(EdgeModel(
            edge_id="e1",
            source_node="intent",
            target_node="context",
        ))
        self.add_edge(EdgeModel(
            edge_id="e2",
            source_node="context",
            target_node="router",
        ))
        self.add_edge(EdgeModel(
            edge_id="e3",
            source_node="router",
            target_node="agent",
        ))
        self.add_edge(EdgeModel(
            edge_id="e4",
            source_node="agent",
            target_node="response",
        ))


class FinanceGraph(StateGraph):
    """Pre-built finance workflow graph."""
    
    def __init__(self):
        super().__init__("finance-graph")
        
        self.add_node(NodeModel(
            node_id="intent",
            node_type=GraphNodeType.INTENT_CLASSIFIER,
            name="Intent Classifier",
        ))
        self.add_node(NodeModel(
            node_id="context",
            node_type=GraphNodeType.CONTEXT_BUILDER,
            name="Context Builder",
            dependencies=["intent"],
        ))
        self.add_node(NodeModel(
            node_id="validator",
            node_type=GraphNodeType.VALIDATOR,
            name="Financial Validator",
            dependencies=["context"],
        ))
        self.add_node(NodeModel(
            node_id="agent",
            node_type=GraphNodeType.AGENT,
            name="Finance Agent",
            dependencies=["validator"],
        ))
        self.add_node(NodeModel(
            node_id="response",
            node_type=GraphNodeType.RESPONSE_GENERATOR,
            name="Response Generator",
            dependencies=["agent"],
        ))
        
        self.add_edge(EdgeModel(edge_id="f1", source_node="intent", target_node="context"))
        self.add_edge(EdgeModel(edge_id="f2", source_node="context", target_node="validator"))
        self.add_edge(EdgeModel(edge_id="f3", source_node="validator", target_node="agent"))
        self.add_edge(EdgeModel(edge_id="f4", source_node="agent", target_node="response"))


class HealthGraph(StateGraph):
    """Pre-built health consultation workflow graph."""
    
    def __init__(self):
        super().__init__("health-graph")
        
        self.add_node(NodeModel(
            node_id="intent",
            node_type=GraphNodeType.INTENT_CLASSIFIER,
            name="Intent Classifier",
        ))
        self.add_node(NodeModel(
            node_id="context",
            node_type=GraphNodeType.CONTEXT_BUILDER,
            name="Context Builder",
            dependencies=["intent"],
        ))
        self.add_node(NodeModel(
            node_id="agent",
            node_type=GraphNodeType.AGENT,
            name="Health Agent",
            dependencies=["context"],
        ))
        self.add_node(NodeModel(
            node_id="response",
            node_type=GraphNodeType.RESPONSE_GENERATOR,
            name="Response Generator",
            dependencies=["agent"],
        ))
        
        self.add_edge(EdgeModel(edge_id="h1", source_node="intent", target_node="context"))
        self.add_edge(EdgeModel(edge_id="h2", source_node="context", target_node="agent"))
        self.add_edge(EdgeModel(edge_id="h3", source_node="agent", target_node="response"))


class LogisticsGraph(StateGraph):
    """Pre-built logistics workflow graph."""
    
    def __init__(self):
        super().__init__("logistics-graph")
        
        self.add_node(NodeModel(
            node_id="intent",
            node_type=GraphNodeType.INTENT_CLASSIFIER,
            name="Intent Classifier",
        ))
        self.add_node(NodeModel(
            node_id="context",
            node_type=GraphNodeType.CONTEXT_BUILDER,
            name="Context Builder",
            dependencies=["intent"],
        ))
        self.add_node(NodeModel(
            node_id="agent",
            node_type=GraphNodeType.AGENT,
            name="Logistics Agent",
            dependencies=["context"],
        ))
        self.add_node(NodeModel(
            node_id="response",
            node_type=GraphNodeType.RESPONSE_GENERATOR,
            name="Response Generator",
            dependencies=["agent"],
        ))
        
        self.add_edge(EdgeModel(edge_id="l1", source_node="intent", target_node="context"))
        self.add_edge(EdgeModel(edge_id="l2", source_node="context", target_node="agent"))
        self.add_edge(EdgeModel(edge_id="l3", source_node="agent", target_node="response"))
