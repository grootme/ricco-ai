"""
DeerFlow Nodes - Tipos de Nodos

Implementaciones específicas de nodos para diferentes casos de uso.
"""

from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
import asyncio
import logging

from .core import Node, NodeStatus

logger = logging.getLogger(__name__)


@dataclass
class ActionNode(Node):
    """
    Nodo de acción simple.
    
    Ejecuta una función/coroutine y retorna su resultado.
    """
    action: Optional[Callable] = None
    action_name: str = ""
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta la acción"""
        if not self.action:
            return {"status": "skipped", "reason": "No action defined"}
        
        try:
            if asyncio.iscoroutinefunction(self.action):
                result = await self.action(context)
            else:
                result = self.action(context)
            
            return {
                "status": "success",
                "result": result,
                "action": self.action_name
            }
        except Exception as e:
            logger.error(f"ActionNode {self.id} error: {e}")
            raise


@dataclass
class DecisionNode(Node):
    """
    Nodo de decisión/branching.
    
    Evalúa condiciones y determina el camino a seguir.
    """
    conditions: Dict[str, str] = field(default_factory=dict)
    # conditions: {"condition_name": "python_expression"}
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evalúa condiciones"""
        results = {}
        
        for name, expression in self.conditions.items():
            try:
                result = bool(eval(expression, {"__builtins__": {}}, context))
                results[name] = result
            except Exception as e:
                results[name] = False
                logger.warning(f"Condition '{name}' evaluation failed: {e}")
        
        return {
            "status": "success",
            "evaluations": results,
            "context_updates": {"_decisions": results}
        }


@dataclass
class ParallelNode(Node):
    """
    Nodo de ejecución paralela.
    
    Ejecuta múltiples nodos en paralelo.
    """
    sub_nodes: List[Node] = field(default_factory=list)
    wait_for_all: bool = True
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta todos los sub-nodos en paralelo"""
        tasks = []
        
        for node in self.sub_nodes:
            node.status = NodeStatus.RUNNING
            node.started_at = self.started_at
            tasks.append(node.execute(context))
        
        if self.wait_for_all:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        else:
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Procesar resultados
        outputs = {}
        errors = []
        
        for i, result in enumerate(results):
            node = self.sub_nodes[i]
            if isinstance(result, Exception):
                node.status = NodeStatus.FAILED
                node.error = str(result)
                errors.append({"node": node.id, "error": str(result)})
            else:
                node.status = NodeStatus.COMPLETED
                node.output = result
                outputs[node.id] = result
        
        return {
            "status": "completed" if not errors else "partial",
            "outputs": outputs,
            "errors": errors,
            "total": len(self.sub_nodes),
            "successful": len(outputs)
        }


@dataclass
class AgentNode(Node):
    """
    Nodo que invoca a un agente.
    
    Permite integrar agentes IOVBA en workflows.
    """
    agent_id: str = ""
    agent_role: str = ""
    task: str = ""
    tools: List[str] = field(default_factory=list)
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta tarea con el agente"""
        # Interpolación de variables en el task
        interpolated_task = self.task
        for key, value in context.items():
            if isinstance(value, (str, int, float, bool)):
                interpolated_task = interpolated_task.replace(
                    f"{{{{{key}}}}}", str(value)
                )
        
        # TODO: Integrar con AgentService real
        # Por ahora retornamos simulación
        return {
            "status": "success",
            "agent_id": self.agent_id,
            "agent_role": self.agent_role,
            "task": interpolated_task,
            "tools_used": self.tools,
            "result": f"Agent {self.agent_role} processed: {interpolated_task[:50]}..."
        }


@dataclass
class TransformNode(Node):
    """
    Nodo de transformación de datos.
    
    Aplica transformaciones al contexto.
    """
    transformations: Dict[str, str] = field(default_factory=dict)
    # transformations: {"output_key": "python_expression"}
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Aplica transformaciones"""
        outputs = {}
        
        for output_key, expression in self.transformations.items():
            try:
                result = eval(expression, {"__builtins__": {}}, context)
                outputs[output_key] = result
            except Exception as e:
                logger.warning(f"Transform '{output_key}' failed: {e}")
                outputs[output_key] = None
        
        return {
            "status": "success",
            "transformations": outputs
        }


@dataclass
class DelayNode(Node):
    """
    Nodo de espera/delay.
    
    Pausa la ejecución por un tiempo determinado.
    """
    delay_seconds: float = 1.0
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Espera el tiempo especificado"""
        await asyncio.sleep(self.delay_seconds)
        
        return {
            "status": "success",
            "delayed_seconds": self.delay_seconds
        }


@dataclass
class LoopNode(Node):
    """
    Nodo de iteración/loop.
    
    Repite una secuencia de nodos sobre una lista de items.
    """
    items_key: str = ""  # Key en el contexto con la lista de items
    item_var: str = "item"  # Nombre de variable para cada item
    max_iterations: int = 100
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta el loop"""
        items = context.get(self.items_key, [])
        
        if not isinstance(items, (list, tuple)):
            return {
                "status": "error",
                "error": f"'{self.items_key}' is not a list"
            }
        
        if len(items) > self.max_iterations:
            items = items[:self.max_iterations]
            logger.warning(
                f"LoopNode {self.id}: truncated to {self.max_iterations} items"
            )
        
        results = []
        for i, item in enumerate(items):
            # Crear contexto para iteración
            iter_context = {**context, self.item_var: item, "_index": i}
            results.append({
                "index": i,
                "item": item,
                "status": "processed"
            })
        
        return {
            "status": "success",
            "iterations": len(results),
            "results": results
        }
