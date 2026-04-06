// app/api/analyses/[id]/route.ts
import { NextResponse } from "next/server"
import { auth } from "@/auth"
import { prisma } from "@/lib/prisma"

// ── Get single analysis (full result) ────────────────────────
export async function GET(
  _req: Request,
  { params }: { params: { id: string } }
) {
  const session = await auth()
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const analysis = await prisma.analysis.findFirst({
    where: {
      id:     params.id,
      userId: session.user.id,    // user can only access their own
    }
  })

  if (!analysis) {
    return NextResponse.json({ error: "Analysis not found" }, { status: 404 })
  }

  return NextResponse.json({ analysis })
}

// ── Delete analysis ───────────────────────────────────────────
export async function DELETE(
  _req: Request,
  { params }: { params: { id: string } }
) {
  const session = await auth()
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  await prisma.analysis.deleteMany({
    where: {
      id:     params.id,
      userId: session.user.id,
    }
  })

  return NextResponse.json({ success: true })
}