'use client'

import { motion } from 'framer-motion'
import { 
  Bot, 
  Wrench, 
  Link2, 
  TrendingUp 
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

const stats = [
  {
    title: 'Agent Types',
    value: 7,
    description: 'LLM, A2A, Sequential, Parallel, Loop, Workflow, Task',
    icon: Bot,
    color: 'text-emerald-500',
    bgColor: 'bg-emerald-500/10',
  },
  {
    title: 'MCP Tools',
    value: 50,
    suffix: '+',
    description: 'Model Context Protocol integration',
    icon: Wrench,
    color: 'text-teal-500',
    bgColor: 'bg-teal-500/10',
  },
  {
    title: 'Integrations',
    value: 16,
    suffix: '+',
    description: 'RICCO Solutions domains',
    icon: Link2,
    color: 'text-cyan-500',
    bgColor: 'bg-cyan-500/10',
  },
  {
    title: 'Context Layers',
    value: 6,
    description: 'L1-L6 memory engineering',
    icon: TrendingUp,
    color: 'text-sky-500',
    bgColor: 'bg-sky-500/10',
  },
]

interface StatsCardsProps {
  inView?: boolean
}

export function StatsCards({ inView = true }: StatsCardsProps) {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  }

  const cardVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 },
  }

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate={inView ? 'visible' : 'hidden'}
      className="grid gap-4 md:grid-cols-2 lg:grid-cols-4"
    >
      {stats.map((stat, index) => (
        <motion.div
          key={stat.title}
          variants={cardVariants}
          transition={{ duration: 0.5, delay: index * 0.1 }}
        >
          <Card className="relative overflow-hidden border-border/50 bg-card/50 backdrop-blur-sm hover:bg-card/80 transition-colors duration-300">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {stat.title}
              </CardTitle>
              <div className={`p-2 rounded-lg ${stat.bgColor}`}>
                <stat.icon className={`h-4 w-4 ${stat.color}`} />
              </div>
            </CardHeader>
            <CardContent>
              <motion.div
                initial={{ scale: 0.5, opacity: 0 }}
                animate={inView ? { scale: 1, opacity: 1 } : { scale: 0.5, opacity: 0 }}
                transition={{ duration: 0.5, delay: 0.2 + index * 0.1 }}
                className="text-3xl font-bold tracking-tight"
              >
                {stat.value}
                {stat.suffix && <span className="text-muted-foreground">{stat.suffix}</span>}
              </motion.div>
              <p className="text-xs text-muted-foreground mt-1">
                {stat.description}
              </p>
            </CardContent>
            <div className="absolute inset-0 bg-gradient-to-br from-transparent via-transparent to-emerald-500/5 pointer-events-none" />
          </Card>
        </motion.div>
      ))}
    </motion.div>
  )
}
