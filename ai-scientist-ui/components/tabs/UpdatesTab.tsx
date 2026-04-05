"use client"
// components/tabs/UpdatesTab.tsx
import { useEffect, useState } from "react"
import { getLatestUpdates, trackDisease, triggerUpdate, getKGInsights, searchKG } from "@/lib/api"
import type { UpdatesResponse, KGInsights } from "@/types"
import { Card, StatCard, Spinner } from "@/components/ui"
import { RefreshCw } from "lucide-react"

export function UpdatesTab({ diseaseName }: { diseaseName: string }) {
  const [updates, setUpdates] = useState<UpdatesResponse | null>(null)
  const [kg, setKG] = useState<KGInsights | null>(null)
  const [loading, setLoading] = useState(true)
  const [triggering, setTriggering] = useState(false)
  const [newDisease, setNewDisease] = useState("")
  const [adding, setAdding] = useState(false)
  const [kgQuery, setKgQuery] = useState("")
  const [kgResults, setKgResults] = useState<any>(null)
  const [searchingKG, setSearchingKG] = useState(false)
  const [addMsg, setAddMsg] = useState("")

  useEffect(() => {
    Promise.all([
      getLatestUpdates(diseaseName),
      getKGInsights(),
    ]).then(([u, k]) => {
      setUpdates(u)
      setKG(k)
    }).catch(console.error)
      .finally(() => setLoading(false))
  }, [diseaseName])

  async function handleTrigger() {
    setTriggering(true)
    try {
      const r = await triggerUpdate() as any
      setAddMsg(`✅ ${r.new_papers ?? 0} new papers found`)
      // Reload updates
      const u = await getLatestUpdates(diseaseName)
      setUpdates(u)
    } catch {}
    setTriggering(false)
  }

  async function handleAddDisease() {
    if (!newDisease.trim()) return
    setAdding(true)
    try {
      const r = await trackDisease(newDisease.trim()) as any
      setAddMsg(`✅ ${r.message ?? "Added!"}`)
      setNewDisease("")
      const u = await getLatestUpdates()
      setUpdates(u)
    } catch {}
    setAdding(false)
  }

  async function handleKGSearch() {
    if (!kgQuery.trim()) return
    setSearchingKG(true)
    try {
      const r = await searchKG(kgQuery) as any
      setKgResults(r.results)
    } catch {}
    setSearchingKG(false)
  }

  if (loading) return <div className="flex justify-center py-16"><Spinner size="lg" /></div>

  const papers = updates?.updates?.[diseaseName] ?? []
  const tracked = updates?.tracked_diseases ?? []
  const stats = updates?.stats

  return (
    <div className="space-y-6 tab-content">
      {/* Live Feed */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-gray-700">📡 Real-Time Scientific Updates</h3>
          <button
            onClick={handleTrigger}
            disabled={triggering}
            className="flex items-center gap-1.5 text-xs bg-blue-50 text-blue-600 hover:bg-blue-100 px-3 py-1.5 rounded-lg font-medium transition-colors disabled:opacity-50"
          >
            {triggering ? <Spinner size="sm" /> : <RefreshCw className="h-3 w-3" />}
            Check Now
          </button>
        </div>
        <p className="text-xs text-gray-400 mb-3">Latest PubMed papers for <strong>{diseaseName}</strong> — auto-checked daily at 06:00 UTC</p>
        {addMsg && <p className="text-sm text-emerald-600 mb-3">{addMsg}</p>}

        {papers.length > 0 ? (
          <div>
            <div className="bg-blue-50 border border-blue-100 rounded-lg px-4 py-3 mb-3 flex items-center justify-between">
              <div>
                <span className="text-xs font-semibold text-blue-600 uppercase tracking-wide">📡 Live Feed</span>
                <p className="text-sm text-blue-800 mt-0.5">{papers.length} recent papers</p>
              </div>
              <span className="text-xs text-gray-400">Last check: {stats?.last_check?.slice(0,19) ?? "Pending"}</span>
            </div>
            <div className="space-y-2">
              {papers.slice(0, 5).map((paper, i) => (
                <Card key={i} padding="md">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      <div className="flex items-start gap-2">
                        <p className="text-sm font-medium text-gray-900 leading-snug">{paper.title}</p>
                        {paper.is_new && (
                          <span className="flex-shrink-0 text-xs bg-emerald-500 text-white px-2 py-0.5 rounded-full font-semibold">NEW</span>
                        )}
                      </div>
                      <p className="text-xs text-gray-400 mt-1">📅 {paper.year} | PubMed ID: {paper.pmid}</p>
                    </div>
                    {paper.url && (
                      <a href={paper.url} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-500 hover:text-blue-700 flex-shrink-0">🔗 Read</a>
                    )}
                  </div>
                </Card>
              ))}
            </div>
          </div>
        ) : (
          <p className="text-sm text-gray-400 bg-gray-50 rounded-lg p-4 text-center">No recent updates for {diseaseName}. Click "Check Now" to fetch.</p>
        )}
      </div>

      {/* Tracked Diseases */}
      <div>
        <h3 className="text-sm font-semibold text-gray-700 mb-3">🔭 Tracked Diseases</h3>
        <div className="grid grid-cols-3 gap-3 mb-4">
          <StatCard label="🔬 Tracked" value={tracked.length} />
          <StatCard label="📄 Total Updates" value={stats?.total_updates ?? 0} color="blue" />
          <StatCard label="🔄 Checks Run" value={stats?.check_count ?? 0} />
        </div>
        <div className="space-y-2 mb-4">
          {tracked.map(d => (
            <div key={d} className="flex items-center justify-between px-4 py-2.5 bg-gray-50 border border-gray-100 rounded-lg">
              <span className="text-sm text-gray-700">🔬 {d}</span>
              <span className="text-xs bg-blue-50 text-blue-600 px-2.5 py-0.5 rounded-full font-medium">
                {stats?.updates_per_disease?.[d] ?? 0} updates
              </span>
            </div>
          ))}
        </div>

        {/* Add disease */}
        <div className="flex gap-2">
          <input
            type="text"
            value={newDisease}
            onChange={e => setNewDisease(e.target.value)}
            onKeyDown={e => e.key === "Enter" && handleAddDisease()}
            placeholder="➕ Track a new disease..."
            className="flex-1 px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={handleAddDisease}
            disabled={adding || !newDisease.trim()}
            className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {adding ? <Spinner size="sm" /> : "Add"}
          </button>
        </div>
      </div>

      {/* Knowledge Graph */}
      <div>
        <h3 className="text-sm font-semibold text-gray-700 mb-3">🧠 Knowledge Graph Memory</h3>
        <p className="text-xs text-gray-400 mb-3">Accumulated intelligence from all past analyses</p>
        {kg && (
          <>
            <div className="grid grid-cols-4 gap-3 mb-4">
              <StatCard label="🔵 Nodes"    value={kg.stats.node_count}      color="blue" />
              <StatCard label="🔗 Edges"    value={kg.stats.edge_count}      />
              <StatCard label="🔬 Analyses" value={kg.stats.total_analyses}  color="purple" />
              <StatCard label="🧬 Proteins" value={kg.stats.total_proteins}  color="green" />
            </div>

            {kg.cross_disease_proteins?.length > 0 && (
              <div className="mb-4">
                <p className="text-xs font-semibold text-gray-500 mb-2">🔁 Cross-Disease Proteins</p>
                <div className="space-y-1">
                  {kg.cross_disease_proteins.slice(0,5).map(p => (
                    <div key={p.gene_symbol} className="flex items-center gap-2 bg-blue-50 border-l-2 border-blue-400 pl-3 py-1.5 rounded-r">
                      <span className="text-sm font-bold text-blue-700">{p.gene_symbol}</span>
                      <span className="text-xs text-gray-500">Found in: {p.diseases?.join(", ")}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {kg.most_analyzed_drugs?.length > 0 && (
              <div className="mb-4">
                <p className="text-xs font-semibold text-gray-500 mb-2">💊 Most Analyzed Drugs</p>
                <div className="space-y-1">
                  {kg.most_analyzed_drugs.slice(0,5).map((d, i) => (
                    <div key={i} className="flex items-center gap-2 bg-emerald-50 border-l-2 border-emerald-400 pl-3 py-1.5 rounded-r">
                      <span className="text-sm font-bold text-emerald-700">{d.drug_name ?? d.name}</span>
                      <span className="text-xs text-gray-500">Phase {d.phase} | {d.appearances} appearances</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* KG Search */}
            <div>
              <p className="text-xs font-semibold text-gray-500 mb-2">🔍 Search Knowledge Graph</p>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={kgQuery}
                  onChange={e => setKgQuery(e.target.value)}
                  onKeyDown={e => e.key === "Enter" && handleKGSearch()}
                  placeholder="e.g. PSEN1, LECANEMAB..."
                  className="flex-1 px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={handleKGSearch}
                  disabled={searchingKG || !kgQuery.trim()}
                  className="px-4 py-2 bg-gray-800 text-white text-sm rounded-lg hover:bg-gray-700 disabled:opacity-50 transition-colors"
                >
                  {searchingKG ? <Spinner size="sm" /> : "Search"}
                </button>
              </div>
              {kgResults && (
                <div className="mt-3">
                  {(kgResults.proteins?.length > 0 || kgResults.drugs?.length > 0) ? (
                    <div className="bg-gray-50 rounded-lg p-3 text-xs text-gray-700">
                      <pre className="overflow-x-auto">{JSON.stringify(kgResults, null, 2)}</pre>
                    </div>
                  ) : (
                    <p className="text-xs text-gray-400">No results for "{kgQuery}"</p>
                  )}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  )
}