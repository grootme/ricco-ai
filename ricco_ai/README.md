# RICCO AI

Plataforma de Agentes Cognitivos con tres pilares integrados:

## DeerFlow - Motor de Workflows
Sistema de orquestación de flujos de trabajo basado en grafos dirigidos.

## Gentle-AI - Sistema de Comportamiento
Framework para comportamientos éticos, personalidades adaptables y comunicación contextual.

## Engram - Sistema de Memoria
Almacenamiento persistente con control de versiones y búsqueda semántica.

## Estructura

```
ricco-ai/
├── __init__.py          # Integración de los tres pilares
├── deerflow/            # Motor de Workflows
│   ├── __init__.py
│   ├── core.py          # Workflow, Node, Edge, WorkflowEngine
│   ├── nodes.py         # ActionNode, DecisionNode, AgentNode, etc.
│   └── execution.py     # ExecutionContext, ExecutionResult
├── gentle-ai/           # Sistema de Comportamiento
│   ├── __init__.py
│   ├── persona.py       # Persona, PersonaConfig, PersonaType
│   ├── behavior.py      # BehaviorEngine, EthicsPolicy
│   └── adapter.py       # ResponseAdapter, AdaptiveContext
└── engram/              # Sistema de Memoria
    ├── __init__.py
    ├── vcs.py           # MemoryVCS, MemoryEntry
    ├── store.py         # EngramStore
    └── index.py         # MemoryIndex
```

## Uso Rápido

```python
from ricco_ai import DeerFlow, GentleAI, Engram

# Workflow
engine = DeerFlow.WorkflowEngine()
workflow = DeerFlow.Workflow(name="mi_proceso")

# Personalidad
persona = GentleAI.Persona(GentleAI.PersonaConfig(
    persona_type=GentleAI.PersonaType.ASSISTANT
))

# Memoria
memory = Engram.MemoryVCS()
memory.upsert("tema:importante", "Contenido a recordar")
```
