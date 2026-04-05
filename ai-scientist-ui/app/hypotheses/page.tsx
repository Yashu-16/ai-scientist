"use client"
// app/hypotheses/page.tsx
// This page renders ALL 10 tabs matching the Streamlit UI exactly.
// Data persists via localStorage - switching tabs never loses state.

import { useState } from "react"
import { useAnalysis } from "../../lib/hooks"
import { Card, Spinner, EmptyState, StatCard } from "../../components/ui"
import { GoNoGoCard } from "../../components/ui/GoNoBadge"
import { Badge, riskVariant, evidenceVariant } from "../../components/ui"
import { HypothesesTab }  from "../../components/tabs/HypothesesTab"
import { ProteinsTab }    from "../../components/tabs/ProteinsTab"
import { DrugsTab }       from "../../components/tabs/DrugsTab"
import { RiskTab }        from "../../components/tabs/RiskTab"
import { NetworkTab }     from "../../components/tabs/NetworkTab"
import { UpdatesTab }     from "../../components/tabs/UpdatesTab"
import { LiteratureTab }  from "../../components/tabs/LiteratureTab"
import { ChatTab }        from "../../components/tabs/ChatTab"
import { TrendsTab }      from "../../components/tabs/TrendsTab"
import { RepurposeTab }   from "../../components/tabs/RepurposeTab"
import { Lightbulb, FlaskConical } from "lucide-react"
import Link from "next/link"

const TABS = [
  { id:"hypotheses",  label:"💡 Hypotheses" },
  { id:"proteins",    label:"🧬 Proteins & Evidence" },
  { id:"drugs",       label:"💊 Drugs" },
  { id:"risk",        label:"⚠️ Risk Analysis" },
  { id:"network",     label:"🕸️ Network" },
  { id:"updates",     label:"📡 Live Updates" },
  { id:"literature",  label:"📄 Literature Review" },
  { id:"chat",        label:"🤖 Ask AI" },
  { id:"trends",      label:"🔥 Trends" },
  { id:"repurpose",   label:"🔁 Repurpose" },
]

