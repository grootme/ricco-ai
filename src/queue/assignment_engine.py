"""
NEXUS Agent Assignment Engine - Motor de Asignación de Agentes

Implementa algoritmo de asignación con scoring multi-factor:
- Capability Match (40%): Coincidencia de capacidades requeridas
- Load Balance (35%): Distribución equilibrada de carga
- User Affinity (15%): Preferencia por sesiones continuas
- Performance (10%): Historial de éxito del agente

Soporta:
- Asignación directa por ID
- Asignación por dominio/rol IOVBA
- Asignación por capacidades
- Asignación con afinidad de usuario
"""

import asyncio
import json
import math
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

from .agent_tracker import (
    AgentAvailabilityTracker,
    AgentInfo,
    AgentStatus,
    AgentCapability
)
from .redis_streams import Task, TaskPriority

logger = logging.getLogger(__name__)


class AssignmentStrategy(str, Enum):
    """Estrategias de asignación"""
    ROUND_ROBIN = "round_robin"           # Rotación simple
    LEAST_BUSY = "least_busy"             # Menor carga
    CAPABILITY_BASED = "capability_based" # Mejor match de capacidades
    AFFINITY_AWARE = "affinity_aware"     # Considera sesiones de usuario
    HYBRID = "hybrid"                     # Multi-factor scoring
    RANDOM = "random"                     # Aleatorio (para testing)


@dataclass
class AssignmentScore:
    """Score de asignación para un agente"""
    agent_id: str
    total_score: float = 0.0
    capability_score: float = 0.0
    load_score: float = 0.0
    affinity_score: float = 0.0
    performance_score: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AssignmentResult:
    """Resultado de una asignación"""
    success: bool
    agent_id: Optional[str] = None
    agent_info: Optional[AgentInfo] = None
    task_id: str = ""
    assigned_at: datetime = field(default_factory=datetime.utcnow)
    strategy_used: AssignmentStrategy = AssignmentStrategy.HYBRID
    scores: List[AssignmentScore] = field(default_factory=list)
    reason: str = ""
    queue_position: int = 0  # Si fue encolado
    estimated_wait_seconds: float = 0.0


