/**
 * IOVBA Chat Service - WebSocket Service for Real-time Chat
 * 
 * Este servicio maneja:
 * - Conexiones WebSocket en tiempo real
 * - Coordinación con Lead Assistant
 * - Integración con el sistema IOVBA completo
 * - Modo directo (asistente IOVBA) y modo super-agente
 */

import { Server as HttpServer } from 'http'
import { Server as IOServer, Socket } from 'socket.io'
import { EventEmitter } from 'events'

// Types
interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system' | 'agent'
  content: string
  timestamp: Date
  agentId?: string
  agentName?: string
  domain?: string
  metadata?: Record<string, unknown>
}

interface ChatSession {
  id: string
  userId: string
  mode: 'direct' | 'super-agent'
  messages: ChatMessage[]
  activeAgents: string[]
  createdAt: Date
  updatedAt: Date
}

interface AgentResponse {
  agentId: string
  agentName: string
  role: string
  domain: string
  response: string
  confidence: number
  processingTime: number
}

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

// Agent Registry (simulated - in production would connect to actual agents)
class AgentRegistry {
  private agents: Map<string, AgentProfile> = new Map()
  
  constructor() {
    this.initializeAgents()
  }

  private initializeAgents() {
    // Create agents for each domain and role
    Object.entries(IOVBA_DOMAINS).forEach(([domainKey, domain]) => {
      Object.entries(IOVBA_ROLES).forEach(([roleKey, role]) => {
        const agentId = `${domainKey.toLowerCase()}-${roleKey.toLowerCase()}`
        this.agents.set(agentId, {
          id: agentId,
          name: `${role.elegantName} of ${domain.elegantName}`,
          domain: domainKey,
          role: roleKey,
          status: 'active',
          cognitiveCapital: Math.floor(Math.random() * 1000) + 100,
          skills: this.getSkillsForRole(roleKey),
          color: domain.color,
        })
      })
    })
  }

  private getSkillsForRole(role: string): string[] {
    const skillMap: Record<string, string[]> = {
      INVESTIGADOR: ['research', 'analysis', 'data-gathering', 'pattern-recognition'],
      OBSERVADOR: ['monitoring', 'anomaly-detection', 'real-time-tracking', 'alerting'],
      VALIDADOR: ['validation', 'testing', 'quality-assurance', 'compliance'],
      BUILDER: ['coding', 'implementation', 'architecture', 'integration'],
      ASISTENTE: ['coordination', 'communication', 'task-management', 'reporting'],
    }
    return skillMap[role] || []
  }

  getAgent(id: string): AgentProfile | undefined {
    return this.agents.get(id)
  }

  getAgentsByDomain(domain: string): AgentProfile[] {
    return Array.from(this.agents.values()).filter(a => a.domain === domain)
  }

  getAgentsByRole(role: string): AgentProfile[] {
    return Array.from(this.agents.values()).filter(a => a.role === role)
  }

  getAllAgents(): AgentProfile[] {
    return Array.from(this.agents.values())
  }
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

// Lead Assistant (Super Agent)
class LeadAssistant {
  private agentRegistry: AgentRegistry
  private eventEmitter: EventEmitter

  constructor(agentRegistry: AgentRegistry) {
    this.agentRegistry = agentRegistry
    this.eventEmitter = new EventEmitter()
  }

  async processMessage(message: string, sessionId: string, mode: 'direct' | 'super-agent'): Promise<AgentResponse[]> {
    const startTime = Date.now()
    const responses: AgentResponse[] = []

    if (mode === 'direct') {
      // Direct mode: Single assistant response
      const response = await this.generateDirectResponse(message, sessionId)
      responses.push(response)
    } else {
      // Super-agent mode: Coordinate multiple agents
      const agentResponses = await this.coordinateAgents(message, sessionId)
      responses.push(...agentResponses)
    }

    return responses
  }

