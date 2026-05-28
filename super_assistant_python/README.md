# 🧠 Super Asistente con Capital Cognitivo

Un sistema de agentes multi-agente inteligente con memoria persistente, orquestación basada en LangGraph, y capacidades de Human-in-the-Loop.

## 📋 Características Principales

### 🔄 Orquestación con LangGraph
- **StateGraph**: Flujo de estados entre agentes
- **Checkpointing**: Persistencia de estado para recuperación
- **Comandos**: Control de flujo dinámico con `Command` y `Send`
- **Paralelismo**: Ejecución paralela de tareas independientes

### 💾 Sistema de Memoria Multi-Tipo
- **Memoria de Sesión**: Contexto de conversación actual
- **Memoria Episódica**: Eventos y experiencias pasadas
- **Memoria Semántica**: Hechos y conocimiento
- **Memoria Procedural**: Habilidades y procedimientos
- **Memoria Declarativa**: Información explícita
- **Memoria de Preferencias**: Preferencias del usuario

### 🤖 Arquitectura de Agentes
- **Lead Agent**: Coordinador principal que delega tareas
- **Researcher Agent**: Investigación y búsqueda de información
- **Analyzer Agent**: Análisis de datos y generación de insights
- **Builder Agent**: Construcción e implementación de soluciones
- **Validator Agent**: Validación y control de calidad
- **Memory Keeper Agent**: Gestión del sistema de memoria
- **Security Guard Agent**: Seguridad y validación de operaciones

### 🛡️ Guardrails de Seguridad
- **Detección de Jailbreak**: Previene intentos de bypass
- **Seguridad de Contenido**: Filtra contenido inapropiado
- **Enmascaramiento de PII**: Protege datos sensibles
- **Detección de Inyección**: SQL, XSS, código

### 👤 Human-in-the-Loop (HITL)
- Aprobación de operaciones sensibles
- Input humano durante la ejecución
- Intervención para decisiones críticas

### 🔧 Sistema de Skills
- Skills locales y remotas
- Registro dinámico
- Integración con LangChain tools

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                    Super Assistant                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   FastAPI    │    │     CLI      │    │   SDK        │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         │                   │                   │           │
│         └───────────────────┼───────────────────┘           │
│                             │                               │
│                    ┌────────▼────────┐                      │
│                    │  Orchestrator   │                      │
│                    │  (LangGraph)    │                      │
│                    └────────┬────────┘                      │
│                             │                               │
│         ┌───────────────────┼───────────────────┐           │
│         │                   │                   │           │
│  ┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐    │
│  │ Lead Agent  │    │   Memory    │    │  Guardrails │    │
│  │ (Supervisor)│    │   System    │    │   Manager   │    │
│  └──────┬──────┘    └─────────────┘    └─────────────┘    │
│         │                                                   │
│    ┌────┴────┬────────┬────────┬────────┬────────┐         │
│    ▼         ▼        ▼        ▼        ▼        ▼         │
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐     │
│ │Research│ │Analyst│ │Builder│ │Validator│ │Memory│ │Security│   │
│ │  er   │ │       │ │       │ │         │ │Keeper│ │ Guard │   │
│ └──────┘ └──────┘ └──────┘ └─────────┘ └──────┘ └──────┘     │
│                                                             │
│                    ┌────────────────┐                       │
│                    │  Skill Registry │                       │
│                    │  (Local/Remote) │                       │
│                    └────────────────┘                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 📦 Instalación

```bash
# Clonar el repositorio
cd /home/z/my-project/super_assistant_python

# Crear entorno virtual
python -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

## 🚀 Uso Rápido

### Uso Básico

```python
from super_assistant import SuperAssistant

# Crear instancia
assistant = SuperAssistant()

# Chat simple
response = await assistant.chat("¿Cuál es la capital de Francia?")
print(response.content)
```

### Con Memoria Personalizada

```python
from super_assistant import SuperAssistant, create_memory_system

# Crear sistema de memoria
memory = create_memory_system(backend="mem0")

# Crear asistente con memoria personalizada
assistant = SuperAssistant(memory_backend="mem0")