class AgentAssignmentEngine:
    """
    Motor de asignación de agentes
    
    Características:
    - Múltiples estrategias de asignación
    - Scoring multi-factor ponderado
    - Soporte para multi-tenant
    - Métricas de asignación
    - Fallback cuando no hay agentes disponibles
    """
    
    # Pesos para scoring híbrido
    WEIGHTS = {
        "capability": 0.40,
        "load": 0.35,
        "affinity": 0.15,
        "performance": 0.10,
    }
    
    def __init__(
        self,
        tracker: AgentAvailabilityTracker,
        strategy: AssignmentStrategy = AssignmentStrategy.HYBRID,
    ):
        self.tracker = tracker
        self.strategy = strategy
        
        # Estado para round robin
        self._round_robin_index: Dict[str, int] = {}
        
        # Métricas
        self._assignment_count: Dict[str, int] = {}
        self._failed_assignments: Dict[str, int] = {}
    
    async def assign(
        self,
        task: Task,
        strategy: Optional[AssignmentStrategy] = None,
        prefer_user_affinity: bool = True,
        required_capabilities: Optional[List[str]] = None,
    ) -> AssignmentResult:
        """
        Asigna un agente a una tarea
        
        Args:
            task: Tarea a asignar
            strategy: Estrategia a usar (opcional, sobrescribe default)
            prefer_user_affinity: Si debe preferir afinidad de usuario
            required_capabilities: Capacidades requeridas
            
        Returns:
            AssignmentResult con el resultado
        """
        strategy = strategy or self.strategy
        
        logger.info(
            f"Starting assignment for task {task.id}",
            extra={
                "task_id": task.id,
                "user_id": task.user_id,
                "domain": task.domain,
                "iovba_role": task.iovba_role,
                "strategy": strategy.value
            }
        )
        
        # 1. Obtener candidatos
        candidates = await self._get_candidates(task, required_capabilities)
        
        if not candidates:
            return AssignmentResult(
                success=False,
                task_id=task.id,
                reason="No available agents found",
                strategy_used=strategy
            )
        
        # 2. Aplicar estrategia de asignación
        if strategy == AssignmentStrategy.DIRECT and task.agent_id:
            return await self._assign_direct(task, candidates)
        elif strategy == AssignmentStrategy.ROUND_ROBIN:
            return await self._assign_round_robin(task, candidates)
        elif strategy == AssignmentStrategy.LEAST_BUSY:
            return await self._assign_least_busy(task, candidates)
        elif strategy == AssignmentStrategy.CAPABILITY_BASED:
            return await self._assign_capability_based(task, candidates, required_capabilities)
        elif strategy == AssignmentStrategy.AFFINITY_AWARE:
            return await self._assign_affinity_aware(task, candidates)
        elif strategy == AssignmentStrategy.RANDOM:
            return await self._assign_random(task, candidates)
        else:  # HYBRID
            return await self._assign_hybrid(
                task, 
                candidates, 
                required_capabilities,
                prefer_user_affinity
            )
    
    async def _get_candidates(
        self,
        task: Task,
        required_capabilities: Optional[List[str]] = None
    ) -> List[AgentInfo]:
        """Obtiene candidatos disponibles para la tarea"""
        candidates = await self.tracker.get_available_agents(
            domain=task.domain,
            iovba_role=task.iovba_role,
            capabilities=required_capabilities
        )
        
        # Si hay agente específico, filtrar
        if task.agent_id:
            candidates = [a for a in candidates if a.id == task.agent_id]
        
        return candidates
    
    async def _assign_direct(
        self,
        task: Task,
        candidates: List[AgentInfo]
    ) -> AssignmentResult:
        """Asignación directa por ID de agente"""
        if not task.agent_id:
            return AssignmentResult(
                success=False,
                task_id=task.id,
                reason="No agent_id specified for direct assignment"
            )
        
        agent = next((a for a in candidates if a.id == task.agent_id), None)
        
        if not agent:
            return AssignmentResult(
                success=False,
                task_id=task.id,
                reason=f"Agent {task.agent_id} not available"
            )
        
        success = await self.tracker.set_agent_busy(agent.id, task.id)
        
        if success:
            self._assignment_count[agent.id] = self._assignment_count.get(agent.id, 0) + 1
            
            return AssignmentResult(
                success=True,
                agent_id=agent.id,
                agent_info=agent,
                task_id=task.id,
                strategy_used=AssignmentStrategy.DIRECT,
                reason="Direct assignment successful"
            )
        
        return AssignmentResult(
            success=False,
            task_id=task.id,
            reason=f"Failed to set agent {agent.id} as busy"
        )
    
    async def _assign_round_robin(
        self,
        task: Task,
        candidates: List[AgentInfo]
    ) -> AssignmentResult:
        """Asignación round robin"""
        if not candidates:
            return AssignmentResult(
                success=False,
                task_id=task.id,
                reason="No candidates for round robin"
            )
        
        # Key para el índice
        key = f"{task.domain}:{task.iovba_role}" if task.iovba_role else task.domain
        
        # Obtener y actualizar índice
        idx = self._round_robin_index.get(key, 0)
        self._round_robin_index[key] = (idx + 1) % len(candidates)
        
        agent = candidates[idx]
        
        success = await self.tracker.set_agent_busy(agent.id, task.id)
        
        if success:
            self._assignment_count[agent.id] = self._assignment_count.get(agent.id, 0) + 1
            
            return AssignmentResult(
                success=True,
                agent_id=agent.id,
                agent_info=agent,
                task_id=task.id,
                strategy_used=AssignmentStrategy.ROUND_ROBIN,
                reason=f"Round robin assignment (index {idx})"
            )
        
        # Fallback al siguiente
        for i in range(1, len(candidates)):
            next_idx = (idx + i) % len(candidates)
            next_agent = candidates[next_idx]
            
            if await self.tracker.set_agent_busy(next_agent.id, task.id):
                self._assignment_count[next_agent.id] = self._assignment_count.get(next_agent.id, 0) + 1
                
                return AssignmentResult(
                    success=True,
                    agent_id=next_agent.id,
                    agent_info=next_agent,
                    task_id=task.id,
                    strategy_used=AssignmentStrategy.ROUND_ROBIN,
                    reason=f"Round robin fallback (index {next_idx})"
                )
        
        return AssignmentResult(
            success=False,
            task_id=task.id,
            reason="All agents busy in round robin"
        )
    
    async def _assign_least_busy(
        self,
        task: Task,
        candidates: List[AgentInfo]
    ) -> AssignmentResult:
        """Asignación al agente con menor carga"""
        if not candidates:
            return AssignmentResult(
                success=False,
                task_id=task.id,
                reason="No candidates"
            )
        
        # Ordenar por carga (ascending)
        sorted_candidates = sorted(
            candidates,
            key=lambda a: a.metrics.current_load
        )
        
        for agent in sorted_candidates:
            if await self.tracker.set_agent_busy(agent.id, task.id):
                self._assignment_count[agent.id] = self._assignment_count.get(agent.id, 0) + 1
                
                return AssignmentResult(
                    success=True,
                    agent_id=agent.id,
                    agent_info=agent,
                    task_id=task.id,
                    strategy_used=AssignmentStrategy.LEAST_BUSY,
                    reason=f"Least busy agent (load: {agent.metrics.current_load:.2f})"
                )
        
        return AssignmentResult(
            success=False,
            task_id=task.id,
            reason="All agents busy"
        )
    
    async def _assign_capability_based(
        self,
        task: Task,
        candidates: List[AgentInfo],
        required_capabilities: Optional[List[str]] = None
    ) -> AssignmentResult:
        """Asignación basada en capacidades"""
        if not candidates:
            return AssignmentResult(
                success=False,
                task_id=task.id,
                reason="No candidates"
            )
        
        # Calcular scores de capacidad
        scored = []
        for agent in candidates:
            score = 0.0
            if required_capabilities:
                for cap in required_capabilities:
                    score += agent.get_capability_score(cap)
                score /= len(required_capabilities)
            else:
                # Score promedio de todas las capacidades
                if agent.capabilities:
                    score = sum(c.score for c in agent.capabilities) / len(agent.capabilities)
            
            scored.append((agent, score))
        
        # Ordenar por score (descending)
        scored.sort(key=lambda x: x[1], reverse=True)
        
        for agent, score in scored:
            if await self.tracker.set_agent_busy(agent.id, task.id):
                self._assignment_count[agent.id] = self._assignment_count.get(agent.id, 0) + 1
                
                return AssignmentResult(
                    success=True,
                    agent_id=agent.id,
                    agent_info=agent,
                    task_id=task.id,
                    strategy_used=AssignmentStrategy.CAPABILITY_BASED,
                    reason=f"Best capability match (score: {score:.2f})",
                    scores=[
                        AssignmentScore(
                            agent_id=a.id,
                            capability_score=s,
                            total_score=s
                        )
                        for a, s in scored[:5]
                    ]
                )
        
        return AssignmentResult(
            success=False,
            task_id=task.id,
            reason="All agents busy"
        )
    
    async def _assign_affinity_aware(
        self,
        task: Task,
        candidates: List[AgentInfo]
    ) -> AssignmentResult:
        """Asignación considerando afinidad de usuario"""
        if not candidates:
            return AssignmentResult(
                success=False,
                task_id=task.id,
                reason="No candidates"
            )
        
        # Calcular scores de afinidad
        scored = []
        for agent in candidates:
            affinity = agent.user_affinity.get(task.user_id, 0.0)
            scored.append((agent, affinity))
        
        # Ordenar por afinidad (descending)
        scored.sort(key=lambda x: x[1], reverse=True)
        
        for agent, affinity in scored:
            if await self.tracker.set_agent_busy(agent.id, task.id):
                self._assignment_count[agent.id] = self._assignment_count.get(agent.id, 0) + 1
                
                # Incrementar afinidad
                await self.tracker.update_user_affinity(
                    agent.id, 
                    task.user_id, 
                    delta=0.1
                )
                
                return AssignmentResult(
                    success=True,
                    agent_id=agent.id,
                    agent_info=agent,
                    task_id=task.id,
                    strategy_used=AssignmentStrategy.AFFINITY_AWARE,
                    reason=f"User affinity match (score: {affinity:.2f})",
                    scores=[
                        AssignmentScore(
                            agent_id=a.id,
                            affinity_score=af,
                            total_score=af
                        )
                        for a, af in scored[:5]
                    ]
                )
        
        return AssignmentResult(
            success=False,
            task_id=task.id,
            reason="All agents busy"
        )
    
    async def _assign_hybrid(
        self,
        task: Task,
        candidates: List[AgentInfo],
        required_capabilities: Optional[List[str]] = None,
        prefer_user_affinity: bool = True
    ) -> AssignmentResult:
        """
        Asignación híbrida con scoring multi-factor
        
        Score = 0.40 * Capability + 0.35 * Load + 0.15 * Affinity + 0.10 * Performance
        """
        if not candidates:
            return AssignmentResult(
                success=False,
                task_id=task.id,
                reason="No candidates"
            )
        
        # Calcular scores para todos los candidatos
        scores: List[AssignmentScore] = []
        
        for agent in candidates:
            assignment_score = AssignmentScore(agent_id=agent.id)
            
            # 1. Capability Score (0-1)
            if required_capabilities:
                cap_score = sum(
                    agent.get_capability_score(cap) 
                    for cap in required_capabilities
                ) / len(required_capabilities)
            else:
                cap_score = 1.0 if not agent.capabilities else (
                    sum(c.score for c in agent.capabilities) / len(agent.capabilities)
                )
            assignment_score.capability_score = cap_score
            
            # 2. Load Score (inverso de carga, 0-1)
            assignment_score.load_score = 1.0 - agent.metrics.current_load
            
            # 3. Affinity Score (0-1)
            if prefer_user_affinity and task.user_id:
                assignment_score.affinity_score = agent.user_affinity.get(task.user_id, 0.0)
            else:
                assignment_score.affinity_score = 0.0
            
            # 4. Performance Score (0-1)
            assignment_score.performance_score = agent.metrics.calculate_performance_score()
            
            # Total ponderado
            assignment_score.total_score = (
                self.WEIGHTS["capability"] * assignment_score.capability_score +
                self.WEIGHTS["load"] * assignment_score.load_score +
                self.WEIGHTS["affinity"] * assignment_score.affinity_score +
                self.WEIGHTS["performance"] * assignment_score.performance_score
            )
            
            assignment_score.details = {
                "agent_name": agent.name,
                "domain": agent.domain,
                "role": agent.iovba_role,
                "current_load": agent.metrics.current_load,
                "tasks_completed": agent.metrics.tasks_completed,
            }
            
            scores.append(assignment_score)
        
        # Ordenar por score total (descending)
        scores.sort(key=lambda s: s.total_score, reverse=True)
        
        # Log de scoring
        logger.info(
            f"Hybrid assignment scores for task {task.id}",
            extra={
                "task_id": task.id,
                "scores": [
                    {
                        "agent_id": s.agent_id,
                        "total": s.total_score,
                        "capability": s.capability_score,
                        "load": s.load_score,
                        "affinity": s.affinity_score,
                        "performance": s.performance_score
                    }
                    for s in scores[:5]
                ]
            }
        )
        
        # Intentar asignar al mejor candidato
        for score in scores:
            agent = next(a for a in candidates if a.id == score.agent_id)
            
            if await self.tracker.set_agent_busy(agent.id, task.id):
                self._assignment_count[agent.id] = self._assignment_count.get(agent.id, 0) + 1
                
                # Incrementar afinidad
                if prefer_user_affinity and task.user_id:
                    await self.tracker.update_user_affinity(
                        agent.id,
                        task.user_id,
                        delta=0.1
                    )
                
                return AssignmentResult(
                    success=True,
                    agent_id=agent.id,
                    agent_info=agent,
                    task_id=task.id,
                    strategy_used=AssignmentStrategy.HYBRID,
                    reason=f"Hybrid best match (score: {score.total_score:.3f})",
                    scores=scores[:5]
                )
        
        return AssignmentResult(
            success=False,
            task_id=task.id,
            reason="All agents busy"
        )
    
    async def _assign_random(
        self,
        task: Task,
        candidates: List[AgentInfo]
    ) -> AssignmentResult:
        """Asignación aleatoria (para testing)"""
        import random
        
        if not candidates:
            return AssignmentResult(
                success=False,
                task_id=task.id,
                reason="No candidates"
            )
        
        random.shuffle(candidates)
        
        for agent in candidates:
            if await self.tracker.set_agent_busy(agent.id, task.id):
                self._assignment_count[agent.id] = self._assignment_count.get(agent.id, 0) + 1
                
                return AssignmentResult(
                    success=True,
                    agent_id=agent.id,
                    agent_info=agent,
                    task_id=task.id,
                    strategy_used=AssignmentStrategy.RANDOM,
                    reason="Random assignment"
                )
        
        return AssignmentResult(
            success=False,
            task_id=task.id,
            reason="All agents busy"
        )
    
    async def get_assignment_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de asignación"""
        return {
            "total_assignments": sum(self._assignment_count.values()),
            "total_failures": sum(self._failed_assignments.values()),
            "by_agent": dict(self._assignment_count),
            "failures_by_agent": dict(self._failed_assignments),
            "strategy": self.strategy.value,
            "weights": self.WEIGHTS,
        }
