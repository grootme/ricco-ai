'use client'

import { motion } from 'framer-motion'
import { Brain, BookOpen, Lightbulb, Target, TrendingUp } from 'lucide-react'
import { CognitiveCapitalDashboard } from '@/components/cognitive-capital/capital-dashboard'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export default function CapitalPage() {
  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-8 space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
              <Brain className="h-8 w-8 text-primary" />
              Cognitive Capital
            </h1>
            <p className="text-muted-foreground mt-1">
              Knowledge + Experience + Patterns + Skills stored as cognitive capital
            </p>
          </div>
        </div>

        {/* What is Cognitive Capital */}
        <Card className="bg-gradient-to-r from-primary/5 to-primary/10">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="h-5 w-5" />
              ¿Qué es el Capital Cognitivo?
            </CardTitle>
            <CardDescription>
              El conocimiento acumulado que un agente posee y puede usar
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg bg-blue-500/10">
                  <BookOpen className="h-5 w-5 text-blue-500" />
                </div>
                <div>
                  <h3 className="font-semibold">Knowledge</h3>
                  <p className="text-sm text-muted-foreground">
                    Información factual, documentos procesados, procedimientos
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg bg-amber-500/10">
                  <Lightbulb className="h-5 w-5 text-amber-500" />
                </div>
                <div>
                  <h3 className="font-semibold">Experience</h3>
                  <p className="text-sm text-muted-foreground">
                    Casos resueltos, errores aprendidos, patrones de usuario
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg bg-purple-500/10">
                  <Target className="h-5 w-5 text-purple-500" />
                </div>
                <div>
                  <h3 className="font-semibold">Patterns</h3>
                  <p className="text-sm text-muted-foreground">
                    Workflows exitosos, decisiones en contextos específicos
                  </p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg bg-green-500/10">
                  <TrendingUp className="h-5 w-5 text-green-500" />
                </div>
                <div>
                  <h3 className="font-semibold">Skills</h3>
                  <p className="text-sm text-muted-foreground">
                    Capacidades desarrolladas, tareas dominadas
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Main Dashboard */}
        <CognitiveCapitalDashboard />
      </div>
    </div>
  )
}
