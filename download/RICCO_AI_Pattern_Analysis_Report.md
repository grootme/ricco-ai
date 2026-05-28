# RICCO-AI: Análisis de Patrones y Plan de Refactorización

**Versión:** 1.0 — Fase F1 Nivel L1  
**Fecha:** 2026-05-20  
**Framework:** RICCO Pattern Framework (5 Niveles)

---

## Resumen Ejecutivo

Este documento aplica el **Framework RICCO de Patrones** al proyecto ricco-ai, analizando los patrones actuales, identificando anti-patrones (especialmente violaciones del principio OCP), y proponiendo una arquitectura basada en los **4 ADN irreducibles** de RICCO:

1. **Guarded Lifecycle** — Validar → Ejecutar → Notificar → Persistir
2. **Registry-Driven Architecture** — Toda configuración desde registros
3. **Event-Driven Consistency** — Coordinación mediante eventos
4. **Resilience-Aware Architecture** — Protección en múltiples capas

---

## 1. Análisis de Anti-Patrones Identificados

### 1.1 Violaciones del Principio OCP (Open/Closed)

El código actual viola el OCP de SOLID en múltiples ubicaciones:

| Archivo | Anti-Patrón | Impacto |
|---------|-------------|---------|
| `route.ts` | `IOVBA_DOMAINS` hardcodeado | Agregar dominio = modificar código |
| `route.ts` | `IOVBA_ROLES` hardcodeado | Agregar rol = modificar código |
| `route.ts` | `domainKeywords` hardcodeado | Nuevo dominio = nuevo if/else |
| `groups.py` | `DOMAIN_BRANDING` diccionario estático | Sin extensibilidad dinámica |
| `groups.py` | `ROLE_BRANDING` diccionario estático | Sin extensibilidad dinámica |
| `groups.py` | `mcp_map` hardcodeado | MCP servers fijos por dominio |
| `nexus_super_agent.py` | `DOMAIN_KEYWORDS` hardcodeado | Detección de dominio rígida |

### 1.2 Código Problemático Identificado

#### Problema 1: Enums disfrazados como Literal Types

```typescript
// ANTI-PATRÓN: Viola OCP
const IOVBA_DOMAINS = {
  CODEX: { name: 'CODEX', ... },
  VITALIS: { name: 'VITALIS', ... },
  // Agregar nuevo dominio = modificar este código
}
```

```python
# ANTI-PATRÓN: Viola OCP
IOVBADomain = Literal[
    "swe", "salud", "deportes", ...
]
```

#### Problema 2: Diccionarios hardcodeados

```python
# ANTI-PATRÓN: Configuración hardcodeada
DOMAIN_BRANDING: Dict[IOVBADomain, IOVBADomainBrand] = {
    "swe": IOVBADomainBrand(...),
    "salud": IOVBADomainBrand(...),
    # Agregar nuevo dominio = modificar este diccionario
}
```

#### Problema 3: Keywords hardcodeadas

```python
# ANTI-PATRÓN: Lógica de detección hardcodeada
DOMAIN_KEYWORDS: Dict[IOVBADomain, List[str]] = {
    "swe": ["código", "programming", ...],
    # Agregar nuevo dominio = modificar este diccionario
}
```

---

## 2. Patrones RICCO a Aplicar

### 2.1 Nivel 1: Patrones Individuales

Se aplicarán los siguientes patrones del **Nivel 1 RICCO**:

| Patrón | Aplicación | Beneficio |
|--------|------------|-----------|
| **Registry Pattern** | AgentRegistry para dominios/roles | Extensibilidad sin modificar código |
| **Strategy Pattern** | DomainStrategy para comportamiento | Polimorfismo por dominio |
| **Specification Pattern** | Spec para validaciones | Composición de validaciones |
| **Factory Pattern** | AgentFactory para creación | Creación dinámica de agentes |
| **Singleton Pattern** | Registry como singleton | Acceso global consistente |
| **Observer Pattern** | EventBus para coordinación | Desacoplamiento entre componentes |
| **Builder Pattern** | AgentBuilder para perfiles | Construcción fluida de agentes |

