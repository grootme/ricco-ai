'use client'

import { motion } from 'framer-motion'
import { 
  Database,
  HardDrive,
  Cpu,
  Brain,
  Network,
  Globe,
  ArrowUpRight
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'

const memoryLayers = [
  {
    level: 'L1',
    name: 'Working Memory',
    description: 'Active conversation context and immediate task data',
    icon: Cpu,
    color: 'text-emerald-500',
    bgColor: 'bg-emerald-500/10',
    capacity: '4K tokens',
    retention: 'Session',
  },
  {
    level: 'L2',
    name: 'Short-term Memory',
    description: 'Recent interactions and temporary cache storage',
    icon: Database,
    color: 'text-teal-500',
    bgColor: 'bg-teal-500/10',
    capacity: '16K tokens',
    retention: '24 hours',
  },
  {
    level: 'L3',
    name: 'Session Memory',
    description: 'User preferences and session-specific context',
    icon: HardDrive,
    color: 'text-cyan-500',
    bgColor: 'bg-cyan-500/10',
    capacity: '64K tokens',
    retention: '7 days',
  },
  {
    level: 'L4',
    name: 'Long-term Memory',
    description: 'Persistent user data and learned patterns',
    icon: Brain,
    color: 'text-sky-500',
    bgColor: 'bg-sky-500/10',
    capacity: '256K tokens',
    retention: '30 days',
  },
  {
    level: 'L5',
    name: 'Knowledge Base',
    description: 'Domain expertise and semantic search index',
    icon: Network,
    color: 'text-emerald-400',
    bgColor: 'bg-emerald-400/10',
    capacity: '1M+ tokens',
    retention: 'Permanent',
  },
  {
    level: 'L6',
    name: 'Global Context',
    description: 'Cross-user insights and aggregated knowledge',
    icon: Globe,
    color: 'text-teal-400',
    bgColor: 'bg-teal-400/10',
    capacity: 'Unlimited',
    retention: 'Permanent',
  },
]

interface ContextSectionProps {
  inView?: boolean
}

export function ContextSection({ inView = true }: ContextSectionProps) {
  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {memoryLayers.map((layer, index) => (
          <motion.div
            key={layer.level}
            initial={{ opacity: 0, y: 20 }}
            animate={inView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
            transition={{ duration: 0.5, delay: index * 0.1 }}
          >
            <Card className="h-full border-border/50 bg-card/50 backdrop-blur-sm hover:bg-card/80 transition-all duration-300 group">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${layer.bgColor}`}>
                      <layer.icon className={`h-4 w-4 ${layer.color}`} />
                    </div>
                    <div>
                      <CardTitle className="text-base flex items-center gap-2">
                        <span className={`font-mono ${layer.color}`}>{layer.level}</span>
                        <span>{layer.name}</span>
                      </CardTitle>
                    </div>
                  </div>
                  <ArrowUpRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <CardDescription className="text-sm">
                  {layer.description}
                </CardDescription>
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">Capacity</span>
                  <span className="font-medium">{layer.capacity}</span>
                </div>
                <Progress value={((index + 1) / 6) * 100} className="h-1.5" />
                <div className="flex items-center justify-between text-xs">
                  <span className="text-muted-foreground">Retention</span>
                  <span className="font-medium">{layer.retention}</span>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
