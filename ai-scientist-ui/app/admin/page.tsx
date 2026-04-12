"use client"
import { useEffect, useState } from "react"
import {
  Users, FlaskConical, Building2,
  CreditCard, TrendingUp, TrendingDown,
  Loader2, Activity
} from "lucide-react"
import Link from "next/link"

const DEC_COLOR: Record<string, string> = {
  "GO":          "text-emerald-400 bg-emerald-900/30",
  "NO-GO":       "text-red-400 bg-red-900/30",
  "INVESTIGATE": "text-amber-400 bg-amber-900/30",
}

const PLAN_COLOR: Record<string, string> = {
  FREE:       "bg-gray-700 text-gray-300",
  ACADEMIC:   "bg-blue-900 text-blue-300",
  PRO:        "bg-purple-900 text-purple-300",
  ENTERPRISE: "bg-amber-900 text-amber-300",
}

export default function AdminOverview() {
  const [data, setData]     = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch("/api/admin/stats")
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
    </div>
  )

  if (!data) return null

  return (
    <div className="space-y-6">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Overview</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {new Date().toLocaleDateString("en-US", {
              weekday:"long", day:"numeric", month:"long", year:"numeric"
            })}
          </p>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-xs text-gray-400">Live</span>
        </div>
      </div>

      {/* Metric cards */}
      <div className="grid grid-cols-4 gap-4">
        {[
          {
            label:  "Total Users",
            value:  data.users.total,
            sub:    `+${data.users.newToday} today`,
            icon:   Users,
            color:  "text-blue-400",
            bg:     "bg-blue-900/20 border-blue-800/50",
            href:   "/admin/users",
          },
          {
            label:  "Total Analyses",
            value:  data.analyses.total,
            sub:    `${data.analyses.today} today`,
            icon:   FlaskConical,
            color:  "text-purple-400",
            bg:     "bg-purple-900/20 border-purple-800/50",
            href:   "/admin/analyses",
          },
          {
            label:  "Organizations",
            value:  data.orgs.total,
            sub:    "active orgs",
            icon:   Building2,
            color:  "text-amber-400",
            bg:     "bg-amber-900/20 border-amber-800/50",
            href:   "/admin/orgs",
          },
          {
            label:  "MRR",
            value:  `$${(data.revenue.mrr / 100).toFixed(2)}`,
            sub:    data.revenue.growth >= 0
              ? `+${data.revenue.growth}% vs last month`
              : `${data.revenue.growth}% vs last month`,
            icon:   CreditCard,
            color:  "text-emerald-400",
            bg:     "bg-emerald-900/20 border-emerald-800/50",
            href:   "/admin/revenue",
            growth: data.revenue.growth,
          },
        ].map(({ label, value, sub, icon: Icon, color, bg, href, growth }) => (
          <Link
            key={label}
            href={href}
            className={`border rounded-xl p-5 hover:brightness-110 transition-all ${bg}`}
          >
            <div className="flex items-center justify-between mb-3">
              <p className="text-xs text-gray-400 uppercase tracking-wide">{label}</p>
              <Icon className={`h-4 w-4 ${color}`} />
            </div>
            <p className={`text-2xl font-black ${color}`}>{value}</p>
            <div className="flex items-center gap-1 mt-1">
              {growth !== undefined && (
                growth >= 0
                  ? <TrendingUp  className="h-3 w-3 text-emerald-400" />
                  : <TrendingDown className="h-3 w-3 text-red-400" />
              )}
              <p className="text-xs text-gray-500">{sub}</p>
            </div>
          </Link>
        ))}
      </div>

      {/* Plan breakdown */}
      <div className="grid grid-cols-2 gap-5">
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <Activity className="h-4 w-4 text-gray-400" />
            Users by Plan
          </h3>
          <div className="space-y-3">
            {data.planCounts.map((p: any) => {
              const pct = data.users.total > 0
                ? Math.round((p._count.plan / data.users.total) * 100)
                : 0
              return (
                <div key={p.plan}>
                  <div className="flex items-center justify-between mb-1">
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${PLAN_COLOR[p.plan] ?? "bg-gray-700 text-gray-300"}`}>
                      {p.plan}
                    </span>
                    <span className="text-xs text-gray-400">
                      {p._count.plan} users · {pct}%
                    </span>
                  </div>
                  <div className="bg-gray-800 rounded-full h-1.5">
                    <div
                      className="bg-blue-500 h-1.5 rounded-full transition-all"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </div>

        {/* Revenue stats */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-white mb-4 flex items-center gap-2">
            <CreditCard className="h-4 w-4 text-gray-400" />
            Revenue Summary
          </h3>
          <div className="space-y-3">
            {[
              { label:"This Month",  value:`$${(data.revenue.mrr / 100).toFixed(2)}`,       color:"text-emerald-400" },
              { label:"Last Month",  value:`$${(data.revenue.lastMonth / 100).toFixed(2)}`,  color:"text-gray-300"   },
              { label:"Total Revenue", value:`$${(data.revenue.total / 100).toFixed(2)}`,   color:"text-white"      },
              { label:"MoM Growth",  value:`${data.revenue.growth >= 0 ? "+" : ""}${data.revenue.growth}%`, color: data.revenue.growth >= 0 ? "text-emerald-400" : "text-red-400" },
            ].map(({ label, value, color }) => (
              <div key={label} className="flex items-center justify-between py-2 border-b border-gray-800 last:border-0">
                <span className="text-xs text-gray-400">{label}</span>
                <span className={`text-sm font-bold ${color}`}>{value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent activity */}
      <div className="grid grid-cols-2 gap-5">

        {/* Recent users */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-800 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">Recent Users</h3>
            <Link href="/admin/users" className="text-xs text-blue-400 hover:text-blue-300">
              View all →
            </Link>
          </div>
          <div className="divide-y divide-gray-800">
            {data.recentUsers.map((user: any) => (
              <div key={user.id} className="px-5 py-3 flex items-center justify-between">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="h-7 w-7 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
                    {user.name?.[0]?.toUpperCase() ?? "?"}
                  </div>
                  <div className="min-w-0">
                    <p className="text-xs font-medium text-white truncate">{user.name}</p>
                    <p className="text-[10px] text-gray-500 truncate">{user.email}</p>
                  </div>
                </div>
                <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium flex-shrink-0 ${PLAN_COLOR[user.plan] ?? "bg-gray-700 text-gray-300"}`}>
                  {user.plan}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Recent analyses */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-800 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-white">Recent Analyses</h3>
            <Link href="/admin/analyses" className="text-xs text-blue-400 hover:text-blue-300">
              View all →
            </Link>
          </div>
          <div className="divide-y divide-gray-800">
            {data.recentAnalyses.map((a: any) => (
              <div key={a.id} className="px-5 py-3 flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <p className="text-xs font-medium text-white truncate">{a.diseaseName}</p>
                  <p className="text-[10px] text-gray-500 truncate">by {a.user?.name}</p>
                </div>
                {a.decision && (
                  <span className={`text-[10px] px-2 py-0.5 rounded-full font-semibold flex-shrink-0 ${DEC_COLOR[a.decision] ?? "text-gray-400 bg-gray-800"}`}>
                    {a.decision}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}