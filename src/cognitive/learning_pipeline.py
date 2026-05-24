"""
NEXUS Learning Pipeline - Pipeline de Aprendizaje Continuo

## ¿Qué es el Learning Pipeline?

El sistema que permite la auto-mejora continua y la coordinación superior
entre agentes. Es el componente que hace que la organización "aprenda".

## Componentes

1. LearningEventProducer: Genera eventos de aprendizaje
2. LearningEventConsumer: Consume y procesa eventos
3. ReinforcementEngine: Motor de refuerzo (premia éxitos, ajusta errores)
4. CoordinationEngine: Coordina aprendizaje entre agentes
5. ReflectionEngine: Motor de reflexión y auto-análisis

## Flujo de Aprendizaje

1. EVENT: Se produce un evento (interacción, observación, etc.)
2. PROCESS: Se procesa el evento y extrae aprendizaje
3. REINFORCE: Se refuerza lo positivo, se corrige lo negativo
4. COORDINATE: Se comparte el aprendizaje con otros agentes
5. REFLECT: Se reflexiona sobre el aprendizaje acumulado

@author: NEXUS - Neural Execution Unified System
"""

from typing import Dict, List, Optional, Any, Callable, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4
import asyncio
import json
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


# ============================================================================
# LEARNING EVENT TYPES
# ============================================================================

class LearningEventType(str, Enum):
    """Tipos de eventos de aprendizaje"""
    # Input events
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    INTERACTION = "interaction"
    FEEDBACK_RECEIVED = "feedback_received"
    
    # Processing events
    OBSERVATION = "observation"
    PATTERN_DETECTED = "pattern_detected"
    ERROR_OCCURRED = "error_occurred"
    SUCCESS_ACHIEVED = "success_achieved"
    
    # Learning events
    KNOWLEDGE_GAINED = "knowledge_gained"
    SKILL_IMPROVED = "skill_improved"
    INSIGHT_GENERATED = "insight_generated"
    MISTAKE_LEARNED = "mistake_learned"
    
    # Coordination events
    SYNC_REQUESTED = "sync_requested"
    SYNC_COMPLETED = "sync_completed"
    PEER_LEARNING = "peer_learning"
    COLLECTIVE_INSIGHT = "collective_insight"
    
    # Reflection events
    REFLECTION_STARTED = "reflection_started"
    REFLECTION_COMPLETED = "reflection_completed"
    SELF_IMPROVEMENT = "self_improvement"


