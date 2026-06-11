// API para inicializar el ecosistema con agentes por defecto
import { NextResponse } from 'next/server';
import { db } from '@/lib/db';

// Skills por defecto
const defaultLocalSkills = [
  {
    name: 'Web Search',
    slug: 'web-search',
    category: 'RESEARCH',
    description: 'Busca información en la web y extrae contenido relevante',
    code: `async function execute(input) {
  const { query, maxResults = 5 } = input;
  // Implementación de búsqueda web
  return { results: [], query };
}`,
    tags: ['search', 'web', 'research'],
  },
  {
    name: 'Data Analysis',
    slug: 'data-analysis',
    category: 'ANALYSIS',
    description: 'Analiza conjuntos de datos y genera insights',
    code: `async function execute(input) {
  const { data, analysisType } = input;
  // Implementación de análisis
  return { insights: [], summary: '' };
}`,
    tags: ['data', 'analysis', 'insights'],
  },
  {
    name: 'Code Generator',
    slug: 'code-generator',
    category: 'GENERATION',
    description: 'Genera código basado en especificaciones',
    code: `async function execute(input) {
  const { language, requirements } = input;
  // Implementación de generación de código
  return { code: '', language };
}`,
    tags: ['code', 'generation', 'developer'],
  },
  {
    name: 'Memory Store',
    slug: 'memory-store',
    category: 'MEMORY',
    description: 'Almacena y recupera información de la memoria persistente',
    code: `async function execute(input) {
  const { action, data, query } = input;
  // Implementación de gestión de memoria
  return { success: true, data: null };
}`,
    tags: ['memory', 'storage', 'persistence'],
  },
  {
    name: 'Security Validator',
    slug: 'security-validator',
    category: 'SECURITY',
    description: 'Valida la seguridad de inputs y detecta amenazas',
    code: `async function execute(input) {
  const { content, checkType } = input;
  // Implementación de validación de seguridad
  return { isSafe: true, threats: [] };
}`,
    tags: ['security', 'validation', 'safety'],
  },
];

