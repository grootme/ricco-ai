# NEXUS Queue System - Documentación de Arquitectura

## Resumen Ejecutivo

El sistema de colas de NEXUS implementa una arquitectura de procesamiento de tareas en tiempo real para agentes IOVBA, basada en Redis Streams y PostgreSQL.

## Decisión de Arquitectura

### Análisis Comparativo

| Tecnología | Latencia | Throughput | Complejidad | Recomendación |
|------------|----------|------------|-------------|---------------|
| Redis Streams | 0.5ms | 1.2M msg/s | Baja | ✅ Recomendado |
| RabbitMQ | 3ms | 350K msg/s | Media | Alternativa |
| Kafka | 10ms | 2M msg/s | Alta | Solo para grandes volúmenes |

**Decisión: Redis Streams** por:
- Sub-millisecond latency para activación de agentes
- Consumer Groups nativos para procesamiento paralelo
- Simple multi-tenant isolation via key namespacing
- Menor complejidad operacional

## Componentes del Sistema

### 1. RedisStreamClient (`src/queue/redis_streams.py`)

**Responsabilidades:**
- Gestión de colas con Redis Streams
- Consumer Groups para procesamiento paralelo
- Publicación y consumo de tareas
- Colas por prioridad (low, normal, high, urgent)
- Dead Letter Queue para mensajes fallidos

**Key Patterns:**
```
nexus:tenant:{tenant_id}:streams:tasks:{priority}
nexus:tenant:{tenant_id}:agents:availability
nexus:tenant:{tenant_id}:dead_letter
```

### 2. EventStore (`src/queue/event_store.py`)

**Responsabilidades:**
- Persistencia de eventos en PostgreSQL
- Event Sourcing para auditoría
- Snapshots de estado para optimización
- Replay de eventos para recuperación

**Schema:**
```sql
CREATE TABLE nexus_events (
    id UUID PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    aggregate_id VARCHAR(100) NOT NULL,
    tenant_id VARCHAR(100) NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    payload JSONB NOT NULL,
    ...
);
```

### 3. AgentAvailabilityTracker (`src/queue/agent_tracker.py`)

**Responsabilidades:**
- Tracking de disponibilidad con heartbeats
- Detección de timeout de agentes
- Scoring de carga para balanceo
- Afinidad usuario-agente para sesiones continuas

**Heartbeat TTL:** 30 segundos

### 4. AgentAssignmentEngine (`src/queue/assignment_engine.py`)

**Responsabilidades:**
- Asignación inteligente de agentes a tareas
- Múltiples estrategias de asignación
- Scoring multi-factor

**Estrategias:**
- `ROUND_ROBIN`: Rotación simple
- `LEAST_BUSY`: Menor carga actual
- `CAPABILITY_BASED`: Mejor match de capacidades
- `AFFINITY_AWARE`: Preferencia por sesiones continuas
- `HYBRID`: Multi-factor scoring (recomendado)

**Fórmula de Scoring Híbrido:**
```
Score = 0.40 × Capability + 0.35 × Load + 0.15 × Affinity + 0.10 × Performance
```

### 5. EventDispatcher (`src/queue/event_dispatcher.py`)

**Responsabilidades:**
- Entrada de eventos al sistema
- Routing a colas por prioridad
- Integración con Assignment Engine
- Múltiples fuentes de eventos

**Fuentes de Eventos:**
- CHAT: Mensajes de usuarios
- API: Llamadas directas
- WEBHOOK: Integraciones externas
- SCHEDULED: Tareas programadas
- INTERNAL: Eventos del sistema

### 6. QueueWorker (`src/queue/worker.py`)

**Responsabilidades:**
- Consumo de tareas de colas
- Procesamiento con timeout
- Retry con backoff
- Logging detallado

## Flujo de Datos

```
┌─────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Usuario   │───▶│ Event Dispatcher │───▶│ Assignment      │
│  (Chat/API) │    │                  │    │ Engine          │
└─────────────┘    └────────┬─────────┘    └────────┬────────┘
                            │                       │
                            ▼                       ▼
                   ┌─────────────────┐    ┌─────────────────┐
                   │ Redis Streams   │    │ Agent Tracker   │
                   │ (Task Queue)    │    │ (Availability)  │
                   └────────┬────────┘    └─────────────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │ Queue Worker    │
                   │ (Processing)    │
                   └────────┬────────┘
                            │
                            ▼
                   ┌─────────────────┐
                   │ Event Store     │
                   │ (PostgreSQL)    │
                   └─────────────────┘
```

## Multi-Tenant Isolation

Usamos **Key Namespacing** para aislar tenants:

```
nexus:tenant:acme-corp:streams:tasks:high
nexus:tenant:acme-corp:agents:availability
nexus:tenant:other-corp:streams:tasks:normal
```

## Escalabilidad

### Horizontal Scaling

1. **Workers**: Múltiples instancias pueden consumir del mismo Consumer Group
2. **Agentes**: Sin límite de agentes registrados por tenant
3. **Tenants**: Aislamiento completo via key namespacing

### Vertical Scaling

1. **Redis**: Cluster mode para alto throughput
2. **PostgreSQL**: Partitioning por tenant_id

## Monitoreo

### Métricas Clave

- Queue depth por prioridad
- Agent availability rate
- Task processing latency
- Assignment success rate
- Error rate en dead letter queue

### Comandos de Monitoreo

```bash
# Estado de colas
redis-cli XINFO STREAM nexus:tenant:default:streams:tasks:normal

# Agentes disponibles
redis-cli SCARD nexus:tenant:default:agents:status:online

# Eventos en PostgreSQL
SELECT event_type, COUNT(*) FROM nexus_events GROUP BY event_type;
```

## Testing

### Tests Unitarios
```bash
pytest tests/test_queue_real.py -v
```

### Demo Interactivo
```bash
python scripts/demo_queue_system.py
```

## Requisitos

- Redis 7.0+
- PostgreSQL 14+
- Python 3.10+
- redis-py (async)

## Configuración

```python
# settings.py
REDIS_URL = "redis://localhost:6379"
DATABASE_URL = "postgresql+asyncpg://user:pass@localhost/nexus"
HEARTBEAT_TIMEOUT = 30  # seconds
```

## Próximos Pasos

1. Integrar con frontend via WebSocket para real-time updates
2. Implementar circuit breaker para LLM calls
3. Agregar métricas con Prometheus
4. Implementar retry con exponential backoff
5. Agregar soporte para Kafka como alternativa
