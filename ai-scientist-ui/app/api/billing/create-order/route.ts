// app/api/billing/create-order/route.ts
import { NextResponse } from "next/server"
import { auth } from "@/auth"
import { prisma } from "@/lib/prisma"
import { PLANS, PlanId } from "@/lib/plans"

export async function POST(req: Request) {
  const session = await auth()
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 })
  }

  // Initialize Razorpay lazily inside the function
  const Razorpay = (await import("razorpay")).default
  const razorpay = new Razorpay({
    key_id:     process.env.RAZORPAY_KEY_ID!,
    key_secret: process.env.RAZORPAY_KEY_SECRET!,
  })

  const { planId } = await req.json()
  const plan = PLANS.find(p => p.id === planId)

  if (!plan || plan.price === 0) {
    return NextResponse.json({ error: "Invalid plan" }, { status: 400 })
  }

  const user = await prisma.user.findUnique({
    where: { id: session.user.id }
  })

  const order = await razorpay.orders.create({
    amount:   plan.priceInPaise,
    currency: "INR",
    receipt:  `rcpt_${Date.now()}`,
    notes: {
      userId: session.user.id,
      planId: plan.id,
      email:  user?.email ?? "",
    },
  })

  await prisma.payment.create({
    data: {
      userId:          session.user.id,
      razorpayOrderId: order.id,
      amount:          plan.priceInPaise,
      currency:        "INR",
      plan:            plan.id as PlanId,
      status:          "PENDING",
    }
  })

  return NextResponse.json({
    orderId:   order.id,
    amount:    plan.priceInPaise,
    currency:  "INR",
    planId:    plan.id,
    planName:  plan.name,
    keyId:     process.env.RAZORPAY_KEY_ID,
    userEmail: user?.email ?? "",
    userName:  user?.name  ?? "",
  })
}