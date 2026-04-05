"use client"
// components/tabs/TrendsTab.tsx
import { useEffect, useState } from "react"
import { getTrendingInsights } from "@/lib/api"
import type { TrendData } from "@/types"
import { Card, Spinner } from "@/components/ui"
import { RefreshCw } from "lucide-react"

export function TrendsTab() {
  const [trends, setTrends] = useState<TrendData | null>(null)
  const [loading, setLoading] = useState(true)

  function load() {
    setLoading(true)
    getTrendingInsights()
      .then(r => setTrends(r.trends))
      .catch(console.error)
      .finally(() => setLoading(false))
  }

  useEffect(() => { load() }, [])

  if (loading) return <div className="flex justify-center py-16"><Spinner size="lg" /></div>

  if (!trends || trends.total_papers_analyzed === 0) return (
    <div className="text-center py-16">
      <p className="text-4xl mb-3">🔥</p>
      <p className="text-sm text-gray-500">No papers analyzed yet.</p>
      <p className="text-xs text-gray-400 mt-1">The system fetches papers on startup and daily. Click "Check Now" in Live Updates.</p>
    </div>
  )

  return (
    <div className="space-y-6 tab-content">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-gray-700">🔥 Emerging Opportunities & Trends</h3>
          <p className="text-xs text-gray-400 mt-0.5">AI-detected trends from {trends.total_papers_analyzed} recent PubMed papers across tracked diseases</p>
          {trends.last_analyzed && <p className="text-xs text-gray-300 mt-0.5">Last analyzed: {trends.last_analyzed?.slice(0,19)}</p>}
        </div>
        <button
          onClick={load}
          className="flex items-center gap-1.5 text-xs bg-gray-100 hover:bg-gray-200 text-gray-600 px-3 py-1.5 rounded-lg font-medium transition-colors"
        >
          <RefreshCw className="h-3 w-3" />
          Refresh
        </button>
      </div>

      {/* Emerging Opportunities */}
      {trends.emerging_opportunities?.length > 0 && (
        <div>
          <h4 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">💡 Emerging Drug Discovery Opportunities</h4>
          <div className="space-y-2">
            {trends.emerging_opportunities.map((opp, i) => (
              <div
                key={i}
                className={`flex items-start justify-between p-4 rounded-xl border ${opp.strength === "Strong" ? "bg-emerald-50 border-emerald-200" : "bg-amber-50 border-amber-200"}`}
              >
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-semibold text-gray-900">
                    {opp.strength === "Strong" ? "🔥" : "📈"} {opp.signal}
                  </p>
                  <p className="text-xs text-gray-600 mt-1 leading-relaxed">{opp.description}</p>
                </div>
                <span className={`flex-shrink-0 ml-3 text-xs px-2.5 py-1 rounded-full font-semibold ring-1 ${opp.strength === "Strong" ? "bg-emerald-100 text-emerald-800 ring-emerald-300" : "bg-amber-100 text-amber-800 ring-amber-300"}`}>
                  {opp.strength} Signal
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Trend columns */}
      <div className="grid grid-cols-3 gap-5">
        <TrendColumn
          title="🧬 Trending Proteins"
          items={trends.trending_proteins}
          barColor="bg-blue-500"
          hotColor="text-red-600"
          risingColor="text-amber-600"
          emergingColor="text-blue-600"
        />
        <TrendColumn
          title="⚗️ Trending Mechanisms"
          items={trends.trending_mechanisms}
          barColor="bg-purple-500"
          hotColor="text-red-600"
          risingColor="text-amber-600"
          emergingColor="text-purple-600"
        />
        <TrendColumn
          title="🏥 Trending Diseases"
          items={trends.trending_diseases}
          barColor="bg-emerald-500"
          hotColor="text-red-600"
          risingColor="text-amber-600"
          emergingColor="text-emerald-600"
        />
      </div>
    </div>
  )
}

function TrendColumn({
  title, items, barColor, hotColor, risingColor, emergingColor
}: {
  title: string
  items: { name: string; mentions: number; trend: string }[]
  barColor: string
  hotColor: string
  risingColor: string
  emergingColor: string
}) {
  const max = Math.max(...(items?.map(i => i.mentions) ?? [1]), 1)

  return (
    <Card padding="md">
      <h4 className="text-xs font-semibold text-gray-600 mb-3">{title}</h4>
      {items?.length ? (
        <div className="space-y-3">
          {items.slice(0, 6).map(item => {
            const isHot = item.trend.includes("Hot")
            const isRising = item.trend.includes("Rising")
            const color = isHot ? hotColor : isRising ? risingColor : emergingColor
            return (
              <div key={item.name}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium text-gray-800">{item.name}</span>
                  <span className={`text-xs font-medium ${color}`}>
                    {item.trend.split(" ")[0]} ({item.mentions})
                  </span>
                </div>
                <div className="bg-gray-100 rounded-full h-1.5">
                  <div
                    className={`h-1.5 rounded-full transition-all ${barColor}`}
                    style={{ width: `${(item.mentions / max) * 100}%` }}
                  />
                </div>
              </div>
            )
          })}
        </div>
      ) : (
        <p className="text-xs text-gray-300 text-center py-4">No data yet</p>
      )}
    </Card>
  )
}