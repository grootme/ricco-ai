"""
DeerFlow Execution - Contexto y Resultados

Gestión del contexto de ejecución y resultados de workflows.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json


class ExecutionStatus(str, Enum):
    """Estado de ejecución de un workflow"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass
class ExecutionResult:
    """
    Resultado completo de una ejecución de workflow.
    """
    workflow_id: str
    execution_id: str
    status: ExecutionStatus = ExecutionStatus.PENDING
    
    # Tiempos
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
    
    # Resultados de nodos
    node_results: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    executed_nodes: List[str] = field(default_factory=list)
    failed_nodes: List[str] = field(default_factory=list)
    
    # Contexto final
    final_context: Dict[str, Any] = field(default_factory=dict)
    
    # Errores
    errors: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa el resultado"""
        return {
            "workflow_id": self.workflow_id,
            "execution_id": self.execution_id,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": self.duration_seconds,
            "node_results": self.node_results,
            "executed_nodes": self.executed_nodes,
            "failed_nodes": self.failed_nodes,
            "final_context": self.final_context,
            "errors": self.errors
        }
    
    def to_json(self) -> str:
        """Serializa a JSON"""
        return json.dumps(self.to_dict(), indent=2, default=str)


@dataclass
class ExecutionContext:
    """
    Contexto de ejecución de un workflow.
    
    Mantiene el estado, variables y resultados durante la ejecución.
    """
    workflow_id: str
    execution_id: str
    
    # Variables de contexto
    variables: Dict[str, Any] = field(default_factory=dict)
    
    # Estado de nodos
    node_states: Dict[str, str] = field(default_factory=dict)
    node_outputs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Metadatos
    started_at: datetime = field(default_factory=datetime.utcnow)
    parent_execution_id: Optional[str] = None
    
    def set_variable(self, key: str, value: Any) -> None:
        """Establece una variable de contexto"""
        self.variables[key] = value
    
    def get_variable(self, key: str, default: Any = None) -> Any:
        """Obtiene una variable de contexto"""
        return self.variables.get(key, default)
    
    def update_node_state(self, node_id: str, state: str) -> None:
        """Actualiza el estado de un nodo"""
        self.node_states[node_id] = state
    
    def set_node_output(self, node_id: str, output: Dict[str, Any]) -> None:
        """Establece la salida de un nodo"""
        self.node_outputs[node_id] = output
        # También actualizar variables con el output
        for key, value in output.items():
            if not key.startswith("_"):
                self.variables[f"{node_id}.{key}"] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa el contexto"""
        return {
            "workflow_id": self.workflow_id,
            "execution_id": self.execution_id,
            "variables": self.variables,
            "node_states": self.node_states,
            "node_outputs": self.node_outputs,
            "started_at": self.started_at.isoformat(),
            "parent_execution_id": self.parent_execution_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionContext":
        """Deserializa el contexto"""
        return cls(
            workflow_id=data["workflow_id"],
            execution_id=data["execution_id"],
            variables=data.get("variables", {}),
            node_states=data.get("node_states", {}),
            node_outputs=data.get("node_outputs", {}),
            started_at=datetime.fromisoformat(data["started_at"]) 
                if data.get("started_at") else datetime.utcnow(),
            parent_execution_id=data.get("parent_execution_id")
        )
    
    def snapshot(self) -> Dict[str, Any]:
        """Crea un snapshot del contexto actual"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "variables": dict(self.variables),
            "node_states": dict(self.node_states),
            "completed_nodes": [
                nid for nid, state in self.node_states.items()
                if state == "completed"
            ],
            "pending_nodes": [
                nid for nid, state in self.node_states.items()
                if state == "pending"
            ]
        }
