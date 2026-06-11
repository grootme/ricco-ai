"""
DeerFlow Validator - Validación de Workflows

Proporciona validación de workflows incluyendo detección de ciclos,
verificación de nodos huérfanos y validación de edges.
"""

from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from .core import Workflow, Edge, EdgeCondition


class ValidationSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationError:
    """Error de validación"""
    code: str
    message: str
    severity: ValidationSeverity
    location: Optional[str] = None
    suggestion: Optional[str] = None


class WorkflowValidator:
    """
    Validador de Workflows.
    
    Realiza validaciones completas incluyendo:
    - Detección de ciclos
    - Nodos huérfanos
    - Nodos inalcanzables
    - Edges inválidos
    - Configuración incompleta
    """
    
    def validate(self, workflow: Workflow) -> List[ValidationError]:
        """Ejecuta todas las validaciones"""
        errors = []
        
        # Validaciones estructurales
        errors.extend(self._validate_structure(workflow))
        
        # Detección de ciclos
        errors.extend(self._validate_cycles(workflow))
        
        # Nodos inalcanzables
        errors.extend(self._validate_reachability(workflow))
        
        # Configuración
        errors.extend(self._validate_config(workflow))
        
        return errors
    
    def _validate_structure(self, workflow: Workflow) -> List[ValidationError]:
        """Valida la estructura básica del workflow"""
        errors = []
        
        # Sin nodos
        if not workflow.nodes:
            errors.append(ValidationError(
                code="EMPTY_WORKFLOW",
                message="El workflow no tiene nodos",
                severity=ValidationSeverity.ERROR,
                suggestion="Añade al menos un nodo al workflow"
            ))
            return errors
        
        # Sin nodo inicial
        if not workflow.start_node:
            errors.append(ValidationError(
                code="NO_START_NODE",
                message="No hay nodo inicial definido",
                severity=ValidationSeverity.ERROR,
                suggestion="Define workflow.start_node con el ID del primer nodo"
            ))
        elif workflow.start_node not in workflow.nodes:
            errors.append(ValidationError(
                code="INVALID_START_NODE",
                message=f"El nodo inicial '{workflow.start_node}' no existe",
                severity=ValidationSeverity.ERROR,
                location=f"start_node={workflow.start_node}",
                suggestion=f"Usa uno de: {list(workflow.nodes.keys())}"
            ))
        
        # Sin nodos finales
        if not workflow.end_nodes:
            errors.append(ValidationError(
                code="NO_END_NODES",
                message="No hay nodos finales definidos",
                severity=ValidationSeverity.WARNING,
                suggestion="Define workflow.end_nodes con los IDs de los nodos terminales"
            ))
        
        # Validar edges
        for edge in workflow.edges:
            if edge.source not in workflow.nodes:
                errors.append(ValidationError(
                    code="INVALID_EDGE_SOURCE",
                    message=f"Edge con origen inexistente: {edge.source}",
                    severity=ValidationSeverity.ERROR,
                    location=f"edge {edge.id}",
                    suggestion=f"El nodo '{edge.source}' no existe en el workflow"
                ))
            if edge.target not in workflow.nodes:
                errors.append(ValidationError(
                    code="INVALID_EDGE_TARGET",
                    message=f"Edge con destino inexistente: {edge.target}",
                    severity=ValidationSeverity.ERROR,
                    location=f"edge {edge.id}",
                    suggestion=f"El nodo '{edge.target}' no existe en el workflow"
                ))
        
        return errors
    
    def detect_cycles(self, workflow: Workflow) -> List[List[str]]:
        """
        Detecta todos los ciclos en el workflow.
        
        Returns:
            Lista de ciclos encontrados, cada ciclo es una lista de node IDs
        """
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node_id: str, path: List[str]) -> None:
            visited.add(node_id)
            rec_stack.add(node_id)
            
            for edge in workflow.get_outgoing_edges(node_id):
                neighbor = edge.target
                if neighbor not in visited:
                    dfs(neighbor, path + [neighbor])
                elif neighbor in rec_stack:
                    # Encontramos un ciclo
                    cycle_start = path.index(neighbor) if neighbor in path else 0
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)
            
            rec_stack.remove(node_id)
        
        for node_id in workflow.nodes:
            if node_id not in visited:
                dfs(node_id, [node_id])
        
        return cycles
    
    def _validate_cycles(self, workflow: Workflow) -> List[ValidationError]:
        """Valida que no haya ciclos no manejados"""
        errors = []
        
        cycles = self.detect_cycles(workflow)
        
        for cycle in cycles:
            # Verificar si el ciclo tiene una condición de salida
            has_exit = False
            for i, node_id in enumerate(cycle[:-1]):
                next_node = cycle[i + 1]
                for edge in workflow.get_outgoing_edges(node_id):
                    if edge.target == next_node:
                        if edge.condition == EdgeCondition.CONDITIONAL:
                            has_exit = True
                            break
            
            if not has_exit:
                errors.append(ValidationError(
                    code="UNHANDLED_CYCLE",
                    message=f"Ciclo sin condición de salida detectado: {' -> '.join(cycle)}",
                    severity=ValidationSeverity.ERROR,
                    location=f"nodes: {cycle}",
                    suggestion="Añade una condición al edge para salir del ciclo"
                ))
        
        return errors
    
    def _validate_reachability(self, workflow: Workflow) -> List[ValidationError]:
        """Valida que todos los nodos sean alcanzables"""
        errors = []
        
        if not workflow.start_node or workflow.start_node not in workflow.nodes:
            return errors
        
        # BFS desde el nodo inicial
        reachable = set()
        queue = [workflow.start_node]
        
        while queue:
            node_id = queue.pop(0)
            if node_id in reachable:
                continue
            reachable.add(node_id)
            
            for edge in workflow.get_outgoing_edges(node_id):
                if edge.target not in reachable:
                    queue.append(edge.target)
        
        # Verificar nodos inalcanzables
        unreachable = set(workflow.nodes.keys()) - reachable
        
        for node_id in unreachable:
            errors.append(ValidationError(
                code="UNREACHABLE_NODE",
                message=f"El nodo '{node_id}' no es alcanzable desde el nodo inicial",
                severity=ValidationSeverity.WARNING,
                location=f"node {node_id}",
                suggestion="Conecta el nodo al flujo principal o elimínalo"
            ))
        
        # Verificar nodos huérfanos (sin edges entrantes excepto start)
        for node_id in workflow.nodes:
            if node_id == workflow.start_node:
                continue
            incoming = workflow.get_incoming_edges(node_id)
            if not incoming and node_id in reachable:
                errors.append(ValidationError(
                    code="ORPHAN_NODE",
                    message=f"El nodo '{node_id}' no tiene edges entrantes",
                    severity=ValidationSeverity.WARNING,
                    location=f"node {node_id}"
                ))
        
        return errors
    
    def _validate_config(self, workflow: Workflow) -> List[ValidationError]:
        """Valida la configuración de los nodos"""
        errors = []
        
        for node_id, node in workflow.nodes.items():
            # Timeout muy bajo
            if node.timeout < 10:
                errors.append(ValidationError(
                    code="LOW_TIMEOUT",
                    message=f"El nodo '{node_id}' tiene un timeout muy bajo ({node.timeout}s)",
                    severity=ValidationSeverity.INFO,
                    location=f"node {node_id}",
                    suggestion="Considera aumentar el timeout a al menos 30 segundos"
                ))
            
            # Max retries muy alto
            if node.max_retries > 10:
                errors.append(ValidationError(
                    code="HIGH_RETRIES",
                    message=f"El nodo '{node_id}' tiene muchos reintentos ({node.max_retries})",
                    severity=ValidationSeverity.WARNING,
                    location=f"node {node_id}",
                    suggestion="Considera reducir los reintentos a máximo 5"
                ))
        
        return errors
    
    def is_valid(self, workflow: Workflow) -> Tuple[bool, List[ValidationError]]:
        """
        Verifica si el workflow es válido.
        
        Returns:
            Tupla de (es_válido, errores)
        """
        errors = self.validate(workflow)
        critical_errors = [e for e in errors if e.severity == ValidationSeverity.ERROR]
        return len(critical_errors) == 0, errors
    
    def get_execution_order(self, workflow: Workflow) -> List[str]:
        """
        Obtiene el orden de ejecución de los nodos.
        
        Returns:
            Lista ordenada de node IDs
        """
        if not workflow.start_node:
            return []
        
        visited = set()
        order = []
        
        def visit(node_id: str) -> None:
            if node_id in visited:
                return
            visited.add(node_id)
            
            for edge in workflow.get_outgoing_edges(node_id):
                visit(edge.target)
            
            order.append(node_id)
        
        visit(workflow.start_node)
        return order


def validate_workflow(workflow: Workflow) -> Tuple[bool, List[ValidationError]]:
    """
    Función de conveniencia para validar un workflow.
    
    Args:
        workflow: El workflow a validar
    
    Returns:
        Tupla de (es_válido, lista_de_errores)
    """
    validator = WorkflowValidator()
    return validator.is_valid(workflow)
