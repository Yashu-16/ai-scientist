// app/api/admin/revenue/route.ts
import { NextResponse } from "next/server"
import { requireAdmin } from "@/lib/adminGuard"
import { prisma } from "@/lib/prisma"

export async function GET() {
  const { error } = await requireAdmin()
  if (error) return error

  const payments = await prisma.payment.findMany({
    where:   { status: "CAPTURED" },
    orderBy: { createdAt: "desc" },
    take:    50,
    include: {
      user: { select: { name: true, email: true } }
    },
  })

  // Monthly breakdown (last 6 months)
  const monthly: Record<string, number> = {}
  payments.forEach(p => {
    const key = new Date(p.createdAt)
      .toLocaleDateString("en-IN", { month: "short", year: "numeric" })
    monthly[key] = (monthly[key] ?? 0) + p.amount / 100
  })

  return NextResponse.json({ payments, monthly })
}