"use client"
// components/tabs/HypothesesTab.tsx
import { useState } from "react"
import type { Hypothesis, Drug } from "@/types"
import { Card, Badge, riskVariant, ScoreBar, ExpandSection } from "@/components/ui"
import { GoNoBadge, GoNoGoCard } from "@/components/ui/GoNoBadge"
import { ChevronDown, ChevronUp } from "lucide-react"

export function HypothesesTab({ hypotheses, drugs }: { hypotheses: Hypothesis[]; drugs: Drug[] }) {
  const [expanded, setExpanded] = useState<number[]>([0])
  const toggle = (i: number) =>
    setExpanded(p => p.includes(i) ? p.filter(x => x !== i) : [...p, i])

  const medals = ["🥇","🥈","🥉"]

  return (
    <div className="space-y-6 tab-content">
      {/* Decision Dashboard */}
      <div>
        <h3 className="text-sm font-semibold text-gray-700 mb-3">🎯 Decision Dashboard</h3>
        <div className="grid gap-3" style={{ gridTemplateColumns: `repeat(${hypotheses.length}, 1fr)` }}>
          {hypotheses.map((h, i) => {
            const gng = h.go_no_go
            const tti = h.time_to_impact
            const fp  = h.failure_prediction
            const score = Math.round((h.final_score ?? h.confidence_score) * 100)
            const scoreColor = score >= 80 ? "text-emerald-600" : score >= 60 ? "text-amber-600" : "text-red-600"
            return (
              <Card key={i} padding="md" className="text-center">
                <div className="text-2xl mb-1">{medals[i] ?? `#${i+1}`}</div>
                <p className={`text-2xl font-bold ${scoreColor}`}>{score}%</p>
                {gng && <div className="my-2 flex justify-center"><GoNoBadge decision={gng.decision} size="sm" /></div>}
                <p className="text-xs text-gray-500 truncate">{h.key_drugs?.[0] ?? "—"}</p>
                {(tti || fp) && (
                  <div className="mt-2 text-xs text-gray-400 bg-gray-50 rounded-lg px-2 py-1">
                    {tti && <span>⏱️ {tti.years_range}</span>}
                    {fp && <span className="ml-2">🎯 {Math.round((fp.success_probability ?? 0)*100)}% success</span>}
                  </div>
                )}
              </Card>
            )
          })}
        </div>
      </div>

      {/* Comparison Table */}
      <Card padding="none">
        <div className="px-5 py-3 border-b border-gray-100">
          <h3 className="text-sm font-semibold text-gray-700">📊 Hypothesis Comparison</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-gray-400 uppercase tracking-wide bg-gray-50">
                {["Rank","Hypothesis","Proteins","Drugs","Score","Causal","Risk","Uncertainty","Decision"].map(h => (
                  <th key={h} className="text-left px-4 py-3 font-medium whitespace-nowrap">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {hypotheses.map((h, i) => {
                const drug = drugs.find(d => h.key_drugs?.[0]?.toLowerCase() === d.drug_name.toLowerCase())
                const ca = h.causal_analysis
                const unc = h.uncertainty
                const gng = h.go_no_go
                const score = Math.round((h.final_score ?? h.confidence_score) * 100)
                return (
                  <tr key={i} onClick={() => toggle(i)} className="cursor-pointer hover:bg-blue-50/30 transition-colors">
                    <td className="px-4 py-3 text-xl">{medals[i] ?? `#${i+1}`}</td>
                    <td className="px-4 py-3 max-w-xs">
                      <p className="font-medium text-gray-900 text-xs leading-snug line-clamp-2">{h.title}</p>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {h.key_proteins?.map(p => (
                          <span key={p} className="text-xs bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded-full">{p}</span>
                        ))}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {h.key_drugs?.map(d => (
                          <span key={d} className="text-xs bg-emerald-50 text-emerald-700 px-1.5 py-0.5 rounded-full">{d}</span>
                        )) ?? <span className="text-gray-300">—</span>}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2 min-w-[80px]">
                        <div className="w-10 bg-gray-100 rounded-full h-1.5">
                          <div className="bg-blue-500 h-1.5 rounded-full" style={{ width:`${score}%` }} />
                        </div>
                        <span className="text-xs font-semibold">{score}%</span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      {ca ? (
                        <span className={`text-xs px-2 py-0.5 rounded-full ${ca.causal_label === "Likely Causal" ? "bg-emerald-50 text-emerald-700" : ca.causal_label === "Possibly Causal" ? "bg-amber-50 text-amber-700" : "bg-gray-50 text-gray-500"}`}>
                          {ca.causal_label === "Likely Causal" ? "✅" : ca.causal_label === "Possibly Causal" ? "⚠️" : "ℹ️"} {ca.causal_label}
                        </span>
                      ) : <span className="text-gray-300">—</span>}
                    </td>
                    <td className="px-4 py-3">
                      {drug ? <Badge label={drug.risk_level} variant={riskVariant(drug.risk_level)} size="sm" /> : <span className="text-gray-300">—</span>}
                    </td>
                    <td className="px-4 py-3">
                      {unc ? (
                        <span className={`text-xs px-2 py-0.5 rounded-full ${unc.uncertainty_label === "Low" ? "bg-emerald-50 text-emerald-700" : unc.uncertainty_label === "Medium" ? "bg-amber-50 text-amber-700" : "bg-red-50 text-red-700"}`}>
                          {unc.uncertainty_label === "Low" ? "✅" : unc.uncertainty_label === "Medium" ? "⚠️" : "🔶"} {unc.uncertainty_label}
                        </span>
                      ) : <span className="text-gray-300">—</span>}
                    </td>
                    <td className="px-4 py-3">
                      {gng && <GoNoBadge decision={gng.decision} size="sm" />}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
        <div className="px-5 py-2 border-t border-gray-50">
          <p className="text-xs text-gray-400">Score = 0.4×protein + 0.3×drug_phase + 0.2×papers − 0.1×fda_risk</p>
        </div>
      </Card>

      {/* Detailed Cards */}
      <div>
        <h3 className="text-sm font-semibold text-gray-700 mb-3">🔬 Detailed Analysis</h3>
        <div className="space-y-4">
          {hypotheses.map((h, i) => (
            <HypothesisCard
              key={i}
              hyp={h}
              index={i}
              expanded={expanded.includes(i)}
              onToggle={() => toggle(i)}
              drugs={drugs}
            />
          ))}
        </div>
      </div>
    </div>
  )
}

function HypothesisCard({ hyp, index, expanded, onToggle, drugs }: {
  hyp: Hypothesis; index: number; expanded: boolean; onToggle: () => void; drugs: Drug[]
}) {
  const medals = ["🥇","🥈","🥉"]
  const score = Math.round((hyp.final_score ?? hyp.confidence_score) * 100)
  const ca = hyp.causal_analysis
  const causalTag = ca ? ` | ${ca.causal_label}` : ""
  const drug = drugs.find(d => hyp.key_drugs?.[0]?.toLowerCase() === d.drug_name.toLowerCase())

  return (
    <Card padding="none" className={expanded ? "ring-2 ring-blue-100" : ""}>
      <button
        className="w-full text-left px-5 py-4 flex items-start gap-4 hover:bg-gray-50/50 transition-colors rounded-xl"
        onClick={onToggle}
      >
        <span className="text-2xl mt-0.5 flex-shrink-0">{medals[index] ?? `#${index+1}`}</span>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-gray-900 leading-snug">{hyp.title}</p>
          <p className="text-xs text-gray-400 mt-1">{causalTag}</p>
          <div className="flex flex-wrap gap-1.5 mt-2">
            {hyp.key_proteins?.map(p => (
              <span key={p} className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full">{p}</span>
            ))}
            {hyp.key_drugs?.map(d => (
              <span key={d} className="text-xs bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded-full">{d}</span>
            ))}
          </div>
        </div>
        <div className="flex items-center gap-3 flex-shrink-0">
          {hyp.go_no_go && <GoNoBadge decision={hyp.go_no_go.decision} size="sm" />}
          <span className="text-lg font-bold text-gray-900">{score}%</span>
          {expanded ? <ChevronUp className="h-4 w-4 text-gray-400" /> : <ChevronDown className="h-4 w-4 text-gray-400" />}
        </div>
      </button>

      {expanded && (
        <div className="px-5 pb-5 space-y-5 border-t border-gray-100 pt-4">

          {/* GO/NO-GO full card */}
          {hyp.go_no_go && <GoNoGoCard gng={hyp.go_no_go} />}

          {/* Score breakdown */}
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">📊 Score Breakdown</p>
            <div className="grid grid-cols-5 gap-3">
              {[
                { label:"🧬 Protein",    v: hyp.protein_score,   help:"×0.4" },
                { label:"💊 Drug Phase", v: hyp.drug_score,      help:"×0.3" },
                { label:"📚 Papers",     v: hyp.paper_score,     help:"×0.2" },
                { label:"⚠️ Risk",       v: -(hyp.risk_penalty ?? 0), help:"×0.1" },
                { label:"🎯 Final",      v: hyp.final_score ?? hyp.confidence_score, help:"composite" },
              ].map(({ label, v, help }) => (
                <div key={label} className="bg-gray-50 rounded-lg p-3 text-center">
                  <p className="text-xs text-gray-400">{label}</p>
                  <p className="text-lg font-bold text-gray-900 mt-1">{v != null ? `${Math.round(v * 100)}%` : "—"}</p>
                  <p className="text-xs text-gray-400">{help}</p>
                </div>
              ))}
            </div>
            {hyp.score_breakdown && (
              <p className="text-xs text-gray-400 mt-2">📐 {hyp.score_breakdown}</p>
            )}
          </div>

          {/* LLM Confidence */}
          <div>
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">LLM Confidence</p>
            <div className="flex items-center gap-3">
              <ScoreBar score={hyp.confidence_score} />
              <span className="text-sm text-gray-600">{hyp.confidence_label}</span>
            </div>
          </div>

          {/* Explanations */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-xs font-semibold text-gray-500 mb-2">🔬 Scientific Explanation</p>
              <div className="bg-gray-50 rounded-lg p-3 text-sm text-gray-700 leading-relaxed">{hyp.explanation}</div>
            </div>
            <div>
              <p className="text-xs font-semibold text-gray-500 mb-2">🧒 Simple Explanation</p>
              <div className="bg-gray-50 rounded-lg p-3 text-sm text-gray-700 leading-relaxed">{hyp.simple_explanation}</div>
            </div>
          </div>

          {hyp.evidence_summary && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-2.5 text-sm text-blue-800">
              📌 {hyp.evidence_summary}
            </div>
          )}

          {/* Reasoning chain */}
          {hyp.reasoning_steps?.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-gray-500 mb-2">🔗 Reasoning Chain</p>
              <div className="space-y-2">
                {hyp.reasoning_steps.map((step, i) => (
                  <div key={i} className="flex gap-2">
                    <span className="flex-shrink-0 h-5 w-5 rounded-full bg-indigo-100 text-indigo-700 text-xs flex items-center justify-center font-semibold">{i+1}</span>
                    <p className="text-sm text-gray-700 leading-relaxed">{step}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Causal Analysis */}
          {ca && (
            <ExpandSection title="🔗 Causal Reasoning" defaultOpen>
              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col items-center justify-center bg-gray-50 rounded-lg p-4">
                  <span className="text-2xl mb-1">{ca.causal_label === "Likely Causal" ? "✅" : ca.causal_label === "Possibly Causal" ? "⚠️" : "ℹ️"}</span>
                  <p className="text-sm font-bold text-gray-800">{ca.causal_label}</p>
                  <p className="text-xs text-gray-400 mt-1">Score: {ca.causal_score?.toFixed(2)} | {ca.total_causal_hits} hits</p>
                </div>
                <div>
                  <p className="text-xs text-gray-600 leading-relaxed mb-2">{ca.correlation_note}</p>
                  {ca.causal_verbs_found?.length > 0 && (
                    <p className="text-xs text-gray-500">
                      Causal verbs: {ca.causal_verbs_found.slice(0,6).map(v => (
                        <code key={v} className="bg-gray-100 px-1 py-0.5 rounded text-xs mx-0.5">{v}</code>
                      ))}
                    </p>
                  )}
                </div>
              </div>
              {ca.causal_chain?.length > 0 && (
                <div className="mt-3">
                  <p className="text-xs font-medium text-gray-500 mb-2">⛓️ Causal Chain</p>
                  <div className="flex flex-wrap items-center gap-1">
                    {ca.causal_chain.map((node, i) => (
                      <span key={i}>
                        <span className="bg-gray-100 text-gray-700 px-2 py-1 rounded text-xs font-medium">{node}</span>
                        {i < ca.causal_chain.length-1 && <span className="text-gray-400 mx-1">→</span>}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {ca.causal_evidence?.slice(0,3).map((ev, i) => (
                <div key={i} className={`mt-2 border-l-2 pl-3 py-1 text-xs rounded-r ${ev.strength === "strong" ? "border-emerald-500 bg-emerald-50" : ev.strength === "moderate" ? "border-amber-500 bg-amber-50" : "border-gray-300 bg-gray-50"}`}>
                  <p className="font-medium text-gray-600 uppercase text-[10px]">{ev.strength} — verb: {ev.causal_verb}</p>
                  <p className="text-gray-700 mt-0.5">"{ev.text}"</p>
                  <p className="text-gray-400 mt-0.5">Source: {ev.source}</p>
                </div>
              ))}
            </ExpandSection>
          )}

          {/* Validation Suggestion */}
          {hyp.validation_suggestion && (
            <ExpandSection title="🧪 Experimental Validation Suggestion" defaultOpen>
              <ValidationCard vs={hyp.validation_suggestion} />
            </ExpandSection>
          )}

          {/* Critique */}
          {hyp.critique && (
            <ExpandSection title="🔍 Critical Evaluation">
              <CritiqueCard critique={hyp.critique} />
            </ExpandSection>
          )}

          {/* Failure Prediction */}
          {hyp.failure_prediction && (
            <ExpandSection title="⚠️ Failure Prediction Analysis" defaultOpen>
              <FailureCard fp={hyp.failure_prediction} />
            </ExpandSection>
          )}

          {/* Time to Impact */}
          {hyp.time_to_impact && (
            <ExpandSection title="⏱️ Time-to-Market Estimate" defaultOpen>
              <TimeToImpactCard tti={hyp.time_to_impact} />
            </ExpandSection>
          )}

          {/* Executive Summary */}
          {hyp.executive_summary && (
            <ExpandSection title="📋 Executive Summary" defaultOpen>
              <ExecutiveSummaryCard es={hyp.executive_summary} />
            </ExpandSection>
          )}

          {/* Uncertainty */}
          {hyp.uncertainty && (
            <ExpandSection title="📐 Uncertainty & Reliability">
              <UncertaintyCard unc={hyp.uncertainty} />
            </ExpandSection>
          )}

        </div>
      )}
    </Card>
  )
}

function ValidationCard({ vs }: { vs: NonNullable<Hypothesis["validation_suggestion"]> }) {
  const typeEmoji: Record<string, string> = { "In-vitro":"🧫", "In-vivo":"🐭", "Clinical":"🏥" }
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-xs font-semibold">{typeEmoji[vs.validation_type] ?? "🔬"} {vs.validation_type}</span>
        <span className={`px-3 py-1 rounded-full text-xs font-semibold ${vs.difficulty === "Low" ? "bg-emerald-100 text-emerald-800" : vs.difficulty === "High" ? "bg-red-100 text-red-800" : "bg-amber-100 text-amber-800"}`}>{vs.difficulty} Difficulty</span>
        <span className="text-xs text-gray-500">⏱️ {vs.estimated_timeline}</span>
      </div>
      <p className="text-sm font-semibold text-gray-800">{vs.experiment_title}</p>
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-gray-50 rounded-lg p-3">
          <p className="text-xs font-medium text-gray-400 uppercase mb-1">Protocol</p>
          <p className="text-xs text-gray-700 leading-relaxed">{vs.experiment_description}</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-3">
          <p className="text-xs font-medium text-gray-400 uppercase mb-1">Required Tools</p>
          {vs.required_tools?.map(t => (
            <p key={t} className="text-xs text-gray-700 mb-1">🔧 {t}</p>
          ))}
        </div>
      </div>
      {vs.expected_outcome && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-2 text-xs text-emerald-800">
          ✅ <strong>Expected Outcome:</strong> {vs.expected_outcome}
        </div>
      )}
    </div>
  )
}

function CritiqueCard({ critique }: { critique: NonNullable<Hypothesis["critique"]> }) {
  return (
    <div className="space-y-3">
      <div className={`rounded-lg p-3 border text-sm italic ${critique.critique_severity === "Major" ? "bg-red-50 border-red-200 text-red-800" : critique.critique_severity === "Minor" ? "bg-emerald-50 border-emerald-200 text-emerald-800" : "bg-amber-50 border-amber-200 text-amber-800"}`}>
        <span className="font-semibold not-italic">{critique.critique_severity === "Major" ? "🔴" : critique.critique_severity === "Minor" ? "🟢" : "🟡"} {critique.critique_severity} Limitations: </span>
        "{critique.overall_assessment}"
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          {critique.weaknesses?.length > 0 && (
            <>
              <p className="text-xs font-semibold text-red-600 mb-1">⚠️ Weaknesses</p>
              {critique.weaknesses.map((w, i) => (
                <p key={i} className="text-xs text-gray-700 bg-red-50 border-l-2 border-red-300 pl-2 py-1 mb-1 rounded-r">• {w}</p>
              ))}
            </>
          )}
          {critique.contradictory_evidence?.length > 0 && (
            <>
              <p className="text-xs font-semibold text-orange-600 mb-1 mt-2">🔄 Contradictory Evidence</p>
              {critique.contradictory_evidence.map((c, i) => (
                <p key={i} className="text-xs text-gray-700 bg-orange-50 border-l-2 border-orange-300 pl-2 py-1 mb-1 rounded-r">• {c}</p>
              ))}
            </>
          )}
        </div>
        <div>
          {critique.risks?.length > 0 && (
            <>
              <p className="text-xs font-semibold text-amber-600 mb-1">🚨 Risks</p>
              {critique.risks.map((r, i) => (
                <p key={i} className="text-xs text-gray-700 bg-amber-50 border-l-2 border-amber-300 pl-2 py-1 mb-1 rounded-r">• {r}</p>
              ))}
            </>
          )}
        </div>
      </div>
      {critique.salvage_suggestion && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-3 text-xs text-emerald-800">
          💡 <strong>How to Strengthen:</strong> {critique.salvage_suggestion}
        </div>
      )}
    </div>
  )
}

function FailureCard({ fp }: { fp: NonNullable<Hypothesis["failure_prediction"]> }) {
  const riskColor = fp.failure_risk_label === "High" || fp.failure_risk_label === "Very High"
    ? "text-red-600 bg-red-50 border-red-200"
    : fp.failure_risk_label === "Medium"
    ? "text-amber-600 bg-amber-50 border-amber-200"
    : "text-emerald-600 bg-emerald-50 border-emerald-200"
  const spColor = (fp.success_probability ?? 0) >= 0.7 ? "text-emerald-600" : (fp.success_probability ?? 0) >= 0.4 ? "text-amber-600" : "text-red-600"

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-3 gap-3">
        <div className={`rounded-lg border p-3 text-center ${riskColor}`}>
          <p className="text-xs font-medium opacity-70 mb-1">Failure Risk</p>
          <p className="text-2xl">{fp.failure_risk_label === "Very High" ? "🔴" : fp.failure_risk_label === "High" ? "🔶" : fp.failure_risk_label === "Medium" ? "🟡" : "🟢"}</p>
          <p className="text-sm font-bold mt-1">{fp.failure_risk_label}</p>
          <p className="text-xs opacity-70">{Math.round((fp.failure_risk_score ?? 0)*100)}%</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <p className="text-xs font-medium text-gray-400 mb-1">Success Probability</p>
          <p className={`text-2xl font-bold ${spColor}`}>{Math.round((fp.success_probability ?? 0)*100)}%</p>
          <p className="text-xs text-gray-400">estimated</p>
        </div>
        <div className="bg-red-50 rounded-lg p-3">
          <p className="text-xs font-medium text-red-400 mb-1">Top Failure Mode</p>
          <p className="text-xs text-red-800 leading-relaxed">{fp.top_failure_reason}</p>
        </div>
      </div>
      {fp.historical_context && (
        <div className="bg-blue-50 border border-blue-100 rounded-lg px-3 py-2 text-xs text-blue-800">
          📚 <strong>Historical Context:</strong> {fp.historical_context}
        </div>
      )}
      {fp.failure_reasons?.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-gray-500 mb-2">Predicted Failure Reasons</p>
          <div className="space-y-2">
            {fp.failure_reasons.slice(0,4).map((r, i) => (
              <div key={i} className="border border-gray-100 rounded-lg p-3">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">{r.category}</span>
                  <span className={`text-xs px-2 py-0.5 rounded ${r.severity === "High" ? "bg-red-100 text-red-700" : r.severity === "Medium" ? "bg-amber-100 text-amber-700" : "bg-emerald-100 text-emerald-700"}`}>{r.severity}</span>
                </div>
                <p className="text-xs text-gray-700 mb-1">{r.reason}</p>
                {r.mitigation && <p className="text-xs text-emerald-700">✓ Mitigation: {r.mitigation}</p>}
              </div>
            ))}
          </div>
        </div>
      )}
      {fp.recommended_safeguards?.length > 0 && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-3">
          <p className="text-xs font-semibold text-emerald-700 mb-2">🛡️ Recommended Safeguards</p>
          {fp.recommended_safeguards.slice(0,4).map((s, i) => (
            <p key={i} className="text-xs text-emerald-800 mb-1">• {s}</p>
          ))}
        </div>
      )}
    </div>
  )
}

function TimeToImpactCard({ tti }: { tti: NonNullable<Hypothesis["time_to_impact"]> }) {
  const speedEmoji = { Fast:"🚀", Medium:"⚡", Slow:"🐢" }[tti.speed_category] ?? "⏱️"
  const spColor = (tti.success_probability ?? 0) >= 0.7 ? "text-emerald-600" : (tti.success_probability ?? 0) >= 0.4 ? "text-amber-600" : "text-red-600"
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <p className="text-xs text-gray-400 mb-1">Estimated Timeline</p>
          <p className="text-lg font-bold text-gray-900">{speedEmoji} {tti.years_range}</p>
          <p className="text-xs text-gray-400">{tti.speed_category} track</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-3 text-center">
          <p className="text-xs text-gray-400 mb-1">Success Probability</p>
          <p className={`text-2xl font-bold ${spColor}`}>{Math.round((tti.success_probability ?? 0)*100)}%</p>
          <p className="text-xs text-gray-400">to market</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-3">
          <p className="text-xs text-gray-400 mb-1">Current Stage</p>
          <p className="text-xs font-semibold text-gray-800">{tti.current_stage}</p>
          {tti.next_milestone && <p className="text-xs text-gray-400 mt-1">Next: {tti.next_milestone?.slice(0,60)}...</p>}
        </div>
      </div>
      {tti.timeline_breakdown?.length > 0 && (
        <div>
          <p className="text-xs font-semibold text-gray-500 mb-2">📅 Timeline Breakdown</p>
          <div className="space-y-1">
            {tti.timeline_breakdown.map((step, i) => (
              <div key={i} className="flex gap-2 text-xs">
                <span className="flex-shrink-0 w-5 h-5 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-semibold">{i+1}</span>
                <p className="text-gray-700">{step}</p>
              </div>
            ))}
          </div>
        </div>
      )}
      {tti.key_bottlenecks?.length > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
          <p className="text-xs font-semibold text-amber-700 mb-1">⚠️ Key Bottlenecks</p>
          {tti.key_bottlenecks.map((b, i) => (
            <p key={i} className="text-xs text-amber-800 mb-0.5">• {b}</p>
          ))}
        </div>
      )}
    </div>
  )
}

function ExecutiveSummaryCard({ es }: { es: NonNullable<Hypothesis["executive_summary"]> }) {
  return (
    <div className="bg-gradient-to-br from-slate-50 to-blue-50 rounded-lg border border-blue-100 p-4 space-y-3">
      <p className="text-sm font-bold text-blue-800">💼 {es.headline}</p>
      <p className="text-sm text-gray-700 leading-relaxed">{es.body}</p>
      {es.market_opportunity && (
        <div className="bg-white/70 rounded px-3 py-2 text-xs text-gray-600">💰 {es.market_opportunity}</div>
      )}
      {es.bottom_line && (
        <div className="bg-emerald-50 rounded px-3 py-2 text-xs text-emerald-800 font-semibold">✅ Bottom Line: {es.bottom_line}</div>
      )}
    </div>
  )
}

function UncertaintyCard({ unc }: { unc: NonNullable<Hypothesis["uncertainty"]> }) {
  const emoji = { Low:"✅", Medium:"⚠️", High:"🔶", "Very High":"❌" }[unc.uncertainty_label] ?? "❓"
  const color = { Low:"text-emerald-700 bg-emerald-50 border-emerald-200", Medium:"text-amber-700 bg-amber-50 border-amber-200", High:"text-red-700 bg-red-50 border-red-200", "Very High":"text-red-800 bg-red-100 border-red-300" }[unc.uncertainty_label] ?? "text-gray-700 bg-gray-50 border-gray-200"
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-3">
        <div className={`rounded-lg border p-3 text-center ${color}`}>
          <span className="text-2xl">{emoji}</span>
          <p className="font-bold text-lg mt-1">{unc.uncertainty_label}</p>
          <p className="text-sm">{Math.round(unc.uncertainty_score*100)}%</p>
        </div>
        <div className="space-y-2">
          <div className="bg-gray-50 rounded-lg p-3 text-xs text-gray-700 leading-relaxed">{unc.uncertainty_reason}</div>
          {unc.reliability_note && (
            <div className="bg-emerald-50 border border-emerald-100 rounded-lg p-2 text-xs text-emerald-800">
              💡 <strong>To reduce:</strong> {unc.reliability_note}
            </div>
          )}
        </div>
      </div>
      {unc.factors?.length > 0 && (
        <div className="space-y-1">
          {unc.factors.map((f, i) => (
            <div key={i} className={`flex items-center gap-2 text-xs border-l-2 pl-2 py-1 rounded-r ${f.impact === "High" ? "border-red-400 bg-red-50" : f.impact === "Medium" ? "border-amber-400 bg-amber-50" : "border-emerald-400 bg-emerald-50"}`}>
              <span className="font-semibold text-gray-700">{f.impact === "High" ? "🔴" : f.impact === "Medium" ? "🟡" : "🟢"} {f.factor}: {f.impact}</span>
              <span className="text-gray-500 truncate">{f.description}</span>
            </div>
          ))}
        </div>
      )}
      {/* Flags */}
      <div className="flex flex-wrap gap-1">
        {unc.low_paper_count && <span className="text-xs bg-red-50 text-red-600 px-2 py-0.5 rounded-full ring-1 ring-red-200">🔴 Low paper count</span>}
        {unc.weak_protein_assoc && <span className="text-xs bg-red-50 text-red-600 px-2 py-0.5 rounded-full ring-1 ring-red-200">🔴 Weak protein assoc.</span>}
        {unc.high_fda_risk && <span className="text-xs bg-red-50 text-red-600 px-2 py-0.5 rounded-full ring-1 ring-red-200">🔴 High FDA risk</span>}
        {unc.no_causal_evidence && <span className="text-xs bg-amber-50 text-amber-600 px-2 py-0.5 rounded-full ring-1 ring-amber-200">🟡 No causal evidence</span>}
        {unc.limited_drug_data && <span className="text-xs bg-amber-50 text-amber-600 px-2 py-0.5 rounded-full ring-1 ring-amber-200">🟡 Limited drug data</span>}
        {!unc.low_paper_count && !unc.weak_protein_assoc && !unc.high_fda_risk && !unc.no_causal_evidence && !unc.limited_drug_data && (
          <span className="text-xs bg-emerald-50 text-emerald-600 px-2 py-0.5 rounded-full ring-1 ring-emerald-200">✅ No critical flags</span>
        )}
      </div>
    </div>
  )
}