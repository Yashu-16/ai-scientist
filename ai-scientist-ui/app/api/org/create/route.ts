import { NextResponse } from "next/server"
import { auth } from "@/auth"
import { prisma } from "@/lib/prisma"

export async function POST(req: Request) {
  const session = await auth()
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const { name, billingEmail } = await req.json()

  if (!name?.trim()) {
    return NextResponse.json({ error: "Organization name required" }, { status: 400 })
  }

  // Check user doesn't already have an org
  const user = await prisma.user.findUnique({
    where: { id: session.user.id }
  })

  if (user?.organizationId) {
    return NextResponse.json({ error: "You already belong to an organization" }, { status: 400 })
  }

  // Generate unique slug
  const baseSlug = name.toLowerCase().replace(/[^a-z0-9]/g, "-").replace(/-+/g, "-").slice(0, 40)
  let slug = baseSlug
  let counter = 1
  while (await prisma.organization.findUnique({ where: { slug } })) {
    slug = `${baseSlug}-${counter++}`
  }

  // Create org and set user as owner
  const org = await prisma.organization.create({
    data: {
      name: name.trim(),
      slug,
      billingEmail: billingEmail || user?.email || "",
      plan: "FREE",
      analysesLimit: 10,
    }
  })

  // Add user as owner
  await prisma.user.update({
    where: { id: session.user.id },
    data: {
      organizationId: org.id,
      orgRole: "OWNER",
    }
  })

  return NextResponse.json({ success: true, org })
}