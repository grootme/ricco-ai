"""
Tests para Red Neuronal de Obviedades (RNO)

Valida el modelo LOCM y la red neuronal de contexto.
"""

import pytest
from datetime import datetime

from src.rno.network import (
    ObviousnessNetwork,
    ObviousnessNeuron,
    NeuronType,
    NetworkState,
    NeuronConnection
)
from src.rno.locm import (
    LOCM,
    LOCMConfig,
    ReasoningResult
)


class TestObviousnessNeuron:
    """Tests para neurona de obviedad"""
    
    def test_neuron_creation(self):
        """Verifica creación de neurona"""
        neuron = ObviousnessNeuron(
            id="test-neuron",
            name="Test Neuron",
            neuron_type=NeuronType.OBJECTIVE,
            description="A test neuron"
        )
        
        assert neuron.id == "test-neuron"
        assert neuron.activation == 0.0
        assert neuron.threshold == 0.5
    
    def test_neuron_activation(self):
        """Verifica activación de neurona"""
        neuron = ObviousnessNeuron(
            id="activation-test",
            name="Activation Test",
            neuron_type=NeuronType.OBJECTIVE
        )
        
        activation = neuron.activate(1.0)
        
        assert activation > 0
        assert neuron.activation > 0
    
    def test_neuron_threshold(self):
        """Verifica umbral de activación"""
        neuron = ObviousnessNeuron(
            id="threshold-test",
            name="Threshold Test",
            neuron_type=NeuronType.OBJECTIVE,
            threshold=0.7
        )
        
        # Activación baja
        neuron.activate(0.1)
        assert not neuron.is_active()
        
        # Reset y activación alta
        neuron.activation = 0.0
        neuron.activate(2.0)
        assert neuron.is_active()
    
    def test_neuron_connections(self):
        """Verifica conexiones de neurona"""
        neuron = ObviousnessNeuron(
            id="conn-test",
            name="Connection Test",
            neuron_type=NeuronType.CONTEXT,
            incoming=["source1"],
            outgoing=["target1", "target2"]
        )
        
        assert len(neuron.incoming) == 1
        assert len(neuron.outgoing) == 2
    
    def test_neuron_learning(self):
        """Verifica aprendizaje de neurona"""
        neuron = ObviousnessNeuron(
            id="learn-test",
            name="Learning Test",
            neuron_type=NeuronType.OBJECTIVE,
            learning_rate=0.1
        )
        
        # Simular aprendizaje con recompensa positiva
        neuron.activate(1.0)
        initial_success_rate = neuron.success_rate
        
        neuron.update_weights(1.0, {})
        
        # La tasa de éxito debe aumentar
        assert neuron.success_rate >= initial_success_rate
    
    def test_neuron_serialization(self):
        """Verifica serialización de neurona"""
        neuron = ObviousnessNeuron(
            id="serial-test",
            name="Serialization Test",
            neuron_type=NeuronType.METRIC,
            content={"key": "value"}
        )
        
        data = neuron.to_dict()
        
        assert data["id"] == "serial-test"
        assert data["neuron_type"] == "metric"
        assert data["content"] == {"key": "value"}


class TestNeuronConnection:
    """Tests para conexiones entre neuronas"""
    
    def test_excitatory_connection(self):
        """Verifica conexión excitatoria"""
        conn = NeuronConnection(
            source_id="source",
            target_id="target",
            weight=0.8,
            connection_type="excitatory"
        )
        
        activation = conn.activate(1.0)
        
        assert activation == 0.8
    
    def test_inhibitory_connection(self):
        """Verifica conexión inhibitoria"""
        conn = NeuronConnection(
            source_id="source",
            target_id="target",
            weight=0.5,
            connection_type="inhibitory"
        )
        
        activation = conn.activate(1.0)
        
        assert activation == -0.5


