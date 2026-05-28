import { NextResponse } from 'next/server';
import { db } from '@/lib/db';

export async function GET() {
  try {
    const existingPhases = await db.phase.count();
    if (existingPhases > 0) {
      return NextResponse.json({ message: 'Already seeded', skipped: true });
    }

    const phases = await Promise.all([
      db.phase.create({ data: { number: 1, name: 'Core ERP', description: 'Configuración de Frappe v16 + ERPNext + HRMS', duration: '1-2 meses', status: 'in_progress', progress: 25 } }),
      db.phase.create({ data: { number: 2, name: 'Operations', description: 'Supply Chain, Warehouse, Manufacturing', duration: '3-4 meses', status: 'pending', progress: 0 } }),
      db.phase.create({ data: { number: 3, name: 'CRM & Sales', description: 'ERPNext CRM y módulos de ventas', duration: '5-6 meses', status: 'pending', progress: 0 } }),
      db.phase.create({ data: { number: 4, name: 'Módulos Especializados', description: 'Ricco Tramite, Logistics, Strategy', duration: '7-9 meses', status: 'pending', progress: 0 } }),
    ]);

    const modules = [
      { name: 'Core Financials', slug: 'finance-core', category: 'Finance', frappeApp: 'erpnext', coverage: 'full', status: 'in_progress', progress: 60, estimatedEffort: '2-3 semanas' },
      { name: 'Billing & Invoicing', slug: 'finance-billing', category: 'Finance', frappeApp: 'erpnext', coverage: 'full', status: 'in_progress', progress: 40, estimatedEffort: '2-3 semanas' },
      { name: 'Payments & Treasury', slug: 'finance-payments', category: 'Finance', frappeApp: 'erpnext', coverage: 'full', status: 'planned', progress: 0, estimatedEffort: '2 semanas' },
      { name: 'Employee Records', slug: 'hr-employees', category: 'HR', frappeApp: 'hrms', coverage: 'full', status: 'in_progress', progress: 30, estimatedEffort: '2 semanas' },
      { name: 'Payroll & Compensation', slug: 'hr-payroll', category: 'HR', frappeApp: 'hrms', coverage: 'full', status: 'planned', progress: 0, estimatedEffort: '3-4 semanas' },
      { name: 'Time & Attendance', slug: 'hr-attendance', category: 'HR', frappeApp: 'hrms', coverage: 'full', status: 'planned', progress: 0, estimatedEffort: '2 semanas' },
      { name: 'Supply Chain', slug: 'ops-supply', category: 'Operations', frappeApp: 'erpnext', coverage: 'full', status: 'planned', progress: 0, estimatedEffort: '3 semanas' },
      { name: 'Warehouse', slug: 'ops-warehouse', category: 'Operations', frappeApp: 'erpnext', coverage: 'full', status: 'planned', progress: 0, estimatedEffort: '3 semanas' },
      { name: 'Manufacturing', slug: 'ops-manufacturing', category: 'Operations', frappeApp: 'erpnext', coverage: 'full', status: 'planned', progress: 0, estimatedEffort: '4 semanas' },
      { name: 'CRM Core', slug: 'crm-core', category: 'CRM', frappeApp: 'erpnext_crm', coverage: 'full', status: 'planned', progress: 0, estimatedEffort: '3 semanas' },
      { name: 'Ricco Maintenance', slug: 'ricco-maintenance', category: 'Custom', frappeApp: 'custom', coverage: 'none', status: 'planned', progress: 0, estimatedEffort: '6-8 semanas' },
      { name: 'Ricco Tramite', slug: 'ricco-tramite', category: 'Custom', frappeApp: 'custom', coverage: 'none', status: 'planned', progress: 0, estimatedEffort: '8-12 semanas' },
      { name: 'Ricco Logistics', slug: 'ricco-logistics', category: 'Custom', frappeApp: 'custom', coverage: 'none', status: 'planned', progress: 0, estimatedEffort: '4-6 semanas' },
      { name: 'Ricco Strategy', slug: 'ricco-strategy', category: 'Custom', frappeApp: 'custom', coverage: 'none', status: 'planned', progress: 0, estimatedEffort: '4-6 semanas' },
      { name: 'Ricco CS', slug: 'ricco-cs', category: 'Custom', frappeApp: 'custom', coverage: 'none', status: 'planned', progress: 0, estimatedEffort: '6-8 semanas' },
    ];

    for (const moduleData of modules) {
      const module = await db.module.create({ data: moduleData });
      const phaseNumber = moduleData.category === 'Finance' || moduleData.category === 'HR' ? 1 : moduleData.category === 'Operations' ? 2 : moduleData.category === 'CRM' ? 3 : 4;
      const phase = phases.find(p => p.number === phaseNumber);
      if (phase) {
        await db.modulePhase.create({ data: { moduleId: module.id, phaseId: phase.id, status: moduleData.status } });
      }
    }

    const services = [
      { name: 'ERP Core', slug: 'erp-core', coverage: '95%', complexity: 'low', modules: JSON.stringify(['Finance', 'HR', 'Operations']) },
      { name: 'CRM & Sales', slug: 'crm-sales', coverage: '70%', complexity: 'medium', modules: JSON.stringify(['CRM', 'Sales', 'CS']) },
      { name: 'Supply Chain', slug: 'supply-chain', coverage: '85%', complexity: 'low', modules: JSON.stringify(['Procurement', 'Warehouse']) },
      { name: 'Manufacturing', slug: 'manufacturing', coverage: '80%', complexity: 'medium', modules: JSON.stringify(['Production', 'Quality']) },
      { name: 'Process Management', slug: 'process-mgmt', coverage: '0%', complexity: 'high', modules: JSON.stringify(['Tramite', 'Analytics']) },
      { name: 'Strategic Planning', slug: 'strategic', coverage: '0%', complexity: 'high', modules: JSON.stringify(['OKRs', 'Strategy']) },
    ];

    for (const service of services) {
      await db.service.create({ data: service });
    }

    await db.customer.createMany({ data: [
      { name: 'Acme Corp', email: 'contact@acme.com', type: 'company', status: 'customer' },
      { name: 'Global Industries', email: 'info@global.com', type: 'company', status: 'customer' },
      { name: 'Tech Solutions', email: 'hello@tech.com', type: 'company', status: 'prospect' },
    ]});

    await db.supplier.createMany({ data: [
      { name: 'Raw Materials Inc', category: 'raw_materials', status: 'active' },
      { name: 'Equipment Suppliers', category: 'equipment', status: 'active' },
    ]});

    await db.product.createMany({ data: [
      { sku: 'PROD-001', name: 'Product A', category: 'Electronics', price: 99.99, stock: 150 },
      { sku: 'PROD-002', name: 'Product B', category: 'Electronics', price: 149.99, stock: 80 },
    ]});

    await db.employee.createMany({ data: [
      { employeeId: 'EMP-001', firstName: 'Admin', lastName: 'User', email: 'admin@ricco.com', department: 'IT', position: 'Administrator', status: 'active' },
      { employeeId: 'EMP-002', firstName: 'Maria', lastName: 'Garcia', email: 'maria@ricco.com', department: 'Finance', position: 'Manager', status: 'active' },
      { employeeId: 'EMP-003', firstName: 'Carlos', lastName: 'Lopez', email: 'carlos@ricco.com', department: 'HR', position: 'Director', status: 'active' },
    ]});

    await db.project.createMany({ data: [
      { name: 'Frappe Migration', code: 'PRJ-001', status: 'active', progress: 25 },
      { name: 'CRM Implementation', code: 'PRJ-002', status: 'planning', progress: 0 },
    ]});

    return NextResponse.json({ message: 'Seeded successfully', phases: phases.length, modules: modules.length, services: services.length });
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
