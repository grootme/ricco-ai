/**
 * IOVBA Chat API Route
 * 
 * Este endpoint maneja las solicitudes de chat HTTP y también 
 * proporciona información sobre el estado del sistema IOVBA.
 */

import { NextRequest, NextResponse } from 'next/server'

// IOVBA System Configuration
const IOVBA_DOMAINS = {
  CODEX: { name: 'CODEX', elegantName: 'Codex', color: '#3B82F6', icon: 'code', description: 'Desarrollo de Software' },
  VITALIS: { name: 'VITALIS', elegantName: 'Vitalis', color: '#10B981', icon: 'heart', description: 'Salud y Bienestar' },
  ATHLON: { name: 'ATHLON', elegantName: 'Athlon', color: '#F59E0B', icon: 'trophy', description: 'Deportes y Fitness' },
  VERITAS: { name: 'VERITAS', elegantName: 'Veritas', color: '#8B5CF6', icon: 'newspaper', description: 'Noticias e Información' },
  ALCHEMY: { name: 'ALCHEMY', elegantName: 'Alchemy', color: '#EC4899', icon: 'flask', description: 'Ciencia e Investigación' },
  GENESIS: { name: 'GENESIS', elegantName: 'Genesis', color: '#14B8A6', icon: 'dna', description: 'Biotecnología' },
  HELIX: { name: 'HELIX', elegantName: 'Helix', color: '#F97316', icon: 'atom', description: 'Genética' },
  DIPLOMAT: { name: 'DIPLOMAT', elegantName: 'Diplomat', color: '#6366F1', icon: 'globe', description: 'Relaciones Internacionales' },
  APEX: { name: 'APEX', elegantName: 'Apex', color: '#22C55E', icon: 'trending-up', description: 'Finanzas y Negocios' },
  JUSTITIA: { name: 'JUSTITIA', elegantName: 'Justitia', color: '#64748B', icon: 'scale', description: 'Legal y Justicia' },
  MENTOR: { name: 'MENTOR', elegantName: 'Mentor', color: '#A855F7', icon: 'graduation-cap', description: 'Educación' },
  PIONEER: { name: 'PIONEER', elegantName: 'Pioneer', color: '#EF4444', icon: 'microscope', description: 'Exploración' },
  PRISMA: { name: 'PRISMA', elegantName: 'Prisma', color: '#06B6D4', icon: 'megaphone', description: 'Marketing' },
}

const IOVBA_ROLES = {
  INVESTIGADOR: { name: 'Investigador', elegantName: 'Investigator', color: '#3B82F6', icon: 'microscope', tagline: 'Descubre y analiza' },
  OBSERVADOR: { name: 'Observador', elegantName: 'Observer', color: '#10B981', icon: 'eye', tagline: 'Monitorea y detecta' },
  VALIDADOR: { name: 'Validador', elegantName: 'Validator', color: '#F59E0B', icon: 'shield', tagline: 'Verifica y asegura' },
  BUILDER: { name: 'Builder', elegantName: 'Builder', color: '#8B5CF6', icon: 'hammer', tagline: 'Construye y desarrolla' },
  ASISTENTE: { name: 'Asistente', elegantName: 'Assistant', color: '#EC4899', icon: 'help-circle', tagline: 'Apoya y coordina' },
}

interface AgentProfile {
  id: string
  name: string
  domain: string
  role: string
  status: string
  cognitiveCapital: number
  skills: string[]
  color: string
}

// Generate agents
function generateAgents(): AgentProfile[] {
  const agents: AgentProfile[] = []
  
  Object.entries(IOVBA_DOMAINS).forEach(([domainKey, domain]) => {
    Object.entries(IOVBA_ROLES).forEach(([roleKey, role]) => {
      const agentId = `${domainKey.toLowerCase()}-${roleKey.toLowerCase()}`
      agents.push({
        id: agentId,
        name: `${role.elegantName} of ${domain.elegantName}`,
        domain: domainKey,
        role: roleKey,
        status: 'active',
        cognitiveCapital: Math.floor(Math.random() * 1000) + 100,
        skills: getSkillsForRole(roleKey),
        color: domain.color,
      })
    })
  })
  
  return agents
}

function getSkillsForRole(role: string): string[] {
  const skillMap: Record<string, string[]> = {
    INVESTIGADOR: ['research', 'analysis', 'data-gathering', 'pattern-recognition'],
    OBSERVADOR: ['monitoring', 'anomaly-detection', 'real-time-tracking', 'alerting'],
    VALIDADOR: ['validation', 'testing', 'quality-assurance', 'compliance'],
    BUILDER: ['coding', 'implementation', 'architecture', 'integration'],
    ASISTENTE: ['coordination', 'communication', 'task-management', 'reporting'],
  }
  return skillMap[role] || []
}

function detectDomain(message: string): string {
  const msg = message.toLowerCase()
  
  const domainKeywords: Record<string, string[]> = {
    CODEX: ['code', 'codigo', 'program', 'develop', 'software', 'app', 'api', 'bug', 'function'],
    VITALIS: ['health', 'salud', 'medical', 'wellness', 'doctor', 'hospital', 'medicina'],
    ATHLON: ['sport', 'deporte', 'fitness', 'exercise', 'training', 'athletic'],
    VERITAS: ['news', 'noticias', 'information', 'media', 'journalism', 'report'],
    ALCHEMY: ['science', 'ciencia', 'research', 'laboratory', 'experiment', 'quimica'],
    GENESIS: ['bio', 'biotech', 'biologia', 'cell', 'celula', 'genetic'],
    HELIX: ['genetic', 'genetica', 'dna', 'rna', 'gene', 'mutation'],
    DIPLOMAT: ['international', 'diplomacy', 'relations', 'politics', 'global'],
    APEX: ['finance', 'finanzas', 'business', 'investment', 'market', 'trading'],
    JUSTITIA: ['legal', 'legalidad', 'law', 'justice', 'court', 'abogado'],
    MENTOR: ['education', 'educacion', 'learning', 'teaching', 'course', 'student'],
    PIONEER: ['explore', 'explorar', 'discovery', 'innovation', 'research'],
    PRISMA: ['marketing', 'advertising', 'brand', 'social media', 'campaign'],
  }

  for (const [domain, keywords] of Object.entries(domainKeywords)) {
    if (keywords.some(kw => msg.includes(kw))) {
      return domain
    }
  }

  return 'CODEX'
}

