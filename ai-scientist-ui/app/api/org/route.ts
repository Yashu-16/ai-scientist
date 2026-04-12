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
    include: {
      organization: {
        include: {
          members: {
            select: {
              id: true, name: true, email: true,
              orgRole: true, createdAt: true, analysesUsed: true
            }
          },
          invites: {
            where: { accepted: false, expires: { gt: new Date() } },
            select: { id: true, email: true, role: true, createdAt: true }
          },
          analyses: {
            orderBy: { createdAt: "desc" },
            take: 50,
            select: {
              id: true, diseaseName: true, decision: true,
              confidence: true, createdAt: true,
              user: { select: { name: true, email: true } }
            }
          }
        }
      }
    }
  })

  return NextResponse.json({
    org:         user?.organization ?? null,
    userOrgRole: user?.orgRole      ?? null,
  })
}
