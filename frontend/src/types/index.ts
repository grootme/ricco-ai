// Cognitive Capital Types
export interface Engram {
  id: string;
  content: string;
  embedding?: number[];
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  access_count: number;
  importance_score: number;
  source: 'interaction' | 'observation' | 'reflection' | 'instruction';
  tags: string[];
}

export interface CognitiveCapital {
  agent_id: string;
  total_engrams: number;
  total_interactions: number;
  learning_score: number;
  domains: string[];
  skills: string[];
  tools: string[];
  mcp_servers: string[];
  memory_vcs_version: string;
  last_updated: string;
  capital_value: number;
}

// Agent Types
export interface AgentProfile {
  id: string;
  name: string;
  description: string;
  domain: string;
  skills: string[];
  tools: string[];
  mcp_servers: string[];
  prompt_template: string;
  cognitive_capital: CognitiveCapital;
  status: 'active' | 'inactive' | 'learning' | 'error';
  created_at: string;
  updated_at: string;
  metrics: AgentMetrics;
  iovba_role?: IOVBARole;
}

export interface AgentMetrics {
  total_interactions: number;
  success_rate: number;
  avg_response_time: number;
  capital_growth: number;
  last_interaction: string;
}

// IOVBA Types - Grupo de agentes orientado a dominio
export type IOVBARole = 'investigador' | 'observador' | 'validador' | 'builder' | 'asistente';

export interface IOVBAGroup {
  id: string;
  name: string;
  domain: string;
  description: string;
  agents: {
    investigador: AgentProfile;
    observador: AgentProfile;
    validador: AgentProfile;
    builder: AgentProfile;
    asistente: AgentProfile;
  };
  status: 'active' | 'inactive' | 'learning';
  created_at: string;
  metrics: IOVBAMetrics;
}

export interface IOVBAMetrics {
  total_tasks: number;
  success_rate: number;
  avg_completion_time: number;
  domain_expertise: number;
}

// Available domains for IOVBA groups
export type IOVBADomain =
  | 'swe'           // Software Engineering
  | 'salud'         // Healthcare
  | 'deportes'      // Sports
  | 'noticias'      // News/Journalism
  | 'quimica'       // Chemistry
  | 'biologia'      // Biology
  | 'biotecnologia' // Biotechnology
  | 'geopolitica'   // Geopolitics
  | 'finanzas'      // Finance
  | 'legal'         // Legal
  | 'educacion'     // Education
  | 'investigacion' // Research
  | 'marketing'     // Marketing
  | 'custom';       // Custom domain

export interface IOVBATemplate {
  domain: IOVBADomain;
  name: string;
  description: string;
  investigador_config: Partial<AgentProfile>;
  observador_config: Partial<AgentProfile>;
  validador_config: Partial<AgentProfile>;
  builder_config: Partial<AgentProfile>;
  asistente_config: Partial<AgentProfile>;
}

// Memory Types
export interface MemoryEntry {
  id: string;
  agent_id: string;
  type: 'short_term' | 'long_term' | 'episodic' | 'semantic';
  content: string;
  embedding?: number[];
  metadata: MemoryMetadata;
  created_at: string;
  expires_at?: string;
  relevance_score: number;
}

export interface MemoryMetadata {
  source: string;
  context: string;
  importance: number;
  tags: string[];
  related_entries: string[];
}

// NVIDIA Blueprint Domain
export interface NVIDIABlueprint {
  id: string;
  name: string;
  description: string;
  domain: string;
  repo_url: string;
  components: BlueprintComponent[];
  agents: AgentProfile[];
  status: 'available' | 'implemented' | 'partial';
}

export interface BlueprintComponent {
  name: string;
  type: 'retriever' | 'llm' | 'vector_store' | 'tool' | 'workflow';
  config: Record<string, unknown>;
}

// MCP Server Types
export interface MCPServer {
  id: string;
  name: string;
  description: string;
  transport: 'stdio' | 'http' | 'websocket';
  command?: string;
  url?: string;
  tools: MCPTool[];
  resources: MCPResource[];
  status: 'connected' | 'disconnected' | 'error';
  last_connected?: string;
}

export interface MCPTool {
  name: string;
  description: string;
  input_schema: Record<string, unknown>;
  output_schema?: Record<string, unknown>;
}

export interface MCPResource {
  uri: string;
  name: string;
  description: string;
  mime_type?: string;
}

// Skill Types
export interface Skill {
  id: string;
  name: string;
  description: string;
  version: string;
  category: string;
  triggers: string[];
  prompt_template: string;
  tools_required: string[];
  mcp_required: string[];
  examples: SkillExample[];
  metadata: Record<string, unknown>;
}

export interface SkillExample {
  input: string;
  output: string;
  explanation: string;
}

// Vector Store Types
export interface VectorStoreConfig {
  type: 'milvus' | 'qdrant';
  host: string;
  port: number;
  collection: string;
  dimension: number;
}

export interface VectorSearchResult {
  id: string;
  score: number;
  content: string;
  metadata: Record<string, unknown>;
}

// API Response Types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// Dashboard Stats
export interface DashboardStats {
  total_agents: number;
  active_agents: number;
  total_capital: number;
  total_engrams: number;
  mcp_servers_connected: number;
  skills_available: number;
  iovba_groups: number;
  system_health: number;
}
