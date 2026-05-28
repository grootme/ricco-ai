/**
 * IOVBA Groups Store - Estado de grupos IOVBA
 * 
 * SRP: Solo maneja estado de grupos IOVBA
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type { IOVBAGroup, IOVBATemplate } from '@/types';
import { iovbaClient } from '@/lib/api/modules/iovba-client';

interface IOVBAGroupsState {
  groups: IOVBAGroup[];
  templates: IOVBATemplate[];
  selectedGroup: IOVBAGroup | null;
  isLoading: boolean;
  error: string | null;
  fetchGroups: () => Promise<void>;
  fetchTemplates: () => Promise<void>;
  selectGroup: (group: IOVBAGroup | null) => void;
}

export const useIOVBAGroupsStore = create<IOVBAGroupsState>()(
  devtools(
    (set) => ({
      groups: [],
      templates: [],
      selectedGroup: null,
      isLoading: false,
      error: null,
      fetchGroups: async () => {
        set({ isLoading: true, error: null });
        try {
          const groups = await iovbaClient.getIOVBAGroups();
          set({ groups, isLoading: false });
        } catch (error) {
          set({ error: (error as Error).message, isLoading: false });
        }
      },
      fetchTemplates: async () => {
        set({ isLoading: true, error: null });
        try {
          const templates = await iovbaClient.getIOVBATemplates();
          set({ templates, isLoading: false });
        } catch (error) {
          set({ error: (error as Error).message, isLoading: false });
        }
      },
      selectGroup: (group) => set({ selectedGroup: group }),
    }),
    { name: 'iovba-groups-store' }
  )
);