### 2.2 Nivel 2: Meta-Patrones

Se implementará el **Meta-Patrón Universal RICCO**:

**Spec-Gated State Reactive**
```
Specification → State Machine → Observer → EventBus
     ↓              ↓              ↓           ↓
  Validar      Transicionar    Notificar   Persistir
```

### 2.3 Nivel 3: ADN Irreducible

La arquitectura se basará en los **4 ADN**:

1. **Guarded Lifecycle**: Toda operación de agente será validada
2. **Registry-Driven**: Toda configuración vendrá de registros
3. **Event-Driven**: Coordinación mediante EventBus
4. **Resilience-Aware**: Manejo de errores en cada capa

---

## 3. Arquitectura Propuesta

### 3.1 Estructura de Archivos

```
lib/
├── registry/
│   ├── domain-registry.ts       # Registry para dominios
│   ├── role-registry.ts         # Registry para roles
│   ├── agent-registry.ts        # Registry para agentes
│   └── config-loader.ts         # Carga configuraciones desde JSON/YAML
├── specifications/
│   ├── domain.spec.ts           # Spec para validar dominios
│   ├── role.spec.ts             # Spec para validar roles
│   ├── agent.spec.ts            # Spec para validar agentes
│   └── spec-composition.ts      # andSpec/orSpec/notSpec
├── strategies/
│   ├── domain-strategy.ts       # Interface de estrategia
│   ├── domain-strategies/       # Estrategias concretas por dominio
│   │   ├── codex.strategy.ts
│   │   ├── vitalis.strategy.ts
│   │   └── ...
│   └── strategy-factory.ts      # Factory de estrategias
├── events/
│   ├── event-bus.ts             # EventBus centralizado
│   ├── agent-events.ts          # Tipos de eventos de agentes
│   └── event-handlers.ts        # Handlers de eventos
├── factory/
│   ├── agent-factory.ts         # Factory de agentes
│   └── agent-builder.ts         # Builder para perfiles
└── resilience/
    ├── circuit-breaker.ts       # Circuit breaker
    ├── error-reporter.ts        # Reporte de errores
    └── retry-policy.ts          # Política de reintentos

config/
├── domains.json                 # Configuración de dominios
├── roles.json                   # Configuración de roles
├── mcp-servers.json             # Configuración de MCP servers
└── domain-keywords.json         # Keywords para detección
```

### 3.2 Diagrama de Arquitectura

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         RICCO-AI ARCHITECTURE                            │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                    REGISTRY LAYER (OCP Compliant)                │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │   │
│  │  │DomainRegistry│  │ RoleRegistry │  │AgentRegistry │           │   │
│  │  │   (JSON)     │  │   (JSON)     │  │  (Dynamic)   │           │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘           │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│  ┌─────────────────────────────────▼────────────────────────────────┐   │
│  │                    SPECIFICATION LAYER                           │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │   │
│  │  │ DomainSpec   │  │  RoleSpec    │  │ AgentSpec    │           │   │
│  │  │ (Composable) │  │ (Composable) │  │ (Composable) │           │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘           │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│  ┌─────────────────────────────────▼────────────────────────────────┐   │
│  │                    STRATEGY LAYER                                │   │
│  │  ┌──────────────────────────────────────────────────────────┐   │   │
│  │  │              DomainStrategyFactory                        │   │   │
│  │  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │   │   │
│  │  │  │CODEX    │ │VITALIS  │ │ATHLON   │ │ ...     │        │   │   │
│  │  │  │Strategy │ │Strategy │ │Strategy │ │         │        │   │   │
│  │  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘        │   │   │
│  │  └──────────────────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│  ┌─────────────────────────────────▼────────────────────────────────┐   │
│  │                    EVENT LAYER (Observer + Mediator)             │   │
│  │  ┌──────────────────────────────────────────────────────────┐   │   │
│  │  │                     EventBus                               │   │   │
│  │  │  ┌─────────────────────────────────────────────────────┐ │   │   │
│  │  │  │ agent.created | agent.updated | domain.detected    │ │   │   │
│  │  │  │ role.assigned | query.processed | error.occurred   │ │   │   │
│  │  │  └─────────────────────────────────────────────────────┘ │   │   │
│  │  └──────────────────────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│  ┌─────────────────────────────────▼────────────────────────────────┐   │
│  │                    RESILIENCE LAYER                              │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │   │
│  │  │CircuitBreaker│  │ErrorReporter │  │ RetryPolicy  │           │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘           │   │
│  └──────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Configuración Dinámica (Registry-Driven)

