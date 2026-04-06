"use client"
// app/dashboard/page.tsx
import { useEffect, useState } from "react"
import { loadAnalysis } from "@/lib/store"
import {
  FlaskConical, ChevronRight, Lightbulb,
  TrendingUp, FileText, Clock, AlertTriangle, Loader2
} from "lucide-react"
import Link from "next/link"
import type { AnalysisResult } from "@/types"

export default function DashboardPage() {
  const [data, setData]         = useState<AnalysisResult | null>(null)
  const [hydrated, setHydrated] = useState(false)

  useEffect(() => {
    setData(loadAnalysis())
    setHydrated(true)
    const handler = () => setData(loadAnalysis())
    window.addEventListener("ais_analysis_updated", handler)
    return () => window.removeEventListener("ais_analysis_updated", handler)
  }, [])

  if (!hydrated) return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
    </div>
  )

  if (!data) return (
    <div className="max-w-5xl mx-auto">
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <FlaskConical className="h-16 w-16 text-gray-200 mb-4" />
        <h3 className="text-lg font-bold text-gray-700 mb-2">No analysis yet</h3>
        <p className="text-sm text-gray-400 max-w-sm mb-6">
          Run an analysis to see the decision intelligence dashboard with GO/NO-GO recommendations.
        </p>
        <Link href="/analysis"
          className="inline-flex items-center gap-2 bg-blue-600 text-white text-sm font-semibold px-5 py-2.5 rounded-lg hover:bg-blue-700 transition-colors">
          <FlaskConical className="h-4 w-4" />
          Run First Analysis
        </Link>
      </div>
      <div className="mt-4">
        <h3 className="text-sm font-semibold text-gray-500 mb-3">Try These Examples</h3>
        <div className="grid grid-cols-4 gap-3">
          {[
            { emoji:"🧠", name:"Alzheimer disease", desc:"Amyloid cascade" },
            { emoji:"🫀", name:"Parkinson disease", desc:"Alpha-synuclein" },
            { emoji:"🎗️", name:"breast cancer",     desc:"HER2, BRCA1" },
            { emoji:"🩸", name:"type 2 diabetes",   desc:"Insulin resistance" },
          ].map(({ emoji, name, desc }) => (
            <Link key={name} href={`/analysis?disease=${encodeURIComponent(name)}`}
              className="bg-white border border-gray-200 rounded-xl p-4 text-center hover:border-blue-200 hover:bg-blue-50 transition-all group">
              <div className="text-2xl mb-2">{emoji}</div>
              <p className="text-sm font-medium text-gray-800 group-hover:text-blue-700">{name}</p>
              <p className="text-xs text-gray-400 mt-1">{desc}</p>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )

  const ds   = data.decision_summary
  const ev   = data.evidence_strength
  const au   = data.analysis_uncertainty
  const gng  = ds?.go_no_go
  const best = data.hypotheses?.[0]
  const fp   = best?.failure_prediction
  const tti  = best?.time_to_impact

  const decBadge = gng?.decision === "GO"
    ? "bg-emerald-900/40 border-emerald-500/50 text-emerald-300"
    : gng?.decision === "NO-GO"
    ? "bg-red-900/40 border-red-500/50 text-red-300"
    : "bg-amber-900/40 border-amber-500/50 text-amber-300"

  const decDot = gng?.decision === "GO" ? "bg-emerald-400"
    : gng?.decision === "NO-GO" ? "bg-red-400" : "bg-amber-400"

  const riskBadge = (r?: string | null) =>
    r === "High"   ? "bg-red-50 text-red-700 ring-red-200" :
    r === "Medium" ? "bg-amber-50 text-amber-700 ring-amber-200" :
                     "bg-emerald-50 text-emerald-700 ring-emerald-200"

  const evBadge = ev?.evidence_label === "Strong"
    ? "bg-emerald-50 text-emerald-700 ring-emerald-200"
    : ev?.evidence_label === "Moderate"
    ? "bg-amber-50 text-amber-700 ring-amber-200"
    : "bg-red-50 text-red-700 ring-red-200"

  return (
    <div className="max-w-6xl mx-auto space-y-5">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{data.disease_name}</h1>
          <p className="text-sm text-gray-500 mt-0.5">Decision Intelligence Report · V5</p>
        </div>
        <Link href="/analysis"
          className="inline-flex items-center gap-2 text-sm bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors font-medium">
          <FlaskConical className="h-4 w-4" />
          New Analysis
        </Link>
      </div>

      {/* Hero GO/NO-GO */}
      <div className="rounded-2xl overflow-hidden shadow-lg bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-6">
        <div className="flex items-start justify-between gap-6">
          <div className="flex-1 space-y-4">
            <div>
              <p className="text-slate-400 text-xs font-medium uppercase tracking-widest mb-2">
                Final Decision
              </p>
              {gng && (
                <span className={`inline-flex items-center gap-2 text-lg font-black px-4 py-2 rounded-full border ${decBadge}`}>
                  <span className={`h-2.5 w-2.5 rounded-full ${decDot}`} />
                  {gng.decision}
                  <span className="text-sm font-normal opacity-70">
                    {Math.round((gng.confidence_in_decision ?? 0) * 100)}%
                  </span>
                </span>
              )}
            </div>
            <div>
              <p className="text-slate-400 text-xs mb-1">Best Recommendation</p>
              <p className="text-white text-base font-semibold leading-snug max-w-xl">
                {ds?.best_hypothesis}
              </p>
            </div>
            {gng?.primary_reason && (
              <div className="bg-white/10 rounded-lg px-4 py-3 text-slate-300 text-sm max-w-xl">
                📋 {gng.primary_reason}
              </div>
            )}
            {gng?.recommended_action && (
              <div className="bg-emerald-900/30 border border-emerald-700/50 rounded-lg px-4 py-2.5 text-sm text-emerald-300">
                🚀 <strong>Action:</strong> {gng.recommended_action}
              </div>
            )}
          </div>

          <div className="flex-shrink-0 text-right space-y-3 min-w-[160px]">
            <div>
              <p className="text-slate-400 text-xs">Drug</p>
              <p className="text-white font-bold text-lg">{ds?.recommended_drug ?? "—"}</p>
            </div>
            <div>
              <p className="text-slate-400 text-xs">Protein</p>
              <p className="text-white font-semibold">{ds?.target_protein ?? "—"}</p>
            </div>
            <div>
              <p className="text-slate-400 text-xs">Confidence</p>
              <p className="text-white font-bold text-2xl">
                {Math.round((ds?.confidence_score ?? 0) * 100)}%
              </p>
            </div>
            <div>
              <p className="text-slate-400 text-xs">Risk</p>
              <p className={`font-bold text-lg ${
                ds?.risk_level === "High" ? "text-red-400" :
                ds?.risk_level === "Medium" ? "text-amber-400" : "text-emerald-400"
              }`}>
                {ds?.risk_level ?? "—"}
              </p>
            </div>
          </div>
        </div>

        {(gng?.supporting_reasons?.length > 0 || gng?.blocking_reasons?.length > 0) && (
          <div className="mt-5 pt-5 border-t border-slate-700 grid grid-cols-2 gap-4">
            {gng?.supporting_reasons?.length > 0 && (
              <div>
                <p className="text-emerald-400 text-xs font-semibold mb-2">✅ Supporting</p>
                {gng.supporting_reasons.map((r: string, i: number) => (
                  <p key={i} className="text-slate-300 text-xs bg-emerald-900/20 rounded px-2 py-1 mb-1">• {r}</p>
                ))}
              </div>
            )}
            {gng?.blocking_reasons?.length > 0 && (
              <div>
                <p className="text-red-400 text-xs font-semibold mb-2">❌ Blocking</p>
                {gng.blocking_reasons.map((r: string, i: number) => (
                  <p key={i} className="text-slate-300 text-xs bg-red-900/20 rounded px-2 py-1 mb-1">• {r}</p>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label:"🧬 Proteins",   value: data.protein_targets?.length ?? 0, color:"text-blue-600",   sub:"OpenTargets" },
          { label:"💊 Drugs",      value: data.drugs?.length ?? 0,           color:"text-emerald-600",sub:"FDA mapped" },
          { label:"📚 Papers",     value: data.papers?.length ?? 0,          color:"text-gray-900",   sub:"PubMed" },
          { label:"💡 Hypotheses", value: data.hypotheses?.length ?? 0,      color:"text-purple-600", sub:"GPT-4o-mini" },
        ].map(({ label, value, color, sub }) => (
          <div key={label} className="bg-white border border-gray-200 rounded-xl p-5">
            <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">{label}</p>
            <p className={`text-3xl font-bold ${color}`}>{value}</p>
            <p className="text-xs text-gray-400 mt-1">{sub}</p>
          </div>
        ))}
      </div>

      {/* Insight cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-700">Reliability</h3>
            <AlertTriangle className="h-4 w-4 text-gray-300" />
          </div>
          <p className="text-2xl font-bold text-gray-900">{au?.uncertainty_label ?? "—"}</p>
          <p className="text-xs text-gray-400">uncertainty</p>
          <p className="text-xs text-gray-500 mt-2 line-clamp-2">{au?.uncertainty_reason}</p>
          {au && (
            <div className="mt-3 bg-gray-100 rounded-full h-1.5">
              <div className={`h-1.5 rounded-full ${
                au.uncertainty_label === "Low" ? "bg-emerald-500" :
                au.uncertainty_label === "Medium" ? "bg-amber-500" : "bg-red-500"
              }`} style={{ width:`${(au.uncertainty_score ?? 0)*100}%` }} />
            </div>
          )}
        </div>

        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-700">Failure Risk</h3>
            <TrendingUp className="h-4 w-4 text-gray-300" />
          </div>
          {fp ? (
            <>
              <p className="text-2xl font-bold text-gray-900">{fp.failure_risk_label}</p>
              <p className="text-xs text-gray-500 mt-1">
                Success:{" "}
                <span className={`font-semibold ${
                  (fp.success_probability ?? 0) >= 0.7 ? "text-emerald-600" :
                  (fp.success_probability ?? 0) >= 0.4 ? "text-amber-600" : "text-red-600"
                }`}>
                  {Math.round((fp.success_probability ?? 0)*100)}%
                </span>
              </p>
              <p className="text-xs text-gray-400 mt-1 line-clamp-2">{fp.top_failure_reason}</p>
            </>
          ) : <p className="text-gray-400 text-sm">No data yet</p>}
        </div>

        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-700">Time to Market</h3>
            <Clock className="h-4 w-4 text-gray-300" />
          </div>
          {tti ? (
            <>
              <p className="text-2xl font-bold text-gray-900">{tti.years_range}</p>
              <p className="text-xs text-gray-400">{tti.speed_category} track</p>
              <p className="text-xs text-gray-500 mt-1">{tti.current_stage}</p>
              <p className="text-xs text-gray-400 mt-1">
                {Math.round((tti.success_probability ?? 0)*100)}% success
              </p>
            </>
          ) : <p className="text-gray-400 text-sm">No data yet</p>}
        </div>
      </div>

      {/* Evidence + Risk */}
      <div className="grid grid-cols-2 gap-4">
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-gray-900">Evidence Strength</h3>
            {ev && (
              <span className={`text-xs px-2.5 py-1 rounded-full font-semibold ring-1 ${evBadge}`}>
                {ev.evidence_label}
              </span>
            )}
          </div>
          {ev && (
            <div className="space-y-2">
              {[
                { label:"Score",         value:`${ev.evidence_score?.toFixed(2)}/1.00` },
                { label:"Total Papers",  value:ev.total_papers },
                { label:"Recent Papers", value:ev.recent_papers },
                { label:"Highly Cited",  value:ev.high_citation_papers },
              ].map(({ label, value }) => (
                <div key={label} className="flex justify-between py-1.5 border-b border-gray-50 last:border-0">
                  <span className="text-xs text-gray-500">{label}</span>
                  <span className="text-xs font-semibold text-gray-800">{value}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-gray-900">Drug Risk Profile</h3>
            {ds?.risk_level && (
              <span className={`text-xs px-2.5 py-1 rounded-full font-semibold ring-1 ${riskBadge(ds.risk_level)}`}>
                {ds.risk_level}
              </span>
            )}
          </div>
          <div className="space-y-3">
            {data.drugs?.slice(0,3).map((drug: any) => (
              <div key={drug.drug_name} className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-900">{drug.drug_name}</p>
                  <p className="text-xs text-gray-400">Phase {drug.clinical_phase} · {drug.target_gene}</p>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ring-1 ${riskBadge(drug.risk_level)}`}>
                  {drug.risk_level}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Top hypothesis */}
      {best && (
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-gray-900 mb-3">🥇 Top Hypothesis</h3>
          <div className="flex items-start gap-4">
            <div className="flex-1">
              <p className="text-sm font-semibold text-gray-800">{best.title}</p>
              <p className="text-xs text-gray-500 mt-2 leading-relaxed line-clamp-3">{best.explanation}</p>
              <div className="flex flex-wrap gap-1.5 mt-2">
                {best.key_proteins?.map((p: string) => (
                  <span key={p} className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full">{p}</span>
                ))}
                {best.key_drugs?.map((d: string) => (
                  <span key={d} className="text-xs bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded-full">{d}</span>
                ))}
              </div>
            </div>
            <div className="flex-shrink-0 text-center">
              <p className={`text-3xl font-black ${
                (best.final_score ?? 0) >= 0.8 ? "text-emerald-600" :
                (best.final_score ?? 0) >= 0.6 ? "text-amber-600" : "text-red-600"
              }`}>
                {Math.round((best.final_score ?? best.confidence_score) * 100)}%
              </p>
              <p className="text-xs text-gray-400">score</p>
              {best.go_no_go && (
                <span className={`mt-2 inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-full font-semibold ring-1 ${
                  best.go_no_go.decision === "GO"    ? "bg-emerald-50 text-emerald-700 ring-emerald-200" :
                  best.go_no_go.decision === "NO-GO" ? "bg-red-50 text-red-700 ring-red-200" :
                                                       "bg-amber-50 text-amber-700 ring-amber-200"
                }`}>
                  {best.go_no_go.decision}
                </span>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Quick nav */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { href:"/hypotheses", label:"All 10 Tabs",         desc:"Full analysis view",     icon:Lightbulb  },
          { href:"/insights",   label:"Trends & Repurposing",desc:"Emerging opportunities", icon:TrendingUp },
          { href:"/report",     label:"Download Report",     desc:"PDF export + AI chat",   icon:FileText   },
        ].map(({ href, label, desc, icon: Icon }) => (
          <Link key={href} href={href}
            className="flex items-center justify-between p-4 bg-white border border-gray-200 rounded-xl hover:border-blue-200 hover:bg-blue-50 transition-all group">
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gray-100 group-hover:bg-blue-100 transition-colors">
                <Icon className="h-4 w-4 text-gray-500 group-hover:text-blue-600" />
              </div>
              <div>
                <p className="text-sm font-semibold text-gray-900">{label}</p>
                <p className="text-xs text-gray-400">{desc}</p>
              </div>
            </div>
            <ChevronRight className="h-4 w-4 text-gray-300 group-hover:text-blue-500" />
          </Link>
        ))}
      </div>
    </div>
  )
}