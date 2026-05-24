"""
NEXUS Queue System Tests - Tests Reales en Caliente

Tests que muestran:
- Inicialización completa del sistema
- Registro de agentes
- Publicación de eventos
- Asignación de tareas
- Procesamiento con logs visibles
- Multi-usuario
- Colas y prioridades

Ejecutar con: python -m pytest tests/test_queue_real.py -v -s
"""

import asyncio
import json
import pytest
import time
import uuid
from datetime import datetime
from typing import Dict, Any

# Configurar logging para ver todo
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)

logger = logging.getLogger(__name__)


# ============================================
# FIXTURES Y CONFIGURACIÓN
# ============================================

@pytest.fixture
def redis_url():
    """URL de Redis (usar localhost para tests)"""
    return "redis://localhost:6379/15"  # DB 15 para tests


@pytest.fixture
def database_url():
    """URL de PostgreSQL para Event Store"""
    return "postgresql+asyncpg://postgres:postgres@localhost:5432/nexus_test"


@pytest.fixture
def tenant_id():
    """Tenant ID para tests"""
    return f"test-tenant-{uuid.uuid4().hex[:8]}"


# ============================================
# TEST: INICIALIZACIÓN DEL SISTEMA
# ============================================

class TestSystemInitialization:
    """Tests de inicialización del sistema de colas"""
    
    @pytest.mark.asyncio
    async def test_redis_connection(self, redis_url, tenant_id):
        """Test: Conexión a Redis"""
        print("\n" + "="*60)
        print("TEST: Redis Connection")
        print("="*60)
        
        from src.queue.redis_streams import RedisStreamClient
        
        client = RedisStreamClient(
            redis_url=redis_url,
            tenant_id=tenant_id,
            consumer_name="test-consumer"
        )
        
        print(f"Connecting to Redis: {redis_url}")
        await client.connect()
        print("✓ Connected successfully")
        
        # Verificar conexión
        stats = await client.get_queue_stats()
        print(f"Queue stats: {json.dumps(stats, indent=2, default=str)}")
        
        await client.disconnect()
        print("✓ Disconnected")
        print("="*60 + "\n")
    
    @pytest.mark.asyncio
    async def test_agent_tracker_initialization(self, redis_url, tenant_id):
        """Test: Inicialización del Agent Tracker"""
        print("\n" + "="*60)
        print("TEST: Agent Tracker Initialization")
        print("="*60)
        
        from src.queue.agent_tracker import AgentAvailabilityTracker, AgentInfo, AgentStatus
        
        tracker = AgentAvailabilityTracker(
            redis_url=redis_url,
            tenant_id=tenant_id
        )
        
        print(f"Connecting Agent Tracker...")
        await tracker.connect()
        print("✓ Connected")
        
        # Registrar un agente de prueba
        agent = AgentInfo(
            id=f"test-agent-{uuid.uuid4().hex[:8]}",
            name="Test Agent CODEX",
            domain="swe",
            iovba_role="investigador",
            iovba_group_id="test-iovba-001",
            tenant_id=tenant_id,
            status=AgentStatus.ONLINE,
            capabilities=[
                {"name": "code-review", "score": 0.9, "tags": ["python", "typescript"]},
                {"name": "debugging", "score": 0.85, "tags": ["general"]},
            ]
        )
        
        print(f"\nRegistering agent: {agent.id}")
        await tracker.register_agent(agent)
        print(f"✓ Agent registered: {agent.name}")
        
        # Verificar registro
        retrieved = await tracker.get_agent(agent.id)
        assert retrieved is not None
        print(f"✓ Agent retrieved: {retrieved.name}, status={retrieved.status.value}")
        
        # Heartbeat
        print(f"\nSending heartbeat...")
        success = await tracker.heartbeat(agent.id)
        assert success
        print("✓ Heartbeat sent")
        
        # Estadísticas
        stats = await tracker.get_statistics()
        print(f"\nTracker stats: {json.dumps(stats, indent=2)}")
        
        # Cleanup
        await tracker.unregister_agent(agent.id)
        print("✓ Agent unregistered")
        
        await tracker.disconnect()
        print("="*60 + "\n")


