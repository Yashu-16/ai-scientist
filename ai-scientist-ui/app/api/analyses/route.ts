import { NextResponse } from "next/server"
import { auth } from "@/auth"
import { prisma } from "@/lib/prisma"

export async function POST(req: Request) {
  const session = await auth()
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const body = await req.json()

  // Check usage limit
  const user = await prisma.user.findUnique({ where: { id: session.user.id } })
  if (user && user.analysesUsed >= user.analysesLimit && user.plan === "FREE") {
    return NextResponse.json({ error: "Analysis limit reached. Please upgrade." }, { status: 403 })
  }

  const analysis = await prisma.analysis.create({
    data: {
      userId:      session.user.id,
      diseaseName: body.diseaseName,
      result:      body.result,
      decision:    body.decision,
      confidence:  body.confidence,
      riskLevel:   body.riskLevel,
    }
  })

  // Increment usage
  await prisma.user.update({
    where: { id: session.user.id },
    data:  { analysesUsed: { increment: 1 } }
  })

  return NextResponse.json({ success: true, id: analysis.id })
}

export async function GET() {
  const session = await auth()
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const analyses = await prisma.analysis.findMany({
    where:   { userId: session.user.id },
    orderBy: { createdAt: "desc" },
    select: {
      id: true, diseaseName: true, decision: true,
      confidence: true, riskLevel: true, createdAt: true
    }
  })

  return NextResponse.json({ analyses })
}