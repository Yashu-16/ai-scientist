"use client"
import { useEffect, useState } from "react"
import { signOut } from "next-auth/react"
import { useRouter } from "next/navigation"
import {
  User, Lock, CreditCard, Trash2,
  Loader2, CheckCircle, Eye, EyeOff,
  Shield, ChevronRight, LogOut
} from "lucide-react"
import Link from "next/link"
import { getPlan, PlanId } from "@/lib/plans"
import { clearAnalysis, clearChatHistory } from "@/lib/store"

type Tab = "profile" | "security" | "plan" | "danger"

const TABS: { id: Tab; label: string; icon: React.ElementType }[] = [
  { id: "profile",  label: "Profile",      icon: User       },
  { id: "security", label: "Security",     icon: Lock       },
  { id: "plan",     label: "Plan & Usage", icon: CreditCard },
  { id: "danger",   label: "Danger Zone",  icon: Trash2     },
]

export default function ProfilePage() {
  const router = useRouter()
  const [activeTab, setActiveTab] = useState<Tab>("profile")
  const [userData, setUserData]   = useState<any>(null)
  const [loading, setLoading]     = useState(true)

  useEffect(() => {
    fetch("/api/user/profile")
      .then(r => r.json())
      .then(d => { setUserData(d.user); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  if (loading) return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
    </div>
  )

  if (!userData) return (
    <div className="text-center py-16 text-gray-500">Failed to load profile</div>
  )

  const initials = userData.name
    ?.split(" ")
    .map((n: string) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2) ?? "?"

  const plan        = getPlan(userData.plan as PlanId)
  const usagePct    = Math.min(
    Math.round((userData.analysesUsed / (userData.analysesLimit === 999999 ? 999999 : userData.analysesLimit)) * 100),
    100
  )
  const memberSince = new Date(userData.createdAt).toLocaleDateString("en-IN", {
    month: "long", year: "numeric"
  })

  return (
    <div className="max-w-4xl mx-auto space-y-5">

      {/* Header card */}
      <div className="bg-white border border-gray-200 rounded-2xl p-6">
        <div className="flex items-center gap-5">

          {/* Avatar */}
          <div className="relative flex-shrink-0">
            {userData.image ? (
              <img
                src={userData.image}
                alt={userData.name}
                className="h-20 w-20 rounded-2xl object-cover"
              />
            ) : (
              <div className="h-20 w-20 rounded-2xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-2xl font-black">
                {initials}
              </div>
            )}
            {/* Role indicator dot */}
            <div className={`absolute -bottom-1 -right-1 h-5 w-5 rounded-full border-2 border-white flex items-center justify-center text-[10px] font-bold ${
              userData.role === "ADMIN" ? "bg-purple-500" : "bg-emerald-500"
            }`} />
          </div>

          {/* Info */}
          <div className="flex-1 min-w-0">
            <h1 className="text-xl font-bold text-gray-900">{userData.name}</h1>
            <p className="text-sm text-gray-500">{userData.email}</p>
            <div className="flex flex-wrap items-center gap-2 mt-2">

              {/* Plan badge */}
              <span className={`text-xs px-2.5 py-1 rounded-full font-semibold ring-1 ${
                plan.id === "FREE"
                  ? "bg-gray-50 text-gray-600 ring-gray-200"
                  : "bg-blue-50 text-blue-700 ring-blue-200"
              }`}>
                {plan.name} Plan
              </span>

              {/* Org role badge */}
              {userData.orgRole && (
                <span className="text-xs px-2.5 py-1 rounded-full font-semibold bg-purple-50 text-purple-700 ring-1 ring-purple-200">
                  {userData.orgRole} · {userData.organization?.name}
                </span>
              )}

              {/* Member since */}
              <span className="text-xs text-gray-400">Member since {memberSince}</span>

              {/* Admin Panel link — only visible to admins */}
              {userData.role === "ADMIN" && (
                <Link
                  href="/admin"
                  className="text-xs px-2.5 py-1 rounded-full font-semibold bg-red-50 text-red-600 ring-1 ring-red-200 hover:bg-red-100 transition-colors"
                >
                  Admin Panel →
                </Link>
              )}
            </div>
          </div>

          {/* Sign out */}
          <button
            onClick={() => signOut({ callbackUrl: "/auth/login" })}
            className="flex items-center gap-1.5 text-sm text-gray-400 hover:text-red-500 px-3 py-2 rounded-lg hover:bg-red-50 transition-colors"
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </button>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-5">

        {/* Sidebar tabs */}
        <div className="col-span-1">
          <nav className="bg-white border border-gray-200 rounded-xl overflow-hidden">
            {TABS.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`w-full flex items-center gap-3 px-4 py-3 text-sm font-medium transition-colors border-b border-gray-50 last:border-0 ${
                  activeTab === id
                    ? "bg-blue-50 text-blue-700"
                    : id === "danger"
                    ? "text-red-500 hover:bg-red-50"
                    : "text-gray-600 hover:bg-gray-50"
                }`}
              >
                <Icon className="h-4 w-4 flex-shrink-0" />
                {label}
                {activeTab === id && (
                  <ChevronRight className="h-3 w-3 ml-auto text-blue-400" />
                )}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab content */}
        <div className="col-span-3">
          {activeTab === "profile"  && <ProfileTab user={userData} onUpdate={u => setUserData((p: any) => ({...p, ...u}))} />}
          {activeTab === "security" && <SecurityTab hasPassword={userData.hasPassword} />}
          {activeTab === "plan"     && <PlanTab user={userData} plan={plan} usagePct={usagePct} />}
          {activeTab === "danger"   && <DangerTab hasPassword={userData.hasPassword} router={router} />}
        </div>
      </div>
    </div>
  )
}

// ── Profile Tab ───────────────────────────────────────────────
function ProfileTab({ user, onUpdate }: { user: any; onUpdate: (u: any) => void }) {
  const [name, setName]       = useState(user.name ?? "")
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError]     = useState("")

  async function handleSave(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError("")
    setSuccess(false)

    const res  = await fetch("/api/user/profile", {
      method:  "PATCH",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ name }),
    })
    const data = await res.json()

    if (!res.ok) {
      setError(data.error ?? "Failed to update")
    } else {
      setSuccess(true)
      onUpdate({ name })
      setTimeout(() => setSuccess(false), 3000)
    }
    setLoading(false)
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-5">
      <h3 className="text-sm font-semibold text-gray-900">Profile Information</h3>

      <form onSubmit={handleSave} className="space-y-4">
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}
        {success && (
          <div className="bg-emerald-50 border border-emerald-200 rounded-lg px-4 py-3 text-sm text-emerald-800 flex items-center gap-2">
            <CheckCircle className="h-4 w-4" />
            Profile updated successfully
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Full Name</label>
          <input
            type="text"
            value={name}
            onChange={e => setName(e.target.value)}
            required
            maxLength={50}
            className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Email Address</label>
          <input
            type="email"
            value={user.email ?? ""}
            disabled
            className="w-full px-4 py-2.5 border border-gray-100 rounded-xl text-sm bg-gray-50 text-gray-400 cursor-not-allowed"
          />
          <p className="text-xs text-gray-400 mt-1">Email cannot be changed</p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Account ID</label>
          <input
            value={user.id}
            disabled
            className="w-full px-4 py-2.5 border border-gray-100 rounded-xl text-sm bg-gray-50 text-gray-400 font-mono cursor-not-allowed text-xs"
          />
        </div>

        <button
          type="submit"
          disabled={loading || name === user.name}
          className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white text-sm font-semibold rounded-xl hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {loading && <Loader2 className="h-4 w-4 animate-spin" />}
          {loading ? "Saving..." : "Save Changes"}
        </button>
      </form>
    </div>
  )
}