# ============================================
# TEST: PUBLICACIÓN Y CONSUMO DE TAREAS
# ============================================

class TestTaskPublishing:
    """Tests de publicación y consumo de tareas"""
    
    @pytest.mark.asyncio
    async def test_task_publish_and_consume(self, redis_url, tenant_id):
        """Test: Publicar y consumir una tarea"""
        print("\n" + "="*60)
        print("TEST: Task Publish and Consume")
        print("="*60)
        
        from src.queue.redis_streams import RedisStreamClient, Task, TaskPriority
        
        client = RedisStreamClient(
            redis_url=redis_url,
            tenant_id=tenant_id,
            consumer_name="test-publisher"
        )
        
        await client.connect()
        print("✓ Connected to Redis")
        
        # Crear tarea
        task = Task(
            tenant_id=tenant_id,
            user_id="user-001",
            session_id="session-001",
            domain="swe",
            iovba_role="investigador",
            task_type="chat",
            priority=TaskPriority.NORMAL,
            input_data={
                "message": "Analyze this code for potential bugs",
                "code": "def process(data):\n    return data['value']"
            },
            metadata={
                "source": "test",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        print(f"\nPublishing task: {task.id}")
        print(f"  - User: {task.user_id}")
        print(f"  - Domain: {task.domain}")
        print(f"  - Role: {task.iovba_role}")
        print(f"  - Priority: {task.priority.value}")
        
        message_id = await client.publish_task(task)
        print(f"✓ Task published with message_id: {message_id}")
        
        # Consumir tarea
        print(f"\nConsuming task...")
        messages = await client.consume_tasks(
            priority=TaskPriority.NORMAL,
            count=1,
            block_ms=5000
        )
        
        assert len(messages) > 0, "No messages received"
        
        stream_msg, retrieved_task = messages[0]
        print(f"✓ Task consumed: {retrieved_task.id}")
        print(f"  - Input message: {retrieved_task.input_data.get('message', '')[:50]}...")
        
        # Ack
        await client.ack_message(stream_msg.stream, stream_msg.id)
        print("✓ Task acknowledged")
        
        # Stats
        stats = await client.get_queue_stats()
        print(f"\nFinal queue stats: {json.dumps(stats, indent=2, default=str)}")
        
        await client.disconnect()
        print("="*60 + "\n")
    
    @pytest.mark.asyncio
    async def test_priority_queues(self, redis_url, tenant_id):
        """Test: Colas con diferentes prioridades"""
        print("\n" + "="*60)
        print("TEST: Priority Queues")
        print("="*60)
        
        from src.queue.redis_streams import RedisStreamClient, Task, TaskPriority
        
        client = RedisStreamClient(
            redis_url=redis_url,
            tenant_id=tenant_id,
            consumer_name="test-priority"
        )
        
        await client.connect()
        
        # Publicar tareas con diferentes prioridades
        priorities = [
            TaskPriority.LOW,
            TaskPriority.NORMAL,
            TaskPriority.HIGH,
            TaskPriority.URGENT
        ]
        
        tasks = []
        for priority in priorities:
            task = Task(
                tenant_id=tenant_id,
                user_id=f"user-{priority.value}",
                domain="swe",
                task_type="test",
                priority=priority,
                input_data={"priority_test": priority.value}
            )
            await client.publish_task(task)
            tasks.append(task)
            print(f"Published task with priority: {priority.value}")
        
        # Verificar que están en colas separadas
        stats = await client.get_queue_stats()
        print(f"\nQueue stats by priority:")
        for priority, info in stats.get("streams", {}).items():
            print(f"  {priority}: {info.get('length', 0)} messages")
        
        # Consumir de cada cola
        for priority in priorities:
            messages = await client.consume_tasks(priority=priority, count=1, block_ms=1000)
            if messages:
                stream_msg, task = messages[0]
                print(f"✓ Consumed from {priority.value}: task {task.id}")
                await client.ack_message(stream_msg.stream, stream_msg.id)
        
        await client.disconnect()
        print("="*60 + "\n")


# ============================================
# TEST: ASIGNACIÓN DE AGENTES
# ============================================

class TestAgentAssignment:
    """Tests del motor de asignación"""
    
    @pytest.mark.asyncio
    async def test_hybrid_assignment(self, redis_url, tenant_id):
        """Test: Asignación híbrida multi-factor"""
        print("\n" + "="*60)
        print("TEST: Hybrid Agent Assignment")
        print("="*60)
        
        from src.queue.agent_tracker import AgentAvailabilityTracker, AgentInfo, AgentStatus
        from src.queue.assignment_engine import AgentAssignmentEngine, AssignmentStrategy
        from src.queue.redis_streams import Task, TaskPriority
        
        # Inicializar tracker
        tracker = AgentAvailabilityTracker(
            redis_url=redis_url,
            tenant_id=tenant_id
        )
        await tracker.connect()
        
        # Registrar múltiples agentes
        agents = []
        roles = ["investigador", "observador", "validador", "builder", "asistente"]
        
        for i, role in enumerate(roles):
            agent = AgentInfo(
                id=f"agent-{role}-{uuid.uuid4().hex[:8]}",
                name=f"{role.upper()} CODEX",
                domain="swe",
                iovba_role=role,
                iovba_group_id="iovba-codex",
                tenant_id=tenant_id,
                status=AgentStatus.ONLINE,
                capabilities=[
                    {"name": "code-review", "score": 0.7 + i * 0.05},
                    {"name": "debugging", "score": 0.6 + i * 0.07},
                ]
            )
            await tracker.register_agent(agent)
            agents.append(agent)
            print(f"Registered agent: {agent.name} (capabilities: {len(agent.capabilities)})")
        
        # Inicializar assignment engine
        engine = AgentAssignmentEngine(
            tracker=tracker,
            strategy=AssignmentStrategy.HYBRID
        )
        
        # Crear tarea
        task = Task(
            tenant_id=tenant_id,
            user_id="user-test-001",
            session_id="session-test",
            domain="swe",
            iovba_role="investigador",  # Preferir investigador
            priority=TaskPriority.HIGH,
            input_data={"query": "Find bugs in this code"},
            metadata={"required_capabilities": ["code-review", "debugging"]}
        )
        
        print(f"\nAssigning task {task.id}...")
        print(f"  Required role: {task.iovba_role}")
        print(f"  User: {task.user_id}")
        
        # Asignar
        result = await engine.assign(
            task,
            strategy=AssignmentStrategy.HYBRID,
            required_capabilities=["code-review", "debugging"]
        )
        
        print(f"\nAssignment Result:")
        print(f"  Success: {result.success}")
        print(f"  Agent: {result.agent_id}")
        print(f"  Strategy: {result.strategy_used.value}")
        print(f"  Reason: {result.reason}")
        
        if result.scores:
            print(f"\n  Top Scores:")
            for score in result.scores[:3]:
                print(f"    - Agent {score.agent_id}: {score.total_score:.3f}")
                print(f"      Capability: {score.capability_score:.3f}")
                print(f"      Load: {score.load_score:.3f}")
                print(f"      Performance: {score.performance_score:.3f}")
        
        # Verificar que el agente está busy
        if result.success:
            agent = await tracker.get_agent(result.agent_id)
            print(f"\n  Agent status after assignment: {agent.status.value}")
        
        # Cleanup
        for agent in agents:
            await tracker.unregister_agent(agent.id)
        
        await tracker.disconnect()
        print("="*60 + "\n")
    
    @pytest.mark.asyncio
    async def test_user_affinity(self, redis_url, tenant_id):
        """Test: Afinidad usuario-agente"""
        print("\n" + "="*60)
        print("TEST: User Affinity")
        print("="*60)
        
        from src.queue.agent_tracker import AgentAvailabilityTracker, AgentInfo, AgentStatus
        from src.queue.assignment_engine import AgentAssignmentEngine, AssignmentStrategy
        from src.queue.redis_streams import Task, TaskPriority
        
        tracker = AgentAvailabilityTracker(
            redis_url=redis_url,
            tenant_id=tenant_id
        )
        await tracker.connect()
        
        # Registrar agentes
        agents = []
        for i in range(3):
            agent = AgentInfo(
                id=f"agent-{i}-{uuid.uuid4().hex[:8]}",
                name=f"Agent {i}",
                domain="swe",
                tenant_id=tenant_id,
                status=AgentStatus.ONLINE
            )
            await tracker.register_agent(agent)
            agents.append(agent)
        
        # Establecer afinidad del usuario con un agente específico
        user_id = "user-loyal-001"
        preferred_agent = agents[0]
        
        print(f"Setting affinity: user {user_id} -> agent {preferred_agent.id}")
        await tracker.update_user_affinity(preferred_agent.id, user_id, delta=0.8)
        
        # Verificar afinidad
        agent = await tracker.get_agent(preferred_agent.id)
        affinity = agent.user_affinity.get(user_id, 0)
        print(f"✓ Affinity score: {affinity:.2f}")
        
        # Asignar tarea del mismo usuario
        engine = AgentAssignmentEngine(
            tracker=tracker,
            strategy=AssignmentStrategy.AFFINITY_AWARE
        )
        
        task = Task(
            tenant_id=tenant_id,
            user_id=user_id,
            domain="swe",
            priority=TaskPriority.NORMAL,
            input_data={"query": "Continue our conversation"}
        )
        
        result = await engine.assign(task)
        
        print(f"\nAssignment result: {result.agent_id}")
        print(f"Expected: {preferred_agent.id}")
        
        assert result.agent_id == preferred_agent.id, "Should assign to preferred agent"
        print("✓ Correct assignment based on affinity")
        
        # Cleanup
        for agent in agents:
            await tracker.unregister_agent(agent.id)
        
        await tracker.disconnect()
        print("="*60 + "\n")


# ============================================
# TEST: EVENT DISPATCHER
# ============================================

class TestEventDispatcher:
    """Tests del Event Dispatcher"""
    
    @pytest.mark.asyncio
    async def test_chat_message_dispatch(self, redis_url, tenant_id):
        """Test: Dispatch de mensaje de chat"""
        print("\n" + "="*60)
        print("TEST: Chat Message Dispatch")
        print("="*60)
        
        from src.queue.redis_streams import RedisStreamClient
        from src.queue.agent_tracker import AgentAvailabilityTracker, AgentInfo, AgentStatus
        from src.queue.assignment_engine import AgentAssignmentEngine, AssignmentStrategy
        from src.queue.event_dispatcher import EventDispatcher, EventSource
        
        # Inicializar componentes
        client = RedisStreamClient(redis_url=redis_url, tenant_id=tenant_id)
        await client.connect()
        
        tracker = AgentAvailabilityTracker(redis_url=redis_url, tenant_id=tenant_id)
        await tracker.connect()
        
        # Registrar agente
        agent = AgentInfo(
            id=f"agent-chat-{uuid.uuid4().hex[:8]}",
            name="Chat Agent",
            domain="swe",
            tenant_id=tenant_id,
            status=AgentStatus.ONLINE
        )
        await tracker.register_agent(agent)
        
        # Inicializar dispatcher
        engine = AgentAssignmentEngine(tracker=tracker, strategy=AssignmentStrategy.HYBRID)
        dispatcher = EventDispatcher(
            stream_client=client,
            assignment_engine=engine,
            agent_tracker=tracker
        )
        
        # Callbacks para ver el flujo
        async def on_task_created(task):
            print(f"  [CALLBACK] Task created: {task.id}")
        
        async def on_task_assigned(task, assignment):
            print(f"  [CALLBACK] Task assigned to: {assignment.agent_id}")
        
        dispatcher.on_task_created(on_task_created)
        dispatcher.on_task_assigned(on_task_assigned)
        
        # Dispatch mensaje de chat
        print("\nDispatching chat message...")
        task_id = await dispatcher.dispatch_chat_message(
            message="Hello, I need help with my Python code",
            user_id="user-chat-001",
            session_id="session-chat-001",
            tenant_id=tenant_id,
            domain="swe"
        )
        
        print(f"✓ Task created: {task_id}")
        
        # Verificar estado de colas
        status = await dispatcher.get_queue_status()
        print(f"\nQueue status: {json.dumps(status, indent=2, default=str)}")
        
        # Cleanup
        await tracker.unregister_agent(agent.id)
        await tracker.disconnect()
        await client.disconnect()
        print("="*60 + "\n")
    
    @pytest.mark.asyncio
    async def test_multi_user_dispatch(self, redis_url, tenant_id):
        """Test: Múltiples usuarios con tareas simultáneas"""
        print("\n" + "="*60)
        print("TEST: Multi-User Dispatch")
        print("="*60)
        
        from src.queue.redis_streams import RedisStreamClient, TaskPriority
        from src.queue.agent_tracker import AgentAvailabilityTracker, AgentInfo, AgentStatus
        from src.queue.assignment_engine import AgentAssignmentEngine
        from src.queue.event_dispatcher import EventDispatcher
        
        # Inicializar
        client = RedisStreamClient(redis_url=redis_url, tenant_id=tenant_id)
        await client.connect()
        
        tracker = AgentAvailabilityTracker(redis_url=redis_url, tenant_id=tenant_id)
        await tracker.connect()
        
        # Registrar 3 agentes
        agents = []
        for i in range(3):
            agent = AgentInfo(
                id=f"agent-{i}-{uuid.uuid4().hex[:8]}",
                name=f"Agent {i}",
                domain="swe",
                iovba_role=["investigador", "builder", "asistente"][i],
                tenant_id=tenant_id,
                status=AgentStatus.ONLINE
            )
            await tracker.register_agent(agent)
            agents.append(agent)
        
        print(f"Registered {len(agents)} agents")
        
        engine = AgentAssignmentEngine(tracker=tracker)
        dispatcher = EventDispatcher(
            stream_client=client,
            assignment_engine=engine,
            agent_tracker=tracker
        )
        
        # Múltiples usuarios enviando mensajes
        users = ["user-1", "user-2", "user-3", "user-4", "user-5"]
        task_ids = []
        
        print("\nDispatching messages from 5 users...")
        for i, user_id in enumerate(users):
            task_id = await dispatcher.dispatch_chat_message(
                message=f"Request #{i+1} from {user_id}",
                user_id=user_id,
                session_id=f"session-{user_id}",
                tenant_id=tenant_id,
                domain="swe"
            )
            task_ids.append(task_id)
            print(f"  User {user_id} -> Task {task_id[:8]}...")
        
        # Verificar asignaciones
        print("\nVerifying assignments...")
        for agent in agents:
            a = await tracker.get_agent(agent.id)
            print(f"  Agent {agent.name}: status={a.status.value}, task={a.current_task_id or 'none'}")
        
        # Stats
        stats = await engine.get_assignment_stats()
        print(f"\nAssignment stats: {json.dumps(stats, indent=2)}")
        
        # Cleanup
        for agent in agents:
            await tracker.unregister_agent(agent.id)
        await tracker.disconnect()
        await client.disconnect()
        print("="*60 + "\n")


# ============================================
# TEST: WORKER PROCESSING
# ============================================

class TestWorkerProcessing:
    """Tests del Worker de procesamiento"""
    
    @pytest.mark.asyncio
    async def test_worker_processing_with_logs(self, redis_url, tenant_id):
        """Test: Worker procesando tareas con logs visibles"""
        print("\n" + "="*60)
        print("TEST: Worker Processing with Logs")
        print("="*60)
        
        from src.queue.redis_streams import RedisStreamClient, Task, TaskPriority
        from src.queue.agent_tracker import AgentAvailabilityTracker, AgentInfo, AgentStatus
        from src.queue.assignment_engine import AgentAssignmentEngine
        from src.queue.event_dispatcher import EventDispatcher
        from src.queue.worker import QueueWorker, ProcessingContext
        
        # Inicializar todo
        client = RedisStreamClient(redis_url=redis_url, tenant_id=tenant_id)
        await client.connect()
        
        tracker = AgentAvailabilityTracker(redis_url=redis_url, tenant_id=tenant_id)
        await tracker.connect()
        
        # Registrar agente
        agent = AgentInfo(
            id=f"worker-agent-{uuid.uuid4().hex[:8]}",
            name="Worker Agent",
            domain="swe",
            tenant_id=tenant_id,
            status=AgentStatus.ONLINE
        )
        await tracker.register_agent(agent)
        
        engine = AgentAssignmentEngine(tracker=tracker)
        dispatcher = EventDispatcher(
            stream_client=client,
            assignment_engine=engine,
            agent_tracker=tracker
        )
        
        # Crear worker
        worker = QueueWorker(
            stream_client=client,
            agent_tracker=tracker,
            worker_id="test-worker-001"
        )
        
        # Callbacks para ver el flujo
        async def on_task_start(task, context):
            print(f"\n  [WORKER] Starting task: {task.id}")
            print(f"           Type: {task.task_type}")
            print(f"           User: {task.user_id}")
        
        async def on_task_complete(task, context):
            print(f"\n  [WORKER] Completed task: {task.id}")
            print(f"           Result: {context.result.value}")
            print(f"           Duration: {context.duration_ms():.2f}ms")
            if context.output:
                print(f"           Output: {json.dumps(context.output, indent=12)}")
        
        worker.on_task_start(on_task_start)
        worker.on_task_complete(on_task_complete)
        
        # Publicar tarea
        print("\nPublishing task...")
        task_id = await dispatcher.dispatch_chat_message(
            message="Test message for worker processing",
            user_id="user-worker-test",
            session_id="session-worker",
            tenant_id=tenant_id,
            domain="swe"
        )
        print(f"Task published: {task_id}")
        
        # Iniciar worker y procesar
        print("\nStarting worker...")
        worker_task = asyncio.create_task(worker.start())
        
        # Esperar procesamiento
        print("Waiting for processing (10 seconds)...")
        await asyncio.sleep(10)
        
        # Detener worker
        await worker.stop()
        worker_task.cancel()
        try:
            await worker_task
        except asyncio.CancelledError:
            pass
        
        # Stats
        stats = worker.get_stats()
        print(f"\nWorker stats: {json.dumps(stats, indent=2)}")
        
        # Cleanup
        await tracker.unregister_agent(agent.id)
        await tracker.disconnect()
        await client.disconnect()
        print("="*60 + "\n")


# ============================================
# TEST: FLUJO COMPLETO
# ============================================

class TestCompleteFlow:
    """Tests del flujo completo end-to-end"""
    
    @pytest.mark.asyncio
    async def test_complete_flow(self, redis_url, tenant_id):
        """Test: Flujo completo desde evento hasta procesamiento"""
        print("\n" + "="*60)
        print("TEST: Complete Flow - Event to Processing")
        print("="*60)
        
        from src.queue.redis_streams import RedisStreamClient
        from src.queue.agent_tracker import AgentAvailabilityTracker, AgentInfo, AgentStatus
        from src.queue.assignment_engine import AgentAssignmentEngine
        from src.queue.event_dispatcher import EventDispatcher
        from src.queue.worker import QueueWorker
        
        print("\n[1/5] Initializing components...")
        
        # Redis
        client = RedisStreamClient(redis_url=redis_url, tenant_id=tenant_id)
        await client.connect()
        print("  ✓ Redis connected")
        
        # Agent Tracker
        tracker = AgentAvailabilityTracker(redis_url=redis_url, tenant_id=tenant_id)
        await tracker.connect()
        print("  ✓ Agent Tracker connected")
        
        print("\n[2/5] Registering IOVBA group (5 agents)...")
        
        # Registrar grupo IOVBA completo
        roles = ["investigador", "observador", "validador", "builder", "asistente"]
        agents = []
        
        for role in roles:
            agent = AgentInfo(
                id=f"codex-{role}-{uuid.uuid4().hex[:8]}",
                name=f"{role.upper()} CODEX",
                domain="swe",
                iovba_role=role,
                iovba_group_id="iovba-codex-001",
                tenant_id=tenant_id,
                status=AgentStatus.ONLINE,
                capabilities=[
                    {"name": "code-review", "score": 0.8},
                    {"name": "debugging", "score": 0.75},
                    {"name": "documentation", "score": 0.7},
                ]
            )
            await tracker.register_agent(agent)
            agents.append(agent)
            print(f"  ✓ {agent.name} registered")
        
        print("\n[3/5] Initializing Assignment Engine and Dispatcher...")
        
        engine = AgentAssignmentEngine(tracker=tracker)
        dispatcher = EventDispatcher(
            stream_client=client,
            assignment_engine=engine,
            agent_tracker=tracker
        )
        print("  ✓ Components initialized")
        
        print("\n[4/5] Dispatching events...")
        
        # Multiple events
        events = [
            ("user-1", "investigador", "Find security vulnerabilities in this code"),
            ("user-2", "builder", "Implement a REST API endpoint"),
            ("user-3", "validador", "Review this pull request"),
        ]
        
        task_ids = []
        for user, role, message in events:
            task_id = await dispatcher.dispatch_chat_message(
                message=message,
                user_id=user,
                session_id=f"session-{user}",
                tenant_id=tenant_id,
                domain="swe",
                iovba_role=role
            )
            task_ids.append(task_id)
            print(f"  ✓ Event from {user} (role: {role}) -> Task {task_id[:8]}...")
        
        print("\n[5/5] Verifying assignments...")
        
        # Verificar estado de agentes
        for agent in agents:
            a = await tracker.get_agent(agent.id)
            status_icon = "🟢" if a.status == AgentStatus.ONLINE else "🔴"
            task_info = f"task: {a.current_task_id[:8]}..." if a.current_task_id else "idle"
            print(f"  {status_icon} {a.name}: {a.status.value} ({task_info})")
        
        # Stats finales
        queue_stats = await dispatcher.get_queue_status()
        assignment_stats = await engine.get_assignment_stats()
        
        print(f"\nQueue Stats:")
        print(f"  Total pending: {queue_stats.get('pending_messages', 0)}")
        print(f"  Available agents: {queue_stats.get('agents', {}).get('available_count', 0)}")
        print(f"  Busy agents: {queue_stats.get('agents', {}).get('busy_count', 0)}")
        
        print(f"\nAssignment Stats:")
        print(f"  Total assignments: {assignment_stats.get('total_assignments', 0)}")
        
        # Cleanup
        print("\nCleaning up...")
        for agent in agents:
            await tracker.unregister_agent(agent.id)
        await tracker.disconnect()
        await client.disconnect()
        
        print("\n✓ Complete flow test finished successfully!")
        print("="*60 + "\n")


if __name__ == "__main__":
    # Ejecutar tests directamente
    pytest.main([__file__, "-v", "-s", "--tb=short"])
