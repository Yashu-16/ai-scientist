// app/api/auth/reset-password/route.ts
import { NextResponse } from "next/server"
import bcrypt from "bcryptjs"
import { prisma } from "@/lib/prisma"

export async function POST(req: Request) {
  const { token, password } = await req.json()

  const reset = await prisma.passwordReset.findUnique({ where: { token } })

  if (!reset || reset.used || reset.expires < new Date()) {
    return NextResponse.json({ error: "Invalid or expired reset link" }, { status: 400 })
  }

  const hashed = await bcrypt.hash(password, 12)

  await prisma.user.update({
    where: { id: reset.userId },
    data:  { password: hashed }
  })

  await prisma.passwordReset.update({
    where: { id: reset.id },
    data:  { used: true }
  })

  return NextResponse.json({ success: true })
}