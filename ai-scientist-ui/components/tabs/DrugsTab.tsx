"use client"
// components/tabs/DrugsTab.tsx
import type { Drug } from "@/types"
import { Card, Badge, riskVariant } from "@/components/ui"

export function DrugsTab({ drugs }: { drugs: Drug[] }) {
  return (
    <div className="space-y-4 tab-content">
      <h3 className="text-sm font-semibold text-gray-700">💊 Drug-Protein Associations</h3>
      {drugs.map(drug => {
        const phase = drug.clinical_phase ?? "N/A"
        const fda = drug.fda_adverse_events ?? []
        const comp = drug.competition_intel
        const r = drug.risk_level
        const riskBg = r === "High" ? "bg-red-50 border-red-200 text-red-800" : r === "Medium" ? "bg-amber-50 border-amber-200 text-amber-800" : r === "Low" ? "bg-emerald-50 border-emerald-200 text-emerald-800" : "bg-gray-50 border-gray-200 text-gray-700"
        const riskEmoji = r === "High" ? "🔴" : r === "Medium" ? "🟡" : r === "Low" ? "🟢" : "⚪"

        return (
          <Card key={drug.drug_name} padding="md">
            <div className="grid grid-cols-5 gap-4">
              {/* Drug name */}
              <div>
                <p className="font-bold text-gray-900">💊 {drug.drug_name}</p>
                <p className="text-xs text-gray-400 mt-0.5">Type: {drug.drug_type}</p>
                <span className="mt-2 inline-block text-xs bg-emerald-50 text-emerald-700 px-2.5 py-0.5 rounded-full font-medium">Phase {phase}</span>
              </div>

              {/* Mechanism */}
              <div className="col-span-1">
                <p className="text-xs text-gray-500 mb-1">Target: <code className="bg-gray-100 px-1 rounded">{drug.target_gene}</code></p>
                <p className="text-xs text-gray-600 leading-relaxed line-clamp-3">{drug.mechanism?.slice(0, 120)}</p>
              </div>

              {/* FDA signals */}
              <div>
                {fda.length > 0 ? (
                  <>
                    <p className="text-xs font-semibold text-red-500 mb-1">⚠️ Top FDA Signal</p>
                    <div className="bg-red-50 border border-red-100 rounded-lg p-2">
                      <p className="text-xs text-red-800 font-medium">🚨 {fda[0].reaction}</p>
                      <p className="text-xs text-gray-500">{fda[0].count.toLocaleString()} reports</p>
                    </div>
                  </>
                ) : (
                  <p className="text-xs text-gray-400">No FDA signals</p>
                )}
              </div>

              {/* Risk level */}
              <div>
                <p className="text-xs font-semibold text-gray-500 mb-1">🛡️ Risk Level</p>
                <div className={`border rounded-lg px-3 py-2 text-sm font-bold ${riskBg}`}>
                  {riskEmoji} {r}
                </div>
                <p className="text-xs text-gray-400 mt-1 leading-relaxed line-clamp-2">{drug.risk_description?.slice(0, 80)}</p>
              </div>

              {/* Competition */}
              <div>
                {comp ? (
                  <>
                    <p className="text-xs font-semibold text-gray-500 mb-1">🏁 Competition</p>
                    <div className="space-y-1">
                      <Badge label={`${comp.competition_level} Competition`} variant={comp.competition_level === "High" ? "red" : comp.competition_level === "Medium" ? "yellow" : "green"} size="sm" />
                      <Badge label={comp.market_opportunity} variant={comp.market_opportunity === "Strong" ? "green" : comp.market_opportunity === "Crowded" ? "red" : "yellow"} size="sm" />
                      <p className="text-xs text-gray-400">{comp.num_similar_drugs} similar drugs</p>
                    </div>
                  </>
                ) : null}
              </div>
            </div>

            {/* Competition detail */}
            {comp && (
              <div className="mt-3 pt-3 border-t border-gray-100">
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs font-medium text-gray-500 mb-1">Drug Class: {comp.drug_class}</p>
                  <p className="text-xs text-gray-600">{comp.strategic_note}</p>
                  {comp.similar_drug_names?.length > 0 && (
                    <p className="text-xs text-gray-400 mt-1">Similar drugs: {comp.similar_drug_names.slice(0,4).join(", ")}</p>
                  )}
                </div>
              </div>
            )}
          </Card>
        )
      })}
    </div>
  )
}