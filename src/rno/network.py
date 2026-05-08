"""
Obviousness Network - Red Neuronal de Obviedades

Implementa la RNO donde cada Trasfondo de Obviedad se modela
como una neurona artificial con pesos dinámicos que representan
la relevancia de diferentes contextos.
"""

import json
import math
from typing import Optional, Dict, Any, List, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class NeuronType(str, Enum):
    """Tipos de neuronas en la red"""
    OBJECTIVE = "objective"      # Finalidad (S)
    METRIC = "metric"            # Métrica (M)
    SCOPE = "scope"              # Alcance (A)
    RELEVANCE = "relevance"      # Relevancia (R)
    TIME = "time"                # Tiempo (T)
    CONTEXT = "context"          # Contexto general
    DOMAIN = "domain"            # Especialización de dominio


class NetworkState(str, Enum):
    """Estado de la red neuronal"""
    INITIALIZING = "initializing"
    READY = "ready"
    TRAINING = "training"
    REASONING = "reasoning"
    ERROR = "error"


@dataclass
class NeuronConnection:
    """Conexión entre neuronas"""
    source_id: str
    target_id: str
    weight: float = 1.0
    connection_type: str = "excitatory"  # excitatory, inhibitory
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def activate(self, source_activation: float) -> float:
        """Calcula la activación transmitida"""
        if self.connection_type == "excitatory":
            return source_activation * self.weight
        else:
            return -source_activation * self.weight


