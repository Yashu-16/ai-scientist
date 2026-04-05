"use client"
// components/tabs/ProteinsTab.tsx
import type { ProteinTarget, Paper } from "@/types"
import { Card } from "@/components/ui"

export function ProteinsTab({ proteins, papers }: { proteins: ProteinTarget[]; papers: Paper[] }) {
  return (
    <div className="space-y-6 tab-content">
      {/* Proteins */}
      <div>
        <h3 className="text-sm font-semibold text-gray-700 mb-3">🧬 Protein Targets</h3>
        <p className="text-xs text-gray-400 mb-3">OpenTargets association scores + AlphaFold pLDDT</p>
        <div className="space-y-3">
          {proteins.map(target => {
            const assoc = target.association_score ?? 0
            const plddt = target.alphafold_plddt ?? 0
            const assocColor = assoc >= 0.8 ? "text-emerald-600" : assoc >= 0.6 ? "text-amber-600" : "text-red-600"
            const plddtColor = plddt >= 0.8 ? "text-emerald-600" : plddt >= 0.6 ? "text-amber-600" : "text-red-600"
            return (
              <Card key={target.gene_symbol} padding="md">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 w-14 h-14 rounded-lg bg-blue-50 flex items-center justify-center">
                    <span className="text-blue-700 font-bold text-sm">{target.gene_symbol}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-gray-900 text-sm">{target.protein_name}</p>
                    <p className="text-xs text-gray-500 mt-0.5 leading-relaxed line-clamp-2">{target.function_description}</p>
                  </div>
                  <div className="flex gap-4 flex-shrink-0">
                    <div className="text-center">
                      <p className={`text-xl font-bold ${assocColor}`}>{assoc.toFixed(2)}</p>
                      <p className="text-xs text-gray-400">Disease Assoc.</p>
                    </div>
                    <div className="text-center bg-gray-50 rounded-lg px-3 py-1">
                      <p className={`text-xl font-bold ${plddtColor}`}>{plddt.toFixed(2)}</p>
                      <p className={`text-xs font-medium ${plddtColor}`}>{target.alphafold_label}</p>
                      <p className="text-xs text-gray-400">AlphaFold pLDDT</p>
                    </div>
                  </div>
                </div>
              </Card>
            )
          })}
        </div>
      </div>

      {/* Papers */}
      <div>
        <h3 className="text-sm font-semibold text-gray-700 mb-3">📚 Research Papers</h3>
        <div className="space-y-3">
          {papers.map((paper, i) => (
            <Card key={i} padding="md">
              <div className="flex items-start gap-3">
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 leading-snug">{paper.title}</p>
                  {(paper.summary && paper.summary !== "No summary available") ? (
                    <p className="text-xs text-gray-500 mt-1 leading-relaxed line-clamp-2">{paper.summary}</p>
                  ) : (paper.abstract && paper.abstract !== "No abstract available") ? (
                    <p className="text-xs text-gray-500 mt-1 leading-relaxed line-clamp-2">{paper.abstract}</p>
                  ) : null}
                </div>
                <div className="flex-shrink-0 text-right">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${paper.source === "PubMed" ? "bg-blue-50 text-blue-700" : "bg-purple-50 text-purple-700"}`}>
                    {paper.source}
                  </span>
                  <p className="text-xs text-gray-400 mt-1">{paper.year ?? "N/A"}</p>
                  {paper.url && (
                    <a href={paper.url} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-500 hover:text-blue-700 mt-1 block">
                      🔗 View
                    </a>
                  )}
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  )
}