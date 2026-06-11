import { NextResponse } from 'next/server';
import { db } from '@/lib/db';

export async function GET() {
  try {
    const phases = await db.phase.findMany({
      orderBy: { number: 'asc' },
      include: {
        modules: {
          include: { module: true }
        }
      }
    });
    return NextResponse.json(phases);
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
