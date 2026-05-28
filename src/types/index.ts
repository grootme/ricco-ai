/**
 * NEXUS - Neural Execution Unified System
 * Sistema operativo semántico basado en Capital Cognitivo
 * 
 * Plataforma SaaS para orquestación de agentes IOVBA
 */

// ============================================
// PLATFORM BRANDING
// ============================================

export const PLATFORM_BRAND = {
  name: 'NEXUS',
  fullName: 'Neural Execution Unified System',
  tagline: 'Intelligent Agent Orchestration',
  version: '2.0.0',
} as const

// ============================================
// IOVBA DOMAIN BRANDING
// ============================================

export interface IOVBADomainBrand {
  domain: IOVBADomain
  name: string
  elegantName: string
  tagline: string
  icon: string
  color: string
  description: string
}

export const IOVBA_DOMAIN_BRANDING: Record<IOVBADomain, IOVBADomainBrand> = {
  swe: {
    domain: 'swe',
    name: 'Software Engineering',
    elegantName: 'CODEX',
    tagline: 'Architecting Digital Excellence',
    icon: 'Code',
    color: '#3B82F6',
    description: 'Unidad de ingeniería de software para desarrollo, testing y arquitectura de sistemas',
  },
  salud: {
    domain: 'salud',
    name: 'Salud y Medicina',
    elegantName: 'VITALIS',
    tagline: 'Advancing Healthcare Intelligence',
    icon: 'Heart',
    color: '#EF4444',
    description: 'Unidad de salud para diagnóstico, investigación médica y análisis clínico',
  },
  deportes: {
    domain: 'deportes',
    name: 'Deportes',
    elegantName: 'ATHLON',
    tagline: 'Peak Performance Analytics',
    icon: 'Trophy',
    color: '#F59E0B',
    description: 'Unidad de análisis deportivo para performance, estadísticas y predicciones',
  },
  noticias: {
    domain: 'noticias',
    name: 'Noticias y Periodismo',
    elegantName: 'VERITAS',
    tagline: 'Truth Through Intelligence',
    icon: 'Newspaper',
    color: '#6366F1',
    description: 'Unidad de noticias para investigación, verificación y análisis periodístico',
  },
  quimica: {
    domain: 'quimica',
    name: 'Química',
    elegantName: 'ALCHEMY',
    tagline: 'Molecular Intelligence',
    icon: 'FlaskConical',
    color: '#8B5CF6',
    description: 'Unidad de investigación química para análisis molecular y síntesis',
  },
  biologia: {
    domain: 'biologia',
    name: 'Biología',
    elegantName: 'GENESIS',
    tagline: 'Life Sciences Intelligence',
    icon: 'Dna',
    color: '#10B981',
    description: 'Unidad de investigación biológica para genómica y análisis de sistemas vivos',
  },
  biotecnologia: {
    domain: 'biotecnologia',
    name: 'Biotecnología',
    elegantName: 'HELIX',
    tagline: 'Engineering Life Solutions',
    icon: 'Atom',
    color: '#14B8A6',
    description: 'Unidad de biotecnología para bioingeniería y aplicaciones terapéuticas',
  },
  geopolitica: {
    domain: 'geopolitica',
    name: 'Geopolítica',
    elegantName: 'DIPLOMAT',
    tagline: 'Strategic Global Intelligence',
    icon: 'Globe',
    color: '#F97316',
    description: 'Unidad de análisis geopolítico para inteligencia estratégica y relaciones internacionales',
  },
  finanzas: {
    domain: 'finanzas',
    name: 'Finanzas',
    elegantName: 'APEX',
    tagline: 'Financial Intelligence Redefined',
    icon: 'TrendingUp',
    color: '#059669',
    description: 'Unidad de análisis financiero para mercados, inversiones y riesgos',
  },
  legal: {
    domain: 'legal',
    name: 'Legal',
    elegantName: 'JUSTITIA',
    tagline: 'Legal Intelligence & Justice',
    icon: 'Scale',
    color: '#7C3AED',
    description: 'Unidad de análisis legal para jurisprudencia, compliance y contratos',
  },
  educacion: {
    domain: 'educacion',
    name: 'Educación',
    elegantName: 'MENTOR',
    tagline: 'Transforming Education Intelligence',
    icon: 'GraduationCap',
    color: '#EC4899',
    description: 'Unidad de educación para aprendizaje personalizado y contenido pedagógico',
  },
  investigacion: {
    domain: 'investigacion',
    name: 'Investigación',
    elegantName: 'PIONEER',
    tagline: 'Pushing Knowledge Boundaries',
    icon: 'Microscope',
    color: '#0EA5E9',
    description: 'Unidad de investigación científica para descubrimiento y publicación académica',
  },
  marketing: {
    domain: 'marketing',
    name: 'Marketing',
    elegantName: 'PRISMA',
    tagline: 'Multifaceted Marketing Intelligence',
    icon: 'Megaphone',
    color: '#D946EF',
    description: 'Unidad de marketing para campañas, análisis de audiencia y optimización',
  },
  custom: {
    domain: 'custom',
    name: 'Personalizado',
    elegantName: 'CUSTOM',
    tagline: 'Tailored Intelligence Solutions',
    icon: 'Settings',
    color: '#64748B',
    description: 'Unidad personalizada para dominios específicos y configuraciones a medida',
  },
}