class LearningPriority(str, Enum):
    """Prioridad de eventos de aprendizaje"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================================
# LEARNING EVENT
# ============================================================================

@dataclass
class LearningEvent:
    """
    Evento de aprendizaje
    
    Unidad fundamental del pipeline de aprendizaje.
    Cada evento es una oportunidad de mejora.
    """
    id: UUID = field(default_factory=uuid4)
    event_type: LearningEventType = LearningEventType.OBSERVATION
    priority: LearningPriority = LearningPriority.NORMAL
    
    # Source
    source_agent_id: str = ""
    source_domain: str = "general"
    
    # Content
    payload: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    
    # Learning potential
    learning_value: float = 0.5
    processing_required: bool = True
    
    # Routing
    target_agents: List[str] = field(default_factory=list)
    broadcast: bool = False
    
    # Status
    processed: bool = False
    processing_result: Optional[Dict[str, Any]] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    
    def mark_processed(self, result: Dict[str, Any] = None) -> None:
        """Marca el evento como procesado"""
        self.processed = True
        self.processing_result = result
        self.processed_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "event_type": self.event_type.value,
            "priority": self.priority.value,
            "source_agent_id": self.source_agent_id,
            "source_domain": self.source_domain,
            "payload": self.payload,
            "context": self.context,
            "learning_value": self.learning_value,
            "processing_required": self.processing_required,
            "target_agents": self.target_agents,
            "broadcast": self.broadcast,
            "processed": self.processed,
            "processing_result": self.processing_result,
            "created_at": self.created_at.isoformat(),
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
        }


# ============================================================================
# REINFORCEMENT ENGINE
# ============================================================================

class ReinforcementEngine:
    """
    Motor de Refuerzo
    
    Implementa el aprendizaje reforzado:
    - Premia comportamientos exitosos
    - Ajusta comportamientos incorrectos
    - Mantiene balance exploración/explotación
    
    Basado en el concepto de "Entrenamiento reforzado sobre la realidad"
    de la Promptología Ontológica.
    """
    
    def __init__(self, learning_rate: float = 0.1, discount_factor: float = 0.9):
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        
        # Q-values para estados-acciones (simplificado)
        self.q_values: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        
        # Historial de recompensas
        self.reward_history: List[Dict[str, Any]] = []
        
        # Métricas
        self.total_reinforcements = 0
        self.positive_reinforcements = 0
        self.negative_adjustments = 0
    
    def compute_reward(
        self,
        event: LearningEvent,
        outcome: str,
        context: Dict[str, Any] = None
    ) -> float:
        """
        Computa la recompensa para un evento
        """
        base_reward = 0.0
        
        # Recompensa por tipo de evento
        if event.event_type == LearningEventType.TASK_COMPLETED:
            base_reward = 1.0
        elif event.event_type == LearningEventType.SUCCESS_ACHIEVED:
            base_reward = 0.8
        elif event.event_type == LearningEventType.TASK_FAILED:
            base_reward = -0.5
        elif event.event_type == LearningEventType.ERROR_OCCURRED:
            base_reward = -0.3
        elif event.event_type == LearningEventType.MISTAKE_LEARNED:
            base_reward = 0.3  # Aprender de errores tiene valor
        elif event.event_type == LearningEventType.INSIGHT_GENERATED:
            base_reward = 0.6
        elif event.event_type == LearningEventType.KNOWLEDGE_GAINED:
            base_reward = 0.4
        
        # Modificar por valor de aprendizaje
        reward = base_reward * event.learning_value
        
        # Registrar
        self.reward_history.append({
            "event_id": str(event.id),
            "event_type": event.event_type.value,
            "reward": reward,
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        return reward
    
    def update_q_value(
        self,
        state: str,
        action: str,
        reward: float,
        next_state: str = None
    ) -> float:
        """
        Actualiza Q-value usando Q-learning
        
        Q(s,a) = Q(s,a) + α * (r + γ * max(Q(s',a')) - Q(s,a))
        """
        current_q = self.q_values[state][action]
        
        # Max Q para siguiente estado
        max_next_q = 0.0
        if next_state and next_state in self.q_values:
            max_next_q = max(self.q_values[next_state].values()) if self.q_values[next_state] else 0.0
        
        # Actualización Q-learning
        new_q = current_q + self.learning_rate * (reward + self.discount_factor * max_next_q - current_q)
        self.q_values[state][action] = new_q
        
        # Métricas
        self.total_reinforcements += 1
        if reward > 0:
            self.positive_reinforcements += 1
        elif reward < 0:
            self.negative_adjustments += 1
        
        return new_q
    
    def get_best_action(self, state: str) -> Optional[Tuple[str, float]]:
        """Obtiene la mejor acción para un estado"""
        if state not in self.q_values:
            return None
        
        actions = self.q_values[state]
        if not actions:
            return None
        
        best_action = max(actions.items(), key=lambda x: x[1])
        return best_action
    
    def get_exploration_action(
        self,
        state: str,
        possible_actions: List[str],
        exploration_rate: float = 0.1
    ) -> str:
        """
        Obtiene acción con balance exploración/explotación
        """
        import random
        
        # Exploración aleatoria
        if random.random() < exploration_rate:
            return random.choice(possible_actions)
        
        # Explotación del mejor conocido
        best = self.get_best_action(state)
        if best and best[0] in possible_actions:
            return best[0]
        
        # Fallback aleatorio
        return random.choice(possible_actions)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas del motor de refuerzo"""
        return {
            "total_reinforcements": self.total_reinforcements,
            "positive_reinforcements": self.positive_reinforcements,
            "negative_adjustments": self.negative_adjustments,
            "positive_ratio": self.positive_reinforcements / max(1, self.total_reinforcements),
            "total_states": len(self.q_values),
            "total_state_action_pairs": sum(len(actions) for actions in self.q_values.values()),
            "recent_rewards": self.reward_history[-10:],
        }


# ============================================================================
# COORDINATION ENGINE
# ============================================================================

