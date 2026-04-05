// lib/hooks.ts
"use client"
import { useEffect, useState, useCallback } from "react"
import { loadAnalysis, onAnalysisChange } from "./store"
import type { AnalysisResult } from "@/types"

// Hook that automatically syncs with localStorage across tab switches
export function useAnalysis() {
  const [data, setData] = useState<AnalysisResult | null>(null)
  const [hydrated, setHydrated] = useState(false)

  useEffect(() => {
    // Load on mount (after hydration)
    setData(loadAnalysis())
    setHydrated(true)

    // Re-sync when analysis changes
    return onAnalysisChange((newData) => setData(newData))
  }, [])

  const refresh = useCallback(() => {
    setData(loadAnalysis())
  }, [])

  return { data, hydrated, refresh }
}