'use client'

import { useState, useEffect, useSyncExternalStore } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Menu,
  X,
  Sparkles,
  Brain,
  Bot,
  Database,
  Server,
  Zap,
  Settings,
  Activity,
  Network,
  BookOpen,
  Cpu,
  GitBranch,
  Layers,
  TrendingUp,
  Clock,
  CheckCircle2,
  AlertCircle,
  Pause,
  RefreshCw,
  ChevronRight,
  ExternalLink,
  Search,
  Filter,
  Eye,
  Trash2,
  Plus,
  Download,
  Users,
  Target,
  Microscope,
  Shield,
  Hammer,
  HelpCircle,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { ThemeToggle } from '@/components/dashboard/theme-toggle'
import {
  useDashboardStore,
  useAgentsStore,
  useCapitalStore,
  useMemoryStore,
  useMCPServersStore,
  useIOVBAGroupsStore,
} from '@/stores'
import type { AgentProfile, Engram, IOVBAGroup, IOVBADomain } from '@/types'

// Use useSyncExternalStore for hydration-safe mounted state
const emptySubscribe = () => () => {}
const getSnapshot = () => true
const getServerSnapshot = () => false

// Navigation items
const navItems = [
  { id: 'dashboard', label: 'Dashboard', icon: Activity },
  { id: 'iovba', label: 'IOVBA Groups', icon: Users },
  { id: 'agents', label: 'Agentes', icon: Bot },
  { id: 'capital', label: 'Capital Cognitivo', icon: Brain },
  { id: 'memory', label: 'Memoria', icon: Database },
  { id: 'mcp', label: 'MCP Servers', icon: Server },
  { id: 'domains', label: 'Dominios NVIDIA', icon: Network },
]

// IOVBA Role icons and colors
const iovbaRoleConfig: Record<string, { icon: React.ElementType; color: string; description: string }> = {
  investigador: { icon: Microscope, color: 'text-blue-500', description: 'Investiga y analiza información' },
  observador: { icon: Eye, color: 'text-amber-500', description: 'Monitorea y detecta patrones' },
  validador: { icon: Shield, color: 'text-green-500', description: 'Valida y verifica calidad' },
  builder: { icon: Hammer, color: 'text-purple-500', description: 'Construye e implementa' },
  asistente: { icon: HelpCircle, color: 'text-teal-500', description: 'Coordina y asiste' },
}

// Domain names
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
}

// Status badge component
function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { variant: 'default' | 'secondary' | 'destructive' | 'outline'; icon: React.ReactNode }> = {
    active: { variant: 'default', icon: <CheckCircle2 className="h-3 w-3" /> },
    inactive: { variant: 'secondary', icon: <Pause className="h-3 w-3" /> },
    learning: { variant: 'outline', icon: <BookOpen className="h-3 w-3" /> },
    error: { variant: 'destructive', icon: <AlertCircle className="h-3 w-3" /> },
    connected: { variant: 'default', icon: <CheckCircle2 className="h-3 w-3" /> },
    disconnected: { variant: 'secondary', icon: <X className="h-3 w-3" /> },
  }
  const c = config[status] || config.inactive
  return (
    <Badge variant={c.variant} className="flex items-center gap-1">
      {c.icon}
      <span className="capitalize">{status}</span>
    </Badge>
  )
}

