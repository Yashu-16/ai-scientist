// components/ui/index.tsx
// All primitive UI components

import React from "react"

// ── Card ──────────────────────────────────────────────────────
export function Card({
  children, className = "", padding = "md"
}: {
  children: React.ReactNode; className?: string; padding?: "sm"|"md"|"lg"|"none"
}) {
  const p = { sm:"p-4", md:"p-5", lg:"p-6", none:"" }[padding]
  return (
    <div className={`bg-white rounded-xl border border-gray-200 shadow-sm ${p} ${className}`}>
      {children}
    </div>
  )
}

export function CardTitle({ children, className="" }: { children: React.ReactNode; className?: string }) {
  return <p className={`text-xs font-medium text-gray-500 uppercase tracking-wide mb-1 ${className}`}>{children}</p>
}

// ── Badge ─────────────────────────────────────────────────────
type BadgeVariant = "green"|"yellow"|"red"|"blue"|"purple"|"gray"
const bv: Record<BadgeVariant, string> = {
  green:  "bg-emerald-50 text-emerald-700 ring-emerald-200",
  yellow: "bg-amber-50 text-amber-700 ring-amber-200",
  red:    "bg-red-50 text-red-700 ring-red-200",
  blue:   "bg-blue-50 text-blue-700 ring-blue-200",
  purple: "bg-purple-50 text-purple-700 ring-purple-200",
  gray:   "bg-gray-50 text-gray-600 ring-gray-200",
}

export function Badge({
  label, variant="gray", size="md"
}: {
  label: string; variant?: BadgeVariant; size?: "sm"|"md"
}) {
  return (
    <span className={`inline-flex items-center rounded-full font-medium ring-1 ${bv[variant]} ${size==="sm" ? "px-2 py-0.5 text-xs" : "px-2.5 py-1 text-xs"}`}>
      {label}
    </span>
  )
}

export function riskVariant(risk: string): BadgeVariant {
  return risk==="High" ? "red" : risk==="Medium" ? "yellow" : risk==="Low" ? "green" : "gray"
}
export function evidenceVariant(label: string): BadgeVariant {
  return label==="Strong" ? "green" : label==="Moderate" ? "yellow" : "red"
}

// ── Spinner ───────────────────────────────────────────────────
export function Spinner({ size="md", className="" }: { size?: "sm"|"md"|"lg"; className?: string }) {
  const s = { sm:"h-4 w-4 border-2", md:"h-7 w-7 border-2", lg:"h-10 w-10 border-2" }[size]
  return <div className={`animate-spin rounded-full border-gray-200 border-t-blue-600 ${s} ${className}`} />
}

// ── Section header ────────────────────────────────────────────
export function SectionHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="mb-5">
      <h2 className="text-base font-semibold text-gray-900">{title}</h2>
      {subtitle && <p className="text-sm text-gray-500 mt-0.5">{subtitle}</p>}
    </div>
  )
}

// ── Score bar ─────────────────────────────────────────────────
export function ScoreBar({ score, color="blue" }: { score: number; color?: string }) {
  const bg = color==="green" ? "bg-emerald-500" : color==="red" ? "bg-red-500" : color==="yellow" ? "bg-amber-500" : "bg-blue-500"
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 bg-gray-100 rounded-full h-1.5">
        <div className={`h-1.5 rounded-full transition-all ${bg}`} style={{ width:`${Math.min(score*100,100)}%` }} />
      </div>
      <span className="text-xs font-medium text-gray-700 w-10 text-right">{Math.round(score*100)}%</span>
    </div>
  )
}

// ── Info row ──────────────────────────────────────────────────
export function InfoRow({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
      <span className="text-xs text-gray-500">{label}</span>
      <span className="text-xs font-medium text-gray-800">{value}</span>
    </div>
  )
}

// ── Expandable section ────────────────────────────────────────
export function ExpandSection({
  title, children, defaultOpen=false, badge
}: {
  title: string; children: React.ReactNode; defaultOpen?: boolean; badge?: React.ReactNode
}) {
  const [open, setOpen] = React.useState(defaultOpen)
  return (
    <div className="border border-gray-100 rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors text-left"
      >
        <span className="text-sm font-medium text-gray-800">{title}</span>
        <div className="flex items-center gap-2">
          {badge}
          <span className="text-gray-400 text-xs">{open ? "▲" : "▼"}</span>
        </div>
      </button>
      {open && <div className="p-4">{children}</div>}
    </div>
  )
}

// ── Empty state ───────────────────────────────────────────────
export function EmptyState({
  icon, title, subtitle, action
}: {
  icon: React.ReactNode; title: string; subtitle?: string; action?: React.ReactNode
}) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="text-gray-200 mb-4">{icon}</div>
      <h3 className="text-base font-semibold text-gray-700 mb-1">{title}</h3>
      {subtitle && <p className="text-sm text-gray-400 max-w-sm mb-4">{subtitle}</p>}
      {action}
    </div>
  )
}

// ── Stat card ─────────────────────────────────────────────────
export function StatCard({
  label, value, sub, color="gray"
}: {
  label: string; value: string|number; sub?: string; color?: string
}) {
  const textColor = color==="green" ? "text-emerald-600" : color==="red" ? "text-red-600" : color==="yellow" ? "text-amber-600" : color==="blue" ? "text-blue-600" : "text-gray-900"
  return (
    <Card padding="md">
      <CardTitle>{label}</CardTitle>
      <p className={`text-2xl font-bold ${textColor}`}>{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </Card>
  )
}