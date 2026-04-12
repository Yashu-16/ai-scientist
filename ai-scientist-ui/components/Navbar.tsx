"use client"
// components/Navbar.tsx
import { useEffect, useState, useRef } from "react"
import { loadAnalysis } from "@/lib/store"
import type { AnalysisResult } from "@/types"
import { GoNoBadge } from "./GoNoBadge"
import { Bell, RefreshCw, FlaskConical, FileText, AlertTriangle, CheckCircle, X, ExternalLink } from "lucide-react"
import Link from "next/link"

// ── Notification Types ─────────────────────────────────────────
type NotificationType = "success" | "info" | "warning" | "paper"

type Notification = {
  id:         string
  type:       NotificationType
  title:      string
  message:    string
  time:       Date
  read:       boolean
  link?:      string
  linkLabel?: string
}

// ── Storage helpers ────────────────────────────────────────────
const STORAGE_KEY = "ais_notifications"

function loadNotifications(): Notification[] {
  if (typeof window === "undefined") return []
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    return JSON.parse(raw).map((n: any) => ({ ...n, time: new Date(n.time) }))
  } catch { return [] }
}

function saveNotifications(notifications: Notification[]) {
  if (typeof window === "undefined") return
  localStorage.setItem(STORAGE_KEY, JSON.stringify(notifications.slice(0, 20)))
}

export function addNotification(notif: Omit<Notification, "id" | "time" | "read">) {
  if (typeof window === "undefined") return
  const newNotif: Notification = {
    ...notif,
    id:   Math.random().toString(36).slice(2),
    time: new Date(),
    read: false,
  }
  saveNotifications([newNotif, ...loadNotifications()])
  window.dispatchEvent(new Event("ais_notification_added"))
}

// ── Time ago ───────────────────────────────────────────────────
function timeAgo(date: Date): string {
  const diff = (Date.now() - date.getTime()) / 1000
  if (diff < 60)    return "just now"
  if (diff < 3600)  return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}

// ── Icon per type ──────────────────────────────────────────────
function NotifIcon({ type }: { type: NotificationType }) {
  if (type === "success") return <CheckCircle   className="h-4 w-4 flex-shrink-0 text-emerald-500" />
  if (type === "warning") return <AlertTriangle className="h-4 w-4 flex-shrink-0 text-amber-500"   />
  if (type === "paper")   return <FileText      className="h-4 w-4 flex-shrink-0 text-blue-500"    />
  return                         <FlaskConical  className="h-4 w-4 flex-shrink-0 text-purple-500"  />
}

