"use client"
// app/page.tsx — Landing page (root route)
import Link from "next/link"
import { useState, useEffect } from "react"
import {
  FlaskConical, Dna, TrendingUp, Shield,
  ChevronRight, BarChart2,
  FileText, MessageSquare, RefreshCw, Zap, Star
} from "lucide-react"

const DISEASES_CYCLE = [
  "Alzheimer disease", "Parkinson disease", "breast cancer",
  "type 2 diabetes", "rheumatoid arthritis", "lung cancer",
]

const FEATURES = [
  { icon: Dna,           title: "9-Stage Analysis Pipeline",   desc: "Protein targets, drug mapping, causal reasoning, hypothesis generation — all automated via OpenTargets, FDA FAERS, PubMed, and GPT-4o-mini.", color: "bg-blue-50 text-blue-600" },
  { icon: Shield,        title: "GO / NO-GO Decision Engine",  desc: "Quantified confidence scores with supporting and blocking factors. Know exactly why a hypothesis is recommended or rejected.",             color: "bg-emerald-50 text-emerald-600" },
  { icon: TrendingUp,    title: "Failure Prediction",          desc: "AI-powered failure risk scoring with historical context, predicted failure modes, and recommended safeguards before you invest.",          color: "bg-purple-50 text-purple-600" },
  { icon: RefreshCw,     title: "Drug Repurposing",            desc: "Find new disease indications for existing drugs. Mechanistic analysis with shared pathways and evidence levels.",                           color: "bg-amber-50 text-amber-600" },
  { icon: MessageSquare, title: "Causyn AI Chat",           desc: "Ask anything about your analysis. Context-aware answers referencing actual scores, proteins, drugs, and evidence.",                       color: "bg-pink-50 text-pink-600" },
  { icon: FileText,      title: "PDF Research Reports",        desc: "Professional 9-section reports with executive decision, evidence analysis, risk tables, and hypothesis comparison.",                       color: "bg-slate-50 text-slate-600" },
]

const STATS = [
  { value:"19+", label:"API Endpoints" },
  { value:"10",  label:"Analysis Tabs" },
  { value:"6",   label:"LLM Passes/Run" },
  { value:"5",   label:"Scientific APIs" },
]

const PIPELINE = [
  "Protein targets","Drug mapping","FDA signals",
  "Paper retrieval","Causal reasoning","Hypotheses",
  "GO/NO-GO","Failure prediction","Exec summary"
]

