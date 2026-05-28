'use client'

import { motion } from 'framer-motion'
import { 
  Brain, 
  Users, 
  ArrowRight, 
  GitBranch, 
  Repeat, 
  Workflow, 
  CheckSquare,
  LucideIcon
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface AgentType {
  name: string
  description: string
  icon: LucideIcon
  color: string
  bgColor: string
  borderColor: string
  features: string[]
}

const agentTypes: AgentType[] = [
  {
    name: 'LLM Agent',
    description: 'Language model powered reasoning and generation',
    icon: Brain,
    color: 'text-emerald-500',
    bgColor: 'bg-emerald-500/10',
    borderColor: 'hover:border-emerald-500/50',
    features: ['GPT-4', 'Claude', 'Gemini'],
  },
  {
    name: 'A2A Agent',
    description: 'Agent-to-Agent communication protocol',
    icon: Users,
    color: 'text-teal-500',
    bgColor: 'bg-teal-500/10',
    borderColor: 'hover:border-teal-500/50',
    features: ['Protocol', 'Swarm', 'Mesh'],
  },
  {
    name: 'Sequential Agent',
    description: 'Step-by-step task execution pipeline',
    icon: ArrowRight,
    color: 'text-cyan-500',
    bgColor: 'bg-cyan-500/10',
    borderColor: 'hover:border-cyan-500/50',
    features: ['Pipeline', 'Chain', 'Order'],
  },
  {
    name: 'Parallel Agent',
    description: 'Concurrent multi-task processing',
    icon: GitBranch,
    color: 'text-sky-500',
    bgColor: 'bg-sky-500/10',
    borderColor: 'hover:border-sky-500/50',
    features: ['Concurrent', 'Distributed', 'Scale'],
  },
  {
    name: 'Loop Agent',
    description: 'Iterative refinement and optimization',
    icon: Repeat,
    color: 'text-emerald-400',
    bgColor: 'bg-emerald-400/10',
    borderColor: 'hover:border-emerald-400/50',
    features: ['Iterate', 'Refine', 'Optimize'],
  },
  {
    name: 'Workflow Agent',
    description: 'Complex multi-step orchestration',
    icon: Workflow,
    color: 'text-teal-400',
    bgColor: 'bg-teal-400/10',
    borderColor: 'hover:border-teal-400/50',
    features: ['Orchestrate', 'DAG', 'Flow'],
  },
  {
    name: 'Task Agent',
    description: 'Specific task-focused execution',
    icon: CheckSquare,
    color: 'text-cyan-400',
    bgColor: 'bg-cyan-400/10',
    borderColor: 'hover:border-cyan-400/50',
    features: ['Focused', 'Execute', 'Complete'],
  },
]

interface AgentGridProps {
  inView?: boolean
}

export function AgentGrid({ inView = true }: AgentGridProps) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      {agentTypes.map((agent, index) => (
        <motion.div
          key={agent.name}
          initial={{ opacity: 0, y: 20 }}
          animate={inView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
          transition={{ duration: 0.5, delay: index * 0.1 }}
          whileHover={{ scale: 1.02, transition: { duration: 0.2 } }}
        >
          <Card className={`h-full cursor-pointer border-border/50 bg-card/50 backdrop-blur-sm transition-all duration-300 ${agent.borderColor}`}>
            <CardHeader className="pb-3">
              <div className="flex items-center gap-3">
                <div className={`p-2.5 rounded-lg ${agent.bgColor}`}>
                  <agent.icon className={`h-5 w-5 ${agent.color}`} />
                </div>
                <CardTitle className="text-lg">{agent.name}</CardTitle>
              </div>
              <CardDescription className="text-sm mt-2">
                {agent.description}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-1.5">
                {agent.features.map((feature) => (
                  <Badge 
                    key={feature} 
                    variant="secondary" 
                    className="text-xs px-2 py-0.5 bg-muted/50"
                  >
                    {feature}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      ))}
    </div>
  )
}
