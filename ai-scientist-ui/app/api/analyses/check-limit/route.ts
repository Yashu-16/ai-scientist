import { NextResponse } from "next/server"
import { auth } from "@/auth"
import { prisma } from "@/lib/prisma"

export async function GET() {
  const session = await auth()
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const user = await prisma.user.findUnique({
    where: { id: session.user.id },
    select: {
      plan:          true,
      analysesUsed:  true,
      analysesLimit: true,
    }
  })

  if (!user) {
    return NextResponse.json({ error: "User not found" }, { status: 404 })
  }

  const limitReached = user.plan === "FREE" && user.analysesUsed >= user.analysesLimit

  return NextResponse.json({
    limitReached,
    plan:  user.plan,
    used:  user.analysesUsed,
    limit: user.analysesLimit,
  })
}