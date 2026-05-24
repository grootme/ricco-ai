'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Send,
  Brain,
  User,
  Loader2,
  Check,
  Copy,
  Trash2,
  RefreshCw,
  Menu,
  X,
  Zap,
  Activity,
  Microscope,
  Eye,
  Shield,
  Hammer,
  HelpCircle,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { cn } from '@/lib/utils'

// Types
interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  domain?: string
  domainBrand?: string
  confidence?: number
  rolesConsulted?: string[]
}

interface NEXUSStatus {
  id: string
  name: string
  full_name: string
  status: string
  domains_available: number
  llm_configured: boolean
  model: string
  capital: {
    total_engrams: number
    total_interactions: number
    capital_value: number
  }
}

interface Domain {
  domain: string
  name: string
  elegant_name: string
  tagline: string
  icon: string
  color: string
  description: string
}

interface Role {
  role: string
  elegant_name: string
  tagline: string
  description: string
  icon: string
  color: string
}

// Role icons
const roleIcons: Record<string, React.ElementType> = {
  investigador: Microscope,
  observador: Eye,
  validador: Shield,
  builder: Hammer,
  asistente: HelpCircle,
}

// Domain colors
const domainColors: Record<string, string> = {
  swe: '#3B82F6',
  salud: '#EF4444',
  deportes: '#F59E0B',
  noticias: '#6366F1',
  quimica: '#8B5CF6',
  biologia: '#10B981',
  biotecnologia: '#14B8A6',
  geopolitica: '#F97316',
  finanzas: '#059669',
  legal: '#7C3AED',
  educacion: '#EC4899',
  investigacion: '#0EA5E9',
  marketing: '#D946EF',
  custom: '#64748B',
}

// API base URL
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

