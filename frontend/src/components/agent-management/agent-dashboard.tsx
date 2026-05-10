'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Brain,
  Wrench,
  Plug,
  Database,
  FileText,
  Globe,
  Play,
  Users,
  Plus,
  Search,
  Filter,
  MoreVertical,
  Edit,
  Trash2,
  Copy,
  Sparkles
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Progress } from '@/components/ui/progress'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { ScrollArea } from '@/components/ui/scroll-area'

interface AgentProfile {
  id: string
  name: string
  domain: string
  skills: { id: string; name: string; proficiency: number }[]
  tools: { name: string; source: string }[]
  mcps: { name: string; tools: string[] }[]
  memory: { domains: string[]; accessLevel: string }
  prompt: { systemPrompt: string; tone: string }
  executionPattern: string
  orchestrationRole: string
  cognitiveValue: number
  status: 'active' | 'inactive' | 'draft'
}

const mockAgents: AgentProfile[] = [
  {
    id: '1',
    name: 'Commerce Agent',
    domain: 'retail_commerce',
    skills: [
      { id: 's1', name: 'product_search', proficiency: 0.95 },
      { id: 's2', name: 'order_management', proficiency: 0.9 },
      { id: 's3', name: 'payment_processing', proficiency: 0.85 },
    ],
    tools: [
      { name: 'search_api', source: 'mcp' },
      { name: 'payment_api', source: 'mcp' },
    ],
    mcps: [
      { name: 'payment-gateway', tools: ['process_payment', 'refund'] },
      { name: 'inventory-system', tools: ['check_stock', 'reserve'] },
    ],
    memory: { domains: ['commerce', 'orders', 'products'], accessLevel: 'domain' },
    prompt: { systemPrompt: 'You are a helpful commerce assistant...', tone: 'friendly' },
    executionPattern: 'llm',
    orchestrationRole: 'specialist',
    cognitiveValue: 0.78,
    status: 'active',
  },
  {
    id: '2',
    name: 'Health Agent',
    domain: 'healthcare',
    skills: [
      { id: 's1', name: 'symptom_assessment', proficiency: 0.8 },
      { id: 's2', name: 'appointment_scheduling', proficiency: 0.95 },
    ],
    tools: [
      { name: 'booking_api', source: 'mcp' },
    ],
    mcps: [
      { name: 'booking-system', tools: ['book_appointment', 'cancel'] },
    ],
    memory: { domains: ['health', 'appointments'], accessLevel: 'domain' },
    prompt: { systemPrompt: 'You are a health consultation assistant...', tone: 'professional' },
    executionPattern: 'llm',
    orchestrationRole: 'specialist',
    cognitiveValue: 0.65,
    status: 'active',
  },
  {
    id: '3',
    name: 'Lead Orchestrator',
    domain: 'orchestration',
    skills: [
      { id: 's1', name: 'task_routing', proficiency: 0.95 },
      { id: 's2', name: 'agent_coordination', proficiency: 0.95 },
    ],
    tools: [],
    mcps: [],
    memory: { domains: ['orchestration', 'routing'], accessLevel: 'global' },
    prompt: { systemPrompt: 'You are the lead orchestrator...', tone: 'professional' },
    executionPattern: 'sequential',
    orchestrationRole: 'lead',
    cognitiveValue: 0.92,
    status: 'active',
  },
]

const NVIDIA_DOMAINS = [
  { id: 'warehouse_operations', name: 'Warehouse Operations', agents: 5 },
  { id: 'customer_service', name: 'Customer Service', agents: 3 },
  { id: 'video_analytics', name: 'Video Analytics', agents: 4 },
  { id: 'enterprise_rag', name: 'Enterprise RAG', agents: 4 },
  { id: 'drug_discovery', name: 'Drug Discovery', agents: 4 },
  { id: 'healthcare', name: 'Healthcare', agents: 3 },
  { id: 'retail_commerce', name: 'Retail & Commerce', agents: 3 },
  { id: 'orchestration', name: 'Orchestration', agents: 3 },
]

