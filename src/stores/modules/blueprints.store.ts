/**
 * Blueprints Store - Estado de NVIDIA Blueprints
 * 
 * SRP: Solo maneja estado de Blueprints
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type { NVIDIABlueprint } from '@/types';
import { blueprintClient } from '@/lib/api/modules/blueprint-client';

interface BlueprintsState {
  blueprints: NVIDIABlueprint[];
  selectedBlueprint: NVIDIABlueprint | null;
  isLoading: boolean;
  error: string | null;
  fetchBlueprints: () => Promise<void>;
  selectBlueprint: (blueprint: NVIDIABlueprint | null) => void;
}

export const useBlueprintsStore = create<BlueprintsState>()(
  devtools(
    (set) => ({
      blueprints: [],
      selectedBlueprint: null,
      isLoading: false,
      error: null,
      fetchBlueprints: async () => {
        set({ isLoading: true, error: null });
        try {
          const blueprints = await blueprintClient.getNVIDIABlueprints();
          set({ blueprints, isLoading: false });
        } catch (error) {
          set({ error: (error as Error).message, isLoading: false });
        }
      },
      selectBlueprint: (blueprint) => set({ selectedBlueprint: blueprint }),
    }),
    { name: 'blueprints-store' }
  )
);
