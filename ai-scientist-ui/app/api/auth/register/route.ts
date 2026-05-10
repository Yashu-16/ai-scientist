// app/api/auth/register/route.ts
import { NextResponse } from "next/server"
import bcrypt from "bcryptjs"
import { prisma } from "@/lib/prisma"
import { sendVerificationEmail } from "@/lib/email"
import crypto from "crypto"

export async function POST(req: Request) {
  try {
    const { name, email, password } = await req.json()

    if (!name || !email || !password) {
      return NextResponse.json({ error: "All fields required" }, { status: 400 })
    }

    if (password.length < 8) {
      return NextResponse.json({ error: "Password must be at least 8 characters" }, { status: 400 })
    }

    const existing = await prisma.user.findUnique({ where: { email } })
    if (existing) {
      return NextResponse.json({ error: "Email already registered" }, { status: 400 })
    }

    const hashed = await bcrypt.hash(password, 12)

    const isDev = process.env.NODE_ENV === "development"

    // In dev: auto-verify. In prod: require email verification
    // Auto-verify users until custom domain is configured in Resend
// Once causyn.ai domain is verified, re-enable email verification
  const user = await prisma.user.create({
    data: {
      name,
      email,
      password: hashed,
      emailVerified: new Date(), // auto-verify for now
    }
  })

  // Try to send welcome email (non-blocking — won't fail registration if email fails)
  try {
    const token = crypto.randomBytes(32).toString("hex")
    await prisma.verificationToken.create({
      data: {
        identifier: email,
        token,
        expires: new Date(Date.now() + 24 * 60 * 60 * 1000),
      }
    })
    await sendVerificationEmail(email, name, token)
  } catch (emailError) {
    console.error("Welcome email failed (non-blocking):", emailError)
  }

  return NextResponse.json({
    success: true,
    message: "Account created. You can now sign in.",
  })

  } catch (error) {
    console.error("Register error:", error)
    return NextResponse.json({ error: "Registration failed" }, { status: 500 })
  }
}