export function AgentManagementDashboard() {
  const [agents, setAgents] = useState<AgentProfile[]>(mockAgents)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedDomain, setSelectedDomain] = useState<string | null>(null)
  const [selectedAgent, setSelectedAgent] = useState<AgentProfile | null>(null)

  const filteredAgents = agents.filter(agent => {
    const matchesSearch = agent.name.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesDomain = !selectedDomain || agent.domain === selectedDomain
    return matchesSearch && matchesDomain
  })

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Left Panel - Agent List */}
      <div className="lg:col-span-1 space-y-4">
        {/* Search & Filter */}
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search agents..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>
          <Button variant="outline" size="icon">
            <Filter className="h-4 w-4" />
          </Button>
        </div>

        {/* Domain Filter */}
        <div className="flex flex-wrap gap-2">
          <Badge
            variant={selectedDomain === null ? 'default' : 'outline'}
            className="cursor-pointer"
            onClick={() => setSelectedDomain(null)}
          >
            All
          </Badge>
          {NVIDIA_DOMAINS.slice(0, 5).map(domain => (
            <Badge
              key={domain.id}
              variant={selectedDomain === domain.id ? 'default' : 'outline'}
              className="cursor-pointer"
              onClick={() => setSelectedDomain(domain.id)}
            >
              {domain.name}
            </Badge>
          ))}
        </div>

        {/* Agent List */}
        <ScrollArea className="h-[600px] pr-4">
          <div className="space-y-3">
            {filteredAgents.map(agent => (
              <motion.div
                key={agent.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                whileHover={{ scale: 1.02 }}
                className="cursor-pointer"
                onClick={() => setSelectedAgent(agent)}
              >
                <Card className={`transition-all ${selectedAgent?.id === agent.id ? 'ring-2 ring-primary' : ''}`}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h3 className="font-semibold">{agent.name}</h3>
                          <Badge variant={agent.status === 'active' ? 'default' : 'secondary'} className="text-xs">
                            {agent.status}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">{agent.domain}</p>
                        <div className="flex items-center gap-4 mt-2">
                          <div className="flex items-center gap-1 text-xs text-muted-foreground">
                            <Brain className="h-3 w-3" />
                            {agent.skills.length} skills
                          </div>
                          <div className="flex items-center gap-1 text-xs text-muted-foreground">
                            <Wrench className="h-3 w-3" />
                            {agent.tools.length} tools
                          </div>
                          <div className="flex items-center gap-1 text-xs text-muted-foreground">
                            <Database className="h-3 w-3" />
                            {agent.memory.domains.length} domains
                          </div>
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-2">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon" className="h-8 w-8">
                              <MoreVertical className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem>
                              <Edit className="h-4 w-4 mr-2" /> Edit
                            </DropdownMenuItem>
                            <DropdownMenuItem>
                              <Copy className="h-4 w-4 mr-2" /> Duplicate
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem className="text-destructive">
                              <Trash2 className="h-4 w-4 mr-2" /> Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                        <div className="text-xs">
                          <span className="text-muted-foreground">Capital: </span>
                          <span className="font-semibold text-primary">{(agent.cognitiveValue * 100).toFixed(0)}%</span>
                        </div>
                      </div>
                    </div>
                    <div className="mt-3">
                      <Progress value={agent.cognitiveValue * 100} className="h-1" />
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>
        </ScrollArea>

        {/* Create Agent Button */}
        <Button className="w-full">
          <Plus className="h-4 w-4 mr-2" />
          Create New Agent
        </Button>
      </div>

      {/* Right Panel - Agent Details */}
      <div className="lg:col-span-2">
        {selectedAgent ? (
          <AgentProfileView agent={selectedAgent} />
        ) : (
          <Card className="h-full flex items-center justify-center">
            <CardContent className="text-center py-20">
              <Sparkles className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">Select an Agent</h3>
              <p className="text-muted-foreground">Choose an agent from the list to view details</p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}

function AgentProfileView({ agent }: { agent: AgentProfile }) {
  const [activeTab, setActiveTab] = useState('overview')

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-xl">{agent.name}</CardTitle>
            <CardDescription>{agent.domain}</CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline">{agent.orchestrationRole}</Badge>
            <Badge variant="secondary">{agent.executionPattern}</Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid grid-cols-5 w-full">
            <TabsTrigger value="overview">
              <Brain className="h-4 w-4 mr-2" />
              Overview
            </TabsTrigger>
            <TabsTrigger value="skills">
              <Sparkles className="h-4 w-4 mr-2" />
              Skills
            </TabsTrigger>
            <TabsTrigger value="tools">
              <Wrench className="h-4 w-4 mr-2" />
              Tools
            </TabsTrigger>
            <TabsTrigger value="mcp">
              <Plug className="h-4 w-4 mr-2" />
              MCP
            </TabsTrigger>
            <TabsTrigger value="memory">
              <Database className="h-4 w-4 mr-2" />
              Memory
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="mt-4">
            <div className="grid grid-cols-2 gap-4">
              {/* Stats Grid */}
              <Card>
                <CardContent className="pt-6">
                  <div className="text-center">
                    <div className="text-3xl font-bold text-primary">{(agent.cognitiveValue * 100).toFixed(0)}%</div>
                    <p className="text-sm text-muted-foreground">Cognitive Capital</p>
                  </div>
                  <Progress value={agent.cognitiveValue * 100} className="mt-4" />
                </CardContent>
              </Card>
              
              <Card>
                <CardContent className="pt-6">
                  <div className="text-center">
                    <div className="text-3xl font-bold">{agent.skills.length}</div>
                    <p className="text-sm text-muted-foreground">Active Skills</p>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <div className="text-center">
                    <div className="text-3xl font-bold">{agent.tools.length}</div>
                    <p className="text-sm text-muted-foreground">Tools Available</p>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <div className="text-center">
                    <div className="text-3xl font-bold">{agent.memory.domains.length}</div>
                    <p className="text-sm text-muted-foreground">Memory Domains</p>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Prompt */}
            <Card className="mt-4">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  System Prompt
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">{agent.prompt.systemPrompt}</p>
                <div className="mt-2 flex items-center gap-2">
                  <span className="text-xs text-muted-foreground">Tone:</span>
                  <Badge variant="outline">{agent.prompt.tone}</Badge>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="skills" className="mt-4">
            <div className="space-y-4">
              {agent.skills.map(skill => (
                <Card key={skill.id}>
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-semibold">{skill.name}</h4>
                      <Badge variant="outline">{(skill.proficiency * 100).toFixed(0)}%</Badge>
                    </div>
                    <Progress value={skill.proficiency * 100} />
                  </CardContent>
                </Card>
              ))}
              <Button variant="outline" className="w-full">
                <Plus className="h-4 w-4 mr-2" /> Add Skill
              </Button>
            </div>
          </TabsContent>

          <TabsContent value="tools" className="mt-4">
            <div className="grid grid-cols-2 gap-4">
              {agent.tools.map((tool, index) => (
                <Card key={index}>
                  <CardContent className="pt-6">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Wrench className="h-4 w-4 text-muted-foreground" />
                        <span className="font-semibold">{tool.name}</span>
                      </div>
                      <Badge variant="secondary">{tool.source}</Badge>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="mcp" className="mt-4">
            <div className="space-y-4">
              {agent.mcps.map((mcp, index) => (
                <Card key={index}>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm flex items-center gap-2">
                      <Plug className="h-4 w-4" />
                      {mcp.name}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-2">
                      {mcp.tools.map(tool => (
                        <Badge key={tool} variant="outline">{tool}</Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          <TabsContent value="memory" className="mt-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Memory Configuration</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <h4 className="text-sm font-semibold mb-2">Domains</h4>
                    <div className="flex flex-wrap gap-2">
                      {agent.memory.domains.map(domain => (
                        <Badge key={domain} variant="secondary">{domain}</Badge>
                      ))}
                    </div>
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold mb-2">Access Level</h4>
                    <Badge variant="outline">{agent.memory.accessLevel}</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}
