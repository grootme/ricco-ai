import { NextResponse } from 'next/server';
import { db } from '@/lib/db';

export async function GET() {
  try {
    const [phases, modules, services, customers, employees, products, projects] = await Promise.all([
      db.phase.findMany({ orderBy: { number: 'asc' } }),
      db.module.findMany(),
      db.service.findMany({ where: { isActive: true } }),
      db.customer.findMany(),
      db.employee.findMany(),
      db.product.findMany(),
      db.project.findMany(),
    ]);

    const totalProgress = modules.reduce((acc, m) => acc + m.progress, 0) / Math.max(modules.length, 1);
    
    const modulesByStatus = {
      completed: modules.filter(m => m.status === 'completed').length,
      in_progress: modules.filter(m => m.status === 'in_progress').length,
      planned: modules.filter(m => m.status === 'planned').length,
    };

    const modulesByCategory = modules.reduce((acc: any, m) => {
      acc[m.category] = (acc[m.category] || 0) + 1;
      return acc;
    }, {});

    const modulesByApp = modules.reduce((acc: any, m) => {
      acc[m.frappeApp] = (acc[m.frappeApp] || 0) + 1;
      return acc;
    }, {});

    return NextResponse.json({
      overview: {
        totalPhases: phases.length,
        totalModules: modules.length,
        totalServices: services.length,
        totalProgress: Math.round(totalProgress),
        totalCustomers: customers.length,
        totalEmployees: employees.length,
        totalProducts: products.length,
        totalProjects: projects.length,
      },
      phases,
      modulesByStatus,
      modulesByCategory,
      modulesByApp,
      recentActivity: [
        { type: 'module', action: 'started', name: 'Core Financials', date: new Date().toISOString() },
        { type: 'phase', action: 'activated', name: 'Core ERP', date: new Date().toISOString() },
        { type: 'employee', action: 'created', name: 'Admin User', date: new Date().toISOString() },
      ]
    });
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
