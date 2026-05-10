"use client"
// components/tabs/RepurposeTab.tsx — Phase 1: Rowan Molecular Validation
import { useState } from "react"
import { repurposeDrug } from "@/lib/api"
import type { RepurposeResult } from "@/types"
import { Card, Badge, Spinner } from "@/components/ui"
import { FlaskConical, ChevronDown, ChevronUp, Beaker, Shield, Zap, AlertTriangle, CheckCircle, Info } from "lucide-react"

const QUICK_DRUGS = ["Lecanemab", "Metformin", "Nirogacestat", "Rapamycin", "Sildenafil", "Imatinib"]

const confColor = { High: "green", Medium: "yellow", Low: "gray" } as const
const evColor: Record<string, string> = {
  "Phase 2":      "text-emerald-700 bg-emerald-50",
  "Phase 1":      "text-lime-700 bg-lime-50",
  "Observational":"text-amber-700 bg-amber-50",
  "Preclinical":  "text-orange-700 bg-orange-50",
  "Theoretical":  "text-gray-600 bg-gray-50",
}

// ── Molecular badge component ──────────────────────────────────────────────
function MolecularBadge({ badge }: { badge: any }) {
  const colors = {
    success: "bg-emerald-50 text-emerald-700 border-emerald-200",
    warning: "bg-amber-50 text-amber-700 border-amber-200",
    danger:  "bg-red-50 text-red-700 border-red-200",
    info:    "bg-blue-50 text-blue-700 border-blue-200",
  }
  return (
    <span className={`inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full border font-medium ${colors[badge.type as keyof typeof colors] ?? colors.info}`}>
      <span>{badge.icon}</span>
      {badge.label}
    </span>
  )
}

