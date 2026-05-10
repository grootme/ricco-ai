#!/usr/bin/env python3
"""
NEXUS - Neural Execution Unified System
Script de Inicialización

Este script:
1. Conecta con Redis
2. Crea los 13 grupos IOVBA (mínimo 10)
3. Inicializa las colas de tareas
4. Configura el sistema de eventos
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional

# Añadir path del proyecto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.queue.redis_streams import RedisStreamClient, Task, TaskPriority, TaskStatus
from src.queue.redis_event_store import RedisEventStore, StoredEvent, EventType
from src.queue.agent_tracker import AgentAvailabilityTracker, AgentInfo, AgentStatus, AgentCapability
from src.iovba.groups import (
    IOVBAGroupManager, IOVBAGroup, AgentProfile,
    DOMAIN_BRANDING, ROLE_BRANDING, PLATFORM_BRAND, IOVBADomain
)


class NexusInitializer:
    """Inicializador del sistema NEXUS"""
    
    # Dominios a inicializar (13 grupos - más de los 10 requeridos)
    DOMAINS_TO_INIT = [
        "swe",           # CODEX
        "salud",         # VITALIS
        "deportes",      # ATHLON
        "noticias",      # VERITAS
        "quimica",       # ALCHEMY
        "biologia",      # GENESIS
        "biotecnologia", # HELIX
        "geopolitica",   # DIPLOMAT
        "finanzas",      # APEX
        "legal",         # JUSTITIA
        "educacion",     # MENTOR
        "investigacion", # PIONEER
        "marketing",     # PRISMA
    ]
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[RedisStreamClient] = None
        self.event_store: Optional[RedisEventStore] = None
        self.agent_tracker: Optional[AgentAvailabilityTracker] = None
        self.iovba_manager: Optional[IOVBAGroupManager] = None
        self.groups: List[IOVBAGroup] = []
        
    async def initialize(self) -> Dict[str, Any]:
        """Inicializa todo el sistema NEXUS"""
        print(f"\n{'='*70}")
        print(f"🚀 NEXUS - Neural Execution Unified System")
        print(f"   Version: {PLATFORM_BRAND['version']}")
        print(f"   {PLATFORM_BRAND['tagline']}")
        print(f"{'='*70}\n")
        
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "platform": PLATFORM_BRAND,
            "steps": []
        }
        
        # Paso 1: Conectar con Redis
        print("📡 [1/5] Conectando con Redis...")
        try:
            await self._connect_redis()
            results["steps"].append({
                "step": "redis_connection",
                "status": "success",
                "message": f"Connected to {self.redis_url}"
            })
            print(f"   ✅ Redis conectado en {self.redis_url}")
        except Exception as e:
            results["steps"].append({
                "step": "redis_connection",
                "status": "failed",
                "error": str(e)
            })
            print(f"   ❌ Error conectando Redis: {e}")
            return results
        
        # Paso 2: Inicializar Event Store
        print("📊 [2/5] Inicializando Event Store...")
        try:
            self.event_store = RedisEventStore(redis_url=self.redis_url, tenant_id="nexus-main")
            await self.event_store.connect()
            results["steps"].append({
                "step": "event_store",
                "status": "success"
            })
            print(f"   ✅ Event Store inicializado")
        except Exception as e:
            results["steps"].append({
                "step": "event_store",
                "status": "failed",
                "error": str(e)
            })
            print(f"   ❌ Error: {e}")
        
        # Paso 3: Inicializar Agent Tracker
        print("👥 [3/5] Inicializando Agent Tracker...")
        try:
            self.agent_tracker = AgentAvailabilityTracker(redis_url=self.redis_url, tenant_id="nexus-main")
            await self.agent_tracker.connect()
            results["steps"].append({
                "step": "agent_tracker",
                "status": "success"
            })
            print(f"   ✅ Agent Tracker inicializado")
        except Exception as e:
            results["steps"].append({
                "step": "agent_tracker",
                "status": "failed",
                "error": str(e)
            })
            print(f"   ❌ Error: {e}")
        
        # Paso 4: Crear Grupos IOVBA
        print("🤖 [4/5] Creando Grupos IOVBA (mínimo 10)...")
        try:
            groups = await self._create_iovba_groups()
            self.groups = groups
            results["steps"].append({
                "step": "iovba_groups",
                "status": "success",
                "groups_created": len(groups)
            })
            print(f"   ✅ {len(groups)} grupos IOVBA creados")
        except Exception as e:
            results["steps"].append({
                "step": "iovba_groups",
                "status": "failed",
                "error": str(e)
            })
            print(f"   ❌ Error: {e}")
        
        # Paso 5: Verificar colas
        print("📬 [5/5] Verificando colas de tareas...")
        try:
            stats = await self.redis_client.get_queue_stats()
            results["steps"].append({
                "step": "queues",
                "status": "success",
                "stats": stats
            })
            print(f"   ✅ Colas verificadas")
            print(f"      - Streams: {list(stats.get('streams', {}).keys())}")
        except Exception as e:
            results["steps"].append({
                "step": "queues",
                "status": "failed",
                "error": str(e)
            })
            print(f"   ❌ Error: {e}")
        
        # Resumen final
        print(f"\n{'='*70}")
        print("📋 RESUMEN DE INICIALIZACIÓN")
        print(f"{'='*70}")
        
        for step in results["steps"]:
            status_icon = "✅" if step["status"] == "success" else "❌"
            print(f"   {status_icon} {step['step']}: {step['status']}")
        
        print(f"\n🌐 NEXUS está listo para recibir solicitudes")
        print(f"{'='*70}\n")
        
        return results
    
    async def _connect_redis(self):
        """Conecta con Redis"""
        self.redis_client = RedisStreamClient(
            redis_url=self.redis_url,
            tenant_id="nexus-main"
        )
        await self.redis_client.connect()
    
    async def _create_iovba_groups(self) -> List[IOVBAGroup]:
        """Crea los grupos IOVBA para cada dominio"""
        self.iovba_manager = IOVBAGroupManager()
        groups = []
        
        for domain in self.DOMAINS_TO_INIT:
            brand = DOMAIN_BRANDING.get(domain)
            if not brand:
                continue
            
            # Crear grupo
            group = self.iovba_manager.create_group(
                name=f"{brand.elegant_name} Unit",
                domain=domain,
                description=brand.description
            )
            
            # Registrar agentes en el tracker
            if self.agent_tracker:
                for role, agent in group.get_all_agents().items():
                    if agent:
                        agent_info = AgentInfo(
                            id=agent.id,
                            name=agent.name,
                            domain=domain,
                            iovba_role=role,
                            iovba_group_id=group.id,
                            tenant_id="nexus-main",
                            status=AgentStatus.ONLINE,
                            capabilities=[
                                AgentCapability(name=skill, score=1.0)
                                for skill in agent.skills
                            ]
                        )
                        await self.agent_tracker.register_agent(agent_info)
            
            groups.append(group)
            
            print(f"   📌 {brand.elegant_name} ({domain}): {group.id[:8]}...")
            print(f"      └─ Agentes: Investigador, Observador, Validador, Builder, Asistente")
        
        return groups
    
    async def publish_task(
        self,
        domain: str = "swe",
        message: str = "Test message",
        role: str = "investigador",
        user_id: str = "test-user",
        priority: TaskPriority = TaskPriority.NORMAL
    ) -> str:
        """Publica una tarea en la cola"""
        if not self.iovba_manager:
            raise RuntimeError("IOVBA Manager not initialized")
        
        # Encontrar grupo del dominio
        target_group = None
        for g in self.groups:
            if g.domain == domain:
                target_group = g
                break
        
        if not target_group:
            raise ValueError(f"No group found for domain: {domain}")
        
        # Crear tarea
        task = Task(
            tenant_id="nexus-main",
            user_id=user_id,
            session_id=f"session-{user_id}",
            iovba_group_id=target_group.id,
            iovba_role=role,
            domain=domain,
            task_type="chat",
            priority=priority,
            input_data={
                "message": message,
                "context": "User request"
            }
        )
        
        # Publicar
        message_id = await self.redis_client.publish_task(task)
        
        # Registrar evento
        if self.event_store:
            event = StoredEvent(
                event_type=EventType.TASK_CREATED,
                aggregate_id=task.id,
                aggregate_type="task",
                tenant_id="nexus-main",
                user_id=user_id,
                payload={
                    "domain": domain,
                    "role": role,
                    "message": message[:100]
                }
            )
            await self.event_store.append(event)
        
        print(f"📝 Tarea publicada: {task.id}")
        print(f"   Grupo: {target_group.elegant_name}")
        print(f"   Rol: {role}")
        print(f"   Message ID: {message_id}")
        
        return task.id
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """Obtiene el estado de las colas"""
        return await self.redis_client.get_queue_stats()
    
    async def get_agent_status(self) -> Dict[str, Any]:
        """Obtiene el estado de los agentes"""
        if not self.agent_tracker:
            return {}
        return await self.agent_tracker.get_all_agents_status()
    
    async def get_groups_info(self) -> List[Dict[str, Any]]:
        """Obtiene información de todos los grupos"""
        return [
            {
                "id": g.id,
                "name": g.name,
                "elegant_name": g.elegant_name,
                "domain": g.domain,
                "description": g.description,
                "agents": {
                    role: {"id": a.id, "name": a.name}
                    for role, a in g.get_all_agents().items()
                    if a
                }
            }
            for g in self.groups
        ]
    
    async def shutdown(self):
        """Cierra todas las conexiones"""
        if self.redis_client:
            await self.redis_client.disconnect()
        if self.event_store:
            await self.event_store.disconnect()
        if self.agent_tracker:
            await self.agent_tracker.disconnect()


async def main():
    """Función principal"""
    initializer = NexusInitializer()
    
    try:
        # Inicializar
        results = await initializer.initialize()
        
        # Mostrar grupos creados
        print("\n📊 Grupos IOVBA creados:")
        for group in await initializer.get_groups_info():
            print(f"   • {group['elegant_name']} ({group['domain']}): {len(group['agents'])} agentes")
        
        # Publicar tareas de prueba para cada dominio
        print("\n🧪 Publicando tareas de prueba...")
        for i, domain in enumerate(initializer.DOMAINS_TO_INIT[:3]):
            try:
                await initializer.publish_task(
                    domain=domain,
                    message=f"Test task #{i+1} for {domain} domain",
                    role=["investigador", "builder", "asistente"][i % 3]
                )
            except Exception as e:
                print(f"   Error publicando tarea para {domain}: {e}")
        
        # Mostrar estado de colas
        print("\n📊 Estado de colas:")
        stats = await initializer.get_queue_status()
        for priority, info in stats.get("streams", {}).items():
            print(f"   {priority}: {info.get('length', 0)} mensajes")
        
        # Mostrar estado de agentes
        print("\n🤖 Estado de agentes:")
        agent_status = await initializer.get_agent_status()
        print(f"   Total registrados: {len(agent_status)}")
        
        # Estadísticas del tracker
        tracker_stats = await initializer.agent_tracker.get_statistics()
        print(f"   Disponibles: {tracker_stats.get('available_count', 0)}")
        print(f"   Ocupados: {tracker_stats.get('busy_count', 0)}")
        
    finally:
        await initializer.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