export default function LandingPage() {
  const [diseaseIdx, setDiseaseIdx] = useState(0)

  useEffect(() => {
    const iv = setInterval(() => setDiseaseIdx(i => (i+1) % DISEASES_CYCLE.length), 2200)
    return () => clearInterval(iv)
  }, [])

  return (
    <div className="min-h-screen bg-white overflow-x-hidden">

      {/* NAV */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="h-8 w-8 rounded-lg bg-blue-600 flex items-center justify-center">
              <Dna className="h-4 w-4 text-white" />
            </div>
            <div>
              <p className="text-sm font-bold text-gray-900 leading-none">Causyn AI</p>
              <p className="text-[10px] text-gray-400">Drug Discovery</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/auth/login"
               className="text-sm text-gray-500 hover:text-gray-800 transition-colors hidden sm:block font-medium">
              Sign In
            </Link>
            <Link href="/auth/register"
              className="flex items-center gap-1.5 text-sm font-bold bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors shadow-sm">
              <FlaskConical className="h-3.5 w-3.5" />
              Get Started Free
            </Link>
          </div>
        </div>
      </nav>

      {/* HERO */}
      <section className="pt-36 pb-24 px-6 relative overflow-hidden">
        <div className="absolute top-20 left-1/4 w-96 h-96 bg-blue-100 rounded-full blur-3xl opacity-40 -z-10" />
        <div className="absolute top-40 right-1/4 w-72 h-72 bg-purple-100 rounded-full blur-3xl opacity-30 -z-10" />

        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 bg-blue-50 border border-blue-100 rounded-full px-4 py-1.5 mb-6">
            <span className="flex h-2 w-2 rounded-full bg-blue-500 animate-pulse" />
            <span className="text-xs font-bold text-blue-700 uppercase tracking-wide">Decision & Risk Intelligence Platform</span>
          </div>

          <h1 className="text-5xl sm:text-6xl font-black text-gray-900 leading-tight mb-4 tracking-tight">
            Drug Discovery<br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 via-purple-600 to-blue-800">
              Powered by AI
            </span>
          </h1>

          <div className="flex items-center justify-center gap-2 mb-6">
            <span className="text-xl text-gray-400">Analyzing</span>
            <div className="overflow-hidden h-9 min-w-[220px] text-left">
              <div className="transition-transform duration-500 ease-in-out"
                   style={{ transform: `translateY(-${diseaseIdx * 36}px)` }}>
                {DISEASES_CYCLE.map(d => (
                  <p key={d} className="h-9 flex items-center text-xl font-black text-blue-600">{d}</p>
                ))}
              </div>
            </div>
          </div>

          <p className="text-lg text-gray-500 max-w-2xl mx-auto leading-relaxed mb-10">
            A production-grade biomedical AI platform that analyzes protein targets, drug interactions,
            and research literature — delivering a quantified GO/NO-GO recommendation in under 90 seconds.
          </p>

          <div className="flex items-center justify-center flex-wrap gap-3">
            <Link href="/auth/register"
              className="flex items-center gap-2 bg-blue-600 text-white px-8 py-3.5 rounded-xl font-black text-sm hover:bg-blue-700 transition-all shadow-lg hover:shadow-blue-200 hover:-translate-y-0.5">
              <Zap className="h-4 w-4" />
              Start Free Analysis
              <ChevronRight className="h-4 w-4" />
            </Link>
            <Link href="/auth/login"
              className="flex items-center gap-2 bg-white border-2 border-gray-200 text-gray-700 px-6 py-3 rounded-xl font-bold text-sm hover:border-blue-300 hover:text-blue-700 transition-all">
              <BarChart2 className="h-4 w-4" />
              Sign In
            </Link>
          </div>

          <p className="text-gray-400 text-xs mt-5">Free plan includes 3 analyses · No credit card required</p>
        </div>
      </section>

      {/* PIPELINE */}
      <section className="py-20 px-6 bg-gray-950">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-10">
            <p className="text-xs font-bold text-blue-400 uppercase tracking-widest mb-2">Automated 9-Stage Pipeline</p>
            <h2 className="text-3xl font-black text-white">Disease name → GO/NO-GO in &lt;90 seconds</h2>
          </div>

          <div className="flex items-start justify-center flex-wrap gap-2">
            {PIPELINE.map((stage, i) => (
              <div key={stage} className="flex items-center gap-2">
                <div className="flex flex-col items-center text-center">
                  <div className="w-11 h-11 rounded-full bg-blue-600/20 border border-blue-500/50 flex items-center justify-center text-blue-300 text-sm font-bold mb-2 hover:bg-blue-600/40 transition-colors">
                    {i+1}
                  </div>
                  <p className="text-[11px] text-gray-400 max-w-[72px] leading-snug">{stage}</p>
                </div>
                {i < PIPELINE.length-1 && <div className="w-5 h-px bg-blue-800 mb-5 flex-shrink-0" />}
              </div>
            ))}
          </div>

          <div className="grid grid-cols-4 gap-4 mt-14">
            {STATS.map(({ value, label }) => (
              <div key={label} className="bg-white/5 border border-white/10 rounded-2xl p-5 text-center hover:bg-white/10 transition-colors">
                <p className="text-4xl font-black text-white mb-1">{value}</p>
                <p className="text-xs text-gray-400">{label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FEATURES */}
      <section className="py-20 px-6 bg-white">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <p className="text-xs font-bold text-blue-600 uppercase tracking-widest mb-2">Full feature set</p>
            <h2 className="text-3xl font-black text-gray-900">Not a wrapper. A platform.</h2>
            <p className="text-gray-500 mt-3 max-w-xl mx-auto text-sm leading-relaxed">
              Unlike simple LLM wrappers, Causyn AI runs a real 9-stage scientific pipeline with 5 live APIs,
              quantified scoring, persistent knowledge graphs, and professional PDF export.
            </p>
          </div>
          <div className="grid grid-cols-3 gap-5">
            {FEATURES.map(({ icon:Icon, title, desc, color }) => (
              <div key={title} className="bg-white border border-gray-100 rounded-2xl p-6 hover:border-blue-200 hover:shadow-lg hover:shadow-blue-50/80 transition-all group cursor-default">
                <div className={`w-11 h-11 rounded-xl flex items-center justify-center mb-4 ${color}`}>
                  <Icon className="h-5 w-5" />
                </div>
                <h3 className="text-sm font-bold text-gray-900 mb-2 group-hover:text-blue-700 transition-colors">{title}</h3>
                <p className="text-xs text-gray-500 leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* DATA SOURCES */}
      <section className="py-16 px-6 bg-gray-50">
        <div className="max-w-4xl mx-auto text-center">
          <p className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-8">Powered by real scientific APIs</p>
          <div className="flex flex-wrap items-stretch justify-center gap-3">
            {[
              { name:"OpenTargets",      sub:"Protein targets",       color:"bg-blue-600" },
              { name:"FDA FAERS",        sub:"Adverse events",        color:"bg-red-600" },
              { name:"PubMed",           sub:"Literature",            color:"bg-green-600" },
              { name:"Semantic Scholar", sub:"Paper summaries",       color:"bg-purple-600" },
              { name:"AlphaFold",        sub:"Structural confidence", color:"bg-amber-600" },
              { name:"GPT-4o-mini",      sub:"Hypothesis generation", color:"bg-slate-700" },
            ].map(({ name, sub, color }) => (
              <div key={name} className="bg-white border border-gray-200 rounded-xl px-5 py-4 text-center shadow-sm hover:shadow-md hover:border-gray-300 transition-all min-w-[140px]">
                <div className={`w-3 h-3 rounded-full ${color} mx-auto mb-2`} />
                <p className="text-sm font-bold text-gray-800">{name}</p>
                <p className="text-xs text-gray-400 mt-0.5">{sub}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* TABS PREVIEW */}
      <section className="py-20 px-6 bg-white">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-10">
            <p className="text-xs font-bold text-blue-600 uppercase tracking-widest mb-2">10 analysis tabs</p>
            <h2 className="text-3xl font-black text-gray-900">Every angle of drug discovery covered</h2>
          </div>
          <div className="grid grid-cols-5 gap-3">
            {[
              { icon:"💡", label:"Hypotheses",      desc:"Ranked + GO/NO-GO" },
              { icon:"🧬", label:"Proteins",        desc:"OpenTargets + AlphaFold" },
              { icon:"💊", label:"Drugs",           desc:"FDA + Competition" },
              { icon:"⚠️", label:"Risk Analysis",   desc:"Adverse events" },
              { icon:"🕸️", label:"Network",         desc:"Interactive graph" },
              { icon:"📡", label:"Live Updates",    desc:"Daily PubMed" },
              { icon:"📄", label:"Literature",      desc:"AI-generated review" },
              { icon:"🤖", label:"Ask AI",          desc:"Context-aware chat" },
              { icon:"🔥", label:"Trends",          desc:"Emerging signals" },
              { icon:"🔁", label:"Repurpose",       desc:"New indications" },
            ].map(({ icon, label, desc }) => (
              <div key={label} className="bg-gray-50 border border-gray-100 rounded-xl p-4 text-center hover:border-blue-200 hover:bg-blue-50 transition-all cursor-default group">
                <div className="text-2xl mb-2">{icon}</div>
                <p className="text-xs font-bold text-gray-800 group-hover:text-blue-700 transition-colors">{label}</p>
                <p className="text-[10px] text-gray-400 mt-0.5">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* PRICING TEASER */}
      <section className="py-16 px-6 bg-gray-50">
        <div className="max-w-3xl mx-auto text-center">
          <p className="text-xs font-bold text-blue-600 uppercase tracking-widest mb-4">Simple pricing</p>
          <h2 className="text-3xl font-black text-gray-900 mb-3">Start free, upgrade when ready</h2>
          <p className="text-gray-500 text-sm mb-8">No credit card required for the free plan</p>
          <div className="grid grid-cols-3 gap-4 mb-8">
            {[
              { plan:"Free",         price:"$0",    analyses:"3 analyses/month",  cta:"Get Started", highlight: false },
              { plan:"Academic",     price:"$25/mo",analyses:"50 analyses/month", cta:"Start Trial", highlight: true  },
              { plan:"Professional", price:"$99/mo",analyses:"Unlimited",         cta:"Start Trial", highlight: false },
            ].map(({ plan, price, analyses, cta, highlight }) => (
              <div key={plan} className={`bg-white rounded-2xl p-6 border ${highlight ? "border-blue-500 ring-2 ring-blue-100" : "border-gray-200"}`}>
                <p className="text-sm font-bold text-gray-900 mb-1">{plan}</p>
                <p className={`text-2xl font-black mb-1 ${highlight ? "text-blue-600" : "text-gray-900"}`}>{price}</p>
                <p className="text-xs text-gray-400 mb-4">{analyses}</p>
                <Link href="/auth/register"
                  className={`block text-center py-2 rounded-xl text-xs font-bold transition-colors ${
                    highlight
                      ? "bg-blue-600 text-white hover:bg-blue-700"
                      : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                  }`}>
                  {cta}
                </Link>
              </div>
            ))}
          </div>
          <Link href="/pricing" className="text-sm text-blue-600 hover:text-blue-800 font-medium">
            View full pricing →
          </Link>
        </div>
      </section>

      {/* CTA BOTTOM */}
      <section className="py-24 px-6 bg-gradient-to-br from-blue-600 to-blue-900 relative overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-blue-500/20 to-transparent" />
        <div className="max-w-2xl mx-auto text-center relative">
          <div className="flex justify-center gap-1 mb-5">
            {[...Array(5)].map((_,i) => (
              <Star key={i} className="h-5 w-5 text-yellow-300 fill-yellow-300" />
            ))}
          </div>
          <h2 className="text-4xl font-black text-white mb-4 leading-tight">
            Ready to discover your next drug candidate?
          </h2>
          <p className="text-blue-200 mb-10 leading-relaxed">
            Create a free account and get a full GO/NO-GO recommendation with protein targets,
            drug risk profiles, failure predictions, and a downloadable PDF report — in under 90 seconds.
          </p>
          <div className="flex items-center justify-center gap-3 flex-wrap">
            <Link href="/auth/register"
              className="inline-flex items-center gap-2 bg-white text-blue-700 px-10 py-4 rounded-2xl font-black text-base hover:bg-blue-50 transition-all shadow-2xl hover:-translate-y-1 active:translate-y-0">
              <FlaskConical className="h-5 w-5" />
              Create Free Account
              <ChevronRight className="h-5 w-5" />
            </Link>
            <Link href="/auth/login"
              className="inline-flex items-center gap-2 bg-blue-700/50 text-white px-6 py-4 rounded-2xl font-bold text-base hover:bg-blue-700 transition-all border border-blue-500">
              Sign In
            </Link>
          </div>
          <p className="text-blue-300 text-xs mt-5">Free plan · 3 analyses/month · No credit card required</p>
        </div>
      </section>

      {/* FOOTER */}
      <footer className="py-8 px-6 bg-gray-950 border-t border-gray-800">
        <div className="max-w-5xl mx-auto flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="h-6 w-6 rounded bg-blue-600 flex items-center justify-center">
              <Dna className="h-3 w-3 text-white" />
            </div>
            <p className="text-sm font-semibold text-gray-400">Causyn AI</p>
          </div>
          <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500">
            <span>FastAPI + Next.js + GPT-4o-mini</span>
            <span>·</span>
            <Link href="/terms"   className="hover:text-gray-300 transition-colors">Terms</Link>
            <span>·</span>
            <Link href="/privacy" className="hover:text-gray-300 transition-colors">Privacy</Link>
            <span>·</span>
            <span>For exploratory research only. Not for clinical use.</span>
          </div>
        </div>
      </footer>
    </div>
  )
}