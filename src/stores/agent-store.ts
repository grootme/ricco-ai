// ============================================
// STORE PRINCIPAL DEL ECOSISTEMA DE AGENTES
// ============================================

import { create } from 'zustand';
import type {
  IAgent,
  ILocalSkill,
  IRemoteSkill,
  IMemory,
  ISession,
  IMessage,
  IAgentExecution,
  IHITLRequest,
  DashboardStats,
  AgentType,
  AgentStatus,
  SkillCategory,
  MemoryType,
} from '@/types/agent';

// ============================================
// ESTADO DE AGENTES
// ============================================

interface AgentState {
  agents: IAgent[];
  selectedAgent: IAgent | null;
  leadAgent: IAgent | null;
  subAgents: IAgent[];
  isLoading: boolean;
  error: string | null;
  
  // Actions
  setAgents: (agents: IAgent[]) => void;
  addAgent: (agent: IAgent) => void;
  updateAgent: (id: string, data: Partial<IAgent>) => void;
  removeAgent: (id: string) => void;
  selectAgent: (agent: IAgent | null) => void;
  setLeadAgent: (agent: IAgent | null) => void;
  setSubAgents: (agents: IAgent[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useAgentStore = create<AgentState>((set) => ({
  agents: [],
  selectedAgent: null,
  leadAgent: null,
  subAgents: [],
  isLoading: false,
  error: null,
  
  setAgents: (agents) => set({ agents }),
  addAgent: (agent) => set((state) => ({ 
    agents: [...state.agents, agent],
    subAgents: agent.type !== 'LEAD' 
      ? [...state.subAgents, agent] 
      : state.subAgents
  })),
  updateAgent: (id, data) => set((state) => ({
    agents: state.agents.map((a) => a.id === id ? { ...a, ...data } : a),
    selectedAgent: state.selectedAgent?.id === id 
      ? { ...state.selectedAgent, ...data } 
      : state.selectedAgent,
    leadAgent: state.leadAgent?.id === id 
      ? { ...state.leadAgent, ...data } 
      : state.leadAgent,
  })),
  removeAgent: (id) => set((state) => ({
    agents: state.agents.filter((a) => a.id !== id),
    selectedAgent: state.selectedAgent?.id === id ? null : state.selectedAgent,
    leadAgent: state.leadAgent?.id === id ? null : state.leadAgent,
    subAgents: state.subAgents.filter((a) => a.id !== id),
  })),
  selectAgent: (agent) => set({ selectedAgent: agent }),
  setLeadAgent: (agent) => set({ leadAgent: agent }),
  setSubAgents: (agents) => set({ subAgents: agents }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
}));

// ============================================
// ESTADO DE SKILLS
// ============================================

interface SkillState {
  localSkills: ILocalSkill[];
  remoteSkills: IRemoteSkill[];
  selectedSkill: ILocalSkill | IRemoteSkill | null;
  isLoading: boolean;
  error: string | null;
  
  // Filtros
  categoryFilter: SkillCategory | null;
  searchQuery: string;
  
  // Actions
  setLocalSkills: (skills: ILocalSkill[]) => void;
  setRemoteSkills: (skills: IRemoteSkill[]) => void;
  addLocalSkill: (skill: ILocalSkill) => void;
  addRemoteSkill: (skill: IRemoteSkill) => void;
  updateLocalSkill: (id: string, data: Partial<ILocalSkill>) => void;
  updateRemoteSkill: (id: string, data: Partial<IRemoteSkill>) => void;
  removeLocalSkill: (id: string) => void;
  removeRemoteSkill: (id: string) => void;
  selectSkill: (skill: ILocalSkill | IRemoteSkill | null) => void;
  setCategoryFilter: (category: SkillCategory | null) => void;
  setSearchQuery: (query: string) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useSkillStore = create<SkillState>((set) => ({
  localSkills: [],
  remoteSkills: [],
  selectedSkill: null,
  isLoading: false,
  error: null,
  categoryFilter: null,
  searchQuery: '',
  
  setLocalSkills: (skills) => set({ localSkills: skills }),
  setRemoteSkills: (skills) => set({ remoteSkills: skills }),
  addLocalSkill: (skill) => set((state) => ({ 
    localSkills: [...state.localSkills, skill] 
  })),
  addRemoteSkill: (skill) => set((state) => ({ 
    remoteSkills: [...state.remoteSkills, skill] 
  })),
  updateLocalSkill: (id, data) => set((state) => ({
    localSkills: state.localSkills.map((s) => s.id === id ? { ...s, ...data } : s),
  })),
  updateRemoteSkill: (id, data) => set((state) => ({
    remoteSkills: state.remoteSkills.map((s) => s.id === id ? { ...s, ...data } : s),
  })),
  removeLocalSkill: (id) => set((state) => ({
    localSkills: state.localSkills.filter((s) => s.id !== id),
  })),
  removeRemoteSkill: (id) => set((state) => ({
    remoteSkills: state.remoteSkills.filter((s) => s.id !== id),
  })),
  selectSkill: (skill) => set({ selectedSkill: skill }),
  setCategoryFilter: (category) => set({ categoryFilter: category }),
  setSearchQuery: (query) => set({ searchQuery: query }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
}));

// ============================================
// ESTADO DE MEMORIA
// ============================================

interface MemoryState {
  memories: IMemory[];
  recentMemories: IMemory[];
  searchResults: IMemory[];
  selectedMemory: IMemory | null;
  isLoading: boolean;
  error: string | null;
  
  // Filtros
  typeFilter: MemoryType | null;
  categoryFilter: string | null;
  
  // Actions
  setMemories: (memories: IMemory[]) => void;
  setRecentMemories: (memories: IMemory[]) => void;
  setSearchResults: (memories: IMemory[]) => void;
  addMemory: (memory: IMemory) => void;
  updateMemory: (id: string, data: Partial<IMemory>) => void;
  removeMemory: (id: string) => void;
  selectMemory: (memory: IMemory | null) => void;
  setTypeFilter: (type: MemoryType | null) => void;
  setCategoryFilter: (category: string | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
}

export const useMemoryStore = create<MemoryState>((set) => ({
  memories: [],
  recentMemories: [],
  searchResults: [],
  selectedMemory: null,
  isLoading: false,
  error: null,
  typeFilter: null,
  categoryFilter: null,
  
  setMemories: (memories) => set({ memories }),
  setRecentMemories: (memories) => set({ recentMemories: memories }),
  setSearchResults: (memories) => set({ searchResults: memories }),
  addMemory: (memory) => set((state) => ({ 
    memories: [...state.memories, memory],
    recentMemories: [memory, ...state.recentMemories].slice(0, 10),
  })),
  updateMemory: (id, data) => set((state) => ({
    memories: state.memories.map((m) => m.id === id ? { ...m, ...data } : m),
  })),
  removeMemory: (id) => set((state) => ({
    memories: state.memories.filter((m) => m.id !== id),
  })),
  selectMemory: (memory) => set({ selectedMemory: memory }),
  setTypeFilter: (type) => set({ typeFilter: type }),
  setCategoryFilter: (category) => set({ categoryFilter: category }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
}));

// ============================================
// ESTADO DE SESIÓN ACTIVA
// ============================================

interface SessionState {
  activeSession: ISession | null;
  messages: IMessage[];
  isTyping: boolean;
  inputText: string;
  
  // Actions
  setActiveSession: (session: ISession | null) => void;
  setMessages: (messages: IMessage[]) => void;
  addMessage: (message: IMessage) => void;
  updateMessage: (id: string, data: Partial<IMessage>) => void;
  setTyping: (typing: boolean) => void;
  setInputText: (text: string) => void;
  clearMessages: () => void;
}

export const useSessionStore = create<SessionState>((set) => ({
  activeSession: null,
  messages: [],
  isTyping: false,
  inputText: '',
  
  setActiveSession: (session) => set({ activeSession: session }),
  setMessages: (messages) => set({ messages }),
  addMessage: (message) => set((state) => ({ 
    messages: [...state.messages, message] 
  })),
  updateMessage: (id, data) => set((state) => ({
    messages: state.messages.map((m) => m.id === id ? { ...m, ...data } : m),
  })),
  setTyping: (typing) => set({ isTyping: typing }),
  setInputText: (text) => set({ inputText: text }),
  clearMessages: () => set({ messages: [] }),
}));

// ============================================
// ESTADO DE EJECUCIONES
// ============================================

interface ExecutionState {
  executions: IAgentExecution[];
  activeExecution: IAgentExecution | null;
  isExecuting: boolean;
  progress: number;
  
  // Actions
  setExecutions: (executions: IAgentExecution[]) => void;
  addExecution: (execution: IAgentExecution) => void;
  updateExecution: (id: string, data: Partial<IAgentExecution>) => void;
  setActiveExecution: (execution: IAgentExecution | null) => void;
  setExecuting: (executing: boolean) => void;
  setProgress: (progress: number) => void;
}

export const useExecutionStore = create<ExecutionState>((set) => ({
  executions: [],
  activeExecution: null,
  isExecuting: false,
  progress: 0,
  
  setExecutions: (executions) => set({ executions }),
  addExecution: (execution) => set((state) => ({ 
    executions: [execution, ...state.executions].slice(0, 100),
  })),
  updateExecution: (id, data) => set((state) => ({
    executions: state.executions.map((e) => e.id === id ? { ...e, ...data } : e),
  })),
  setActiveExecution: (execution) => set({ activeExecution: execution }),
  setExecuting: (executing) => set({ isExecuting: executing }),
  setProgress: (progress) => set({ progress }),
}));

// ============================================
// ESTADO DE HITL
// ============================================

interface HITLState {
  requests: IHITLRequest[];
  pendingRequests: IHITLRequest[];
  selectedRequest: IHITLRequest | null;
  
  // Actions
  setRequests: (requests: IHITLRequest[]) => void;
  setPendingRequests: (requests: IHITLRequest[]) => void;
  addRequest: (request: IHITLRequest) => void;
  updateRequest: (id: string, data: Partial<IHITLRequest>) => void;
  selectRequest: (request: IHITLRequest | null) => void;
}

export const useHITLStore = create<HITLState>((set) => ({
  requests: [],
  pendingRequests: [],
  selectedRequest: null,
  
  setRequests: (requests) => set({ requests }),
  setPendingRequests: (requests) => set({ pendingRequests: requests }),
  addRequest: (request) => set((state) => ({ 
    requests: [request, ...state.requests],
    pendingRequests: request.status === 'PENDING' 
      ? [request, ...state.pendingRequests] 
      : state.pendingRequests,
  })),
  updateRequest: (id, data) => set((state) => ({
    requests: state.requests.map((r) => r.id === id ? { ...r, ...data } : r),
    pendingRequests: state.pendingRequests.filter((r) => 
      r.id === id && data.status && data.status !== 'PENDING' ? false : true
    ),
  })),
  selectRequest: (request) => set({ selectedRequest: request }),
}));

// ============================================
// ESTADO DEL DASHBOARD
// ============================================

interface DashboardState {
  stats: DashboardStats | null;
  isLoading: boolean;
  lastUpdated: Date | null;
  
  // Actions
  setStats: (stats: DashboardStats) => void;
  setLoading: (loading: boolean) => void;
  refreshStats: () => Promise<void>;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  stats: null,
  isLoading: false,
  lastUpdated: null,
  
  setStats: (stats) => set({ stats, lastUpdated: new Date() }),
  setLoading: (loading) => set({ isLoading: loading }),
  refreshStats: async () => {
    set({ isLoading: true });
    try {
      const response = await fetch('/api/dashboard/stats');
      if (response.ok) {
        const data = await response.json();
        set({ stats: data.data, lastUpdated: new Date() });
      }
    } catch (error) {
      console.error('Error refreshing stats:', error);
    } finally {
      set({ isLoading: false });
    }
  },
}));

// ============================================
// ESTADO DE UI
// ============================================

interface UIState {
  sidebarOpen: boolean;
  activeTab: string;
  theme: 'light' | 'dark' | 'system';
  notifications: Array<{
    id: string;
    type: 'success' | 'error' | 'warning' | 'info';
    message: string;
    timestamp: Date;
  }>;
  
  // Actions
  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setActiveTab: (tab: string) => void;
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
  addNotification: (notification: Omit<UIState['notifications'][0], 'id' | 'timestamp'>) => void;
  removeNotification: (id: string) => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  activeTab: 'dashboard',
  theme: 'system',
  notifications: [],
  
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setActiveTab: (tab) => set({ activeTab: tab }),
  setTheme: (theme) => set({ theme }),
  addNotification: (notification) => set((state) => ({
    notifications: [
      ...state.notifications,
      { ...notification, id: crypto.randomUUID(), timestamp: new Date() },
    ].slice(-10),
  })),
  removeNotification: (id) => set((state) => ({
    notifications: state.notifications.filter((n) => n.id !== id),
  })),
}));