### 4.1 domains.json

```json
{
  "domains": [
    {
      "id": "codex",
      "name": "CODEX",
      "domain": "swe",
      "elegantName": "Codex",
      "tagline": "Architecting Digital Excellence",
      "icon": "Code",
      "color": "#3B82F6",
      "description": "Unidad de ingeniería de software",
      "keywords": ["código", "programming", "software", "desarrollo", "api", "debug"],
      "mcpServers": ["github", "docker", "filesystem", "git"]
    },
    {
      "id": "vitalis",
      "name": "VITALIS",
      "domain": "salud",
      "elegantName": "Vitalis",
      "tagline": "Advancing Healthcare Intelligence",
      "icon": "Heart",
      "color": "#EF4444",
      "description": "Unidad de salud y medicina",
      "keywords": ["salud", "health", "médico", "medical", "diagnóstico"],
      "mcpServers": ["medical-db", "hl7-fhir", "pubmed"]
    }
  ]
}
```

### 4.2 roles.json

```json
{
  "roles": [
    {
      "id": "investigador",
      "name": "INVESTIGATOR",
      "elegantName": "Investigator",
      "tagline": "Discovery & Analysis",
      "description": "Investiga profundamente y descubre insights",
      "icon": "Microscope",
      "color": "#3B82F6",
      "skills": ["research", "data-analysis", "web-search", "document-analysis"],
      "tools": ["search", "scraper", "pdf-reader", "database-query"]
    },
    {
      "id": "observador",
      "name": "OBSERVER",
      "elegantName": "Observer",
      "tagline": "Monitoring & Patterns",
      "description": "Monitorea sistemas y detecta patrones",
      "icon": "Eye",
      "color": "#F59E0B",
      "skills": ["monitoring", "pattern-recognition", "anomaly-detection"],
      "tools": ["logger", "metrics", "alerts", "dashboard"]
    }
  ]
}
```

---

## 5. Implementación de Patrones

### 5.1 Registry Pattern

```typescript
// domain-registry.ts
export interface DomainConfig {
  id: string;
  name: string;
  domain: string;
  elegantName: string;
  tagline: string;
  icon: string;
  color: string;
  description: string;
  keywords: string[];
  mcpServers: string[];
}

export class DomainRegistry {
  private static instance: DomainRegistry;
  private domains: Map<string, DomainConfig> = new Map();
  
  private constructor() {}
  
  static getInstance(): DomainRegistry {
    if (!DomainRegistry.instance) {
      DomainRegistry.instance = new DomainRegistry();
    }
    return DomainRegistry.instance;
  }
  
  register(config: DomainConfig): void {
    this.domains.set(config.id, config);
  }
  
  get(id: string): DomainConfig | undefined {
    return this.domains.get(id);
  }
  
  getAll(): DomainConfig[] {
    return Array.from(this.domains.values());
  }
  
  detectFromText(text: string): DomainConfig | undefined {
    const lowerText = text.toLowerCase();
    for (const domain of this.domains.values()) {
      if (domain.keywords.some(kw => lowerText.includes(kw))) {
        return domain;
      }
    }
    return this.domains.get('custom');
  }
}
```

### 5.2 Specification Pattern

