"use client"
import { useEffect, useState, useCallback } from "react"
import { Loader2, Search, FlaskConical, ChevronLeft, ChevronRight, RefreshCw } from "lucide-react"

const DEC_COLOR: Record<string, string> = {
  "GO":          "text-emerald-400 bg-emerald-900/30",
  "NO-GO":       "text-red-400 bg-red-900/30",
  "INVESTIGATE": "text-amber-400 bg-amber-900/30",
}

export default function AdminAnalyses() {
  const [analyses, setAnalyses] = useState<any[]>([])
  const [total, setTotal]       = useState(0)
  const [pages, setPages]       = useState(1)
  const [page, setPage]         = useState(1)
  const [loading, setLoading]   = useState(true)
  const [search, setSearch]     = useState("")
  const [decision, setDecision] = useState("")

  const load = useCallback(async () => {
    setLoading(true)
    const params = new URLSearchParams({ page: String(page), limit: "20" })
    if (search)   params.set("search",   search)
    if (decision) params.set("decision", decision)

    const res  = await fetch(`/api/admin/analyses?${params}`)
    const data = await res.json()
    setAnalyses(data.analyses ?? [])
    setTotal(data.total ?? 0)
    setPages(data.pages ?? 1)
    setLoading(false)
  }, [page, search, decision])

  useEffect(() => { load() }, [load])

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Analyses</h1>
          <p className="text-sm text-gray-500 mt-0.5">{total} total analyses</p>
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
          <input type="text" value={search}
            onChange={e => { setSearch(e.target.value); setPage(1) }}
            placeholder="Search by disease..."
            className="w-full pl-9 pr-4 py-2.5 bg-gray-900 border border-gray-700 rounded-xl text-sm text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <select value={decision} onChange={e => { setDecision(e.target.value); setPage(1) }}
          className="px-3 py-2.5 bg-gray-900 border border-gray-700 rounded-xl text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500">
          <option value="">All Decisions</option>
          <option value="GO">GO</option>
          <option value="NO-GO">NO-GO</option>
          <option value="INVESTIGATE">INVESTIGATE</option>
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
              <div className="col-span-4">Disease</div>
              <div className="col-span-2">Decision</div>
              <div className="col-span-2">Confidence</div>
              <div className="col-span-2">User</div>
              <div className="col-span-2">Date</div>
            </div>
            <div className="divide-y divide-gray-800">
              {analyses.length === 0 ? (
                <p className="text-center py-10 text-sm text-gray-500">No analyses found</p>
              ) : analyses.map(a => (
                <div key={a.id} className="grid grid-cols-12 gap-3 px-5 py-3.5 items-center hover:bg-gray-800/50 transition-colors">
                  <div className="col-span-4 flex items-center gap-3 min-w-0">
                    <FlaskConical className="h-4 w-4 text-gray-500 flex-shrink-0" />
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-white truncate">{a.diseaseName}</p>
                      {a.organization && (
                        <p className="text-[10px] text-gray-500">🏢 {a.organization.name}</p>
                      )}
                    </div>
                  </div>
                  <div className="col-span-2">
                    {a.decision ? (
                      <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${DEC_COLOR[a.decision] ?? "text-gray-400 bg-gray-800"}`}>
                        {a.decision}
                      </span>
                    ) : <span className="text-gray-600 text-xs">—</span>}
                  </div>
                  <div className="col-span-2">
                    {a.confidence != null ? (
                      <span className="text-sm font-semibold text-gray-300">
                        {Math.round(a.confidence * 100)}%
                      </span>
                    ) : <span className="text-gray-600 text-xs">—</span>}
                  </div>
                  <div className="col-span-2 min-w-0">
                    <p className="text-xs text-gray-300 truncate">{a.user?.name}</p>
                    <p className="text-[10px] text-gray-500 truncate">{a.user?.email}</p>
                  </div>
                  <div className="col-span-2">
                    <p className="text-xs text-gray-400">
                      {new Date(a.createdAt).toLocaleDateString("en-IN", {
                        day:"numeric", month:"short"
                      })}
                    </p>
                    <p className="text-[10px] text-gray-600">
                      {new Date(a.createdAt).toLocaleTimeString("en-IN", {
                        hour:"2-digit", minute:"2-digit"
                      })}
                    </p>
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
          <p className="text-sm text-gray-500">Page {page} of {pages}</p>
          <div className="flex gap-2">
            <button onClick={() => setPage(p => Math.max(1,p-1))} disabled={page===1}
              className="p-2 border border-gray-700 rounded-lg hover:bg-gray-800 disabled:opacity-40">
              <ChevronLeft className="h-4 w-4 text-gray-400" />
            </button>
            <button onClick={() => setPage(p => Math.min(pages,p+1))} disabled={page===pages}
              className="p-2 border border-gray-700 rounded-lg hover:bg-gray-800 disabled:opacity-40">
              <ChevronRight className="h-4 w-4 text-gray-400" />
            </button>
          </div>
        </div>
      )}
    </div>
  )
}