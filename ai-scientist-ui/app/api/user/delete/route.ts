// app/api/user/delete/route.ts
import { NextResponse } from "next/server"
import bcrypt from "bcryptjs"
import { auth } from "@/auth"
import { prisma } from "@/lib/prisma"

export async function DELETE(req: Request) {
  const session = await auth()
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const { password, confirmation } = await req.json()

  if (confirmation !== "DELETE MY ACCOUNT") {
    return NextResponse.json(
      { error: "Please type DELETE MY ACCOUNT to confirm" },
      { status: 400 }
    )
  }

  const user = await prisma.user.findUnique({
    where: { id: session.user.id }
  })

  // Verify password if credentials user
  if (user?.password) {
    if (!password) {
      return NextResponse.json({ error: "Password required" }, { status: 400 })
    }
    const valid = await bcrypt.compare(password, user.password)
    if (!valid) {
      return NextResponse.json({ error: "Incorrect password" }, { status: 400 })
    }
  }

  // Cannot delete if org owner
  if (user?.orgRole === "OWNER") {
    return NextResponse.json(
      { error: "Transfer organization ownership before deleting your account" },
      { status: 400 }
    )
  }

  // Delete user (cascades to analyses, sessions, accounts)
  await prisma.user.delete({
    where: { id: session.user.id }
  })

  return NextResponse.json({ success: true })
}