  private async generateDirectResponse(message: string, _sessionId: string): Promise<AgentResponse> {
    const startTime = Date.now()
    
    // Simulate processing
    await this.simulateProcessing(500, 1500)

    // Analyze message and determine domain
    const detectedDomain = this.detectDomain(message)
    const domain = IOVBA_DOMAINS[detectedDomain as keyof typeof IOVBA_DOMAINS] || IOVBA_DOMAINS.CODEX

    // Generate contextual response
    const response = this.generateContextualResponse(message, domain)

    return {
      agentId: 'lead-assistant',
      agentName: 'IOVBA Assistant',
      role: 'ASISTENTE',
      domain: detectedDomain,
      response: response,
      confidence: 0.85 + Math.random() * 0.1,
      processingTime: Date.now() - startTime,
    }
  }

  private async coordinateAgents(message: string, _sessionId: string): Promise<AgentResponse[]> {
    const responses: AgentResponse[] = []
    const detectedDomain = this.detectDomain(message)
    
    // Get relevant agents based on message analysis
    const agents = this.selectRelevantAgents(message, detectedDomain)
    
    // Process in parallel (simulated)
    for (const agent of agents.slice(0, 3)) { // Limit to 3 agents for performance
      const startTime = Date.now()
      await this.simulateProcessing(300, 800)
      
      const response = await this.generateAgentResponse(message, agent)
      responses.push({
        agentId: agent.id,
        agentName: agent.name,
        role: agent.role,
        domain: agent.domain,
        response: response,
        confidence: 0.7 + Math.random() * 0.25,
        processingTime: Date.now() - startTime,
      })
    }

    // Add lead assistant coordination summary
    const summaryStart = Date.now()
    await this.simulateProcessing(200, 500)
    
    responses.push({
      agentId: 'lead-assistant',
      agentName: 'Lead Assistant',
      role: 'COORDINATOR',
      domain: 'ALL',
      response: this.generateCoordinationSummary(responses),
      confidence: 0.95,
      processingTime: Date.now() - summaryStart,
    })

    return responses
  }

  private detectDomain(message: string): string {
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

    return 'CODEX' // Default domain
  }

  private selectRelevantAgents(message: string, domain: string): AgentProfile[] {
    const allAgents = this.agentRegistry.getAllAgents()
    
    // Prioritize agents from detected domain
    const domainAgents = allAgents.filter(a => a.domain === domain)
    const otherAgents = allAgents.filter(a => a.domain !== domain)
    
    // Select role diversity
    const selected: AgentProfile[] = []
    const usedRoles = new Set<string>()

    // Add domain agents first
    for (const agent of domainAgents) {
      if (!usedRoles.has(agent.role) && selected.length < 3) {
        selected.push(agent)
        usedRoles.add(agent.role)
      }
    }

    // Fill with other agents if needed
    for (const agent of otherAgents) {
      if (!usedRoles.has(agent.role) && selected.length < 3) {
        selected.push(agent)
        usedRoles.add(agent.role)
      }
    }

    return selected
  }

  private async generateAgentResponse(message: string, agent: AgentProfile): Promise<string> {
    const roleResponses: Record<string, string[]> = {
      INVESTIGADOR: [
        `He analizado tu consulta desde la perspectiva de investigación. Los datos sugieren múltiples enfoques posibles.`,
        `Mi investigación indica que hay varios factores a considerar. Permíteme detallar los hallazgos principales.`,
        `Basándome en el análisis de datos, puedo identificar patrones relevantes para tu solicitud.`,
      ],
      OBSERVADOR: [
        `Monitoreando los indicadores relevantes, detecto que tu consulta tiene varias dimensiones observables.`,
        `He observado patrones similares en consultas anteriores. Esto me permite ofrecerte insights valiosos.`,
        `La observación continua del tema que mencionas revela tendencias interesantes.`,
      ],
      VALIDADOR: [
        `Validando los aspectos clave de tu consulta, confirmo que el enfoque propuesto es sólido.`,
        `Mi análisis de validación indica que los criterios principales se cumplen satisfactoriamente.`,
        `He verificado la información y puedo confirmar su consistencia con los estándares establecidos.`,
      ],
      BUILDER: [
        `Desde la perspectiva de construcción, puedo implementar una solución práctica para tu necesidad.`,
        `El desarrollo de esta funcionalidad requeriría considerar los siguientes componentes.`,
        `Para construir una solución efectiva, propongo la siguiente arquitectura.`,
      ],
      ASISTENTE: [
        `Como asistente, he coordinado con los demás agentes para ofrecerte una respuesta integral.`,
        `Mi rol es facilitarte la información más relevante. Aquí está el resumen coordinado.`,
        `Apoyando tu solicitud, he recopilado los recursos necesarios para tu éxito.`,
      ],
    }

    const responses = roleResponses[agent.role] || roleResponses.ASISTENTE
    return responses[Math.floor(Math.random() * responses.length)]
  }

