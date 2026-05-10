import type {
  AgentProfile,
  CognitiveCapital,
  MemoryEntry,
  MCPServer,
  Skill,
  NVIDIABlueprint,
  DashboardStats,
  IOVBAGroup,
  IOVBATemplate,
  IOVBADomain,
  PaginatedResponse,
  Engram,
} from '@/types';

// Backend API base URL - ricco-ai FastAPI backend
const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';
const BACKEND_PORT = process.env.NEXT_PUBLIC_BACKEND_PORT || '8000';

class ApiClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = API_BASE || '';
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    port?: string
  ): Promise<T> {
    const url = port
      ? `${endpoint}?XTransformPort=${port}`
      : endpoint;

    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // Dashboard
  async getDashboardStats(): Promise<DashboardStats> {
    return {
      total_agents: 15,
      active_agents: 12,
      total_capital: 45820,
      total_engrams: 3421,
      mcp_servers_connected: 15,
      skills_available: 28,
      iovba_groups: 3,
      system_health: 98.5,
    };
  }

  // IOVBA Groups - Grupo de agentes orientado a dominio
  async getIOVBAGroups(): Promise<IOVBAGroup[]> {
    return [
      {
        id: 'iovba-swe',
        name: 'SWE Team',
        domain: 'swe',
        description: 'Software Engineering - Desarrollo, debugging, code review y arquitectura',
        status: 'active',
        created_at: '2024-01-15T10:00:00Z',
        agents: {
          investigador: this.createIOVBAAgent('investigador', 'swe', 'Investiga código, documenta y analiza arquitecturas'),
          observador: this.createIOVBAAgent('observador', 'swe', 'Monitorea logs, métricas y comportamientos del sistema'),
          validador: this.createIOVBAAgent('validador', 'swe', 'Code review, testing y validación de calidad'),
          builder: this.createIOVBAAgent('builder', 'swe', 'Implementa features, refactoriza y optimiza código'),
          asistente: this.createIOVBAAgent('asistente', 'swe', 'Coordina tareas y facilita comunicación del equipo'),
        },
        metrics: {
          total_tasks: 156,
          success_rate: 0.94,
          avg_completion_time: 2.3,
          domain_expertise: 0.87,
        },
      },
      {
        id: 'iovba-salud',
        name: 'Salud Team',
        domain: 'salud',
        description: 'Salud y Medicina - Análisis clínico, investigación médica y diagnóstico asistido',
        status: 'active',
        created_at: '2024-02-01T08:00:00Z',
        agents: {
          investigador: this.createIOVBAAgent('investigador', 'salud', 'Investiga literatura médica y estudios clínicos'),
          observador: this.createIOVBAAgent('observador', 'salud', 'Monitorea síntomas, signos vitales y patrones'),
          validador: this.createIOVBAAgent('validador', 'salud', 'Valida diagnósticos y verifica protocolos médicos'),
          builder: this.createIOVBAAgent('builder', 'salud', 'Desarrolla planes de tratamiento y protocolos'),
          asistente: this.createIOVBAAgent('asistente', 'salud', 'Coordina atención y facilita comunicación clínica'),
        },
        metrics: {
          total_tasks: 89,
          success_rate: 0.91,
          avg_completion_time: 3.5,
          domain_expertise: 0.82,
        },
      },
      {
        id: 'iovba-biotecnologia',
        name: 'Biotecnología Team',
        domain: 'biotecnologia',
        description: 'Biotecnología - Investigación, desarrollo de fármacos y análisis genómico',
        status: 'learning',
        created_at: '2024-03-10T14:00:00Z',
        agents: {
          investigador: this.createIOVBAAgent('investigador', 'biotecnologia', 'Investiga secuencias genéticas y compuestos'),
          observador: this.createIOVBAAgent('observador', 'biotecnologia', 'Monitorea experimentos y resultados de laboratorio'),
          validador: this.createIOVBAAgent('validador', 'biotecnologia', 'Valida resultados y verifica reproducibilidad'),
          builder: this.createIOVBAAgent('builder', 'biotecnologia', 'Desarrolla nuevos compuestos y protocolos'),
          asistente: this.createIOVBAAgent('asistente', 'biotecnologia', 'Coordina proyectos y documenta hallazgos'),
        },
        metrics: {
          total_tasks: 34,
          success_rate: 0.78,
          avg_completion_time: 5.2,
          domain_expertise: 0.65,
        },
      },
    ];
  }

  private createIOVBAAgent(role: string, domain: string, description: string): AgentProfile {
    return {
      id: `agent-${domain}-${role}`,
      name: `${role.charAt(0).toUpperCase() + role.slice(1)} ${domain.toUpperCase()}`,
      description,
      domain,
      skills: this.getSkillsForRole(role),
      tools: this.getToolsForDomain(domain),
      mcp_servers: this.getMCPForDomain(domain),
      prompt_template: `Eres el ${role} especializado en ${domain}...`,
      cognitive_capital: {
        agent_id: `agent-${domain}-${role}`,
        total_engrams: Math.floor(Math.random() * 500) + 100,
        total_interactions: Math.floor(Math.random() * 2000) + 500,
        learning_score: 0.7 + Math.random() * 0.25,
        domains: [domain],
        skills: this.getSkillsForRole(role),
        tools: this.getToolsForDomain(domain),
        mcp_servers: this.getMCPForDomain(domain),
        memory_vcs_version: 'v1.2.0',
        last_updated: new Date().toISOString(),
        capital_value: Math.floor(Math.random() * 5000) + 1000,
      },
      status: 'active',
      created_at: '2024-01-15T10:00:00Z',
      updated_at: new Date().toISOString(),
      metrics: {
        total_interactions: Math.floor(Math.random() * 2000) + 500,
        success_rate: 0.85 + Math.random() * 0.12,
        avg_response_time: 0.5 + Math.random() * 2,
        capital_growth: 0.1 + Math.random() * 0.2,
        last_interaction: new Date().toISOString(),
      },
      iovba_role: role as any,
    };
  }

  private getSkillsForRole(role: string): string[] {
    const skillsMap: Record<string, string[]> = {
      investigador: ['web-search', 'data-analysis', 'research-synthesis', 'document-analysis'],
      observador: ['monitoring', 'pattern-recognition', 'anomaly-detection', 'reporting'],
      validador: ['quality-assurance', 'testing', 'review', 'verification'],
      builder: ['implementation', 'development', 'optimization', 'refactoring'],
      asistente: ['coordination', 'communication', 'documentation', 'scheduling'],
    };
    return skillsMap[role] || [];
  }

  private getToolsForDomain(domain: string): string[] {
    const toolsMap: Record<string, string[]> = {
      swe: ['git', 'code-executor', 'linter', 'docker', 'ci-cd'],
      salud: ['medical-db', 'diagnostic-tools', 'imaging', 'lab-results'],
      biotecnologia: ['genomics-db', 'molecular-sim', 'lab-equipment', 'compound-db'],
      deportes: ['stats-analyzer', 'video-analysis', 'performance-tracker'],
      noticias: ['news-api', 'fact-checker', 'sentiment-analyzer'],
      quimica: ['molecule-db', 'reaction-sim', 'safety-checker'],
      biologia: ['species-db', 'cell-sim', 'gene-analyzer'],
      geopolitica: ['maps-api', 'news-aggregator', 'trend-analyzer'],
      finanzas: ['market-data', 'risk-analyzer', 'portfolio-tracker'],
      legal: ['case-law-db', 'contract-analyzer', 'compliance-checker'],
      educacion: ['content-creator', 'quiz-generator', 'progress-tracker'],
      investigacion: ['paper-db', 'citation-manager', 'methodology-guide'],
      marketing: ['analytics', 'social-media', 'campaign-builder'],
      custom: [],
    };
    return toolsMap[domain] || [];
  }

  private getMCPForDomain(domain: string): string[] {
    const baseMCP = ['filesystem', 'github'];
    const domainMCP: Record<string, string[]> = {
      swe: ['docker', 'kubernetes', 'postgresql'],
      salud: ['medical-db', 'hl7-fhir'],
      biotecnologia: ['ncbi', 'uniprot', 'pubmed'],
      deportes: ['stats-api', 'video-processing'],
      noticias: ['brave-search', 'news-api'],
      quimica: ['pubchem', 'chemspider'],
      biologia: ['ncbi', 'ensembl'],
      geopolitica: ['brave-search', 'maps-api'],
      finanzas: ['alpha-vantage', 'coingecko'],
      legal: ['court-api', 'statute-db'],
      educacion: ['lms-integration', 'content-db'],
      investigacion: ['arxiv', 'pubmed', 'semantic-scholar'],
      marketing: ['google-analytics', 'social-apis'],
      custom: [],
    };
    return [...baseMCP, ...(domainMCP[domain] || [])];
  }

  // IOVBA Templates
  async getIOVBATemplates(): Promise<IOVBATemplate[]> {
    const domains: IOVBADomain[] = [
      'swe', 'salud', 'deportes', 'noticias', 'quimica',
      'biologia', 'biotecnologia', 'geopolitica', 'finanzas',
      'legal', 'educacion', 'investigacion', 'marketing'
    ];

    const domainNames: Record<IOVBADomain, string> = {
      swe: 'Software Engineering',
      salud: 'Salud y Medicina',
      deportes: 'Deportes',
      noticias: 'Noticias y Periodismo',
      quimica: 'Química',
      biologia: 'Biología',
      biotecnologia: 'Biotecnología',
      geopolitica: 'Geopolítica',
      finanzas: 'Finanzas',
      legal: 'Legal',
      educacion: 'Educación',
      investigacion: 'Investigación',
      marketing: 'Marketing',
      custom: 'Personalizado',
    };

    return domains.map(domain => ({
      domain,
      name: domainNames[domain],
      description: `Grupo IOVBA especializado en ${domainNames[domain]}`,
      investigador_config: { domain, skills: this.getSkillsForRole('investigador') },
      observador_config: { domain, skills: this.getSkillsForRole('observador') },
      validador_config: { domain, skills: this.getSkillsForRole('validador') },
      builder_config: { domain, skills: this.getSkillsForRole('builder') },
      asistente_config: { domain, skills: this.getSkillsForRole('asistente') },
    }));
  }

  // Agents (individuals)
  async getAgents(page = 1, pageSize = 10): Promise<PaginatedResponse<AgentProfile>> {
    const groups = await this.getIOVBAGroups();
    const agents: AgentProfile[] = [];

    for (const group of groups) {
      agents.push(
        group.agents.investigador,
        group.agents.observador,
        group.agents.validador,
        group.agents.builder,
        group.agents.asistente
      );
    }

    return {
      items: agents.slice((page - 1) * pageSize, page * pageSize),
      total: agents.length,
      page,
      page_size: pageSize,
      total_pages: Math.ceil(agents.length / pageSize),
    };
  }

  async getAgent(id: string): Promise<AgentProfile | null> {
    const response = await this.getAgents();
    return response.items.find(a => a.id === id) || null;
  }

  // Cognitive Capital
  async getCognitiveCapital(agentId: string): Promise<CognitiveCapital> {
    const response = await this.getAgents();
    const agent = response.items.find(a => a.id === agentId);
    if (!agent) throw new Error('Agent not found');
    return agent.cognitive_capital;
  }

  async getEngrams(agentId: string, page = 1, pageSize = 20): Promise<PaginatedResponse<Engram>> {
    const engrams: Engram[] = Array.from({ length: 50 }, (_, i) => ({
      id: `engram-${agentId}-${i}`,
      content: `Learning entry ${i + 1}: Discovered pattern in data analysis workflow that improves accuracy by 15% when using hierarchical summarization...`,
      metadata: {
        source_type: i % 4 === 0 ? 'interaction' : i % 4 === 1 ? 'observation' : i % 4 === 2 ? 'reflection' : 'instruction',
        confidence: 0.7 + Math.random() * 0.3,
        related_skills: ['data-analysis', 'summarization'],
      },
      created_at: new Date(Date.now() - i * 3600000).toISOString(),
      updated_at: new Date().toISOString(),
      access_count: Math.floor(Math.random() * 100),
      importance_score: 0.5 + Math.random() * 0.5,
      source: i % 4 === 0 ? 'interaction' : i % 4 === 1 ? 'observation' : i % 4 === 2 ? 'reflection' : 'instruction',
      tags: ['learning', 'pattern', 'analysis', 'optimization'].slice(0, 1 + (i % 3)),
    }));

    return {
      items: engrams.slice((page - 1) * pageSize, page * pageSize),
      total: engrams.length,
      page,
      page_size: pageSize,
      total_pages: Math.ceil(engrams.length / pageSize),
    };
  }

  // Memory
  async getMemoryEntries(
    agentId: string,
    type?: 'short_term' | 'long_term' | 'episodic' | 'semantic'
  ): Promise<MemoryEntry[]> {
    const entries: MemoryEntry[] = [
      {
        id: 'mem-001',
        agent_id: agentId,
        type: type || 'long_term',
        content: 'User prefers concise responses with bullet points for technical content.',
        metadata: {
          source: 'interaction-feedback',
          context: 'user-preference-learning',
          importance: 0.85,
          tags: ['preference', 'format', 'communication'],
          related_entries: ['mem-002', 'mem-003'],
        },
        created_at: new Date(Date.now() - 86400000).toISOString(),
        relevance_score: 0.92,
      },
      {
        id: 'mem-002',
        agent_id: agentId,
        type: 'episodic',
        content: 'Successfully resolved complex debugging issue using systematic approach: isolate, reproduce, diagnose, fix.',
        metadata: {
          source: 'task-completion',
          context: 'debugging-workflow',
          importance: 0.78,
          tags: ['debugging', 'workflow', 'success-pattern'],
          related_entries: [],
        },
        created_at: new Date(Date.now() - 172800000).toISOString(),
        relevance_score: 0.88,
      },
      {
        id: 'mem-003',
        agent_id: agentId,
        type: 'semantic',
        content: 'RAG systems combine retrieval and generation for enhanced accuracy. Key components: vector store, embedder, retriever, generator.',
        metadata: {
          source: 'knowledge-extraction',
          context: 'rag-architecture',
          importance: 0.95,
          tags: ['rag', 'architecture', 'knowledge'],
          related_entries: ['mem-001'],
        },
        created_at: new Date(Date.now() - 259200000).toISOString(),
        relevance_score: 0.95,
      },
    ];

    return entries;
  }

  // MCP Servers
  async getMCPServers(): Promise<MCPServer[]> {
    return [
      {
        id: 'mcp-001',
        name: 'GitHub',
        description: 'GitHub repository operations and PR management',
        transport: 'http',
        url: 'http://github-mcp:3000',
        tools: [
          { name: 'create_pr', description: 'Create a pull request', input_schema: {} },
          { name: 'review_pr', description: 'Review a pull request', input_schema: {} },
          { name: 'search_repos', description: 'Search repositories', input_schema: {} },
        ],
        resources: [],
        status: 'connected',
        last_connected: new Date().toISOString(),
      },
      {
        id: 'mcp-002',
        name: 'Filesystem',
        description: 'File system operations with sandboxed access',
        transport: 'stdio',
        command: 'mcp-filesystem',
        tools: [
          { name: 'read_file', description: 'Read file contents', input_schema: {} },
          { name: 'write_file', description: 'Write file contents', input_schema: {} },
          { name: 'list_dir', description: 'List directory contents', input_schema: {} },
        ],
        resources: [],
        status: 'connected',
        last_connected: new Date().toISOString(),
      },
      {
        id: 'mcp-003',
        name: 'Brave Search',
        description: 'Web search using Brave Search API',
        transport: 'http',
        url: 'http://brave-search-mcp:3000',
        tools: [
          { name: 'web_search', description: 'Search the web', input_schema: {} },
          { name: 'news_search', description: 'Search news articles', input_schema: {} },
        ],
        resources: [],
        status: 'connected',
        last_connected: new Date().toISOString(),
      },
      {
        id: 'mcp-004',
        name: 'Docker',
        description: 'Docker container management',
        transport: 'stdio',
        command: 'mcp-docker',
        tools: [
          { name: 'run_container', description: 'Run a container', input_schema: {} },
          { name: 'list_containers', description: 'List running containers', input_schema: {} },
          { name: 'build_image', description: 'Build a Docker image', input_schema: {} },
        ],
        resources: [],
        status: 'disconnected',
      },
      {
        id: 'mcp-005',
        name: 'PostgreSQL',
        description: 'PostgreSQL database operations',
        transport: 'stdio',
        command: 'mcp-postgres',
        tools: [
          { name: 'query', description: 'Execute SQL query', input_schema: {} },
          { name: 'list_tables', description: 'List database tables', input_schema: {} },
        ],
        resources: [],
        status: 'connected',
        last_connected: new Date().toISOString(),
      },
    ];
  }

  // Skills
  async getSkills(): Promise<Skill[]> {
    return [
      {
        id: 'skill-001',
        name: 'Web Search',
        description: 'Search the web for information and synthesize results',
        version: '1.0.0',
        category: 'information-retrieval',
        triggers: ['search for', 'find information about', 'look up'],
        prompt_template: 'Search the web for {query} and provide a comprehensive summary...',
        tools_required: ['web-search'],
        mcp_required: ['brave-search'],
        examples: [],
        metadata: {},
      },
      {
        id: 'skill-002',
        name: 'Code Generation',
        description: 'Generate code based on specifications',
        version: '1.0.0',
        category: 'development',
        triggers: ['write code', 'create function', 'implement'],
        prompt_template: 'Generate {language} code for {specification}...',
        tools_required: ['code-executor'],
        mcp_required: ['filesystem'],
        examples: [],
        metadata: {},
      },
      {
        id: 'skill-003',
        name: 'Document Analysis',
        description: 'Analyze and extract insights from documents',
        version: '1.0.0',
        category: 'analysis',
        triggers: ['analyze document', 'extract from', 'summarize document'],
        prompt_template: 'Analyze the provided document and extract {output_type}...',
        tools_required: ['document-reader'],
        mcp_required: ['filesystem'],
        examples: [],
        metadata: {},
      },
    ];
  }

  // NVIDIA Blueprints
  async getNVIDIABlueprints(): Promise<NVIDIABlueprint[]> {
    return [
      {
        id: 'bp-001',
        name: 'Multi-Agent Intelligent Warehouse',
        description: 'Autonomous warehouse management with multi-agent coordination',
        domain: 'logistics',
        repo_url: 'https://github.com/NVIDIA-AI-Blueprints/Multi-Agent-Intelligent-Warehouse',
        components: [
          { name: 'Milvus Vector Store', type: 'vector_store', config: {} },
          { name: 'Hybrid RAG Retriever', type: 'retriever', config: {} },
          { name: 'NIM LLM', type: 'llm', config: {} },
        ],
        agents: [],
        status: 'available',
      },
      {
        id: 'bp-002',
        name: 'Digital Human',
        description: 'Conversational AI with realistic avatar interactions',
        domain: 'customer-service',
        repo_url: 'https://github.com/NVIDIA-AI-Blueprints/digital-human',
        components: [
          { name: 'Riva TTS', type: 'tool', config: {} },
          { name: 'Audio2Face', type: 'tool', config: {} },
          { name: 'NIM LLM', type: 'llm', config: {} },
        ],
        agents: [],
        status: 'partial',
      },
      {
        id: 'bp-003',
        name: 'Visual Search Agent',
        description: 'Image-based search and recommendation system',
        domain: 'e-commerce',
        repo_url: 'https://github.com/NVIDIA-AI-Blueprints/visual-search-agent',
        components: [
          { name: 'CLIP Embeddings', type: 'retriever', config: {} },
          { name: 'Milvus Vector Store', type: 'vector_store', config: {} },
          { name: 'Vision NIM', type: 'llm', config: {} },
        ],
        agents: [],
        status: 'available',
      },
      {
        id: 'bp-004',
        name: 'PDF Document Extraction',
        description: 'Intelligent document processing and extraction',
        domain: 'document-processing',
        repo_url: 'https://github.com/NVIDIA-AI-Blueprints/pdf-extraction',
        components: [
          { name: 'NVIDIA Ingest', type: 'tool', config: {} },
          { name: 'OCR Engine', type: 'tool', config: {} },
          { name: 'Milvus Vector Store', type: 'vector_store', config: {} },
        ],
        agents: [],
        status: 'implemented',
      },
    ];
  }
}

export const apiClient = new ApiClient();
export default apiClient;
