"""
NEXUS Agent Availability Tracker - Sistema de Tracking de Agentes

Implementa tracking de disponibilidad con:
- Heartbeats para detección de agentes activos
- Scoring de carga para balanceo
- Afinidad usuario-agente para sesiones
- Métricas de performance
"""

import asyncio
import json
import time
import uuid
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import math

try:
    import redis.asyncio as redis
    from redis.asyncio import Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class AgentStatus(str, Enum):
    """Estado de un agente"""
    ONLINE = "online"          # Disponible y activo
    BUSY = "busy"              # Ocupado procesando
    AWAY = "away"              # Ausente temporal
    OFFLINE = "offline"        # Desconectado
    ERROR = "error"            # En estado de error
    MAINTENANCE = "maintenance" # En mantenimiento


@dataclass
class AgentCapability:
    """Capacidad de un agente"""
    name: str
    score: float = 1.0  # 0.0 - 1.0
    tags: List[str] = field(default_factory=list)


@dataclass
class AgentMetrics:
    """Métricas de un agente"""
    tasks_completed: int = 0
    tasks_failed: int = 0
    avg_response_time_ms: float = 0.0
    avg_processing_time_ms: float = 0.0
    success_rate: float = 1.0
    current_load: float = 0.0  # 0.0 - 1.0
    last_task_at: Optional[datetime] = None
    
    def calculate_performance_score(self) -> float:
        """Calcula score de performance (0-1)"""
        # Factores: success_rate, response_time, failures
        score = self.success_rate * 0.5
        
        # Penalizar por response time alto
        if self.avg_response_time_ms > 0:
            time_score = max(0, 1 - (self.avg_response_time_ms / 5000))
            score += time_score * 0.3
        
        # Penalizar por failures
        if self.tasks_completed > 0:
            failure_rate = self.tasks_failed / (self.tasks_completed + self.tasks_failed)
            score += (1 - failure_rate) * 0.2
        else:
            score += 0.2
        
        return min(1.0, max(0.0, score))


