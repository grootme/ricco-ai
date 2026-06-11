"""
DeerFlow Core - Motor de Workflows

Implementación del grafo de flujo y motor de ejecución.
"""

from typing import Dict, Any, List, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)


class NodeStatus(str, Enum):
    """Estado de un nodo"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class EdgeCondition(str, Enum):
    """Tipo de condición de un edge"""
    ALWAYS = "always"
    ON_SUCCESS = "on_success"
    ON_FAILURE = "on_failure"
    CONDITIONAL = "conditional"


@dataclass
class Edge:
    """
    Conexión entre nodos.
    
    Define el flujo de ejecución entre nodos con condiciones opcionales.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    source: str = ""  # Node ID
    target: str = ""  # Node ID
    condition: EdgeCondition = EdgeCondition.ALWAYS
    expression: Optional[str] = None  # Python expression for conditional
    label: Optional[str] = None
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evalúa si el edge debe seguirse de forma segura."""
        if self.condition == EdgeCondition.ALWAYS:
            return True
        if self.condition == EdgeCondition.ON_SUCCESS:
            return context.get("_success", True)
        if self.condition == EdgeCondition.ON_FAILURE:
            return not context.get("_success", True)
        if self.condition == EdgeCondition.CONDITIONAL and self.expression:
            try:
                # Safe expression evaluation using limited operators
                # Only allow simple comparisons and boolean logic
                allowed_chars = set('0123456789.+-*/() ==!=<>andorTrueFalsenot in_ ')
                if not all(c in allowed_chars or c.isalnum() or c == '_' for c in self.expression):
                    logger.warning(f"Unsafe expression blocked: {self.expression}")
                    return False
                
                # Create safe evaluation context
                safe_context = {k: v for k, v in context.items() if not k.startswith('_')}
                safe_context['True'] = True
                safe_context['False'] = False
                
                # Use restricted eval with no builtins
                result = eval(self.expression, {"__builtins__": {}}, safe_context)
                return bool(result)
            except Exception as e:
                logger.warning(f"Edge evaluation failed: {e}")
                return False
        return True


@dataclass
class Node:
    """
    Nodo base del workflow.
    
    Un nodo representa una unidad de trabajo en el flujo.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: str = ""
    status: NodeStatus = NodeStatus.PENDING
    timeout: int = 300  # seconds
    retry_count: int = 0
    max_retries: int = 3
    
    # Resultados
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    output: Dict[str, Any] = field(default_factory=dict)
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta el nodo - sobrescribir en subclases"""
        raise NotImplementedError("Subclasses must implement execute()")
    
    def reset(self) -> None:
        """Reinicia el estado del nodo"""
        self.status = NodeStatus.PENDING
        self.started_at = None
        self.completed_at = None
        self.error = None
        self.output = {}
        self.retry_count = 0


@dataclass
class Workflow:
    """
    Definición de un workflow.
    
    Un workflow es un grafo dirigido de nodos conectados por edges.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: str = ""
    version: str = "1.0.0"
    
    # Nodos y edges
    nodes: Dict[str, Node] = field(default_factory=dict)
    edges: List[Edge] = field(default_factory=list)
    
    # Configuración
    start_node: Optional[str] = None
    end_nodes: Set[str] = field(default_factory=set)
    
    # Estado
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def add_node(self, node: Node) -> "Workflow":
        """Añade un nodo al workflow"""
        self.nodes[node.id] = node
        self.updated_at = datetime.utcnow()
        return self
    
    def add_edge(
        self,
        source: str,
        target: str,
        condition: EdgeCondition = EdgeCondition.ALWAYS,
        expression: Optional[str] = None
    ) -> Edge:
        """Añade un edge entre dos nodos"""
        edge = Edge(
            source=source,
            target=target,
            condition=condition,
            expression=expression
        )
        self.edges.append(edge)
        self.updated_at = datetime.utcnow()
        return edge
    
    def get_outgoing_edges(self, node_id: str) -> List[Edge]:
        """Obtiene edges salientes de un nodo"""
        return [e for e in self.edges if e.source == node_id]
    
    def get_incoming_edges(self, node_id: str) -> List[Edge]:
        """Obtiene edges entrantes a un nodo"""
        return [e for e in self.edges if e.target == node_id]
    
    def validate(self) -> List[str]:
        """Valida el workflow y retorna errores"""
        errors = []
        
        # Verificar nodo inicial
        if not self.start_node:
            errors.append("No start node defined")
        elif self.start_node not in self.nodes:
            errors.append(f"Start node '{self.start_node}' not found")
        
        # Verificar que todos los nodos referenciados existen
        for edge in self.edges:
            if edge.source not in self.nodes:
                errors.append(f"Edge source '{edge.source}' not found")
            if edge.target not in self.nodes:
                errors.append(f"Edge target '{edge.target}' not found")
        
        # Verificar que hay nodos finales
        if not self.end_nodes:
            errors.append("No end nodes defined")
        
        return errors
    
    def reset(self) -> None:
        """Reinicia todos los nodos"""
        for node in self.nodes.values():
            node.reset()