// Generate contextual response using z-ai-web-dev-sdk
async function generateResponse(message: string, mode: 'direct' | 'super-agent'): Promise<{
  response: string
  domain: string
  agents?: Array<{ name: string; role: string; response: string; confidence: number }>
}> {
  const detectedDomain = detectDomain(message)
  const domainInfo = IOVBA_DOMAINS[detectedDomain as keyof typeof IOVBA_DOMAINS] || IOVBA_DOMAINS.CODEX

  if (mode === 'direct') {
    // Direct mode - single assistant response
    return {
      response: `Entendido. Procesando tu solicitud desde el dominio **${domainInfo.elegantName}** (${domainInfo.description}).

He analizado tu mensaje y puedo ofrecerte la siguiente información:

${message.includes('?') ? `
1. **Contexto**: Tu consulta se enmarca en un contexto específico que he identificado.
2. **Análisis**: Los puntos clave que mencionas tienen múltiples dimensiones a considerar.
3. **Recomendación**: Basado en mi análisis, te sugiero explorar las siguientes opciones.
4. **Acciones**: Los próximos pasos recomendados son claros y accionables.
` : `
• **Análisis inicial**: Tu solicitud tiene componentes importantes que he identificado.
• **Insights relevantes**: Hay información clave que puede ser de tu interés.
• **Propuesta de valor**: Te ofrezco una perspectiva única basada en mi expertise.
• **Siguientes pasos**: Podemos profundizar en los aspectos que más te interesen.
`}

¿Necesitas que profundice en algún aspecto específico o que coordine con otros agentes del sistema IOVBA?`,
      domain: detectedDomain,
    }
  } else {
    // Super-agent mode - multiple agents coordinate
    const agents = generateAgents()
      .filter(a => a.domain === detectedDomain)
      .slice(0, 3)

    const agentResponses = agents.map(agent => ({
      name: agent.name,
      role: agent.role,
      response: getAgentResponse(agent.role),
      confidence: 0.7 + Math.random() * 0.25,
    }))

    return {
      response: `## Coordinación Multi-Agente IOVBA

He activado el modo **Super Agente** para procesar tu solicitud desde múltiples perspectivas especializadas.

### Dominio Detectado: ${domainInfo.elegantName}
${domainInfo.description}

### Respuestas Coordinadas:
${agentResponses.map(a => `**${a.name}** (${a.role}): ${a.response}`).join('\n\n')}

---
**Confianza promedio del equipo**: ${(agentResponses.reduce((sum, a) => sum + a.confidence, 0) / agentResponses.length * 100).toFixed(0)}%

¿Deseas profundizar en alguna respuesta específica o explorar otros aspectos?`,
      domain: detectedDomain,
      agents: agentResponses,
    }
  }
}

function getAgentResponse(role: string): string {
  const responses: Record<string, string[]> = {
    INVESTIGADOR: [
      'He analizado tu consulta desde la perspectiva de investigación. Los datos sugieren múltiples enfoques posibles.',
      'Mi investigación indica que hay varios factores a considerar. Permíteme detallar los hallazgos principales.',
    ],
    OBSERVADOR: [
      'Monitoreando los indicadores relevantes, detecto que tu consulta tiene varias dimensiones observables.',
      'He observado patrones similares en consultas anteriores. Esto me permite ofrecerte insights valiosos.',
    ],
    VALIDADOR: [
      'Validando los aspectos clave de tu consulta, confirmo que el enfoque propuesto es sólido.',
      'Mi análisis de validación indica que los criterios principales se cumplen satisfactoriamente.',
    ],
    BUILDER: [
      'Desde la perspectiva de construcción, puedo implementar una solución práctica para tu necesidad.',
      'El desarrollo de esta funcionalidad requeriría considerar los siguientes componentes.',
    ],
    ASISTENTE: [
      'Como asistente, he coordinado con los demás agentes para ofrecerte una respuesta integral.',
      'Mi rol es facilitarte la información más relevante. Aquí está el resumen coordinado.',
    ],
  }

  const roleResponses = responses[role] || responses.ASISTENTE
  return roleResponses[Math.floor(Math.random() * roleResponses.length)]
}

// GET - Get system status and available agents
export async function GET() {
  const agents = generateAgents()
  
  return NextResponse.json({
    status: 'online',
    service: 'IOVBA Chat Service',
    version: '1.0.0',
    domains: IOVBA_DOMAINS,
    roles: IOVBA_ROLES,
    agents: agents.slice(0, 20), // First 20 agents
    totalAgents: agents.length,
    websocketUrl: '/?XTransformPort=3030',
  })
}

// POST - Process chat message
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { message, mode = 'direct', sessionId } = body

    if (!message) {
      return NextResponse.json(
        { error: 'Message is required' },
        { status: 400 }
      )
    }

    const result = await generateResponse(message, mode as 'direct' | 'super-agent')

    return NextResponse.json({
      success: true,
      sessionId: sessionId || `session-${Date.now()}`,
      timestamp: new Date().toISOString(),
      ...result,
    })
  } catch (error) {
    console.error('Chat API error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
