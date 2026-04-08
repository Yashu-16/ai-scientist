import { NextResponse } from "next/server"
import { auth } from "@/auth"
import { prisma } from "@/lib/prisma"

export async function PATCH(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const session = await auth()
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }
  const { id } = await params
  const { role } = await req.json()
  const actor = await prisma.user.findUnique({ where: { id: session.user.id } })
  if (!["OWNER", "ADMIN"].includes(actor?.orgRole ?? "")) {
    return NextResponse.json({ error: "Insufficient permissions" }, { status: 403 })
  }
  await prisma.user.update({ where: { id }, data: { orgRole: role } })
  return NextResponse.json({ success: true })
}

export async function DELETE(
  _req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const session = await auth()
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }
  const { id } = await params
  const actor = await prisma.user.findUnique({ where: { id: session.user.id } })
  if (!["OWNER", "ADMIN"].includes(actor?.orgRole ?? "")) {
    return NextResponse.json({ error: "Insufficient permissions" }, { status: 403 })
  }
  const target = await prisma.user.findUnique({ where: { id } })
  if (target?.orgRole === "OWNER") {
    return NextResponse.json({ error: "Cannot remove the organization owner" }, { status: 400 })
  }
  await prisma.user.update({ where: { id }, data: { organizationId: null, orgRole: null } })
  return NextResponse.json({ success: true })
}