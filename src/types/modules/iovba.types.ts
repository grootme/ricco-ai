/**
 * IOVBA Types - Tipos específicos del sistema IOVBA
 * 
 * SRP: Solo tipos IOVBA
 * OCP: Extensible sin modificar
 */

import { IOVBADomain, IOVBARole } from './index';
import { AgentProfile } from './agent.types';

export interface IOVBAMetrics {
  total_tasks: number;
  success_rate: number;
  avg_completion_time: number;
  domain_expertise: number;
}

export interface IOVBAGroup {
  id: string;
  name: string;
  elegant_name: string;
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
  branding?: DomainBrand;
}

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
  branding: DomainBrand;
}

export interface DomainBrand {
  domain: string;
  name: string;
  elegantName: string;
  tagline: string;
  icon: string;
  color: string;
  description: string;
}
