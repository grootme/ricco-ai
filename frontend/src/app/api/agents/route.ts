// API de Agentes - CRUD Completo
import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { z } from 'zod';

// Schema de validación
const AgentCreateSchema = z.object({
  name: z.string().min(1).max(100),
  type: z.enum(['LEAD', 'RESEARCHER', 'ANALYZER', 'BUILDER', 'VALIDATOR', 'ORCHESTRATOR', 'MEMORY', 'SECURITY', 'CUSTOM']),
  description: z.string().optional(),
  systemPrompt: z.string().optional(),
  modelProvider: z.string().default('openai'),
  modelName: z.string().default('gpt-4'),
  temperature: z.number().min(0).max(2).default(0.7),
  maxTokens: z.number().min(1).max(100000).default(4096),
  capabilities: z.array(z.string()).optional(),
  toolsEnabled: z.boolean().default(true),
  memoryEnabled: z.boolean().default(true),
  hitlEnabled: z.boolean().default(false),
  config: z.record(z.unknown()).optional(),
});

// GET - Listar todos los agentes
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const type = searchParams.get('type');
    const status = searchParams.get('status');
    const page = parseInt(searchParams.get('page') || '1');
    const limit = parseInt(searchParams.get('limit') || '20');

    const where: Record<string, unknown> = {};
    if (type) where.type = type;
    if (status) where.status = status;

    const [agents, total] = await Promise.all([
      db.agent.findMany({
        where,
        include: {
          localSkills: {
            include: { localSkill: true }
          },
          remoteSkills: {
            include: { remoteSkill: true }
          },
          _count: {
            select: { sessions: true, executions: true, memories: true }
          }
        },
        orderBy: { createdAt: 'desc' },
        skip: (page - 1) * limit,
        take: limit,
      }),
      db.agent.count({ where })
    ]);

    return NextResponse.json({
      success: true,
      data: agents.map(agent => ({
        ...agent,
        capabilities: agent.capabilities ? JSON.parse(agent.capabilities) : [],
        config: agent.config ? JSON.parse(agent.config) : null,
        metadata: agent.metadata ? JSON.parse(agent.metadata) : null,
        localSkills: agent.localSkills.map(s => ({
          id: s.localSkill.id,
          name: s.localSkill.name,
          category: s.localSkill.category,
          enabled: s.enabled,
        })),
        remoteSkills: agent.remoteSkills.map(s => ({
          id: s.remoteSkill.id,
          name: s.remoteSkill.name,
          source: s.remoteSkill.source,
          enabled: s.enabled,
        })),
      })),
      total,
      page,
      pageSize: limit,
      totalPages: Math.ceil(total / limit),
    });
  } catch (error) {
    console.error('Error fetching agents:', error);
    return NextResponse.json(
      { success: false, error: 'Error al obtener agentes' },
      { status: 500 }
    );
  }
}

// POST - Crear nuevo agente
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const validated = AgentCreateSchema.parse(body);

    // Si es LEAD, verificar que no exista otro activo
    if (validated.type === 'LEAD') {
      const existingLead = await db.agent.findFirst({
        where: { type: 'LEAD', status: 'ACTIVE' }
      });
      if (existingLead) {
        return NextResponse.json(
          { success: false, error: 'Ya existe un Lead Agent activo' },
          { status: 400 }
        );
      }
    }

    const agent = await db.agent.create({
      data: {
        name: validated.name,
        type: validated.type,
        description: validated.description,
        systemPrompt: validated.systemPrompt,
        modelProvider: validated.modelProvider,
        modelName: validated.modelName,
        temperature: validated.temperature,
        maxTokens: validated.maxTokens,
        capabilities: validated.capabilities ? JSON.stringify(validated.capabilities) : null,
        toolsEnabled: validated.toolsEnabled,
        memoryEnabled: validated.memoryEnabled,
        hitlEnabled: validated.hitlEnabled,
        config: validated.config ? JSON.stringify(validated.config) : null,
        status: 'INACTIVE',
      }
    });

    return NextResponse.json({
      success: true,
      data: {
        ...agent,
        capabilities: agent.capabilities ? JSON.parse(agent.capabilities) : [],
        config: agent.config ? JSON.parse(agent.config) : null,
      },
      message: 'Agente creado exitosamente'
    }, { status: 201 });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { success: false, error: 'Datos inválidos', details: error.errors },
        { status: 400 }
      );
    }
    console.error('Error creating agent:', error);
    return NextResponse.json(
      { success: false, error: 'Error al crear agente' },
      { status: 500 }
    );
  }
}
