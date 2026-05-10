# OpenClaw Agent SaaS - Filosofía de Diseño

## Principio Fundamental: Agentes por Configuración, No por Tipo

### ❌ Lo Incorrecto

```python
# MAL: Agentes definidos por enums rígidos
class AgentType(str, Enum):
    COMMERCE = "commerce"
    HEALTH = "health"
    FINANCE = "finance"
    LOGISTICS = "logistics"
    # ...
```

Este enfoque es **restrictivo y no escalable**. Limita lo que un agente puede ser a una lista predefinida.

### ✅ Lo Correcto

```python
# BIEN: Agentes definidos por su configuración
profile = AgentProfile(
    name="Mi Agente de Commerce",
    domain="commerce",  # Etiqueta descriptiva, NO restricción
    skills=[
        SkillRef(skill_id="search", skill_name="product_search"),
        SkillRef(skill_id="orders", skill_name="order_management"),
    ],
    mcps=[
        MCPRef(mcp_id="payments", mcp_name="payment-gateway", 
               tools=["process", "refund"]),
    ],
    prompt_context=PromptContext(
        system_prompt="You are a helpful commerce assistant...",
    ),
    memory_scope=MemoryScope(domains=["commerce", "orders", "products"]),
)
```

## ¿Por Qué Esto Es Mejor?

### 1. Flexibilidad

Un agente "commerce" NO está limitado a ser solo commerce. Puede:
- Tener skills de múltiples dominios
- Cambiar su configuración en runtime
- Evolucionar sin cambiar código

### 2. Composición Dinámica

Un agente puede ser creado combinando:
- **Skills** de diferentes áreas
- **Tools/MCP** de múltiples sistemas
- **Prompts** personalizados
- **Memoria** con dominios específicos

### 3. Descubrimiento Automático

El sistema puede **encontrar agentes capaces** basándose en sus capacidades:

```python
# Encontrar agentes que puedan procesar pagos
capable_agents = registry.find_capable_agents(
    required_skills=["payment_processing"],
    required_tools=["process_payment"],
)
```

## Conceptos Clave

### Skills vs Tools vs MCP

| Concepto | Qué Es | Ejemplo |
|----------|--------|---------|
| **Skill** | Capacidad abstracta del agente | "product_search", "sentiment_analysis" |
| **Tool** | Herramienta concreta ejecutable | "search_api", "database_query" |
| **MCP** | Servidor que provee tools | "filesystem-server", "payment-gateway" |

### ExecutionPattern ≠ AgentType

**IMPORTANTE**: Los siguientes NO son tipos de agentes:

- `LLM` - Patrón de ejecución simple
- `A2A` - Patrón de comunicación Agent-to-Agent
- `Sequential` - Patrón de composición secuencial
- `Parallel` - Patrón de composición paralela
- `Loop` - Patrón de ejecución iterativa
- `Workflow` - Patrón de flujo con nodos y edges
- `Task` - Patrón basado en tareas

Estos son **PATRONES DE EJECUCIÓN** que determinan CÓMO se ejecuta un agente, no QUÉ es el agente.

### OrchestrationRole ≠ AgentType

Los roles de orquestación:
- `LEAD` - Coordinador principal
- `SPECIALIST` - Especialista en un área
- `WORKER` - Ejecutor de tareas
- `SUPERVISOR` - Supervisor de calidad

Estos definen **RESPONSABILIDADES** en la jerarquía del swarm, no el "tipo" de agente.

## Arquitectura

```
┌─────────────────────────────────────────────────────────────────┐
│                      AGENT PROFILE                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   SKILLS    │  │    TOOLS    │  │     MCP     │            │
│  │  Qué sabe   │  │  Qué tiene  │  │  De dónde   │            │
│  │   hacer     │  │  disponible │  │   vienen    │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   PROMPT    │  │   MEMORY    │  │   DOMAIN    │            │
│  │  Cómo actúa │  │  Qué conoce │  │   Etiqueta  │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                 │
│  ┌─────────────────────────────────────────────────┐          │
│  │           EXECUTION PATTERN                      │          │
│  │   LLM | A2A | Sequential | Parallel | Workflow   │          │
│  │   (CÓMO se ejecuta, NO qué es)                   │          │
│  └─────────────────────────────────────────────────┘          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Ejemplo Completo

### Crear un Agente de Commerce

```python
from agents.profile import AgentProfileBuilder, ExecutionPattern

# Crear perfil
profile = (AgentProfileBuilder("E-Commerce Assistant")
    # Dominio (etiqueta descriptiva)
    .with_domain("commerce", sub_domains=["orders", "products", "payments"])
    
    # Skills (capacidades)
    .with_skill("product-search-v1", "product_search", proficiency=0.95)
    .with_skill("order-mgmt-v1", "order_management", proficiency=0.9)
    .with_skill("payment-v1", "payment_processing", proficiency=0.85)
    
    # Tools (herramientas directas)
    .with_tool("search_api", source="mcp")
    .with_tool("payment_api", source="mcp")
    
    # MCP Servers
    .with_mcp("payment-gateway-id", "payment-gateway", 
              tools=["process_payment", "refund", "verify"])
    .with_mcp("inventory-id", "inventory-system",
              tools=["check_stock", "reserve", "release"])
    
    # Memoria (Capital Cognitivo)
    .with_memory_domains("commerce", "orders", "products", "customers")
    
    # Comportamiento
    .with_prompt(
        system_prompt="You are a helpful e-commerce assistant...",
        role_description="Asistente de comercio electrónico",
        tone="friendly",
        behavioral_guidelines=[
            "Always verify product availability before processing orders",
            "Offer alternatives if a product is out of stock",
            "Never store complete credit card numbers",
        ]
    )
    
    # Patrón de ejecución
    .with_execution_pattern(ExecutionPattern.LLM)
    
    # Metadata
    .with_tags("commerce", "e-commerce", "customer-facing")
    .build())

# Crear agente
from agents.profile.factory import ProfileBasedAgentFactory

factory = ProfileBasedAgentFactory(memory_vcs=memory_vcs)
agent = factory.create_agent(profile)

# Usar agente
response = await agent.process({
    "query": "Busco una laptop para gaming",
})
```

### Crear un Equipo de Agentes Secuencial

```python
# Crear especialistas
researcher = (AgentProfileBuilder("Researcher")
    .with_domain("research")
    .with_skill("web_search", "web_search")
    .build())

analyst = (AgentProfileBuilder("Analyst")
    .with_domain("analysis")
    .with_skill("data_analysis", "data_analysis")
    .build())

writer = (AgentProfileBuilder("Writer")
    .with_domain("writing")
    .with_skill("content_creation", "content_creation")
    .build())

# Crear equipo secuencial
team = factory.create_sequential_team(
    name="Content Pipeline",
    agent_profiles=[researcher, analyst, writer]
)

# El equipo ejecutará: researcher → analyst → writer
```

## Beneficios de Esta Arquitectura

1. **Extensibilidad**: Nuevos dominios, skills, y tools se agregan sin modificar código existente

2. **Componibilidad**: Agentes pueden combinarse de múltiples formas

3. **Descubrimiento**: El sistema puede encontrar agentes por capacidades

4. **Evolución**: Un agente puede cambiar su configuración sin ser "recreado"

5. **Testabilidad**: Cada componente puede probarse independientemente

6. **Mantenibilidad**: Sin enums rígidos que limitan el sistema