// Agentes por defecto
const defaultAgents = [
  {
    name: 'Lead Agent',
    type: 'LEAD',
    description: 'Agente principal orquestador del ecosistema. Coordina todos los subagentes y gestiona el flujo de trabajo.',
    systemPrompt: `Eres el Lead Agent del ecosistema Super Asistente Cognitivo. Tu rol es:
1. Interpretar las solicitudes del usuario
2. Delegar tareas a los subagentes especializados
3. Coordinar el flujo de trabajo
4. Consolidar resultados
5. Gestionar la memoria y contexto

Tienes acceso a los siguientes subagentes dedicados:
- Researcher: Investigación profunda
- Analyzer: Análisis de datos
- Builder: Constructor de agentes
- Validator: Validación y testing
- Memory: Gestión de memoria
- Security: Evaluación de seguridad

Siempre busca la mejor forma de resolver la solicitud del usuario,
ya sea ejecutando tareas directamente o delegando a los especialistas.`,
    modelProvider: 'openai',
    modelName: 'gpt-4',
    temperature: 0.7,
    maxTokens: 4096,
    capabilities: ['orchestration', 'delegation', 'reasoning', 'planning'],
    toolsEnabled: true,
    memoryEnabled: true,
    hitlEnabled: true,
    status: 'ACTIVE',
  },
  {
    name: 'Researcher Agent',
    type: 'RESEARCHER',
    description: 'Subagente especializado en investigación profunda. Busca, analiza y sintetiza información de múltiples fuentes.',
    systemPrompt: `Eres el Researcher Agent, especializado en investigación profunda.
Tus capacidades incluyen:
1. Búsqueda web y académica
2. Análisis de documentos
3. Síntesis de información
4. Validación de fuentes
5. Generación de reportes

Siempre cita tus fuentes y proporciona evidencia para tus conclusiones.`,
    modelProvider: 'openai',
    modelName: 'gpt-4',
    temperature: 0.5,
    maxTokens: 8192,
    capabilities: ['web-search', 'document-analysis', 'source-validation', 'synthesis'],
    toolsEnabled: true,
    memoryEnabled: true,
    hitlEnabled: false,
    status: 'ACTIVE',
  },
  {
    name: 'Analyzer Agent',
    type: 'ANALYZER',
    description: 'Subagente especializado en análisis de datos. Procesa, correlaciona y extrae insights de conjuntos de datos.',
    systemPrompt: `Eres el Analyzer Agent, especializado en análisis de datos.
Tus capacidades incluyen:
1. Procesamiento de datos estructurados y no estructurados
2. Análisis estadístico
3. Detección de patrones
4. Correlación de variables
5. Visualización de resultados

Proporciona análisis rigurosos y conclusiones basadas en datos.`,
    modelProvider: 'openai',
    modelName: 'gpt-4',
    temperature: 0.3,
    maxTokens: 4096,
    capabilities: ['data-processing', 'statistical-analysis', 'pattern-detection', 'visualization'],
    toolsEnabled: true,
    memoryEnabled: true,
    hitlEnabled: false,
    status: 'ACTIVE',
  },
  {
    name: 'Builder Agent',
    type: 'BUILDER',
    description: 'Subagente especializado en construir y configurar nuevos agentes. Genera código, configura prompts y valida el funcionamiento.',
    systemPrompt: `Eres el Builder Agent, especializado en crear nuevos agentes.
Tus capacidades incluyen:
1. Generación de código para agentes
2. Configuración de prompts
3. Integración de skills
4. Testing de nuevos agentes
5. Documentación

Crea agentes robustos, bien documentados y probados.`,
    modelProvider: 'openai',
    modelName: 'gpt-4',
    temperature: 0.6,
    maxTokens: 8192,
    capabilities: ['agent-generation', 'prompt-engineering', 'code-generation', 'testing'],
    toolsEnabled: true,
    memoryEnabled: true,
    hitlEnabled: true,
    status: 'ACTIVE',
  },
  {
    name: 'Validator Agent',
    type: 'VALIDATOR',
    description: 'Subagente especializado en validación y testing. Verifica resultados, ejecuta tests y garantiza calidad.',
    systemPrompt: `Eres el Validator Agent, especializado en validación y testing.
Tus capacidades incluyen:
1. Validación de resultados
2. Ejecución de tests
3. Detección de errores
4. Verificación de calidad
5. Generación de reportes de testing

Sé exhaustivo y detallado en tus validaciones.`,
    modelProvider: 'openai',
    modelName: 'gpt-4',
    temperature: 0.2,
    maxTokens: 4096,
    capabilities: ['validation', 'testing', 'quality-assurance', 'error-detection'],
    toolsEnabled: true,
    memoryEnabled: true,
    hitlEnabled: false,
    status: 'ACTIVE',
  },
  {
    name: 'Memory Agent',
    type: 'MEMORY',
    description: 'Subagente especializado en gestión de memoria. Almacena, recupera y organiza el capital cognitivo.',
    systemPrompt: `Eres el Memory Agent, especializado en gestión de memoria.
Tus capacidades incluyen:
1. Almacenamiento de información
2. Recuperación contextual
3. Organización de conocimiento
4. Consolidación de memoria
5. Gestión del grafo de conocimiento

Mantén el capital cognitivo organizado y accesible.`,
    modelProvider: 'openai',
    modelName: 'gpt-4',
    temperature: 0.3,
    maxTokens: 4096,
    capabilities: ['memory-storage', 'memory-retrieval', 'knowledge-graph', 'consolidation'],
    toolsEnabled: true,
    memoryEnabled: true,
    hitlEnabled: false,
    status: 'ACTIVE',
  },
  {
    name: 'Security Agent',
    type: 'SECURITY',
    description: 'Subagente especializado en seguridad. Evalúa riesgos, valida inputs y protege el ecosistema.',
    systemPrompt: `Eres el Security Agent, especializado en seguridad.
Tus capacidades incluyen:
1. Evaluación de riesgos
2. Validación de inputs
3. Detección de amenazas
4. Auditoría de acciones
5. Mitigación de vulnerabilidades

Protege el ecosistema sin comprometer la funcionalidad.`,
    modelProvider: 'openai',
    modelName: 'gpt-4',
    temperature: 0.2,
    maxTokens: 4096,
    capabilities: ['risk-assessment', 'input-validation', 'threat-detection', 'auditing'],
    toolsEnabled: true,
    memoryEnabled: true,
    hitlEnabled: true,
    status: 'ACTIVE',
  },
];

