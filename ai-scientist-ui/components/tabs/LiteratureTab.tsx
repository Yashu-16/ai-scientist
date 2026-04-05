"use client"
// components/tabs/LiteratureTab.tsx
import { useState } from "react"
import type { LiteratureReview } from "@/types"
import { Card } from "@/components/ui"

const sections: { title: string; key: keyof LiteratureReview; color: string }[] = [
  { title: "🔬 Background",          key: "background",          color: "border-blue-400 bg-blue-50" },
  { title: "📚 Current Research",     key: "current_research",    color: "border-purple-400 bg-purple-50" },
  { title: "🔍 Research Gaps",        key: "research_gaps",       color: "border-amber-400 bg-amber-50" },
  { title: "💡 Proposed Hypothesis",  key: "proposed_hypothesis", color: "border-emerald-400 bg-emerald-50" },
  { title: "📊 Supporting Evidence",  key: "supporting_evidence", color: "border-cyan-400 bg-cyan-50" },
  { title: "⚠️ Risks & Limitations",  key: "risks_limitations",  color: "border-red-400 bg-red-50" },
  { title: "✅ Conclusion",           key: "conclusion",          color: "border-emerald-500 bg-emerald-50" },
]

export function LiteratureTab({ lr, diseaseName }: { lr?: LiteratureReview; diseaseName: string }) {
  const [copied, setCopied] = useState(false)

  function copyReport() {
    if (!lr) return
    const text = sections
      .filter(s => lr[s.key])
      .map(s => `${s.title}\n${lr[s.key]}`)
      .join("\n\n")
    navigator.clipboard.writeText(`LITERATURE REVIEW: ${diseaseName}\n\n${text}`)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  if (!lr) return (
    <div className="text-center py-16">
      <p className="text-gray-400 text-sm">Literature review will appear here after analysis.</p>
    </div>
  )

  return (
    <div className="space-y-4 tab-content">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-gray-700">📄 Auto-Generated Literature Review</h3>
          <p className="text-xs text-gray-400 mt-0.5">AI-generated research summary for <strong>{diseaseName}</strong> based on retrieved evidence</p>
          {lr.generated_at && <p className="text-xs text-gray-300 mt-0.5">Generated: {lr.generated_at?.slice(0,19)}</p>}
        </div>
        <button
          onClick={copyReport}
          className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-600 px-3 py-1.5 rounded-lg transition-colors font-medium"
        >
          {copied ? "✅ Copied!" : "📥 Copy Full Report"}
        </button>
      </div>

      <div className="space-y-3">
        {sections.map(s => {
          const content = lr[s.key]
          if (!content) return null
          return (
            <div key={s.key} className={`border-l-4 rounded-r-xl p-4 ${s.color}`}>
              <p className="text-xs font-bold text-gray-600 uppercase tracking-wide mb-2">{s.title}</p>
              <p className="text-sm text-gray-800 leading-relaxed">{content as string}</p>
            </div>
          )
        })}
      </div>
    </div>
  )
}