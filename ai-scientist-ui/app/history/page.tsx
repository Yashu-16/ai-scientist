"use client"
import { useEffect, useState, useCallback } from "react"
import { useRouter } from "next/navigation"
import {
  FlaskConical, Search, Filter, Trash2,
  ChevronLeft, ChevronRight, Loader2,
  RefreshCw, BarChart2, Calendar
} from "lucide-react"
import { saveAnalysis } from "@/lib/store"
import Link from "next/link"

type Analysis = {
  id:          string
  diseaseName: string
  decision:    string | null
  confidence:  number | null
  riskLevel:   string | null
  createdAt:   string
}

type Stats = { decision: string | null; _count: { decision: number } }[]

const DEC_STYLE: Record<string, string> = {
  "GO":          "bg-emerald-50 text-emerald-700 ring-emerald-200",
  "NO-GO":       "bg-red-50 text-red-700 ring-red-200",
  "INVESTIGATE": "bg-amber-50 text-amber-700 ring-amber-200",
}

const RISK_STYLE: Record<string, string> = {
  "High":   "text-red-600",
  "Medium": "text-amber-600",
  "Low":    "text-emerald-600",
}

export default function HistoryPage() {
  const router = useRouter()

  const [analyses, setAnalyses] = useState<Analysis[]>([])
  const [total, setTotal]       = useState(0)
  const [pages, setPages]       = useState(1)
  const [page, setPage]         = useState(1)
  const [stats, setStats]       = useState<Stats>([])
  const [loading, setLoading]   = useState(true)
  const [deleting, setDeleting] = useState<string | null>(null)
  const [reopening, setReopening] = useState<string | null>(null)

  const [search,   setSearch]   = useState("")
  const [decision, setDecision] = useState("")

  const load = useCallback(async () => {
    setLoading(true)
    const params = new URLSearchParams({
      page:  String(page),
      limit: "15",
    })
    if (search)   params.set("search",   search)
    if (decision) params.set("decision", decision)

    const res  = await fetch(`/api/analyses?${params}`)
    const data = await res.json()

    setAnalyses(data.analyses ?? [])
    setTotal(data.total ?? 0)
    setPages(data.pages ?? 1)
    setStats(data.stats ?? [])
    setLoading(false)
  }, [page, search, decision])

  useEffect(() => { load() }, [load])

  // Reopen — load full result and go to hypotheses tab
  async function handleReopen(id: string) {
    setReopening(id)
    try {
      const res  = await fetch(`/api/analyses/${id}`)
      const data = await res.json()
      if (data.analysis?.result) {
        saveAnalysis(data.analysis.result)
        router.push("/hypotheses")
      }
    } catch {}
    setReopening(null)
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this analysis? This cannot be undone.")) return
    setDeleting(id)
    await fetch(`/api/analyses/${id}`, { method: "DELETE" })
    setDeleting(null)
    load()
  }

  // Summary stat cards
  const goCount  = stats.find(s => s.decision === "GO")?._count.decision ?? 0
  const noCount  = stats.find(s => s.decision === "NO-GO")?._count.decision ?? 0
  const invCount = stats.find(s => s.decision === "INVESTIGATE")?._count.decision ?? 0

  return (
    <div className="max-w-5xl mx-auto space-y-5">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Analysis History</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {total} total analyses · click any row to reopen instantly
          </p>
        </div>
        <Link href="/analysis"
          className="flex items-center gap-1.5 text-sm bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-blue-700 transition-colors">
          <FlaskConical className="h-4 w-4" />
          New Analysis
        </Link>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label:"Total",       value: total,    color:"text-gray-900",    bg:"bg-white" },
          { label:"GO",          value: goCount,  color:"text-emerald-600", bg:"bg-emerald-50" },
          { label:"NO-GO",       value: noCount,  color:"text-red-600",     bg:"bg-red-50" },
          { label:"INVESTIGATE", value: invCount, color:"text-amber-600",   bg:"bg-amber-50" },
        ].map(({ label, value, color, bg }) => (
          <div key={label} className={`${bg} border border-gray-200 rounded-xl p-4`}>
            <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">{label}</p>
            <p className={`text-3xl font-black ${color}`}>{value}</p>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(1) }}
            placeholder="Search by disease name..."
            className="w-full pl-9 pr-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <select
          value={decision}
          onChange={e => { setDecision(e.target.value); setPage(1) }}
          className="px-3 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
        >
          <option value="">All Decisions</option>
          <option value="GO">GO</option>
          <option value="NO-GO">NO-GO</option>
          <option value="INVESTIGATE">INVESTIGATE</option>
        </select>
        <button
          onClick={load}
          className="p-2.5 border border-gray-200 rounded-xl hover:bg-gray-50 transition-colors"
          title="Refresh"
        >
          <RefreshCw className="h-4 w-4 text-gray-400" />
        </button>
      </div>

      {/* Table */}
      <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
          </div>
        ) : analyses.length === 0 ? (
          <div className="text-center py-16">
            <FlaskConical className="h-12 w-12 text-gray-200 mx-auto mb-3" />
            <p className="text-gray-500 font-medium">No analyses found</p>
            <p className="text-sm text-gray-400 mt-1">
              {search || decision ? "Try clearing filters" : "Run your first analysis to see it here"}
            </p>
            {!search && !decision && (
              <Link href="/analysis"
                className="inline-flex items-center gap-1.5 mt-4 text-sm bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-blue-700 transition-colors">
                <FlaskConical className="h-4 w-4" />
                Run Analysis
              </Link>
            )}
          </div>
        ) : (
          <>
            {/* Table header */}
            <div className="grid grid-cols-12 gap-3 px-5 py-3 bg-gray-50 border-b border-gray-100 text-xs font-semibold text-gray-400 uppercase tracking-wide">
              <div className="col-span-4">Disease</div>
              <div className="col-span-2">Decision</div>
              <div className="col-span-2">Confidence</div>
              <div className="col-span-2">Risk</div>
              <div className="col-span-1">Date</div>
              <div className="col-span-1"></div>
            </div>

            {/* Rows */}
            <div className="divide-y divide-gray-50">
              {analyses.map(a => {
                const isReopening = reopening === a.id
                const isDeleting  = deleting  === a.id
                return (
                  <div
                    key={a.id}
                    className="grid grid-cols-12 gap-3 px-5 py-4 items-center hover:bg-blue-50/30 transition-colors cursor-pointer group"
                    onClick={() => !isReopening && !isDeleting && handleReopen(a.id)}
                  >
                    {/* Disease name */}
                    <div className="col-span-4 flex items-center gap-2 min-w-0">
                      <div className="h-8 w-8 rounded-lg bg-blue-50 flex items-center justify-center flex-shrink-0">
                        <FlaskConical className="h-4 w-4 text-blue-600" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-semibold text-gray-900 truncate group-hover:text-blue-700 transition-colors">
                          {a.diseaseName}
                        </p>
                        <p className="text-xs text-gray-400 font-mono truncate">{a.id.slice(0, 8)}...</p>
                      </div>
                    </div>

                    {/* Decision */}
                    <div className="col-span-2">
                      {a.decision ? (
                        <span className={`text-xs px-2.5 py-1 rounded-full font-semibold ring-1 ${DEC_STYLE[a.decision] ?? "bg-gray-50 text-gray-600 ring-gray-200"}`}>
                          {a.decision}
                        </span>
                      ) : (
                        <span className="text-gray-300 text-xs">—</span>
                      )}
                    </div>

                    {/* Confidence */}
                    <div className="col-span-2">
                      {a.confidence != null ? (
                        <div className="flex items-center gap-2">
                          <div className="flex-1 bg-gray-100 rounded-full h-1.5">
                            <div
                              className="bg-blue-500 h-1.5 rounded-full"
                              style={{ width: `${Math.round(a.confidence * 100)}%` }}
                            />
                          </div>
                          <span className="text-xs font-semibold text-gray-700 w-9 text-right">
                            {Math.round(a.confidence * 100)}%
                          </span>
                        </div>
                      ) : (
                        <span className="text-gray-300 text-xs">—</span>
                      )}
                    </div>

                    {/* Risk */}
                    <div className="col-span-2">
                      {a.riskLevel ? (
                        <span className={`text-xs font-semibold ${RISK_STYLE[a.riskLevel] ?? "text-gray-500"}`}>
                          {a.riskLevel === "High" ? "🔴" : a.riskLevel === "Medium" ? "🟡" : "🟢"} {a.riskLevel}
                        </span>
                      ) : (
                        <span className="text-gray-300 text-xs">—</span>
                      )}
                    </div>

                    {/* Date */}
                    <div className="col-span-1">
                      <p className="text-xs text-gray-400">
                        {new Date(a.createdAt).toLocaleDateString("en-IN", {
                          day: "numeric", month: "short"
                        })}
                      </p>
                      <p className="text-xs text-gray-300">
                        {new Date(a.createdAt).getFullYear()}
                      </p>
                    </div>

                    {/* Actions */}
                    <div className="col-span-1 flex items-center justify-end gap-1">
                      {isReopening ? (
                        <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
                      ) : (
                        <button
                          onClick={e => { e.stopPropagation(); handleDelete(a.id) }}
                          disabled={isDeleting}
                          className="p-1.5 text-gray-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                          title="Delete"
                        >
                          {isDeleting
                            ? <Loader2 className="h-3.5 w-3.5 animate-spin" />
                            : <Trash2 className="h-3.5 w-3.5" />}
                        </button>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          </>
        )}
      </div>

      {/* Pagination */}
      {pages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-500">
            Showing {((page-1)*15)+1}–{Math.min(page*15, total)} of {total}
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage(p => Math.max(1, p-1))}
              disabled={page === 1}
              className="p-2 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40 transition-colors"
            >
              <ChevronLeft className="h-4 w-4 text-gray-600" />
            </button>
            <div className="flex gap-1">
              {Array.from({ length: Math.min(5, pages) }, (_, i) => {
                const p = page <= 3 ? i+1 : page-2+i
                if (p > pages) return null
                return (
                  <button
                    key={p}
                    onClick={() => setPage(p)}
                    className={`w-8 h-8 text-sm rounded-lg font-medium transition-colors ${
                      p === page
                        ? "bg-blue-600 text-white"
                        : "border border-gray-200 text-gray-600 hover:bg-gray-50"
                    }`}
                  >
                    {p}
                  </button>
                )
              })}
            </div>
            <button
              onClick={() => setPage(p => Math.min(pages, p+1))}
              disabled={page === pages}
              className="p-2 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40 transition-colors"
            >
              <ChevronRight className="h-4 w-4 text-gray-600" />
            </button>
          </div>
        </div>
      )}

      {/* Usage note */}
      <div className="bg-blue-50 border border-blue-100 rounded-xl px-5 py-3 flex items-center gap-3">
        <BarChart2 className="h-5 w-5 text-blue-500 flex-shrink-0" />
        <p className="text-sm text-blue-700">
          Click any row to instantly reopen that analysis — all 10 tabs load from saved data, no re-running needed.
        </p>
      </div>
    </div>
  )
}