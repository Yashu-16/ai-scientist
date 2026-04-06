// app/api/billing/webhook/route.ts
// Razorpay webhook handler
import { NextResponse } from "next/server"
import crypto from "crypto"
import { prisma } from "@/lib/prisma"

export async function POST(req: Request) {
  const body      = await req.text()
  const signature = req.headers.get("x-razorpay-signature") ?? ""

  // Verify webhook signature
  const expected = crypto
    .createHmac("sha256", process.env.RAZORPAY_KEY_SECRET!)
    .update(body)
    .digest("hex")

  if (expected !== signature) {
    return NextResponse.json({ error: "Invalid signature" }, { status: 400 })
  }

  const event = JSON.parse(body)

  if (event.event === "payment.captured") {
    const payment = event.payload.payment.entity
    const notes   = payment.notes ?? {}

    if (notes.userId && notes.planId) {
      await prisma.user.update({
        where: { id: notes.userId },
        data: {
          plan:         notes.planId,
          analysesUsed: 0,
        }
      })
    }
  }

  if (event.event === "subscription.cancelled") {
    const sub = event.payload.subscription.entity
    await prisma.subscription.updateMany({
      where: { razorpaySubId: sub.id },
      data:  { status: "CANCELLED" }
    })
  }

  return NextResponse.json({ received: true })
}