  private generateContextualResponse(message: string, domain: typeof IOVBA_DOMAINS.CODEX): string {
    const domainInfo = domain
    
    return `Entendido. Procesando tu solicitud desde el dominio **${domainInfo.elegantName}** (${domainInfo.description}).

Tu mensaje ha sido analizado y te ofrezco la siguiente respuesta:

${this.generateDetailedResponse(message)}

¿Necesitas que profundice en algún aspecto específico o que coordine con otros agentes del sistema IOVBA?`
  }

  private generateDetailedResponse(message: string): string {
    // Generate a contextual response based on message content
    if (message.includes('?')) {
      return `He analizado tu pregunta y puedo ofrecerte la siguiente información:

1. **Contexto**: Tu consulta se enmarca en un contexto específico que he identificado.
2. **Análisis**: Los puntos clave que mencionas tienen múltiples dimensiones a considerar.
3. **Recomendación**: Basado en mi análisis, te sugiero explorar las siguientes opciones.
4. **Acciones**: Los próximos pasos recomendados son claros y accionables.`
    }
    
    return `He procesado tu mensaje y esto es lo que puedo ofrecerte:

• **Análisis inicial**: Tu solicitud tiene componentes importantes que he identificado.
• **Insights relevantes**: Hay información clave que puede ser de tu interés.
• **Propuesta de valor**: Te ofrezco una perspectiva única basada en mi expertise.
• **Siguientes pasos**: Podemos profundizar en los aspectos que más te interesen.`
  }

  private generateCoordinationSummary(responses: AgentResponse[]): string {
    const agentNames = responses.map(r => r.agentName).join(', ')
    const avgConfidence = (responses.reduce((sum, r) => sum + r.confidence, 0) / responses.length * 100).toFixed(0)

    return `## Resumen de Coordinación

He coordinado las respuestas de **${responses.length} agentes** del sistema IOVBA:
${responses.map(r => `- **${r.agentName}** (${r.role}): Confianza ${(r.confidence * 100).toFixed(0)}%`).join('\n')}

### Consenso
La confianza promedio del equipo es del **${avgConfidence}%**.

### Recomendación Unificada
Basado en el análisis conjunto, te recomiendo considerar las perspectivas presentadas por cada especialista. El sistema IOVBA trabaja en coordinación para ofrecerte respuestas completas y validadas.

¿Deseas profundizar en alguna respuesta específica o explorar otros dominios?`
  }

  private simulateProcessing(minMs: number, maxMs: number): Promise<void> {
    return new Promise(resolve => 
      setTimeout(resolve, minMs + Math.random() * (maxMs - minMs))
    )
  }
}

// Session Manager
class SessionManager {
  private sessions: Map<string, ChatSession> = new Map()

