import { NextResponse } from "next/server"
import { auth } from "@/auth"
import { prisma } from "@/lib/prisma"
import { sendOrgInviteEmail } from "@/lib/email"
import crypto from "crypto"

export async function POST(req: Request) {
  const session = await auth()
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const { email, role } = await req.json()

  if (!email) {
    return NextResponse.json({ error: "Email required" }, { status: 400 })
  }

  // Get user and org
  const user = await prisma.user.findUnique({
    where: { id: session.user.id },
    include: { organization: true }
  })

  if (!user?.organization) {
    return NextResponse.json({ error: "You don't belong to an organization" }, { status: 400 })
  }

  // Only owners and admins can invite
  if (!["OWNER", "ADMIN"].includes(user.orgRole ?? "")) {
    return NextResponse.json({ error: "Only admins can invite members" }, { status: 403 })
  }

  // Check if already a member
  const existing = await prisma.user.findFirst({
    where: { email, organizationId: user.organizationId! }
  })
  if (existing) {
    return NextResponse.json({ error: "User is already a member" }, { status: 400 })
  }

  // Check for existing pending invite
  const existingInvite = await prisma.orgInvite.findFirst({
    where: {
      email,
      organizationId: user.organizationId!,
      accepted: false,
      expires: { gt: new Date() }
    }
  })
  if (existingInvite) {
    return NextResponse.json({ error: "Invite already sent to this email" }, { status: 400 })
  }

  // Create invite token
  const token = crypto.randomBytes(32).toString("hex")

  await prisma.orgInvite.create({
    data: {
      email,
      role: role ?? "MEMBER",
      token,
      expires: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000), // 7 days
      organizationId: user.organizationId!,
    }
  })

  await sendOrgInviteEmail(
    email,
    user.organization.name,
    user.name ?? "A teammate",
    role ?? "Member",
    token
  )

  return NextResponse.json({ success: true, message: `Invite sent to ${email}` })
}