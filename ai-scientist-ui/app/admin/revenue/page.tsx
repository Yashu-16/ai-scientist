"use client"
import { useEffect, useState } from "react"
import { Loader2, CreditCard } from "lucide-react"
import { getPlan, PlanId } from "@/lib/plans"

export default function AdminRevenue() {
  const [data, setData]       = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch("/api/admin/revenue")
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false) })
  }, [])

  if (loading) return (
    <div className="flex justify-center py-16">
      <Loader2 className="h-7 w-7 animate-spin text-blue-500" />
    </div>
  )

  return (
    <div className="space-y-5">
      <h1 className="text-xl font-bold text-white">Revenue</h1>

      {/* Monthly breakdown */}
      {data?.monthly && Object.keys(data.monthly).length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-white mb-4">Monthly Revenue (INR)</h3>
          <div className="space-y-3">
            {Object.entries(data.monthly)
              .sort((a, b) => b[0].localeCompare(a[0]))
              .map(([month, amount]) => {
                const max = Math.max(...Object.values(data.monthly) as number[])
                const pct = max > 0 ? Math.round(((amount as number) / max) * 100) : 0
                return (
                  <div key={month} className="flex items-center gap-4">
                    <p className="text-xs text-gray-400 w-24 flex-shrink-0">{month}</p>
                    <div className="flex-1 bg-gray-800 rounded-full h-2">
                      <div className="bg-emerald-500 h-2 rounded-full"
                        style={{ width: `${pct}%` }} />
                    </div>
                    <p className="text-xs font-semibold text-emerald-400 w-24 text-right">
                      ₹{(amount as number).toLocaleString("en-IN")}
                    </p>
                  </div>
                )
              })}
          </div>
        </div>
      )}

      {/* Payments table */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-800">
          <h3 className="text-sm font-semibold text-white flex items-center gap-2">
            <CreditCard className="h-4 w-4 text-gray-400" />
            Payment History ({data?.payments?.length ?? 0})
          </h3>
        </div>
        <div className="divide-y divide-gray-800">
          {data?.payments?.length === 0 ? (
            <p className="text-center py-10 text-sm text-gray-500">No payments yet</p>
          ) : data?.payments?.map((p: any) => (
            <div key={p.id} className="px-5 py-3.5 flex items-center justify-between">
              <div className="flex items-center gap-3 min-w-0">
                <div className="h-8 w-8 rounded-full bg-gray-800 flex items-center justify-center flex-shrink-0">
                  <CreditCard className="h-4 w-4 text-gray-400" />
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-medium text-white">
                    {p.user?.name}
                    <span className="ml-2 text-xs text-gray-500">{p.user?.email}</span>
                  </p>
                  <p className="text-xs text-gray-500">
                    {getPlan(p.plan as PlanId).name} Plan ·{" "}
                    {new Date(p.createdAt).toLocaleDateString("en-IN", {
                      day:"numeric", month:"short", year:"numeric"
                    })}
                  </p>
                </div>
              </div>
              <div className="text-right flex-shrink-0">
                <p className="text-sm font-bold text-emerald-400">
                  ₹{(p.amount / 100).toLocaleString("en-IN")}
                </p>
                <span className="text-[10px] bg-emerald-900/30 text-emerald-400 px-2 py-0.5 rounded-full">
                  Captured
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}