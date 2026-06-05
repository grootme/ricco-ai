# RICCO AI - Entidad Relación Diagrama

## Arquitectura Consolidada

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           SRC/SHARED (Núcleo OCP)                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐    │
│  │     ENUMS        │     │    REGISTRY      │     │      DATA        │    │
│  ├──────────────────┤     ├──────────────────┤     ├──────────────────┤    │
│  │ AIProviderType   │     │ EntityRegistry   │     │ skills.json      │    │
│  │ AgentType        │     │ RegistryEntry    │     │ blueprints.json  │    │
│  │ MCPCategory      │     │ GlobalRegistry   │     │                  │    │
│  │ TransportType    │     │                  │     │ (OCP-Compliant)  │    │
│  │ SkillCategory    │     │ (Single Source   │     │                  │    │
│  │ BlueprintType    │     │  of Truth)       │     │                  │    │
│  │ ...              │     │                  │     │                  │    │
│  └────────┬─────────┘     └────────┬─────────┘     └────────┬─────────┘    │
│           │                        │                        │               │
└───────────┼────────────────────────┼────────────────────────┼───────────────┘
            │                        │                        │
            ▼                        ▼                        ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DOMINIOS                                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │   CORE/          │  │   MCP/           │  │   BLUEPRINTS/    │          │
│  ├──────────────────┤  ├──────────────────┤  ├──────────────────┤          │
│  │ protocols.py     │  │ registry/        │  │ base.py          │          │
│  │ container.py     │  │  ├─skill_registry│  │ registry.py      │          │
│  │ agent_profile.py │  │  ├─tool_registry │  │ aiq.py           │          │
│  │                  │  │  └─server_registry│  │ rag.py           │          │
│  │ (Importa desde   │  │                  │  │ video_search.py  │          │
│  │  shared/enums)   │  │ (Carga desde     │  │ ...              │          │
│  │                  │  │  shared/data)    │  │ (19 blueprints)  │          │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘          │
│                                                                             │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │   SCHEMAS/       │  │   AI_PROVIDERS/  │  │   SERVICES/      │          │
│  ├──────────────────┤  ├──────────────────┤  ├──────────────────┤          │
│  │ config_schemas.py│  │ openrouter_      │  │ context_engine.py│          │
│  │ agent_config.py  │  │   provider.py    │  │ session_service  │          │
│  │                  │  │ anthropic_       │  │ agent_service    │          │
│  │ (Importa desde   │  │   provider.py    │  │                  │          │
│  │  shared/enums)   │  │ ...              │  │                  │          │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Entidades Principales

### 1. ENUMS (src/shared/enums.py)

| Enum | Valores | Uso |
|------|---------|-----|
| AIProviderType | OPENAI, ANTHROPIC, GOOGLE, LOCAL, OPENROUTER | Proveedores de IA |
| AgentType | LLM, A2A, SEQUENTIAL, PARALLEL, LOOP, WORKFLOW, TASK, ORCHESTRATOR, COMMERCE, HEALTH, etc. | Tipos de agentes |
| MCPCategory | FILESYSTEM, DATABASE, WEB, AI, FINANCE, RICCO, DEVOPS, MONITORING, DOCUMENTS, PRODUCTIVITY | Categorías MCP |
| TransportType | STDIO, HTTP, GRPC, WEBSOCKET | Transporte MCP |
| SkillCategory | DOCUMENT, VISUALIZATION, AI, BLUEPRINT, COMMUNICATION, DATA, DEVELOPMENT, PRODUCTIVITY, RESEARCH, FINANCE, INDUSTRIAL | Categorías de skills |
| BlueprintType | AIQ_RESEARCH, RAG, VIDEO_SEARCH, DATA_FLYWHEEL, DIGITAL_HUMAN, HEALTHCARE, RETAIL_COMMERCE, etc. (19 tipos) | Tipos de blueprints |
| BlueprintStatus | PENDING, RUNNING, COMPLETED, FAILED, CANCELLED | Estado de ejecución |

### 2. REGISTRY (src/shared/registry.py)

```
EntityRegistry<T>
├── _entities: Dict[str, RegistryEntry]
├── _by_category: Dict[str, List[str]]
├── _by_tag: Dict[str, List[str>]
├── _hooks: Dict[str, List[Callable]]
├── register(entry: RegistryEntry) -> None
├── unregister(entity_id: str) -> bool
├── get(entity_id: str) -> Optional[RegistryEntry]
├── list_by_category(category: str) -> List[RegistryEntry]
├── search(query: str) -> List[RegistryEntry]
└── load_from_config(config_path: Path) -> int

GlobalRegistry (Singleton)
├── skills: EntityRegistry
├── tools: EntityRegistry
├── servers: EntityRegistry
├── agents: EntityRegistry
├── blueprints: EntityRegistry
└── components: EntityRegistry
```

### 3. DATA (src/shared/data/)

#### skills.json (24 skills)
```json
{
  "entity_type": "skill",
  "entities": [
    {
      "id": "aiq-blueprint",
      "name": "AI-Q Research Agent",
      "category": "research",
      "tags": ["nvidia", "research", "agents"],
      "metadata": { "tools": [...] }
    }
  ]
}
```

#### blueprints.json (19 blueprints)
```json
{
  "entity_type": "blueprint",
  "entities": [
    {
      "id": "aiq",
      "name": "AI-Q Research Agent",
      "category": "research",
      "metadata": {
        "module": "src.blueprints.aiq",
        "class": "AIQBlueprint",
        "skills": ["aiq-blueprint"]
      }
    }
  ]
}
```

## Relaciones

```
                    ┌─────────────┐
                    │   ENUMS     │
                    │ (shared/)   │
                    └──────┬──────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           ▼               ▼               ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │ PROTOCOLS   │ │  SCHEMAS    │ │ BLUEPRINTS  │
    │ (core/)     │ │ (schemas/)  │ │ (blueprints/)│
    └─────────────┘ └─────────────┘ └─────────────┘
           │               │               │
           └───────────────┼───────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  REGISTRY   │
                    │ (shared/)   │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │    DATA     │
                    │ (*.json)    │
                    └─────────────┘
```

## Principios Aplicados

1. **ELIMINAR antes de CREAR**: Se eliminaron 147 enums duplicados
2. **CONSOLIDAR antes de DIVIDIR**: Single source of truth en src/shared/
3. **OCP Extendido**: Datos en configuración JSON, no hardcodeados
4. **Corrección Local → Emergencia Global**: Cada módulo respeta los 4 DNA

## Métricas

| Métrica | Antes | Después |
|---------|-------|---------|
| Enums duplicados | 147 | 0 (consolidados) |
| Skills hardcodeados | 35+ | 0 (JSON config) |
| Blueprints hardcodeados | 7 | 0 (JSON config) |
| Archivos modificados | - | 6 |
| Nuevos archivos | - | 5 |
| Tests pasando | 97 | 97 (100%) |
