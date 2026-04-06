"use client"
import { useState } from "react"
import { useRouter } from "next/navigation"
import { Check, Zap, Building2, GraduationCap, Loader2 } from "lucide-react"
import { PLANS, PlanConfig } from "@/lib/plans"
import Link from "next/link"

declare global {
  interface Window { Razorpay: any }
}

const PLAN_ICONS: Record<string, React.ElementType> = {
  FREE:       Zap,
  ACADEMIC:   GraduationCap,
  PRO:        Zap,
  ENTERPRISE: Building2,
}

export default function PricingPage() {
  const router = useRouter()
  const [loadingPlan, setLoadingPlan] = useState<string | null>(null)
  const [error, setError]             = useState("")

  async function handleUpgrade(plan: PlanConfig) {
    if (plan.id === "FREE") return
    if (plan.id === "ENTERPRISE") {
      window.location.href = "mailto:sales@aiscientist.in?subject=Enterprise Plan Inquiry"
      return
    }

    setLoadingPlan(plan.id)
    setError("")

    try {
      // Load Razorpay script
      await loadRazorpay()

      // Create order
      const res  = await fetch("/api/billing/create-order", {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify({ planId: plan.id }),
      })
      const data = await res.json()

      if (!res.ok) {
        setError(data.error ?? "Failed to create order")
        setLoadingPlan(null)
        return
      }

      // Open Razorpay checkout
      const rzp = new window.Razorpay({
        key:         data.keyId,
        amount:      data.amount,
        currency:    data.currency,
        name:        "AI Scientist",
        description: `${data.planName} Plan — Monthly`,
        order_id:    data.orderId,
        prefill: {
          name:  data.userName,
          email: data.userEmail,
        },
        theme:   { color: "#2563EB" },
        handler: async (response: any) => {
          // Verify payment
          const verifyRes = await fetch("/api/billing/verify", {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({
              razorpay_order_id:   response.razorpay_order_id,
              razorpay_payment_id: response.razorpay_payment_id,
              razorpay_signature:  response.razorpay_signature,
              planId:              plan.id,
            }),
          })

          if (verifyRes.ok) {
            router.push("/billing?success=1")
            router.refresh()
          } else {
            setError("Payment verification failed. Contact support.")
          }
        },
        modal: {
          ondismiss: () => setLoadingPlan(null)
        }
      })

      rzp.open()
    } catch (err) {
      setError("Something went wrong. Please try again.")
      setLoadingPlan(null)
    }
  }

  function loadRazorpay(): Promise<void> {
    return new Promise(resolve => {
      if (window.Razorpay) { resolve(); return }
      const script    = document.createElement("script")
      script.src      = "https://checkout.razorpay.com/v1/checkout.js"
      script.onload   = () => resolve()
      document.body.appendChild(script)
    })
  }

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-black text-gray-900">Simple, transparent pricing</h1>
        <p className="text-gray-500 mt-2 text-base">
          Start free. Upgrade when you need more. Cancel anytime.
        </p>
        <p className="text-xs text-gray-400 mt-1">
          All prices in INR · GST applicable · Secure payments via Razorpay
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl px-5 py-3 text-sm text-red-700 text-center">
          {error}
        </div>
      )}

      {/* Plans grid */}
      <div className="grid grid-cols-4 gap-4">
        {PLANS.map(plan => {
          const Icon = PLAN_ICONS[plan.id] ?? Zap
          const isLoading = loadingPlan === plan.id

          return (
            <div
              key={plan.id}
              className={`relative bg-white rounded-2xl border flex flex-col ${
                plan.highlighted
                  ? "border-blue-500 shadow-lg shadow-blue-100 ring-2 ring-blue-500"
                  : "border-gray-200"
              }`}
            >
              {/* Badge */}
              {plan.badge && (
                <div className={`absolute -top-3 left-1/2 -translate-x-1/2 text-xs font-bold px-3 py-1 rounded-full whitespace-nowrap ${
                  plan.highlighted
                    ? "bg-blue-600 text-white"
                    : "bg-gray-800 text-white"
                }`}>
                  {plan.badge}
                </div>
              )}

              <div className="p-6 flex-1">
                {/* Icon + name */}
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center mb-4 ${
                  plan.highlighted ? "bg-blue-100" : "bg-gray-100"
                }`}>
                  <Icon className={`h-5 w-5 ${plan.highlighted ? "text-blue-600" : "text-gray-500"}`} />
                </div>

                <h3 className="text-base font-bold text-gray-900">{plan.name}</h3>

                {/* Price */}
                <div className="mt-3 mb-5">
                  {plan.price === 0 && plan.id === "FREE" ? (
                    <p className="text-3xl font-black text-gray-900">Free</p>
                  ) : plan.price === 0 ? (
                    <p className="text-3xl font-black text-gray-900">Custom</p>
                  ) : (
                    <div className="flex items-baseline gap-1">
                      <span className="text-xl font-bold text-gray-500">₹</span>
                      <span className="text-3xl font-black text-gray-900">
                        {plan.price.toLocaleString("en-IN")}
                      </span>
                      <span className="text-sm text-gray-400">/mo</span>
                    </div>
                  )}
                </div>

                {/* Features */}
                <ul className="space-y-2">
                  {plan.features.map(f => (
                    <li key={f} className="flex items-start gap-2 text-sm text-gray-600">
                      <Check className={`h-4 w-4 flex-shrink-0 mt-0.5 ${
                        plan.highlighted ? "text-blue-500" : "text-emerald-500"
                      }`} />
                      {f}
                    </li>
                  ))}
                </ul>
              </div>

              {/* CTA */}
              <div className="p-6 pt-0">
                <button
                  onClick={() => handleUpgrade(plan)}
                  disabled={plan.id === "FREE" || isLoading}
                  className={`w-full py-2.5 rounded-xl text-sm font-bold transition-all flex items-center justify-center gap-2 ${
                    plan.id === "FREE"
                      ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                      : plan.highlighted
                      ? "bg-blue-600 text-white hover:bg-blue-700 shadow-md hover:shadow-blue-200"
                      : "bg-gray-900 text-white hover:bg-gray-800"
                  }`}
                >
                  {isLoading && <Loader2 className="h-4 w-4 animate-spin" />}
                  {isLoading ? "Opening..." : plan.cta}
                </button>
              </div>
            </div>
          )
        })}
      </div>

      {/* FAQ */}
      <div className="bg-white border border-gray-200 rounded-2xl p-8">
        <h3 className="text-base font-bold text-gray-900 mb-5">Frequently asked questions</h3>
        <div className="grid grid-cols-2 gap-6">
          {[
            {
              q: "What counts as one analysis?",
              a: "Each time you run the full 9-stage pipeline for a disease. Cached results don't count."
            },
            {
              q: "Can I upgrade or downgrade anytime?",
              a: "Yes. Upgrades take effect immediately. Downgrades apply at the end of your billing period."
            },
            {
              q: "Is my payment secure?",
              a: "All payments are processed by Razorpay — PCI-DSS compliant. We never store card details."
            },
            {
              q: "Do you provide GST invoices?",
              a: "Yes. Pro and Enterprise plans include GST invoices. Enter your GSTIN during checkout."
            },
            {
              q: "What payment methods are accepted?",
              a: "UPI, credit/debit cards, net banking, and wallets via Razorpay."
            },
            {
              q: "Is this for clinical use?",
              a: "No. AI Scientist is for exploratory research only, not clinical decisions."
            },
          ].map(({ q, a }) => (
            <div key={q}>
              <p className="text-sm font-semibold text-gray-900 mb-1">{q}</p>
              <p className="text-sm text-gray-500 leading-relaxed">{a}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Back link */}
      <div className="text-center">
        <Link href="/" className="text-sm text-gray-400 hover:text-gray-600">
          ← Back to dashboard
        </Link>
      </div>
    </div>
  )
}