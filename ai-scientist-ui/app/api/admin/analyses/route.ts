// app/api/admin/analyses/route.ts
import { NextResponse } from "next/server"
import { requireAdmin } from "@/lib/adminGuard"
import { prisma } from "@/lib/prisma"

export async function GET(req: Request) {
  const { error } = await requireAdmin()
  if (error) return error

  const { searchParams } = new URL(req.url)
  const page     = parseInt(searchParams.get("page")     ?? "1")
  const limit    = parseInt(searchParams.get("limit")    ?? "20")
  const decision = searchParams.get("decision") ?? ""
  const search   = searchParams.get("search")   ?? ""

  const where: any = {}
  if (decision) where.decision    = decision
  if (search)   where.diseaseName = { contains: search, mode: "insensitive" }

  const [analyses, total] = await Promise.all([
    prisma.analysis.findMany({
      where,
      orderBy: { createdAt: "desc" },
      skip:    (page - 1) * limit,
      take:    limit,
      select:  {
        id: true, diseaseName: true, decision: true,
        confidence: true, riskLevel: true, createdAt: true,
        user: { select: { name: true, email: true } },
        organization: { select: { name: true } },
      },
    }),
    prisma.analysis.count({ where }),
  ])

  return NextResponse.json({
    analyses,
    total,
    pages: Math.ceil(total / limit),
    page,
  })
}