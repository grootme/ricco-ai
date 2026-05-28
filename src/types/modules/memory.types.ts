/**
 * Memory Types - Tipos relacionados con memoria
 * 
 * SRP: Solo tipos de memoria
 * OCP: Extensible sin modificar
 */

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
