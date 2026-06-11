'use client'

import { motion } from 'framer-motion'
import { 
  Building,
  ShoppingCart,
  Users,
  Truck,
  Factory,
  Stethoscope,
  GraduationCap,
  Home,
  Utensils,
  Plane,
  Banknote,
  Scale,
  Leaf,
  Zap,
  Gamepad2,
  Heart,
  LucideIcon
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface Integration {
  name: string
  description: string
  icon: LucideIcon
  color: string
  status: 'active' | 'beta' | 'coming-soon'
}

const integrations: Integration[] = [
  { name: 'ERP Enterprise', description: 'Enterprise resource planning', icon: Building, color: 'text-emerald-500', status: 'active' },
  { name: 'E-Commerce', description: 'Online store management', icon: ShoppingCart, color: 'text-teal-500', status: 'active' },
  { name: 'CRM', description: 'Customer relationship management', icon: Users, color: 'text-cyan-500', status: 'active' },
  { name: 'Logistics', description: 'Supply chain & delivery', icon: Truck, color: 'text-sky-500', status: 'active' },
  { name: 'Manufacturing', description: 'Production & inventory', icon: Factory, color: 'text-emerald-400', status: 'active' },
  { name: 'Healthcare', description: 'Medical practice management', icon: Stethoscope, color: 'text-teal-400', status: 'active' },
  { name: 'Education', description: 'Learning management system', icon: GraduationCap, color: 'text-cyan-400', status: 'active' },
  { name: 'Real Estate', description: 'Property management', icon: Home, color: 'text-sky-400', status: 'beta' },
  { name: 'Restaurant', description: 'Food service & POS', icon: Utensils, color: 'text-emerald-500', status: 'beta' },
  { name: 'Travel', description: 'Booking & reservations', icon: Plane, color: 'text-teal-500', status: 'beta' },
  { name: 'Finance', description: 'Accounting & payments', icon: Banknote, color: 'text-cyan-500', status: 'active' },
  { name: 'Legal', description: 'Law practice management', icon: Scale, color: 'text-sky-500', status: 'beta' },
  { name: 'Agriculture', description: 'Farm management system', icon: Leaf, color: 'text-emerald-400', status: 'coming-soon' },
  { name: 'Energy', description: 'Utility management', icon: Zap, color: 'text-teal-400', status: 'coming-soon' },
  { name: 'Gaming', description: 'Game studio tools', icon: Gamepad2, color: 'text-cyan-400', status: 'coming-soon' },
  { name: 'Wellness', description: 'Health & fitness', icon: Heart, color: 'text-sky-400', status: 'coming-soon' },
]

const statusColors = {
  'active': 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20',
  'beta': 'bg-amber-500/10 text-amber-500 border-amber-500/20',
  'coming-soon': 'bg-muted text-muted-foreground border-border',
}

interface IntegrationsSectionProps {
  inView?: boolean
}

export function IntegrationsSection({ inView = true }: IntegrationsSectionProps) {
  const activeCount = integrations.filter(i => i.status === 'active').length
  const betaCount = integrations.filter(i => i.status === 'beta').length
  
  return (
    <div className="space-y-6">
      {/* Summary Stats */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={inView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
        transition={{ duration: 0.5 }}
        className="flex flex-wrap gap-4 justify-center"
      >
        <Badge variant="secondary" className="px-4 py-2 text-sm">
          <span className="text-emerald-500 font-bold mr-1">{activeCount}</span> Active
        </Badge>
        <Badge variant="secondary" className="px-4 py-2 text-sm">
          <span className="text-amber-500 font-bold mr-1">{betaCount}</span> Beta
        </Badge>
        <Badge variant="secondary" className="px-4 py-2 text-sm">
          <span className="text-muted-foreground font-bold mr-1">{integrations.length - activeCount - betaCount}</span> Coming Soon
        </Badge>
      </motion.div>

      {/* Integrations Grid */}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {integrations.map((integration, index) => (
          <motion.div
            key={integration.name}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={inView ? { opacity: 1, scale: 1 } : { opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.3, delay: index * 0.05 }}
            whileHover={{ scale: 1.02 }}
          >
            <Card className={`h-full border-border/50 bg-card/50 backdrop-blur-sm hover:bg-card/80 transition-all duration-300 ${integration.status === 'coming-soon' ? 'opacity-60' : ''}`}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`p-2 rounded-lg bg-muted/50`}>
                      <integration.icon className={`h-4 w-4 ${integration.color}`} />
                    </div>
                    <div>
                      <p className="font-medium text-sm">{integration.name}</p>
                      <p className="text-xs text-muted-foreground">{integration.description}</p>
                    </div>
                  </div>
                </div>
                <div className="mt-2">
                  <Badge 
                    variant="outline" 
                    className={`text-xs ${statusColors[integration.status]}`}
                  >
                    {integration.status}
                  </Badge>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
