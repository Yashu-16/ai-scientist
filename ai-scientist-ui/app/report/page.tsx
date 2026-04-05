"use client"
// app/report/page.tsx
import { useState } from "react"
import { useAnalysis } from "../../lib/hooks"
import { generatePDF } from "@/lib/api"
import { ChatTab } from "../../components/tabs/ChatTab"
import { Card, StatCard, Spinner, EmptyState, Badge, riskVariant, evidenceVariant } from "../../components/ui"
import { GoNoBadge } from "../../components/ui/GoNoBadge"
import { Download, FileText, FlaskConical } from "lucide-react"
import Link from "next/link"

export default function ReportPage() {
  const { data, hydrated } = useAnalysis()
  const [pdfLoading, setPdfLoading] = useState(false)
  const [pdfReady, setPdfReady] = useState(false)
  const [pdfBlob, setPdfBlob] = useState<Blob | null>(null)
  const [pdfError, setPdfError] = useState<string | null>(null)

  if (!hydrated) return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <Spinner size="lg" />
    </div>
  )

  if (!data) return (
    <EmptyState
      icon={<FileText className="h-16 w-16" />}
      title="No report available"
      subtitle="Run an analysis first to generate and download a PDF report."
      action={
        <Link href="/analysis" className="inline-flex items-center gap-2 bg-blue-600 text-white text-sm font-medium px-5 py-2.5 rounded-lg hover:bg-blue-700 transition-colors">
          <FlaskConical className="h-4 w-4" />
          Run Analysis
        </Link>
      }
    />
  )

  async function handleGeneratePDF() {
    if (!data) return
    setPdfLoading(true)
    setPdfError(null)
    try {
      const blob = await generatePDF(data.disease_name)
      setPdfBlob(blob)
      setPdfReady(true)
    } catch (e) {
      setPdfError(e instanceof Error ? e.message : "PDF generation failed")
    }
    setPdfLoading(false)
  }

  function handleDownload() {
    if (!pdfBlob || !data) return
    const url = URL.createObjectURL(pdfBlob)
    const a = document.createElement("a")
    a.href = url
    a.download = `AI_Scientist_${data.disease_name.replace(/ /g, "_")}.pdf`
    a.click()
    URL.revokeObjectURL(url)
  }

  const ds = data.decision_summary
  const ev = data.evidence_strength

  return (
    <div className="max-w-5xl mx-auto space-y-5">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Report</h1>
          <p className="text-sm text-gray-500 mt-0.5">{data.disease_name} — Full Analysis Export</p>
        </div>
        <div className="flex gap-2">
          {!pdfReady ? (
            <button
              onClick={handleGeneratePDF}
              disabled={pdfLoading}
              className="inline-flex items-center gap-2 px-4 py-2 bg-slate-900 text-white text-sm font-semibold rounded-lg hover:bg-slate-800 disabled:opacity-50 transition-colors shadow-sm"
            >
              {pdfLoading ? <Spinner size="sm" /> : <Download className="h-4 w-4" />}
              {pdfLoading ? "Generating PDF..." : "Generate PDF Report"}
            </button>
          ) : (
            <button
              onClick={handleDownload}
              className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white text-sm font-semibold rounded-lg hover:bg-emerald-700 transition-colors shadow-sm"
            >
              <Download className="h-4 w-4" />
              ⬇️ Download PDF Report
            </button>
          )}
        </div>
      </div>

      {pdfError && (
        <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-700">❌ {pdfError}</div>
      )}
      {pdfReady && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-lg px-4 py-3 text-sm text-emerald-800">
          ✅ PDF ready! Click "Download PDF Report" to save.
        </div>
      )}

      {/* Summary stats */}
      <div className="grid grid-cols-4 gap-3">
        <Card padding="md">
          <p className="text-xs text-gray-400 uppercase tracking-wide mb-2">Decision</p>
          {ds?.go_no_go && <GoNoBadge decision={ds.go_no_go.decision} size="sm" />}
        </Card>
        <Card padding="md">
          <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">Confidence</p>
          <p className="text-xl font-bold text-gray-900">{Math.round((ds?.confidence_score ?? 0)*100)}%</p>
        </Card>
        <Card padding="md">
          <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">Risk Level</p>
          {ds?.risk_level && <Badge label={ds.risk_level} variant={riskVariant(ds.risk_level)} />}
        </Card>
        <Card padding="md">
          <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">Evidence</p>
          {ev && <Badge label={ev.evidence_label} variant={evidenceVariant(ev.evidence_label)} />}
        </Card>
      </div>

      {/* Content grid */}
      <div className="grid grid-cols-2 gap-5">

        {/* Protein targets */}
        <Card padding="md">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">🧬 Protein Targets</h3>
          <div className="space-y-3">
            {data.protein_targets?.slice(0,5).map(p => (
              <div key={p.gene_symbol} className="flex items-center justify-between py-1.5 border-b border-gray-50 last:border-0">
                <div>
                  <p className="text-sm font-semibold text-gray-900">{p.gene_symbol}</p>
                  <p className="text-xs text-gray-400">{p.protein_name?.slice(0,30)}</p>
                </div>
                <div className="text-right">
                  <p className={`text-sm font-bold ${p.association_score >= 0.8 ? "text-emerald-600" : p.association_score >= 0.6 ? "text-amber-600" : "text-red-600"}`}>
                    {p.association_score?.toFixed(3)}
                  </p>
                  <p className="text-xs text-gray-400">pLDDT {p.alphafold_plddt?.toFixed(2)}</p>
                </div>
              </div>
            ))}
          </div>
        </Card>

        {/* Drugs */}
        <Card padding="md">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">💊 Drug Overview</h3>
          <div className="space-y-3">
            {data.drugs?.slice(0,5).map(d => (
              <div key={d.drug_name} className="flex items-center justify-between py-1.5 border-b border-gray-50 last:border-0">
                <div>
                  <p className="text-sm font-semibold text-gray-900">{d.drug_name}</p>
                  <p className="text-xs text-gray-400">Phase {d.clinical_phase} · {d.target_gene}</p>
                </div>
                <Badge label={d.risk_level} variant={riskVariant(d.risk_level)} size="sm" />
              </div>
            ))}
          </div>
        </Card>

        {/* Literature overview */}
        <Card padding="md" className="col-span-2">
          <h3 className="text-sm font-semibold text-gray-900 mb-4">📄 Literature Overview</h3>
          {data.literature_review ? (
            <div className="grid grid-cols-2 gap-4">
              {[
                { key:"background",       label:"Background" },
                { key:"current_research", label:"Current Research" },
                { key:"research_gaps",    label:"Research Gaps" },
                { key:"conclusion",       label:"Conclusion" },
              ].map(({ key, label }) => {
                const content = (data.literature_review as any)?.[key]
                return content ? (
                  <div key={key}>
                    <p className="text-xs font-semibold text-gray-500 mb-1">{label}</p>
                    <p className="text-xs text-gray-700 leading-relaxed line-clamp-3">{content}</p>
                  </div>
                ) : null
              })}
            </div>
          ) : (
            <p className="text-sm text-gray-400">No literature review available</p>
          )}
        </Card>
      </div>

      {/* AI Chat */}
      <Card padding="md">
        <ChatTab data={data} />
      </Card>
    </div>
  )
}