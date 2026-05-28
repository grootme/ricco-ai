/**
 * Skills Store - Estado de Skills
 * 
 * SRP: Solo maneja estado de Skills
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type { Skill } from '@/types';
import { skillClient } from '@/lib/api/modules/skill-client';

interface SkillsState {
  skills: Skill[];
  selectedSkill: Skill | null;
  isLoading: boolean;
  error: string | null;
  fetchSkills: () => Promise<void>;
  selectSkill: (skill: Skill | null) => void;
}

export const useSkillsStore = create<SkillsState>()(
  devtools(
    (set) => ({
      skills: [],
      selectedSkill: null,
      isLoading: false,
      error: null,
      fetchSkills: async () => {
        set({ isLoading: true, error: null });
        try {
          const skills = await skillClient.getSkills();
          set({ skills, isLoading: false });
        } catch (error) {
          set({ error: (error as Error).message, isLoading: false });
        }
      },
      selectSkill: (skill) => set({ selectedSkill: skill }),
    }),
    { name: 'skills-store' }
  )
);
