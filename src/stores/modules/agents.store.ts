/**
 * Agents Store - Estado de agentes
 * 
 * SRP: Solo maneja estado de agentes
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type { AgentProfile } from '@/types';
import { agentClient } from '@/lib/api/modules/agent-client';

interface AgentsState {
  agents: AgentProfile[];
  selectedAgent: AgentProfile | null;
  isLoading: boolean;
  error: string | null;
  fetchAgents: () => Promise<void>;
  selectAgent: (agent: AgentProfile | null) => void;
  getAgentById: (id: string) => AgentProfile | undefined;
}

export const useAgentsStore = create<AgentsState>()(
  devtools(
    (set, get) => ({
      agents: [],
      selectedAgent: null,
      isLoading: false,
      error: null,
      fetchAgents: async () => {
        set({ isLoading: true, error: null });
        try {
          const response = await agentClient.getAgents();
          set({ agents: response.items, isLoading: false });
        } catch (error) {
          set({ error: (error as Error).message, isLoading: false });
        }
      },
      selectAgent: (agent) => set({ selectedAgent: agent }),
      getAgentById: (id) => get().agents.find((a) => a.id === id),
    }),
    { name: 'agents-store' }
  )
);
