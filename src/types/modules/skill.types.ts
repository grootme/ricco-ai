/**
 * Skill Types - Tipos relacionados con habilidades
 * 
 * SRP: Solo tipos de skills
 * OCP: Extensible sin modificar
 */

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
