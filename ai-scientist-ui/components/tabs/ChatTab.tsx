"use client"
// components/tabs/ChatTab.tsx — with localStorage persistence
import { useState, useRef, useEffect, useCallback } from "react"
import { askQuestion } from "@/lib/api"
import { saveChatHistory, loadChatHistory, clearChatHistory } from "@/lib/store"
import type { AnalysisResult, ChatMessage } from "@/types"
import { Spinner } from "@/components/ui"
import { Send, RotateCcw } from "lucide-react"

const SUGGESTED = [
  "Why is the top hypothesis risky?",
  "Explain the amyloidogenic pathway simply",
  "What are the main differences between the top 2 drugs?",
  "Which protein target is most promising and why?",
  "What experiments should I run first?",
  "Summarize this analysis for a non-scientist",
  "What are the biggest uncertainties?",
  "What is the FDA risk and how serious is it?",
  "Why did the hypothesis score lower?",
  "What would make this a GO instead of INVESTIGATE?",
]

function buildContext(data: AnalysisResult) {
  return {
    protein_targets: data.protein_targets?.slice(0,5).map(p => ({
      gene_symbol: p.gene_symbol,
      association_score: p.association_score,
      protein_name: p.protein_name,
    })),
    drugs: data.drugs?.slice(0,5).map(d => ({
      drug_name: d.drug_name,
      clinical_phase: d.clinical_phase,
      risk_level: d.risk_level,
      mechanism: d.mechanism?.slice(0, 100),
      target_gene: d.target_gene,
    })),
    hypotheses: data.hypotheses?.slice(0,3).map(h => ({
      title: h.title,
      final_score: h.final_score,
      key_proteins: h.key_proteins,
      key_drugs: h.key_drugs,
      go_no_go: { decision: h.go_no_go?.decision ?? "" },
      failure_prediction: {
        failure_risk_label: h.failure_prediction?.failure_risk_label ?? "",
        success_probability: h.failure_prediction?.success_probability ?? 0,
      },
    })),
    evidence_strength: {
      evidence_label: data.evidence_strength?.evidence_label,
      total_papers: data.evidence_strength?.total_papers,
    },
    decision_summary: {
      recommended_drug: data.decision_summary?.recommended_drug,
      target_protein: data.decision_summary?.target_protein,
      go_no_go: {
        decision: data.decision_summary?.go_no_go?.decision ?? "",
        confidence_in_decision: data.decision_summary?.go_no_go?.confidence_in_decision ?? 0,
      },
    },
    papers: data.papers?.slice(0,3).map(p => ({ title: p.title?.slice(0,80) })),
  }
}

export function ChatTab({ data }: { data: AnalysisResult }) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [hydrated, setHydrated] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  // Load persisted chat on mount
  useEffect(() => {
    const saved = loadChatHistory(data.disease_name)
    setMessages(saved)
    setHydrated(true)
  }, [data.disease_name])

  // Scroll to bottom on new messages
  useEffect(() => {
    if (hydrated) bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, hydrated])

  const updateMessages = useCallback((newMessages: ChatMessage[]) => {
    setMessages(newMessages)
    saveChatHistory(newMessages, data.disease_name)
  }, [data.disease_name])

  async function send(q: string) {
    if (!q.trim() || loading) return
    const newMsgs: ChatMessage[] = [...messages, { role: "user", content: q }]
    updateMessages(newMsgs)
    setInput("")
    setLoading(true)
    try {
      const ctx = buildContext(data)
      const res = await askQuestion(q, data.disease_name, ctx as any)
      const withReply: ChatMessage[] = [...newMsgs, {
        role: "assistant",
        content: res.answer,
        sources: res.sources_used,
      }]
      updateMessages(withReply)
    } catch {
      const withErr: ChatMessage[] = [...newMsgs, {
        role: "assistant",
        content: "Sorry, I couldn't process that. Make sure the backend is running on port 8000.",
      }]
      updateMessages(withErr)
    }
    setLoading(false)
  }

  function handleClear() {
    clearChatHistory(data.disease_name)
    setMessages([])
  }

  if (!hydrated) return null

  return (
    <div className="flex flex-col h-[680px]">
      <div className="mb-3">
        <h3 className="text-sm font-semibold text-gray-700">🤖 Ask Anything — AI Scientist Chat</h3>
        <p className="text-xs text-gray-400 mt-0.5">
          Ask questions about the <strong>{data.disease_name}</strong> analysis. Chat history persists across tab switches.
        </p>
      </div>

      {/* Suggested questions — only shown when no messages */}
      {messages.length === 0 && (
        <div className="mb-4">
          <p className="text-xs font-semibold text-gray-500 mb-2">💡 Suggested Questions</p>
          <div className="grid grid-cols-3 gap-2">
            {SUGGESTED.slice(0, 6).map(q => (
              <button
                key={q}
                onClick={() => send(q)}
                disabled={loading}
                className="text-xs text-left px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg hover:bg-blue-50 hover:border-blue-200 hover:text-blue-700 transition-colors disabled:opacity-50"
              >
                {q}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-3 mb-4 pr-1">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-[80%] rounded-2xl px-4 py-3 ${
              msg.role === "user"
                ? "bg-blue-600 text-white rounded-br-sm"
                : "bg-white border border-gray-200 shadow-sm rounded-bl-sm"
            }`}>
              <p className={`text-[11px] font-semibold mb-1 ${msg.role === "user" ? "text-blue-200" : "text-emerald-600"}`}>
                {msg.role === "user" ? "👤 You" : "🤖 AI Scientist"}
              </p>
              <p className={`text-sm leading-relaxed whitespace-pre-wrap ${msg.role === "user" ? "text-white" : "text-gray-800"}`}>
                {msg.content}
              </p>
              {msg.sources && msg.sources.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2 pt-2 border-t border-white/20">
                  <span className="text-[10px] text-gray-400">Sources:</span>
                  {msg.sources.map(s => (
                    <span key={s} className="text-[10px] bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded">{s}</span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 shadow-sm rounded-2xl rounded-bl-sm px-4 py-3 flex items-center gap-2">
              <div className="flex gap-1">
                <div className="w-2 h-2 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: "0ms" }} />
                <div className="w-2 h-2 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: "150ms" }} />
                <div className="w-2 h-2 rounded-full bg-blue-400 animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
              <span className="text-sm text-gray-400">AI Scientist is thinking...</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-100 pt-3">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === "Enter" && !e.shiftKey && send(input)}
            placeholder={`Ask about ${data.disease_name}...`}
            disabled={loading}
            className="flex-1 px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 bg-gray-50"
          />
          <button
            onClick={() => send(input)}
            disabled={loading || !input.trim()}
            className="px-4 py-2.5 bg-blue-600 text-white rounded-xl hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            <Send className="h-4 w-4" />
          </button>
          {messages.length > 0 && (
            <button
              onClick={handleClear}
              className="px-3 py-2.5 border border-gray-200 text-gray-400 hover:text-gray-600 rounded-xl hover:bg-gray-50 transition-colors"
              title="Clear chat history"
            >
              <RotateCcw className="h-4 w-4" />
            </button>
          )}
        </div>
        {messages.length > 0 && (
          <p className="text-xs text-gray-400 mt-1.5">
            💬 {messages.filter(m => m.role === "user").length} question{messages.filter(m => m.role === "user").length !== 1 ? "s" : ""} · Chat saved automatically
          </p>
        )}
      </div>
    </div>
  )
}