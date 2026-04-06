import { NextResponse } from "next/server"
import { auth } from "@/auth"
import { prisma } from "@/lib/prisma"

// Update member role
export async function PATCH(req: Request, { params }: { params: { id: string } }) {
  const session = await auth()
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const { role } = await req.json()

  const actor = await prisma.user.findUnique({ where: { id: session.user.id } })
  if (!["OWNER", "ADMIN"].includes(actor?.orgRole ?? "")) {
    return NextResponse.json({ error: "Insufficient permissions" }, { status: 403 })
  }

  await prisma.user.update({
    where: { id: params.id },
    data: { orgRole: role }
  })

  return NextResponse.json({ success: true })
}

// Remove member
export async function DELETE(_req: Request, { params }: { params: { id: string } }) {
  const session = await auth()
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const actor = await prisma.user.findUnique({ where: { id: session.user.id } })
  if (!["OWNER", "ADMIN"].includes(actor?.orgRole ?? "")) {
    return NextResponse.json({ error: "Insufficient permissions" }, { status: 403 })
  }

  // Can't remove the owner
  const target = await prisma.user.findUnique({ where: { id: params.id } })
  if (target?.orgRole === "OWNER") {
    return NextResponse.json({ error: "Cannot remove the organization owner" }, { status: 400 })
  }

  await prisma.user.update({
    where: { id: params.id },
    data: { organizationId: null, orgRole: null }
  })

  return NextResponse.json({ success: true })
}