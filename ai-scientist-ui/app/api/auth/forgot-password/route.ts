// app/api/auth/forgot-password/route.ts
import { NextResponse } from "next/server"
import { prisma } from "@/lib/prisma"
import { sendPasswordResetEmail } from "../../../../lib/email"
import crypto from "crypto"

export async function POST(req: Request) {
  const { email } = await req.json()

  const user = await prisma.user.findUnique({ where: { email } })

  // Always return success to prevent email enumeration
  if (!user || !user.password) {
    return NextResponse.json({ success: true })
  }

  const token = crypto.randomBytes(32).toString("hex")

  await prisma.passwordReset.create({
    data: {
      userId:  user.id,
      token,
      expires: new Date(Date.now() + 60 * 60 * 1000), // 1h
    }
  })

  await sendPasswordResetEmail(email, user.name ?? "there", token)

  return NextResponse.json({ success: true })
}