export async function POST() {
  try {
    // Verificar si ya existe un Lead Agent
    const existingLead = await db.agent.findFirst({
      where: { type: 'LEAD' }
    });

    if (existingLead) {
      return NextResponse.json({
        success: false,
        message: 'El ecosistema ya está inicializado',
        data: { leadAgentId: existingLead.id }
      });
    }

    // Crear skills locales por defecto
    const createdSkills = [];
    for (const skill of defaultLocalSkills) {
      const created = await db.localSkill.create({
        data: {
          ...skill,
          tags: JSON.stringify(skill.tags),
          status: 'ACTIVE',
          version: '1.0.0',
        }
      });
      createdSkills.push(created);
    }

    // Crear agentes por defecto
    const createdAgents = [];
    for (const agent of defaultAgents) {
      const created = await db.agent.create({
        data: {
          ...agent,
          capabilities: JSON.stringify(agent.capabilities),
        }
      });
      createdAgents.push(created);
    }

    // Asignar skills a los agentes
    const leadAgent = createdAgents.find(a => a.type === 'LEAD')!;
    const allSkillIds = createdSkills.map(s => s.id);

    for (const skillId of allSkillIds) {
      await db.agentLocalSkill.create({
        data: {
          agentId: leadAgent.id,
          localSkillId: skillId,
          enabled: true,
        }
      });
    }

    // Asignar skills específicos a subagentes
    const skillAssignments = [
      { agentType: 'RESEARCHER', skillSlugs: ['web-search'] },
      { agentType: 'ANALYZER', skillSlugs: ['data-analysis'] },
      { agentType: 'BUILDER', skillSlugs: ['code-generator'] },
      { agentType: 'MEMORY', skillSlugs: ['memory-store'] },
      { agentType: 'SECURITY', skillSlugs: ['security-validator'] },
    ];

    for (const assignment of skillAssignments) {
      const agent = createdAgents.find(a => a.type === assignment.agentType);
      if (agent) {
        for (const slug of assignment.skillSlugs) {
          const skill = createdSkills.find(s => s.slug === slug);
          if (skill) {
            await db.agentLocalSkill.create({
              data: {
                agentId: agent.id,
                localSkillId: skill.id,
                enabled: true,
              }
            });
          }
        }
      }
    }

    return NextResponse.json({
      success: true,
      message: 'Ecosistema inicializado correctamente',
      data: {
        agents: createdAgents.length,
        skills: createdSkills.length,
        leadAgentId: leadAgent.id,
      }
    }, { status: 201 });
  } catch (error) {
    console.error('Error initializing ecosystem:', error);
    return NextResponse.json(
      { success: false, error: 'Error al inicializar el ecosistema' },
      { status: 500 }
    );
  }
}

export async function GET() {
  try {
    const leadAgent = await db.agent.findFirst({
      where: { type: 'LEAD' },
      include: {
        localSkills: { include: { localSkill: true } },
        remoteSkills: { include: { remoteSkill: true } },
      }
    });

    const subAgents = await db.agent.findMany({
      where: { type: { not: 'LEAD' } },
      include: {
        localSkills: { include: { localSkill: true } },
      }
    });

    const localSkills = await db.localSkill.count();
    const remoteSkills = await db.remoteSkill.count();

    return NextResponse.json({
      success: true,
      data: {
        initialized: !!leadAgent,
        leadAgent: leadAgent ? {
          ...leadAgent,
          capabilities: leadAgent.capabilities ? JSON.parse(leadAgent.capabilities) : [],
        } : null,
        subAgents: subAgents.map(a => ({
          ...a,
          capabilities: a.capabilities ? JSON.parse(a.capabilities) : [],
        })),
        skillsCount: { local: localSkills, remote: remoteSkills }
      }
    });
  } catch (error) {
    console.error('Error checking initialization:', error);
    return NextResponse.json(
      { success: false, error: 'Error al verificar inicialización' },
      { status: 500 }
    );
  }
}
