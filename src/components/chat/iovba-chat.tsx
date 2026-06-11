'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { io, Socket } from 'socket.io-client'
import {
  Send,
  Bot,
  User,
  Sparkles,
  Brain,
  Users,
  Zap,
  Settings,
  Trash2,
  Copy,
  Check,
  Loader2,
  Wifi,
  WifiOff,
  ChevronDown,
  MessageSquare,
  Cpu,
  Network,
  Shield,
  Eye,
  Microscope,
  Hammer,
  HelpCircle,
  Globe,
  TrendingUp,
  Scale,
  GraduationCap,
  FlaskConical,
  Dna,
  Atom,
  Heart,
  Trophy,
  Newspaper,
  Megaphone,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'

// Types
interface Message {
  id: string
  role: 'user' | 'assistant' | 'system' | 'agent'
  content: string
  timestamp: Date
  agentId?: string
  agentName?: string
  domain?: string
  metadata?: {
    confidence?: number
    processingTime?: number
    role?: string
  }
}

interface Agent {
  id: string
  name: string
  domain: string
  role: string
  status: string
  cognitiveCapital: number
  skills: string[]
  color: string
}

interface Domain {
  name: string
  elegantName: string
  color: string
  icon: string
  description: string
}

// Icon mapping
const iconMap: Record<string, React.ElementType> = {
  code: Cpu,
  heart: Heart,
  trophy: Trophy,
  newspaper: Newspaper,
  flask: FlaskConical,
  dna: Dna,
  atom: Atom,
  globe: Globe,
  'trending-up': TrendingUp,
  scale: Scale,
  'graduation-cap': GraduationCap,
  microscope: Microscope,
  megaphone: Megaphone,
  eye: Eye,
  shield: Shield,
  hammer: Hammer,
  'help-circle': HelpCircle,
  network: Network,
}

const roleIconMap: Record<string, React.ElementType> = {
  INVESTIGADOR: Microscope,
  OBSERVADOR: Eye,
  VALIDADOR: Shield,
  BUILDER: Hammer,
  ASISTENTE: HelpCircle,
}

// Mode type
type ChatMode = 'direct' | 'super-agent'

export function IOVBAChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [mode, setMode] = useState<ChatMode>('direct')
  const [isTyping, setIsTyping] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [agents, setAgents] = useState<Agent[]>([])
  const [domains, setDomains] = useState<Record<string, Domain>>({})
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const [useHttp, setUseHttp] = useState(true) // Default to HTTP mode for reliability
  
  const socketRef = useRef<Socket | null>(null)
  const scrollRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Initialize WebSocket connection
  useEffect(() => {
    if (!useHttp) {
      const socket = io('/?XTransformPort=3030', {
        transports: ['websocket', 'polling'],
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 1000,
      })

      socket.on('connect', () => {
        console.log('Connected to IOVBA Chat Service')
        setIsConnected(true)
      })

      socket.on('disconnect', () => {
        console.log('Disconnected from IOVBA Chat Service')
        setIsConnected(false)
      })

      socket.on('connected', (data) => {
        setSessionId(data.sessionId)
        setAgents(data.agents || [])
        setDomains(data.domains || {})
      })

      socket.on('session-created', (session) => {
        setSessionId(session.id)
      })

      socket.on('message-received', (message: Message) => {
        setMessages(prev => [...prev, { ...message, timestamp: new Date(message.timestamp) }])
      })

      socket.on('typing', ({ isTyping: typing }) => {
        setIsTyping(typing)
      })

      socket.on('agent-response', (message: Message) => {
        setMessages(prev => [...prev, { ...message, timestamp: new Date(message.timestamp) }])
        setIsTyping(false)
      })

      socket.on('error', (error) => {
        console.error('Socket error:', error)
        setIsTyping(false)
      })

      socketRef.current = socket

      // Create session
      socket.emit('create-session', { mode, userId: 'user-' + Date.now() })

      return () => {
        socket.disconnect()
      }
    } else {
      // HTTP mode - fetch initial data
      fetch('/api/chat')
        .then(res => res.json())
        .then(data => {
          setIsConnected(true)
          setAgents(data.agents || [])
          setDomains(data.domains || {})
          setSessionId(`http-session-${Date.now()}`)
        })
        .catch(err => {
          console.error('Failed to fetch chat data:', err)
          setIsConnected(false)
        })
    }
  }, [useHttp, mode])

  // Auto-scroll to bottom
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  // Send message via HTTP
  const sendMessageHttp = async (messageText: string) => {
    try {
      setIsTyping(true)
      
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: messageText,
          mode,
          sessionId,
        }),
      })

      const data = await response.json()

      if (data.success) {
        const agentMessage: Message = {
          id: `msg-${Date.now()}`,
          role: 'agent',
          content: data.response,
          timestamp: new Date(),
          agentId: 'iovba-assistant',
          agentName: mode === 'direct' ? 'IOVBA Assistant' : 'Lead Assistant',
          domain: data.domain,
          metadata: {
            confidence: 0.85,
            processingTime: 500,
          },
        }

        setMessages(prev => [...prev, agentMessage])

        // Add individual agent responses if in super-agent mode
        if (data.agents && data.agents.length > 0) {
          for (const agent of data.agents) {
            setMessages(prev => [...prev, {
              id: `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
              role: 'agent',
              content: agent.response,
              timestamp: new Date(),
              agentId: agent.id || agent.name.toLowerCase().replace(/\s+/g, '-'),
              agentName: agent.name,
              domain: data.domain,
              metadata: {
                confidence: agent.confidence,
                role: agent.role,
              },
            }])
          }
        }
      }
    } catch (error) {
      console.error('Failed to send message:', error)
    } finally {
      setIsTyping(false)
    }
  }

  // Send message
  const handleSend = useCallback(async () => {
    const trimmedInput = input.trim()
    if (!trimmedInput || isTyping) return

    const userMessage: Message = {
      id: `msg-${Date.now()}`,
      role: 'user',
      content: trimmedInput,
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')

    if (useHttp) {
      await sendMessageHttp(trimmedInput)
    } else if (socketRef.current && isConnected) {
      socketRef.current.emit('chat-message', {
        sessionId,
        message: trimmedInput,
        mode,
      })
    }
  }, [input, isTyping, useHttp, sessionId, mode, isConnected])

  // Handle key press
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  // Copy message to clipboard
  const copyToClipboard = async (text: string, id: string) => {
    await navigator.clipboard.writeText(text)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  // Clear chat
  const clearChat = () => {
    setMessages([])
  }

  // Switch mode
  const handleModeSwitch = (newMode: ChatMode) => {
    setMode(newMode)
    if (socketRef.current && isConnected) {
      socketRef.current.emit('switch-mode', { sessionId, mode: newMode })
    }
  }

  return (
    <div className="flex h-full">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="border-b border-border/50 bg-card/30 backdrop-blur-sm p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-gradient-to-br from-violet-500 via-purple-500 to-fuchsia-500 shadow-lg shadow-purple-500/25">
                <Sparkles className="h-5 w-5 text-white" />
              </div>
              <div>
                <h2 className="font-bold text-lg">IOVBA Chat</h2>
                <p className="text-xs text-muted-foreground">
                  Sistema Multi-Agente Inteligente
                </p>
              </div>
            </div>
            
            <div className="flex items-center gap-4">
              {/* Mode Toggle */}
              <div className="flex items-center gap-2 border rounded-lg p-1">
                <Button
                  variant={mode === 'direct' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => handleModeSwitch('direct')}
                  className="gap-1"
                >
                  <Bot className="h-4 w-4" />
                  Directo
                </Button>
                <Button
                  variant={mode === 'super-agent' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => handleModeSwitch('super-agent')}
                  className="gap-1"
                >
                  <Users className="h-4 w-4" />
                  Super Agente
                </Button>
              </div>

              {/* Connection Status */}
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Badge variant={isConnected ? 'default' : 'secondary'} className="gap-1">
                      {isConnected ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
                      {isConnected ? 'Conectado' : 'Desconectado'}
                    </Badge>
                  </TooltipTrigger>
                  <TooltipContent>
                    {useHttp ? 'Modo HTTP activo' : 'Modo WebSocket activo'}
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>

              {/* Clear Chat */}
              <Button variant="ghost" size="icon" onClick={clearChat}>
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Mode Description */}
          <div className="mt-3 text-sm text-muted-foreground">
            {mode === 'direct' ? (
              <span className="flex items-center gap-2">
                <Bot className="h-4 w-4 text-violet-500" />
                <strong>Modo Directo:</strong> Interactúa directamente con el asistente IOVBA
              </span>
            ) : (
              <span className="flex items-center gap-2">
                <Users className="h-4 w-4 text-fuchsia-500" />
                <strong>Modo Super Agente:</strong> Múltiples agentes coordinan para responderte
              </span>
            )}
          </div>
        </div>

        {/* Messages Area */}
        <ScrollArea className="flex-1 p-4" ref={scrollRef}>
          <div className="space-y-4 max-w-4xl mx-auto">
            {/* Welcome Message */}
            {messages.length === 0 && (
              <div className="text-center py-12">
                <motion.div
                  initial={{ scale: 0.8, opacity: 0 }}
                  animate={{ scale: 1, opacity: 1 }}
                  className="inline-block p-4 rounded-full bg-gradient-to-br from-violet-500/20 to-fuchsia-500/20 mb-4"
                >
                  <Brain className="h-12 w-12 text-violet-500" />
                </motion.div>
                <h3 className="text-xl font-bold mb-2">Bienvenido a IOVBA Chat</h3>
                <p className="text-muted-foreground max-w-md mx-auto">
                  Sistema multi-agente inteligente con 13 dominios especializados.
                  Pregunta cualquier cosa y deja que los agentes IOVBA te ayuden.
                </p>
                <div className="flex flex-wrap gap-2 justify-center mt-6">
                  <Button variant="outline" size="sm" onClick={() => setInput('¿Qué puedes hacer?')}>
                    ¿Qué puedes hacer?
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => setInput('Explícame el sistema IOVBA')}>
                    Explícame IOVBA
                  </Button>
                  <Button variant="outline" size="sm" onClick={() => setInput('¿Cuáles son los dominios disponibles?')}>
                    Ver dominios
                  </Button>
                </div>
              </div>
            )}

            {/* Messages */}
            <AnimatePresence>
              {messages.map((message) => (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  {message.role !== 'user' && (
                    <Avatar className="h-8 w-8 mt-1">
                      <AvatarFallback 
                        className="bg-gradient-to-br from-violet-500 to-fuchsia-500 text-white text-xs"
                      >
                        {message.agentName?.charAt(0) || <Bot className="h-4 w-4" />}
                      </AvatarFallback>
                    </Avatar>
                  )}
                  
                  <div className={`max-w-[80%] ${message.role === 'user' ? 'order-1' : ''}`}>
                    {message.agentName && (
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-medium">{message.agentName}</span>
                        {message.domain && (
                          <Badge variant="outline" className="text-xs">
                            {message.domain}
                          </Badge>
                        )}
                        {message.metadata?.confidence && (
                          <Badge variant="secondary" className="text-xs">
                            {(message.metadata.confidence * 100).toFixed(0)}% confianza
                          </Badge>
                        )}
                      </div>
                    )}
                    <Card className={`${message.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted'}`}>
                      <CardContent className="p-3">
                        <div className="prose prose-sm dark:prose-invert max-w-none">
                          {message.content.split('\n').map((line, i) => (
                            <p key={i} className={line.startsWith('#') || line.startsWith('**') ? 'font-semibold' : ''}>
                              {line}
                            </p>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                    <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                      <span>{new Date(message.timestamp).toLocaleTimeString()}</span>
                      {message.role !== 'user' && (
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 px-2"
                          onClick={() => copyToClipboard(message.content, message.id)}
                        >
                          {copiedId === message.id ? (
                            <Check className="h-3 w-3" />
                          ) : (
                            <Copy className="h-3 w-3" />
                          )}
                        </Button>
                      )}
                    </div>
                  </div>

                  {message.role === 'user' && (
                    <Avatar className="h-8 w-8 mt-1 order-2">
                      <AvatarFallback className="bg-gradient-to-br from-emerald-500 to-teal-500 text-white">
                        <User className="h-4 w-4" />
                      </AvatarFallback>
                    </Avatar>
                  )}
                </motion.div>
              ))}
            </AnimatePresence>

            {/* Typing Indicator */}
            {isTyping && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex gap-3"
              >
                <Avatar className="h-8 w-8">
                  <AvatarFallback className="bg-gradient-to-br from-violet-500 to-fuchsia-500 text-white">
                    <Bot className="h-4 w-4" />
                  </AvatarFallback>
                </Avatar>
                <Card className="bg-muted">
                  <CardContent className="p-3 flex items-center gap-2">
                    <Loader2 className="h-4 w-4 animate-spin" />
                    <span className="text-sm text-muted-foreground">
                      {mode === 'direct' ? 'IOVBA está pensando...' : 'Agentes coordinando respuesta...'}
                    </span>
                  </CardContent>
                </Card>
              </motion.div>
            )}
          </div>
        </ScrollArea>

        {/* Input Area */}
        <div className="border-t border-border/50 bg-card/30 backdrop-blur-sm p-4">
          <div className="max-w-4xl mx-auto">
            <div className="flex gap-2">
              <Textarea
                ref={inputRef as React.RefObject<HTMLTextAreaElement>}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder={
                  mode === 'direct'
                    ? 'Escribe tu mensaje al asistente IOVBA...'
                    : 'Escribe tu mensaje - múltiples agentes coordinarán la respuesta...'
                }
                className="min-h-[60px] resize-none"
                disabled={isTyping}
              />
              <Button
                onClick={handleSend}
                disabled={!input.trim() || isTyping}
                className="h-auto px-4"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
            <div className="flex items-center justify-between mt-2 text-xs text-muted-foreground">
              <span>Presiona Enter para enviar, Shift+Enter para nueva línea</span>
              <div className="flex items-center gap-2">
                <Label htmlFor="http-mode" className="text-xs">HTTP Mode</Label>
                <Switch
                  id="http-mode"
                  checked={useHttp}
                  onCheckedChange={setUseHttp}
                />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Sidebar - Agents List */}
      <div className="w-72 border-l border-border/50 bg-card/30 backdrop-blur-sm flex flex-col">
        <div className="p-4 border-b border-border/50">
          <h3 className="font-semibold flex items-center gap-2">
            <Network className="h-4 w-4" />
            Agentes Disponibles
          </h3>
          <p className="text-xs text-muted-foreground mt-1">
            {agents.length} agentes activos
          </p>
        </div>
        
        <ScrollArea className="flex-1">
          <div className="p-2 space-y-1">
            {agents.slice(0, 20).map((agent) => {
              const RoleIcon = roleIconMap[agent.role] || Bot
              return (
                <TooltipProvider key={agent.id}>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div className="flex items-center gap-2 p-2 rounded-lg hover:bg-muted/50 cursor-pointer transition-colors">
                        <div
                          className="p-1.5 rounded-md"
                          style={{ backgroundColor: agent.color + '20' }}
                        >
                          <RoleIcon className="h-3.5 w-3.5" style={{ color: agent.color }} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-xs font-medium truncate">{agent.name}</p>
                          <p className="text-[10px] text-muted-foreground truncate">
                            {agent.domain}
                          </p>
                        </div>
                        <Badge variant="secondary" className="text-[10px] px-1">
                          {agent.cognitiveCapital}
                        </Badge>
                      </div>
                    </TooltipTrigger>
                    <TooltipContent side="left" className="max-w-xs">
                      <div className="text-xs">
                        <p className="font-medium">{agent.name}</p>
                        <p className="text-muted-foreground">{agent.role}</p>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {agent.skills.map((skill) => (
                            <Badge key={skill} variant="outline" className="text-[10px]">
                              {skill}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )
            })}
          </div>
        </ScrollArea>

        {/* Domains Summary */}
        <div className="p-4 border-t border-border/50">
          <h4 className="text-xs font-semibold mb-2">Dominios IOVBA</h4>
          <div className="flex flex-wrap gap-1">
            {Object.entries(domains).slice(0, 7).map(([key, domain]) => {
              const DomainIcon = iconMap[domain.icon] || Network
              return (
                <Badge
                  key={key}
                  variant="outline"
                  className="text-[10px] px-1.5"
                  style={{ borderColor: domain.color + '60', color: domain.color }}
                >
                  <DomainIcon className="h-3 w-3 mr-1" />
                  {domain.elegantName}
                </Badge>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
