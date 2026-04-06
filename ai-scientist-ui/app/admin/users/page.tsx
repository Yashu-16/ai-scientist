"use client"
import { useEffect, useState, useCallback } from "react"
import {
  Search, Loader2, ChevronLeft, ChevronRight,
  Trash2, Shield, UserCheck, RefreshCw
} from "lucide-react"

const PLAN_COLOR: Record<string, string> = {
  FREE:       "bg-gray-800 text-gray-300",
  ACADEMIC:   "bg-blue-900 text-blue-300",
  PRO:        "bg-purple-900 text-purple-300",
  ENTERPRISE: "bg-amber-900 text-amber-300",
}

export default function AdminUsers() {
  const [users, setUsers]     = useState<any[]>([])
  const [total, setTotal]     = useState(0)
  const [pages, setPages]     = useState(1)
  const [page, setPage]       = useState(1)
  const [loading, setLoading] = useState(true)
  const [search, setSearch]   = useState("")
  const [plan, setPlan]       = useState("")
  const [updating, setUpdating] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    const params = new URLSearchParams({
      page: String(page), limit: "20"
    })
    if (search) params.set("search", search)
    if (plan)   params.set("plan",   plan)

    const res  = await fetch(`/api/admin/users?${params}`)
    const data = await res.json()
    setUsers(data.users ?? [])
    setTotal(data.total ?? 0)
    setPages(data.pages ?? 1)
    setLoading(false)
  }, [page, search, plan])

  useEffect(() => { load() }, [load])

  async function updateUser(id: string, updates: any) {
    setUpdating(id)
    await fetch(`/api/admin/users/${id}`, {
      method:  "PATCH",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify(updates),
    })
    setUpdating(null)
    load()
  }

  async function deleteUser(id: string, name: string) {
    if (!confirm(`Delete user "${name}"? This cannot be undone.`)) return
    await fetch(`/api/admin/users/${id}`, { method: "DELETE" })
    load()
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Users</h1>
          <p className="text-sm text-gray-500 mt-0.5">{total} total users</p>
        </div>
        <button onClick={load}
          className="p-2 border border-gray-700 rounded-lg hover:bg-gray-800 transition-colors">
          <RefreshCw className="h-4 w-4 text-gray-400" />
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-500" />
          <input
            type="text" value={search}
            onChange={e => { setSearch(e.target.value); setPage(1) }}
            placeholder="Search by name or email..."
            className="w-full pl-9 pr-4 py-2.5 bg-gray-900 border border-gray-700 rounded-xl text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <select value={plan} onChange={e => { setPlan(e.target.value); setPage(1) }}
          className="px-3 py-2.5 bg-gray-900 border border-gray-700 rounded-xl text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500">
          <option value="">All Plans</option>
          {["FREE","ACADEMIC","PRO","ENTERPRISE"].map(p => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>
      </div>

      {/* Table */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        {loading ? (
          <div className="flex justify-center py-16">
            <Loader2 className="h-7 w-7 animate-spin text-blue-500" />
          </div>
        ) : (
          <>
            <div className="grid grid-cols-12 gap-3 px-5 py-3 bg-gray-800 text-xs font-semibold text-gray-400 uppercase tracking-wide">
              <div className="col-span-4">User</div>
              <div className="col-span-2">Plan</div>
              <div className="col-span-2">Usage</div>
              <div className="col-span-2">Analyses</div>
              <div className="col-span-1">Role</div>
              <div className="col-span-1"></div>
            </div>
            <div className="divide-y divide-gray-800">
              {users.map(user => (
                <div key={user.id} className="grid grid-cols-12 gap-3 px-5 py-3.5 items-center hover:bg-gray-800/50 transition-colors">
                  <div className="col-span-4 flex items-center gap-3 min-w-0">
                    <div className="h-8 w-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
                      {user.name?.[0]?.toUpperCase() ?? "?"}
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-white truncate">{user.name}</p>
                      <p className="text-xs text-gray-500 truncate">{user.email}</p>
                    </div>
                  </div>

                  <div className="col-span-2">
                    <select
                      value={user.plan}
                      onChange={e => updateUser(user.id, { plan: e.target.value })}
                      disabled={updating === user.id}
                      className="text-xs bg-gray-800 border border-gray-700 text-white rounded-lg px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    >
                      {["FREE","ACADEMIC","PRO","ENTERPRISE"].map(p => (
                        <option key={p} value={p}>{p}</option>
                      ))}
                    </select>
                  </div>

                  <div className="col-span-2">
                    <p className="text-xs text-gray-300">
                      {user.analysesUsed} / {user.analysesLimit === 999999 ? "∞" : user.analysesLimit}
                    </p>
                    <div className="mt-1 bg-gray-800 rounded-full h-1">
                      <div className="bg-blue-500 h-1 rounded-full"
                        style={{ width: `${Math.min((user.analysesUsed / (user.analysesLimit || 1)) * 100, 100)}%` }} />
                    </div>
                  </div>

                  <div className="col-span-2">
                    <p className="text-xs text-gray-300">{user._count?.analyses ?? 0} total</p>
                    {user.organization && (
                      <p className="text-[10px] text-gray-500 truncate">🏢 {user.organization.name}</p>
                    )}
                  </div>

                  <div className="col-span-1">
                    <select
                      value={user.role}
                      onChange={e => updateUser(user.id, { role: e.target.value })}
                      disabled={updating === user.id}
                      className="text-xs bg-gray-800 border border-gray-700 text-white rounded-lg px-2 py-1 focus:outline-none"
                    >
                      <option value="USER">User</option>
                      <option value="ADMIN">Admin</option>
                    </select>
                  </div>

                  <div className="col-span-1 flex justify-end">
                    {updating === user.id ? (
                      <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
                    ) : (
                      <button
                        onClick={() => deleteUser(user.id, user.name)}
                        className="p-1.5 text-gray-600 hover:text-red-400 hover:bg-red-900/20 rounded-lg transition-colors"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>

      {/* Pagination */}
      {pages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-500">
            Page {page} of {pages} · {total} users
          </p>
          <div className="flex gap-2">
            <button onClick={() => setPage(p => Math.max(1, p-1))} disabled={page === 1}
              className="p-2 border border-gray-700 rounded-lg hover:bg-gray-800 disabled:opacity-40 transition-colors">
              <ChevronLeft className="h-4 w-4 text-gray-400" />
            </button>
            <button onClick={() => setPage(p => Math.min(pages, p+1))} disabled={page === pages}
              className="p-2 border border-gray-700 rounded-lg hover:bg-gray-800 disabled:opacity-40 transition-colors">
              <ChevronRight className="h-4 w-4 text-gray-400" />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}