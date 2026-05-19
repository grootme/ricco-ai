import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import type {
  AgentProfile,
  CognitiveCapital,
  MemoryEntry,
  MCPServer,
  Skill,
  NVIDIABlueprint,
  DashboardStats,
  AgentGroup,
  DomainConfig,
  RoleConfig,
  Engram,
  PlatformConfig,
  NEXUSConfig,
} from '@/types';
import apiClient from '@/lib/api/client';

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
          const stats = await apiClient.getDashboardStats();
          set({ stats, isLoading: false });
        } catch (error) {
          set({ error: (error as Error).message, isLoading: false });
        }
      },
    }),
    { name: 'dashboard-store' }
  )
);

// Agent Groups Store (renamed from IOVBAGroupsStore)
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
      groups: [],
      domains: [],
      roles: [],
      selectedGroup: null,
      isLoading: false,
      error: null,
      fetchGroups: async () => {
        set({ isLoading: true, error: null });
        try {
          const groups = await apiClient.getAgentGroups();
          set({ groups, isLoading: false });
        } catch (error) {
          set({ error: (error as Error).message, isLoading: false });
        }
      },
      fetchDomains: async () => {
        set({ isLoading: true, error: null });
        try {
          const domains = await apiClient.getDomains();
          set({ domains, isLoading: false });
        } catch (error) {
          set({ error: (error as Error).message, isLoading: false });
        }
      },
      fetchRoles: async () => {
        set({ isLoading: true, error: null });
        try {
          const roles = await apiClient.getRoles();
          set({ roles, isLoading: false });
        } catch (error) {
          set({ error: (error as Error).message, isLoading: false });
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
          const response = await apiClient.getAgents();
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

// Cognitive Capital Store
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
          const capital = await apiClient.getCognitiveCapital(agentId);
          set({ capital, isLoading: false });
        } catch (error) {
          set({ error: (error as Error).message, isLoading: false });
        }
      },
      fetchEngrams: async (agentId, page = 1) => {
        set({ isLoading: true, error: null });
        try {
          const response = await apiClient.getEngrams(agentId, page);
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

// Memory Store
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
          const entries = await apiClient.getMemoryEntries(agentId, type);
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
          const servers = await apiClient.getMCPServers();
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

// Skills Store
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
          const skills = await apiClient.getSkills();
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

// Blueprints Store
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
          const blueprints = await apiClient.getNVIDIABlueprints();
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

// Platform Configuration Store
interface PlatformState {
  config: PlatformConfig | null;
  nexusConfig: NEXUSConfig | null;
  isLoading: boolean;
  error: string | null;
  fetchPlatformConfig: () => Promise<void>;
  fetchNEXUSConfig: () => Promise<void>;
}

export const usePlatformStore = create<PlatformState>()(
  devtools(
    (set) => ({
      config: null,
      nexusConfig: null,
      isLoading: false,
      error: null,
      fetchPlatformConfig: async () => {
        set({ isLoading: true, error: null });
        try {
          const config = await apiClient.getPlatformConfig();
          set({ config, isLoading: false });
        } catch (error) {
          set({ error: (error as Error).message, isLoading: false });
        }
      },
      fetchNEXUSConfig: async () => {
        set({ isLoading: true, error: null });
        try {
          const nexusConfig = await apiClient.getNEXUSConfig();
          set({ nexusConfig, isLoading: false });
        } catch (error) {
          set({ error: (error as Error).message, isLoading: false });
        }
      },
    }),
    { name: 'platform-store' }
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
