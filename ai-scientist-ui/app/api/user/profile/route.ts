import { NextResponse } from "next/server"
import { auth } from "@/auth"
import { prisma } from "@/lib/prisma"

export async function GET() {
  const session = await auth()
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const user = await prisma.user.findUnique({
    where:  { id: session.user.id },
    select: {
      id:            true,
      name:          true,
      email:         true,
      image:         true,
      plan:          true,
      role:          true,
      password:      true,
      analysesUsed:  true,
      analysesLimit: true,
      createdAt:     true,
      orgRole:       true,
      organization: {
        select: { id: true, name: true, plan: true }
      },
      subscription: {
        select: {
          plan:             true,
          status:           true,
          currentPeriodEnd: true,
        }
      },
      _count: {
        select: { analyses: true }
      }
    }
  })

  if (!user) {
    return NextResponse.json({ error: "User not found" }, { status: 404 })
  }

  const { password, ...safeUser } = user
  return NextResponse.json({ user: { ...safeUser, hasPassword: !!password } })
}

export async function PATCH(req: Request) {
  const session = await auth()
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const { name } = await req.json()

  if (!name?.trim()) {
    return NextResponse.json({ error: "Name is required" }, { status: 400 })
  }

  const user = await prisma.user.update({
    where:  { id: session.user.id },
    data:   { name: name.trim() },
    select: { id: true, name: true, email: true }
  })

  return NextResponse.json({ success: true, user })
}
