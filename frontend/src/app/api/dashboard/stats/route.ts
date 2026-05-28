// API de Dashboard - Estadísticas del Ecosistema
import { NextResponse } from 'next/server';
import { db } from '@/lib/db';

export async function GET() {
  try {
    // Estadísticas de Agentes
    const agentStats = await db.agent.groupBy({
      by: ['status'],
      _count: { id: true }
    });

    const totalAgents = await db.agent.count();
    const activeAgents = agentStats.find(s => s.status === 'ACTIVE')?._count.id || 0;
    const busyAgents = agentStats.find(s => s.status === 'BUSY')?._count.id || 0;
    const errorAgents = agentStats.find(s => s.status === 'ERROR')?._count.id || 0;

    // Estadísticas de Skills
    const localSkillsCount = await db.localSkill.count({
      where: { status: 'ACTIVE' }
    });
    const remoteSkillsCount = await db.remoteSkill.count({
      where: { status: 'ACTIVE' }
    });
    const activeSkills = await db.localSkill.count({
      where: { status: 'ACTIVE' }
    }) + await db.remoteSkill.count({
      where: { status: 'ACTIVE' }
    });

    // Estadísticas de Ejecuciones (últimas 24h)
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);

    const executionsToday = await db.agentExecution.count({
      where: { startedAt: { gte: yesterday } }
    });

    const completedExecutions = await db.agentExecution.count({
      where: {
        startedAt: { gte: yesterday },
        status: 'COMPLETED'
      }
    });

    const failedExecutions = await db.agentExecution.count({
      where: {
        startedAt: { gte: yesterday },
        status: 'FAILED'
      }
    });

    const successRate = executionsToday > 0 
      ? Math.round((completedExecutions / executionsToday) * 100) 
      : 0;

    // Duración promedio
    const avgDurationResult = await db.agentExecution.aggregate({
      where: {
        startedAt: { gte: yesterday },
        duration: { not: null }
      },
      _avg: { duration: true }
    });
    const avgDuration = Math.round(avgDurationResult._avg.duration || 0);

    // Estadísticas de Memoria
    const memoryCount = await db.memory.count();
    
    const memoryByCategory = await db.memory.groupBy({
      by: ['category'],
      _count: { id: true }
    });

    const avgImportanceResult = await db.memory.aggregate({
      _avg: { importance: true }
    });

    // Estadísticas HITL
    const hitlStats = await db.hITLRequest.groupBy({
      by: ['status'],
      _count: { id: true }
    });

    const pendingHITL = hitlStats.find(s => s.status === 'PENDING')?._count.id || 0;
    const approvedHITL = hitlStats.find(s => s.status === 'APPROVED')?._count.id || 0;
    const rejectedHITL = hitlStats.find(s => s.status === 'REJECTED')?._count.id || 0;

    // Actividad reciente
    const recentExecutions = await db.agentExecution.findMany({
      take: 5,
      orderBy: { startedAt: 'desc' },
      include: {
        agent: { select: { id: true, name: true, type: true } }
      }
    });

    const recentSessions = await db.session.findMany({
      take: 5,
      orderBy: { startedAt: 'desc' },
      include: {
        agent: { select: { id: true, name: true, type: true } }
      }
    });

    return NextResponse.json({
      success: true,
      data: {
        agents: {
          total: totalAgents,
          active: activeAgents,
          busy: busyAgents,
          error: errorAgents,
          byStatus: agentStats.reduce((acc, s) => {
            acc[s.status] = s._count.id;
            return acc;
          }, {} as Record<string, number>)
        },
        skills: {
          local: localSkillsCount,
          remote: remoteSkillsCount,
          active: activeSkills
        },
        executions: {
          today: executionsToday,
          successRate,
          avgDuration,
          completed: completedExecutions,
          failed: failedExecutions
        },
        memory: {
          entries: memoryCount,
          categories: memoryByCategory.length,
          avgImportance: Math.round((avgImportanceResult._avg.importance || 0) * 100) / 100
        },
        hitl: {
          pending: pendingHITL,
          approved: approvedHITL,
          rejected: rejectedHITL
        },
        recentActivity: {
          executions: recentExecutions,
          sessions: recentSessions
        },
        timestamp: new Date().toISOString()
      }
    });
  } catch (error) {
    console.error('Error fetching dashboard stats:', error);
    return NextResponse.json(
      { success: false, error: 'Error al obtener estadísticas' },
      { status: 500 }
    );
  }
}