class TestObviousnessNetwork:
    """Tests para Red Neuronal de Obviedades"""
    
    @pytest.fixture
    def network(self):
        return ObviousnessNetwork()
    
    def test_initialization(self, network):
        """Verifica inicialización de la red"""
        assert network.state == NetworkState.READY
        assert len(network._neurons) >= 5  # Al menos las 5 SMART
    
    def test_base_structure(self, network):
        """Verifica estructura base SMART"""
        neuron_types = set(n.neuron_type for n in network._neurons.values())
        
        assert NeuronType.OBJECTIVE in neuron_types
        assert NeuronType.METRIC in neuron_types
        assert NeuronType.SCOPE in neuron_types
        assert NeuronType.RELEVANCE in neuron_types
        assert NeuronType.TIME in neuron_types
    
    def test_add_neuron(self, network):
        """Verifica adición de neurona"""
        neuron = ObviousnessNeuron(
            id="added-neuron",
            name="Added Neuron",
            neuron_type=NeuronType.DOMAIN,
            domain="retail"
        )
        
        network.add_neuron(neuron)
        
        assert network.get_neuron("added-neuron") is not None
    
    def test_remove_neuron(self, network):
        """Verifica eliminación de neurona"""
        neuron = ObviousnessNeuron(
            id="to-remove",
            name="To Remove",
            neuron_type=NeuronType.CONTEXT
        )
        
        network.add_neuron(neuron)
        result = network.remove_neuron("to-remove")
        
        assert result is True
        assert network.get_neuron("to-remove") is None
    
    def test_connect_neurons(self, network):
        """Verifica conexión entre neuronas"""
        network.add_neuron(ObviousnessNeuron(
            id="conn-source",
            name="Source",
            neuron_type=NeuronType.OBJECTIVE
        ))
        
        network.add_neuron(ObviousnessNeuron(
            id="conn-target",
            name="Target",
            neuron_type=NeuronType.METRIC
        ))
        
        result = network.connect("conn-source", "conn-target", weight=0.7)
        
        assert result is True
        assert "conn-target" in network._neurons["conn-source"].outgoing
    
    def test_disconnect_neurons(self, network):
        """Verifica desconexión entre neuronas"""
        network.add_neuron(ObviousnessNeuron(
            id="disc-source",
            name="Source",
            neuron_type=NeuronType.OBJECTIVE
        ))
        
        network.add_neuron(ObviousnessNeuron(
            id="disc-target",
            name="Target",
            neuron_type=NeuronType.METRIC
        ))
        
        network.connect("disc-source", "disc-target")
        result = network.disconnect("disc-source", "disc-target")
        
        assert result is True
        assert "disc-target" not in network._neurons["disc-source"].outgoing
    
    def test_reasoning(self, network):
        """Verifica razonamiento"""
        result = network.reason({
            "objective": "Test reasoning",
            "metrics": {"recall": 0.8}
        })
        
        assert "active_neurons" in result
        assert "recommendations" in result
        assert "overall_activation" in result
    
    def test_get_layer(self, network):
        """Verifica obtención de capa"""
        objectives = network.get_layer(NeuronType.OBJECTIVE)
        
        assert len(objectives) > 0
        assert all(n.neuron_type == NeuronType.OBJECTIVE for n in objectives)
    
    def test_get_active_neurons(self, network):
        """Verifica obtención de neuronas activas"""
        # Activar la red
        network.reason({"objective": "Test activation"})
        
        active = network.get_active_neurons()
        
        assert isinstance(active, list)
    
    def test_network_stats(self, network):
        """Verifica estadísticas de la red"""
        stats = network.get_stats()
        
        assert "total_neurons" in stats
        assert "total_connections" in stats
        assert "by_type" in stats
    
    def test_network_serialization(self, network):
        """Verifica serialización de la red"""
        data = network.to_dict()
        
        assert "neurons" in data
        assert "connections" in data


