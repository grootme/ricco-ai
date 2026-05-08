"""
LOCM - Large Obviousness-Context Model

Modelo de lenguaje especializado que no razona sobre palabras
generales, sino sobre la arquitectura normativa del negocio real.
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
import logging

from .network import ObviousnessNetwork, NeuronType

logger = logging.getLogger(__name__)


@dataclass
class LOCMConfig:
    """Configuración del modelo LOCM"""
    domain: str = "general"
    version: str = "1.0.0"
    max_context_tokens: int = 8000
    reasoning_depth: int = 5
    confidence_threshold: float = 0.7
    enable_learning: bool = True
    learning_rate: float = 0.1


@dataclass
class ReasoningResult:
    """Resultado de razonamiento del LOCM"""
    query: str
    understanding: str
    relevant_context: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    confidence: float
    reasoning_trace: List[str] = field(default_factory=list)
    neurons_activated: List[str] = field(default_factory=list)
    processing_time_ms: int = 0


class LOCM:
    """
    Large Obviousness-Context Model.
    
    Modelo especializado para razonar sobre el contexto de negocio
    y los Trasfondos de Obviedad de una organización.
    
    A diferencia de un LLM general que razona sobre texto,
    LOCM razona sobre la estructura normativa del negocio.
    
    Usage:
        locm = LOCM(LOCMConfig(domain="retail"))
        
        # Entrenar con contexto organizacional
        locm.ingest_organization_context(org_data)
        
        # Razonar sobre una consulta
        result = locm.reason("¿Cómo optimizar el inventario?")
    """
    
    def __init__(self, config: LOCMConfig):
        """
        Inicializa el modelo LOCM.
        
        Args:
            config: Configuración del modelo
        """
        self.config = config
        self._network = ObviousnessNetwork(domain=config.domain)
        
        # Base de conocimiento organizacional
        self._org_context: Dict[str, Any] = {}
        self._policies: List[Dict[str, Any]] = []
        self._domain_knowledge: Dict[str, Any] = {}
        
        # Estadísticas
        self._query_count = 0
        self._successful_queries = 0
    
    def ingest_organization_context(
        self,
        context: Dict[str, Any]
    ) -> None:
        """
        Ingiere contexto organizacional.
        
        Este contexto define la "arquitectura normativa" sobre la
        cual el modelo razonará.
        
        Args:
            context: Contexto organizacional con:
                - policies: Políticas de la organización
                - objectives: Objetivos estratégicos
                - constraints: Restricciones operativas
                - knowledge_base: Base de conocimiento
        """
        self._org_context = context
        
        # Extraer políticas
        policies = context.get("policies", [])
        self._policies.extend(policies)
        
        # Crear neuronas para cada objetivo
        objectives = context.get("objectives", [])
        for i, obj in enumerate(objectives):
            from .network import ObviousnessNeuron
            neuron = ObviousnessNeuron(
                id=f"obj_{i}",
                name=obj.get("name", f"Objective {i}"),
                neuron_type=NeuronType.OBJECTIVE,
                description=obj.get("description", ""),
                content=obj
            )
            self._network.add_neuron(neuron)
        
        # Crear neuronas para restricciones
        constraints = context.get("constraints", [])
        for i, constraint in enumerate(constraints):
            from .network import ObviousnessNeuron
            neuron = ObviousnessNeuron(
                id=f"const_{i}",
                name=constraint.get("name", f"Constraint {i}"),
                neuron_type=NeuronType.SCOPE,
                description=constraint.get("description", ""),
                content=constraint
            )
            self._network.add_neuron(neuron)
    
    def ingest_domain_knowledge(
        self,
        domain: str,
        knowledge: Dict[str, Any]
    ) -> None:
        """
        Ingiere conocimiento específico de dominio.
        
        Args:
            domain: Dominio (retail, health, industrial, etc.)
            knowledge: Conocimiento específico del dominio
        """
        self._domain_knowledge[domain] = knowledge
        
        # Crear neuronas de dominio
        from .network import ObviousnessNeuron
        
        for key, value in knowledge.items():
            if isinstance(value, dict):
                neuron = ObviousnessNeuron(
                    id=f"domain_{domain}_{key}",
                    name=f"{domain}:{key}",
                    neuron_type=NeuronType.DOMAIN,
                    domain=domain,
                    content=value
                )
                self._network.add_neuron(neuron)
    
    def reason(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ReasoningResult:
        """
        Razona sobre una consulta usando la RNO.
        
        Args:
            query: Consulta del usuario
            context: Contexto adicional
        
        Returns:
            ReasoningResult con el razonamiento
        """
        start_time = datetime.utcnow()
        self._query_count += 1
        
        context = context or {}
        
        # Combinar contexto de entrada con contexto organizacional
        combined_context = {
            **self._org_context,
            **context,
            "query": query
        }
        
        # Ejecutar razonamiento en la red
        network_result = self._network.reason(combined_context)
        
        # Construir entendimiento
        understanding = self._build_understanding(query, network_result)
        
        # Identificar contexto relevante
        relevant_context = self._identify_relevant_context(query, network_result)
        
        # Generar recomendaciones
        recommendations = self._generate_recommendations(
            query,
            network_result,
            relevant_context
        )
        
        # Calcular confianza
        confidence = network_result.get("overall_activation", 0.5)
        
        # Construir traza de razonamiento
        reasoning_trace = self._build_reasoning_trace(network_result)
        
        # Neuronas activadas
        neurons_activated = [
            n[0] for n in network_result.get("active_neurons", [])
        ]
        
        processing_time = int(
            (datetime.utcnow() - start_time).total_seconds() * 1000
        )
        
        # Actualizar estadísticas
        if confidence >= self.config.confidence_threshold:
            self._successful_queries += 1
        
        return ReasoningResult(
            query=query,
            understanding=understanding,
            relevant_context=relevant_context,
            recommendations=recommendations,
            confidence=confidence,
            reasoning_trace=reasoning_trace,
            neurons_activated=neurons_activated,
            processing_time_ms=processing_time
        )
    
    def _build_understanding(
        self,
        query: str,
        network_result: Dict[str, Any]
    ) -> str:
        """Construye el entendimiento de la consulta"""
        active_neurons = network_result.get("active_neurons", [])
        
        if not active_neurons:
            return f"No se pudo determinar un contexto específico para: {query}"
        
        top_neuron = active_neurons[0]
        
        understanding = f"La consulta '{query}' se relaciona principalmente con "
        understanding += f"{top_neuron[0]} (activación: {top_neuron[1]:.2f}). "
        
        if len(active_neurons) > 1:
            understanding += f"También tiene conexión con: {', '.join(n[0] for n in active_neurons[1:3])}."
        
        return understanding
    
    def _identify_relevant_context(
        self,
        query: str,
        network_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identifica contexto relevante de la organización"""
        relevant = []
        
        active_types = set()
        for neuron_name, activation, n_type in network_result.get("active_neurons", []):
            if activation >= self.config.confidence_threshold:
                active_types.add(n_type)
        
        # Agregar políticas relevantes
        for policy in self._policies:
            policy_type = policy.get("type", "")
            if any(t in policy_type for t in active_types):
                relevant.append({
                    "type": "policy",
                    "name": policy.get("name"),
                    "description": policy.get("description"),
                    "relevance": "high" if policy.get("type") in active_types else "medium"
                })
        
        # Agregar conocimiento de dominio
        for domain, domain_knowledge in self._domain_knowledge.items():
            for key, value in domain_knowledge.items():
                # Buscar match en query o en valores
                if query.lower() in str(value).lower() or key.lower() in query.lower():
                    relevant.append({
                        "type": "domain_knowledge",
                        "domain": domain,
                        "key": key,
                        "value": str(value)[:100],
                        "relevance": "medium"
                    })
        
        # Si no hay contexto específico, agregar las neuronas activas como contexto
        if not relevant and network_result.get("active_neurons"):
            for neuron_name, activation, n_type in network_result.get("active_neurons", [])[:3]:
                relevant.append({
                    "type": "activated_neuron",
                    "name": neuron_name,
                    "neuron_type": n_type,
                    "activation": activation,
                    "relevance": "high" if activation > 0.7 else "medium"
                })
        
        return relevant[:5]  # Limitar a 5 items
    
    def _generate_recommendations(
        self,
        query: str,
        network_result: Dict[str, Any],
        relevant_context: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Genera recomendaciones basadas en el razonamiento"""
        recommendations = []
        
        # Recomendaciones de la red
        for rec in network_result.get("recommendations", []):
            recommendations.append({
                "source": "network",
                "type": rec.get("type"),
                "message": rec.get("message"),
                "confidence": rec.get("confidence", 0.5)
            })
        
        # Recomendaciones de políticas
        for ctx in relevant_context:
            if ctx.get("type") == "policy":
                recommendations.append({
                    "source": "policy",
                    "policy": ctx.get("name"),
                    "message": f"Considerar política: {ctx.get('description', '')}",
                    "confidence": 0.8
                })
        
        return recommendations
    
    def _build_reasoning_trace(
        self,
        network_result: Dict[str, Any]
    ) -> List[str]:
        """Construye la traza de razonamiento"""
        trace = []
        
        trace.append(f"Red activada con {len(network_result.get('active_neurons', []))} neuronas relevantes")
        
        for neuron_name, activation, n_type in network_result.get("active_neurons", [])[:3]:
            trace.append(f"  - {neuron_name} ({n_type}): activación {activation:.2f}")
        
        trace.append(f"Profundidad de razonamiento: {network_result.get('reasoning_depth', 0)} iteraciones")
        
        return trace
    
    def add_obviousness_context(
        self,
        obviousness: Dict[str, Any]
    ) -> None:
        """
        Añade un Trasfondo de Obviedad específico.
        
        Args:
            obviousness: Contexto SMART+R+T completo
        """
        from .network import ObviousnessNeuron
        
        # Crear neuronas para cada dimensión
        if "objective" in obviousness:
            neuron = ObviousnessNeuron(
                id=f"obj_{obviousness.get('session_id', 'unknown')}",
                name=obviousness["objective"][:50],
                neuron_type=NeuronType.OBJECTIVE,
                content=obviousness
            )
            self._network.add_neuron(neuron)
        
        if "metrics" in obviousness:
            neuron = ObviousnessNeuron(
                id=f"metric_{obviousness.get('session_id', 'unknown')}",
                name=f"Metrics for {obviousness.get('objective', 'unknown')[:30]}",
                neuron_type=NeuronType.METRIC,
                content=obviousness.get("metrics", {})
            )
            self._network.add_neuron(neuron)
    
    def get_network_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la red neuronal"""
        return self._network.get_stats()
    
    def get_model_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del modelo"""
        return {
            "domain": self.config.domain,
            "version": self.config.version,
            "query_count": self._query_count,
            "successful_queries": self._successful_queries,
            "success_rate": self._successful_queries / self._query_count if self._query_count > 0 else 0,
            "policies_loaded": len(self._policies),
            "domains_loaded": list(self._domain_knowledge.keys())
        }
