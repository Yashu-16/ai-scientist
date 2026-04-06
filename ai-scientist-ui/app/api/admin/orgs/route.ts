// app/api/admin/orgs/route.ts
import { NextResponse } from "next/server"
import { requireAdmin } from "@/lib/adminGuard"
import { prisma } from "@/lib/prisma"

export async function GET() {
  const { error } = await requireAdmin()
  if (error) return error

  const orgs = await prisma.organization.findMany({
    orderBy: { createdAt: "desc" },
    include: {
      members:  { select: { id: true, name: true, email: true, orgRole: true } },
      _count:   { select: { analyses: true, members: true } },
    },
  })

  return NextResponse.json({ orgs })
}