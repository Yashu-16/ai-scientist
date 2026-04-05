// lib/store.ts
import type { AnalysisResult, ChatMessage } from "@/types"

const ANALYSIS_KEY = "ais_last_analysis"
const DISEASE_KEY  = "ais_last_disease"
const CHAT_KEY     = "ais_chat_history"
const UPDATE_EVENT = "ais_analysis_updated"

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
  localStorage.removeItem(CHAT_KEY)
  window.dispatchEvent(new Event(UPDATE_EVENT))
}

export function onAnalysisChange(cb: (data: AnalysisResult | null) => void): () => void {
  const handler = () => cb(loadAnalysis())
  window.addEventListener(UPDATE_EVENT, handler)
  return () => window.removeEventListener(UPDATE_EVENT, handler)
}

export function saveChatHistory(messages: ChatMessage[]): void {
  try { localStorage.setItem(CHAT_KEY, JSON.stringify(messages)) } catch {}
}

export function loadChatHistory(): ChatMessage[] {
  try {
    const raw = localStorage.getItem(CHAT_KEY)
    return raw ? (JSON.parse(raw) as ChatMessage[]) : []
  } catch { return [] }
}

export function clearChatHistory(): void {
  localStorage.removeItem(CHAT_KEY)
}