// ── Security Tab ──────────────────────────────────────────────
function SecurityTab({ hasPassword }: { hasPassword: boolean }) {
  const [current, setCurrent] = useState("")
  const [newPw, setNewPw]     = useState("")
  const [confirm, setConfirm] = useState("")
  const [showCur, setShowCur] = useState(false)
  const [showNew, setShowNew] = useState(false)
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState(false)
  const [error, setError]     = useState("")

  const pwStrength = newPw.length === 0 ? 0 : newPw.length < 8 ? 1 : newPw.length < 12 ? 2 : 3
  const pwColor    = ["bg-gray-200","bg-red-400","bg-amber-400","bg-emerald-400"][pwStrength]
  const pwLabel    = ["","Too short","Good","Strong"][pwStrength]

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (newPw !== confirm) { setError("Passwords don't match"); return }
    setLoading(true)
    setError("")
    setSuccess(false)

    const res  = await fetch("/api/user/password", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ currentPassword: current, newPassword: newPw }),
    })
    const data = await res.json()

    if (!res.ok) {
      setError(data.error ?? "Failed to change password")
    } else {
      setSuccess(true)
      setCurrent(""); setNewPw(""); setConfirm("")
      setTimeout(() => setSuccess(false), 3000)
    }
    setLoading(false)
  }

  if (!hasPassword) return (
    <div className="bg-white border border-gray-200 rounded-xl p-6">
      <h3 className="text-sm font-semibold text-gray-900 mb-3">Security</h3>
      <div className="bg-blue-50 border border-blue-100 rounded-xl p-4 flex items-start gap-3">
        <Shield className="h-5 w-5 text-blue-500 flex-shrink-0 mt-0.5" />
        <div>
          <p className="text-sm font-semibold text-blue-800">Social login account</p>
          <p className="text-xs text-blue-600 mt-1 leading-relaxed">
            You signed in with Google or GitHub. Password management is handled by your social provider.
          </p>
        </div>
      </div>
    </div>
  )

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6 space-y-5">
      <h3 className="text-sm font-semibold text-gray-900">Change Password</h3>
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}
        {success && (
          <div className="bg-emerald-50 border border-emerald-200 rounded-lg px-4 py-3 text-sm text-emerald-800 flex items-center gap-2">
            <CheckCircle className="h-4 w-4" />
            Password changed successfully
          </div>
        )}

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Current Password</label>
          <div className="relative">
            <input
              type={showCur ? "text" : "password"}
              value={current}
              onChange={e => setCurrent(e.target.value)}
              required
              placeholder="••••••••"
              className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 pr-10"
            />
            <button type="button" onClick={() => setShowCur(!showCur)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
              {showCur ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">New Password</label>
          <div className="relative">
            <input
              type={showNew ? "text" : "password"}
              value={newPw}
              onChange={e => setNewPw(e.target.value)}
              required
              minLength={8}
              placeholder="Min 8 characters"
              className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 pr-10"
            />
            <button type="button" onClick={() => setShowNew(!showNew)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600">
              {showNew ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          {newPw && (
            <div className="mt-2">
              <div className="flex gap-1">
                {[1,2,3].map(i => (
                  <div key={i} className={`h-1 flex-1 rounded-full ${i <= pwStrength ? pwColor : "bg-gray-200"}`} />
                ))}
              </div>
              <p className="text-xs text-gray-400 mt-1">{pwLabel}</p>
            </div>
          )}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Confirm New Password</label>
          <input
            type="password"
            value={confirm}
            onChange={e => setConfirm(e.target.value)}
            required
            placeholder="••••••••"
            className={`w-full px-4 py-2.5 border rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              confirm && confirm !== newPw ? "border-red-300 bg-red-50" : "border-gray-200"
            }`}
          />
          {confirm && confirm !== newPw && (
            <p className="text-xs text-red-500 mt-1">Passwords don't match</p>
          )}
        </div>

        <button
          type="submit"
          disabled={loading || !current || !newPw || newPw !== confirm}
          className="flex items-center gap-2 px-5 py-2.5 bg-blue-600 text-white text-sm font-semibold rounded-xl hover:bg-blue-700 disabled:opacity-50 transition-colors"
        >
          {loading && <Loader2 className="h-4 w-4 animate-spin" />}
          {loading ? "Changing..." : "Change Password"}
        </button>
      </form>
    </div>
  )
}

// ── Plan Tab ──────────────────────────────────────────────────
function PlanTab({ user, plan, usagePct }: { user: any; plan: any; usagePct: number }) {
  return (
    <div className="space-y-4">
      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <h3 className="text-sm font-semibold text-gray-900 mb-4">Current Plan</h3>
        <div className="flex items-center justify-between mb-5">
          <div>
            <p className="text-2xl font-black text-gray-900">{plan.name}</p>
            <p className="text-sm text-gray-500 mt-0.5">
              {plan.price === 0 ? "Free forever" : `₹${plan.price.toLocaleString("en-IN")}/month`}
            </p>
          </div>
          {plan.id !== "PRO" && plan.id !== "ENTERPRISE" && (
            <Link href="/pricing"
              className="flex items-center gap-1.5 text-sm bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-blue-700 transition-colors">
              Upgrade Plan
            </Link>
          )}
        </div>
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <p className="text-xs text-gray-500 font-medium">Analyses used this month</p>
            <p className="text-xs font-bold text-gray-700">
              {user.analysesUsed} / {user.analysesLimit === 999999 ? "∞" : user.analysesLimit}
            </p>
          </div>
          <div className="bg-gray-100 rounded-full h-2.5">
            <div
              className={`h-2.5 rounded-full transition-all ${
                usagePct >= 90 ? "bg-red-500" : usagePct >= 70 ? "bg-amber-500" : "bg-blue-500"
              }`}
              style={{ width: `${usagePct}%` }}
            />
          </div>
          {usagePct >= 80 && (
            <p className="text-xs text-amber-600 mt-1.5">
              ⚠️ Running low —{" "}
              <Link href="/pricing" className="underline font-medium">upgrade for more</Link>
            </p>
          )}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3">
        {[
          { label:"Total Analyses",      value: user._count?.analyses ?? 0,                                color:"text-blue-600"   },
          { label:"Analyses This Month", value: user.analysesUsed ?? 0,                                   color:"text-purple-600" },
          { label:"Plan Limit",          value: user.analysesLimit === 999999 ? "∞" : user.analysesLimit, color:"text-gray-900"   },
        ].map(({ label, value, color }) => (
          <div key={label} className="bg-white border border-gray-200 rounded-xl p-4">
            <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">{label}</p>
            <p className={`text-2xl font-bold ${color}`}>{value}</p>
          </div>
        ))}
      </div>

      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <h4 className="text-sm font-semibold text-gray-900 mb-3">
          Your {plan.name} plan includes:
        </h4>
        <ul className="space-y-2">
          {plan.features.map((f: string) => (
            <li key={f} className="flex items-center gap-2 text-sm text-gray-600">
              <CheckCircle className="h-4 w-4 text-emerald-500 flex-shrink-0" />
              {f}
            </li>
          ))}
        </ul>
        {plan.id === "FREE" && (
          <div className="mt-4 pt-4 border-t border-gray-100">
            <Link href="/pricing" className="text-sm text-blue-600 font-semibold hover:text-blue-800">
              View all plans & upgrade →
            </Link>
          </div>
        )}
      </div>

      <Link href="/billing"
        className="flex items-center justify-between bg-white border border-gray-200 rounded-xl px-5 py-4 hover:border-blue-200 hover:bg-blue-50 transition-colors group">
        <div className="flex items-center gap-3">
          <CreditCard className="h-5 w-5 text-gray-400 group-hover:text-blue-500" />
          <div>
            <p className="text-sm font-semibold text-gray-900">Billing & Invoices</p>
            <p className="text-xs text-gray-400">View payment history and invoices</p>
          </div>
        </div>
        <ChevronRight className="h-4 w-4 text-gray-300 group-hover:text-blue-400" />
      </Link>
    </div>
  )
}

// ── Danger Zone Tab ───────────────────────────────────────────
function DangerTab({
  hasPassword,
  router
}: {
  hasPassword: boolean
  router: ReturnType<typeof useRouter>
}) {
  const [password, setPassword]       = useState("")
  const [confirm, setConfirm]         = useState("")
  const [loading, setLoading]         = useState(false)
  const [error, setError]             = useState("")
  const [showConfirm, setShowConfirm] = useState(false)

  async function handleDelete(e: React.FormEvent) {
    e.preventDefault()
    if (confirm !== "DELETE MY ACCOUNT") {
      setError('Please type "DELETE MY ACCOUNT" exactly')
      return
    }
    setLoading(true)
    setError("")

    const res  = await fetch("/api/user/delete", {
      method:  "DELETE",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ password, confirmation: confirm }),
    })
    const data = await res.json()

    if (!res.ok) {
      setError(data.error ?? "Failed to delete account")
      setLoading(false)
      return
    }

    clearAnalysis()
    clearChatHistory()
    router.push("/auth/login")
  }

  return (
    <div className="space-y-4">
      <div className="bg-red-50 border border-red-200 rounded-xl p-5">
        <div className="flex items-start gap-3">
          <Trash2 className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="text-sm font-bold text-red-800">Delete Account</h3>
            <p className="text-sm text-red-600 mt-1 leading-relaxed">
              This will permanently delete your account and all associated data including
              analyses, organization membership, and billing history.
              <strong> This action cannot be undone.</strong>
            </p>
          </div>
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-xl p-5">
        <h4 className="text-sm font-semibold text-gray-900 mb-3">
          What will be permanently deleted:
        </h4>
        <ul className="space-y-2">
          {[
            "Your account and profile",
            "All analyses and saved results",
            "Organization membership",
            "API keys and sessions",
            "Billing history and invoices",
          ].map(item => (
            <li key={item} className="flex items-center gap-2 text-sm text-gray-600">
              <span className="h-1.5 w-1.5 rounded-full bg-red-400 flex-shrink-0" />
              {item}
            </li>
          ))}
        </ul>
      </div>

      {!showConfirm ? (
        <button
          onClick={() => setShowConfirm(true)}
          className="flex items-center gap-2 px-5 py-2.5 bg-red-600 text-white text-sm font-semibold rounded-xl hover:bg-red-700 transition-colors"
        >
          <Trash2 className="h-4 w-4" />
          Delete My Account
        </button>
      ) : (
        <div className="bg-white border border-red-200 rounded-xl p-5">
          <h4 className="text-sm font-bold text-gray-900 mb-4">Confirm account deletion</h4>
          <form onSubmit={handleDelete} className="space-y-4">
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-700">
                {error}
              </div>
            )}

            {hasPassword && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Enter your password to confirm
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  required
                  placeholder="••••••••"
                  className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-red-500"
                />
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">
                Type{" "}
                <code className="bg-gray-100 px-1.5 py-0.5 rounded text-red-600 font-mono">
                  DELETE MY ACCOUNT
                </code>{" "}
                to confirm
              </label>
              <input
                type="text"
                value={confirm}
                onChange={e => setConfirm(e.target.value)}
                placeholder="DELETE MY ACCOUNT"
                className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-red-500 font-mono"
              />
            </div>

            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => { setShowConfirm(false); setError("") }}
                className="flex-1 py-2.5 border border-gray-200 text-gray-600 text-sm font-semibold rounded-xl hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading || confirm !== "DELETE MY ACCOUNT"}
                className="flex-1 flex items-center justify-center gap-2 py-2.5 bg-red-600 text-white text-sm font-semibold rounded-xl hover:bg-red-700 disabled:opacity-50 transition-colors"
              >
                {loading && <Loader2 className="h-4 w-4 animate-spin" />}
                {loading ? "Deleting..." : "Permanently Delete"}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  )
}