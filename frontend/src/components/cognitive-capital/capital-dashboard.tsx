'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  Brain,
  BookOpen,
  Lightbulb,
  Target,
  TrendingUp,
  Plus,
  Search,
  Filter,
  ChevronRight,
  Clock,
  Zap
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

interface CognitiveCapital {
  id: string
  agentId: string
  type: 'knowledge' | 'experience' | 'pattern' | 'skill' | 'insight'
  source: 'document' | 'interaction' | 'observation' | 'derived'
  domain: string
  title: string
  content: string
  keywords: string[]
  cognitiveValue: number
  confidence: number
  usageCount: number
  createdAt: string
  status: 'active' | 'archived' | 'deprecated'
}

const mockCapitals: CognitiveCapital[] = [
  {
    id: '1',
    agentId: 'agent-1',
    type: 'knowledge',
    source: 'document',
    domain: 'commerce',
    title: 'Product Catalog Structure',
    content: 'Understanding of product categorization and hierarchy in e-commerce systems...',
    keywords: ['products', 'catalog', 'taxonomy', 'categories'],
    cognitiveValue: 0.85,
    confidence: 0.9,
    usageCount: 127,
    createdAt: '2024-01-15T10:30:00Z',
    status: 'active',
  },
  {
    id: '2',
    agentId: 'agent-1',
    type: 'experience',
    source: 'interaction',
    domain: 'commerce',
    title: 'Customer Return Handling',
    content: 'Learned pattern for handling customer return requests efficiently...',
    keywords: ['returns', 'customer-service', 'refunds'],
    cognitiveValue: 0.72,
    confidence: 0.85,
    usageCount: 45,
    createdAt: '2024-01-20T14:15:00Z',
    status: 'active',
  },
  {
    id: '3',
    agentId: 'agent-2',
    type: 'pattern',
    source: 'derived',
    domain: 'healthcare',
    title: 'Appointment Scheduling Optimization',
    content: 'Pattern identified for optimal appointment slot suggestions...',
    keywords: ['appointments', 'scheduling', 'optimization'],
    cognitiveValue: 0.91,
    confidence: 0.88,
    usageCount: 234,
    createdAt: '2024-01-18T09:00:00Z',
    status: 'active',
  },
  {
    id: '4',
    agentId: 'agent-1',
    type: 'insight',
    source: 'observation',
    domain: 'commerce',
    title: 'Peak Shopping Hours',
    content: 'Identified peak shopping patterns for better inventory management...',
    keywords: ['analytics', 'peak-hours', 'inventory'],
    cognitiveValue: 0.68,
    confidence: 0.75,
    usageCount: 89,
    createdAt: '2024-01-22T16:45:00Z',
    status: 'active',
  },
  {
    id: '5',
    agentId: 'agent-3',
    type: 'skill',
    source: 'learned',
    domain: 'orchestration',
    title: 'Multi-Agent Task Routing',
    content: 'Developed skill for routing tasks to appropriate specialist agents...',
    keywords: ['routing', 'orchestration', 'multi-agent'],
    cognitiveValue: 0.95,
    confidence: 0.92,
    usageCount: 567,
    createdAt: '2024-01-10T08:00:00Z',
    status: 'active',
  },
]

const TYPE_CONFIG = {
  knowledge: { icon: BookOpen, color: 'text-blue-500', bg: 'bg-blue-500/10' },
  experience: { icon: Lightbulb, color: 'text-amber-500', bg: 'bg-amber-500/10' },
  pattern: { icon: Target, color: 'text-purple-500', bg: 'bg-purple-500/10' },
  skill: { icon: Zap, color: 'text-green-500', bg: 'bg-green-500/10' },
  insight: { icon: Brain, color: 'text-pink-500', bg: 'bg-pink-500/10' },
}

const SOURCE_LABELS = {
  document: '📄 Document',
  interaction: '💬 Interaction',
  observation: '👁️ Observation',
  derived: '🔄 Derived',
}

