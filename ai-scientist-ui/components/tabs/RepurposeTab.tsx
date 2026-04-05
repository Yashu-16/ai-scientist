"use client"
// components/tabs/RepurposeTab.tsx
import { useState } from "react"
import { repurposeDrug } from "@/lib/api"
import type { RepurposeResult } from "@/types"
import { Card, Badge, Spinner } from "@/components/ui"
import { FlaskConical, ChevronDown, ChevronUp } from "lucide-react"

const QUICK_DRUGS = ["Lecanemab", "Metformin", "Nirogacestat", "Rapamycin", "Sildenafil", "Aducanumab"]

const confColor = { High: "green", Medium: "yellow", Low: "gray" } as const
const evColor: Record<string, string> = {
  "Phase 2": "text-emerald-700 bg-emerald-50",
  "Phase 1": "text-lime-700 bg-lime-50",
  "Observational": "text-amber-700 bg-amber-50",
  "Preclinical": "text-orange-700 bg-orange-50",
  "Theoretical": "text-gray-600 bg-gray-50",
}

export function RepurposeTab() {
  const [drugInput, setDrugInput] = useState("")
  const [result, setResult] = useState<RepurposeResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [expanded, setExpanded] = useState<number[]>([0])

  async function handleRepurpose(drug: string) {
    if (!drug.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)
    setExpanded([0])
    try {
      const r = await repurposeDrug(drug.trim())
      setResult(r)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed")
    }
    setLoading(false)
  }

  const toggle = (i: number) =>
    setExpanded(p => p.includes(i) ? p.filter(x => x !== i) : [...p, i])

  const medals = ["🥇", "🥈", "🥉"]
  const potColor = { High: "text-emerald-700 bg-emerald-50 border-emerald-200", Medium: "text-amber-700 bg-amber-50 border-amber-200", Low: "text-gray-600 bg-gray-50 border-gray-200" }
  const potEmoji = { High: "🔥", Medium: "⚡", Low: "❄️" }

  return (
    <div className="space-y-5 tab-content">
      <div>
        <h3 className="text-sm font-semibold text-gray-700">🔁 Drug Repurposing Mode</h3>
        <p className="text-xs text-gray-400 mt-0.5">Enter a drug name to discover potential new disease indications based on mechanism of action and shared pathways.</p>
      </div>

      {/* Quick select */}
      <div>
        <p className="text-xs font-medium text-gray-500 mb-2">Quick select:</p>
        <div className="flex flex-wrap gap-2">
          {QUICK_DRUGS.map(d => (
            <button
              key={d}
              onClick={() => { setDrugInput(d); handleRepurpose(d) }}
              disabled={loading}
              className="text-xs px-3 py-1.5 bg-gray-50 border border-gray-200 rounded-full hover:bg-blue-50 hover:border-blue-200 hover:text-blue-700 transition-colors disabled:opacity-50 font-medium"
            >
              {d}
            </button>
          ))}
        </div>
      </div>

      {/* Input */}
      <div className="flex gap-2">
        <input
          type="text"
          value={drugInput}
          onChange={e => setDrugInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && handleRepurpose(drugInput)}
          placeholder="e.g. Lecanemab, Metformin, Rapamycin..."
          disabled={loading}
          className="flex-1 px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
        />
        <button
          onClick={() => handleRepurpose(drugInput)}
          disabled={loading || !drugInput.trim()}
          className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white text-sm font-semibold rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {loading ? <Spinner size="sm" /> : <FlaskConical className="h-4 w-4" />}
          {loading ? "Analyzing..." : "Analyze"}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-4">
          {/* Drug header card */}
          <Card padding="md" className="border-blue-100">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs text-blue-500 font-semibold uppercase tracking-wide mb-1">Drug Repurposing Analysis</p>
                <p className="text-xl font-bold text-gray-900">💊 {result.drug_name}</p>
                <p className="text-xs text-gray-400 mt-0.5">Primary: {result.primary_indication}</p>
              </div>
              <div className={`text-center border rounded-xl px-4 py-2 ${potColor[result.overall_potential as keyof typeof potColor] ?? potColor.Medium}`}>
                <p className="text-xs font-medium opacity-70 mb-0.5">Repurposing Potential</p>
                <p className="text-lg font-bold">
                  {potEmoji[result.overall_potential as keyof typeof potEmoji] ?? "❓"} {result.overall_potential}
                </p>
              </div>
            </div>
            <div className="mt-3 bg-gray-50 rounded-lg px-4 py-3 text-sm text-gray-700">
              <strong className="text-blue-600">Mechanism: </strong>{result.mechanism_summary}
            </div>
            {result.repurposing_rationale && (
              <p className="text-xs text-gray-400 italic mt-2">{result.repurposing_rationale}</p>
            )}
          </Card>

          {/* Candidates */}
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3">
              🎯 {result.repurposing_candidates?.length ?? 0} Repurposing Candidates
            </h4>
            <div className="space-y-3">
              {result.repurposing_candidates?.map((c, i) => (
                <Card key={i} padding="none" className={expanded.includes(i) ? "ring-2 ring-blue-100" : ""}>
                  <button
                    className="w-full text-left px-5 py-4 flex items-center justify-between hover:bg-gray-50/50 transition-colors rounded-xl"
                    onClick={() => toggle(i)}
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <span className="text-xl flex-shrink-0">{medals[i] ?? `#${i + 1}`}</span>
                      <div className="min-w-0">
                        <p className="text-sm font-semibold text-gray-900">{c.disease}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <Badge
                            label={c.confidence}
                            variant={confColor[c.confidence as keyof typeof confColor] ?? "gray"}
                            size="sm"
                          />
                          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${evColor[c.evidence_level] ?? "text-gray-600 bg-gray-50"}`}>
                            {c.evidence_level}
                          </span>
                        </div>
                      </div>
                    </div>
                    {expanded.includes(i)
                      ? <ChevronUp className="h-4 w-4 text-gray-400 flex-shrink-0" />
                      : <ChevronDown className="h-4 w-4 text-gray-400 flex-shrink-0" />}
                  </button>

                  {expanded.includes(i) && (
                    <div className="px-5 pb-5 space-y-3 border-t border-gray-100 pt-4">
                      <p className="text-sm text-gray-700 leading-relaxed">{c.rationale}</p>

                      {c.shared_pathway && (
                        <div className="bg-purple-50 border-l-2 border-purple-400 pl-3 py-2 rounded-r text-xs text-purple-800">
                          🔗 <strong>Shared pathway:</strong> {c.shared_pathway}
                        </div>
                      )}
                      {c.key_challenge && (
                        <div className="bg-amber-50 border-l-2 border-amber-400 pl-3 py-2 rounded-r text-xs text-amber-800">
                          ⚠️ <strong>Key challenge:</strong> {c.key_challenge}
                        </div>
                      )}
                      {c.next_step && (
                        <div className="bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-2 text-xs text-emerald-800">
                          🚀 <strong>Next step:</strong> {c.next_step}
                        </div>
                      )}
                    </div>
                  )}
                </Card>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}