// ── Rowan validation panel ─────────────────────────────────────────────────
function RowanValidationPanel({ mol }: { mol: any }) {
  if (!mol) return null

  if (!mol.available) {
    // Biologic drug — show special message
    if (mol.is_biologic) return (
      <div className="mt-3 bg-purple-50 border border-purple-200 rounded-xl p-4 space-y-2">
        <div className="flex items-center gap-2">
          <div className="h-6 w-6 rounded-lg bg-purple-600 flex items-center justify-center flex-shrink-0">
            <Beaker className="h-3.5 w-3.5 text-white" />
          </div>
          <p className="text-xs font-bold text-purple-800">Biologic Drug — Special Validation Required</p>
        </div>
        <p className="text-xs text-purple-700 leading-relaxed">{mol.biologic_note}</p>
        <div className="flex flex-wrap gap-2 mt-2">
          {["Immunogenicity Assay", "Epitope Mapping", "Cryo-EM Structure", "PK/PD Modeling"].map(t => (
            <span key={t} className="text-xs bg-purple-100 text-purple-700 border border-purple-200 px-2.5 py-1 rounded-full font-medium">
              {t}
            </span>
          ))}
        </div>
      </div>
    )

    // Small molecule not found
    return (
      <div className="mt-3 bg-gray-50 border border-gray-200 rounded-xl p-4">
        <div className="flex items-center gap-2 text-gray-500 text-xs">
          <Info className="h-4 w-4" />
          <span>{mol.error ?? "Molecular structure not found in PubChem"}</span>
        </div>
      </div>
    )
  }

  const score = mol.molecular_score ?? 0
  const grade = mol.molecular_grade ?? ""
  const scoreColor = score >= 75 ? "text-emerald-600" : score >= 55 ? "text-amber-600" : "text-red-600"
  const scoreBg    = score >= 75 ? "bg-emerald-50 border-emerald-200" : score >= 55 ? "bg-amber-50 border-amber-200" : "bg-red-50 border-red-200"

  return (
    <div className="mt-4 space-y-3">
      {/* Rowan header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="h-5 w-5 rounded bg-blue-600 flex items-center justify-center">
            <Beaker className="h-3 w-3 text-white" />
          </div>
          <span className="text-xs font-bold text-gray-700">
            Rowan Molecular Validation
            {mol.mock && <span className="ml-1 text-gray-400">(demo)</span>}
          </span>
        </div>
        <div className={`flex items-center gap-2 border rounded-xl px-3 py-1.5 ${scoreBg}`}>
          <span className={`text-lg font-black ${scoreColor}`}>{score}</span>
          <span className="text-xs text-gray-500">/100</span>
        </div>
      </div>

      {/* Grade */}
      <p className={`text-xs font-semibold ${scoreColor}`}>{grade}</p>

      {/* SMILES */}
      {mol.smiles && (
        <div className="bg-gray-900 rounded-lg px-3 py-2">
          <p className="text-[10px] text-gray-500 mb-0.5">Molecular Structure (SMILES)</p>
          <p className="text-xs font-mono text-green-400 truncate">{mol.smiles}</p>
        </div>
      )}

      {/* ADMET */}
      {mol.admet && (
        <div className="bg-white border border-gray-100 rounded-xl p-3">
          <p className="text-xs font-bold text-gray-600 mb-2">🧪 ADMET Properties</p>
          <div className="grid grid-cols-2 gap-2 text-xs">
            {[
              { label:"BBB Permeability",    value: mol.admet.bbb_permeability },
              { label:"hERG Inhibition",     value: mol.admet.herg_inhibition },
              { label:"Hepatotoxicity",      value: mol.admet.hepatotoxicity },
              { label:"Oral Bioavailability",value: mol.admet.oral_bioavailability },
              { label:"Solubility",          value: mol.admet.solubility },
              { label:"Clearance",           value: mol.admet.clearance },
            ].filter(p => p.value && p.value !== "Unknown").map(({ label, value }) => (
              <div key={label} className="flex justify-between gap-1">
                <span className="text-gray-400">{label}</span>
                <span className="font-medium text-gray-700 text-right">{String(value)}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* pKa */}
      {mol.pka && (
        <div className="bg-white border border-gray-100 rounded-xl p-3">
          <p className="text-xs font-bold text-gray-600 mb-2">⚗️ Ionization (pKa)</p>
          <div className="text-xs space-y-1">
            {mol.pka.active_at_physiological_ph && (
              <p className="text-gray-700">
                <span className="text-gray-400">At pH 7.4: </span>
                {mol.pka.active_at_physiological_ph}
              </p>
            )}
            {mol.pka.macroscopic_pka && (
              <p className="text-gray-700">
                <span className="text-gray-400">Macroscopic pKa: </span>
                {mol.pka.macroscopic_pka}
              </p>
            )}
          </div>
        </div>
      )}

      {/* Solubility */}
      {mol.solubility && (
        <div className="bg-white border border-gray-100 rounded-xl p-3">
          <p className="text-xs font-bold text-gray-600 mb-2">💧 Aqueous Solubility</p>
          <div className="text-xs space-y-1">
            {mol.solubility.solubility_class && (
              <p className="text-gray-700">
                <span className="text-gray-400">Class: </span>
                {mol.solubility.solubility_class}
              </p>
            )}
            {mol.solubility.log_s !== null && mol.solubility.log_s !== undefined && (
              <p className="text-gray-700">
                <span className="text-gray-400">LogS: </span>
                {mol.solubility.log_s}
              </p>
            )}
          </div>
        </div>
      )}

      {/* Docking results */}
      {mol.docking && mol.docking.length > 0 && (
        <div className="bg-white border border-gray-100 rounded-xl p-3">
          <p className="text-xs font-bold text-gray-600 mb-2">🎯 Protein-Ligand Docking</p>
          <div className="space-y-2">
            {mol.docking.map((dock: any, i: number) => (
              <div key={i} className="text-xs flex justify-between items-center">
                <span className="text-gray-500">{dock.protein_name} ({dock.pdb_id})</span>
                <div className="text-right">
                  <span className={`font-bold ${(dock.binding_affinity_kcal_mol ?? 0) <= -7 ? "text-emerald-600" : "text-amber-600"}`}>
                    {dock.binding_affinity_kcal_mol} kcal/mol
                  </span>
                  <span className="text-gray-400 ml-1">— {dock.binding_quality}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Summary */}
      {mol.molecular_summary && (
        <p className="text-xs text-gray-400 italic">{mol.molecular_summary}</p>
      )}
    </div>
  )
}

// ── Main RepurposeTab ──────────────────────────────────────────────────────
export function RepurposeTab() {
  const [drugInput, setDrugInput]   = useState("")
  const [result, setResult]         = useState<any>(null)
  const [loading, setLoading]       = useState(false)
  const [error, setError]           = useState<string | null>(null)
  const [expanded, setExpanded]     = useState<number[]>([0])
  const [runRowan, setRunRowan]     = useState(true)

  async function handleRepurpose(drug: string) {
    if (!drug.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)
    setExpanded([0])
    try {
      const r = await repurposeDrug(drug.trim(), runRowan)
      setResult(r)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed")
    }
    setLoading(false)
  }

  const toggle = (i: number) =>
    setExpanded(p => p.includes(i) ? p.filter(x => x !== i) : [...p, i])

  const medals   = ["🥇", "🥈", "🥉"]
  const potColor = {
    High:   "text-emerald-700 bg-emerald-50 border-emerald-200",
    Medium: "text-amber-700 bg-amber-50 border-amber-200",
    Low:    "text-gray-600 bg-gray-50 border-gray-200"
  }
  const potEmoji = { High: "🔥", Medium: "⚡", Low: "❄️" }

  return (
    <div className="space-y-5 tab-content">
      <div>
        <h3 className="text-sm font-semibold text-gray-700">🔁 Drug Repurposing Mode</h3>
        <p className="text-xs text-gray-400 mt-0.5">
          Enter a drug name to discover potential new disease indications.
          Powered by GPT-4o-mini + Rowan molecular validation (ADMET, pKa, Docking).
        </p>
      </div>

      {/* Quick select */}
      <div>
        <p className="text-xs font-medium text-gray-500 mb-2">Quick select:</p>
        <div className="flex flex-wrap gap-2">
          {QUICK_DRUGS.map(d => (
            <button key={d} onClick={() => { setDrugInput(d); handleRepurpose(d) }}
              disabled={loading}
              className="text-xs px-3 py-1.5 bg-gray-50 border border-gray-200 rounded-full hover:bg-blue-50 hover:border-blue-200 hover:text-blue-700 transition-colors disabled:opacity-50 font-medium">
              {d}
            </button>
          ))}
        </div>
      </div>

      {/* Rowan toggle */}
      <div className="flex items-center gap-3 bg-blue-50 border border-blue-100 rounded-xl px-4 py-3">
        <div className="h-7 w-7 rounded-lg bg-blue-600 flex items-center justify-center flex-shrink-0">
          <Beaker className="h-4 w-4 text-white" />
        </div>
        <div className="flex-1">
          <p className="text-xs font-bold text-blue-800">Rowan Molecular Validation</p>
          <p className="text-[11px] text-blue-600 mt-0.5">
            Runs ADMET, pKa, Solubility & Docking via Rowan API for molecular-level proof
          </p>
        </div>
        <button
          onClick={() => setRunRowan(v => !v)}
          className={`relative w-10 h-5 rounded-full transition-colors flex-shrink-0 ${runRowan ? "bg-blue-600" : "bg-gray-300"}`}
        >
          <span className={`absolute top-0.5 left-0.5 h-4 w-4 bg-white rounded-full shadow transition-transform ${runRowan ? "translate-x-5" : ""}`} />
        </button>
      </div>

      {/* Input */}
      <div className="flex gap-2">
        <input type="text" value={drugInput}
          onChange={e => setDrugInput(e.target.value)}
          onKeyDown={e => e.key === "Enter" && handleRepurpose(drugInput)}
          placeholder="e.g. Lecanemab, Metformin, Rapamycin..."
          disabled={loading}
          className="flex-1 px-4 py-2.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
        />
        <button onClick={() => handleRepurpose(drugInput)}
          disabled={loading || !drugInput.trim()}
          className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white text-sm font-semibold rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors">
          {loading ? <Spinner size="sm" /> : <FlaskConical className="h-4 w-4" />}
          {loading ? "Analyzing..." : "Analyze"}
        </button>
      </div>

      {/* Loading status */}
      {loading && (
        <div className="bg-blue-50 border border-blue-100 rounded-xl px-4 py-3 space-y-1.5">
          <div className="flex items-center gap-2 text-xs text-blue-700 font-medium">
            <Spinner size="sm" />
            <span>Running GPT-4o-mini repurposing analysis...</span>
          </div>
          {runRowan && (
            <div className="flex items-center gap-2 text-xs text-blue-600">
              <Beaker className="h-3.5 w-3.5" />
              <span>Fetching SMILES from PubChem → Running Rowan ADMET + pKa + Docking...</span>
            </div>
          )}
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-4">
          {/* Drug header */}
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

            {/* Rowan powered badge */}
            {result.rowan_powered && (
              <div className="mt-3 flex items-center gap-2 bg-blue-600 text-white text-xs font-semibold px-3 py-1.5 rounded-lg w-fit">
                <Beaker className="h-3.5 w-3.5" />
                Molecular validation by Rowan
              </div>
            )}
          </Card>

          {/* Drug-level Rowan validation */}
          {result.molecular_validation && (
            <Card padding="md">
              <p className="text-xs font-bold text-gray-500 uppercase tracking-wide mb-1">
                🔬 Drug Molecular Profile
              </p>
              <RowanValidationPanel mol={result.molecular_validation} />
            </Card>
          )}

          {/* Candidates */}
          <div>
            <h4 className="text-sm font-semibold text-gray-700 mb-3">
              🎯 {result.repurposing_candidates?.length ?? 0} Repurposing Candidates
            </h4>
            <div className="space-y-3">
              {result.repurposing_candidates?.map((c: any, i: number) => (
                <Card key={i} padding="none" className={expanded.includes(i) ? "ring-2 ring-blue-100" : ""}>
                  <button
                    className="w-full text-left px-5 py-4 flex items-center justify-between hover:bg-gray-50/50 transition-colors rounded-xl"
                    onClick={() => toggle(i)}
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <span className="text-xl flex-shrink-0">{medals[i] ?? `#${i + 1}`}</span>
                      <div className="min-w-0">
                        <p className="text-sm font-semibold text-gray-900">{c.disease}</p>
                        <div className="flex items-center gap-2 mt-1 flex-wrap">
                          <Badge
                            label={c.confidence}
                            variant={confColor[c.confidence as keyof typeof confColor] ?? "gray"}
                            size="sm"
                          />
                          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${evColor[c.evidence_level] ?? "text-gray-600 bg-gray-50"}`}>
                            {c.evidence_level}
                          </span>
                          {/* Molecular score badge */}
                          {c.molecular_proof?.molecular_score && (
                            <span className={`text-xs px-2 py-0.5 rounded-full font-bold border ${
                              c.molecular_proof.molecular_score >= 70
                                ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                                : c.molecular_proof.molecular_score >= 50
                                ? "bg-amber-50 text-amber-700 border-amber-200"
                                : "bg-gray-50 text-gray-600 border-gray-200"
                            }`}>
                              🔬 Mol. Score: {c.molecular_proof.molecular_score}/100
                            </span>
                          )}
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

                      {/* Molecular proof badges per candidate */}
                      {c.molecular_proof?.badges?.length > 0 && (
                        <div>
                          <p className="text-xs font-bold text-gray-500 mb-2">🔬 Molecular Proof</p>
                          <div className="flex flex-wrap gap-2">
                            {c.molecular_proof.badges.map((badge: any, bi: number) => (
                              <MolecularBadge key={bi} badge={badge} />
                            ))}
                          </div>
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