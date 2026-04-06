// app/api/billing/verify/route.ts
import { NextResponse } from "next/server"
import crypto from "crypto"
import { auth } from "@/auth"
import { prisma } from "@/lib/prisma"
import { PLANS, PlanId } from "@/lib/plans"

export async function POST(req: Request) {
  const session = await auth()
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  const {
    razorpay_order_id,
    razorpay_payment_id,
    razorpay_signature,
    planId,
  } = await req.json()

  // Verify signature
  const body      = `${razorpay_order_id}|${razorpay_payment_id}`
  const expected  = crypto
    .createHmac("sha256", process.env.RAZORPAY_KEY_SECRET!)
    .update(body)
    .digest("hex")

  if (expected !== razorpay_signature) {
    return NextResponse.json({ error: "Invalid payment signature" }, { status: 400 })
  }

  const plan = PLANS.find(p => p.id === planId)
  if (!plan) {
    return NextResponse.json({ error: "Invalid plan" }, { status: 400 })
  }

  // Update payment record
  await prisma.payment.updateMany({
    where: { razorpayOrderId: razorpay_order_id },
    data: {
      razorpayPaymentId: razorpay_payment_id,
      status: "CAPTURED",
    }
  })

  // Upgrade user plan
  const analysesLimit = plan.analysesLimit === -1 ? 999999 : plan.analysesLimit

  await prisma.user.update({
    where: { id: session.user.id },
    data: {
      plan:          plan.id as PlanId,
      analysesLimit: analysesLimit,
      analysesUsed:  0, // reset usage on upgrade
    }
  })

  // Create or update subscription record
  await prisma.subscription.upsert({
    where:  { userId: session.user.id },
    create: {
      userId:            session.user.id,
      razorpayPaymentId: razorpay_payment_id,
      plan:              plan.id as PlanId,
      status:            "ACTIVE",
      currentPeriodStart: new Date(),
      currentPeriodEnd:   new Date(Date.now() + 30 * 24 * 60 * 60 * 1000),
    },
    update: {
      plan:              plan.id as PlanId,
      status:            "ACTIVE",
      currentPeriodStart: new Date(),
      currentPeriodEnd:   new Date(Date.now() + 30 * 24 * 60 * 60 * 1000),
    }
  })

  return NextResponse.json({ success: true, plan: plan.id })
}