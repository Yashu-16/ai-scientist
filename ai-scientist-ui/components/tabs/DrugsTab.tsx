"use client"
// components/tabs/DrugsTab.tsx
import type { Drug } from "@/types"
import { Card, Badge, riskVariant } from "@/components/ui"

export function DrugsTab({ drugs }: { drugs: Drug[] }) {
  return (
    <div className="space-y-4 tab-content">
      <h3 className="text-sm font-semibold text-gray-700">💊 Drug-Protein Associations</h3>
      {drugs.map(drug => {
        const phase              = drug.clinical_phase ?? "N/A"
        const fda                = drug.fda_adverse_events ?? []
        const comp               = drug.competition_intel
        const trials             = (drug as any).clinical_trials      ?? []
        const trialCount         = (drug as any).trial_count          ?? 0
        const activeTrialCount   = (drug as any).active_trial_count   ?? 0
        const completedTrialCount= (drug as any).completed_trial_count ?? 0
        const r        = drug.risk_level
        const riskBg   = r === "High"   ? "bg-red-50 border-red-200 text-red-800"
                       : r === "Medium" ? "bg-amber-50 border-amber-200 text-amber-800"
                       : r === "Low"    ? "bg-emerald-50 border-emerald-200 text-emerald-800"
                       :                  "bg-gray-50 border-gray-200 text-gray-700"
        const riskEmoji= r === "High" ? "🔴" : r === "Medium" ? "🟡" : r === "Low" ? "🟢" : "⚪"

        return (
          <Card key={drug.drug_name} padding="md">
            <div className="grid grid-cols-5 gap-4">

              {/* Drug name + trial badge */}
              <div>
                <p className="font-bold text-gray-900">💊 {drug.drug_name}</p>
                <p className="text-xs text-gray-400 mt-0.5">Type: {drug.drug_type}</p>
                <div className="flex flex-wrap gap-1 mt-2">
                  <span className="text-xs bg-emerald-50 text-emerald-700 px-2.5 py-0.5 rounded-full font-medium">
                    Phase {phase}
                  </span>
                  {trialCount > 0 && (
                    <span className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${
                      activeTrialCount > 0
                        ? "bg-blue-50 text-blue-700"
                        : "bg-gray-100 text-gray-500"
                    }`}>
                      🔬 {trialCount} trial{trialCount !== 1 ? "s" : ""}
                    </span>
                  )}
                </div>
              </div>

              {/* Mechanism */}
              <div className="col-span-1">
                <p className="text-xs text-gray-500 mb-1">
                  Target: <code className="bg-gray-100 px-1 rounded">{drug.target_gene}</code>
                </p>
                <p className="text-xs text-gray-600 leading-relaxed line-clamp-3">
                  {drug.mechanism?.slice(0, 120)}
                </p>
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
                <p className="text-xs text-gray-400 mt-1 leading-relaxed line-clamp-2">
                  {drug.risk_description?.slice(0, 80)}
                </p>
              </div>

              {/* Competition */}
              <div>
                {comp ? (
                  <>
                    <p className="text-xs font-semibold text-gray-500 mb-1">🏆 Competition</p>
                    <div className="space-y-1">
                      <Badge
                        label={`${comp.competition_level} Competition`}
                        variant={comp.competition_level === "High" ? "red" : comp.competition_level === "Medium" ? "yellow" : "green"}
                        size="sm"
                      />
                      <Badge
                        label={comp.market_opportunity}
                        variant={comp.market_opportunity === "Strong" ? "green" : comp.market_opportunity === "Crowded" ? "red" : "yellow"}
                        size="sm"
                      />
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
                    <p className="text-xs text-gray-400 mt-1">
                      Similar drugs: {comp.similar_drug_names.slice(0, 4).join(", ")}
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* ── ClinicalTrials.gov section ──────────────────────── */}
            <div className="mt-3 pt-3 border-t border-gray-100">
              {trialCount > 0 ? (
                <>
                  {/* Header */}
                  <div className="flex items-center justify-between mb-2">
                    <p className="text-xs font-semibold text-blue-700 flex items-center gap-1.5">
                      🔬 ClinicalTrials.gov
                      <span className="bg-blue-100 text-blue-700 text-[10px] px-2 py-0.5 rounded-full font-bold">
                        {trialCount} trial{trialCount !== 1 ? "s" : ""}
                      </span>
                    </p>
                    <div className="flex items-center gap-1.5">
                      {activeTrialCount > 0 && (
                        <span className="text-[10px] bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded-full font-semibold">
                          ● {activeTrialCount} Active
                        </span>
                      )}
                      {completedTrialCount > 0 && (
                        <span className="text-[10px] bg-gray-100 text-gray-500 border border-gray-200 px-2 py-0.5 rounded-full font-semibold">
                          ✓ {completedTrialCount} Completed
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Trial list */}
                  <div className="space-y-1.5">
                    {trials.slice(0, 3).map((trial: any) => {
                      const statusColor =
                        trial.status === "RECRUITING"            ? "bg-emerald-50 border-emerald-200 text-emerald-700" :
                        trial.status === "ACTIVE_NOT_RECRUITING" ? "bg-blue-50 border-blue-200 text-blue-700" :
                        trial.status === "COMPLETED"             ? "bg-gray-50 border-gray-200 text-gray-500" :
                        trial.status === "NOT_YET_RECRUITING"    ? "bg-amber-50 border-amber-200 text-amber-700" :
                        trial.status === "TERMINATED"            ? "bg-red-50 border-red-200 text-red-600" :
                                                                   "bg-gray-50 border-gray-200 text-gray-400"
                      return (
                        <a
                          key={trial.nct_id}
                          href={trial.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-start justify-between gap-3 bg-white border border-gray-100 rounded-lg px-3 py-2 hover:border-blue-200 hover:bg-blue-50 transition-colors group"
                        >
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-0.5">
                              <span className="text-[10px] font-mono font-bold text-blue-600 group-hover:text-blue-800">
                                {trial.nct_id}
                              </span>
                              {trial.phase && trial.phase !== "N/A" && (
                                <span className="text-[10px] bg-purple-50 text-purple-600 px-1.5 py-0.5 rounded font-medium">
                                  {trial.phase}
                                </span>
                              )}
                            </div>
                            <p className="text-xs text-gray-700 leading-snug line-clamp-1 group-hover:text-blue-700">
                              {trial.title}
                            </p>
                            {(trial.sponsor || trial.start_date) && (
                              <p className="text-[10px] text-gray-400 mt-0.5">
                                {trial.sponsor && <span>{trial.sponsor}</span>}
                                {trial.sponsor && trial.start_date && <span> · </span>}
                                {trial.start_date && <span>Started {trial.start_date}</span>}
                              </p>
                            )}
                          </div>
                          <span className={`flex-shrink-0 text-[10px] border px-2 py-0.5 rounded-full font-semibold whitespace-nowrap ${statusColor}`}>
                            {trial.status_label}
                          </span>
                        </a>
                      )
                    })}

                    {trialCount > 3 && (
                      <a
                        href={`https://clinicaltrials.gov/search?intr=${encodeURIComponent(drug.drug_name)}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block text-center text-xs text-blue-500 hover:text-blue-700 py-1.5 border border-dashed border-blue-200 rounded-lg hover:bg-blue-50 transition-colors"
                      >
                        View all {trialCount} trials on ClinicalTrials.gov →
                      </a>
                    )}
                  </div>
                </>
              ) : (
                <p className="text-xs text-gray-400 flex items-center gap-1.5">
                  🔬 <span>No clinical trials found on ClinicalTrials.gov for this drug-disease combination</span>
                </p>
              )}
            </div>

          </Card>
        )
      })}
    </div>
  )
}