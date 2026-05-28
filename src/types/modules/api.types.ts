/**
 * API Types - Tipos relacionados con API responses
 * 
 * SRP: Solo tipos de API
 * OCP: Extensible sin modificar
 */

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

export interface BlueprintComponent {
  name: string;
  type: 'retriever' | 'llm' | 'vector_store' | 'tool' | 'workflow';
  config: Record<string, unknown>;
}

export interface NVIDIABlueprint {
  id: string;
  name: string;
  description: string;
  domain: string;
  repo_url: string;
  components: BlueprintComponent[];
  agents: unknown[];
  status: 'available' | 'implemented' | 'partial';
}
