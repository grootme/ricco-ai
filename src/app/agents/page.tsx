'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { 
  Sparkles,
  Warehouse,
  HeadphonesIcon,
  Video,
  FileSearch,
  FlaskConical,
  Heart,
  ShoppingCart,
  Network,
  Brain
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { AgentManagementDashboard } from '@/components/agent-management/agent-dashboard'

const NVIDIA_DOMAINS = [
  {
    id: 'warehouse_operations',
    name: 'Warehouse Operations',
    icon: Warehouse,
    description: 'Optimización de operaciones de almacén, inventario y logística',
    agents: ['Equipment Agent', 'Operations Agent', 'Safety Agent', 'Forecasting Agent', 'Document Agent'],
    color: 'text-orange-500',
    bgColor: 'bg-orange-500/10',
  },
  {
    id: 'customer_service',
    name: 'Customer Service',
    icon: HeadphonesIcon,
    description: 'Servicio al cliente con soporte automatizado',
    agents: ['RAG Agent', 'Support Agent', 'Router Agent'],
    color: 'text-blue-500',
    bgColor: 'bg-blue-500/10',
  },
  {
    id: 'video_analytics',
    name: 'Video Analytics',
    icon: Video,
    description: 'Búsqueda, resumen y análisis de video',
    agents: ['Ingestion Agent', 'VLM Agent', 'Search Agent', 'Summarization Agent'],
    color: 'text-purple-500',
    bgColor: 'bg-purple-500/10',
  },
  {
    id: 'enterprise_rag',
    name: 'Enterprise RAG',
    icon: FileSearch,
    description: 'Retrieval-Augmented Generation empresarial',
    agents: ['Document Agent', 'Embedding Agent', 'Retrieval Agent', 'Generation Agent'],
    color: 'text-green-500',
    bgColor: 'bg-green-500/10',
  },
  {
    id: 'drug_discovery',
    name: 'Drug Discovery',
    icon: FlaskConical,
    description: 'Descubrimiento de fármacos con IA generativa',
    agents: ['Protein Agent', 'Molecule Agent', 'Docking Agent', 'Screening Agent'],
    color: 'text-pink-500',
    bgColor: 'bg-pink-500/10',
  },
  {
    id: 'healthcare',
    name: 'Healthcare',
    icon: Heart,
    description: 'Consultas de salud y programación de citas',
    agents: ['Consultation Agent', 'Scheduling Agent', 'Wellness Agent'],
    color: 'text-red-500',
    bgColor: 'bg-red-500/10',
  },
  {
    id: 'retail_commerce',
    name: 'Retail & Commerce',
    icon: ShoppingCart,
    description: 'E-commerce y gestión de productos',
    agents: ['Product Agent', 'Order Agent', 'Customer Agent'],
    color: 'text-amber-500',
    bgColor: 'bg-amber-500/10',
  },
  {
    id: 'orchestration',
    name: 'Orchestration',
    icon: Network,
    description: 'Coordinación de múltiples agentes',
    agents: ['Lead Agent', 'Router Agent', 'Coordinator Agent'],
    color: 'text-teal-500',
    bgColor: 'bg-teal-500/10',
  },
]

export default function AgentsPage() {
  const [selectedDomain, setSelectedDomain] = useState<string | null>(null)

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8 space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
              <Brain className="h-8 w-8 text-primary" />
              Agent Management
            </h1>
            <p className="text-muted-foreground mt-1">
              Manage agents by capabilities, not types. Based on NVIDIA AI Blueprints.
            </p>
          </div>
          <Button>
            <Sparkles className="h-4 w-4 mr-2" />
            Create Agent
          </Button>
        </div>

        {/* Tabs */}
        <Tabs defaultValue="agents" className="space-y-6">
          <TabsList>
            <TabsTrigger value="agents">All Agents</TabsTrigger>
            <TabsTrigger value="domains">NVIDIA Domains</TabsTrigger>
            <TabsTrigger value="profiles">Profiles</TabsTrigger>
          </TabsList>

          <TabsContent value="agents">
            <AgentManagementDashboard />
          </TabsContent>

          <TabsContent value="domains">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {NVIDIA_DOMAINS.map(domain => {
                const Icon = domain.icon
                return (
                  <motion.div
                    key={domain.id}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <Card 
                      className={`cursor-pointer transition-all ${selectedDomain === domain.id ? 'ring-2 ring-primary' : ''}`}
                      onClick={() => setSelectedDomain(domain.id)}
                    >
                      <CardHeader className="pb-2">
                        <div className="flex items-center gap-3">
                          <div className={`p-2 rounded-lg ${domain.bgColor}`}>
                            <Icon className={`h-5 w-5 ${domain.color}`} />
                          </div>
                          <div>
                            <CardTitle className="text-sm">{domain.name}</CardTitle>
                            <Badge variant="outline" className="text-xs mt-1">
                              {domain.agents.length} agents
                            </Badge>
                          </div>
                        </div>
                      </CardHeader>
                      <CardContent>
                        <p className="text-xs text-muted-foreground line-clamp-2">
                          {domain.description}
                        </p>
                        <div className="flex flex-wrap gap-1 mt-3">
                          {domain.agents.slice(0, 3).map(agent => (
                            <Badge key={agent} variant="secondary" className="text-xs">
                              {agent}
                            </Badge>
                          ))}
                          {domain.agents.length > 3 && (
                            <Badge variant="outline" className="text-xs">
                              +{domain.agents.length - 3}
                            </Badge>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                )
              })}
            </div>
          </TabsContent>

          <TabsContent value="profiles">
            <Card>
              <CardHeader>
                <CardTitle>Agent Profile Architecture</CardTitle>
                <CardDescription>
                  Agents are defined by configuration, not by enum types
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <Card>
                    <CardContent className="pt-6 text-center">
                      <Brain className="h-8 w-8 mx-auto text-primary mb-2" />
                      <h3 className="font-semibold">Skills</h3>
                      <p className="text-xs text-muted-foreground">What the agent knows</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-6 text-center">
                      <Network className="h-8 w-8 mx-auto text-primary mb-2" />
                      <h3 className="font-semibold">Tools/MCP</h3>
                      <p className="text-xs text-muted-foreground">What the agent can use</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-6 text-center">
                      <FileSearch className="h-8 w-8 mx-auto text-primary mb-2" />
                      <h3 className="font-semibold">Prompt</h3>
                      <p className="text-xs text-muted-foreground">How the agent behaves</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-6 text-center">
                      <Warehouse className="h-8 w-8 mx-auto text-primary mb-2" />
                      <h3 className="font-semibold">Memory</h3>
                      <p className="text-xs text-muted-foreground">Cognitive Capital</p>
                    </CardContent>
                  </Card>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
