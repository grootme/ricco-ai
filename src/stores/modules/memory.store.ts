/**
 * Memory Store - Estado de memoria
 * 
 * SRP: Solo maneja estado de memoria
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type { MemoryEntry } from '@/types';
import { memoryClient } from '@/lib/api/modules/memory-client';

interface MemoryState {
  entries: MemoryEntry[];
  selectedEntry: MemoryEntry | null;
  filterType: 'all' | 'short_term' | 'long_term' | 'episodic' | 'semantic';
  searchQuery: string;
  isLoading: boolean;
  error: string | null;
  fetchMemory: (agentId: string, type?: 'short_term' | 'long_term' | 'episodic' | 'semantic') => Promise<void>;
  selectEntry: (entry: MemoryEntry | null) => void;
  setFilterType: (type: 'all' | 'short_term' | 'long_term' | 'episodic' | 'semantic') => void;
  setSearchQuery: (query: string) => void;
}

export const useMemoryStore = create<MemoryState>()(
  devtools(
    (set, get) => ({
      entries: [],
      selectedEntry: null,
      filterType: 'all',
      searchQuery: '',
      isLoading: false,
      error: null,
      fetchMemory: async (agentId, type) => {
        set({ isLoading: true, error: null });
        try {
          const entries = await memoryClient.getMemoryEntries(agentId, type);
          set({ entries, isLoading: false });
        } catch (error) {
          set({ error: (error as Error).message, isLoading: false });
        }
      },
      selectEntry: (entry) => set({ selectedEntry: entry }),
      setFilterType: (type) => set({ filterType: type }),
      setSearchQuery: (query) => set({ searchQuery: query }),
    }),
    { name: 'memory-store' }
  )
);
