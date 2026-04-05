"use client"
// components/Navbar.tsx
import { useEffect, useState } from "react"
import { loadAnalysis } from "@/lib/store"
import type { AnalysisResult } from "@/types"
import { GoNoBadge } from "./GoNoBadge"
import { Bell, RefreshCw } from "lucide-react"
import Link from "next/link"

export function Navbar() {
  const [data, setData] = useState<AnalysisResult | null>(null)

  useEffect(() => {
    setData(loadAnalysis())
    const handler = () => setData(loadAnalysis())
    window.addEventListener("ais_analysis_updated", handler)
    return () => window.removeEventListener("ais_analysis_updated", handler)
  }, [])

  return (
    <header className="fixed top-0 left-56 right-0 h-14 bg-white border-b border-gray-100 flex items-center justify-between px-6 z-30 shadow-sm">
      <div className="flex items-center gap-3">
        {data ? (
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-400">Analyzing:</span>
            <span className="text-sm font-semibold text-gray-900">{data.disease_name}</span>
            <span className="text-xs text-gray-300">|</span>
            <span className="text-xs text-gray-400">{data.protein_targets?.length} proteins · {data.drugs?.length} drugs · {data.papers?.length} papers</span>
          </div>
        ) : (
          <span className="text-sm text-gray-400">No analysis loaded</span>
        )}
      </div>

      <div className="flex items-center gap-2">
        {data?.decision_summary?.go_no_go && (
          <GoNoBadge decision={data.decision_summary.go_no_go.decision} size="sm" />
        )}
        <Link
          href="/analysis"
          className="flex items-center gap-1.5 text-xs bg-blue-50 text-blue-600 hover:bg-blue-100 px-3 py-1.5 rounded-lg font-medium transition-colors"
        >
          <RefreshCw className="h-3 w-3" />
          New Analysis
        </Link>
        <button className="p-2 rounded-lg hover:bg-gray-50 text-gray-400 hover:text-gray-600 transition-colors">
          <Bell className="h-4 w-4" />
        </button>
      </div>
    </header>
  )
}