export function CognitiveCapitalDashboard() {
  const [capitals, setCapitals] = useState<CognitiveCapital[]>(mockCapitals)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedType, setSelectedType] = useState<string | null>(null)
  const [selectedCapital, setSelectedCapital] = useState<CognitiveCapital | null>(null)

  const filteredCapitals = capitals.filter(capital => {
    const matchesSearch = capital.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         capital.content.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesType = !selectedType || capital.type === selectedType
    return matchesSearch && matchesType
  })

  const stats = {
    total: capitals.length,
    totalValue: capitals.reduce((sum, c) => sum + c.cognitiveValue, 0),
    avgConfidence: capitals.reduce((sum, c) => sum + c.confidence, 0) / capitals.length,
    byType: {
      knowledge: capitals.filter(c => c.type === 'knowledge').length,
      experience: capitals.filter(c => c.type === 'experience').length,
      pattern: capitals.filter(c => c.type === 'pattern').length,
      skill: capitals.filter(c => c.type === 'skill').length,
      insight: capitals.filter(c => c.type === 'insight').length,
    },
  }

  return (
    <div className="space-y-6">
      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-2 rounded-lg bg-primary/10">
                <Brain className="h-5 w-5 text-primary" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Total Capital</p>
                <p className="text-2xl font-bold">{stats.total}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-2 rounded-lg bg-green-500/10">
                <TrendingUp className="h-5 w-5 text-green-500" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Avg. Value</p>
                <p className="text-2xl font-bold">{((stats.totalValue / stats.total) * 100).toFixed(0)}%</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-2 rounded-lg bg-amber-500/10">
                <Target className="h-5 w-5 text-amber-500" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Confidence</p>
                <p className="text-2xl font-bold">{(stats.avgConfidence * 100).toFixed(0)}%</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4">
              <div className="p-2 rounded-lg bg-purple-500/10">
                <Zap className="h-5 w-5 text-purple-500" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Most Active</p>
                <p className="text-lg font-bold">Pattern</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Panel - Capital List */}
        <div className="lg:col-span-2 space-y-4">
          {/* Search & Filters */}
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search cognitive capital..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
              />
            </div>
            <Button variant="outline" size="icon">
              <Filter className="h-4 w-4" />
            </Button>
          </div>

          {/* Type Filters */}
          <div className="flex flex-wrap gap-2">
            <Badge
              variant={selectedType === null ? 'default' : 'outline'}
              className="cursor-pointer"
              onClick={() => setSelectedType(null)}
            >
              All ({stats.total})
            </Badge>
            {Object.entries(stats.byType).map(([type, count]) => (
              <Badge
                key={type}
                variant={selectedType === type ? 'default' : 'outline'}
                className="cursor-pointer"
                onClick={() => setSelectedType(type)}
              >
                {type} ({count})
              </Badge>
            ))}
          </div>

          {/* Capital List */}
          <ScrollArea className="h-[500px]">
            <div className="space-y-3 pr-4">
              {filteredCapitals.map(capital => {
                const config = TYPE_CONFIG[capital.type]
                const Icon = config.icon
                return (
                  <motion.div
                    key={capital.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    whileHover={{ scale: 1.01 }}
                    className="cursor-pointer"
                    onClick={() => setSelectedCapital(capital)}
                  >
                    <Card className={`transition-all ${selectedCapital?.id === capital.id ? 'ring-2 ring-primary' : ''}`}>
                      <CardContent className="p-4">
                        <div className="flex items-start gap-3">
                          <div className={`p-2 rounded-lg ${config.bg}`}>
                            <Icon className={`h-4 w-4 ${config.color}`} />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2">
                              <h3 className="font-semibold truncate">{capital.title}</h3>
                              <Badge variant="outline" className="text-xs capitalize">{capital.type}</Badge>
                            </div>
                            <p className="text-sm text-muted-foreground line-clamp-2 mt-1">
                              {capital.content}
                            </p>
                            <div className="flex items-center gap-4 mt-2">
                              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                                <Clock className="h-3 w-3" />
                                {new Date(capital.createdAt).toLocaleDateString()}
                              </div>
                              <div className="text-xs text-muted-foreground">
                                Used {capital.usageCount} times
                              </div>
                              <Badge variant="secondary" className="text-xs">
                                {capital.domain}
                              </Badge>
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-sm font-semibold text-primary">
                              {(capital.cognitiveValue * 100).toFixed(0)}%
                            </div>
                            <div className="text-xs text-muted-foreground">value</div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </motion.div>
                )
              })}
            </div>
          </ScrollArea>
        </div>

        {/* Right Panel - Detail / Generator */}
        <div className="space-y-4">
          {selectedCapital ? (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">{selectedCapital.title}</CardTitle>
                <CardDescription className="flex items-center gap-2">
                  <Badge variant="outline" className="capitalize">{selectedCapital.type}</Badge>
                  <span>via {SOURCE_LABELS[selectedCapital.source]}</span>
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <h4 className="text-sm font-semibold mb-2">Content</h4>
                  <p className="text-sm text-muted-foreground">{selectedCapital.content}</p>
                </div>

                <div>
                  <h4 className="text-sm font-semibold mb-2">Keywords</h4>
                  <div className="flex flex-wrap gap-1">
                    {selectedCapital.keywords.map(kw => (
                      <Badge key={kw} variant="secondary" className="text-xs">{kw}</Badge>
                    ))}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h4 className="text-sm font-semibold mb-1">Cognitive Value</h4>
                    <Progress value={selectedCapital.cognitiveValue * 100} className="h-2" />
                    <p className="text-xs text-muted-foreground mt-1">
                      {(selectedCapital.cognitiveValue * 100).toFixed(0)}%
                    </p>
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold mb-1">Confidence</h4>
                    <Progress value={selectedCapital.confidence * 100} className="h-2" />
                    <p className="text-xs text-muted-foreground mt-1">
                      {(selectedCapital.confidence * 100).toFixed(0)}%
                    </p>
                  </div>
                </div>

                <div className="pt-4 border-t">
                  <Button className="w-full">
                    <Plus className="h-4 w-4 mr-2" />
                    Generate Related Capital
                  </Button>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card className="h-full flex items-center justify-center">
              <CardContent className="text-center py-20">
                <Brain className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">Select Capital</h3>
                <p className="text-muted-foreground">Choose an entry to view details</p>
              </CardContent>
            </Card>
          )}

          {/* Capital Generator */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm flex items-center gap-2">
                <Zap className="h-4 w-4 text-primary" />
                Capital Generator
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground mb-4">
                Generate new cognitive capital from interactions, documents, or observations.
              </p>
              <div className="space-y-2">
                <Button variant="outline" className="w-full justify-start">
                  <BookOpen className="h-4 w-4 mr-2" />
                  From Document
                </Button>
                <Button variant="outline" className="w-full justify-start">
                  <Lightbulb className="h-4 w-4 mr-2" />
                  From Interaction
                </Button>
                <Button variant="outline" className="w-full justify-start">
                  <Target className="h-4 w-4 mr-2" />
                  Derive Pattern
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
