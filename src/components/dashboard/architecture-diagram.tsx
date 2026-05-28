'use client'

import { motion } from 'framer-motion'
import { 
  Layers, 
  Box, 
  Settings2, 
  Wrench, 
  Container,
  ArrowRightLeft,
  LucideIcon
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import { useState } from 'react'

interface ModuleItem {
  name: string
  description: string
  files: string[]
}

interface Module {
  title: string
  icon: LucideIcon
  color: string
  bgColor: string
  items: ModuleItem[]
}

const modules: Module[] = [
  {
    title: 'core/',
    icon: Box,
    color: 'text-emerald-500',
    bgColor: 'bg-emerald-500/10',
    items: [
      { name: 'protocols.py', description: 'Protocol-based interfaces', files: ['AgentProtocol', 'ToolProtocol', 'ServiceProtocol'] },
      { name: 'container.py', description: 'Dependency injection', files: ['Container', 'inject', 'singleton'] },
      { name: 'exceptions.py', description: 'Custom exceptions', files: ['AgentError', 'ToolError', 'ConfigError'] },
    ],
  },
  {
    title: 'services/a2ui/',
    icon: Settings2,
    color: 'text-teal-500',
    bgColor: 'bg-teal-500/10',
    items: [
      { name: 'service.py', description: 'A2UI main service', files: ['A2UIService', 'render', 'stream'] },
      { name: 'models.py', description: 'Data models', files: ['Component', 'Template', 'Theme'] },
      { name: 'templates.py', description: 'UI templates', files: ['Layout', 'Page', 'Widget'] },
    ],
  },
  {
    title: 'agents/',
    icon: Layers,
    color: 'text-cyan-500',
    bgColor: 'bg-cyan-500/10',
    items: [
      { name: 'factory/', description: 'Agent factory pattern', files: ['AgentFactory', 'create', 'register'] },
      { name: 'swarm/', description: 'Swarm orchestration', files: ['SwarmAgent', 'coordinate', 'dispatch'] },
      { name: 'graphs/', description: 'Graph workflows', files: ['StateGraph', 'Node', 'Edge'] },
    ],
  },
  {
    title: 'mcp/',
    icon: Wrench,
    color: 'text-sky-500',
    bgColor: 'bg-sky-500/10',
    items: [
      { name: 'registry/', description: 'Tool registry', files: ['ServerRegistry', 'ToolRegistry', 'register'] },
      { name: 'proxy/', description: 'Request proxy', files: ['TokenProxy', 'LoadBalancer', 'CircuitBreaker'] },
      { name: 'tools/', description: 'Tool definitions', files: ['ToolDefinition', 'execute', 'validate'] },
    ],
  },
]

const designPatterns = [
  { name: 'Factory', description: 'Agent creation' },
  { name: 'Singleton', description: 'Container' },
  { name: 'Strategy', description: 'Execution' },
  { name: 'Builder', description: 'Config' },
  { name: 'Observer', description: 'Events' },
  { name: 'Repository', description: 'Data' },
]

interface ArchitectureDiagramProps {
  inView?: boolean
}

export function ArchitectureDiagram({ inView = true }: ArchitectureDiagramProps) {
  const [openModule, setOpenModule] = useState<string | null>(null)

  return (
    <div className="space-y-6">
      {/* Module Structure */}
      <div className="grid gap-4 md:grid-cols-2">
        {modules.map((module, index) => (
          <motion.div
            key={module.title}
            initial={{ opacity: 0, x: index % 2 === 0 ? -20 : 20 }}
            animate={inView ? { opacity: 1, x: 0 } : { opacity: 0, x: index % 2 === 0 ? -20 : 20 }}
            transition={{ duration: 0.5, delay: index * 0.1 }}
          >
            <Collapsible
              open={openModule === module.title}
              onOpenChange={(open) => setOpenModule(open ? module.title : null)}
            >
              <CollapsibleTrigger asChild>
                <Card className="w-full cursor-pointer border-border/50 bg-card/50 backdrop-blur-sm hover:bg-card/80 transition-all duration-300">
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${module.bgColor}`}>
                          <module.icon className={`h-5 w-5 ${module.color}`} />
                        </div>
                        <CardTitle className="text-lg font-mono">{module.title}</CardTitle>
                      </div>
                      <ArrowRightLeft className="h-4 w-4 text-muted-foreground" />
                    </div>
                  </CardHeader>
                </Card>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <Card className="w-full border-border/50 bg-card/30 backdrop-blur-sm mt-2">
                  <CardContent className="pt-4">
                    <div className="space-y-3">
                      {module.items.map((item) => (
                        <div key={item.name} className="flex items-start gap-3">
                          <Container className="h-4 w-4 mt-0.5 text-muted-foreground" />
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium font-mono truncate">{item.name}</p>
                            <p className="text-xs text-muted-foreground">{item.description}</p>
                            <div className="flex flex-wrap gap-1 mt-1">
                              {item.files.map((file) => (
                                <Badge key={file} variant="outline" className="text-xs px-1.5 py-0">
                                  {file}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </CollapsibleContent>
            </Collapsible>
          </motion.div>
        ))}
      </div>

      {/* Design Patterns */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={inView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
        transition={{ duration: 0.5, delay: 0.4 }}
        className="mt-6"
      >
        <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              <Container className="h-5 w-5 text-emerald-500" />
              GOF Design Patterns
            </CardTitle>
            <CardDescription>
              Architectural patterns implemented in the refactored codebase
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {designPatterns.map((pattern) => (
                <Badge 
                  key={pattern.name}
                  variant="secondary"
                  className="px-3 py-1.5 bg-gradient-to-r from-emerald-500/10 to-teal-500/10 hover:from-emerald-500/20 hover:to-teal-500/20 transition-colors"
                >
                  <span className="font-medium">{pattern.name}</span>
                  <span className="text-muted-foreground ml-1.5 text-xs">({pattern.description})</span>
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}