export default function HypothesesPage() {
  const { data, hydrated } = useAnalysis()
  const [activeTab, setActiveTab] = useState("hypotheses")

  if (!hydrated) return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <Spinner size="lg" />
    </div>
  )

  if (!data) return (
    <EmptyState
      icon={<Lightbulb className="h-16 w-16" />}
      title="No analysis loaded"
      subtitle="Run an analysis first to see all 10 analysis tabs with full decision intelligence."
      action={
        <Link href="/analysis" className="inline-flex items-center gap-2 bg-blue-600 text-white text-sm font-medium px-5 py-2.5 rounded-lg hover:bg-blue-700 transition-colors">
          <FlaskConical className="h-4 w-4" />
          Run Analysis
        </Link>
      }
    />
  )

  const ev = data.evidence_strength
  const au = data.analysis_uncertainty
  const ds = data.decision_summary

  return (
    <div className="space-y-5">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">{data.disease_name}</h1>
          <p className="text-sm text-gray-500 mt-0.5">V5 Decision & Risk Intelligence Platform</p>
        </div>
        <Link href="/analysis" className="text-xs bg-blue-50 text-blue-600 hover:bg-blue-100 px-3 py-1.5 rounded-lg font-medium transition-colors flex items-center gap-1.5">
          <FlaskConical className="h-3 w-3" />
          New Analysis
        </Link>
      </div>

      {/* Metrics row */}
      <div className="grid grid-cols-4 gap-3">
        <StatCard label="🧬 Proteins"   value={data.protein_targets?.length ?? 0} color="blue" />
        <StatCard label="💊 Drugs"      value={data.drugs?.length ?? 0}           color="green" />
        <StatCard label="📚 Papers"     value={data.papers?.length ?? 0}          />
        <StatCard label="💡 Hypotheses" value={data.hypotheses?.length ?? 0}      color="purple" />
      </div>

      {/* Evidence banner */}
      {ev && (
        <div className={`rounded-xl border px-5 py-3 flex items-center justify-between ${ev.evidence_color === "green" ? "bg-emerald-50 border-emerald-200" : ev.evidence_color === "red" ? "bg-red-50 border-red-200" : "bg-amber-50 border-amber-200"}`}>
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wide">Evidence Strength</p>
            <div className="flex items-center gap-3 mt-0.5">
              <span className="text-lg font-bold text-gray-900">
                {ev.evidence_color === "green" ? "🟢" : ev.evidence_color === "red" ? "🔴" : "🟡"} {ev.evidence_label}
              </span>
              <span className="text-sm text-gray-500">Score: {ev.evidence_score?.toFixed(2)}/1.00</span>
            </div>
            <p className="text-xs text-gray-400 mt-0.5">📐 {ev.evidence_breakdown}</p>
          </div>
          <div className="text-right text-sm text-gray-500">
            <p>📄 {ev.total_papers} papers</p>
            <p>⭐ {ev.high_citation_papers} highly cited</p>
            <p>🕐 {ev.recent_papers} recent</p>
          </div>
        </div>
      )}

      {/* Uncertainty banner */}
      {au && (
        <div className={`rounded-xl border px-5 py-3 ${au.uncertainty_label === "Low" ? "bg-emerald-50 border-emerald-200" : au.uncertainty_label === "Medium" ? "bg-amber-50 border-amber-200" : "bg-red-50 border-red-200"}`}>
          <div className="flex items-center justify-between mb-1">
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500 uppercase tracking-wide">Analysis Reliability</span>
              <span className="font-bold text-gray-900">
                {au.uncertainty_label === "Low" ? "✅" : au.uncertainty_label === "Medium" ? "⚠️" : au.uncertainty_label === "High" ? "🔶" : "❌"} {au.uncertainty_label} Uncertainty
              </span>
              <span className="text-sm text-gray-500">Score: {au.uncertainty_score?.toFixed(2)}/1.00</span>
            </div>
          </div>
          <p className="text-xs text-gray-500 mb-2">{au.uncertainty_reason}</p>
          <div className="flex flex-wrap gap-1.5">
            {au.low_paper_count    && <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full ring-1 ring-red-200">⚠️ Low Paper Count</span>}
            {au.weak_protein_assoc && <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full ring-1 ring-red-200">⚠️ Weak Protein Assoc.</span>}
            {au.high_fda_risk      && <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full ring-1 ring-red-200">⚠️ High FDA Risk</span>}
            {au.no_causal_evidence && <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full ring-1 ring-amber-200">⚠️ No Causal Evidence</span>}
            {au.limited_drug_data  && <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full ring-1 ring-amber-200">⚠️ Limited Drug Data</span>}
            {!au.low_paper_count && !au.weak_protein_assoc && !au.high_fda_risk && !au.no_causal_evidence && !au.limited_drug_data && (
              <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full ring-1 ring-emerald-200">✅ No critical uncertainty flags</span>
            )}
          </div>
        </div>
      )}

      {/* Decision summary panel */}
      {ds && (
        <Card padding="md">
          <p className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-3">🎯 V4 Decision Intelligence</p>
          <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-4 mb-4">
            <p className="text-xs text-blue-300 font-semibold uppercase tracking-wide mb-1">✅ Best Recommendation for {data.disease_name}</p>
            <p className="text-white text-base font-medium">{ds.best_hypothesis}</p>
          </div>

          <div className="grid grid-cols-4 gap-3 mb-4">
            <div className="bg-blue-50 border border-blue-100 rounded-lg px-4 py-3 text-center">
              <p className="text-xs text-blue-400 font-medium mb-1">💊 Recommended Drug</p>
              <p className="text-lg font-bold text-blue-700">{ds.recommended_drug}</p>
            </div>
            <div className="bg-purple-50 border border-purple-100 rounded-lg px-4 py-3 text-center">
              <p className="text-xs text-purple-400 font-medium mb-1">🧬 Target Protein</p>
              <p className="text-lg font-bold text-purple-700">{ds.target_protein}</p>
            </div>
            <div className="bg-gray-50 border border-gray-100 rounded-lg px-4 py-3 text-center">
              <p className="text-xs text-gray-400 font-medium mb-1">📊 Confidence</p>
              <p className={`text-lg font-bold ${(ds.confidence_score ?? 0) >= 0.8 ? "text-emerald-700" : (ds.confidence_score ?? 0) >= 0.6 ? "text-amber-700" : "text-red-700"}`}>
                {Math.round((ds.confidence_score ?? 0) * 100)}%
              </p>
              <p className="text-xs text-gray-400">{ds.confidence_label}</p>
            </div>
            <div className="bg-gray-50 border border-gray-100 rounded-lg px-4 py-3 text-center">
              <p className="text-xs text-gray-400 font-medium mb-1">⚠️ Risk Level</p>
              <p className={`text-lg font-bold ${ds.risk_level === "High" ? "text-red-700" : ds.risk_level === "Medium" ? "text-amber-700" : "text-emerald-700"}`}>
                {ds.risk_level === "High" ? "🔴" : ds.risk_level === "Medium" ? "🟡" : "🟢"} {ds.risk_level}
              </p>
            </div>
          </div>

          {ds.go_no_go && <GoNoGoCard gng={ds.go_no_go} />}

          <div className="mt-4 space-y-2">
            {ds.target_pathway && (
              <span className="inline-block bg-blue-50 text-blue-700 border border-blue-100 px-3 py-1 rounded-full text-xs font-medium">
                🔬 Pathway: {ds.target_pathway}
              </span>
            )}
            {ds.reasoning_summary && (
              <div className="bg-gray-900 rounded-lg px-4 py-3 border-l-4 border-blue-500">
                <p className="text-xs font-semibold text-blue-400 uppercase tracking-wide mb-1">🧠 Scientific Reasoning</p>
                <p className="text-sm text-gray-300 leading-relaxed">{ds.reasoning_summary}</p>
              </div>
            )}
            {ds.suggested_action && (
              <div className="bg-emerald-50 border border-emerald-200 rounded-lg px-4 py-3">
                <p className="text-xs font-semibold text-emerald-600 uppercase tracking-wide mb-1">🚀 Suggested Next Action</p>
                <p className="text-sm text-emerald-800">{ds.suggested_action}</p>
              </div>
            )}
            {ds.evidence_basis && (
              <div className="bg-gray-50 rounded-lg px-4 py-2">
                <p className="text-xs text-gray-400">📐 {ds.evidence_basis}</p>
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Tab bar */}
      <div className="border-b border-gray-200 overflow-x-auto">
        <div className="flex gap-0 min-w-max">
          {TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-3 text-sm font-medium whitespace-nowrap transition-all border-b-2 -mb-px ${
                activeTab === tab.id
                  ? "border-blue-600 text-blue-700 bg-blue-50/50"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content — mounted once, shown/hidden via CSS to preserve state */}
      <div>
        <div className={activeTab === "hypotheses" ? "" : "hidden"}>
          <HypothesesTab hypotheses={data.hypotheses ?? []} drugs={data.drugs ?? []} />
        </div>
        <div className={activeTab === "proteins" ? "" : "hidden"}>
          <ProteinsTab proteins={data.protein_targets ?? []} papers={data.papers ?? []} />
        </div>
        <div className={activeTab === "drugs" ? "" : "hidden"}>
          <DrugsTab drugs={data.drugs ?? []} />
        </div>
        <div className={activeTab === "risk" ? "" : "hidden"}>
          <RiskTab drugs={data.drugs ?? []} />
        </div>
        {activeTab === "network" && (
          <NetworkTab diseaseName={data.disease_name} />
        )}
        {activeTab === "updates" && (
          <UpdatesTab diseaseName={data.disease_name} />
        )}
        <div className={activeTab === "literature" ? "" : "hidden"}>
          <LiteratureTab lr={data.literature_review} diseaseName={data.disease_name} />
        </div>
        <div className={activeTab === "chat" ? "" : "hidden"}>
          <ChatTab data={data} />
        </div>
        {activeTab === "trends" && <TrendsTab />}
        {activeTab === "repurpose" && <RepurposeTab />}
      </div>
    </div>
  )
}