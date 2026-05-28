/**
 * Agent Types - Tipos relacionados con agentes
 * 
 * SRP: Solo tipos de agentes
 * OCP: Extensible sin modificar
 */

import { IOVBADomain, IOVBARole } from './index';

export interface AgentMetrics {
  total_interactions: number;
  success_rate: number;
  avg_response_time: number;
  capital_growth: number;
  last_interaction: string;
}

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
