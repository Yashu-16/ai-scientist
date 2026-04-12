"use client"
// app/analysis/page.tsx
import { useState, useEffect } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { analyzeDisease, getExampleDiseases } from "@/lib/api"
import { saveAnalysis, clearChatHistory  } from "@/lib/store"
import { Card, Spinner } from "../../components/ui"
import { FlaskConical, Zap, CheckCircle } from "lucide-react"
import { Suspense } from "react"

const STAGES = [
  { label:"Fetching protein targets from OpenTargets...",    duration:8000 },
  { label:"Mapping drugs & FDA adverse event signals...",    duration:8000 },
  { label:"Retrieving PubMed & Semantic Scholar papers...",  duration:15000 },
  { label:"Running causal reasoning analysis...",           duration:10000 },
  { label:"Generating hypotheses (GPT-4o-mini)...",         duration:15000 },
  { label:"Computing GO/NO-GO decision engine...",          duration:8000 },
  { label:"Predicting failure risks & time-to-market...",   duration:8000 },
  { label:"Generating executive summary & literature...",   duration:8000 },
  { label:"Finalizing analysis & saving to knowledge graph...", duration:5000 },
]

function AnalysisForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [disease, setDisease] = useState(searchParams.get("disease") ?? "")
  const [loading, setLoading] = useState(false)
  const [stageIdx, setStageIdx] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [examples, setExamples] = useState<string[]>([])
  const [elapsed, setElapsed] = useState(0)

  useEffect(() => {
    getExampleDiseases()
      .then(setExamples)
      .catch(() => setExamples(["Alzheimer disease","Parkinson disease","breast cancer","type 2 diabetes"]))
  }, [])

  // Auto-run if disease passed via URL
  useEffect(() => {
    const d = searchParams.get("disease")
    if (d) { setDisease(d); }
  }, [searchParams])

  async function handleSubmit(diseaseName: string) {
    if (!diseaseName.trim()) return

    // ── Check plan limit BEFORE running analysis ──────────
    try {
      const limitCheck = await fetch("/api/analyses/check-limit")
      const limitData  = await limitCheck.json()
      if (limitData.limitReached) {
        setError(`Analysis limit reached (${limitData.used}/${limitData.limit}). Please upgrade your plan.`)
        return
      }
    } catch (e) {
      // If check fails, allow the analysis to proceed
    }

    setLoading(true)
    setError(null)
    setStageIdx(0)
    setElapsed(0)

    // Stage ticker
    let idx = 0
    let elapsed = 0
    const ticker = setInterval(() => {
      elapsed += 1
      setElapsed(elapsed)
      if (idx < STAGES.length - 1) {
        // Advance stage based on cumulative duration
        const cumulative = STAGES.slice(0, idx+1).reduce((s, st) => s + st.duration/1000, 0)
        if (elapsed >= cumulative) { idx++; setStageIdx(idx) }
      }
    }, 1000)

    try {
      const result = await analyzeDisease(diseaseName.trim())
      clearInterval(ticker)
      // After successful pipeline result:
        if (result.success) {
          // Save to localStorage (for instant tab switching)
          saveAnalysis(result.data, result.message)
          clearChatHistory(result.data.disease_name) // clear this disease's chat for fresh start

          // Save to PostgreSQL (for history)
          try {
            await fetch("/api/analyses", {
              method:  "POST",
              headers: { "Content-Type": "application/json" },
              body:    JSON.stringify({
                diseaseName: result.data.disease_name,
                result:      result.data,
                decision:    result.data.decision_summary?.go_no_go?.decision   ?? null,
                confidence:  result.data.decision_summary?.confidence_score     ?? null,
                riskLevel:   result.data.decision_summary?.risk_level           ?? null,
              }),
            })
          } catch (e) {
            console.error("Failed to save analysis to DB:", e)
            // Don't block user — localStorage still works
          }

          router.push("/hypotheses")
        } else {
          setError("Analysis failed. Please try again.")
          setLoading(false)
        }
    } catch (e) {
      clearInterval(ticker)
      setError(e instanceof Error ? e.message : "Connection error. Make sure backend is running on port 8000.")
      setLoading(false)
    }
  }

  return (
    <div className="max-w-2xl mx-auto space-y-5">
      <div>
        <h1 className="text-xl font-bold text-gray-900">Run Analysis</h1>
        <p className="text-sm text-gray-500 mt-0.5">Enter a disease to trigger the full 9-stage decision intelligence pipeline</p>
      </div>

      <Card padding="lg">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-semibold text-gray-700 mb-2">Disease Name</label>
            <input
              type="text"
              value={disease}
              onChange={e => setDisease(e.target.value)}
              onKeyDown={e => e.key === "Enter" && !loading && handleSubmit(disease)}
              placeholder="e.g. Alzheimer disease, breast cancer, type 2 diabetes..."
              disabled={loading}
              className="w-full px-4 py-3 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 disabled:bg-gray-50"
              autoFocus
            />
          </div>

          {/* Quick select */}
          <div>
            <p className="text-xs font-medium text-gray-500 mb-2">Quick select:</p>
            <div className="flex flex-wrap gap-2">
              {examples.slice(0,4).map(d => (
                <button
                  key={d}
                  onClick={() => { setDisease(d); handleSubmit(d) }}
                  disabled={loading}
                  className="text-xs px-3 py-1.5 bg-gray-50 border border-gray-200 rounded-full hover:bg-blue-50 hover:border-blue-200 hover:text-blue-700 transition-colors disabled:opacity-50 font-medium"
                >
                  {d}
                </button>
              ))}
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-700">
              ❌ {error}
            </div>
          )}

          <button
            onClick={() => handleSubmit(disease)}
            disabled={loading || !disease.trim()}
            className={`w-full flex items-center justify-center gap-2 py-3 rounded-lg text-sm font-bold transition-all ${
              loading || !disease.trim()
                ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                : "bg-blue-600 text-white hover:bg-blue-700 active:scale-[0.99] shadow-sm"
            }`}
          >
            {loading ? (
              <>
                <Spinner size="sm" />
                Analyzing... ({elapsed}s)
              </>
            ) : (
              <>
                <FlaskConical className="h-4 w-4" />
                Run Analysis
              </>
            )}
          </button>
        </div>
      </Card>

      {/* Pipeline progress */}
      {loading && (
        <Card padding="md">
          <p className="text-xs font-bold text-gray-500 uppercase tracking-wide mb-4">🔬 Pipeline Progress</p>
          <div className="space-y-2.5">
            {STAGES.map((s, i) => (
              <div key={i} className="flex items-center gap-3">
                <div className={`flex-shrink-0 h-6 w-6 rounded-full flex items-center justify-center text-xs font-bold ${
                  i < stageIdx ? "bg-emerald-100 text-emerald-700" :
                  i === stageIdx ? "bg-blue-100 text-blue-700" :
                  "bg-gray-100 text-gray-400"
                }`}>
                  {i < stageIdx ? <CheckCircle className="h-3.5 w-3.5" /> : i + 1}
                </div>
                <span className={`text-sm flex-1 ${
                  i < stageIdx ? "text-gray-300 line-through" :
                  i === stageIdx ? "text-gray-900 font-medium" :
                  "text-gray-400"
                }`}>
                  {s.label}
                </span>
                {i === stageIdx && <Spinner size="sm" className="flex-shrink-0" />}
                {i < stageIdx && <CheckCircle className="h-4 w-4 text-emerald-500 flex-shrink-0" />}
              </div>
            ))}
          </div>
          <div className="mt-4 bg-gray-100 rounded-full h-1.5">
            <div
              className="bg-blue-500 h-1.5 rounded-full transition-all"
              style={{ width:`${((stageIdx + 1) / STAGES.length) * 100}%` }}
            />
          </div>
          <p className="text-xs text-gray-400 mt-2">Typically 60–100 seconds. Cached results return instantly.</p>
        </Card>
      )}

      {/* What the pipeline does */}
      {!loading && (
        <Card padding="md">
          <p className="text-xs font-bold text-gray-500 uppercase tracking-wide mb-3">What the pipeline does</p>
          <div className="space-y-2">
            {[
              "Fetches protein targets from OpenTargets GraphQL API",
              "Maps FDA FAERS adverse event signals per drug",
              "Retrieves PubMed + Semantic Scholar papers",
              "Runs causal reasoning analysis on paper evidence",
              "Generates hypotheses with 6 GPT-4o-mini passes",
              "Computes GO/NO-GO with 9-stage scoring pipeline",
              "Predicts failure risks + time-to-market estimate",
              "Generates literature review + executive summaries",
              "Updates persistent knowledge graph (cross-disease)",
            ].map((step, i) => (
              <div key={i} className="flex items-start gap-2 text-sm text-gray-600">
                <Zap className="h-3.5 w-3.5 text-blue-400 flex-shrink-0 mt-0.5" />
                {step}
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  )
}

export default function AnalysisPage() {
  return (
    <Suspense fallback={<div className="flex justify-center py-16"><Spinner size="lg" /></div>}>
      <AnalysisForm />
    </Suspense>
  )
}