export default function Dashboard() {
  const mounted = useSyncExternalStore(emptySubscribe, getSnapshot, getServerSnapshot)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [activeView, setActiveView] = useState('dashboard')
  const [selectedAgent, setSelectedAgent] = useState<AgentProfile | null>(null)
  const [selectedIOVBAGroup, setSelectedIOVBAGroup] = useState<IOVBAGroup | null>(null)
  const [searchQuery, setSearchQuery] = useState('')

  // Stores
  const { stats, fetchStats } = useDashboardStore()
  const { agents, fetchAgents } = useAgentsStore()
  const { capital, engrams, fetchCapital, fetchEngrams } = useCapitalStore()
  const { entries, fetchMemory } = useMemoryStore()
  const { servers, fetchServers } = useMCPServersStore()
  const { groups, templates, fetchGroups, fetchTemplates } = useIOVBAGroupsStore()

  useEffect(() => {
    fetchStats()
    fetchAgents()
    fetchServers()
    fetchGroups()
    fetchTemplates()
  }, [fetchStats, fetchAgents, fetchServers, fetchGroups, fetchTemplates])

  useEffect(() => {
    if (selectedAgent) {
      fetchCapital(selectedAgent.id)
      fetchEngrams(selectedAgent.id)
      fetchMemory(selectedAgent.id)
    }
  }, [selectedAgent, fetchCapital, fetchEngrams, fetchMemory])

  if (!mounted) return null

  return (
    <div className="min-h-screen flex bg-background">
      {/* Sidebar */}
      <aside
        className={`${
          sidebarOpen ? 'w-64' : 'w-16'
        } border-r border-border/50 bg-card/30 backdrop-blur-sm transition-all duration-300 flex flex-col`}
      >
        {/* Sidebar Header */}
        <div className="h-14 flex items-center justify-between px-4 border-b border-border/50">
          {sidebarOpen && (
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-500">
                <Sparkles className="h-4 w-4 text-white" />
              </div>
              <span className="font-semibold">OpenClaw SaaS</span>
            </div>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="h-8 w-8"
          >
            {sidebarOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </Button>
        </div>

        {/* Navigation */}
        <ScrollArea className="flex-1 py-4">
          <nav className="px-2 space-y-1">
            {navItems.map((item) => (
              <Button
                key={item.id}
                variant={activeView === item.id ? 'secondary' : 'ghost'}
                className={`w-full ${sidebarOpen ? 'justify-start' : 'justify-center'} gap-2`}
                onClick={() => setActiveView(item.id)}
              >
                <item.icon className="h-4 w-4" />
                {sidebarOpen && <span>{item.label}</span>}
              </Button>
            ))}
          </nav>
        </ScrollArea>

        {/* Sidebar Footer */}
        {sidebarOpen && (
          <div className="p-4 border-t border-border/50">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Cpu className="h-3 w-3" />
              <span>IOVBA Stack • v2.0</span>
            </div>
          </div>
        )}
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="h-14 border-b border-border/50 bg-background/80 backdrop-blur-lg flex items-center justify-between px-6">
          <div className="flex items-center gap-4">
            <h1 className="text-lg font-semibold">
              {navItems.find((n) => n.id === activeView)?.label || 'Dashboard'}
            </h1>
            <Badge variant="secondary" className="text-xs">
              <Activity className="h-3 w-3 mr-1" />
              System Health: {stats?.system_health || 0}%
            </Badge>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={() => window.location.reload()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <ThemeToggle />
          </div>
        </header>

        {/* Content Area */}
        <main className="flex-1 overflow-auto p-6">
          {/* Dashboard View */}
          {activeView === 'dashboard' && (
            <div className="space-y-6">
              {/* Stats Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-muted-foreground">Total Agentes</p>
                        <p className="text-2xl font-bold">{stats?.total_agents || 0}</p>
                      </div>
                      <Bot className="h-8 w-8 text-primary opacity-50" />
                    </div>
                    <Progress value={(stats?.active_agents || 0) / (stats?.total_agents || 1) * 100} className="mt-2 h-1" />
                    <p className="text-xs text-muted-foreground mt-1">{stats?.active_agents || 0} activos</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-muted-foreground">IOVBA Groups</p>
                        <p className="text-2xl font-bold">{stats?.iovba_groups || 0}</p>
                      </div>
                      <Users className="h-8 w-8 text-primary opacity-50" />
                    </div>
                    <p className="text-xs text-muted-foreground mt-2">Grupos orientados a dominio</p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-muted-foreground">Capital Cognitivo</p>
                        <p className="text-2xl font-bold">{stats?.total_capital?.toLocaleString() || 0}</p>
                      </div>
                      <Brain className="h-8 w-8 text-primary opacity-50" />
                    </div>
                    <div className="flex items-center gap-1 mt-2 text-emerald-500 text-xs">
                      <TrendingUp className="h-3 w-3" />
                      <span>+12.5% esta semana</span>
                    </div>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm text-muted-foreground">MCP Servers</p>
                        <p className="text-2xl font-bold">{stats?.mcp_servers_connected || 0}</p>
                      </div>
                      <Server className="h-8 w-8 text-primary opacity-50" />
                    </div>
                    <p className="text-xs text-muted-foreground mt-2">{stats?.skills_available || 0} skills disponibles</p>
                  </CardContent>
                </Card>
              </div>

              {/* IOVBA Groups Overview */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <Users className="h-5 w-5" />
                      IOVBA Groups
                    </span>
                    <Button variant="ghost" size="sm" onClick={() => setActiveView('iovba')}>
                      Ver todos <ChevronRight className="h-4 w-4" />
                    </Button>
                  </CardTitle>
                  <CardDescription>
                    Grupos de agentes orientados a dominio: Investigador, Observador, Validador, Builder, Asistente
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {groups.slice(0, 3).map((group) => (
                      <div
                        key={group.id}
                        className="p-4 rounded-lg border hover:border-primary/50 cursor-pointer transition-colors"
                        onClick={() => {
                          setSelectedIOVBAGroup(group)
                          setActiveView('iovba')
                        }}
                      >
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="font-medium">{group.name}</h3>
                          <StatusBadge status={group.status} />
                        </div>
                        <p className="text-sm text-muted-foreground mb-3">{group.description}</p>
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="text-xs">
                            {domainNames[group.domain as IOVBADomain] || group.domain}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {group.metrics.success_rate * 100}% éxito
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Agents Overview */}
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-base flex items-center justify-between">
                    <span>Agentes Activos</span>
                    <Button variant="ghost" size="sm" onClick={() => setActiveView('agents')}>
                      Ver todos <ChevronRight className="h-4 w-4" />
                    </Button>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {agents.slice(0, 5).map((agent) => (
                      <div
                        key={agent.id}
                        className="flex items-center justify-between p-3 rounded-lg bg-muted/50 hover:bg-muted cursor-pointer"
                        onClick={() => {
                          setSelectedAgent(agent)
                          setActiveView('capital')
                        }}
                      >
                        <div className="flex items-center gap-3">
                          <div className="p-2 rounded-lg bg-gradient-to-br from-emerald-500/20 to-teal-500/20">
                            {agent.iovba_role && iovbaRoleConfig[agent.iovba_role] ? (
                              <motion.div
                                initial={{ scale: 0.8, opacity: 0 }}
                                animate={{ scale: 1, opacity: 1 }}
                                className={iovbaRoleConfig[agent.iovba_role].color}
                              >
                                {(() => {
                                  const Icon = iovbaRoleConfig[agent.iovba_role!].icon
                                  return <Icon className="h-4 w-4" />
                                })()}
                              </motion.div>
                            ) : (
                              <Bot className="h-4 w-4" />
                            )}
                          </div>
                          <div>
                            <p className="font-medium text-sm">{agent.name}</p>
                            <p className="text-xs text-muted-foreground">{agent.domain}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-muted-foreground">{agent.cognitive_capital.capital_value}</span>
                          <StatusBadge status={agent.status} />
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* IOVBA Groups View */}
          {activeView === 'iovba' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-2xl font-bold">IOVBA Groups</h2>
                  <p className="text-muted-foreground">
                    Grupos de agentes orientados a dominio: Investigador, Observador, Validador, Builder, Asistente
                  </p>
                </div>
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Nuevo Grupo IOVBA
                </Button>
              </div>

              {/* IOVBA Roles Explanation */}
              <Card className="bg-muted/30">
                <CardContent className="p-4">
                  <h3 className="font-medium mb-3">Roles IOVBA</h3>
                  <div className="grid grid-cols-5 gap-4">
                    {Object.entries(iovbaRoleConfig).map(([role, config]) => {
                      const Icon = config.icon
                      return (
                        <div key={role} className="text-center">
                          <div className={`p-3 rounded-full bg-background mx-auto w-fit ${config.color}`}>
                            <Icon className="h-5 w-5" />
                          </div>
                          <p className="text-sm font-medium mt-2 capitalize">{role}</p>
                          <p className="text-xs text-muted-foreground">{config.description}</p>
                        </div>
                      )
                    })}
                  </div>
                </CardContent>
              </Card>

              {/* Groups Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {groups.map((group) => (
                  <Card key={group.id} className="overflow-hidden">
                    <CardHeader className="pb-2">
                      <div className="flex items-center justify-between">
                        <div>
                          <CardTitle className="text-lg">{group.name}</CardTitle>
                          <CardDescription>{group.description}</CardDescription>
                        </div>
                        <StatusBadge status={group.status} />
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="mb-4">
                        <Badge variant="outline" className="text-xs">
                          {domainNames[group.domain as IOVBADomain] || group.domain}
                        </Badge>
                      </div>

                      {/* Agents in Group */}
                      <div className="space-y-2 mb-4">
                        {Object.entries(group.agents).map(([role, agent]) => {
                          const config = iovbaRoleConfig[role]
                          const Icon = config.icon
                          return (
                            <div
                              key={role}
                              className="flex items-center justify-between p-2 rounded bg-muted/50 hover:bg-muted cursor-pointer"
                              onClick={() => {
                                setSelectedAgent(agent)
                                setActiveView('capital')
                              }}
                            >
                              <div className="flex items-center gap-2">
                                <Icon className={`h-4 w-4 ${config.color}`} />
                                <span className="text-sm capitalize">{role}</span>
                              </div>
                              <div className="flex items-center gap-2">
                                <span className="text-xs text-muted-foreground">
                                  {agent.cognitive_capital.capital_value}
                                </span>
                                <StatusBadge status={agent.status} />
                              </div>
                            </div>
                          )
                        })}
                      </div>

                      {/* Metrics */}
                      <Separator className="my-3" />
                      <div className="grid grid-cols-4 gap-2 text-center text-xs">
                        <div>
                          <p className="text-muted-foreground">Tasks</p>
                          <p className="font-medium">{group.metrics.total_tasks}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Success</p>
                          <p className="font-medium text-emerald-500">{(group.metrics.success_rate * 100).toFixed(0)}%</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Avg Time</p>
                          <p className="font-medium">{group.metrics.avg_completion_time}h</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Expertise</p>
                          <p className="font-medium">{(group.metrics.domain_expertise * 100).toFixed(0)}%</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              {/* Available Templates */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Dominios Disponibles</CardTitle>
                  <CardDescription>Templates para crear nuevos grupos IOVBA orientados a dominio</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-2">
                    {templates.map((template) => (
                      <Button
                        key={template.domain}
                        variant="outline"
                        className="justify-start h-auto py-2"
                      >
                        <Target className="h-4 w-4 mr-2" />
                        <span className="text-xs">{template.name}</span>
                      </Button>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Agents View */}
          {activeView === 'agents' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Buscar agentes..."
                      className="pl-9 w-64"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                  </div>
                  <Button variant="outline" size="sm">
                    <Filter className="h-4 w-4 mr-2" />
                    Filtros
                  </Button>
                </div>
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Nuevo Agente
                </Button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {agents
                  .filter((a) => a.name.toLowerCase().includes(searchQuery.toLowerCase()))
                  .map((agent) => (
                    <Card
                      key={agent.id}
                      className="cursor-pointer hover:border-primary/50 transition-colors"
                      onClick={() => {
                        setSelectedAgent(agent)
                        setActiveView('capital')
                      }}
                    >
                      <CardHeader className="pb-2">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            {agent.iovba_role && iovbaRoleConfig[agent.iovba_role] && (
                              <div className={iovbaRoleConfig[agent.iovba_role].color}>
                                {(() => {
                                  const Icon = iovbaRoleConfig[agent.iovba_role].icon
                                  return <Icon className="h-4 w-4" />
                                })()}
                              </div>
                            )}
                            <CardTitle className="text-base">{agent.name}</CardTitle>
                          </div>
                          <StatusBadge status={agent.status} />
                        </div>
                        <CardDescription className="line-clamp-2">{agent.description}</CardDescription>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-3">
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-muted-foreground">Dominio</span>
                            <Badge variant="outline">{agent.domain}</Badge>
                          </div>
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-muted-foreground">Capital</span>
                            <span className="font-medium">{agent.cognitive_capital.capital_value.toLocaleString()}</span>
                          </div>
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-muted-foreground">Success Rate</span>
                            <span className="font-medium text-emerald-500">{(agent.metrics.success_rate * 100).toFixed(0)}%</span>
                          </div>
                          <Separator />
                          <div className="flex flex-wrap gap-1">
                            {agent.skills.slice(0, 3).map((skill) => (
                              <Badge key={skill} variant="secondary" className="text-xs">
                                {skill}
                              </Badge>
                            ))}
                            {agent.skills.length > 3 && (
                              <Badge variant="secondary" className="text-xs">
                                +{agent.skills.length - 3}
                              </Badge>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
              </div>
            </div>
          )}

          {/* Cognitive Capital View */}
          {activeView === 'capital' && (
            <div className="space-y-6">
              {selectedAgent ? (
                <>
                  {/* Agent Header */}
                  <Card>
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className="p-3 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-500">
                            {selectedAgent.iovba_role && iovbaRoleConfig[selectedAgent.iovba_role] ? (
                              (() => {
                                const Icon = iovbaRoleConfig[selectedAgent.iovba_role!].icon
                                return <Icon className="h-6 w-6 text-white" />
                              })()
                            ) : (
                              <Bot className="h-6 w-6 text-white" />
                            )}
                          </div>
                          <div>
                            <h2 className="text-xl font-bold">{selectedAgent.name}</h2>
                            <p className="text-muted-foreground">{selectedAgent.description}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          {selectedAgent.iovba_role && (
                            <Badge variant="outline" className="capitalize">
                              {selectedAgent.iovba_role}
                            </Badge>
                          )}
                          <StatusBadge status={selectedAgent.status} />
                          <Button variant="outline" size="sm">
                            <Settings className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Capital Stats */}
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <Card>
                      <CardContent className="p-4">
                        <p className="text-sm text-muted-foreground">Capital Total</p>
                        <p className="text-2xl font-bold">{capital?.capital_value?.toLocaleString() || 0}</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="p-4">
                        <p className="text-sm text-muted-foreground">Engrams</p>
                        <p className="text-2xl font-bold">{capital?.total_engrams?.toLocaleString() || 0}</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="p-4">
                        <p className="text-sm text-muted-foreground">Learning Score</p>
                        <p className="text-2xl font-bold">{((capital?.learning_score || 0) * 100).toFixed(0)}%</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="p-4">
                        <p className="text-sm text-muted-foreground">Interacciones</p>
                        <p className="text-2xl font-bold">{capital?.total_interactions?.toLocaleString() || 0}</p>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Engrams List */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center justify-between">
                        <span>Engrams (Memoria Cognitiva)</span>
                        <Button variant="outline" size="sm">
                          <Download className="h-4 w-4 mr-2" />
                          Exportar
                        </Button>
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <ScrollArea className="h-96">
                        <div className="space-y-3">
                          {engrams.map((engram) => (
                            <div
                              key={engram.id}
                              className="p-4 rounded-lg bg-muted/50 hover:bg-muted cursor-pointer"
                            >
                              <div className="flex items-start justify-between">
                                <div className="flex-1">
                                  <p className="text-sm">{engram.content}</p>
                                  <div className="flex items-center gap-2 mt-2">
                                    <Badge variant="outline" className="text-xs">
                                      {engram.source}
                                    </Badge>
                                    {engram.tags.map((tag) => (
                                      <Badge key={tag} variant="secondary" className="text-xs">
                                        {tag}
                                      </Badge>
                                    ))}
                                  </div>
                                </div>
                                <div className="text-right text-xs text-muted-foreground">
                                  <p>Score: {(engram.importance_score * 100).toFixed(0)}%</p>
                                  <p>Access: {engram.access_count}</p>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </ScrollArea>
                    </CardContent>
                  </Card>
                </>
              ) : (
                <Card>
                  <CardContent className="p-12 text-center">
                    <Brain className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                    <p className="text-lg font-medium">Selecciona un agente</p>
                    <p className="text-muted-foreground">Ve a la sección de Agentes y selecciona uno para ver su capital cognitivo</p>
                    <Button className="mt-4" onClick={() => setActiveView('agents')}>
                      Ver Agentes
                    </Button>
                  </CardContent>
                </Card>
              )}
            </div>
          )}

          {/* Memory View */}
          {activeView === 'memory' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <Tabs defaultValue="all">
                  <TabsList>
                    <TabsTrigger value="all">Toda</TabsTrigger>
                    <TabsTrigger value="short_term">Corto Plazo</TabsTrigger>
                    <TabsTrigger value="long_term">Largo Plazo</TabsTrigger>
                    <TabsTrigger value="episodic">Episódica</TabsTrigger>
                    <TabsTrigger value="semantic">Semántica</TabsTrigger>
                  </TabsList>
                </Tabs>
                <div className="flex items-center gap-2">
                  <Button variant="outline" size="sm">
                    <Download className="h-4 w-4 mr-2" />
                    Exportar
                  </Button>
                </div>
              </div>

              {selectedAgent ? (
                <Card>
                  <CardHeader>
                    <CardTitle>Memoria de {selectedAgent.name}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <ScrollArea className="h-[500px]">
                      <div className="space-y-4">
                        {entries.map((entry) => (
                          <div key={entry.id} className="p-4 rounded-lg border">
                            <div className="flex items-start justify-between mb-2">
                              <Badge variant="outline">{entry.type}</Badge>
                              <div className="flex items-center gap-2">
                                <span className="text-xs text-muted-foreground">
                                  Relevancia: {(entry.relevance_score * 100).toFixed(0)}%
                                </span>
                                <Button variant="ghost" size="icon" className="h-6 w-6">
                                  <Eye className="h-3 w-3" />
                                </Button>
                                <Button variant="ghost" size="icon" className="h-6 w-6">
                                  <Trash2 className="h-3 w-3" />
                                </Button>
                              </div>
                            </div>
                            <p className="text-sm">{entry.content}</p>
                            <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
                              <Clock className="h-3 w-3" />
                              {new Date(entry.created_at).toLocaleString()}
                            </div>
                          </div>
                        ))}
                      </div>
                    </ScrollArea>
                  </CardContent>
                </Card>
              ) : (
                <Card>
                  <CardContent className="p-12 text-center">
                    <Database className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                    <p className="text-lg font-medium">Selecciona un agente</p>
                    <p className="text-muted-foreground">Selecciona un agente para explorar su memoria</p>
                    <Button className="mt-4" onClick={() => setActiveView('agents')}>
                      Ver Agentes
                    </Button>
                  </CardContent>
                </Card>
              )}
            </div>
          )}

          {/* MCP Servers View */}
          {activeView === 'mcp' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <Input placeholder="Buscar servidor..." className="w-64" />
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  Conectar Server
                </Button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {servers.map((server) => (
                  <Card key={server.id}>
                    <CardHeader className="pb-2">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-base">{server.name}</CardTitle>
                        <StatusBadge status={server.status} />
                      </div>
                      <CardDescription className="text-xs">{server.description}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">Transport</span>
                          <Badge variant="outline" className="text-xs">
                            {server.transport}
                          </Badge>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">Tools</span>
                          <span className="font-medium">{server.tools.length}</span>
                        </div>
                        <Separator />
                        <div className="flex flex-wrap gap-1">
                          {server.tools.slice(0, 3).map((tool) => (
                            <Badge key={tool.name} variant="secondary" className="text-xs">
                              {tool.name}
                            </Badge>
                          ))}
                          {server.tools.length > 3 && (
                            <Badge variant="secondary" className="text-xs">
                              +{server.tools.length - 3}
                            </Badge>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {/* Domains View */}
          {activeView === 'domains' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <Input placeholder="Buscar dominio..." className="w-64" />
                <Link href="/domains">
                  <Button>
                    <ExternalLink className="h-4 w-4 mr-2" />
                    Ver todos los Blueprints
                  </Button>
                </Link>
              </div>
              <div className="text-center py-12">
                <Network className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-lg font-medium">NVIDIA AI Blueprints</p>
                <p className="text-muted-foreground">Explora e implementa blueprints de NVIDIA</p>
                <Link href="/domains">
                  <Button className="mt-4">Explorar Dominios</Button>
                </Link>
              </div>
            </div>
          )}
        </main>

        {/* Footer */}
        <footer className="h-10 border-t border-border/50 bg-card/30 flex items-center justify-between px-6 text-xs text-muted-foreground">
          <span>OpenClaw Agent SaaS • Cognitive Capital System</span>
          <div className="flex items-center gap-4">
            <span>IOVBA: {groups.length} grupos activos</span>
            <span>Memory VCS: v{capital?.memory_vcs_version || '1.0'}</span>
          </div>
        </footer>
      </div>
    </div>
  )
}
