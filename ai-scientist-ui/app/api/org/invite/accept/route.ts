import { NextResponse } from "next/server"
import { auth } from "@/auth"
import { prisma } from "@/lib/prisma"

export async function POST(req: Request) {
  const session = await auth()
  if (!session?.user?.id) {
    return NextResponse.json(
      { error: "Please sign in to accept the invitation" },
      { status: 401 }
    )
  }

  const body = await req.json().catch(() => null) as { token?: string } | null
  const token = body?.token
  if (!token || typeof token !== "string") {
    return NextResponse.json({ error: "Invalid token" }, { status: 400 })
  }

  const invite = await prisma.orgInvite.findUnique({
    where: { token },
    include: { organization: true },
  })

  if (!invite) {
    return NextResponse.json({ error: "Invite not found" }, { status: 404 })
  }

  if (invite.accepted) {
    return NextResponse.json({ error: "This invite was already used" }, { status: 400 })
  }

  if (invite.expires < new Date()) {
    return NextResponse.json({ error: "This invite has expired" }, { status: 400 })
  }

  const user = await prisma.user.findUnique({
    where: { id: session.user.id },
  })

  if (!user?.email) {
    return NextResponse.json({ error: "Your account has no email" }, { status: 400 })
  }

  if (user.email.toLowerCase() !== invite.email.toLowerCase()) {
    return NextResponse.json(
      { error: "Sign in with the email address that received this invite" },
      { status: 403 }
    )
  }

  if (user.organizationId && user.organizationId !== invite.organizationId) {
    return NextResponse.json(
      { error: "You already belong to another organization" },
      { status: 400 }
    )
  }

  if (user.organizationId === invite.organizationId) {
    await prisma.orgInvite.update({
      where: { id: invite.id },
      data: { accepted: true },
    })
    return NextResponse.json({
      success: true,
      organizationId: invite.organizationId,
      organizationName: invite.organization.name,
    })
  }

  await prisma.$transaction([
    prisma.user.update({
      where: { id: user.id },
      data: {
        organizationId: invite.organizationId,
        orgRole: invite.role,
      },
    }),
    prisma.orgInvite.update({
      where: { id: invite.id },
      data: { accepted: true },
    }),
  ])

  return NextResponse.json({
    success: true,
    organizationId: invite.organizationId,
    organizationName: invite.organization.name,
  })
}
