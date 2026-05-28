/**
 * Capital Store - Estado de capital cognitivo
 * 
 * SRP: Solo maneja estado de capital cognitivo
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type { CognitiveCapital, Engram } from '@/types';
import { agentClient } from '@/lib/api/modules/agent-client';
import { memoryClient } from '@/lib/api/modules/memory-client';

interface CapitalState {
  capital: CognitiveCapital | null;
  engrams: Engram[];
  selectedEngram: Engram | null;
  currentPage: number;
  totalPages: number;
  isLoading: boolean;
  error: string | null;
  fetchCapital: (agentId: string) => Promise<void>;
  fetchEngrams: (agentId: string, page?: number) => Promise<void>;
  selectEngram: (engram: Engram | null) => void;
}

export const useCapitalStore = create<CapitalState>()(
  devtools(
    (set) => ({
      capital: null,
      engrams: [],
      selectedEngram: null,
      currentPage: 1,
      totalPages: 1,
      isLoading: false,
      error: null,
      fetchCapital: async (agentId) => {
        set({ isLoading: true, error: null });
        try {
          const capital = await agentClient.getCognitiveCapital(agentId);
          set({ capital, isLoading: false });
        } catch (error) {
          set({ error: (error as Error).message, isLoading: false });
        }
      },
      fetchEngrams: async (agentId, page = 1) => {
        set({ isLoading: true, error: null });
        try {
          const response = await memoryClient.getEngrams(agentId, page);
          set({
            engrams: response.items,
            currentPage: page,
            totalPages: response.total_pages,
            isLoading: false,
          });
        } catch (error) {
          set({ error: (error as Error).message, isLoading: false });
        }
      },
      selectEngram: (engram) => set({ selectedEngram: engram }),
    }),
    { name: 'capital-store' }
  )
);
