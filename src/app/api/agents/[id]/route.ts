// API de Agente Individual - GET, PUT, DELETE
import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { z } from 'zod';

const AgentUpdateSchema = z.object({
  name: z.string().min(1).max(100).optional(),
  description: z.string().optional(),
  systemPrompt: z.string().optional(),
  modelProvider: z.string().optional(),
  modelName: z.string().optional(),
  temperature: z.number().min(0).max(2).optional(),
  maxTokens: z.number().min(1).max(100000).optional(),
  capabilities: z.array(z.string()).optional(),
  toolsEnabled: z.boolean().optional(),
  memoryEnabled: z.boolean().optional(),
  hitlEnabled: z.boolean().optional(),
  status: z.enum(['ACTIVE', 'INACTIVE', 'BUSY', 'ERROR', 'MAINTENANCE']).optional(),
  config: z.record(z.unknown()).optional(),
});

// GET - Obtener agente por ID
export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    
    const agent = await db.agent.findUnique({
      where: { id },
      include: {
        localSkills: {
          include: { localSkill: true }
        },
        remoteSkills: {
          include: { remoteSkill: true }
        },
        memories: {
          take: 10,
          orderBy: { createdAt: 'desc' }
        },
        sessions: {
          take: 5,
          orderBy: { startedAt: 'desc' }
        },
        executions: {
          take: 10,
          orderBy: { startedAt: 'desc' }
        },
        _count: {
          select: { sessions: true, executions: true, memories: true }
        }
      }
    });

    if (!agent) {
      return NextResponse.json(
        { success: false, error: 'Agente no encontrado' },
        { status: 404 }
      );
    }

    return NextResponse.json({
      success: true,
      data: {
        ...agent,
        capabilities: agent.capabilities ? JSON.parse(agent.capabilities) : [],
        config: agent.config ? JSON.parse(agent.config) : null,
        metadata: agent.metadata ? JSON.parse(agent.metadata) : null,
        localSkills: agent.localSkills.map(s => ({
          ...s,
          localSkill: {
            ...s.localSkill,
            config: s.localSkill.config ? JSON.parse(s.localSkill.config) : null,
          }
        })),
        remoteSkills: agent.remoteSkills.map(s => ({
          ...s,
          remoteSkill: {
            ...s.remoteSkill,
            config: s.remoteSkill.config ? JSON.parse(s.remoteSkill.config) : null,
          }
        })),
      }
    });
  } catch (error) {
    console.error('Error fetching agent:', error);
    return NextResponse.json(
      { success: false, error: 'Error al obtener agente' },
      { status: 500 }
    );
  }
}

// PUT - Actualizar agente
export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const body = await request.json();
    const validated = AgentUpdateSchema.parse(body);

    const existingAgent = await db.agent.findUnique({ where: { id } });
    if (!existingAgent) {
      return NextResponse.json(
        { success: false, error: 'Agente no encontrado' },
        { status: 404 }
      );
    }

    const agent = await db.agent.update({
      where: { id },
      data: {
        ...validated,
        capabilities: validated.capabilities ? JSON.stringify(validated.capabilities) : undefined,
        config: validated.config ? JSON.stringify(validated.config) : undefined,
      }
    });

    return NextResponse.json({
      success: true,
      data: {
        ...agent,
        capabilities: agent.capabilities ? JSON.parse(agent.capabilities) : [],
        config: agent.config ? JSON.parse(agent.config) : null,
      },
      message: 'Agente actualizado exitosamente'
    });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { success: false, error: 'Datos inválidos', details: error.errors },
        { status: 400 }
      );
    }
    console.error('Error updating agent:', error);
    return NextResponse.json(
      { success: false, error: 'Error al actualizar agente' },
      { status: 500 }
    );
  }
}

// DELETE - Eliminar agente
export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;

    const agent = await db.agent.findUnique({ where: { id } });
    if (!agent) {
      return NextResponse.json(
        { success: false, error: 'Agente no encontrado' },
        { status: 404 }
      );
    }

    // No permitir eliminar Lead Agent activo
    if (agent.type === 'LEAD' && agent.status === 'ACTIVE') {
      return NextResponse.json(
        { success: false, error: 'No se puede eliminar el Lead Agent activo' },
        { status: 400 }
      );
    }

    await db.agent.delete({ where: { id } });

    return NextResponse.json({
      success: true,
      message: 'Agente eliminado exitosamente'
    });
  } catch (error) {
    console.error('Error deleting agent:', error);
    return NextResponse.json(
      { success: false, error: 'Error al eliminar agente' },
      { status: 500 }
    );
  }
}
