// app/api/admin/users/route.ts
import { NextResponse } from "next/server"
import { requireAdmin } from "@/lib/adminGuard"
import { prisma } from "@/lib/prisma"

export async function GET(req: Request) {
  const { error } = await requireAdmin()
  if (error) return error

  const { searchParams } = new URL(req.url)
  const page   = parseInt(searchParams.get("page")  ?? "1")
  const limit  = parseInt(searchParams.get("limit") ?? "20")
  const search = searchParams.get("search") ?? ""
  const plan   = searchParams.get("plan")   ?? ""

  const where: any = {}
  if (search) {
    where.OR = [
      { name:  { contains: search, mode: "insensitive" } },
      { email: { contains: search, mode: "insensitive" } },
    ]
  }
  if (plan) where.plan = plan

  const [users, total] = await Promise.all([
    prisma.user.findMany({
      where,
      orderBy: { createdAt: "desc" },
      skip:    (page - 1) * limit,
      take:    limit,
      select:  {
        id:           true,
        name:         true,
        email:        true,
        plan:         true,
        role:         true,
        analysesUsed: true,
        analysesLimit: true,
        createdAt:    true,
        emailVerified: true,
        organization: { select: { name: true } },
        _count:       { select: { analyses: true } },
      },
    }),
    prisma.user.count({ where }),
  ])

  return NextResponse.json({
    users,
    total,
    pages: Math.ceil(total / limit),
    page,
  })
}