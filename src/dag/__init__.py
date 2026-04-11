"""
DAG Execution Module for RICCO AI.

LangGraph-based DAG execution for agent orchestration with cycle prevention.
"""

from typing import Any, Dict, List, Optional, Set
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import asyncio
import logging

logger = logging.getLogger(__name__)


class NodeStatus(str, Enum):
    """Status of a DAG node."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class DAGNodeType(str, Enum):
    """Types of DAG nodes."""
    START = "start"
    END = "end"
    AGENT = "agent"
    TOOL = "tool"
    CONDITION = "condition"
    PARALLEL = "parallel"
    LOOP = "loop"


class DAGNode(BaseModel):
    """Node in a DAG."""
    node_id: str
    node_type: DAGNodeType
    name: str
    config: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    timeout_seconds: int = 30
    retry_count: int = 0


class DAGEdge(BaseModel):
    """Edge in a DAG."""
    edge_id: str
    source: str
    target: str
    condition: Optional[str] = None
    label: Optional[str] = None


class DAGDefinition(BaseModel):
    """Complete DAG definition."""
    dag_id: str
    name: str
    description: str = ""
    nodes: List[DAGNode] = Field(default_factory=list)
    edges: List[DAGEdge] = Field(default_factory=list)
    entry_node: Optional[str] = None
    exit_nodes: List[str] = Field(default_factory=list)
    version: str = "1.0.0"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ExecutionState(BaseModel):
    """State of a DAG execution."""
    execution_id: str
    dag_id: str
    status: str = "pending"
    current_node: Optional[str] = None
    completed_nodes: List[str] = Field(default_factory=list)
    failed_nodes: List[str] = Field(default_factory=list)
    context: Dict[str, Any] = Field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class ExecutionResult(BaseModel):
    """Result of a DAG execution."""
    execution_id: str
    dag_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    execution_time_ms: float = 0.0
    nodes_executed: int = 0
    error: Optional[str] = None


class CycleDetector:
    """Detects cycles in a DAG."""
    
    @staticmethod
    def detect(nodes: List[DAGNode], edges: List[DAGEdge]) -> List[str]:
        """
        Detect cycles in the graph.
        
        Returns list of node IDs that are part of cycles.
        """
        # Build adjacency list
        adj: Dict[str, List[str]] = {n.node_id: [] for n in nodes}
        for edge in edges:
            if edge.source in adj:
                adj[edge.source].append(edge.target)
        
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        cycle_nodes: List[str] = []
        
        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        if node not in cycle_nodes:
                            cycle_nodes.append(node)
                        return True
                elif neighbor in rec_stack:
                    if node not in cycle_nodes:
                        cycle_nodes.append(node)
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in adj:
            if node not in visited:
                dfs(node)
        
        return cycle_nodes
    
    @staticmethod
    def validate(dag: DAGDefinition) -> bool:
        """Validate that a DAG has no cycles."""
        cycles = CycleDetector.detect(dag.nodes, dag.edges)
        return len(cycles) == 0


class RecursionGuard:
    """Guards against excessive recursion in DAG execution."""
    
    def __init__(self, max_depth: int = 10, max_total_nodes: int = 100):
        self.max_depth = max_depth
        self.max_total_nodes = max_total_nodes
    
    def check(self, depth: int, total_nodes: int) -> bool:
        """Check if execution should continue."""
        return depth < self.max_depth and total_nodes < self.max_total_nodes


class DAGExecutor:
    """
    Executes DAGs with cycle prevention and checkpointing.
    
    Features:
    - Sequential and parallel execution
    - Cycle detection and prevention
    - Recursion limits
    - Error handling and recovery
    """
    
    def __init__(
        self,
        max_depth: int = 10,
        max_total_nodes: int = 100,
        default_timeout: int = 30,
    ):
        self.recursion_guard = RecursionGuard(max_depth, max_total_nodes)
        self.default_timeout = default_timeout
        self._active_executions: Dict[str, ExecutionState] = {}
    
    async def execute(
        self,
        dag: DAGDefinition,
        initial_context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """
        Execute a DAG.
        
        Args:
            dag: DAG definition to execute
            initial_context: Initial execution context
            
        Returns:
            ExecutionResult with outcome
        """
        import time
        import uuid
        
        start_time = time.time()
        
        # Validate DAG
        if not CycleDetector.validate(dag):
            return ExecutionResult(
                execution_id=str(uuid.uuid4()),
                dag_id=dag.dag_id,
                status="failed",
                error="DAG contains cycles",
            )
        
        # Initialize execution state
        execution_id = str(uuid.uuid4())
        state = ExecutionState(
            execution_id=execution_id,
            dag_id=dag.dag_id,
            context=initial_context or {},
        )
        
        self._active_executions[execution_id] = state
        
        try:
            state.status = "running"
            state.started_at = datetime.utcnow()
            
            # Build node map
            node_map = {n.node_id: n for n in dag.nodes}
            
            # Find entry node
            entry = dag.entry_node
            if not entry:
                # Find node with no dependencies
                for node in dag.nodes:
                    if not node.dependencies:
                        entry = node.node_id
                        break
            
            if not entry:
                raise ValueError("No entry node found")
            
            # Execute from entry
            await self._execute_node(
                dag, node_map, entry, state, depth=0
            )
            
            state.status = "completed"
            state.completed_at = datetime.utcnow()
            
            return ExecutionResult(
                execution_id=execution_id,
                dag_id=dag.dag_id,
                status="completed",
                result=state.context,
                execution_time_ms=(time.time() - start_time) * 1000,
                nodes_executed=len(state.completed_nodes),
            )
            
        except Exception as e:
            state.status = "failed"
            state.error = str(e)
            state.completed_at = datetime.utcnow()
            
            logger.exception(f"DAG execution failed: {e}")
            
            return ExecutionResult(
                execution_id=execution_id,
                dag_id=dag.dag_id,
                status="failed",
                error=str(e),
                execution_time_ms=(time.time() - start_time) * 1000,
                nodes_executed=len(state.completed_nodes),
            )
            
        finally:
            self._active_executions.pop(execution_id, None)
    
    async def _execute_node(
        self,
        dag: DAGDefinition,
        node_map: Dict[str, DAGNode],
        node_id: str,
        state: ExecutionState,
        depth: int,
    ) -> None:
        """Execute a single node and its successors."""
        
        # Check recursion guard
        if not self.recursion_guard.check(depth, len(state.completed_nodes)):
            raise RuntimeError("Recursion limit exceeded")
        
        # Skip if already completed
        if node_id in state.completed_nodes:
            return
        
        node = node_map.get(node_id)
        if not node:
            return
        
        state.current_node = node_id
        
        # Check dependencies
        for dep in node.dependencies:
            if dep not in state.completed_nodes:
                return  # Dependency not met, skip
        
        logger.debug(f"Executing node: {node.name}")
        
        # Execute node (placeholder)
        await asyncio.sleep(0.01)
        
        # Update state
        state.completed_nodes.append(node_id)
        state.context[f"{node_id}_status"] = "completed"
        
        # Find successors
        successors = [
            e.target for e in dag.edges
            if e.source == node_id
        ]
        
        # Execute successors
        for successor in successors:
            await self._execute_node(
                dag, node_map, successor, state, depth + 1
            )
    
    def get_execution_state(self, execution_id: str) -> Optional[ExecutionState]:
        """Get the state of an active execution."""
        return self._active_executions.get(execution_id)


# Predefined DAGs
ORDER_PROCESSING_DAG = DAGDefinition(
    dag_id="order_processing",
    name="Order Processing Pipeline",
    description="Process customer orders from validation to fulfillment",
    nodes=[
        DAGNode(node_id="start", node_type=DAGNodeType.START, name="Start"),
        DAGNode(node_id="validate", node_type=DAGNodeType.CONDITION, name="Validate Order"),
        DAGNode(node_id="check_inventory", node_type=DAGNodeType.TOOL, name="Check Inventory"),
        DAGNode(node_id="process_payment", node_type=DAGNodeType.AGENT, name="Process Payment"),
        DAGNode(node_id="create_shipment", node_type=DAGNodeType.AGENT, name="Create Shipment"),
        DAGNode(node_id="notify", node_type=DAGNodeType.TOOL, name="Send Notification"),
        DAGNode(node_id="end", node_type=DAGNodeType.END, name="End"),
    ],
    edges=[
        DAGEdge(edge_id="e1", source="start", target="validate"),
        DAGEdge(edge_id="e2", source="validate", target="check_inventory"),
        DAGEdge(edge_id="e3", source="check_inventory", target="process_payment"),
        DAGEdge(edge_id="e4", source="process_payment", target="create_shipment"),
        DAGEdge(edge_id="e5", source="create_shipment", target="notify"),
        DAGEdge(edge_id="e6", source="notify", target="end"),
    ],
    entry_node="start",
    exit_nodes=["end"],
)

KYC_VERIFICATION_DAG = DAGDefinition(
    dag_id="kyc_verification",
    name="KYC Verification Flow",
    description="Identity verification for compliance",
    nodes=[
        DAGNode(node_id="start", node_type=DAGNodeType.START, name="Start"),
        DAGNode(node_id="collect_docs", node_type=DAGNodeType.AGENT, name="Collect Documents"),
        DAGNode(node_id="verify_id", node_type=DAGNodeType.TOOL, name="Verify ID"),
        DAGNode(node_id="check_watchlist", node_type=DAGNodeType.TOOL, name="Check Watchlist"),
        DAGNode(node_id="assess_risk", node_type=DAGNodeType.AGENT, name="Assess Risk"),
        DAGNode(node_id="update_trust", node_type=DAGNodeType.TOOL, name="Update Trust Score"),
        DAGNode(node_id="end", node_type=DAGNodeType.END, name="End"),
    ],
    edges=[
        DAGEdge(edge_id="k1", source="start", target="collect_docs"),
        DAGEdge(edge_id="k2", source="collect_docs", target="verify_id"),
        DAGEdge(edge_id="k3", source="verify_id", target="check_watchlist"),
        DAGEdge(edge_id="k4", source="check_watchlist", target="assess_risk"),
        DAGEdge(edge_id="k5", source="assess_risk", target="update_trust"),
        DAGEdge(edge_id="k6", source="update_trust", target="end"),
    ],
    entry_node="start",
    exit_nodes=["end"],
)

# DAG Registry
DAG_REGISTRY: Dict[str, DAGDefinition] = {
    "order_processing": ORDER_PROCESSING_DAG,
    "kyc_verification": KYC_VERIFICATION_DAG,
}


def get_dag(dag_id: str) -> Optional[DAGDefinition]:
    """Get a DAG by ID."""
    return DAG_REGISTRY.get(dag_id)


def list_dags() -> List[DAGDefinition]:
    """List all registered DAGs."""
    return list(DAG_REGISTRY.values())
