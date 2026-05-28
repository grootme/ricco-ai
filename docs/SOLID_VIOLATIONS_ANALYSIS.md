# Análisis de Violaciones SOLID en RICCO-AI

## Código Problemático Identificado

### Archivos con Violaciones:
1. `/src/lib/api/client.ts` - Líneas 32-65
2. `/ecosystem/ricco-ai/src/schemas/profile_schemas.py` - Líneas 61-81

---

## Violaciones Detectadas

### 1. OCP (Open/Closed Principle) - CRÍTICO

**Problema:**
```typescript
// VIOLACIÓN: Para agregar un nuevo dominio hay que MODIFICAR este código
const DOMAIN_ELEGANT_NAMES: Record<IOVBADomain, string> = {
  swe: 'CODEX',
  salud: 'VITALIS',
  // ... agregar nuevo dominio requiere modificar aquí
};
```

**Por qué viola OCP:**
- El código está **cerrado para extensión, abierto para modificación** (al revés de lo que debería ser)
- Agregar un nuevo dominio requiere cambiar el código fuente
- No hay forma de extender sin modificar

**Solución Correcta:**
```typescript
// CORRECTO: Los dominios vienen de configuración
interface DomainConfig {
  id: string;
  elegantName: string;
  description: string;
  skills: string[];
  tools: string[];
  mcpServers: string[];
}

// Se carga desde archivo de configuración
const domainRegistry = new DomainRegistry(configLoader.load('domains.yaml'));
```

---

### 2. SRP (Single Responsibility Principle) - ALTO

**Problema:**
```typescript
class ApiClient {
  // Responsabilidad 1: Comunicación HTTP
  private async request<T>() {...}
  
  // Responsabilidad 2: Creación de agentes
  private createIOVBAAgent() {...}
  
  // Responsabilidad 3: Mapeo de datos
  private getSkillsForRole() {...}
  
  // Responsabilidad 4: Lógica de dominios
  private getToolsForDomain() {...}
}
```

**Por qué viola SRP:**
- `ApiClient` tiene **múltiples razones para cambiar**:
  - Cambios en la API
  - Cambios en la estructura de agentes
  - Nuevos dominios
  - Nuevos roles

**Solución Correcta:**
```typescript
// Responsabilidad única: Comunicación HTTP
class ApiClient {
  async request<T>(endpoint: string) {...}
}

// Responsabilidad única: Creación de agentes
class AgentFactory {
  createAgent(config: AgentConfig) {...}
}

// Responsabilidad única: Gestión de dominios
class DomainRegistry {
  getDomainConfig(id: string) {...}
}
```

---

### 3. DIP (Dependency Inversion Principle) - ALTO

**Problema:**
```typescript
// VIOLACIÓN: Depende de implementación concreta hardcodeada
const skillsMap: Record<IOVBARole, string[]> = {
  investigador: ['web-search', 'data-analysis', ...],
};
```

**Por qué viola DIP:**
- Los módulos de alto nivel (`ApiClient`) dependen de módulos de bajo nivel (hardcoded mappings)
- No hay abstracción para la configuración de roles/skills

**Solución Correcta:**
```typescript
// CORRECTO: Depende de abstracción
interface ISkillProvider {
  getSkillsForRole(role: string): Promise<string[]>;
}

class ConfigSkillProvider implements ISkillProvider {
  constructor(private config: SkillConfig) {}
  
  async getSkillsForRole(role: string): Promise<string[]> {
    return this.config.roles[role]?.skills || [];
  }
}

class ApiClient {
  constructor(private skillProvider: ISkillProvider) {}
}
```

---

### 4. LSP (Liskov Substitution Principle) - MEDIO

**Problema en Python:**
```python
class Domain(str, Enum):
    CODEX = "codex"
    # ...
```

**Por qué viola LSP:**
- El uso de `Enum` restringe la sustitución
- No se puede extender sin modificar la clase
- Las subclases no pueden agregar nuevos dominios sin romper el contrato

---

### 5. ISP (Interface Segregation Principle) - BAJO

**Problema:**
```typescript
interface AgentProfile {
  // Muchas propiedades que no todos los clientes necesitan
  skills: string[];
  tools: string[];
  mcp_servers: string[];
  cognitive_capital: CognitiveCapital;
  // ... 20+ propiedades más
}
```

---

## Resumen de Violaciones por Archivo

| Archivo | OCP | SRP | DIP | LSP | ISP | Severidad |
|---------|-----|-----|-----|-----|-----|-----------|
| `client.ts` | ❌ | ❌ | ❌ | ⚠️ | ⚠️ | **CRÍTICA** |
| `profile_schemas.py` | ❌ | ⚠️ | ❌ | ❌ | ✅ | **ALTA** |

---

## Patrones Incorrectos Identificados

### ❌ Patrón 1: Enum para Dominios
```python
class Domain(str, Enum):
    CODEX = "codex"
    VITALIS = "vitalis"
```

### ❌ Patrón 2: Hardcoded Mappings
```typescript
const DOMAIN_ELEGANT_NAMES: Record<IOVBADomain, string> = {...}
const DOMAIN_DESCRIPTIONS: Record<IOVBADomain, string> = {...}
```

### ❌ Patrón 3: God Class
```typescript
class ApiClient {
  // 700+ líneas con múltiples responsabilidades
}
```

---

## Solución Propuesta

### Arquitectura Basada en Configuración

```
┌─────────────────────────────────────────────────────────┐
│                    CONFIG LAYER                          │
├─────────────────────────────────────────────────────────┤
│  domains.yaml    │  roles.yaml    │  agents.yaml        │
│  - codex         │  - investigator│  - templates        │
│  - vitalis       │  - observer    │  - defaults         │
│  - ...           │  - ...         │  - overrides        │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                  REGISTRY LAYER                          │
├─────────────────────────────────────────────────────────┤
│  DomainRegistry   │  RoleRegistry   │  AgentRegistry    │
│  - get(id)        │  - get(id)      │  - get(id)        │
│  - list()         │  - list()       │  - create(config) │
│  - add(config)    │  - add(config)  │  - update()       │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                   SERVICE LAYER                          │
├─────────────────────────────────────────────────────────┤
│  ApiClient        │  AgentFactory   │  ProfileService   │
│  (HTTP only)      │  (Creation)     │  (Management)     │
└─────────────────────────────────────────────────────────┘
```

### Principios Aplicados:

1. **OCP**: Agregar dominios/roles sin modificar código → editar YAML
2. **SRP**: Cada clase tiene una única responsabilidad
3. **DIP**: Servicios dependen de abstracciones (registries)
4. **LSP**: Interfaces extensibles sin romper contratos
5. **ISP**: Interfaces específicas para cada cliente