// ============================================
// IOVBA ROLE BRANDING
// ============================================

export interface IOVBARoleBrand {
  role: IOVBARole
  elegantName: string
  tagline: string
  description: string
  icon: string
  color: string
  gradient: string
}

export const IOVBA_ROLE_BRANDING: Record<IOVBARole, IOVBARoleBrand> = {
  investigador: {
    role: 'investigador',
    elegantName: 'INVESTIGATOR',
    tagline: 'Discovery & Analysis',
    description: 'Investiga profundamente, analiza datos y descubre insights ocultos. Maestro de la investigación y síntesis de información.',
    icon: 'Microscope',
    color: '#3B82F6',
    gradient: 'from-blue-500 to-cyan-500',
  },
  observador: {
    role: 'observador',
    elegantName: 'OBSERVER',
    tagline: 'Monitoring & Patterns',
    description: 'Monitorea sistemas, detecta patrones y anomalías. Guardián de la observación continua y alertas inteligentes.',
    icon: 'Eye',
    color: '#F59E0B',
    gradient: 'from-amber-500 to-orange-500',
  },
  validador: {
    role: 'validador',
    elegantName: 'VALIDATOR',
    tagline: 'Quality & Verification',
    description: 'Valida resultados, asegura calidad y verifica compliance. Campeón de la integridad y exactitud.',
    icon: 'Shield',
    color: '#10B981',
    gradient: 'from-emerald-500 to-teal-500',
  },
  builder: {
    role: 'builder',
    elegantName: 'BUILDER',
    tagline: 'Creation & Implementation',
    description: 'Construye soluciones, implementa sistemas y optimiza código. Arquitecto de la materialización digital.',
    icon: 'Hammer',
    color: '#8B5CF6',
    gradient: 'from-violet-500 to-purple-500',
  },
  asistente: {
    role: 'asistente',
    elegantName: 'ASSISTANT',
    tagline: 'Coordination & Support',
    description: 'Coordina equipos, facilita comunicación y gestiona documentación. Director de orquestación fluida.',
    icon: 'HelpCircle',
    color: '#14B8A6',
    gradient: 'from-teal-500 to-cyan-500',
  },
}

// ============================================
// COGNITIVE CAPITAL TYPES
// ============================================

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

// ============================================
// AGENT TYPES
// ============================================

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

// ============================================
// IOVBA TYPES
// ============================================

export type IOVBARole = 'investigador' | 'observador' | 'validador' | 'builder' | 'asistente';

export interface IOVBAGroup {
  id: string;
  name: string;
  elegant_name: string; // Nuevo: nombre elegante (CODEX, VITALIS, etc.)
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
  branding?: IOVBADomainBrand; // Nuevo: branding del dominio
}

export interface IOVBAMetrics {
  total_tasks: number;
  success_rate: number;
  avg_completion_time: number;
  domain_expertise: number;
}

