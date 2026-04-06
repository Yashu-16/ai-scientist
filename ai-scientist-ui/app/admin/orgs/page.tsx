"use client"
import { useEffect, useState } from "react"
import { Loader2, Building2, Users } from "lucide-react"

const PLAN_COLOR: Record<string, string> = {
  FREE:       "bg-gray-800 text-gray-300",
  ACADEMIC:   "bg-blue-900 text-blue-300",
  PRO:        "bg-purple-900 text-purple-300",
  ENTERPRISE: "bg-amber-900 text-amber-300",
}

export default function AdminOrgs() {
  const [orgs, setOrgs]       = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch("/api/admin/orgs")
      .then(r => r.json())
      .then(d => { setOrgs(d.orgs ?? []); setLoading(false) })
  }, [])

  if (loading) return (
    <div className="flex justify-center py-16">
      <Loader2 className="h-7 w-7 animate-spin text-blue-500" />
    </div>
  )

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-bold text-white">Organizations</h1>
        <p className="text-sm text-gray-500 mt-0.5">{orgs.length} total organizations</p>
      </div>

      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <div className="grid grid-cols-12 gap-3 px-5 py-3 bg-gray-800 text-xs font-semibold text-gray-400 uppercase tracking-wide">
          <div className="col-span-4">Organization</div>
          <div className="col-span-2">Plan</div>
          <div className="col-span-2">Members</div>
          <div className="col-span-2">Analyses</div>
          <div className="col-span-2">Usage</div>
        </div>
        <div className="divide-y divide-gray-800">
          {orgs.length === 0 ? (
            <p className="text-center py-10 text-sm text-gray-500">No organizations yet</p>
          ) : orgs.map(org => {
            const usagePct = Math.min(
              Math.round((org.analysesUsed / (org.analysesLimit || 1)) * 100),
              100
            )
            return (
              <div key={org.id} className="grid grid-cols-12 gap-3 px-5 py-4 items-center hover:bg-gray-800/50 transition-colors">
                <div className="col-span-4 flex items-center gap-3 min-w-0">
                  <div className="h-9 w-9 rounded-xl bg-blue-900/40 flex items-center justify-center flex-shrink-0">
                    <Building2 className="h-4 w-4 text-blue-400" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-white truncate">{org.name}</p>
                    <p className="text-xs text-gray-500">{org.slug}</p>
                  </div>
                </div>
                <div className="col-span-2">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${PLAN_COLOR[org.plan]}`}>
                    {org.plan}
                  </span>
                </div>
                <div className="col-span-2 flex items-center gap-1.5">
                  <Users className="h-3.5 w-3.5 text-gray-500" />
                  <span className="text-sm text-gray-300">{org._count?.members ?? 0}</span>
                </div>
                <div className="col-span-2">
                  <span className="text-sm text-gray-300">{org._count?.analyses ?? 0}</span>
                </div>
                <div className="col-span-2">
                  <p className="text-xs text-gray-400 mb-1">
                    {org.analysesUsed}/{org.analysesLimit}
                  </p>
                  <div className="bg-gray-800 rounded-full h-1.5">
                    <div className={`h-1.5 rounded-full ${
                      usagePct >= 90 ? "bg-red-500" :
                      usagePct >= 70 ? "bg-amber-500" : "bg-blue-500"
                    }`} style={{ width:`${usagePct}%` }} />
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}