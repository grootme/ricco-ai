'use client'

import { motion } from 'framer-motion'
import { 
  Wrench,
  Globe,
  Database,
  FileCode,
  Cloud,
  MessageSquare,
  Search,
  Code,
  LucideIcon
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'

interface ToolCategory {
  name: string
  description: string
  icon: LucideIcon
  color: string
  bgColor: string
  tools: string[]
  count: number
}

const toolCategories: ToolCategory[] = [
  {
    name: 'Web & Search',
    description: 'Web scraping, search engines, APIs',
    icon: Globe,
    color: 'text-emerald-500',
    bgColor: 'bg-emerald-500/10',
    tools: ['web_search', 'scrape', 'fetch', 'selenium', 'playwright'],
    count: 12,
  },
  {
    name: 'Data & Storage',
    description: 'Databases, file systems, caching',
    icon: Database,
    color: 'text-teal-500',
    bgColor: 'bg-teal-500/10',
    tools: ['sqlite', 'postgres', 'redis', 'mongodb', 's3'],
    count: 15,
  },
  {
    name: 'Code & Development',
    description: 'Code execution, git, terminals',
    icon: Code,
    color: 'text-cyan-500',
    bgColor: 'bg-cyan-500/10',
    tools: ['python', 'node', 'git', 'docker', 'kubectl'],
    count: 10,
  },
  {
    name: 'File Operations',
    description: 'File manipulation, conversions',
    icon: FileCode,
    color: 'text-sky-500',
    bgColor: 'bg-sky-500/10',
    tools: ['read', 'write', 'convert', 'compress', 'parse'],
    count: 8,
  },
  {
    name: 'Cloud Services',
    description: 'AWS, GCP, Azure integrations',
    icon: Cloud,
    color: 'text-emerald-400',
    bgColor: 'bg-emerald-400/10',
    tools: ['aws_cli', 'gcloud', 'azure', 'terraform'],
    count: 6,
  },
  {
    name: 'Communication',
    description: 'Email, messaging, notifications',
    icon: MessageSquare,
    color: 'text-teal-400',
    bgColor: 'bg-teal-400/10',
    tools: ['sendgrid', 'twilio', 'slack', 'discord'],
    count: 5,
  },
]

const popularTools = [
  'web_search', 'python_runner', 'sqlite', 'git', 'fetch',
  'openapi', 'filesystem', 'redis', 'docker', 'slack',
]

interface McpArsenalProps {
  inView?: boolean
}

export function McpArsenal({ inView = true }: McpArsenalProps) {
  return (
    <div className="space-y-6">
      {/* Tool Categories */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {toolCategories.map((category, index) => (
          <motion.div
            key={category.name}
            initial={{ opacity: 0, y: 20 }}
            animate={inView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
            transition={{ duration: 0.5, delay: index * 0.1 }}
          >
            <Card className="h-full border-border/50 bg-card/50 backdrop-blur-sm hover:bg-card/80 transition-all duration-300">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg ${category.bgColor}`}>
                      <category.icon className={`h-4 w-4 ${category.color}`} />
                    </div>
                    <CardTitle className="text-base">{category.name}</CardTitle>
                  </div>
                  <Badge variant="secondary" className="font-mono">
                    {category.count}
                  </Badge>
                </div>
                <CardDescription className="text-sm mt-1">
                  {category.description}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-16">
                  <div className="flex flex-wrap gap-1">
                    {category.tools.map((tool) => (
                      <Badge 
                        key={tool} 
                        variant="outline" 
                        className="text-xs px-1.5 py-0 font-mono"
                      >
                        {tool}
                      </Badge>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      {/* Popular Tools */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={inView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
        transition={{ duration: 0.5, delay: 0.3 }}
      >
        <Card className="border-border/50 bg-card/50 backdrop-blur-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg flex items-center gap-2">
              <Search className="h-5 w-5 text-emerald-500" />
              Popular MCP Tools
            </CardTitle>
            <CardDescription>
              Most frequently used tools across all integrations
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {popularTools.map((tool, index) => (
                <motion.div
                  key={tool}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={inView ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0.9 }}
                  transition={{ duration: 0.3, delay: 0.4 + index * 0.05 }}
                >
                  <Badge 
                    variant="secondary"
                    className="px-3 py-1.5 font-mono text-sm bg-gradient-to-r from-emerald-500/10 to-teal-500/10 hover:from-emerald-500/20 hover:to-teal-500/20 transition-colors cursor-pointer"
                  >
                    <Wrench className="h-3 w-3 mr-1.5 text-emerald-500" />
                    {tool}
                  </Badge>
                </motion.div>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}
