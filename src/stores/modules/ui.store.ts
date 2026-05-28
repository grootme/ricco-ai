/**
 * UI Store - Estado de interfaz de usuario
 * 
 * SRP: Solo maneja estado de UI
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';

interface UIState {
  sidebarOpen: boolean;
  theme: 'light' | 'dark' | 'system';
  activeTab: string;
  toggleSidebar: () => void;
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  setActiveTab: (tab: string) => void;
}

export const useUIStore = create<UIState>()(
  devtools(
    persist(
      (set) => ({
        sidebarOpen: true,
        theme: 'system',
        activeTab: 'dashboard',
        toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
        setTheme: (theme) => set({ theme }),
        setActiveTab: (tab) => set({ activeTab: tab }),
      }),
      { name: 'ui-store' }
    ),
    { name: 'ui-store' }
  )
);
