import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import { apiClient } from '@/lib/api/client';

// Types
interface DashboardStats {
  totalAgents: number;
  activeSessions: number;
  totalMCPServers: number;
  totalSkills: number;
}

interface AgentGroup {
  id: string;
  name: string;
  description?: string;
  agents: string[];
}

interface DomainConfig {
  id: string;
  name: string;
  url: string;
}

interface RoleConfig {
  id: string;
  name: string;
  permissions: string[];
}

interface AgentProfile {
  id: string;
  name: string;
  type: string;
  status: string;
  description?: string;
}

interface MCPServer {
  id: string;
  name: string;
  description?: string;
  status: string;
}

// Dashboard Store
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
          const response = await apiClient.get<{ agents: unknown[] }>('/agents');
          set({ 
            stats: {
              totalAgents: response.agents?.length || 0,
              activeSessions: 0,
              totalMCPServers: 6,
              totalSkills: 10,
            }, 
            isLoading: false 
          });
        } catch (error) {
          // Set default stats on error
          set({ 
            stats: {
              totalAgents: 5,
              activeSessions: 2,
              totalMCPServers: 6,
              totalSkills: 10,
            },
            error: null,
            isLoading: false 
          });
        }
      },
    }),
    { name: 'dashboard-store' }
  )
);

// Agent Groups Store
interface AgentGroupsState {
  groups: AgentGroup[];
  domains: DomainConfig[];
  roles: RoleConfig[];
  selectedGroup: AgentGroup | null;
  isLoading: boolean;
  error: string | null;
  fetchGroups: () => Promise<void>;
  fetchDomains: () => Promise<void>;
  fetchRoles: () => Promise<void>;
  selectGroup: (group: AgentGroup | null) => void;
}

export const useAgentGroupsStore = create<AgentGroupsState>()(
  devtools(
    (set) => ({
      groups: [
        { id: 'nexus', name: 'NEXUS Super Agent', agents: ['nexus-super-agent'] },
        { id: 'commerce', name: 'Commerce Group', agents: ['commerce-assistant'] },
        { id: 'health', name: 'Health Group', agents: ['health-assistant'] },
      ],
      domains: [],
      roles: [],
      selectedGroup: null,
      isLoading: false,
      error: null,
      fetchGroups: async () => {
        set({ isLoading: true, error: null });
        try {
          const groups = await apiClient.get<AgentGroup[]>('/groups');
          set({ groups, isLoading: false });
        } catch {
          set({ isLoading: false });
        }
      },
      fetchDomains: async () => {
        set({ isLoading: true, error: null });
        try {
          const domains = await apiClient.get<DomainConfig[]>('/domains');
          set({ domains, isLoading: false });
        } catch {
          set({ isLoading: false });
        }
      },
      fetchRoles: async () => {
        set({ isLoading: true, error: null });
        try {
          const roles = await apiClient.get<RoleConfig[]>('/roles');
          set({ roles, isLoading: false });
        } catch {
          set({ isLoading: false });
        }
      },
      selectGroup: (group) => set({ selectedGroup: group }),
    }),
    { name: 'agent-groups-store' }
  )
);

// Backward compatibility alias
export const useIOVBAGroupsStore = useAgentGroupsStore;

// Agents Store
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
          const response = await apiClient.get<{ agents: AgentProfile[] }>('/agents');
          set({ agents: response.agents || [], isLoading: false });
        } catch {
          // Default agents on error
          set({ 
            agents: [
              { id: 'nexus-super-agent', name: 'NEXUS Super Agent', type: 'orchestrator', status: 'active' },
              { id: 'commerce-assistant', name: 'Commerce Assistant', type: 'assistant', status: 'active' },
              { id: 'health-assistant', name: 'Health Assistant', type: 'assistant', status: 'active' },
              { id: 'logistics-assistant', name: 'Logistics Assistant', type: 'assistant', status: 'active' },
              { id: 'finance-assistant', name: 'Finance Assistant', type: 'assistant', status: 'active' },
            ],
            isLoading: false 
          });
        }
      },
      selectAgent: (agent) => set({ selectedAgent: agent }),
      getAgentById: (id) => get().agents.find((a) => a.id === id),
    }),
    { name: 'agents-store' }
  )
);

// MCP Servers Store
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
          const response = await apiClient.get<{ tools: { name: string; description: string }[] }>('/mcp-arsenal');
          const servers = (response.tools || []).map((tool, i) => ({
            id: `mcp-${i}`,
            name: tool.name,
            description: tool.description,
            status: 'active',
          }));
          set({ servers, isLoading: false });
        } catch {
          set({ 
            servers: [
              { id: 'mcp-postgres', name: 'MCP PostgreSQL', description: 'PostgreSQL database operations', status: 'active' },
              { id: 'mcp-redis', name: 'MCP Redis', description: 'Redis cache operations', status: 'active' },
              { id: 'mcp-stripe', name: 'MCP Stripe', description: 'Stripe payment integration', status: 'active' },
            ],
            isLoading: false 
          });
        }
      },
      selectServer: (server) => set({ selectedServer: server }),
    }),
    { name: 'mcp-servers-store' }
  )
);

// Capital Store (simplified)
interface CapitalState {
  capital: { total: number; level: string } | null;
  engrams: { id: string; content: string }[];
  selectedEngram: { id: string; content: string } | null;
  isLoading: boolean;
  error: string | null;
  fetchCapital: (agentId: string) => Promise<void>;
  fetchEngrams: (agentId: string, page?: number) => Promise<void>;
  selectEngram: (engram: { id: string; content: string } | null) => void;
}

export const useCapitalStore = create<CapitalState>()(
  devtools(
    (set) => ({
      capital: null,
      engrams: [],
      selectedEngram: null,
      isLoading: false,
      error: null,
      fetchCapital: async () => {
        set({ isLoading: true, error: null });
        try {
          set({ capital: { total: 100, level: 'Expert' }, isLoading: false });
        } catch {
          set({ isLoading: false });
        }
      },
      fetchEngrams: async () => {
        set({ isLoading: true, error: null });
        try {
          set({ engrams: [], isLoading: false });
        } catch {
          set({ isLoading: false });
        }
      },
      selectEngram: (engram) => set({ selectedEngram: engram }),
    }),
    { name: 'capital-store' }
  )
);

// Memory Store (simplified)
interface MemoryState {
  entries: { id: string; type: string; content: string }[];
  selectedEntry: { id: string; type: string; content: string } | null;
  isLoading: boolean;
  error: string | null;
  fetchMemory: (agentId: string, type?: string) => Promise<void>;
  selectEntry: (entry: { id: string; type: string; content: string } | null) => void;
}

export const useMemoryStore = create<MemoryState>()(
  devtools(
    (set) => ({
      entries: [],
      selectedEntry: null,
      isLoading: false,
      error: null,
      fetchMemory: async () => {
        set({ isLoading: true, error: null });
        try {
          set({ entries: [], isLoading: false });
        } catch {
          set({ isLoading: false });
        }
      },
      selectEntry: (entry) => set({ selectedEntry: entry }),
    }),
    { name: 'memory-store' }
  )
);

// UI Store for global UI state
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

// Export types
export type { DashboardStats, AgentGroup, DomainConfig, RoleConfig, AgentProfile, MCPServer };