class CoordinationEngine:
    """
    Motor de Coordinación
    
    Coordina el aprendizaje entre múltiples agentes.
    Implementa la "red de contextos de obviedad" que permite
    la inteligencia organizacional viva.
    
    Según la tesis: "El futuro de la IA aplicada a organizaciones 
    no está en modelos que 'predicen mejor', sino en redes que 
    'coordinan mejor'."
    """
    
    def __init__(self):
        # Registro de agentes
        self.registered_agents: Dict[str, Dict[str, Any]] = {}
        
        # Capital compartido por dominio
        self.domain_capital: Dict[str, Dict[str, Any]] = defaultdict(dict)
        
        # Grafo de coordinación
        self.coordination_graph: Dict[str, Set[str]] = defaultdict(set)
        
        # Cola de eventos pendientes
        self.pending_events: List[LearningEvent] = []
        
        # Métricas
        self.coordination_events = 0
        self.successful_coordination = 0
    
    def register_agent(
        self,
        agent_id: str,
        domain: str,
        capabilities: List[str] = None
    ) -> None:
        """Registra un agente en la red de coordinación"""
        self.registered_agents[agent_id] = {
            "agent_id": agent_id,
            "domain": domain,
            "capabilities": capabilities or [],
            "registered_at": datetime.utcnow().isoformat(),
            "coordination_count": 0,
        }
        
        # Añadir al grafo por dominio
        for other_agent in self.registered_agents.values():
            if other_agent["agent_id"] != agent_id and other_agent["domain"] == domain:
                self.coordination_graph[agent_id].add(other_agent["agent_id"])
                self.coordination_graph[other_agent["agent_id"]].add(agent_id)
    
    async def coordinate_learning(
        self,
        event: LearningEvent,
        learning_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Coordina el aprendizaje entre agentes
        """
        self.coordination_events += 1
        
        coordination_result = {
            "event_id": str(event.id),
            "source_agent": event.source_agent_id,
            "coordination_type": "broadcast" if event.broadcast else "targeted",
            "target_agents": [],
            "shared_learning": {},
            "sync_status": {},
        }
        
        # Determinar objetivos
        if event.broadcast:
            # Broadcast a todos los del dominio
            targets = [
                aid for aid, info in self.registered_agents.items()
                if info["domain"] == event.source_domain and aid != event.source_agent_id
            ]
        else:
            targets = event.target_agents
        
        # Compartir aprendizaje
        for target_id in targets:
            if target_id in self.registered_agents:
                # Simular compartición (en producción usaría Redis/event bus)
                sync_status = await self._sync_to_agent(
                    target_id,
                    event.source_domain,
                    learning_result
                )
                coordination_result["target_agents"].append(target_id)
                coordination_result["sync_status"][target_id] = sync_status
        
        # Actualizar dominio capital
        domain = event.source_domain
        self._update_domain_capital(domain, learning_result)
        coordination_result["shared_learning"] = self.domain_capital[domain]
        
        if coordination_result["target_agents"]:
            self.successful_coordination += 1
        
        return coordination_result
    
    async def _sync_to_agent(
        self,
        target_agent_id: str,
        domain: str,
        learning: Dict[str, Any]
    ) -> str:
        """Sincroniza aprendizaje a un agente objetivo"""
        # En producción, esto usaría Redis pub/sub o similar
        return "synced"
    
    def _update_domain_capital(
        self,
        domain: str,
        learning: Dict[str, Any]
    ) -> None:
        """Actualiza el capital compartido del dominio"""
        if "patterns" in learning:
            if "patterns" not in self.domain_capital[domain]:
                self.domain_capital[domain]["patterns"] = []
            self.domain_capital[domain]["patterns"].extend(learning["patterns"])
        
        if "skills" in learning:
            if "skills" not in self.domain_capital[domain]:
                self.domain_capital[domain]["skills"] = {}
            self.domain_capital[domain]["skills"].update(learning["skills"])
        
        if "insights" in learning:
            if "insights" not in self.domain_capital[domain]:
                self.domain_capital[domain]["insights"] = []
            self.domain_capital[domain]["insights"].extend(learning["insights"])
    
    def get_peers_for_agent(self, agent_id: str) -> List[str]:
        """Obtiene agentes coordinados con uno dado"""
        return list(self.coordination_graph.get(agent_id, set()))
    
    def get_domain_capital(self, domain: str) -> Dict[str, Any]:
        """Obtiene el capital compartido de un dominio"""
        return self.domain_capital.get(domain, {})
    
    def get_coordination_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas de coordinación"""
        return {
            "registered_agents": len(self.registered_agents),
            "coordination_events": self.coordination_events,
            "successful_coordination": self.successful_coordination,
            "success_rate": self.successful_coordination / max(1, self.coordination_events),
            "domains": list(set(a["domain"] for a in self.registered_agents.values())),
            "coordination_graph_size": sum(len(peers) for peers in self.coordination_graph.values()),
        }


# ============================================================================
# REFLECTION ENGINE
# ============================================================================

class ReflectionEngine:
    """
    Motor de Reflexión
    
    Permite la auto-análisis y reflexión del agente.
    Según PPCC: "La reflexión es el mecanismo mediante el cual
    el agente analiza su propio comportamiento y capital."
    
    Tipos de reflexión:
    1. PERFORMANCE: Analiza rendimiento reciente
    2. STRATEGY: Evalúa estrategias usadas
    3. LEARNING: Evalúa progreso de aprendizaje
    4. COORDINATION: Evalúa coordinación con otros
    5. SELF_IMPROVEMENT: Genera plan de mejora
    """
    
    def __init__(self):
        self.reflection_history: List[Dict[str, Any]] = []
        self.improvement_plans: List[Dict[str, Any]] = []
    
    async def reflect(
        self,
        agent_id: str,
        capital_report: Dict[str, Any],
        coordination_metrics: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Realiza una reflexión completa del agente
        """
        reflection = {
            "agent_id": agent_id,
            "timestamp": datetime.utcnow().isoformat(),
            "reflection_types": [],
            "findings": [],
            "recommendations": [],
            "improvement_plan": None,
        }
        
        # Reflexión de rendimiento
        perf_reflection = self._reflect_performance(capital_report)
        if perf_reflection:
            reflection["reflection_types"].append("performance")
            reflection["findings"].extend(perf_reflection["findings"])
            reflection["recommendations"].extend(perf_reflection["recommendations"])
        
        # Reflexión de aprendizaje
        learn_reflection = self._reflect_learning(capital_report)
        if learn_reflection:
            reflection["reflection_types"].append("learning")
            reflection["findings"].extend(learn_reflection["findings"])
            reflection["recommendations"].extend(learn_reflection["recommendations"])
        
        # Reflexión de coordinación
        if coordination_metrics:
            coord_reflection = self._reflect_coordination(coordination_metrics)
            if coord_reflection:
                reflection["reflection_types"].append("coordination")
                reflection["findings"].extend(coord_reflection["findings"])
                reflection["recommendations"].extend(coord_reflection["recommendations"])
        
        # Generar plan de mejora
        improvement_plan = self._generate_improvement_plan(reflection)
        reflection["improvement_plan"] = improvement_plan
        
        # Guardar en historial
        self.reflection_history.append(reflection)
        if improvement_plan:
            self.improvement_plans.append(improvement_plan)
        
        return reflection
    
    def _reflect_performance(self, capital_report: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Reflexión sobre rendimiento"""
        findings = []
        recommendations = []
        
        metrics = capital_report.get("metrics", {})
        experiences = capital_report.get("experiences", {})
        
        # Analizar éxito
        total = experiences.get("total", 0)
        successful = experiences.get("successful", 0)
        
        if total > 0:
            success_rate = successful / total
            if success_rate >= 0.8:
                findings.append("High success rate maintained")
            elif success_rate >= 0.5:
                findings.append("Moderate success rate - room for improvement")
                recommendations.append("Focus on reducing errors in common failure scenarios")
            else:
                findings.append("Low success rate - significant improvement needed")
                recommendations.append("Review and reinforce core skills")
        
        # Analizar capital
        capital_value = metrics.get("capital_value", 0)
        if capital_value > 1000:
            findings.append("Strong cognitive capital accumulated")
        elif capital_value > 500:
            findings.append("Moderate cognitive capital - continue learning")
        else:
            findings.append("Low cognitive capital - increase engagement")
            recommendations.append("Process more experiences to build capital")
        
        return {"findings": findings, "recommendations": recommendations}
    
    def _reflect_learning(self, capital_report: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Reflexión sobre aprendizaje"""
        findings = []
        recommendations = []
        
        skills = capital_report.get("skills", {})
        by_level = skills.get("by_level", {})
        
        # Analizar distribución de skills
        expert = by_level.get("expert", 0)
        advanced = by_level.get("advanced", 0)
        
        if expert > 0:
            findings.append(f"{expert} skills at expert level")
        
        beginner = by_level.get("beginner", 0)
        if beginner > 3:
            recommendations.append("Focus on improving beginner-level skills")
        
        # Analizar insights
        insights = capital_report.get("insights", {})
        total_insights = insights.get("total", 0)
        
        if total_insights > 10:
            findings.append("Rich insight generation")
        elif total_insights > 5:
            findings.append("Moderate insight generation")
        else:
            recommendations.append("Increase reflection frequency for more insights")
        
        return {"findings": findings, "recommendations": recommendations}
    
    def _reflect_coordination(self, metrics: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Reflexión sobre coordinación"""
        findings = []
        recommendations = []
        
        success_rate = metrics.get("success_rate", 0)
        if success_rate >= 0.8:
            findings.append("Effective coordination with peers")
        elif success_rate >= 0.5:
            recommendations.append("Improve coordination reliability")
        else:
            recommendations.append("Review coordination protocols")
        
        graph_size = metrics.get("coordination_graph_size", 0)
        if graph_size > 5:
            findings.append("Well-connected in coordination network")
        
        return {"findings": findings, "recommendations": recommendations}
    
    def _generate_improvement_plan(self, reflection: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Genera plan de mejora basado en la reflexión"""
        recommendations = reflection.get("recommendations", [])
        
        if not recommendations:
            return None
        
        plan = {
            "plan_id": str(uuid4()),
            "generated_at": datetime.utcnow().isoformat(),
            "based_on_reflection": reflection.get("timestamp"),
            "actions": [],
            "priority": "normal",
        }
        
        # Convertir recomendaciones en acciones
        for i, rec in enumerate(recommendations[:5]):  # Max 5 acciones
            action = {
                "action_id": i + 1,
                "description": rec,
                "status": "pending",
                "estimated_impact": "medium",
            }
            plan["actions"].append(action)
        
        # Determinar prioridad
        if len(recommendations) > 3:
            plan["priority"] = "high"
        
        return plan
    
    def get_recent_reflections(self, n: int = 5) -> List[Dict[str, Any]]:
        """Obtiene las n reflexiones más recientes"""
        return self.reflection_history[-n:]
    
    def get_active_improvement_plans(self) -> List[Dict[str, Any]]:
        """Obtiene planes de mejora activos"""
        return [p for p in self.improvement_plans if any(a["status"] == "pending" for a in p.get("actions", []))]


# ============================================================================
# LEARNING PIPELINE COMPLETO
# ============================================================================

class LearningPipeline:
    """
    Pipeline de Aprendizaje Continuo Completo
    
    Integra todos los componentes para crear un sistema de
    aprendizaje y auto-mejora que genera CAPITAL COGNITIVO REAL.
    
    Flujo:
    1. EVENT → Evento de aprendizaje generado
    2. PROCESS → Procesamiento del evento
    3. REINFORCE → Refuerzo de comportamientos
    4. COORDINATE → Coordinación con otros agentes
    5. REFLECT → Reflexión y auto-análisis
    
    Resultado: CAPITAL COGNITIVO REAL acumulado
    """
    
    def __init__(self, agent_id: str, domain: str = "general"):
        self.agent_id = agent_id
        self.domain = domain
        
        # Componentes
        self.reinforcement_engine = ReinforcementEngine()
        self.coordination_engine = CoordinationEngine()
        self.reflection_engine = ReflectionEngine()
        
        # Estado
        self.is_running = False
        self.event_queue: List[LearningEvent] = []
        
        # Métricas globales
        self.pipeline_metrics = {
            "events_processed": 0,
            "total_learning_value": 0.0,
            "reflections_completed": 0,
            "coordinations_completed": 0,
            "started_at": None,
        }
    
    async def start(self) -> None:
        """Inicia el pipeline"""
        self.is_running = True
        self.pipeline_metrics["started_at"] = datetime.utcnow().isoformat()
        
        # Registrar agente en coordinación
        self.coordination_engine.register_agent(self.agent_id, self.domain)
        
        logger.info(f"Learning pipeline started for {self.agent_id}")
    
    async def stop(self) -> None:
        """Detiene el pipeline"""
        self.is_running = False
        logger.info(f"Learning pipeline stopped for {self.agent_id}")
    
    async def submit_event(self, event: LearningEvent) -> str:
        """Envía un evento al pipeline"""
        self.event_queue.append(event)
        return str(event.id)
    
    async def process_event(self, event: LearningEvent) -> Dict[str, Any]:
        """
        Procesa un evento a través de todo el pipeline
        """
        result = {
            "event_id": str(event.id),
            "event_type": event.event_type.value,
            "processing_stages": [],
            "learning_extracted": {},
            "capital_delta": 0.0,
        }
        
        # Stage 1: Procesar
        learning = self._extract_learning(event)
        result["learning_extracted"] = learning
        result["processing_stages"].append("processed")
        
        # Stage 2: Reforzar
        reward = self.reinforcement_engine.compute_reward(event, "processed")
        state = f"{event.source_domain}:{event.event_type.value}"
        new_q = self.reinforcement_engine.update_q_value(state, "process", reward)
        result["q_value_update"] = new_q
        result["processing_stages"].append("reinforced")
        
        # Stage 3: Coordinar
        if event.broadcast or event.target_agents:
            coordination = await self.coordination_engine.coordinate_learning(event, learning)
            result["coordination"] = coordination
            self.pipeline_metrics["coordinations_completed"] += 1
        result["processing_stages"].append("coordinated")
        
        # Stage 4: Actualizar métricas
        event.mark_processed(result)
        self.pipeline_metrics["events_processed"] += 1
        self.pipeline_metrics["total_learning_value"] += event.learning_value
        
        # Calcular delta de capital
        result["capital_delta"] = event.learning_value * 10 + reward * 5
        
        return result
    
    def _extract_learning(self, event: LearningEvent) -> Dict[str, Any]:
        """Extrae aprendizaje de un evento"""
        learning = {
            "patterns": [],
            "skills": [],
            "insights": [],
        }
        
        payload = event.payload
        
        # Extraer patrones
        if "patterns" in payload:
            learning["patterns"] = payload["patterns"]
        
        # Extraer skills
        if "skills_demonstrated" in payload:
            learning["skills"] = payload["skills_demonstrated"]
        
        # Extraer insights
        if "insights" in payload:
            learning["insights"] = payload["insights"]
        
        # Generar insight básico del evento
        if event.event_type == LearningEventType.SUCCESS_ACHIEVED:
            learning["insights"].append({
                "type": "success_pattern",
                "context": event.context,
                "confidence": 0.7,
            })
        
        return learning
    
    async def run_reflection_cycle(self, capital_report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta un ciclo de reflexión
        """
        coordination_metrics = self.coordination_engine.get_coordination_metrics()
        
        reflection = await self.reflection_engine.reflect(
            self.agent_id,
            capital_report,
            coordination_metrics
        )
        
        self.pipeline_metrics["reflections_completed"] += 1
        
        return reflection
    
    async def process_queue(self, batch_size: int = 10) -> List[Dict[str, Any]]:
        """Procesa eventos pendientes en cola"""
        results = []
        
        to_process = self.event_queue[:batch_size]
        self.event_queue = self.event_queue[batch_size:]
        
        for event in to_process:
            result = await self.process_event(event)
            results.append(result)
        
        return results
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Obtiene estado completo del pipeline"""
        return {
            "agent_id": self.agent_id,
            "domain": self.domain,
            "is_running": self.is_running,
            "queue_size": len(self.event_queue),
            "metrics": self.pipeline_metrics,
            "reinforcement": self.reinforcement_engine.get_metrics(),
            "coordination": self.coordination_engine.get_coordination_metrics(),
            "recent_reflections": self.reflection_engine.get_recent_reflections(3),
            "active_improvement_plans": self.reflection_engine.get_active_improvement_plans(),
        }


# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    "LearningEventType",
    "LearningPriority",
    "LearningEvent",
    "ReinforcementEngine",
    "CoordinationEngine",
    "ReflectionEngine",
    "LearningPipeline",
]
