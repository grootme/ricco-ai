'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  RICCO_SKILLS, 
  type RiccoSkill, 
  type SDDPhase, 
  type MemoryType,
  type PersonaMode 
} from '@/types'
import { 
  Code, 
  Brain, 
  Settings, 
  Play, 
  Search, 
  Save, 
  CheckCircle,
  AlertCircle,
  Clock,
  FileText,
  GitBranch,
  Zap,
  Target,
  Users
} from 'lucide-react'

// Icons for each skill category
const categoryIcons = {
  workflow: Code,
  memory: Brain,
  orchestration: Settings,
}

// Phase icons for SDD workflow
const phaseIcons: Record<SDDPhase, React.ReactNode> = {
  init: <Play className="h-4 w-4" />,
  explore: <Search className="h-4 w-4" />,
  proposal: <FileText className="h-4 w-4" />,
  spec: <FileText className="h-4 w-4" />,
  design: <GitBranch className="h-4 w-4" />,
  tasks: <Target className="h-4 w-4" />,
  apply: <Zap className="h-4 w-4" />,
  verify: <CheckCircle className="h-4 w-4" />,
  sync: <GitBranch className="h-4 w-4" />,
  archive: <Save className="h-4 w-4" />,
}

// Memory type colors
const memoryTypeColors: Record<MemoryType, string> = {
  architecture: 'bg-blue-500',
  decision: 'bg-purple-500',
  bugfix: 'bg-red-500',
  discovery: 'bg-green-500',
  user_prompt: 'bg-yellow-500',
  session: 'bg-gray-500',
  custom: 'bg-pink-500',
}

// Persona badges
const personaBadges: Record<PersonaMode, { color: string; label: string }> = {
  gentleman: { color: 'bg-violet-500', label: 'el Gentleman' },
  neutral: { color: 'bg-slate-500', label: 'Neutral' },
}

