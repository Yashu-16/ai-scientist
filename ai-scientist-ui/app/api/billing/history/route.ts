// app/api/billing/history/route.ts
import { NextResponse } from "next/server"
import { auth } from "@/auth"
import { prisma } from "@/lib/prisma"

export async function GET() {
  const session = await auth()
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const [payments, subscription, user] = await Promise.all([
    prisma.payment.findMany({
      where:   { userId: session.user.id, status: "CAPTURED" },
      orderBy: { createdAt: "desc" },
    }),
    prisma.subscription.findUnique({
      where: { userId: session.user.id }
    }),
    prisma.user.findUnique({
      where:  { id: session.user.id },
      select: { plan: true, analysesUsed: true, analysesLimit: true }
    })
  ])

  return NextResponse.json({ payments, subscription, user })
}