// Available domains for IOVBA groups
export type IOVBADomain =
  | 'swe'           // Software Engineering -> CODEX
  | 'salud'         // Healthcare -> VITALIS
  | 'deportes'      // Sports -> ATHLON
  | 'noticias'      // News/Journalism -> VERITAS
  | 'quimica'       // Chemistry -> ALCHEMY
  | 'biologia'      // Biology -> GENESIS
  | 'biotecnologia' // Biotechnology -> HELIX
  | 'geopolitica'   // Geopolitics -> DIPLOMAT
  | 'finanzas'      // Finance -> APEX
  | 'legal'         // Legal -> JUSTITIA
  | 'educacion'     // Education -> MENTOR
  | 'investigacion' // Research -> PIONEER
  | 'marketing'     // Marketing -> PRISMA
  | 'custom';       // Custom domain -> CUSTOM

export interface IOVBATemplate {
  domain: IOVBADomain;
  name: string;
  elegant_name: string;
  description: string;
  investigador_config: Partial<AgentProfile>;
  observador_config: Partial<AgentProfile>;
  validador_config: Partial<AgentProfile>;
  builder_config: Partial<AgentProfile>;
  asistente_config: Partial<AgentProfile>;
  branding: IOVBADomainBrand;
}

// ============================================
// TESTING TYPES
// ============================================

export type TestLevel = 'basic' | 'intermediate' | 'advanced' | 'expert' | 'master';

export interface IOVBATestCase {
  id: string;
  name: string;
  description: string;
  level: TestLevel;
  domain: IOVBADomain;
  role?: IOVBARole;
  input: Record<string, unknown>;
  expected_output: Record<string, unknown>;
  validation_rules: ValidationRule[];
  timeout_ms: number;
  tags: string[];
}

export interface ValidationRule {
  type: 'exact' | 'contains' | 'regex' | 'semantic' | 'custom';
  field: string;
  value: string | number | boolean | RegExp;
  weight: number;
}

export interface IOVBATestResult {
  test_id: string;
  group_id: string;
  agent_role?: IOVBARole;
  passed: boolean;
  score: number;
  execution_time_ms: number;
  output: Record<string, unknown>;
  validation_results: ValidationResult[];
  timestamp: string;
}

export interface ValidationResult {
  rule_id: string;
  passed: boolean;
  score: number;
  message: string;
}

export interface IOVBATestSuite {
  id: string;
  name: string;
  description: string;
  domain: IOVBADomain;
  level: TestLevel;
  test_cases: IOVBATestCase[];
  total_tests: number;
  estimated_duration_ms: number;
}

export interface IOVBATestReport {
  suite_id: string;
  group_id: string;
  total_tests: number;
  passed: number;
  failed: number;
  skipped: number;
  score: number;
  level_achieved: TestLevel;
  execution_time_ms: number;
  results: IOVBATestResult[];
  recommendations: string[];
  timestamp: string;
}

// ============================================
// MEMORY TYPES
// ============================================

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

// ============================================
// NVIDIA BLUEPRINT DOMAIN
// ============================================

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

// ============================================
// MCP SERVER TYPES
// ============================================

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

// ============================================
// SKILL TYPES
// ============================================

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

// ============================================
// VECTOR STORE TYPES
// ============================================

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

// ============================================
// API RESPONSE TYPES
// ============================================

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

// ============================================
// DASHBOARD STATS
// ============================================

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

// ============================================
// RICCO AI TYPES - DeerFlow Integration
// ============================================

/**
 * RICCO AI - Plataforma de Agentes Cognitivos
 * Integración con DeerFlow (LangGraph 1.2.0)
 */

// SDD/OpenSpec Workflow Types
export type SDDPhase = 'init' | 'explore' | 'proposal' | 'spec' | 'design' | 'tasks' | 'apply' | 'verify' | 'sync' | 'archive';

export type TDDPhase = 'RED' | 'GREEN' | 'TRIANGULATE' | 'REFACTOR';

export type WorkRouting = 'inline' | 'delegate' | 'sdd';

export type DelegationTrigger = 
  | 'four_file_rule' 
  | 'multi_file_write' 
  | 'pr_rule' 
  | 'incident_rule' 
  | 'long_session';

export interface SDDArtifact {
  phase: SDDPhase;
  path: string;
  content?: string;
  metadata: Record<string, unknown>;
}

export interface SDDProposal {
  change_name: string;
  title: string;
  summary: string;
  motivation: string;
  approach: string;
  alternatives?: string;
}

export interface SDDSpec {
  change_name: string;
  domain: string;
  requirements: string[];
  acceptance_criteria: string[];
  non_goals?: string[];
}