@dataclass
class ObviousnessNeuron:
    """
    Neurona que representa un Trasfondo de Obviedad.
    
    Cada neurona encapsula una dimensión SMART del contexto
    y puede activarse en respuesta a inputs relacionados.
    """
    id: str
    name: str
    neuron_type: NeuronType
    description: str = ""
    
    # Estado
    activation: float = 0.0
    bias: float = 0.0
    threshold: float = 0.5
    
    # Conexiones
    incoming: List[str] = field(default_factory=list)
    outgoing: List[str] = field(default_factory=list)
    
    # Contenido
    content: Dict[str, Any] = field(default_factory=dict)
    keywords: Set[str] = field(default_factory=set)
    
    # Aprendizaje
    learning_rate: float = 0.1
    usage_count: int = 0
    success_rate: float = 1.0
    
    # Metadatos
    domain: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    def activate(self, input_signal: float) -> float:
        """
        Calcula la activación de la neurona.
        
        Usa función sigmoide para suavizar la respuesta.
        """
        # Sumar bias
        total_input = input_signal + self.bias
        
        # Función de activación sigmoide
        self.activation = 1 / (1 + math.exp(-total_input))
        
        # Incrementar uso
        self.usage_count += 1
        
        return self.activation
    
    def update_weights(
        self,
        reward: float,
        connections: Dict[str, 'ObviousnessNeuron']
    ) -> None:
        """
        Actualiza pesos basado en retroalimentación.
        
        Implementa regla de Hebb modificada.
        """
        for conn_id in self.outgoing:
            if conn_id in connections:
                target = connections[conn_id]
                # Regla de Hebb: neurons that fire together, wire together
                delta = self.learning_rate * self.activation * target.activation * reward
                # Actualizar tasa de éxito
                if reward > 0:
                    self.success_rate = self.success_rate * 0.9 + 0.1
                else:
                    self.success_rate = self.success_rate * 0.9
    
    def is_active(self) -> bool:
        """Verifica si la neurona está activa"""
        return self.activation >= self.threshold
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa la neurona"""
        return {
            "id": self.id,
            "name": self.name,
            "neuron_type": self.neuron_type.value,
            "description": self.description,
            "activation": self.activation,
            "bias": self.bias,
            "threshold": self.threshold,
            "incoming": self.incoming,
            "outgoing": self.outgoing,
            "content": self.content,
            "keywords": list(self.keywords),
            "learning_rate": self.learning_rate,
            "usage_count": self.usage_count,
            "success_rate": self.success_rate,
            "domain": self.domain
        }


class ObviousnessNetwork:
    """
    Red Neuronal de Obviedades (RNO).
    
    Implementa un modelo LOCM (Large Obviousness-Context Model)
    que razona sobre la arquitectura normativa del negocio.
    
    Usage:
        network = ObviousnessNetwork()
        
        # Añadir neuronas
        network.add_neuron(ObviousnessNeuron(
            id="obj-1",
            name="Analizar Ventas",
            neuron_type=NeuronType.OBJECTIVE
        ))
        
        # Conectar neuronas
        network.connect("obj-1", "metric-1", weight=0.8)
        
        # Activar y razonar
        result = network.reason(input_context)
    """
    
    def __init__(self, domain: Optional[str] = None):
        """
        Inicializa la red neuronal.
        
        Args:
            domain: Dominio específico (retail, health, industrial, etc.)
        """
        self.domain = domain
        self.state = NetworkState.INITIALIZING
        
        # Estructura de la red
        self._neurons: Dict[str, ObviousnessNeuron] = {}
        self._connections: Dict[str, NeuronConnection] = {}
        
        # Capas por tipo
        self._layers: Dict[NeuronType, List[str]] = {}
        for nt in NeuronType:
            self._layers[nt] = []
        
        # Estado de razonamiento
        self._activation_history: List[Dict[str, float]] = []
        
        # Inicializar con estructura base
        self._initialize_base_structure()
        
        self.state = NetworkState.READY
    
    def _initialize_base_structure(self) -> None:
        """Inicializa la estructura base de la red"""
        # Crear neuronas de las 5 dimensiones SMART
        base_neurons = [
            ("S_finality", "Finalidad", NeuronType.OBJECTIVE, "Objetivo técnico específico"),
            ("M_metric", "Métrica", NeuronType.METRIC, "Criterios cuantitativos de éxito"),
            ("A_scope", "Alcance", NeuronType.SCOPE, "Fronteras operativas"),
            ("R_relevance", "Relevancia", NeuronType.RELEVANCE, "Impacto organizacional"),
            ("T_time", "Tiempo", NeuronType.TIME, "Restricciones temporales"),
        ]
        
        for neuron_id, name, n_type, description in base_neurons:
            neuron = ObviousnessNeuron(
                id=neuron_id,
                name=name,
                neuron_type=n_type,
                description=description
            )
            self.add_neuron(neuron)
        
        # Conexiones base
        self.connect("S_finality", "M_metric", weight=0.7)
        self.connect("M_metric", "A_scope", weight=0.5)
        self.connect("A_scope", "R_relevance", weight=0.6)
        self.connect("R_relevance", "T_time", weight=0.4)
    
    def add_neuron(self, neuron: ObviousnessNeuron) -> None:
        """Añade una neurona a la red"""
        self._neurons[neuron.id] = neuron
        self._layers[neuron.neuron_type].append(neuron.id)
    
    def remove_neuron(self, neuron_id: str) -> bool:
        """Remueve una neurona de la red"""
        if neuron_id not in self._neurons:
            return False
        
        neuron = self._neurons[neuron_id]
        
        # Remover de capa
        self._layers[neuron.neuron_type].remove(neuron_id)
        
        # Remover conexiones
        for conn_id in list(self._connections.keys()):
            if neuron_id in conn_id:
                del self._connections[conn_id]
        
        del self._neurons[neuron_id]
        return True
    
    def connect(
        self,
        source_id: str,
        target_id: str,
        weight: float = 1.0,
        connection_type: str = "excitatory"
    ) -> bool:
        """Conecta dos neuronas"""
        if source_id not in self._neurons or target_id not in self._neurons:
            return False
        
        conn_id = f"{source_id}->{target_id}"
        
        self._connections[conn_id] = NeuronConnection(
            source_id=source_id,
            target_id=target_id,
            weight=weight,
            connection_type=connection_type
        )
        
        # Actualizar listas de conexiones
        self._neurons[source_id].outgoing.append(target_id)
        self._neurons[target_id].incoming.append(source_id)
        
        return True
    
    def disconnect(self, source_id: str, target_id: str) -> bool:
        """Desconecta dos neuronas"""
        conn_id = f"{source_id}->{target_id}"
        
        if conn_id not in self._connections:
            return False
        
        del self._connections[conn_id]
        
        self._neurons[source_id].outgoing.remove(target_id)
        self._neurons[target_id].incoming.remove(source_id)
        
        return True
    
    def reason(
        self,
        input_context: Dict[str, Any],
        max_iterations: int = 10
    ) -> Dict[str, Any]:
        """
        Ejecuta razonamiento sobre la red.
        
        Propaga activación a través de la red hasta convergencia
        o máximo de iteraciones.
        
        Args:
            input_context: Contexto de entrada
            max_iterations: Máximo de iteraciones de propagación
        
        Returns:
            Resultado del razonamiento con activaciones y recomendaciones
        """
        self.state = NetworkState.REASONING
        
        # Reset activaciones
        for neuron in self._neurons.values():
            neuron.activation = 0.0
        
        # Activar neuronas basado en input
        initial_activations = self._map_input_to_activations(input_context)
        
        for neuron_id, activation in initial_activations.items():
            if neuron_id in self._neurons:
                self._neurons[neuron_id].activate(activation)
        
        # Propagar activación
        for iteration in range(max_iterations):
            new_activations = self._propagate_activation()
            
            # Verificar convergencia
            if self._check_convergence(new_activations):
                break
            
            self._activation_history.append(new_activations)
        
        # Recolectar resultados
        result = self._collect_reasoning_result(input_context)
        
        self.state = NetworkState.READY
        
        return result
    
    def _map_input_to_activations(
        self,
        input_context: Dict[str, Any]
    ) -> Dict[str, float]:
        """Mapea el contexto de entrada a activaciones iniciales"""
        activations = {}
        
        # Mapear objetivo a neurona S
        if "objective" in input_context:
            activations["S_finality"] = 0.8
        
        # Mapear métricas a neurona M
        if "metrics" in input_context or "target_recall" in input_context:
            activations["M_metric"] = 0.7
        
        # Mapear alcance a neurona A
        if "boundaries" in input_context or "allowed_tools" in input_context:
            activations["A_scope"] = 0.6
        
        # Mapear relevancia a neurona R
        if "organizational_impact" in input_context or "cognitive_capital_value" in input_context:
            activations["R_relevance"] = 0.7
        
        # Mapear tiempo a neurona T
        if "timeout" in input_context or "deadline" in input_context:
            activations["T_time"] = 0.5
        
        return activations
    
    def _propagate_activation(self) -> Dict[str, float]:
        """Propaga activación a través de la red"""
        new_activations = {}
        
        for neuron_id, neuron in self._neurons.items():
            # Sumar activación de conexiones entrantes
            total_input = 0.0
            
            for source_id in neuron.incoming:
                conn_id = f"{source_id}->{neuron_id}"
                if conn_id in self._connections:
                    conn = self._connections[conn_id]
                    source = self._neurons.get(source_id)
                    if source:
                        total_input += conn.activate(source.activation)
            
            # Calcular nueva activación
            new_activation = neuron.activate(total_input)
            new_activations[neuron_id] = new_activation
        
        return new_activations
    
    def _check_convergence(
        self,
        new_activations: Dict[str, float]
    ) -> bool:
        """Verifica si la red ha convergido"""
        # Simplificado: convergencia si cambio < 0.01
        for neuron_id, new_act in new_activations.items():
            old_act = self._neurons[neuron_id].activation
            if abs(new_act - old_act) > 0.01:
                return False
        return True
    
    def _collect_reasoning_result(
        self,
        input_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Recolecta el resultado del razonamiento"""
        # Obtener neuronas más activas
        active_neurons = sorted(
            [(n.name, n.activation, n.neuron_type.value) for n in self._neurons.values()],
            key=lambda x: x[1],
            reverse=True
        )
        
        # Generar recomendaciones basadas en activación
        recommendations = []
        
        if self._neurons["S_finality"].is_active():
            recommendations.append({
                "type": "objective_alignment",
                "message": "El objetivo está bien alineado con el contexto",
                "confidence": self._neurons["S_finality"].activation
            })
        
        if self._neurons["M_metric"].is_active():
            recommendations.append({
                "type": "metric_validation",
                "message": "Verificar métricas de éxito",
                "confidence": self._neurons["M_metric"].activation
            })
        
        if self._neurons["A_scope"].is_active():
            recommendations.append({
                "type": "scope_boundary",
                "message": "Respetar límites de alcance definidos",
                "confidence": self._neurons["A_scope"].activation
            })
        
        return {
            "active_neurons": active_neurons[:5],
            "recommendations": recommendations,
            "overall_activation": sum(n.activation for n in self._neurons.values()) / len(self._neurons),
            "reasoning_depth": len(self._activation_history)
        }
    
    def train(
        self,
        training_data: List[Dict[str, Any]],
        epochs: int = 10
    ) -> Dict[str, Any]:
        """
        Entrena la red con ejemplos.
        
        Args:
            training_data: Lista de ejemplos de entrenamiento
            epochs: Número de épocas
        
        Returns:
            Métricas de entrenamiento
        """
        self.state = NetworkState.TRAINING
        
        metrics = {
            "epochs": epochs,
            "samples": len(training_data),
            "improvements": []
        }
        
        for epoch in range(epochs):
            epoch_improvement = 0
            
            for sample in training_data:
                # Razonar sobre el ejemplo
                result = self.reason(sample.get("input", {}))
                
                # Calcular recompensa basada en si la predicción fue correcta
                expected = sample.get("expected_output", {})
                reward = self._calculate_reward(result, expected)
                
                # Actualizar pesos
                for neuron in self._neurons.values():
                    neuron.update_weights(reward, self._neurons)
                
                epoch_improvement += reward
            
            avg_improvement = epoch_improvement / len(training_data) if training_data else 0
            metrics["improvements"].append(avg_improvement)
        
        self.state = NetworkState.READY
        
        return metrics
    
    def _calculate_reward(
        self,
        result: Dict[str, Any],
        expected: Dict[str, Any]
    ) -> float:
        """Calcula la recompensa basada en el resultado"""
        # Simplificado: recompensa basada en activación general
        return result.get("overall_activation", 0.5)
    
    def get_neuron(self, neuron_id: str) -> Optional[ObviousnessNeuron]:
        """Obtiene una neurona por ID"""
        return self._neurons.get(neuron_id)
    
    def get_layer(self, neuron_type: NeuronType) -> List[ObviousnessNeuron]:
        """Obtiene todas las neuronas de un tipo"""
        return [
            self._neurons[nid] for nid in self._layers[neuron_type]
            if nid in self._neurons
        ]
    
    def get_active_neurons(self) -> List[ObviousnessNeuron]:
        """Obtiene todas las neuronas activas"""
        return [n for n in self._neurons.values() if n.is_active()]
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa la red completa"""
        return {
            "domain": self.domain,
            "state": self.state.value,
            "neurons": {nid: n.to_dict() for nid, n in self._neurons.items()},
            "connections": {
                cid: {
                    "source": c.source_id,
                    "target": c.target_id,
                    "weight": c.weight,
                    "type": c.connection_type
                }
                for cid, c in self._connections.items()
            }
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la red"""
        return {
            "total_neurons": len(self._neurons),
            "total_connections": len(self._connections),
            "by_type": {
                nt.value: len(self._layers[nt])
                for nt in NeuronType
            },
            "avg_activation": sum(n.activation for n in self._neurons.values()) / len(self._neurons),
            "avg_usage": sum(n.usage_count for n in self._neurons.values()) / len(self._neurons)
        }