```typescript
// spec-composition.ts
export interface Specification<T> {
  id: string;
  label: string;
  isSatisfiedBy(candidate: T): boolean;
}

export function andSpec<T>(...specs: Specification<T>[]): Specification<T> {
  return {
    id: specs.map(s => s.id).join('_and_'),
    label: specs.map(s => s.label).join(' + '),
    isSatisfiedBy(candidate: T): boolean {
      return specs.every(spec => {
        try {
          return spec.isSatisfiedBy(candidate);
        } catch {
          return false;
        }
      });
    }
  };
}

export function orSpec<T>(...specs: Specification<T>[]): Specification<T> {
  return {
    id: specs.map(s => s.id).join('_or_'),
    label: specs.map(s => s.label).join(' | '),
    isSatisfiedBy(candidate: T): boolean {
      return specs.some(spec => {
        try {
          return spec.isSatisfiedBy(candidate);
        } catch {
          return false;
        }
      });
    }
  };
}
```

### 5.3 Strategy Pattern

```typescript
// domain-strategy.ts
export interface DomainStrategy {
  domainId: string;
  processQuery(query: string, context: QueryContext): Promise<StrategyResult>;
  getSystemPrompt(): string;
  getAvailableTools(): string[];
}

export class DomainStrategyFactory {
  private strategies: Map<string, DomainStrategy> = new Map();
  
  register(strategy: DomainStrategy): void {
    this.strategies.set(strategy.domainId, strategy);
  }
  
  get(domainId: string): DomainStrategy | undefined {
    return this.strategies.get(domainId);
  }
}
```

---

## 6. Plan de Migración

### Fase 1: Configuración Dinámica (Prioridad Alta)
1. Crear archivos JSON de configuración
2. Implementar DomainRegistry y RoleRegistry
3. Migrar datos hardcodeados a JSON

### Fase 2: Specifications (Prioridad Alta)
1. Crear specs para validación de dominios
2. Crear specs para validación de roles
3. Implementar composición de specs

### Fase 3: Strategies (Prioridad Media)
1. Crear interfaz DomainStrategy
2. Implementar estrategias por dominio
3. Migrar lógica de detección a estrategias

### Fase 4: Events (Prioridad Media)
1. Implementar EventBus
2. Crear tipos de eventos
3. Conectar componentes con eventos

### Fase 5: Resilience (Prioridad Baja)
1. Implementar Circuit Breaker
2. Agregar Error Reporter
3. Configurar Retry Policy

---

## 7. Scorecard de Madurez

| Dimensión | Estado Actual | Objetivo | Gap |
|-----------|---------------|----------|-----|
| Registry-Driven | 1/5 | 5/5 | -4 |
| Specification | 0/5 | 5/5 | -5 |
| Strategy | 2/5 | 5/5 | -3 |
| Observer/Events | 1/5 | 5/5 | -4 |
| Resilience | 2/5 | 5/5 | -3 |
| OCP Compliance | 1/5 | 5/5 | -4 |
| Testability | 2/5 | 5/5 | -3 |

**Puntuación Global Actual:** 1.6/5  
**Puntuación Global Objetivo:** 5/5

---

## 8. Conclusión

La arquitectura actual de ricco-ai tiene una base sólida pero viola el principio OCP de SOLID al usar configuraciones hardcodeadas. Aplicando el **Framework RICCO de Patrones** con sus **4 ADN irreducibles**, podemos transformar el código en una arquitectura:

- **Extensible**: Agregar dominios/roles sin modificar código
- **Validada**: Specification pattern para reglas de negocio
- **Coordinada**: EventBus para comunicación entre componentes
- **Resiliente**: Múltiples capas de protección

La migración debe seguir un enfoque incremental, priorizando Registry y Specification que tienen el mayor impacto en el cumplimiento de SOLID.

---

*RICCO-AI Pattern Analysis Report — Framework RICCO Nivel 1-3*
*Generado: 2026-05-20*