export interface SDDDesign {
  change_name: string;
  architecture: string;
  components: string[];
  interfaces?: string[];
  data_models?: string[];
  risks?: string[];
}

export interface SDDTask {
  id: string;
  name: string;
  description: string;
  dependencies?: string[];
  status: 'pending' | 'in_progress' | 'completed' | 'blocked';
}

export interface TDDRecord {
  test_name: string;
  phase: TDDPhase;
  status: 'passed' | 'failed' | 'skipped';
  output?: string;
  timestamp?: string;
}

// Engram Memory Types
export type MemoryType = 'architecture' | 'decision' | 'bugfix' | 'discovery' | 'user_prompt' | 'session' | 'custom';

export interface EngramMemory {
  id: string;
  title: string;
  content: string;
  type: MemoryType;
  project?: string;
  topic_key?: string;
  what?: string;
  why?: string;
  where?: string;
  learned?: string;
  created_at: string;
  updated_at: string;
}

export interface EngramSearchResult {
  query: string;
  results: EngramMemory[];
  total: number;
}

export interface EngramStats {
  total_memories: number;
  by_type: Record<MemoryType, number>;
  by_project: Record<string, number>;
  oldest_memory?: string;
  newest_memory?: string;
}

// Gentle-Pi Types
export type PersonaMode = 'gentleman' | 'neutral';

export type ThinkingEffort = 'off' | 'low' | 'medium' | 'high' | 'inherit';

export type SubagentType = 'scout' | 'worker' | 'reviewer' | 'context-builder';

export interface ModelAssignment {
  agent_name: string;
  model?: string;
  thinking: ThinkingEffort;
}

export interface SDDPreflightConfig {
  execution_mode: 'interactive' | 'auto';
  artifact_store: 'openspec' | 'engram' | 'both';
  pr_strategy: 'auto-forecast' | 'ask-always' | 'single-pr-default' | 'force-chained';
  review_budget_lines?: number;
}

export interface DelegationCheck {
  triggers_activated: DelegationTrigger[];
  recommendations: string[];
  metrics: {
    files_read: number;
    files_to_write: number;
    tool_calls: number;
    exploratory_reads: number;
    non_mechanical_edits: number;
  };
}

export interface ReviewWorkloadForecast {
  total_lines: number;
  files_changed: number;
  areas_touched: string[];
  risk_level: 'low' | 'medium' | 'high';
  recommendations: string[];
}

// RICCO AI Skill Types
export interface RiccoSkill {
  name: string;
  description: string;
  version: string;
  author: string;
  tags: string[];
  tools: string[];
  category: 'workflow' | 'memory' | 'orchestration';
}

export const RICCO_SKILLS: RiccoSkill[] = [
  {
    name: 'gentle-ai',
    description: 'Gentle AI harness discipline: clarify first, preserve artifacts, use strict TDD',
    version: '1.0.0',
    author: 'Gentleman Programming',
    tags: ['workflow', 'sdd', 'testing', 'orchestration'],
    tools: ['sdd_init', 'sdd_proposal', 'sdd_spec', 'sdd_design', 'sdd_tasks', 'sdd_apply', 'sdd_verify', 'sdd_archive'],
    category: 'workflow',
  },
  {
    name: 'engram',
    description: 'Persistent memory for AI agents: save, search, and retrieve memories',
    version: '1.0.0',
    author: 'Gentleman Programming',
    tags: ['memory', 'persistence', 'sqlite', 'mcp'],
    tools: ['mem_save', 'mem_search', 'mem_context', 'mem_timeline', 'mem_update', 'mem_delete', 'mem_stats', 'mem_session_start', 'mem_session_end'],
    category: 'memory',
  },
  {
    name: 'gentle-pi',
    description: 'Turn Pi into a controlled development harness with SDD/OpenSpec workflows',
    version: '1.0.0',
    author: 'Gentleman Programming',
    tags: ['pi', 'sdd', 'workflow', 'orchestration', 'testing'],
    tools: ['gentle_persona', 'gentle_models', 'sdd_preflight', 'skill_registry_refresh', 'delegate_task', 'check_delegation_triggers', 'forecast_review_workload'],
    category: 'orchestration',
  },
];
