"use client"
import { useEffect, useState } from "react"
import { useSearchParams } from "next/navigation"
import { CheckCircle, CreditCard, Loader2, TrendingUp } from "lucide-react"
import { getPlan, PLANS, PlanId } from "@/lib/plans"
import Link from "next/link"
import { Suspense } from "react"

function BillingContent() {
  const params  = useSearchParams()
  const success = params.get("success")

  const [data, setData]     = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch("/api/billing/history")
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="flex justify-center py-16">
      <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
    </div>
  )

  const currentPlan = getPlan((data?.user?.plan ?? "FREE") as PlanId)
  const usagePct    = data?.user
    ? Math.min(Math.round((data.user.analysesUsed / data.user.analysesLimit) * 100), 100)
    : 0

  return (
    <div className="max-w-3xl mx-auto space-y-6">

      {/* Success banner */}
      {success && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl px-5 py-4 flex items-center gap-3">
          <CheckCircle className="h-6 w-6 text-emerald-500 flex-shrink-0" />
          <div>
            <p className="text-sm font-bold text-emerald-800">Payment successful!</p>
            <p className="text-xs text-emerald-600 mt-0.5">
              Your plan has been upgraded. All features are now active.
            </p>
          </div>
        </div>
      )}

      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Billing & Plan</h1>
          <p className="text-sm text-gray-500 mt-0.5">Manage your subscription and payment history</p>
        </div>
        <Link href="/pricing"
          className="flex items-center gap-1.5 text-sm bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-blue-700 transition-colors">
          <TrendingUp className="h-4 w-4" />
          Upgrade Plan
        </Link>
      </div>

      {/* Current plan */}
      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <h3 className="text-sm font-semibold text-gray-900 mb-4">Current Plan</h3>
        <div className="flex items-center justify-between mb-4">
          <div>
            <p className="text-2xl font-black text-gray-900">{currentPlan.name}</p>
            <p className="text-sm text-gray-500 mt-0.5">
              {currentPlan.price === 0
                ? "Free forever"
                : `₹${currentPlan.price.toLocaleString("en-IN")}/month`}
            </p>
          </div>
          <span className={`text-sm font-bold px-4 py-2 rounded-xl ${
            currentPlan.id === "FREE"
              ? "bg-gray-100 text-gray-600"
              : "bg-blue-50 text-blue-700 ring-1 ring-blue-200"
          }`}>
            {currentPlan.id === "FREE" ? "Free" : "Active"}
          </span>
        </div>

        {/* Usage */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <p className="text-xs text-gray-500">Analyses used this month</p>
            <p className="text-xs font-semibold text-gray-700">
              {data?.user?.analysesUsed ?? 0} / {data?.user?.analysesLimit === 999999 ? "∞" : data?.user?.analysesLimit ?? 3}
            </p>
          </div>
          <div className="bg-gray-100 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all ${
                usagePct >= 90 ? "bg-red-500" :
                usagePct >= 70 ? "bg-amber-500" : "bg-blue-500"
              }`}
              style={{ width: `${usagePct}%` }}
            />
          </div>
          {usagePct >= 80 && (
            <p className="text-xs text-amber-600 mt-1">
              Running low —{" "}
              <Link href="/pricing" className="underline font-medium">upgrade for more</Link>
            </p>
          )}
        </div>

        {/* Subscription details */}
        {data?.subscription && (
          <div className="mt-4 pt-4 border-t border-gray-100 grid grid-cols-2 gap-3">
            <div>
              <p className="text-xs text-gray-400">Period start</p>
              <p className="text-sm font-medium text-gray-800">
                {new Date(data.subscription.currentPeriodStart).toLocaleDateString("en-IN")}
              </p>
            </div>
            <div>
              <p className="text-xs text-gray-400">Next renewal</p>
              <p className="text-sm font-medium text-gray-800">
                {data.subscription.currentPeriodEnd
                  ? new Date(data.subscription.currentPeriodEnd).toLocaleDateString("en-IN")
                  : "—"}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Payment history */}
      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-100 flex items-center gap-2">
          <CreditCard className="h-4 w-4 text-gray-400" />
          <h3 className="text-sm font-semibold text-gray-900">Payment History</h3>
        </div>

        {!data?.payments?.length ? (
          <div className="text-center py-10">
            <p className="text-sm text-gray-400">No payments yet</p>
            <Link href="/pricing" className="text-xs text-blue-500 hover:text-blue-700 mt-1 block">
              View plans →
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-gray-50">
            {data.payments.map((p: any) => (
              <div key={p.id} className="px-6 py-4 flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-900">
                    {getPlan(p.plan as PlanId).name} Plan
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {new Date(p.createdAt).toLocaleDateString("en-IN", {
                      day:"numeric", month:"long", year:"numeric"
                    })}
                    {p.razorpayPaymentId && (
                      <span className="ml-2 font-mono">{p.razorpayPaymentId.slice(0,16)}...</span>
                    )}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-gray-900">
                    ₹{(p.amount / 100).toLocaleString("en-IN")}
                  </p>
                  <span className="text-xs bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded-full font-medium">
                    Paid
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Compare plans */}
      <div className="text-center py-2">
        <p className="text-sm text-gray-500">
          Need more?{" "}
          <Link href="/pricing" className="text-blue-600 font-medium hover:text-blue-800">
            Compare all plans →
          </Link>
        </p>
      </div>
    </div>
  )
}

export default function BillingPage() {
  return <Suspense><BillingContent /></Suspense>
}