  createSession(userId: string, mode: 'direct' | 'super-agent'): ChatSession {
    const session: ChatSession = {
      id: `session-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      userId,
      mode,
      messages: [],
      activeAgents: [],
      createdAt: new Date(),
      updatedAt: new Date(),
    }
    this.sessions.set(session.id, session)
    return session
  }

  getSession(id: string): ChatSession | undefined {
    return this.sessions.get(id)
  }

  addMessage(sessionId: string, message: ChatMessage): void {
    const session = this.sessions.get(sessionId)
    if (session) {
      session.messages.push(message)
      session.updatedAt = new Date()
    }
  }

  getMessages(sessionId: string): ChatMessage[] {
    return this.sessions.get(sessionId)?.messages || []
  }
}

// Main Chat Service
class IOVBAChatService {
  private io: IOServer
  private agentRegistry: AgentRegistry
  private leadAssistant: LeadAssistant
  private sessionManager: SessionManager

  constructor(server: HttpServer) {
    this.io = new IOServer(server, {
      cors: {
        origin: '*',
        methods: ['GET', 'POST'],
      },
    })

    this.agentRegistry = new AgentRegistry()
    this.leadAssistant = new LeadAssistant(this.agentRegistry)
    this.sessionManager = new SessionManager()

    this.setupEventHandlers()
    console.log('🚀 IOVBA Chat Service initialized on port 3030')
  }

  private setupEventHandlers() {
    this.io.on('connection', (socket: Socket) => {
      console.log(`📱 Client connected: ${socket.id}`)

      // Send initial data
      socket.emit('connected', {
        sessionId: socket.id,
        agents: this.agentRegistry.getAllAgents().slice(0, 20),
        domains: IOVBA_DOMAINS,
        roles: IOVBA_ROLES,
      })

      // Handle session creation
      socket.on('create-session', (data: { mode: 'direct' | 'super-agent', userId: string }) => {
        const session = this.sessionManager.createSession(data.userId, data.mode)
        socket.join(session.id)
        socket.emit('session-created', session)
        console.log(`📝 Session created: ${session.id} (mode: ${data.mode})`)
      })

      // Handle chat messages
      socket.on('chat-message', async (data: { sessionId: string, message: string, mode: 'direct' | 'super-agent' }) => {
        console.log(`💬 Message received in session ${data.sessionId}: ${data.message.substring(0, 50)}...`)

        // Add user message to session
        const userMessage: ChatMessage = {
          id: `msg-${Date.now()}`,
          role: 'user',
          content: data.message,
          timestamp: new Date(),
        }
        this.sessionManager.addMessage(data.sessionId, userMessage)
        
        // Emit user message confirmation
        socket.emit('message-received', userMessage)

        // Show typing indicator
        socket.emit('typing', { agentId: 'lead-assistant', isTyping: true })

        try {
          // Process message through Lead Assistant
          const responses = await this.leadAssistant.processMessage(
            data.message,
            data.sessionId,
            data.mode
          )

          // Emit each agent response
          for (const response of responses) {
            const agentMessage: ChatMessage = {
              id: `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
              role: 'agent',
              content: response.response,
              timestamp: new Date(),
              agentId: response.agentId,
              agentName: response.agentName,
              domain: response.domain,
              metadata: {
                confidence: response.confidence,
                processingTime: response.processingTime,
                role: response.role,
              },
            }
            
            this.sessionManager.addMessage(data.sessionId, agentMessage)
            socket.emit('agent-response', agentMessage)
            
            // Small delay between agent responses for realistic feel
            await new Promise(resolve => setTimeout(resolve, 200))
          }
        } catch (error) {
          console.error('Error processing message:', error)
          socket.emit('error', { message: 'Error processing your message' })
        } finally {
          socket.emit('typing', { agentId: 'lead-assistant', isTyping: false })
        }
      })

      // Handle mode switch
      socket.on('switch-mode', (data: { sessionId: string, mode: 'direct' | 'super-agent' }) => {
        const session = this.sessionManager.getSession(data.sessionId)
        if (session) {
          session.mode = data.mode
          socket.emit('mode-switched', { mode: data.mode })
          console.log(`🔄 Mode switched to ${data.mode} for session ${data.sessionId}`)
        }
      })

      // Handle agent selection
      socket.on('select-agent', (data: { agentId: string }) => {
        const agent = this.agentRegistry.getAgent(data.agentId)
        if (agent) {
          socket.emit('agent-selected', agent)
        }
      })

      // Handle disconnect
      socket.on('disconnect', () => {
        console.log(`📱 Client disconnected: ${socket.id}`)
      })
    })
  }
}

// Start server
const PORT = 3030
const httpServer = new HttpServer()
new IOVBAChatService(httpServer)

httpServer.listen(PORT, () => {
  console.log(`🚀 IOVBA Chat Service running on port ${PORT}`)
})

export { IOVBAChatService, AgentRegistry, LeadAssistant, SessionManager }
