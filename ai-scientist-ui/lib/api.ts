// lib/api.ts
// Complete API service matching all FastAPI endpoints

import type {
  AnalysisResult, TrendData, RepurposeResult,
  UpdatesResponse, KGInsights, NetworkData
} from "@/types"

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  })
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText)
    throw new Error(`${res.status}: ${text}`)
  }
  return res.json() as Promise<T>
}

// ── Analysis ──────────────────────────────────────────────────
export async function analyzeDisease(
  disease_name: string,
  max_targets = 5,
  max_papers = 5,
  max_drugs = 3
): Promise<{ success: boolean; data: AnalysisResult; message: string }> {
  return api("/analyze-disease", {
    method: "POST",
    body: JSON.stringify({ disease_name, max_targets, max_papers, max_drugs }),
  })
}

export async function getExampleDiseases(): Promise<string[]> {
  const r = await api<{ examples: string[] }>("/diseases/examples")
  return r.examples
}

export async function compareDiseases(
  diseases: string[],
  max_targets = 5,
  max_papers = 5,
  max_drugs = 3
) {
  return api("/compare-diseases", {
    method: "POST",
    body: JSON.stringify({ diseases, max_targets, max_papers, max_drugs }),
  })
}

// ── Network ───────────────────────────────────────────────────
export async function getNetworkData(
  disease_name: string,
  max_targets = 5,
  max_papers = 5,
  max_drugs = 3
): Promise<{ network: NetworkData }> {
  return api("/network-data", {
    method: "POST",
    body: JSON.stringify({ disease_name, max_targets, max_papers, max_drugs }),
  })
}

// ── Updates ───────────────────────────────────────────────────
export async function getLatestUpdates(disease?: string): Promise<UpdatesResponse> {
  const q = disease ? `?disease=${encodeURIComponent(disease)}` : ""
  return api(`/latest-updates${q}`)
}

export async function trackDisease(disease_name: string) {
  return api("/track-disease", {
    method: "POST",
    body: JSON.stringify({ disease_name }),
  })
}

export async function triggerUpdate() {
  return api("/trigger-update", { method: "POST" })
}

// ── Trends ────────────────────────────────────────────────────
export async function getTrendingInsights(): Promise<{ trends: TrendData }> {
  return api("/trending-insights")
}

// ── Repurposing ───────────────────────────────────────────────
export async function repurposeDrug(drug_name: string): Promise<RepurposeResult> {
  return api("/repurpose-drug", {
    method: "POST",
    body: JSON.stringify({ drug_name }),
  })
}

// ── PDF ───────────────────────────────────────────────────────
export async function generatePDF(
  disease_name: string,
  max_targets = 5,
  max_papers = 5,
  max_drugs = 3
): Promise<Blob> {
  const res = await fetch(`${BASE}/generate-pdf-report`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ disease_name, max_targets, max_papers, max_drugs }),
  })
  if (!res.ok) throw new Error("PDF generation failed")
  return res.blob()
}

// ── Chat ──────────────────────────────────────────────────────
export async function askQuestion(
  question: string,
  disease_name: string,
  context_data: Record<string, unknown> = {}
): Promise<{ success: boolean; answer: string; sources_used: string[] }> {
  return api("/ask-question", {
    method: "POST",
    body: JSON.stringify({ question, disease_name, context_data }),
  })
}

// ── Knowledge Graph ───────────────────────────────────────────
export async function getKGInsights(): Promise<KGInsights> {
  return api("/knowledge-graph/insights")
}

export async function searchKG(query: string) {
  return api(`/knowledge-graph/search?query=${encodeURIComponent(query)}`)
}

// ── Cache ─────────────────────────────────────────────────────
export async function clearCache() {
  return api("/cache/clear", { method: "DELETE" })
}