export function RiccoAISkillsPanel() {
  const [activeSkill, setActiveSkill] = useState<string>('gentle-ai')
  const [selectedPhase, setSelectedPhase] = useState<SDDPhase>('init')
  const [memoryType, setMemoryType] = useState<MemoryType>('discovery')
  const [persona, setPersona] = useState<PersonaMode>('gentleman')

  const currentSkill = RICCO_SKILLS.find(s => s.name === activeSkill)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">RICCO AI Skills</h2>
          <p className="text-muted-foreground">
            DeerFlow integration with LangGraph 1.2.0 interrupt support
          </p>
        </div>
        <Badge variant="outline" className="text-sm">
          <Brain className="mr-2 h-4 w-4" />
          3 Skills Active
        </Badge>
      </div>

      <Tabs value={activeSkill} onValueChange={setActiveSkill}>
        <TabsList className="grid w-full grid-cols-3">
          {RICCO_SKILLS.map((skill) => {
            const Icon = categoryIcons[skill.category]
            return (
              <TabsTrigger key={skill.name} value={skill.name} className="flex items-center gap-2">
                <Icon className="h-4 w-4" />
                {skill.name.replace('-', ' ')}
              </TabsTrigger>
            )
          })}
        </TabsList>

        {/* Gentle AI Tab */}
        <TabsContent value="gentle-ai" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Code className="h-5 w-5" />
                SDD/OpenSpec Workflow
              </CardTitle>
              <CardDescription>
                Structured development with TDD evidence tracking
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex flex-wrap gap-2">
                  {(['init', 'explore', 'proposal', 'spec', 'design', 'tasks', 'apply', 'verify', 'sync', 'archive'] as SDDPhase[]).map((phase) => (
                    <Button
                      key={phase}
                      variant={selectedPhase === phase ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setSelectedPhase(phase)}
                      className="flex items-center gap-1"
                    >
                      {phaseIcons[phase]}
                      {phase}
                    </Button>
                  ))}
                </div>

                <div className="grid grid-cols-2 gap-4 mt-4">
                  <Card className="p-4">
                    <h4 className="font-semibold mb-2">Work Routing</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex items-center gap-2">
                        <Badge variant="secondary">inline</Badge>
                        <span className="text-muted-foreground">Small + known context</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="secondary">delegate</Badge>
                        <span className="text-muted-foreground">Unknown / context-heavy</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="secondary">sdd</Badge>
                        <span className="text-muted-foreground">Large / risky</span>
                      </div>
                    </div>
                  </Card>

                  <Card className="p-4">
                    <h4 className="font-semibold mb-2">TDD Phases</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex items-center gap-2">
                        <Badge className="bg-red-500">RED</Badge>
                        <span className="text-muted-foreground">Write failing test</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge className="bg-green-500">GREEN</Badge>
                        <span className="text-muted-foreground">Make it pass</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge className="bg-yellow-500">TRIANGULATE</Badge>
                        <span className="text-muted-foreground">Add more cases</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge className="bg-blue-500">REFACTOR</Badge>
                        <span className="text-muted-foreground">Clean up</span>
                      </div>
                    </div>
                  </Card>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Engram Tab */}
        <TabsContent value="engram" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Brain className="h-5 w-5" />
                Persistent Memory
              </CardTitle>
              <CardDescription>
                SQLite + FTS5 full-text search for agent memory
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex flex-wrap gap-2">
                  {(['architecture', 'decision', 'bugfix', 'discovery', 'user_prompt', 'session', 'custom'] as MemoryType[]).map((type) => (
                    <Badge
                      key={type}
                      className={`${memoryTypeColors[type]} text-white cursor-pointer`}
                      onClick={() => setMemoryType(type)}
                    >
                      {type.replace('_', ' ')}
                    </Badge>
                  ))}
                </div>

                <div className="grid grid-cols-3 gap-4 mt-4">
                  <Card className="p-4 text-center">
                    <div className="text-2xl font-bold">9</div>
                    <div className="text-sm text-muted-foreground">MCP Tools</div>
                  </Card>
                  <Card className="p-4 text-center">
                    <div className="text-2xl font-bold">19</div>
                    <div className="text-sm text-muted-foreground">Total Tools</div>
                  </Card>
                  <Card className="p-4 text-center">
                    <div className="text-2xl font-bold">FTS5</div>
                    <div className="text-sm text-muted-foreground">Search Engine</div>
                  </Card>
                </div>

                <Card className="p-4">
                  <h4 className="font-semibold mb-2">Memory Structure</h4>
                  <pre className="text-xs bg-muted p-2 rounded overflow-auto">
{`{
  "id": "uuid",
  "title": "Memory title",
  "content": "What, Why, Where, Learned",
  "type": "${memoryType}",
  "project": "project-name",
  "topic_key": "domain/topic"
}`}
                  </pre>
                </Card>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Gentle-Pi Tab */}
        <TabsContent value="gentle-pi" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-5 w-5" />
                Pi Development Harness
              </CardTitle>
              <CardDescription>
                Controlled development with el Gentleman persona
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex gap-4">
                  {(['gentleman', 'neutral'] as PersonaMode[]).map((mode) => (
                    <Button
                      key={mode}
                      variant={persona === mode ? 'default' : 'outline'}
                      onClick={() => setPersona(mode)}
                      className="flex items-center gap-2"
                    >
                      <Badge className={`${personaBadges[mode].color} text-white`}>
                        {personaBadges[mode].label}
                      </Badge>
                    </Button>
                  ))}
                </div>

                <div className="grid grid-cols-2 gap-4 mt-4">
                  <Card className="p-4">
                    <h4 className="font-semibold mb-2 flex items-center gap-2">
                      <AlertCircle className="h-4 w-4" />
                      Delegation Triggers
                    </h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">4+ files</Badge>
                        <span className="text-muted-foreground">Launch scout</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">2+ writes</Badge>
                        <span className="text-muted-foreground">Use worker</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">20+ calls</Badge>
                        <span className="text-muted-foreground">Long session</span>
                      </div>
                    </div>
                  </Card>

                  <Card className="p-4">
                    <h4 className="font-semibold mb-2 flex items-center gap-2">
                      <Users className="h-4 w-4" />
                      Subagent Types
                    </h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex items-center gap-2">
                        <Badge variant="secondary">scout</Badge>
                        <span className="text-muted-foreground">Exploration</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="secondary">worker</Badge>
                        <span className="text-muted-foreground">Implementation</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge variant="secondary">reviewer</Badge>
                        <span className="text-muted-foreground">Adversarial review</span>
                      </div>
                    </div>
                  </Card>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Tools Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Available Tools</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {currentSkill?.tools.map((tool) => (
              <Badge key={tool} variant="outline" className="font-mono text-xs">
                {tool}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
