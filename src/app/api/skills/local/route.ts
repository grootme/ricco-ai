// API de Skills Locales - CRUD
import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/lib/db';
import { z } from 'zod';

const SkillCreateSchema = z.object({
  name: z.string().min(1).max(100),
  slug: z.string().min(1).max(100).regex(/^[a-z0-9-]+$/),
  category: z.enum(['RESEARCH', 'ANALYSIS', 'GENERATION', 'TRANSFORM', 'VALIDATION', 'INTEGRATION', 'AUTOMATION', 'COMMUNICATION', 'MEMORY', 'SECURITY', 'CUSTOM']),
  description: z.string().optional(),
  version: z.string().default('1.0.0'),
  author: z.string().optional(),
  code: z.string().min(1),
  config: z.record(z.unknown()).optional(),
  inputSchema: z.record(z.unknown()).optional(),
  outputSchema: z.record(z.unknown()).optional(),
  isPublic: z.boolean().default(false),
  tags: z.array(z.string()).optional(),
});

// GET - Listar skills locales
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const category = searchParams.get('category');
    const status = searchParams.get('status');
    const search = searchParams.get('search');
    const page = parseInt(searchParams.get('page') || '1');
    const limit = parseInt(searchParams.get('limit') || '20');

    const where: Record<string, unknown> = {};
    if (category) where.category = category;
    if (status) where.status = status;
    if (search) {
      where.OR = [
        { name: { contains: search } },
        { description: { contains: search } },
      ];
    }

    const [skills, total] = await Promise.all([
      db.localSkill.findMany({
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
      db.localSkill.count({ where })
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
    console.error('Error fetching local skills:', error);
    return NextResponse.json(
      { success: false, error: 'Error al obtener skills locales' },
      { status: 500 }
    );
  }
}

// POST - Crear nueva skill local
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const validated = SkillCreateSchema.parse(body);

    // Verificar slug único
    const existing = await db.localSkill.findUnique({
      where: { slug: validated.slug }
    });
    if (existing) {
      return NextResponse.json(
        { success: false, error: 'Ya existe una skill con ese slug' },
        { status: 400 }
      );
    }

    const skill = await db.localSkill.create({
      data: {
        name: validated.name,
        slug: validated.slug,
        category: validated.category,
        description: validated.description,
        version: validated.version,
        author: validated.author,
        code: validated.code,
        config: validated.config ? JSON.stringify(validated.config) : null,
        inputSchema: validated.inputSchema ? JSON.stringify(validated.inputSchema) : null,
        outputSchema: validated.outputSchema ? JSON.stringify(validated.outputSchema) : null,
        isPublic: validated.isPublic,
        tags: validated.tags ? JSON.stringify(validated.tags) : null,
        status: 'ACTIVE',
      }
    });

    return NextResponse.json({
      success: true,
      data: {
        ...skill,
        config: skill.config ? JSON.parse(skill.config) : null,
        inputSchema: skill.inputSchema ? JSON.parse(skill.inputSchema) : null,
        outputSchema: skill.outputSchema ? JSON.parse(skill.outputSchema) : null,
        tags: skill.tags ? JSON.parse(skill.tags) : [],
      },
      message: 'Skill creada exitosamente'
    }, { status: 201 });
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { success: false, error: 'Datos inválidos', details: error.errors },
        { status: 400 }
      );
    }
    console.error('Error creating local skill:', error);
    return NextResponse.json(
      { success: false, error: 'Error al crear skill' },
      { status: 500 }
    );
  }
}
