/**
 * MCP Servers Store - Estado de MCP Servers
 * 
 * SRP: Solo maneja estado de MCP Servers
 */

import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import type { MCPServer } from '@/types';
import { mcpClient } from '@/lib/api/modules/mcp-client';

interface MCPServersState {
  servers: MCPServer[];
  selectedServer: MCPServer | null;
  isLoading: boolean;
  error: string | null;
  fetchServers: () => Promise<void>;
  selectServer: (server: MCPServer | null) => void;
}

export const useMCPServersStore = create<MCPServersState>()(
  devtools(
    (set) => ({
      servers: [],
      selectedServer: null,
      isLoading: false,
      error: null,
      fetchServers: async () => {
        set({ isLoading: true, error: null });
        try {
          const servers = await mcpClient.getMCPServers();
          set({ servers, isLoading: false });
        } catch (error) {
          set({ error: (error as Error).message, isLoading: false });
        }
      },
      selectServer: (server) => set({ selectedServer: server }),
    }),
    { name: 'mcp-servers-store' }
  )
);
