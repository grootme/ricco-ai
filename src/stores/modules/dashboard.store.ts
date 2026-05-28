/**
 * Dashboard Store - Estado del dashboard
 * 
 * SRP: Solo maneja estado del dashboard
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type { DashboardStats } from '@/types';
import { dashboardClient } from '@/lib/api/modules/dashboard-client';

interface DashboardState {
  stats: DashboardStats | null;
  isLoading: boolean;
  error: string | null;
  fetchStats: () => Promise<void>;
}

export const useDashboardStore = create<DashboardState>()(
  devtools(
    (set) => ({
      stats: null,
      isLoading: false,
      error: null,
      fetchStats: async () => {
        set({ isLoading: true, error: null });
        try {
          const stats = await dashboardClient.getDashboardStats();
          set({ stats, isLoading: false });
        } catch (error) {
          set({ error: (error as Error).message, isLoading: false });
        }
      },
    }),
    { name: 'dashboard-store' }
  )
);