@dataclass
class AgentInfo:
    """Información completa de un agente"""
    id: str
    name: str
    domain: str
    iovba_role: Optional[str] = None
    iovba_group_id: Optional[str] = None
    tenant_id: str = "default"
    status: AgentStatus = AgentStatus.OFFLINE
    capabilities: List[AgentCapability] = field(default_factory=list)
    metrics: AgentMetrics = field(default_factory=AgentMetrics)
    current_task_id: Optional[str] = None
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    registered_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Afinidad con usuarios (para sesiones continuas)
    user_affinity: Dict[str, float] = field(default_factory=dict)
    
    def is_available(self) -> bool:
        """Verifica si el agente está disponible"""
        return self.status == AgentStatus.ONLINE and self.current_task_id is None
    
    def get_capability_score(self, capability_name: str) -> float:
        """Obtiene score de una capacidad específica"""
        for cap in self.capabilities:
            if cap.name == capability_name:
                return cap.score
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Serializa a diccionario"""
        return {
            "id": self.id,
            "name": self.name,
            "domain": self.domain,
            "iovba_role": self.iovba_role,
            "iovba_group_id": self.iovba_group_id,
            "tenant_id": self.tenant_id,
            "status": self.status.value,
            "capabilities": [
                {"name": c.name, "score": c.score, "tags": c.tags}
                for c in self.capabilities
            ],
            "metrics": {
                "tasks_completed": self.metrics.tasks_completed,
                "tasks_failed": self.metrics.tasks_failed,
                "avg_response_time_ms": self.metrics.avg_response_time_ms,
                "avg_processing_time_ms": self.metrics.avg_processing_time_ms,
                "success_rate": self.metrics.success_rate,
                "current_load": self.metrics.current_load,
                "performance_score": self.metrics.calculate_performance_score(),
            },
            "current_task_id": self.current_task_id,
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "registered_at": self.registered_at.isoformat(),
            "is_available": self.is_available(),
            "user_affinity": self.user_affinity,
            "metadata": self.metadata,
        }


class AgentAvailabilityTracker:
    """
    Tracker de disponibilidad de agentes con Redis
    
    Características:
    - Heartbeats con TTL
    - Detección de timeout
    - Scoring de carga
    - Afinidad usuario-agente
    - Métricas en tiempo real
    """
    
    # Key patterns
    AGENT_KEY = "nexus:tenant:{tenant_id}:agent:{agent_id}"
    AGENTS_SET = "nexus:tenant:{tenant_id}:agents"
    AGENTS_BY_DOMAIN = "nexus:tenant:{tenant_id}:agents:domain:{domain}"
    AGENTS_BY_ROLE = "nexus:tenant:{tenant_id}:agents:role:{role}"
    AGENTS_BY_STATUS = "nexus:tenant:{tenant_id}:agents:status:{status}"
    
    # Heartbeat TTL (30 segundos)
    HEARTBEAT_TTL = 30
    HEARTBEAT_INTERVAL = 10  # Segundos entre heartbeats
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        tenant_id: str = "default",
        heartbeat_timeout: int = 30
    ):
        if not REDIS_AVAILABLE:
            raise ImportError("redis package required")
        
        self.redis_url = redis_url
        self.tenant_id = tenant_id
        self.heartbeat_timeout = heartbeat_timeout
        self._redis: Optional[Redis] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._registered_agents: Dict[str, AgentInfo] = {}
    
    def _get_agent_key(self, agent_id: str) -> str:
        return self.AGENT_KEY.format(
            tenant_id=self.tenant_id,
            agent_id=agent_id
        )
    
    def _get_agents_set_key(self) -> str:
        return self.AGENTS_SET.format(tenant_id=self.tenant_id)
    
    def _get_domain_key(self, domain: str) -> str:
        return self.AGENTS_BY_DOMAIN.format(
            tenant_id=self.tenant_id,
            domain=domain
        )
    
    def _get_role_key(self, role: str) -> str:
        return self.AGENTS_BY_ROLE.format(
            tenant_id=self.tenant_id,
            role=role
        )
    
    def _get_status_key(self, status: AgentStatus) -> str:
        return self.AGENTS_BY_STATUS.format(
            tenant_id=self.tenant_id,
            status=status.value
        )
    
    async def connect(self) -> None:
        """Conecta a Redis"""
        self._redis = redis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=False
        )
        logger.info(f"AgentAvailabilityTracker connected to Redis")
    
    async def disconnect(self) -> None:
        """Desconecta de Redis"""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        
        if self._redis:
            await self._redis.close()
            self._redis = None
    
    async def register_agent(self, agent: AgentInfo) -> None:
        """
        Registra un agente en el sistema
        
        Args:
            agent: Información del agente
        """
        if not self._redis:
            raise RuntimeError("Not connected to Redis")
        
        agent_key = self._get_agent_key(agent.id)
        agents_set = self._get_agents_set_key()
        
        # Guardar información del agente
        await self._redis.hset(agent_key, mapping={
            "info": json.dumps(agent.to_dict()),
            "heartbeat": datetime.utcnow().isoformat(),
            "status": agent.status.value,
        })
        
        # TTL para heartbeat
        await self._redis.expire(agent_key, self.HEARTBEAT_TTL * 3)
        
        # Agregar a sets de índices
        await self._redis.sadd(agents_set, agent.id)
        
        # Índice por dominio
        domain_key = self._get_domain_key(agent.domain)
        await self._redis.sadd(domain_key, agent.id)
        
        # Índice por rol IOVBA
        if agent.iovba_role:
            role_key = self._get_role_key(agent.iovba_role)
            await self._redis.sadd(role_key, agent.id)
        
        # Índice por status
        status_key = self._get_status_key(agent.status)
        await self._redis.sadd(status_key, agent.id)
        
        # Guardar localmente
        self._registered_agents[agent.id] = agent
        
        logger.info(
            f"Agent registered: {agent.id}",
            extra={
                "agent_id": agent.id,
                "domain": agent.domain,
                "role": agent.iovba_role
            }
        )
    
    async def unregister_agent(self, agent_id: str) -> None:
        """Elimina un agente del sistema"""
        if not self._redis:
            raise RuntimeError("Not connected to Redis")
        
        # Obtener info primero
        agent = await self.get_agent(agent_id)
        
        if agent:
            agent_key = self._get_agent_key(agent_id)
            agents_set = self._get_agents_set_key()
            
            # Eliminar de sets
            await self._redis.srem(agents_set, agent_id)
            
            domain_key = self._get_domain_key(agent.domain)
            await self._redis.srem(domain_key, agent_id)
            
            if agent.iovba_role:
                role_key = self._get_role_key(agent.iovba_role)
                await self._redis.srem(role_key, agent_id)
            
            # Eliminar key principal
            await self._redis.delete(agent_key)
        
        # Eliminar localmente
        self._registered_agents.pop(agent_id, None)
        
        logger.info(f"Agent unregistered: {agent_id}")
    
    async def heartbeat(self, agent_id: str, status: Optional[AgentStatus] = None) -> bool:
        """
        Envía heartbeat para un agente
        
        Args:
            agent_id: ID del agente
            status: Nuevo estado (opcional)
            
        Returns:
            True si el heartbeat fue exitoso
        """
        if not self._redis:
            raise RuntimeError("Not connected to Redis")
        
        agent_key = self._get_agent_key(agent_id)
        
        # Verificar que el agente existe
        exists = await self._redis.exists(agent_key)
        if not exists:
            logger.warning(f"Heartbeat for unknown agent: {agent_id}")
            return False
        
        # Actualizar heartbeat
        updates = {
            "heartbeat": datetime.utcnow().isoformat(),
        }
        
        if status:
            # Actualizar status
            old_status = await self._redis.hget(agent_key, "status")
            if old_status:
                old_status_str = old_status.decode() if isinstance(old_status, bytes) else old_status
                # Remover de índice anterior
                old_status_key = self._get_status_key(AgentStatus(old_status_str))
                await self._redis.srem(old_status_key, agent_id)
            
            updates["status"] = status.value
            
            # Agregar a nuevo índice
            new_status_key = self._get_status_key(status)
            await self._redis.sadd(new_status_key, agent_id)
        
        await self._redis.hset(agent_key, mapping=updates)
        await self._redis.expire(agent_key, self.HEARTBEAT_TTL * 3)
        
        return True
    
    async def get_agent(self, agent_id: str) -> Optional[AgentInfo]:
        """Obtiene información de un agente"""
        if not self._redis:
            raise RuntimeError("Not connected to Redis")
        
        agent_key = self._get_agent_key(agent_id)
        data = await self._redis.hgetall(agent_key)
        
        if not data:
            return None
        
        info_json = data.get(b"info") or data.get("info")
        if info_json:
            info_dict = json.loads(
                info_json.decode() if isinstance(info_json, bytes) else info_json
            )
            return AgentInfo(
                id=info_dict["id"],
                name=info_dict["name"],
                domain=info_dict["domain"],
                iovba_role=info_dict.get("iovba_role"),
                iovba_group_id=info_dict.get("iovba_group_id"),
                tenant_id=info_dict.get("tenant_id", self.tenant_id),
                status=AgentStatus(info_dict["status"]),
                capabilities=[
                    AgentCapability(**c) for c in info_dict.get("capabilities", [])
                ],
                metrics=AgentMetrics(
                    tasks_completed=info_dict.get("metrics", {}).get("tasks_completed", 0),
                    tasks_failed=info_dict.get("metrics", {}).get("tasks_failed", 0),
                    avg_response_time_ms=info_dict.get("metrics", {}).get("avg_response_time_ms", 0),
                    success_rate=info_dict.get("metrics", {}).get("success_rate", 1.0),
                    current_load=info_dict.get("metrics", {}).get("current_load", 0),
                ),
                current_task_id=info_dict.get("current_task_id"),
                last_heartbeat=datetime.fromisoformat(info_dict["last_heartbeat"]),
                registered_at=datetime.fromisoformat(info_dict["registered_at"]),
                user_affinity=info_dict.get("user_affinity", {}),
                metadata=info_dict.get("metadata", {}),
            )
        
        return None
    
    async def get_available_agents(
        self,
        domain: Optional[str] = None,
        iovba_role: Optional[str] = None,
        capabilities: Optional[List[str]] = None,
    ) -> List[AgentInfo]:
        """
        Obtiene agentes disponibles con filtros
        
        Args:
            domain: Filtrar por dominio
            iovba_role: Filtrar por rol IOVBA
            capabilities: Capacidades requeridas
            
        Returns:
            Lista de agentes disponibles
        """
        if not self._redis:
            raise RuntimeError("Not connected to Redis")
        
        # Obtener IDs de agentes
        if domain:
            agent_ids = await self._redis.smembers(self._get_domain_key(domain))
        elif iovba_role:
            agent_ids = await self._redis.smembers(self._get_role_key(iovba_role))
        else:
            agent_ids = await self._redis.smembers(self._get_agents_set_key())
        
        agents = []
        for agent_id in agent_ids:
            aid = agent_id.decode() if isinstance(agent_id, bytes) else agent_id
            agent = await self.get_agent(aid)
            
            if agent and agent.is_available():
                # Verificar capacidades
                if capabilities:
                    has_all = all(
                        agent.get_capability_score(cap) > 0
                        for cap in capabilities
                    )
                    if not has_all:
                        continue
                
                agents.append(agent)
        
        return agents
    
    async def set_agent_busy(
        self,
        agent_id: str,
        task_id: str
    ) -> bool:
        """Marca un agente como ocupado con una tarea"""
        if not self._redis:
            raise RuntimeError("Not connected to Redis")
        
        agent = await self.get_agent(agent_id)
        if not agent or not agent.is_available():
            return False
        
        agent.status = AgentStatus.BUSY
        agent.current_task_id = task_id
        
        agent_key = self._get_agent_key(agent_id)
        await self._redis.hset(agent_key, mapping={
            "info": json.dumps(agent.to_dict()),
            "status": AgentStatus.BUSY.value,
        })
        
        # Actualizar índices
        old_status_key = self._get_status_key(AgentStatus.ONLINE)
        new_status_key = self._get_status_key(AgentStatus.BUSY)
        await self._redis.srem(old_status_key, agent_id)
        await self._redis.sadd(new_status_key, agent_id)
        
        return True
    
    async def set_agent_available(
        self,
        agent_id: str,
        task_completed: bool = True,
        processing_time_ms: Optional[float] = None
    ) -> bool:
        """Marca un agente como disponible nuevamente"""
        if not self._redis:
            raise RuntimeError("Not connected to Redis")
        
        agent = await self.get_agent(agent_id)
        if not agent:
            return False
        
        # Actualizar métricas
        if task_completed:
            agent.metrics.tasks_completed += 1
        else:
            agent.metrics.tasks_failed += 1
        
        if processing_time_ms:
            # Promedio móvil
            total = agent.metrics.tasks_completed + agent.metrics.tasks_failed
            agent.metrics.avg_processing_time_ms = (
                (agent.metrics.avg_processing_time_ms * (total - 1) + processing_time_ms) / total
            )
        
        agent.status = AgentStatus.ONLINE
        agent.current_task_id = None
        agent.metrics.current_load = 0
        
        # Recalcular success rate
        if agent.metrics.tasks_completed + agent.metrics.tasks_failed > 0:
            agent.metrics.success_rate = (
                agent.metrics.tasks_completed / 
                (agent.metrics.tasks_completed + agent.metrics.tasks_failed)
            )
        
        agent_key = self._get_agent_key(agent_id)
        await self._redis.hset(agent_key, mapping={
            "info": json.dumps(agent.to_dict()),
            "status": AgentStatus.ONLINE.value,
        })
        
        # Actualizar índices
        old_status_key = self._get_status_key(AgentStatus.BUSY)
        new_status_key = self._get_status_key(AgentStatus.ONLINE)
        await self._redis.srem(old_status_key, agent_id)
        await self._redis.sadd(new_status_key, agent_id)
        
        return True
    
    async def update_user_affinity(
        self,
        agent_id: str,
        user_id: str,
        delta: float = 0.1
    ) -> None:
        """Actualiza afinidad usuario-agente (para sesiones continuas)"""
        if not self._redis:
            raise RuntimeError("Not connected to Redis")
        
        agent = await self.get_agent(agent_id)
        if not agent:
            return
        
        current = agent.user_affinity.get(user_id, 0.0)
        agent.user_affinity[user_id] = min(1.0, current + delta)
        
        agent_key = self._get_agent_key(agent_id)
        await self._redis.hset(agent_key, "info", json.dumps(agent.to_dict()))
    
    async def detect_timeouts(self) -> List[str]:
        """
        Detecta agentes que no han enviado heartbeat
        
        Returns:
            Lista de IDs de agentes con timeout
        """
        if not self._redis:
            raise RuntimeError("Not connected to Redis")
        
        agents_set = self._get_agents_set_key()
        agent_ids = await self._redis.smembers(agents_set)
        
        timed_out = []
        now = datetime.utcnow()
        
        for agent_id in agent_ids:
            aid = agent_id.decode() if isinstance(agent_id, bytes) else agent_id
            agent = await self.get_agent(aid)
            
            if agent:
                time_since_heartbeat = (now - agent.last_heartbeat).total_seconds()
                if time_since_heartbeat > self.heartbeat_timeout:
                    timed_out.append(aid)
                    logger.warning(
                        f"Agent timeout detected: {aid}",
                        extra={
                            "agent_id": aid,
                            "seconds_since_heartbeat": time_since_heartbeat
                        }
                    )
        
        return timed_out
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Obtiene estadísticas del tracker"""
        if not self._redis:
            raise RuntimeError("Not connected to Redis")
        
        agents_set = self._get_agents_set_key()
        all_agent_ids = await self._redis.smembers(agents_set)
        
        stats = {
            "total_agents": len(all_agent_ids),
            "by_status": {},
            "by_domain": {},
            "by_role": {},
            "available_count": 0,
            "busy_count": 0,
        }
        
        for status in AgentStatus:
            status_key = self._get_status_key(status)
            count = await self._redis.scard(status_key)
            stats["by_status"][status.value] = count
            
            if status == AgentStatus.ONLINE:
                stats["available_count"] = count
            elif status == AgentStatus.BUSY:
                stats["busy_count"] = count
        
        return stats
    
    async def register_agent_simple(
        self,
        agent_id: str,
        agent_name: str,
        iovba_group_id: Optional[str] = None,
        iovba_role: Optional[str] = None,
        domain: str = "swe",
        capabilities: Optional[List[AgentCapability]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Registra un agente de forma simplificada
        
        Args:
            agent_id: ID único del agente
            agent_name: Nombre del agente
            iovba_group_id: ID del grupo IOVBA
            iovba_role: Rol en el grupo IOVBA
            domain: Dominio del agente
            capabilities: Lista de capacidades
            metadata: Metadatos adicionales
        """
        agent = AgentInfo(
            id=agent_id,
            name=agent_name,
            domain=domain,
            iovba_role=iovba_role,
            iovba_group_id=iovba_group_id,
            tenant_id=self.tenant_id,
            status=AgentStatus.ONLINE,
            capabilities=capabilities or [],
            metadata=metadata or {}
        )
        await self.register_agent(agent)
    
    async def get_all_agents_status(self) -> Dict[str, Any]:
        """
        Obtiene el estado de todos los agentes registrados
        
        Returns:
            Diccionario con ID del agente como clave y su estado como valor
        """
        if not self._redis:
            raise RuntimeError("Not connected to Redis")
        
        agents_set = self._get_agents_set_key()
        agent_ids = await self._redis.smembers(agents_set)
        
        result = {}
        for agent_id in agent_ids:
            aid = agent_id.decode() if isinstance(agent_id, bytes) else agent_id
            agent = await self.get_agent(aid)
            if agent:
                result[aid] = agent.to_dict()
        
        return result
