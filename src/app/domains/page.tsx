'use client'

import { motion } from 'framer-motion'
import { 
  Warehouse,
  HeadphonesIcon,
  Video,
  FileSearch,
  FlaskConical,
  Heart,
  ShoppingCart,
  Network,
  Brain,
  ChevronRight,
  ExternalLink
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

const NVIDIA_DOMAINS = [
  {
    id: 'warehouse_operations',
    name: 'Warehouse Operations',
    icon: Warehouse,
    description: 'Optimización de operaciones de almacén, inventario y logística',
    agents: ['Equipment Agent', 'Operations Agent', 'Safety Agent', 'Forecasting Agent', 'Document Agent'],
    keySkills: ['asset_tracking', 'inventory_management', 'safety_monitoring', 'demand_forecasting'],
    technologies: ['LangGraph', 'Milvus', 'PostgreSQL/TimescaleDB', 'NVIDIA NIM'],
    color: 'text-orange-500',
    bgColor: 'bg-orange-500/10',
    borderColor: 'border-orange-500/20',
    nvidiaLink: 'https://build.nvidia.com/nvidia/multi-agent-intelligent-warehouse',
  },
  {
    id: 'customer_service',
    name: 'Customer Service',
    icon: HeadphonesIcon,
    description: 'Servicio al cliente con soporte automatizado y avatares digitales',
    agents: ['RAG Agent', 'Avatar Agent', 'Speech Agent'],
    keySkills: ['customer_support', 'rag_qa', 'speech_processing'],
    technologies: ['NVIDIA ACE', 'Tokkio', 'NeMo', 'TTS/STT'],
    color: 'text-blue-500',
    bgColor: 'bg-blue-500/10',
    borderColor: 'border-blue-500/20',
    nvidiaLink: 'https://build.nvidia.com/nvidia/digital-human',
  },
  {
    id: 'video_analytics',
    name: 'Video Search & Summarization',
    icon: Video,
    description: 'Búsqueda, resumen y análisis de video con VLMs',
    agents: ['Ingestion Agent', 'VLM Agent', 'Search Agent', 'Summarization Agent'],
    keySkills: ['video_search', 'video_summarization', 'visual_qa'],
    technologies: ['VLMs', 'Milvus', 'Cosmos Reason', 'NVIDIA NIM'],
    color: 'text-purple-500',
    bgColor: 'bg-purple-500/10',
    borderColor: 'border-purple-500/20',
    nvidiaLink: 'https://build.nvidia.com/nvidia/video-search-and-summarization',
  },
  {
    id: 'enterprise_rag',
    name: 'Enterprise RAG',
    icon: FileSearch,
    description: 'Retrieval-Augmented Generation para conocimiento empresarial',
    agents: ['Document Agent', 'Embedding Agent', 'Retrieval Agent', 'Generation Agent'],
    keySkills: ['document_processing', 'semantic_search', 'generation'],
    technologies: ['NeMo Retriever', 'Milvus', 'OpenSearch', 'Guardrailing'],
    color: 'text-green-500',
    bgColor: 'bg-green-500/10',
    borderColor: 'border-green-500/20',
    nvidiaLink: 'https://build.nvidia.com/nvidia/rag',
  },
  {
    id: 'drug_discovery',
    name: 'Drug Discovery',
    icon: FlaskConical,
    description: 'Descubrimiento de fármacos con IA generativa molecular',
    agents: ['Protein Agent', 'Molecule Agent', 'Docking Agent', 'Screening Agent'],
    keySkills: ['protein_structure', 'molecule_generation', 'virtual_screening'],
    technologies: ['BioNeMo', 'NIM', 'GPU-accelerated microservices'],
    color: 'text-pink-500',
    bgColor: 'bg-pink-500/10',
    borderColor: 'border-pink-500/20',
    nvidiaLink: 'https://build.nvidia.com/nvidia/generative-virtual-screening',
  },
  {
    id: 'healthcare',
    name: 'Healthcare',
    icon: Heart,
    description: 'Consultas de salud, programación de citas y bienestar',
    agents: ['Consultation Agent', 'Scheduling Agent', 'Wellness Agent'],
    keySkills: ['health_consultation', 'appointment_scheduling', 'wellness_tracking'],
    technologies: ['NIM', 'LLMs', 'RAG', 'Integration APIs'],
    color: 'text-red-500',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/20',
    nvidiaLink: '#',
  },
  {
    id: 'retail_commerce',
    name: 'Retail & Commerce',
    icon: ShoppingCart,
    description: 'E-commerce, gestión de productos y enriquecimiento de catálogos',
    agents: ['Product Agent', 'Content Agent', '3D Agent', 'Quality Agent'],
    keySkills: ['product_analysis', 'content_generation', '3d_generation'],
    technologies: ['Nemotron VLM', 'FLUX', 'TRELLIS', 'NIM'],
    color: 'text-amber-500',
    bgColor: 'bg-amber-500/10',
    borderColor: 'border-amber-500/20',
    nvidiaLink: 'https://build.nvidia.com/nvidia/retail-catalog-enrichment',
  },
  {
    id: 'orchestration',
    name: 'Orchestration',
    icon: Network,
    description: 'Coordinación de múltiples agentes y routing de tareas',
    agents: ['Lead Agent', 'Router Agent', 'Coordinator Agent'],
    keySkills: ['task_routing', 'agent_coordination', 'conflict_resolution'],
    technologies: ['LangGraph', 'NeMo Agent Toolkit', 'A2A Protocol'],
    color: 'text-teal-500',
    bgColor: 'bg-teal-500/10',
    borderColor: 'border-teal-500/20',
    nvidiaLink: 'https://build.nvidia.com/nvidia/aiq',
  },
]

export default function DomainsPage() {
  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8 space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Brain className="h-8 w-8 text-primary" />
            NVIDIA AI Blueprint Domains
          </h1>
          <p className="text-muted-foreground mt-1">
            11 domains with specialized agents, all compatible with OpenClaw Agent SaaS
          </p>
        </div>

        {/* Domain Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {NVIDIA_DOMAINS.map((domain, index) => {
            const Icon = domain.icon
            return (
              <motion.div
                key={domain.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <Card className={`h-full hover:shadow-lg transition-all border-2 ${domain.borderColor}`}>
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`p-2 rounded-lg ${domain.bgColor}`}>
                          <Icon className={`h-6 w-6 ${domain.color}`} />
                        </div>
                        <div>
                          <CardTitle>{domain.name}</CardTitle>
                          <Badge variant="outline" className="mt-1">
                            {domain.agents.length} agents
                          </Badge>
                        </div>
                      </div>
                      {domain.nvidiaLink !== '#' && (
                        <Button variant="ghost" size="icon" asChild>
                          <a href={domain.nvidiaLink} target="_blank" rel="noopener noreferrer">
                            <ExternalLink className="h-4 w-4" />
                          </a>
                        </Button>
                      )}
                    </div>
                    <CardDescription className="mt-2">
                      {domain.description}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {/* Agents */}
                    <div>
                      <h4 className="text-sm font-semibold mb-2">Specialized Agents</h4>
                      <div className="flex flex-wrap gap-1">
                        {domain.agents.map(agent => (
                          <Badge key={agent} variant="secondary" className="text-xs">
                            {agent}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    {/* Key Skills */}
                    <div>
                      <h4 className="text-sm font-semibold mb-2">Key Skills</h4>
                      <div className="flex flex-wrap gap-1">
                        {domain.keySkills.map(skill => (
                          <Badge key={skill} variant="outline" className="text-xs">
                            {skill.replace('_', ' ')}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    {/* Technologies */}
                    <div>
                      <h4 className="text-sm font-semibold mb-2">Technologies</h4>
                      <div className="flex flex-wrap gap-1">
                        {domain.technologies.map(tech => (
                          <Badge key={tech} className="text-xs">
                            {tech}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
