// lib/store.ts
import type { AnalysisResult, ChatMessage } from "@/types"

const ANALYSIS_KEY = "ais_last_analysis"
const DISEASE_KEY  = "ais_last_disease"
const UPDATE_EVENT = "ais_analysis_updated"

// ── Analysis ──────────────────────────────────────────────────
export function saveAnalysis(data: AnalysisResult, message = ""): void {
  try {
    localStorage.setItem(ANALYSIS_KEY, JSON.stringify(data))
    localStorage.setItem(DISEASE_KEY,  data.disease_name)
    window.dispatchEvent(new CustomEvent(UPDATE_EVENT, { detail: data }))
  } catch (e) { console.error("Failed to save analysis:", e) }
}

export function loadAnalysis(): AnalysisResult | null {
  try {
    const raw = localStorage.getItem(ANALYSIS_KEY)
    return raw ? (JSON.parse(raw) as AnalysisResult) : null
  } catch { return null }
}

export function loadDisease(): string {
  return localStorage.getItem(DISEASE_KEY) ?? ""
}

export function clearAnalysis(): void {
  localStorage.removeItem(ANALYSIS_KEY)
  localStorage.removeItem(DISEASE_KEY)
  // Clear all disease-specific chat keys
  Object.keys(localStorage)
    .filter(k => k.startsWith("ais_chat_"))
    .forEach(k => localStorage.removeItem(k))
  window.dispatchEvent(new Event(UPDATE_EVENT))
}

export function onAnalysisChange(
  cb: (data: AnalysisResult | null) => void
): () => void {
  const handler = () => cb(loadAnalysis())
  window.addEventListener(UPDATE_EVENT, handler)
  return () => window.removeEventListener(UPDATE_EVENT, handler)
}

// ── Chat — per disease ────────────────────────────────────────
// Each disease gets its own isolated chat history.
// Switching diseases loads that disease's chat (empty if first time).

function chatKey(disease: string): string {
  return `ais_chat_${disease
    .toLowerCase()
    .replace(/\s+/g, "_")
    .replace(/[^a-z0-9_]/g, "")}`
}

export function saveChatHistory(
  messages: ChatMessage[],
  disease?: string
): void {
  try {
    const key = disease ? chatKey(disease) : "ais_chat_default"
    localStorage.setItem(key, JSON.stringify(messages))
  } catch {}
}

export function loadChatHistory(disease?: string): ChatMessage[] {
  try {
    const key = disease ? chatKey(disease) : "ais_chat_default"
    const raw = localStorage.getItem(key)
    return raw ? (JSON.parse(raw) as ChatMessage[]) : []
  } catch { return [] }
}

export function clearChatHistory(disease?: string): void {
  if (disease) {
    localStorage.removeItem(chatKey(disease))
  } else {
    Object.keys(localStorage)
      .filter(k => k.startsWith("ais_chat_"))
      .forEach(k => localStorage.removeItem(k))
  }
}