# Almacenar preferencia
await assistant.remember(
    content="El usuario prefiere respuestas cortas",
    memory_type="preference",
    user_id="user_123"
)

# Recuperar memorias
memories = await assistant.recall(
    query="preferencias del usuario",
    user_id="user_123"
)
```

### Con Skills Personalizadas

```python
from super_assistant import SuperAssistant, BaseSkill, SkillDefinition

# Crear skill personalizada
class MyCustomSkill(BaseSkill):
    def _get_default_definition(self):
        return SkillDefinition(
            name="custom_skill",
            description="Mi skill personalizada"
        )
    
    async def execute(self, parameters, context):
        return {"result": "Ejecutado!"}

# Registrar skill
assistant = SuperAssistant()
assistant.register_skill(MyCustomSkill())

# Ejecutar skill
result = await assistant.execute_skill("custom_skill", {})
```

### API REST

```bash
# Iniciar servidor
cd /home/z/my-project/super_assistant_python
uvicorn api.main:app --reload

# Chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hola, ¿cómo estás?"}'

# Listar skills
curl http://localhost:8000/skills

# Buscar en memoria
curl -X POST http://localhost:8000/memory/search \
  -H "Content-Type: application/json" \
  -d '{"query": "preferencias", "top_k": 5}'
```

## 📁 Estructura del Proyecto

```
super_assistant_python/
├── __init__.py              # Punto de entrada principal
├── config/
│   └── settings.py          # Configuración central
├── core/
│   └── models.py            # Modelos de datos
├── agents/
│   └── base.py              # Agentes especializados
├── orchestration/
│   └── graph.py             # Grafo de LangGraph
├── memory/
│   └── memory_system.py     # Sistema de memoria
├── security/
│   └── guardrails.py        # Guardrails de seguridad
├── skills/
│   └── registry.py          # Registro de skills
├── hitl/
│   └── hitl_system.py       # Human-in-the-Loop
├── api/
│   └── main.py              # API FastAPI
├── repos/                   # Repositorios clonados
│   ├── langchain/
│   ├── langgraph/
│   ├── NeMo-Agent-Toolkit/
│   ├── mem0/
│   └── ...
├── requirements.txt
└── README.md
```

## 🔧 Configuración

### Variables de Entorno

```bash
# .env
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
NVIDIA_API_KEY=your_key

# Configuración de memoria
MEMORY_BACKEND=mem0
MEM0_API_KEY=your_key

# Configuración de LLM
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview
LLM_TEMPERATURE=0.7
```

### Configuración Programática

```python
from super_assistant import Settings, LLMConfig, MemoryConfig

settings = Settings(
    llm=LLMConfig(
        provider="openai",
        model_name="gpt-4-turbo-preview",
        temperature=0.7
    ),
    memory=MemoryConfig(
        backend="mem0"
    )
)

assistant = SuperAssistant(settings=settings)
```

## 🧪 Testing

```bash
# Ejecutar tests
pytest tests/

# Con coverage
pytest tests/ --cov=super_assistant --cov-report=html
```

## 📊 Flujo de Ejecución

1. **Entrada del Usuario** → Guardrails de Input
2. **Clasificación de Intención** → Determinar tipo de tarea
3. **Supervisor** → Decidir qué agente usar
4. **Ejecución de Agente** → Realizar tarea específica
5. **Validación** → Verificar resultados
6. **HITL** (si es necesario) → Solicitar aprobación humana
7. **Respuesta** → Guardrails de Output
8. **Memoria** → Almacenar interacción

## 🤝 Integraciones

### LangChain / LangGraph
- Orquestación principal
- Tool calling
- Checkpointing

### Mem0
- Sistema de memoria persistente
- Entity extraction
- Vector search

### NeMo Guardrails
- Input/output validation
- Safety rails

### NVIDIA NIM
- LLM inference optimizado
- Modelos de NVIDIA

## 📝 Licencia

MIT License

## 🙋 Soporte

Para issues y feature requests, crear un issue en el repositorio.
