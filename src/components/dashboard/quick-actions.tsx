'use client'

import { motion } from 'framer-motion'
import { 
  Plus, 
  FileText, 
  Settings,
  Sparkles,
  Terminal,
  BookOpen,
  Zap
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

const quickActions = [
  {
    title: 'Create Agent',
    description: 'Build a new AI agent with factory pattern',
    icon: Plus,
    color: 'text-emerald-500',
    bgColor: 'bg-emerald-500/10',
    hoverBg: 'hover:bg-emerald-500/20',
  },
  {
    title: 'View Logs',
    description: 'Monitor agent activity and performance',
    icon: FileText,
    color: 'text-teal-500',
    bgColor: 'bg-teal-500/10',
    hoverBg: 'hover:bg-teal-500/20',
  },
  {
    title: 'Configure MCP',
    description: 'Manage MCP server connections',
    icon: Settings,
    color: 'text-cyan-500',
    bgColor: 'bg-cyan-500/10',
    hoverBg: 'hover:bg-cyan-500/20',
  },
  {
    title: 'A2UI Studio',
    description: 'Dynamic UI component builder',
    icon: Sparkles,
    color: 'text-sky-500',
    bgColor: 'bg-sky-500/10',
    hoverBg: 'hover:bg-sky-500/20',
  },
]

const additionalActions = [
  { label: 'CLI Tools', icon: Terminal, color: 'text-emerald-400' },
  { label: 'Documentation', icon: BookOpen, color: 'text-teal-400' },
  { label: 'Quick Deploy', icon: Zap, color: 'text-cyan-400' },
]

interface QuickActionsProps {
  inView?: boolean
}

export function QuickActions({ inView = true }: QuickActionsProps) {
  return (
    <div className="space-y-4">
      {/* Main Actions Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {quickActions.map((action, index) => (
          <motion.div
            key={action.title}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={inView ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.3, delay: index * 0.1 }}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <Card className={`h-full cursor-pointer border-border/50 bg-card/50 backdrop-blur-sm transition-all duration-300 ${action.hoverBg}`}>
              <CardHeader className="pb-2">
                <div className={`p-2.5 rounded-lg ${action.bgColor} w-fit`}>
                  <action.icon className={`h-5 w-5 ${action.color}`} />
                </div>
              </CardHeader>
              <CardContent>
                <CardTitle className="text-base">{action.title}</CardTitle>
                <CardDescription className="text-sm mt-1">
                  {action.description}
                </CardDescription>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Additional Quick Links */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={inView ? { opacity: 1, y: 0 } : { opacity: 0, y: 10 }}
        transition={{ duration: 0.3, delay: 0.4 }}
        className="flex flex-wrap gap-2 justify-center"
      >
        {additionalActions.map((action) => (
          <Button
            key={action.label}
            variant="outline"
            size="sm"
            className="gap-2 border-border/50 bg-card/30 backdrop-blur-sm"
          >
            <action.icon className={`h-4 w-4 ${action.color}`} />
            {action.label}
          </Button>
        ))}
      </motion.div>
    </div>
  )
}
