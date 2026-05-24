#!/usr/bin/env python3
"""
NEXUS Queue System Demo - Demo en tiempo real del sistema de colas

Este script demuestra:
1. Inicialización del sistema completo
2. Registro de agentes IOVBA
3. Dispatch de eventos de chat
4. Asignación inteligente de agentes
5. Procesamiento de tareas con logs en tiempo real
6. Multi-usuario y prioridades

Uso:
    python demo_queue_system.py

Requiere:
    - Redis corriendo en localhost:6379
    - Python 3.10+
"""

import asyncio
import json
import time
import uuid
import signal
import sys
from datetime import datetime
from typing import Optional

# Agregar path del proyecto
sys.path.insert(0, "/home/z/my-project/ecosystem/ricco-ai")

# Configurar logging para ver todo
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("nexus.demo")


# Colores para terminal
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text: str):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}  {text}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")


def print_success(text: str):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_info(text: str):
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


def print_warning(text: str):
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def print_error(text: str):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_task(text: str):
    print(f"{Colors.OKBLUE}▸ {text}{Colors.ENDC}")


class NexusDemo:
    """Demo del sistema de colas NEXUS"""
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/15",
        tenant_id: str = "demo-tenant"
    ):
        self.redis_url = redis_url
        self.tenant_id = tenant_id
        
        # Componentes
        self.client = None
        self.tracker = None
        self.engine = None
        self.dispatcher = None
        self.worker = None
        
        # Estado
        self.agents = []
        self.running = False
    
    async def initialize(self):
        """Inicializa todos los componentes"""
        print_header("INICIALIZANDO SISTEMA NEXUS")
        
        # Importar componentes
        from src.queue.redis_streams import RedisStreamClient
        from src.queue.agent_tracker import AgentAvailabilityTracker
        from src.queue.assignment_engine import AgentAssignmentEngine
        from src.queue.event_dispatcher import EventDispatcher
        from src.queue.worker import QueueWorker
        
        # Redis
        print_info("Conectando a Redis...")
        self.client = RedisStreamClient(
            redis_url=self.redis_url,
            tenant_id=self.tenant_id,
            consumer_name="demo-consumer"
        )
        await self.client.connect()
        print_success("Redis conectado")
        
        # Agent Tracker
        print_info("Iniciando Agent Tracker...")
        self.tracker = AgentAvailabilityTracker(
            redis_url=self.redis_url,
            tenant_id=self.tenant_id
        )
        await self.tracker.connect()
        print_success("Agent Tracker iniciado")
        
        # Assignment Engine
        print_info("Iniciando Assignment Engine...")
        self.engine = AgentAssignmentEngine(tracker=self.tracker)
        print_success("Assignment Engine iniciado")
        
        # Event Dispatcher
        print_info("Iniciando Event Dispatcher...")
        self.dispatcher = EventDispatcher(
            stream_client=self.client,
            assignment_engine=self.engine,
            agent_tracker=self.tracker
        )
        print_success("Event Dispatcher iniciado")
        
        # Worker
        print_info("Iniciando Queue Worker...")
        self.worker = QueueWorker(
            stream_client=self.client,
            agent_tracker=self.tracker,
            worker_id="demo-worker-001"
        )
        
        # Configurar callbacks
        async def on_task_start(task, context):
            print(f"\n{Colors.BOLD}[WORKER] Procesando tarea:{Colors.ENDC}")
            print(f"  ID: {task.id}")
            print(f"  Usuario: {task.user_id}")
            print(f"  Tipo: {task.task_type}")
            print(f"  Agente: {task.agent_id}")
        
        async def on_task_complete(task, context):
            result_color = Colors.OKGREEN if context.result.value == "success" else Colors.FAIL
            print(f"\n{result_color}[WORKER] Tarea completada:{Colors.ENDC}")
            print(f"  Resultado: {context.result.value}")
            print(f"  Duración: {context.duration_ms():.2f}ms")
            if context.output:
                print(f"  Output: {json.dumps(context.output, indent=4, ensure_ascii=False)[:200]}...")
        
        self.worker.on_task_start(on_task_start)
        self.worker.on_task_complete(on_task_complete)
        
        print_success("Queue Worker iniciado")
    
    async def register_iovba_group(self, group_id: str, domain: str = "swe"):
        """Registra un grupo IOVBA completo (5 agentes)"""
        from src.queue.agent_tracker import AgentInfo, AgentStatus
        
        print_header(f"REGISTRANDO GRUPO IOVBA: {group_id.upper()}")
        
        roles = [
            ("investigador", "INVESTIGATOR", ["research", "analysis", "data-gathering"]),
            ("observador", "OBSERVER", ["monitoring", "patterns", "anomalies"]),
            ("validador", "VALIDATOR", ["qa", "testing", "verification"]),
            ("builder", "BUILDER", ["implementation", "coding", "deployment"]),
            ("asistente", "ASSISTANT", ["coordination", "documentation", "scheduling"])
        ]
        
        domain_names = {
            "swe": "CODEX",
            "salud": "VITALIS",
            "finanzas": "APEX",
            "legal": "JUSTITIA"
        }
        
        elegant_name = domain_names.get(domain, domain.upper())
        
        for role, role_elegant, skills in roles:
            agent = AgentInfo(
                id=f"{domain}-{role}-{uuid.uuid4().hex[:8]}",
                name=f"{role_elegant} {elegant_name}",
                domain=domain,
                iovba_role=role,
                iovba_group_id=group_id,
                tenant_id=self.tenant_id,
                status=AgentStatus.ONLINE,
                capabilities=[
                    {"name": skill, "score": 0.7 + hash(skill) % 30 / 100}
                    for skill in skills
                ],
                metadata={
                    "elegant_name": f"{role_elegant} {elegant_name}",
                    "group": group_id
                }
            )
            
            await self.tracker.register_agent(agent)
            self.agents.append(agent)
            
            print_task(f"Agente registrado: {agent.name}")
            print(f"         Role: {role}")
            print(f"         Capabilities: {len(agent.capabilities)}")
        
        print_success(f"Grupo IOVBA {elegant_name} registrado con 5 agentes")
    
    async def dispatch_chat_message(
        self,
        message: str,
        user_id: str,
        role: Optional[str] = None
    ):
        """Dispatch de mensaje de chat"""
        task_id = await self.dispatcher.dispatch_chat_message(
            message=message,
            user_id=user_id,
            session_id=f"session-{user_id}",
            tenant_id=self.tenant_id,
            domain="swe",
            iovba_role=role
        )
        return task_id
    
    async def demo_single_user(self):
        """Demo: Usuario único enviando mensajes"""
        print_header("DEMO 1: USUARIO ÚNICO")
        
        # Enviar mensajes
        messages = [
            ("user-demo-1", None, "Hola, necesito ayuda con mi código Python"),
            ("user-demo-1", "investigador", "Analiza este código en busca de bugs"),
            ("user-demo-1", "builder", "Implementa una función de validación"),
        ]
        
        for user, role, message in messages:
            print_task(f"Usuario {user} envía: \"{message}\"")
            if role:
                print(f"         Rol preferido: {role}")
            
            task_id = await self.dispatcher.dispatch_chat_message(
                message=message,
                user_id=user,
                session_id=f"session-{user}",
                tenant_id=self.tenant_id,
                domain="swe",
                iovba_role=role
            )
            print_success(f"Tarea creada: {task_id[:16]}...")
            
            await asyncio.sleep(0.5)
        
        # Verificar estado
        print_info("\nEstado de agentes:")
        for agent in self.agents:
            a = await self.tracker.get_agent(agent.id)
            status = "🟢 ONLINE" if a.status.value == "online" else "🔴 BUSY"
            task = f" (task: {a.current_task_id[:8]}...)" if a.current_task_id else ""
            print(f"  {status} {a.name}{task}")
    
    async def demo_multi_user(self):
        """Demo: Múltiples usuarios simultáneos"""
        print_header("DEMO 2: MÚLTIPLES USUARIOS")
        
        users = [
            ("alice", "investigador", "Find patterns in this dataset"),
            ("bob", "builder", "Create a new API endpoint"),
            ("charlie", "validador", "Review my code changes"),
            ("diana", "observador", "Monitor system performance"),
            ("eve", "asistente", "Schedule a team meeting"),
        ]
        
        print_info(f"Enviando {len(users)} mensajes simultáneos...\n")
        
        tasks = []
        for user, role, message in users:
            print_task(f"{user} → {role}: \"{message[:30]}...\"")
            
            task_id = await self.dispatcher.dispatch_chat_message(
                message=message,
                user_id=user,
                session_id=f"session-{user}",
                tenant_id=self.tenant_id,
                domain="swe",
                iovba_role=role
            )
            tasks.append((user, task_id))
        
        await asyncio.sleep(1)
        
        # Verificar asignaciones
        print_info("\nAsignaciones:")
        for agent in self.agents:
            a = await self.tracker.get_agent(agent.id)
            if a.current_task_id:
                # Encontrar usuario
                user = next((u for u, t in tasks if t[:8] == a.current_task_id[:8]), "unknown")
                print(f"  {a.name} → Usuario: {user}")
        
        # Stats
        stats = await self.engine.get_assignment_stats()
        print_info(f"\nEstadísticas de asignación:")
        print(f"  Total asignaciones: {stats['total_assignments']}")
        print(f"  Por agente: {stats['by_agent']}")
    
    async def demo_priority_queues(self):
        """Demo: Colas con prioridades"""
        print_header("DEMO 3: COLAS POR PRIORIDAD")
        
        from src.queue.redis_streams import TaskPriority
        
        priorities = [
            (TaskPriority.LOW, "user-low", "Background task: clean temp files"),
            (TaskPriority.NORMAL, "user-normal", "Regular task: generate report"),
            (TaskPriority.HIGH, "user-high", "Important: fix critical bug"),
            (TaskPriority.URGENT, "user-urgent", "URGENT: system is down!"),
        ]
        
        for priority, user, message in priorities:
            print_task(f"Priority {priority.value.upper()}: \"{message[:30]}...\"")
            
            await self.dispatcher.dispatch_chat_message(
                message=message,
                user_id=user,
                session_id=f"session-{user}",
                tenant_id=self.tenant_id,
                domain="swe"
            )
        
        # Verificar colas
        stats = await self.client.get_queue_stats()
        print_info("\nEstado de colas:")
        for priority, info in stats.get("streams", {}).items():
            print(f"  {priority}: {info.get('length', 0)} mensajes")
    
    async def demo_user_affinity(self):
        """Demo: Afinidad usuario-agente"""
        print_header("DEMO 4: AFINIDAD USUARIO-AGENTE")
        
        # Crear usuario recurrente
        user_id = "loyal-user-001"
        
        # Resetear agentes a online
        for agent in self.agents:
            await self.tracker.set_agent_available(agent.id)
        
        # Primera interacción
        print_info(f"Primera interacción de {user_id}...")
        task_id = await self.dispatcher.dispatch_chat_message(
            message="Hola, necesito ayuda con un proyecto",
            user_id=user_id,
            session_id=f"session-{user_id}",
            tenant_id=self.tenant_id,
            domain="swe"
        )
        
        # Verificar qué agente fue asignado
        assigned_agent = None
        for agent in self.agents:
            a = await self.tracker.get_agent(agent.id)
            if a.current_task_id:
                assigned_agent = agent
                print_success(f"Asignado a: {a.name}")
                break
        
        # Liberar agente
        if assigned_agent:
            await self.tracker.set_agent_available(assigned_agent.id)
        
        await asyncio.sleep(0.5)
        
        # Segunda interacción (mismo usuario)
        print_info(f"\nSegunda interacción de {user_id}...")
        task_id = await self.dispatcher.dispatch_chat_message(
            message="Continuamos con el proyecto",
            user_id=user_id,
            session_id=f"session-{user_id}",
            tenant_id=self.tenant_id,
            domain="swe"
        )
        
        # Verificar que se asigna al mismo agente
        for agent in self.agents:
            a = await self.tracker.get_agent(agent.id)
            if a.current_task_id:
                if agent.id == assigned_agent.id:
                    print_success(f"¡Mismo agente asignado! Afinidad funcionando: {a.name}")
                else:
                    print_warning(f"Diferente agente: {a.name}")
                break
    
    async def run_worker_demo(self, duration_seconds: int = 30):
        """Ejecuta el worker procesando tareas"""
        print_header(f"WORKER EN EJECUCIÓN ({duration_seconds}s)")
        
        # Iniciar worker
        self.running = True
        worker_task = asyncio.create_task(self.worker.start())
        
        print_info("Worker iniciado. Procesando tareas...")
        print_info("Los logs de procesamiento aparecerán abajo.\n")
        
        # Publicar tareas periódicamente
        async def publish_tasks():
            counter = 0
            while self.running:
                counter += 1
                await self.dispatcher.dispatch_chat_message(
                    message=f"Tarea de prueba #{counter}",
                    user_id=f"user-{counter % 5}",
                    session_id=f"session-{counter % 5}",
                    tenant_id=self.tenant_id,
                    domain="swe"
                )
                await asyncio.sleep(2)
        
        publisher_task = asyncio.create_task(publish_tasks())
        
        # Esperar
        await asyncio.sleep(duration_seconds)
        
        # Detener
        self.running = False
        publisher_task.cancel()
        
        await self.worker.stop()
        worker_task.cancel()
        
        try:
            await worker_task
        except asyncio.CancelledError:
            pass
        
        # Stats finales
        stats = self.worker.get_stats()
        print_info("\nEstadísticas del Worker:")
        print(f"  Tareas procesadas: {stats['processed_count']}")
        print(f"  Tareas fallidas: {stats['failed_count']}")
        print(f"  Tasa de éxito: {stats['success_rate']*100:.1f}%")
        print(f"  Tiempo promedio: {stats['avg_processing_time_ms']:.2f}ms")
    
    async def cleanup(self):
        """Limpia todo"""
        print_header("LIMPIANDO")
        
        # Desregistrar agentes
        for agent in self.agents:
            await self.tracker.unregister_agent(agent.id)
            print_task(f"Agente desregistrado: {agent.name}")
        
        # Desconectar
        await self.tracker.disconnect()
        await self.client.disconnect()
        
        print_success("Limpieza completada")
    
    async def run_full_demo(self):
        """Ejecuta el demo completo"""
        print(f"\n{Colors.BOLD}{Colors.HEADER}")
        print("╔════════════════════════════════════════════════════════════════════╗")
        print("║                    NEXUS QUEUE SYSTEM DEMO                         ║")
        print("║           Neural Execution Unified System - v2.0                   ║")
        print("╚════════════════════════════════════════════════════════════════════╝")
        print(f"{Colors.ENDC}")
        
        try:
            # Inicializar
            await self.initialize()
            
            # Registrar grupo IOVBA
            await self.register_iovba_group("iovba-codex-demo", "swe")
            
            # Demos
            await self.demo_single_user()
            await asyncio.sleep(2)
            
            await self.demo_multi_user()
            await asyncio.sleep(2)
            
            # Reset agentes
            for agent in self.agents:
                await self.tracker.set_agent_available(agent.id)
            
            await self.demo_priority_queues()
            await asyncio.sleep(2)
            
            # Reset agentes
            for agent in self.agents:
                await self.tracker.set_agent_available(agent.id)
            
            await self.demo_user_affinity()
            await asyncio.sleep(2)
            
            # Reset agentes
            for agent in self.agents:
                await self.tracker.set_agent_available(agent.id)
            
            # Worker procesando
            await self.run_worker_demo(duration_seconds=20)
            
            # Stats finales
            print_header("ESTADÍSTICAS FINALES")
            
            queue_stats = await self.client.get_queue_stats()
            assignment_stats = await self.engine.get_assignment_stats()
            
            print_info("Colas:")
            print(f"  Total mensajes pendientes: {queue_stats.get('pending_messages', 0)}")
            
            print_info("\nAsignaciones:")
            print(f"  Total: {assignment_stats.get('total_assignments', 0)}")
            print(f"  Por agente: {json.dumps(assignment_stats.get('by_agent', {}), indent=4)}")
            
        except Exception as e:
            print_error(f"Error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await self.cleanup()
        
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}✓ Demo completado{Colors.ENDC}\n")


async def main():
    demo = NexusDemo()
    
    # Manejar Ctrl+C
    def signal_handler(sig, frame):
        print("\n\nDeteniendo demo...")
        demo.running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    
    await demo.run_full_demo()


if __name__ == "__main__":
    asyncio.run(main())
