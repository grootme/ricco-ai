// ============================================
// SUPER AGENTE COGNITIVO - TIPOS E INTERFACES
// ============================================

// Tipos de Agente
export type AgentType = 
  | 'LEAD'        // Agente principal orquestador
  | 'RESEARCHER'  // Investigador profundo
  | 'ANALYZER'    // Analizador de datos
  | 'BUILDER'     // Constructor de agentes
  | 'VALIDATOR'   // Validador y tester
  | 'ORCHESTRATOR' // Coordinador de flujos
  | 'MEMORY'      // Gestor de memoria
  | 'SECURITY'    // Evaluador de seguridad
  | 'CUSTOM';     // Agente personalizado

export type AgentStatus = 'ACTIVE' | 'INACTIVE' | 'BUSY' | 'ERROR' | 'MAINTENANCE';

export type SkillCategory = 
  | 'RESEARCH'
  | 'ANALYSIS'
  | 'GENERATION'
  | 'TRANSFORM'
  | 'VALIDATION'
  | 'INTEGRATION'
  | 'AUTOMATION'
  | 'COMMUNICATION'
  | 'MEMORY'
  | 'SECURITY'
  | 'CUSTOM';

export type SkillStatus = 'ACTIVE' | 'INACTIVE' | 'DEPRECATED' | 'ERROR';

export type SkillSource = 
  | 'DEERFLOW'
  | 'NIM'
  | 'LANGCHAIN'
  | 'CUSTOM'
  | 'GITHUB'
  | 'HUGGINGFACE';

export type SyncStatus = 'PENDING' | 'SYNCING' | 'SYNCED' | 'ERROR';

export type MemoryType = 
  | 'SESSION'     // Corto plazo
  | 'EPISODIC'    // Mediano plazo
  | 'SEMANTIC'    // Largo plazo
  | 'PROCEDURAL'  // Habilidades
  | 'DECLARATIVE' // Hechos
  | 'PREFERENCE'; // Preferencias

export type ExecutionStatus = 
  | 'PENDING'
  | 'RUNNING'
  | 'COMPLETED'
  | 'FAILED'
  | 'CANCELLED'
  | 'TIMEOUT';

export type HITLType = 
  | 'APPROVAL'
  | 'REVIEW'
  | 'CORRECTION'
  | 'TRAINING'
  | 'FEEDBACK';

export type HITLStatus = 
  | 'PENDING'
  | 'APPROVED'
  | 'REJECTED'
  | 'MODIFIED'
  | 'EXPIRED';

// ============================================
// INTERFACES PRINCIPALES
// ============================================

export interface IAgent {
  id: string;
  name: string;
  type: AgentType;
  description?: string;
  status: AgentStatus;
  version: string;
  systemPrompt?: string;
  modelProvider: string;
  modelName: string;
  temperature: number;
  maxTokens: number;
  capabilities?: string[];
  toolsEnabled: boolean;
  memoryEnabled: boolean;
  hitlEnabled: boolean;
  config?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  createdAt: Date;
  updatedAt: Date;
}

export interface ILocalSkill {
  id: string;
  name: string;
  slug: string;
  category: SkillCategory;
  description?: string;
  version: string;
  author?: string;
  code: string;
  config?: Record<string, unknown>;
  inputSchema?: Record<string, unknown>;
  outputSchema?: Record<string, unknown>;
  status: SkillStatus;
  isPublic: boolean;
  downloads: number;
  rating: number;
  tags?: string[];
  metadata?: Record<string, unknown>;
  createdAt: Date;
  updatedAt: Date;
}

export interface IRemoteSkill {
  id: string;
  name: string;
  slug: string;
  source: SkillSource;
  sourceUrl: string;
  sourceId?: string;
  category: SkillCategory;
  description?: string;
  version?: string;
  author?: string;
  config?: Record<string, unknown>;
  inputSchema?: Record<string, unknown>;
  outputSchema?: Record<string, unknown>;
  status: SkillStatus;
  syncStatus: SyncStatus;
  lastSyncAt?: Date;
  cacheCode?: string;
  tags?: string[];
  metadata?: Record<string, unknown>;
  createdAt: Date;
  updatedAt: Date;
}

