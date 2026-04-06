// app/api/analyses/route.ts
import { NextResponse } from "next/server"
import { auth } from "@/auth"
import { prisma } from "@/lib/prisma"

// ── Save analysis ─────────────────────────────────────────────
export async function POST(req: Request) {
  const session = await auth()
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const body = await req.json()
  const user  = await prisma.user.findUnique({
    where: { id: session.user.id }
  })

  // Enforce plan limit
  if (
    user &&
    user.plan === "FREE" &&
    user.analysesUsed >= user.analysesLimit
  ) {
    return NextResponse.json(
      { error: "Analysis limit reached. Please upgrade your plan.", limitReached: true },
      { status: 403 }
    )
  }

  // Save analysis
  const analysis = await prisma.analysis.create({
    data: {
      userId:         session.user.id,
      organizationId: user?.organizationId ?? null,
      diseaseName:    body.diseaseName,
      result:         body.result,
      decision:       body.decision   ?? null,
      confidence:     body.confidence ?? null,
      riskLevel:      body.riskLevel  ?? null,
    }
  })

  // Increment usage counter
  await prisma.user.update({
    where: { id: session.user.id },
    data:  { analysesUsed: { increment: 1 } }
  })

  return NextResponse.json({ success: true, id: analysis.id })
}

// ── Get all analyses for current user ─────────────────────────
export async function GET(req: Request) {
  const session = await auth()
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const { searchParams } = new URL(req.url)
  const page     = parseInt(searchParams.get("page")     ?? "1")
  const limit    = parseInt(searchParams.get("limit")    ?? "20")
  const decision = searchParams.get("decision") // GO | NO-GO | INVESTIGATE | null
  const search   = searchParams.get("search")   // disease name search

  const where: any = { userId: session.user.id }
  if (decision) where.decision = decision
  if (search)   where.diseaseName = { contains: search, mode: "insensitive" }

  const [analyses, total] = await Promise.all([
    prisma.analysis.findMany({
      where,
      orderBy: { createdAt: "desc" },
      skip:    (page - 1) * limit,
      take:    limit,
      select: {
        id:          true,
        diseaseName: true,
        decision:    true,
        confidence:  true,
        riskLevel:   true,
        createdAt:   true,
        // Don't return full result in list — too heavy
      }
    }),
    prisma.analysis.count({ where })
  ])

  // Stats
  const stats = await prisma.analysis.groupBy({
    by:     ["decision"],
    where:  { userId: session.user.id },
    _count: { decision: true }
  })

  return NextResponse.json({
    analyses,
    total,
    page,
    pages: Math.ceil(total / limit),
    stats,
  })
}