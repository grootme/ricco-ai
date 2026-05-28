// API de Skills Remotas - CRUD y Sincronización
import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { z } from 'zod';

const RemoteSkillCreateSchema = z.object({
  name: z.string().min(1).max(100),
  slug: z.string().min(1).max(100).regex(/^[a-z0-9-]+$/),
  source: z.enum(['DEERFLOW', 'NIM', 'LANGCHAIN', 'CUSTOM', 'GITHUB', 'HUGGINGFACE']),
  sourceUrl: z.string().url(),
  sourceId: z.string().optional(),
  category: z.enum(['RESEARCH', 'ANALYSIS', 'GENERATION', 'TRANSFORM', 'VALIDATION', 'INTEGRATION', 'AUTOMATION', 'COMMUNICATION', 'MEMORY', 'SECURITY', 'CUSTOM']),
  description: z.string().optional(),
  version: z.string().optional(),
  author: z.string().optional(),
  config: z.record(z.unknown()).optional(),
  tags: z.array(z.string()).optional(),
});

// GET - Listar skills remotas
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const source = searchParams.get('source');
    const category = searchParams.get('category');
    const syncStatus = searchParams.get('syncStatus');
    const search = searchParams.get('search');
    const page = parseInt(searchParams.get('page') || '1');
    const limit = parseInt(searchParams.get('limit') || '20');

    const where: Record<string, unknown> = {};
    if (source) where.source = source;
    if (category) where.category = category;
    if (syncStatus) where.syncStatus = syncStatus;
    if (search) {
      where.OR = [
        { name: { contains: search } },
        { description: { contains: search } },
      ];
    }

    const [skills, total] = await Promise.all([
      db.remoteSkill.findMany({
        where,
        include: {
          agents: {
            include: {
              agent: { select: { id: true, name: true, type: true } }
            }
          },
          _count: { select: { executions: true, agents: true } }
        },
        orderBy: { createdAt: 'desc' },
        skip: (page - 1) * limit,
        take: limit,
      }),
      db.remoteSkill.count({ where })
    ]);

    return NextResponse.json({
      success: true,
      data: skills.map(skill => ({
        ...skill,
        config: skill.config ? JSON.parse(skill.config) : null,
        inputSchema: skill.inputSchema ? JSON.parse(skill.inputSchema) : null,
        outputSchema: skill.outputSchema ? JSON.parse(skill.outputSchema) : null,
        tags: skill.tags ? JSON.parse(skill.tags) : [],
        metadata: skill.metadata ? JSON.parse(skill.metadata) : null,
      })),
      total,
      page,
      pageSize: limit,
      totalPages: Math.ceil(total / limit),
    });
  } catch (error) {
    console.error('Error fetching remote skills:', error);
    return NextResponse.json(
      { success: false, error: 'Error al obtener skills remotas' },
      { status: 500 }
    );
  }
}

// POST - Registrar nueva skill remota
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const validated = RemoteSkillCreateSchema.parse(body);

    // Verificar slug único
    const existing = await db.remoteSkill.findUnique({
      where: { slug: validated.slug }
    });
    if (existing) {
      return NextResponse.json(
        { success: false, error: 'Ya existe una skill remota con ese slug' },
        { status: 400 }
      );
    }

    const skill = await db.remoteSkill.create({
      data: {
        name: validated.name,
        slug: validated.slug,
        source: validated.source,
        sourceUrl: validated.sourceUrl,
        sourceId: validated.sourceId,
        category: validated.category,
        description: validated.description,
        version: validated.version,
        author: validated.author,
        config: validated.config ? JSON.stringify(validated.config) : null,
        tags: validated.tags ? JSON.stringify(validated.tags) : null,
        status: 'ACTIVE',
        syncStatus: 'PENDING',
      }
    });

    return NextResponse.json({
      success: true,
      data: {
        ...skill,
        config: skill.config ? JSON.parse(skill.config) : null,
        tags: skill.tags ? JSON.parse(skill.tags) : [],
      },
      message: 'Skill remota registrada. Pendiente de sincronización.'
    }, { status: 201 });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { success: false, error: 'Datos inválidos', details: error.errors },
        { status: 400 }
      );
    }
    console.error('Error creating remote skill:', error);
    return NextResponse.json(
      { success: false, error: 'Error al registrar skill remota' },
      { status: 500 }
    );
  }
}