class WorkflowEngine:
    """
    Motor de ejecución de workflows.
    
    Ejecuta workflows de forma asíncrona con manejo de errores,
    reintentos y seguimiento de estado.
    """
    
    def __init__(self):
        self._workflows: Dict[str, Workflow] = {}
        self._running: Dict[str, Dict[str, Any]] = {}
    
    def register(self, workflow: Workflow) -> None:
        """Registra un workflow"""
        errors = workflow.validate()
        if errors:
            raise ValueError(f"Invalid workflow: {errors}")
        self._workflows[workflow.id] = workflow
        logger.info(f"Workflow registered: {workflow.name} ({workflow.id})")
    
    async def execute(
        self,
        workflow_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Ejecuta un workflow.
        
        Args:
            workflow_id: ID del workflow a ejecutar
            context: Contexto inicial de ejecución
        
        Returns:
            Resultado de la ejecución
        """
        workflow = self._workflows.get(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        # Inicializar contexto
        ctx = context or {}
        ctx["_workflow_id"] = workflow_id
        ctx["_started_at"] = datetime.utcnow().isoformat()
        
        # Reiniciar workflow
        workflow.reset()
        
        # Ejecutar desde nodo inicial
        current_node_id = workflow.start_node
        executed_nodes: List[str] = []
        
        while current_node_id:
            node = workflow.nodes.get(current_node_id)
            if not node:
                break
            
            # Ejecutar nodo
            node.status = NodeStatus.RUNNING
            node.started_at = datetime.utcnow()
            
            try:
                result = await node.execute(ctx)
                node.output = result
                node.status = NodeStatus.COMPLETED
                node.completed_at = datetime.utcnow()
                
                # Actualizar contexto
                ctx[node.id] = result
                executed_nodes.append(node.id)
                
                # Buscar siguiente nodo
                next_node = self._find_next_node(workflow, node.id, ctx)
                
                if next_node is None or node.id in workflow.end_nodes:
                    # Workflow completado
                    break
                
                current_node_id = next_node
                
            except Exception as e:
                node.status = NodeStatus.FAILED
                node.error = str(e)
                node.completed_at = datetime.utcnow()
                
                logger.error(f"Node {node.id} failed: {e}")
                
                # Intentar retry
                if node.retry_count < node.max_retries:
                    node.retry_count += 1
                    node.status = NodeStatus.PENDING
                    continue
                
                # Buscar camino de error
                next_node = self._find_next_node(
                    workflow, node.id, ctx, on_failure=True
                )
                
                if next_node:
                    current_node_id = next_node
                else:
                    # Workflow fallido
                    break
        
        return {
            "workflow_id": workflow_id,
            "status": "completed" if executed_nodes else "failed",
            "executed_nodes": executed_nodes,
            "context": ctx,
            "completed_at": datetime.utcnow().isoformat()
        }
    
    def _find_next_node(
        self,
        workflow: Workflow,
        node_id: str,
        context: Dict[str, Any],
        on_failure: bool = False
    ) -> Optional[str]:
        """Encuentra el siguiente nodo a ejecutar"""
        edges = workflow.get_outgoing_edges(node_id)
        
        for edge in edges:
            # Verificar condición
            if on_failure and edge.condition == EdgeCondition.ON_FAILURE:
                return edge.target
            if not on_failure and edge.condition in (
                EdgeCondition.ALWAYS, 
                EdgeCondition.ON_SUCCESS,
                EdgeCondition.CONDITIONAL
            ):
                if edge.evaluate(context):
                    return edge.target
        
        return None
