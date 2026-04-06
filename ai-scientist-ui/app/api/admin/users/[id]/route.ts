// app/api/admin/users/[id]/route.ts
import { NextResponse } from "next/server"
import { requireAdmin } from "@/lib/adminGuard"
import { prisma } from "@/lib/prisma"

export async function PATCH(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { error } = await requireAdmin()
  if (error) return error

  const { id } = await params
  const { plan, role, analysesLimit } = await req.json()

  const data: any = {}
  if (plan)          data.plan          = plan
  if (role)          data.role          = role
  if (analysesLimit) data.analysesLimit = parseInt(analysesLimit)

  const user = await prisma.user.update({
    where:  { id },
    data,
    select: { id: true, name: true, email: true, plan: true, role: true },
  })

  return NextResponse.json({ success: true, user })
}

export async function DELETE(
  _req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { error, session } = await requireAdmin()
  if (error) return error

  const { id } = await params

  if (id === session!.user.id) {
    return NextResponse.json(
      { error: "Cannot delete your own admin account" },
      { status: 400 }
    )
  }

  await prisma.user.delete({ where: { id } })
  return NextResponse.json({ success: true })
}