// ── Dropdown ───────────────────────────────────────────────────
function NotificationDropdown({
  notifications, onRead, onReadAll, onDelete, onClose,
}: {
  notifications: Notification[]
  onRead:    (id: string) => void
  onReadAll: () => void
  onDelete:  (id: string) => void
  onClose:   () => void
}) {
  const unread = notifications.filter(n => !n.read).length

  return (
    <div className="absolute right-0 top-full mt-2 w-96 bg-white border border-gray-200 rounded-2xl shadow-xl z-50 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 bg-gray-50">
        <div className="flex items-center gap-2">
          <Bell className="h-4 w-4 text-gray-600" />
          <span className="text-sm font-semibold text-gray-900">Notifications</span>
          {unread > 0 && (
            <span className="text-xs bg-blue-600 text-white px-2 py-0.5 rounded-full font-bold">
              {unread}
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {unread > 0 && (
            <button onClick={onReadAll} className="text-xs text-blue-600 hover:text-blue-800 font-medium">
              Mark all read
            </button>
          )}
          <button onClick={onClose} className="p-1 hover:bg-gray-200 rounded-lg transition-colors">
            <X className="h-3.5 w-3.5 text-gray-400" />
          </button>
        </div>
      </div>

      {/* List */}
      <div className="max-h-[420px] overflow-y-auto divide-y divide-gray-50">
        {notifications.length === 0 ? (
          <div className="text-center py-12">
            <Bell className="h-8 w-8 text-gray-200 mx-auto mb-3" />
            <p className="text-sm text-gray-400 font-medium">No notifications yet</p>
            <p className="text-xs text-gray-300 mt-1">Run an analysis to get started</p>
          </div>
        ) : (
          notifications.map(notif => (
            <div
              key={notif.id}
              onClick={() => onRead(notif.id)}
              className={`flex items-start gap-3 px-4 py-3 cursor-pointer hover:bg-gray-50 transition-colors group ${
                !notif.read ? "bg-blue-50/40" : ""
              }`}
            >
              <div className="mt-0.5"><NotifIcon type={notif.type} /></div>

              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between gap-2">
                  <p className={`text-sm font-semibold leading-snug ${
                    !notif.read ? "text-gray-900" : "text-gray-600"
                  }`}>
                    {notif.title}
                  </p>
                  <div className="flex items-center gap-1 flex-shrink-0">
                    <span className="text-[10px] text-gray-400 whitespace-nowrap">
                      {timeAgo(notif.time)}
                    </span>
                    <button
                      onClick={e => { e.stopPropagation(); onDelete(notif.id) }}
                      className="opacity-0 group-hover:opacity-100 p-0.5 hover:bg-gray-200 rounded transition-all"
                    >
                      <X className="h-3 w-3 text-gray-400" />
                    </button>
                  </div>
                </div>
                <p className="text-xs text-gray-500 mt-0.5 leading-relaxed">{notif.message}</p>
                {notif.link && (
                  <Link
                    href={notif.link}
                    onClick={e => e.stopPropagation()}
                    className="inline-flex items-center gap-1 mt-1.5 text-xs text-blue-600 hover:text-blue-800 font-medium"
                  >
                    {notif.linkLabel ?? "View"} →
                  </Link>
                )}
              </div>

              {!notif.read && (
                <div className="h-2 w-2 rounded-full bg-blue-600 flex-shrink-0 mt-1.5" />
              )}
            </div>
          ))
        )}
      </div>

      {/* Footer */}
      {notifications.length > 0 && (
        <div className="px-4 py-2.5 border-t border-gray-100 bg-gray-50">
          <Link
            href="/history"
            onClick={onClose}
            className="text-xs text-blue-600 hover:text-blue-800 font-medium flex items-center gap-1"
          >
            <ExternalLink className="h-3 w-3" />
            View all analyses in History
          </Link>
        </div>
      )}
    </div>
  )
}

// ── Main Navbar ────────────────────────────────────────────────
export function Navbar() {
  const [data, setData]                   = useState<AnalysisResult | null>(null)
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [showDropdown, setShowDropdown]   = useState(false)
  const dropdownRef                       = useRef<HTMLDivElement>(null)

  // Load analysis + fire notification on new analysis
  useEffect(() => {
    setData(loadAnalysis())
    const handler = () => {
      const analysis = loadAnalysis()
      setData(analysis)
      if (analysis) {
        const decision = analysis.decision_summary?.go_no_go?.decision ?? "INVESTIGATE"
        const drug     = analysis.decision_summary?.recommended_drug ?? "Unknown"
        const emoji    = decision === "GO" ? "✅" : decision === "NO-GO" ? "❌" : "🔍"
        addNotification({
          type:      decision === "GO" ? "success" : decision === "NO-GO" ? "warning" : "info",
          title:     `${emoji} ${analysis.disease_name} — ${decision}`,
          message:   `Drug: ${drug} | ${analysis.protein_targets?.length ?? 0} proteins, ${analysis.drugs?.length ?? 0} drugs, ${analysis.papers?.length ?? 0} papers found.`,
          link:      "/hypotheses",
          linkLabel: "View Results",
        })
      }
    }
    window.addEventListener("ais_analysis_updated", handler)
    return () => window.removeEventListener("ais_analysis_updated", handler)
  }, [])

  // Load + sync notifications
  useEffect(() => {
    setNotifications(loadNotifications())
    const handler = () => setNotifications(loadNotifications())
    window.addEventListener("ais_notification_added", handler)
    return () => window.removeEventListener("ais_notification_added", handler)
  }, [])

  // Close on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setShowDropdown(false)
      }
    }
    document.addEventListener("mousedown", handleClick)
    return () => document.removeEventListener("mousedown", handleClick)
  }, [])

  // Check for paper updates notification
  useEffect(() => {
    async function checkUpdates() {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/latest-updates`)
        if (!res.ok) return
        const data = await res.json()
        const total = data?.stats?.total_updates ?? 0
        if (total > 0) {
          const existing = loadNotifications()
          // Only notify once per session (check if already have a paper notification from today)
          const today = new Date().toDateString()
          const alreadyNotified = existing.some(n =>
            n.type === "paper" && new Date(n.time).toDateString() === today
          )
          if (!alreadyNotified) {
            addNotification({
              type:      "paper",
              title:     "📄 New Research Papers",
              message:   `${total} new papers found across tracked diseases. Stay updated with the latest research.`,
              link:      "/hypotheses?tab=updates",
              linkLabel: "View Updates",
          })
          }
        }
      } catch {}
    }
    const timer = setTimeout(checkUpdates, 4000)
    return () => clearTimeout(timer)
  }, [])

  const unread = notifications.filter(n => !n.read).length

  function handleRead(id: string) {
    const updated = notifications.map(n => n.id === id ? { ...n, read: true } : n)
    setNotifications(updated)
    saveNotifications(updated)
  }

  function handleReadAll() {
    const updated = notifications.map(n => ({ ...n, read: true }))
    setNotifications(updated)
    saveNotifications(updated)
  }

  function handleDelete(id: string) {
    const updated = notifications.filter(n => n.id !== id)
    setNotifications(updated)
    saveNotifications(updated)
  }

  return (
    <header className="fixed top-0 left-56 right-0 h-14 bg-white border-b border-gray-100 flex items-center justify-between px-6 z-30 shadow-sm">

      {/* Left — current analysis */}
      <div className="flex items-center gap-3">
        {data ? (
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-400">Analyzing:</span>
            <span className="text-sm font-semibold text-gray-900">{data.disease_name}</span>
            <span className="text-xs text-gray-300">|</span>
            <span className="text-xs text-gray-400">
              {data.protein_targets?.length} proteins · {data.drugs?.length} drugs · {data.papers?.length} papers
            </span>
          </div>
        ) : (
          <span className="text-sm text-gray-400">No analysis loaded</span>
        )}
      </div>

      {/* Right — actions */}
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

        {/* Bell with dropdown */}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setShowDropdown(prev => !prev)}
            className={`relative p-2 rounded-lg transition-colors ${
              showDropdown
                ? "bg-blue-50 text-blue-600"
                : "hover:bg-gray-50 text-gray-400 hover:text-gray-600"
            }`}
          >
            <Bell className="h-4 w-4" />
            {unread > 0 && (
              <span className="absolute -top-0.5 -right-0.5 h-4 w-4 bg-red-500 text-white text-[9px] font-bold rounded-full flex items-center justify-center">
                {unread > 9 ? "9+" : unread}
              </span>
            )}
          </button>

          {showDropdown && (
            <NotificationDropdown
              notifications={notifications}
              onRead={handleRead}
              onReadAll={handleReadAll}
              onDelete={handleDelete}
              onClose={() => setShowDropdown(false)}
            />
          )}
        </div>
      </div>
    </header>
  )
}