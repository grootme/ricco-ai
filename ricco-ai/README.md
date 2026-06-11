# RICCO AI

Plataforma de Agentes Cognitivos con **cuatro pilares DNA** integrados:

## 🧬 Los 4 DNA

### 1. DeerFlow - Motor de Workflows
Sistema de orquestación de flujos de trabajo basado en grafos dirigidos.

**Capacidades:**
- Definición de workflows como grafos dirigidos
- Nodos con reintentos automáticos y timeout
- Condiciones en edges para bifurcación
- Motor de ejecución asíncrono
- Validación de workflows

**Uso:**
```python
from ricco_ai.deerflow import Workflow, WorkflowEngine, Node

workflow = Workflow(name="mi_proceso", start_node="inicio")
workflow.add_node(Node(id="inicio", name="Inicio"))
workflow.add_node(Node(id="fin", name="Fin"))
workflow.add_edge("inicio", "fin")

engine = WorkflowEngine()
engine.register(workflow)
result = await engine.execute(workflow.id)
```

### 2. Gentle-AI - Sistema de Comportamiento
Framework para comportamientos éticos, personalidades adaptables y comunicación contextual.

**Capacidades:**
- Reglas de comportamiento configurables
- Políticas éticas predefinidas (honestidad, privacidad, respeto)
- Detección de contenido sensible
- Verificación de violaciones éticas
- Filtros de lenguaje ofensivo

**Uso:**
```python
from ricco_ai.gentle_ai import BehaviorEngine, EthicsPolicy

engine = BehaviorEngine(policies=[EthicsPolicy.HONESTY, EthicsPolicy.PRIVACY])
violations = engine.check_ethics("Contenido a verificar")
result = engine.evaluate({"content": "mensaje", "confidence": 0.8})
```

### 3. Engram - Sistema de Memoria
Almacenamiento persistente con control de versiones y búsqueda semántica.

**Capacidades:**
- Upsert con versionado automático
- Búsqueda semántica con FTS5
- Divulgación progresiva (compact/timeline/full)
- Relaciones entre memorias (grafo de conocimiento)
- Valor cognitivo por memoria

**Uso:**
```python
from ricco_ai.engram import EngramStore, MemoryVCS

store = EngramStore()
store.remember("proyecto:config", "Configuración importante", tags=["importante"])
results = store.recall("configuración", full_content=True)
```

### 4. Gentle-Pi - Agent Orchestration
Orquestador de agentes con gestión de personas, delegación de tareas y asignación de modelos.

**Capacidades:**
- Gestión de personas (gentleman, neutral, expert)
- Delegación inteligente de tareas
- 5 tipos de agentes (scout, worker, reviewer, context_builder, analyzer)
- Asignación de modelos por agente
- Triggers de delegación automática
- Predicción de carga de trabajo

**Uso:**
```python
from ricco_ai.gentle_pi import GentlePiOrchestrator, PersonaType, AgentType, DelegationRequest

orchestrator = GentlePiOrchestrator(persona=PersonaType.GENTLEMAN)

# Delegar tarea
result = await orchestrator.delegate(DelegationRequest(
    task_description="Analizar el módulo de autenticación",
    agent_type=AgentType.SCOUT
))

# Verificar triggers
triggers = orchestrator.check_triggers({"files_read": 10, "files_to_write": 5})
```

## 📁 Estructura

```
ricco-ai/
├── __init__.py              # Integración de los cuatro DNA
│
├── deerflow/                # DNA 1: Motor de Workflows
│   ├── __init__.py
│   ├── core.py              # Workflow, Node, Edge, WorkflowEngine
│   ├── nodes.py             # ActionNode, DecisionNode, AgentNode
│   ├── execution.py         # ExecutionContext, ExecutionResult
│   └── validator.py         # WorkflowValidator, detección de ciclos
│
├── gentle-ai/               # DNA 2: Sistema de Comportamiento
│   ├── __init__.py
│   ├── persona.py           # Persona, PersonaConfig, PersonaType
│   ├── behavior.py          # BehaviorEngine, EthicsPolicy
│   └── adapter.py           # ResponseAdapter, AdaptiveContext
│
├── engram/                  # DNA 3: Sistema de Memoria
│   ├── __init__.py
│   ├── vcs.py               # MemoryVCS, MemoryEntry, MemoryVersion
│   ├── store.py             # EngramStore
│   └── index.py             # MemoryIndex
│
└── gentle-pi/               # DNA 4: Agent Orchestration
    ├── __init__.py
    └── orchestrator.py      # GentlePiOrchestrator, DelegationRequest
```

## 🔗 Integración de DNA

Los cuatro DNA trabajan juntos de forma integrada:

```python
from ricco_ai import DeerFlow, GentleAI, Engram, GentlePi

# Crear orquestador
orchestrator = GentlePi.GentlePiOrchestrator()

# Integrar otros DNA
orchestrator.integrate_deerflow(DeerFlow.WorkflowEngine())
orchestrator.integrate_gentle_ai(GentleAI.BehaviorEngine())
orchestrator.integrate_engram(Engram.EngramStore())

# Usar el orquestador con todos los DNA conectados
result = await orchestrator.delegate(
    GentlePi.DelegationRequest(
        task_description="Tarea compleja que requiere múltiples DNA",
        agent_type=GentlePi.AgentType.WORKER
    )
)
```

## 🚀 Inicio Rápido

```python
from ricco_ai import DeerFlow, GentleAI, Engram, GentlePi

# DNA 1: Workflow
engine = DeerFlow.WorkflowEngine()
workflow = DeerFlow.Workflow(name="mi_proceso")
workflow.add_node(DeerFlow.Node(id="inicio", name="Inicio"))
engine.register(workflow)

# DNA 2: Comportamiento
behavior = GentleAI.BehaviorEngine()
violations = behavior.check_ethics("contenido a verificar")

# DNA 3: Memoria
memory = Engram.EngramStore()
memory.remember("tema:importante", "Contenido a recordar")

# DNA 4: Orquestación
orchestrator = GentlePi.GentlePiOrchestrator()
orchestrator.set_persona(GentlePi.PersonaType.GENTLEMAN)
```

## 📊 Características por DNA

| Característica | DeerFlow | Gentle-AI | Engram | Gentle-Pi |
|----------------|----------|-----------|--------|-----------|
| Async/Await | ✅ | ✅ | ✅ | ✅ |
| Type Hints | ✅ | ✅ | ✅ | ✅ |
| Tests | ⚠️ | ⚠️ | ⚠️ | ⚠️ |
| Documentación | ✅ | ✅ | ✅ | ✅ |
| Integración | ✅ | ✅ | ✅ | ✅ |

## 📦 Dependencias

- Python 3.11+
- SQLite3 (Engram)
- asyncio

## 📄 Licencia

MIT License