export interface IMemory {
  id: string;
  agentId: string;
  type: MemoryType;
  category?: string;
  key?: string;
  content: string;
  embedding?: number[];
  importance: number;
  accessCount: number;
  lastAccessedAt?: Date;
  expiresAt?: Date;
  sessionId?: string;
  sourceType?: string;
  sourceId?: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface ISession {
  id: string;
  agentId: string;
  status: 'ACTIVE' | 'PAUSED' | 'ENDED' | 'ARCHIVED';
  context?: Record<string, unknown>;
  summary?: string;
  messageCount: number;
  tokenCount: number;
  channelId?: string;
  userId?: string;
  metadata?: Record<string, unknown>;
  startedAt: Date;
  endedAt?: Date;
  messages: IMessage[];
}

export interface IMessage {
  id: string;
  sessionId: string;
  role: 'USER' | 'ASSISTANT' | 'SYSTEM' | 'TOOL' | 'HITL';
  content: string;
  tokens?: number;
  model?: string;
  latency?: number;
  skillUsed?: string;
  parentMsgId?: string;
  createdAt: Date;
}

export interface IAgentExecution {
  id: string;
  agentId: string;
  status: ExecutionStatus;
  input: Record<string, unknown>;
  output?: Record<string, unknown>;
  duration?: number;
  tokensIn?: number;
  tokensOut?: number;
  cost?: number;
  trace?: Record<string, unknown>[];
  error?: string;
  sessionId?: string;
  triggeredBy?: string;
  startedAt: Date;
  completedAt?: Date;
}

export interface ISkillExecution {
  id: string;
  localSkillId?: string;
  remoteSkillId?: string;
  status: ExecutionStatus;
  input: Record<string, unknown>;
  output?: Record<string, unknown>;
  duration?: number;
  error?: string;
  agentId?: string;
  sessionId?: string;
  executedAt: Date;
}

export interface IHITLRequest {
  id: string;
  agentId: string;
  type: HITLType;
  title: string;
  content: Record<string, unknown>;
  status: HITLStatus;
  response?: string;
  respondedBy?: string;
  respondedAt?: Date;
  sessionId?: string;
  executionId?: string;
  priority: number;
  expiresAt?: Date;
  createdAt: Date;
}

export interface IImprovement {
  id: string;
  agentId?: string;
  type: 'PROMPT' | 'SKILL' | 'MODEL' | 'MEMORY' | 'FLOW' | 'AGENT';
  title: string;
  description?: string;
  status: 'PENDING' | 'TESTING' | 'APPROVED' | 'APPLIED' | 'REJECTED' | 'ROLLED_BACK';
  before?: Record<string, unknown>;
  after?: Record<string, unknown>;
  impact?: number;
  metrics?: Record<string, unknown>;
  hitlRequired: boolean;
  hitlRequestId?: string;
  appliedAt?: Date;
  createdAt: Date;
}

// ============================================
// TIPOS DE API
// ============================================

export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  success: boolean;
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface AgentCreateInput {
  name: string;
  type: AgentType;
  description?: string;
  systemPrompt?: string;
  modelProvider?: string;
  modelName?: string;
  temperature?: number;
  maxTokens?: number;
  capabilities?: string[];
  toolsEnabled?: boolean;
  memoryEnabled?: boolean;
  hitlEnabled?: boolean;
  config?: Record<string, unknown>;
}

export interface AgentUpdateInput {
  name?: string;
  description?: string;
  systemPrompt?: string;
  modelProvider?: string;
  modelName?: string;
  temperature?: number;
  maxTokens?: number;
  capabilities?: string[];
  toolsEnabled?: boolean;
  memoryEnabled?: boolean;
  hitlEnabled?: boolean;
  status?: AgentStatus;
  config?: Record<string, unknown>;
}

export interface SkillCreateInput {
  name: string;
  slug: string;
  category: SkillCategory;
  description?: string;
  version?: string;
  author?: string;
  code: string;
  config?: Record<string, unknown>;
  inputSchema?: Record<string, unknown>;
  outputSchema?: Record<string, unknown>;
  isPublic?: boolean;
  tags?: string[];
}

export interface RemoteSkillCreateInput {
  name: string;
  slug: string;
  source: SkillSource;
  sourceUrl: string;
  sourceId?: string;
  category: SkillCategory;
  description?: string;
  version?: string;
  author?: string;
  config?: Record<string, unknown>;
  tags?: string[];
}

export interface MemoryCreateInput {
  agentId: string;
  type: MemoryType;
  category?: string;
  key?: string;
  content: string;
  importance?: number;
  sessionId?: string;
  sourceType?: string;
  sourceId?: string;
}

export interface ExecutionInput {
  agentId: string;
  input: Record<string, unknown>;
  sessionId?: string;
  triggeredBy?: string;
}

export interface SkillExecutionInput {
  skillId: string;
  isRemote: boolean;
  input: Record<string, unknown>;
  agentId?: string;
  sessionId?: string;
}

// ============================================
// TIPOS DE WEBSOCKET
// ============================================

export type WebSocketEventType = 
  | 'agent:status'
  | 'agent:message'
  | 'agent:execution'
  | 'skill:execution'
  | 'memory:update'
  | 'hitl:request'
  | 'improvement:applied'
  | 'session:update';

export interface WebSocketMessage<T = unknown> {
  type: WebSocketEventType;
  payload: T;
  timestamp: Date;
}

export interface AgentStatusPayload {
  agentId: string;
  status: AgentStatus;
  previousStatus?: AgentStatus;
}

export interface AgentMessagePayload {
  sessionId: string;
  message: IMessage;
}

export interface ExecutionPayload {
  executionId: string;
  agentId: string;
  status: ExecutionStatus;
  progress?: number;
}

// ============================================
// TIPOS DE DASHBOARD
// ============================================

export interface DashboardStats {
  agents: {
    total: number;
    active: number;
    busy: number;
    error: number;
  };
  skills: {
    local: number;
    remote: number;
    active: number;
  };
  executions: {
    today: number;
    successRate: number;
    avgDuration: number;
  };
  memory: {
    entries: number;
    categories: number;
    avgImportance: number;
  };
  hitl: {
    pending: number;
    approved: number;
    rejected: number;
  };
}

export interface AgentWithSkills extends IAgent {
  localSkills: Array<{
    id: string;
    name: string;
    category: SkillCategory;
    enabled: boolean;
  }>;
  remoteSkills: Array<{
    id: string;
    name: string;
    source: SkillSource;
    enabled: boolean;
  }>;
  _count?: {
    sessions: number;
    executions: number;
    memories: number;
  };
}
