"use client"
// components/tabs/RiskTab.tsx
import type { Drug } from "@/types"
import { Card, StatCard } from "@/components/ui"

export function RiskTab({ drugs }: { drugs: Drug[] }) {
  const counts = { High: 0, Medium: 0, Low: 0, Unknown: 0 }
  drugs.forEach(d => { counts[d.risk_level as keyof typeof counts] = (counts[d.risk_level as keyof typeof counts] ?? 0) + 1 })

  return (
    <div className="space-y-6 tab-content">
      <div>
        <h3 className="text-sm font-semibold text-gray-700 mb-3">⚠️ FDA Risk Intelligence Summary</h3>
        <div className="grid grid-cols-4 gap-3 mb-6">
          <StatCard label="🔴 High Risk"   value={counts.High}    color="red" />
          <StatCard label="🟡 Medium Risk" value={counts.Medium}  color="yellow" />
          <StatCard label="🟢 Low Risk"    value={counts.Low}     color="green" />
          <StatCard label="⚪ Unknown"      value={counts.Unknown} color="gray" />
        </div>
      </div>

      <div>
        <h3 className="text-sm font-semibold text-gray-700 mb-3">📋 Drug Risk Details</h3>
        <div className="space-y-4">
          {drugs.map(drug => {
            const r = drug.risk_level
            const riskBg  = r === "High" ? "bg-red-50 border-red-300" : r === "Medium" ? "bg-amber-50 border-amber-300" : r === "Low" ? "bg-emerald-50 border-emerald-300" : "bg-gray-50 border-gray-200"
            const riskText= r === "High" ? "text-red-800" : r === "Medium" ? "text-amber-800" : r === "Low" ? "text-emerald-800" : "text-gray-700"
            const riskEmoji = r === "High" ? "🔴" : r === "Medium" ? "🟡" : r === "Low" ? "🟢" : "⚪"
            const fda = drug.fda_adverse_events ?? []
            const comp = drug.competition_intel

            return (
              <Card key={drug.drug_name} padding="none">
                {/* Header */}
                <div className={`px-5 py-3 border-l-4 rounded-t-xl flex items-center justify-between ${riskBg} ${r === "High" ? "border-l-red-500" : r === "Medium" ? "border-l-amber-500" : r === "Low" ? "border-l-emerald-500" : "border-l-gray-300"}`}>
                  <div>
                    <p className={`font-bold ${riskText}`}>{riskEmoji} {drug.drug_name} — {r} Risk</p>
                    <p className={`text-xs ${riskText} opacity-75`}>Phase {drug.clinical_phase} · Target: {drug.target_gene}</p>
                  </div>
                  <p className={`text-xs max-w-xs text-right ${riskText} opacity-80`}>{drug.risk_description?.slice(0, 120)}</p>
                </div>

                {/* Competition */}
                {comp && (
                  <div className="px-5 py-3 border-b border-gray-100 bg-gray-50/50">
                    <p className="text-xs font-semibold text-gray-500 mb-2">🏁 Competitive Landscape</p>
                    <div className="flex flex-wrap gap-2 mb-2">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${comp.competition_level === "High" ? "bg-red-100 text-red-700" : comp.competition_level === "Medium" ? "bg-amber-100 text-amber-700" : "bg-emerald-100 text-emerald-700"}`}>
                        {comp.competition_level === "High" ? "🔴" : comp.competition_level === "Medium" ? "🟡" : "🟢"} {comp.competition_level} Competition
                      </span>
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${comp.market_opportunity === "Strong" ? "bg-emerald-100 text-emerald-700" : comp.market_opportunity === "Crowded" ? "bg-red-100 text-red-700" : "bg-amber-100 text-amber-700"}`}>
                        {comp.market_opportunity === "Strong" ? "🌟" : comp.market_opportunity === "Crowded" ? "🏁" : "⚡"} {comp.market_opportunity}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 mb-1">Drug class: {comp.drug_class}</p>
                    <p className="text-xs text-gray-600">{comp.strategic_note}</p>
                    {comp.similar_drug_names?.length > 0 && (
                      <p className="text-xs text-gray-400 mt-1">Similar: {comp.similar_drug_names.slice(0,4).join(", ")}</p>
                    )}
                  </div>
                )}

                {/* FDA adverse events */}
                <div className="px-5 py-4">
                  {fda.length > 0 ? (
                    <>
                      <p className="text-xs font-semibold text-gray-500 mb-3">Top FDA Adverse Events</p>
                      <div className="space-y-2">
                        {fda.slice(0, 5).map(ae => {
                          const pct = Math.min(ae.count / 300, 1)
                          return (
                            <div key={ae.reaction} className="flex items-center gap-3">
                              <p className="text-xs text-gray-700 flex-1 min-w-0 truncate">{ae.reaction}</p>
                              <div className="flex items-center gap-2 flex-shrink-0">
                                <div className="w-24 bg-gray-100 rounded-full h-1.5">
                                  <div className="bg-red-400 h-1.5 rounded-full" style={{ width:`${pct*100}%` }} />
                                </div>
                                <span className="text-xs text-gray-500 w-20 text-right">{ae.count.toLocaleString()} reports</span>
                              </div>
                            </div>
                          )
                        })}
                      </div>
                    </>
                  ) : (
                    <p className="text-sm text-gray-400">No adverse event data in FDA FAERS</p>
                  )}
                </div>
              </Card>
            )
          })}
        </div>
      </div>
    </div>
  )
}