class TestLOCM:
    """Tests para Large Obviousness-Context Model"""
    
    @pytest.fixture
    def locm(self):
        return LOCM(LOCMConfig(
            domain="retail",
            confidence_threshold=0.7
        ))
    
    def test_initialization(self, locm):
        """Verifica inicialización del modelo"""
        assert locm.config.domain == "retail"
        assert locm._network is not None
    
    def test_ingest_organization_context(self, locm):
        """Verifica ingesta de contexto organizacional"""
        locm.ingest_organization_context({
            "objectives": [
                {"name": "Increase Sales", "description": "Increase quarterly sales"}
            ],
            "constraints": [
                {"name": "Budget Limit", "description": "Stay within budget"}
            ],
            "policies": [
                {"name": "Data Privacy", "type": "privacy", "description": "Protect customer data"}
            ]
        })
        
        assert len(locm._policies) == 1
        stats = locm.get_network_stats()
        assert stats["total_neurons"] > 5  # Base + added
    
    def test_ingest_domain_knowledge(self, locm):
        """Verifica ingesta de conocimiento de dominio"""
        locm.ingest_domain_knowledge("retail", {
            "inventory": {"tracking": "real-time"},
            "pricing": {"strategy": "dynamic"}
        })
        
        assert "retail" in locm._domain_knowledge
    
    def test_reasoning(self, locm):
        """Verifica razonamiento"""
        locm.ingest_organization_context({
            "objectives": [{"name": "Test Objective", "description": "Test"}]
        })
        
        result = locm.reason("¿Cómo optimizar el inventario?")
        
        assert isinstance(result, ReasoningResult)
        assert result.query == "¿Cómo optimizar el inventario?"
        assert result.confidence >= 0
        assert len(result.reasoning_trace) > 0
    
    def test_reasoning_with_context(self, locm):
        """Verifica razonamiento con contexto adicional"""
        result = locm.reason(
            "Analizar tendencias de venta",
            context={"domain": "retail", "timeframe": "Q1"}
        )
        
        assert result.query == "Analizar tendencias de venta"
        assert len(result.relevant_context) >= 0
    
    def test_add_obviousness_context(self, locm):
        """Verifica adición de contexto de obviedad"""
        locm.add_obviousness_context({
            "session_id": "test-session",
            "objective": "Test objective",
            "metrics": {"recall": 0.8}
        })
        
        stats = locm.get_network_stats()
        # Debe haber más neuronas que las base
        assert stats["total_neurons"] > 5
    
    def test_model_stats(self, locm):
        """Verifica estadísticas del modelo"""
        stats = locm.get_model_stats()
        
        assert stats["domain"] == "retail"
        assert "query_count" in stats
        assert "success_rate" in stats


class TestLOCMTraining:
    """Tests para entrenamiento del LOCM"""
    
    @pytest.fixture
    def locm(self):
        return LOCM(LOCMConfig(enable_learning=True))
    
    def test_training_basic(self, locm):
        """Verifica entrenamiento básico"""
        training_data = [
            {
                "input": {"objective": "Optimize sales"},
                "expected_output": {"focus": "revenue"}
            },
            {
                "input": {"objective": "Reduce costs"},
                "expected_output": {"focus": "efficiency"}
            }
        ]
        
        metrics = locm._network.train(training_data, epochs=2)
        
        assert "epochs" in metrics
        assert metrics["epochs"] == 2
        assert len(metrics["improvements"]) == 2
    
    def test_multiple_reasoning_sessions(self, locm):
        """Verifica múltiples sesiones de razonamiento"""
        queries = [
            "Analizar ventas Q1",
            "Optimizar inventario",
            "Mejorar atención al cliente"
        ]
        
        for query in queries:
            result = locm.reason(query)
            assert result.confidence >= 0
        
        stats = locm.get_model_stats()
        assert stats["query_count"] == 3


class TestRNOIntegration:
    """Tests de integración para RNO"""
    
    def test_full_reasoning_pipeline(self):
        """Verifica pipeline completo de razonamiento"""
        locm = LOCM(LOCMConfig(domain="finance"))
        
        # Ingestar contexto organizacional
        locm.ingest_organization_context({
            "objectives": [
                {"name": "Risk Management", "description": "Minimize financial risk"}
            ],
            "policies": [
                {"name": "Compliance", "type": "regulatory", "description": "Follow regulations"}
            ]
        })
        
        # Ingestar conocimiento de dominio
        locm.ingest_domain_knowledge("finance", {
            "risk": {"model": "VaR", "threshold": 0.05},
            "portfolio": {"strategy": "diversified"}
        })
        
        # Añadir contexto de obviedad
        locm.add_obviousness_context({
            "session_id": "finance-session",
            "objective": "Optimize portfolio risk",
            "metrics": {"var_limit": 0.03}
        })
        
        # Razonar
        result = locm.reason(
            "¿Cómo reducir la exposición al riesgo del portafolio?"
        )
        
        assert result.confidence > 0
        assert len(result.recommendations) >= 0
    
    def test_network_persistence(self):
        """Verifica persistencia de la red"""
        network1 = ObviousnessNetwork()
        
        # Añadir neuronas
        network1.add_neuron(ObviousnessNeuron(
            id="persist-test",
            name="Persist Test",
            neuron_type=NeuronType.DOMAIN
        ))
        
        # Serializar
        data = network1.to_dict()
        
        # Crear nueva red y cargar
        network2 = ObviousnessNetwork()
        for nid, ndata in data["neurons"].items():
            if nid not in network2._neurons:
                network2.add_neuron(ObviousnessNeuron(
                    id=ndata["id"],
                    name=ndata["name"],
                    neuron_type=NeuronType(ndata["neuron_type"])
                ))
        
        assert network2.get_neuron("persist-test") is not None