export default function NEXUSChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [nexusStatus, setNexusStatus] = useState<NEXUSStatus | null>(null)
  const [domains, setDomains] = useState<Domain[]>([])
  const [roles, setRoles] = useState<Role[]>([])
  const [selectedDomain, setSelectedDomain] = useState<string>('auto')
  const [selectedRole, setSelectedRole] = useState<string>('auto')
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const [sidebarOpen, setSidebarOpen] = useState(true)
  
  const scrollRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Fetch NEXUS status
  const fetchStatus = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/nexus/status`)
      if (response.ok) {
        const data = await response.json()
        setNexusStatus(data)
      }
    } catch (error) {
      console.error('Error fetching status:', error)
    }
  }, [])

  // Fetch domains
  const fetchDomains = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/nexus/domains`)
      if (response.ok) {
        const data = await response.json()
        setDomains(data)
      }
    } catch (error) {
      console.error('Error fetching domains:', error)
    }
  }, [])

  // Fetch roles
  const fetchRoles = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/nexus/roles`)
      if (response.ok) {
        const data = await response.json()
        setRoles(data)
      }
    } catch (error) {
      console.error('Error fetching roles:', error)
    }
  }, [])

  // Initial fetch
  useEffect(() => {
    fetchStatus()
    fetchDomains()
    fetchRoles()
  }, [fetchStatus, fetchDomains, fetchRoles])

  // Auto-scroll
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  // Send message
  const sendMessage = async () => {
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString(),
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const response = await fetch(`${API_BASE}/nexus/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: input.trim(),
          domain: selectedDomain === 'auto' ? null : selectedDomain,
          role: selectedRole === 'auto' ? null : selectedRole,
          stream: false,
        }),
      })

      if (response.ok) {
        const data = await response.json()
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: data.content,
          timestamp: data.timestamp,
          domain: data.domain,
          domainBrand: data.domain_brand,
          confidence: data.confidence,
          rolesConsulted: data.roles_consulted,
        }
        setMessages(prev => [...prev, assistantMessage])
        fetchStatus()
      } else {
        const error = await response.json()
        setMessages(prev => [...prev, {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: `Error: ${error.detail || 'Failed to get response'}`,
          timestamp: new Date().toISOString(),
        }])
      }
    } catch (error) {
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Error: Could not connect to NEXUS. Please check if the server is running.',
        timestamp: new Date().toISOString(),
      }])
    } finally {
      setIsLoading(false)
    }
  }

  // Handle key press
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  // Copy to clipboard
  const copyToClipboard = async (text: string, id: string) => {
    await navigator.clipboard.writeText(text)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  // Format time
  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }

  // Parse content
  const parseContent = (content: string) => {
    return content.split('\n').map((line, i) => {
      if (line.startsWith('# ')) return <h1 key={i} className="text-2xl font-bold mt-4 mb-2">{line.slice(2)}</h1>
      if (line.startsWith('## ')) return <h2 key={i} className="text-xl font-bold mt-3 mb-2">{line.slice(3)}</h2>
      if (line.startsWith('### ')) return <h3 key={i} className="text-lg font-semibold mt-2 mb-1">{line.slice(4)}</h3>
      if (line.startsWith('- ') || line.startsWith('• ')) return <li key={i} className="ml-4">{line.slice(2)}</li>
      if (line.trim()) return <p key={i} className="mb-1">{line}</p>
      return null
    })
  }

  return (
    <div className="min-h-screen flex bg-background">
      {/* Sidebar */}
      <aside className={cn(
        'border-r border-border/50 bg-card/30 backdrop-blur-sm transition-all duration-300 flex flex-col',
        sidebarOpen ? 'w-80' : 'w-0 overflow-hidden'
      )}>
        <div className="h-14 flex items-center justify-between px-4 border-b border-border/50">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500">
              <Brain className="h-4 w-4 text-white" />
            </div>
            <span className="font-semibold">NEXUS Chat</span>
          </div>
        </div>

        <ScrollArea className="flex-1 p-4">
          <div className="space-y-6">
            {/* Status */}
            {nexusStatus && (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2">
                    <Activity className="h-4 w-4" />
                    Estado del Sistema
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Status</span>
                    <Badge variant="default" className="bg-emerald-500">{nexusStatus.status}</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Modelo</span>
                    <span className="font-mono text-xs">{nexusStatus.model || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Dominios</span>
                    <span>{nexusStatus.domains_available}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Capital</span>
                    <span>{nexusStatus.capital?.capital_value?.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">LLM</span>
                    <Badge variant={nexusStatus.llm_configured ? 'default' : 'secondary'}>
                      {nexusStatus.llm_configured ? 'OK' : 'No config'}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Domain Selection */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Dominio</label>
              <Select value={selectedDomain} onValueChange={setSelectedDomain}>
                <SelectTrigger><SelectValue placeholder="Seleccionar dominio" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="auto">
                    <div className="flex items-center gap-2">
                      <Zap className="h-4 w-4" />
                      Detección Automática
                    </div>
                  </SelectItem>
                  {domains.map((domain) => (
                    <SelectItem key={domain.domain} value={domain.domain}>
                      <div className="flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full" style={{ backgroundColor: domain.color }} />
                        {domain.elegant_name}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Role Selection */}
            <div className="space-y-2">
              <label className="text-sm font-medium">Rol IOVBA</label>
              <Select value={selectedRole} onValueChange={setSelectedRole}>
                <SelectTrigger><SelectValue placeholder="Seleccionar rol" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="auto">
                    <div className="flex items-center gap-2">
                      <Zap className="h-4 w-4" />
                      Automático
                    </div>
                  </SelectItem>
                  {roles.map((role) => {
                    const Icon = roleIcons[role.role] || HelpCircle
                    return (
                      <SelectItem key={role.role} value={role.role}>
                        <div className="flex items-center gap-2">
                          <Icon className="h-4 w-4" />
                          {role.elegant_name}
                        </div>
                      </SelectItem>
                    )
                  })}
                </SelectContent>
              </Select>
            </div>

            {/* Domains Grid */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Dominios</CardTitle>
                <CardDescription className="text-xs">13 dominios especializados</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-1">
                  {domains.slice(0, 8).map((domain) => (
                    <button
                      key={domain.domain}
                      onClick={() => setSelectedDomain(domain.domain)}
                      className={cn(
                        'p-2 rounded-lg text-left text-xs transition-colors hover:bg-muted',
                        selectedDomain === domain.domain && 'bg-muted ring-1 ring-primary'
                      )}
                    >
                      <div className="flex items-center gap-1">
                        <div className="w-2 h-2 rounded-full" style={{ backgroundColor: domain.color }} />
                        <span className="font-medium">{domain.elegant_name}</span>
                      </div>
                    </button>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Roles */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm">Roles IOVBA</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-1">
                  {roles.map((role) => {
                    const Icon = roleIcons[role.role] || HelpCircle
                    return (
                      <button
                        key={role.role}
                        onClick={() => setSelectedRole(role.role)}
                        className={cn(
                          'w-full p-2 rounded-lg text-left text-xs transition-colors hover:bg-muted flex items-center gap-2',
                          selectedRole === role.role && 'bg-muted ring-1 ring-primary'
                        )}
                      >
                        <Icon className="h-4 w-4" />
                        <div>
                          <div className="font-medium">{role.elegant_name}</div>
                          <div className="text-muted-foreground text-[10px]">{role.tagline}</div>
                        </div>
                      </button>
                    )
                  })}
                </div>
              </CardContent>
            </Card>
          </div>
        </ScrollArea>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="h-14 border-b border-border/50 bg-background/80 backdrop-blur-lg flex items-center justify-between px-4">
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => setSidebarOpen(!sidebarOpen)}>
              {sidebarOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
            </Button>
            <div className="flex items-center gap-2">
              <div className="p-1.5 rounded-lg bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500">
                <Brain className="h-4 w-4 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-semibold">NEXUS</h1>
                <p className="text-xs text-muted-foreground">Neural Execution Unified System</p>
              </div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" onClick={fetchStatus}>
              <RefreshCw className="h-4 w-4 mr-2" /> Actualizar
            </Button>
            <Button variant="outline" size="sm" onClick={() => setMessages([])}>
              <Trash2 className="h-4 w-4 mr-2" /> Limpiar
            </Button>
          </div>
        </header>

        {/* Chat Area */}
        <div ref={scrollRef} className="flex-1 overflow-auto p-4">
          {messages.length === 0 ? (
            <div className="h-full flex items-center justify-center">
              <div className="text-center max-w-md">
                <div className="p-4 rounded-full bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 mx-auto w-fit mb-4">
                  <Brain className="h-8 w-8 text-white" />
                </div>
                <h2 className="text-2xl font-bold mb-2">Bienvenido a NEXUS</h2>
                <p className="text-muted-foreground mb-4">
                  Tu Super Agente Coordinador del sistema IOVBA. Puedo ayudarte con cualquier
                  consulta en los 13 dominios disponibles.
                </p>
                <div className="flex flex-wrap gap-2 justify-center">
                  <Badge variant="outline" className="cursor-pointer" onClick={() => setInput('¿Qué es el hantavirus?')}>
                    ¿Qué es el hantavirus?
                  </Badge>
                  <Badge variant="outline" className="cursor-pointer" onClick={() => setInput('Ayúdame con código Python')}>
                    Código Python
                  </Badge>
                  <Badge variant="outline" className="cursor-pointer" onClick={() => setInput('Análisis de mercado financiero')}>
                    Análisis Financiero
                  </Badge>
                </div>
              </div>
            </div>
          ) : (
            <div className="max-w-4xl mx-auto space-y-4">
              <AnimatePresence>
                {messages.map((message) => (
                  <motion.div
                    key={message.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -10 }}
                    className={cn('flex gap-3', message.role === 'user' ? 'justify-end' : 'justify-start')}
                  >
                    {message.role === 'assistant' && (
                      <div className="p-2 rounded-lg bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 h-fit">
                        <Brain className="h-4 w-4 text-white" />
                      </div>
                    )}
                    <div className={cn(
                      'max-w-[80%] rounded-lg p-4',
                      message.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted'
                    )}>
                      {message.role === 'assistant' && message.domainBrand && (
                        <div className="flex items-center gap-2 mb-2 pb-2 border-b border-border/50">
                          <Badge variant="outline" style={{
                            borderColor: domainColors[message.domain || 'custom'],
                            color: domainColors[message.domain || 'custom'],
                          }}>
                            {message.domainBrand}
                          </Badge>
                          {message.confidence && (
                            <Badge variant="secondary" className="text-xs">
                              {Math.round(message.confidence * 100)}% confianza
                            </Badge>
                          )}
                          {message.rolesConsulted && (
                            <div className="flex gap-1">
                              {message.rolesConsulted.map((role) => {
                                const Icon = roleIcons[role] || HelpCircle
                                return <Icon key={role} className="h-3 w-3 text-muted-foreground" />
                              })}
                            </div>
                          )}
                        </div>
                      )}
                      <div className="prose prose-sm dark:prose-invert max-w-none">
                        {parseContent(message.content)}
                      </div>
                      <div className="flex items-center justify-between mt-2 pt-2 border-t border-border/30">
                        <span className="text-xs text-muted-foreground">{formatTime(message.timestamp)}</span>
                        {message.role === 'assistant' && (
                          <Button variant="ghost" size="icon" className="h-6 w-6"
                            onClick={() => copyToClipboard(message.content, message.id)}>
                            {copiedId === message.id ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                          </Button>
                        )}
                      </div>
                    </div>
                    {message.role === 'user' && (
                      <div className="p-2 rounded-lg bg-primary h-fit">
                        <User className="h-4 w-4 text-primary-foreground" />
                      </div>
                    )}
                  </motion.div>
                ))}
              </AnimatePresence>
              
              {isLoading && (
                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-3">
                  <div className="p-2 rounded-lg bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 h-fit">
                    <Brain className="h-4 w-4 text-white" />
                  </div>
                  <div className="bg-muted rounded-lg p-4">
                    <div className="flex items-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <span className="text-sm">NEXUS está pensando...</span>
                    </div>
                  </div>
                </motion.div>
              )}
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="border-t border-border/50 bg-background/80 backdrop-blur-lg p-4">
          <div className="max-w-4xl mx-auto">
            <div className="flex gap-2">
              <Textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder="Escribe tu mensaje a NEXUS..."
                className="min-h-[60px] max-h-[200px] resize-none"
                disabled={isLoading}
              />
              <Button size="icon" className="h-[60px] w-[60px]" onClick={sendMessage} disabled={!input.trim() || isLoading}>
                {isLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
              </Button>
            </div>
            <div className="flex items-center justify-between mt-2 text-xs text-muted-foreground">
              <div className="flex items-center gap-4">
                <span>Dominio: <Badge variant="outline" className="text-xs">
                  {selectedDomain === 'auto' ? 'Auto' : domains.find(d => d.domain === selectedDomain)?.elegant_name}
                </Badge></span>
                <span>Rol: <Badge variant="outline" className="text-xs">
                  {selectedRole === 'auto' ? 'Auto' : roles.find(r => r.role === selectedRole)?.elegant_name}
                </Badge></span>
              </div>
              <span>Enter para enviar • Shift+Enter para nueva línea</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
