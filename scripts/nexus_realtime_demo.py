#!/usr/bin/env python3
"""
NEXUS - Demo de Procesamiento en Tiempo Real

Este script demuestra:
1. Inicialización del sistema
2. Publicación de tareas
3. Procesamiento con workers
4. Visualización en tiempo real de pasos y estado
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import time

# Añadir path del proyecto
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.queue.redis_streams import RedisStreamClient, Task, TaskPriority, TaskStatus
from src.queue.redis_event_store import RedisEventStore, StoredEvent, EventType
from src.queue.agent_tracker import AgentAvailabilityTracker, AgentInfo, AgentStatus, AgentCapability
from src.queue.worker import QueueWorker, TaskResult, ProcessingContext
from src.iovba.groups import (
    IOVBAGroupManager, IOVBAGroup, AgentProfile,
    DOMAIN_BRANDING, ROLE_BRANDING, PLATFORM_BRAND
)


class NexusRealTimeDemo:
    """Demo en tiempo real de NEXUS"""
    
    DOMAINS = ["swe", "salud", "deportes", "finanzas", "legal"]
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[RedisStreamClient] = None
        self.event_store: Optional[RedisEventStore] = None
        self.agent_tracker: Optional[AgentAvailabilityTracker] = None
        self.iovba_manager: Optional[IOVBAGroupManager] = None
        self.worker: Optional[QueueWorker] = None
        self.groups: List[IOVBAGroup] = []
        self.processed_tasks: List[Dict[str, Any]] = []
        
    async def run(self):
        """Ejecuta el demo completo"""
        self._print_header()
        
        # Inicializar
        await self._initialize()
        
        # Crear grupos
        await self._create_groups()
        
        # Publicar tareas
        await self._publish_demo_tasks()
        
        # Iniciar worker
        await self._start_worker()
        
        # Monitorear procesamiento
        await self._monitor_processing()
        
        # Mostrar resultados
        await self._show_results()
        
        # Cleanup
        await self._cleanup()
    
    def _print_header(self):
        """Imprime header del demo"""
        print(f"\n{'='*70}")
        print(f"🚀 NEXUS - Neural Execution Unified System")
        print(f"   DEMO: Procesamiento en Tiempo Real")
        print(f"{'='*70}\n")
    
    async def _initialize(self):
        """Inicializa todos los componentes"""
        print("📡 Inicializando componentes...")
        
        # Redis
        self.redis_client = RedisStreamClient(redis_url=self.redis_url, tenant_id="nexus-demo")
        await self.redis_client.connect()
        print("   ✅ Redis conectado")
        
        # Event Store
        self.event_store = RedisEventStore(redis_url=self.redis_url, tenant_id="nexus-demo")
        await self.event_store.connect()
        print("   ✅ Event Store inicializado")
        
        # Agent Tracker
        self.agent_tracker = AgentAvailabilityTracker(redis_url=self.redis_url, tenant_id="nexus-demo")
        await self.agent_tracker.connect()
        print("   ✅ Agent Tracker inicializado")
        
        # IOVBA Manager
        self.iovba_manager = IOVBAGroupManager()
        print("   ✅ IOVBA Manager inicializado")
    
    async def _create_groups(self):
        """Crea los grupos IOVBA"""
        print(f"\n🤖 Creando {len(self.DOMAINS)} grupos IOVBA...")
        
        for domain in self.DOMAINS:
            brand = DOMAIN_BRANDING.get(domain)
            if not brand:
                continue
            
            group = self.iovba_manager.create_group(
                name=f"{brand.elegant_name} Unit",
                domain=domain,
                description=brand.description
            )
            
            # Registrar agentes
            for role, agent in group.get_all_agents().items():
                if agent:
                    agent_info = AgentInfo(
                        id=agent.id,
                        name=agent.name,
                        domain=domain,
                        iovba_role=role,
                        iovba_group_id=group.id,
                        tenant_id="nexus-demo",
                        status=AgentStatus.ONLINE,
                        capabilities=[AgentCapability(name=s, score=1.0) for s in agent.skills]
                    )
                    await self.agent_tracker.register_agent(agent_info)
            
            self.groups.append(group)
            print(f"   📌 {brand.elegant_name} ({domain})")
        
        print(f"   ✅ {len(self.groups)} grupos creados con {len(self.groups) * 5} agentes")
    
    async def _publish_demo_tasks(self):
        """Publica tareas de demostración"""
        print(f"\n📝 Publicando tareas de demostración...")
        
        demo_scenarios = [
            {
                "domain": "swe",
                "role": "investigador",
                "message": "Analiza el código del módulo de autenticación y encuentra posibles vulnerabilidades",
                "priority": TaskPriority.HIGH
            },
            {
                "domain": "salud",
                "role": "observador",
                "message": "Monitorea los signos vitales del paciente y detecta anomalías",
                "priority": TaskPriority.NORMAL
            },
            {
                "domain": "finanzas",
                "role": "validador",
                "message": "Valida la transacción y verifica compliance con regulaciones",
                "priority": TaskPriority.URGENT
            },
            {
                "domain": "deportes",
                "role": "builder",
                "message": "Genera un plan de entrenamiento personalizado basado en métricas",
                "priority": TaskPriority.NORMAL
            },
            {
                "domain": "legal",
                "role": "asistente",
                "message": "Prepara documentación legal para el caso de estudio",
                "priority": TaskPriority.LOW
            },
        ]
        
        for i, scenario in enumerate(demo_scenarios):
            # Encontrar grupo
            target_group = None
            for g in self.groups:
                if g.domain == scenario["domain"]:
                    target_group = g
                    break
            
            if not target_group:
                continue
            
            task = Task(
                tenant_id="nexus-demo",
                user_id=f"demo-user-{i+1}",
                session_id=f"demo-session-{i+1}",
                iovba_group_id=target_group.id,
                iovba_role=scenario["role"],
                domain=scenario["domain"],
                task_type="chat",
                priority=scenario["priority"],
                input_data={
                    "message": scenario["message"],
                    "scenario_id": i + 1
                }
            )
            
            message_id = await self.redis_client.publish_task(task)
            
            brand = DOMAIN_BRANDING.get(scenario["domain"])
            print(f"   📤 {brand.elegant_name}/{scenario['role']}: {scenario['priority'].value}")
            print(f"      └─ '{scenario['message'][:50]}...'")
        
        print(f"   ✅ {len(demo_scenarios)} tareas publicadas")
    
    async def _start_worker(self):
        """Inicia el worker de procesamiento"""
        print(f"\n⚙️  Iniciando worker de procesamiento...")
        
        self.worker = QueueWorker(
            stream_client=self.redis_client,
            event_store=self.event_store,
            agent_tracker=self.agent_tracker,
            worker_id="demo-worker-001",
            priorities=[TaskPriority.URGENT, TaskPriority.HIGH, TaskPriority.NORMAL, TaskPriority.LOW]
        )
        
        # Configurar callbacks para visualización
        self.worker.on_task_start(self._on_task_start)
        self.worker.on_task_complete(self._on_task_complete)
        
        await self.worker.start()
        print(f"   ✅ Worker iniciado: {self.worker.worker_id}")
    
    async def _on_task_start(self, task: Task, context: ProcessingContext):
        """Callback cuando inicia una tarea"""
        brand = DOMAIN_BRANDING.get(task.domain, DOMAIN_BRANDING["custom"])
        
        print(f"\n{'─'*60}")
        print(f"🔄 INICIANDO TAREA")
        print(f"{'─'*60}")
        print(f"   ID: {task.id[:16]}...")
        print(f"   Grupo: {brand.elegant_name}")
        print(f"   Rol: {task.iovba_role}")
        print(f"   Prioridad: {task.priority.value}")
        print(f"   Usuario: {task.user_id}")
        print(f"   Mensaje: {task.input_data.get('message', 'N/A')[:60]}...")
        print(f"{'─'*60}")
    
    async def _on_task_complete(self, task: Task, context: ProcessingContext):
        """Callback cuando completa una tarea"""
        self.processed_tasks.append({
            "task_id": task.id,
            "domain": task.domain,
            "role": task.iovba_role,
            "result": context.result.value,
            "duration_ms": context.duration_ms(),
            "output": context.output,
            "logs": context.logs[-5:]  # Últimos 5 logs
        })
        
        print(f"\n{'─'*60}")
        print(f"✅ TAREA COMPLETADA: {context.result.value}")
        print(f"{'─'*60}")
        print(f"   Duración: {context.duration_ms():.2f}ms")
        print(f"   Output: {json.dumps(context.output, indent=2)[:200]}...")
        
        print(f"\n   📋 LOGS DE EJECUCIÓN:")
        for log in context.logs[-5:]:
            level_icon = {"INFO": "ℹ️", "DEBUG": "🔍", "WARNING": "⚠️", "ERROR": "❌"}.get(log.get("level", "INFO"), "📌")
            print(f"      {level_icon} [{log.get('level', 'INFO')}] {log.get('message', 'N/A')}")
        print(f"{'─'*60}")
    
    async def _monitor_processing(self):
        """Monitorea el procesamiento de tareas"""
        print(f"\n⏳ Procesando tareas (esperando 15 segundos)...")
        
        for i in range(15):
            await asyncio.sleep(1)
            
            # Mostrar estado actual
            stats = self.worker.get_stats()
            agent_stats = await self.agent_tracker.get_statistics()
            
            print(f"   ⏱️  {i+1}s | Procesadas: {stats['processed_count']} | "
                  f"Fallidas: {stats['failed_count']} | "
                  f"Disponibles: {agent_stats['available_count']} | "
                  f"Ocupados: {agent_stats['busy_count']}")
            
            # Si ya procesamos todas las tareas, salir
            if stats['processed_count'] >= 5:
                print(f"\n   ✅ Todas las tareas procesadas!")
                break
    
    async def _show_results(self):
        """Muestra los resultados finales"""
        print(f"\n{'='*70}")
        print(f"📊 RESULTADOS FINALES")
        print(f"{'='*70}")
        
        # Estadísticas del worker
        stats = self.worker.get_stats()
        print(f"\n⚙️  WORKER:")
        print(f"   Total procesadas: {stats['processed_count']}")
        print(f"   Fallidas: {stats['failed_count']}")
        print(f"   Tasa de éxito: {stats['success_rate']*100:.1f}%")
        print(f"   Tiempo total: {stats['total_processing_time_ms']:.2f}ms")
        print(f"   Tiempo promedio: {stats['avg_processing_time_ms']:.2f}ms")
        
        # Estadísticas de agentes
        agent_stats = await self.agent_tracker.get_statistics()
        print(f"\n🤖 AGENTES:")
        print(f"   Total: {agent_stats['total_agents']}")
        print(f"   Disponibles: {agent_stats['available_count']}")
        print(f"   Ocupados: {agent_stats['busy_count']}")
        
        # Estadísticas de colas
        queue_stats = await self.redis_client.get_queue_stats()
        print(f"\n📬 COLAS:")
        for priority, info in queue_stats.get("streams", {}).items():
            print(f"   {priority}: {info.get('length', 0)} mensajes")
        
        # Detalles por dominio
        print(f"\n📈 POR DOMINIO:")
        domain_results = {}
        for t in self.processed_tasks:
            domain = t["domain"]
            if domain not in domain_results:
                domain_results[domain] = {"count": 0, "total_time": 0}
            domain_results[domain]["count"] += 1
            domain_results[domain]["total_time"] += t["duration_ms"]
        
        for domain, data in domain_results.items():
            brand = DOMAIN_BRANDING.get(domain, DOMAIN_BRANDING["custom"])
            print(f"   {brand.elegant_name}: {data['count']} tareas, {data['total_time']:.2f}ms total")
        
        # Eventos registrados
        events = await self.event_store.get_events(limit=10)
        print(f"\n📚 EVENTOS: {len(events)} almacenados")
        
        print(f"\n{'='*70}\n")
    
    async def _cleanup(self):
        """Limpieza final"""
        print("🧹 Limpiando...")
        
        if self.worker:
            await self.worker.stop()
        
        if self.redis_client:
            await self.redis_client.disconnect()
        
        if self.event_store:
            await self.event_store.disconnect()
        
        if self.agent_tracker:
            await self.agent_tracker.disconnect()
        
        print("   ✅ Limpieza completada")


async def main():
    """Función principal"""
    demo = NexusRealTimeDemo()
    
    try:
        await demo.run()
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrumpido por el usuario")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await demo._cleanup()


if __name__ == "__main__":
    asyncio.run(main())
