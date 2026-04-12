"use client"
import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import {
  Building2, Users, FlaskConical, Mail,
  Shield, Eye, Crown, Loader2, Trash2,
  UserPlus, RefreshCw, CheckCircle
} from "lucide-react"
import Link from "next/link"

const ROLE_COLORS: Record<string, string> = {
  OWNER:  "bg-purple-50 text-purple-700 ring-purple-200",
  ADMIN:  "bg-blue-50 text-blue-700 ring-blue-200",
  MEMBER: "bg-gray-50 text-gray-600 ring-gray-200",
  VIEWER: "bg-amber-50 text-amber-700 ring-amber-200",
}

const ROLE_ICONS: Record<string, React.ElementType> = {
  OWNER:  Crown,
  ADMIN:  Shield,
  MEMBER: Users,
  VIEWER: Eye,
}

type Member = {
  id: string
  name: string
  email: string
  orgRole: string
  analysesUsed: number
  createdAt: string
}

type Invite = {
  id: string
  email: string
  role: string
  createdAt: string
}

type Analysis = {
  id: string
  diseaseName: string
  decision: string
  confidence: number
  createdAt: string
  user: { name: string; email: string }
}

type Org = {
  id: string
  name: string
  slug: string
  plan: string
  analysesUsed: number
  analysesLimit: number
  members: Member[]
  invites: Invite[]
  analyses: Analysis[]
}

export default function OrgDashboard() {
  const router = useRouter()
  const [org, setOrg]               = useState<Org | null>(null)
  const [userRole, setUserRole]     = useState<string | null>(null)
  const [loading, setLoading]       = useState(true)
  const [inviteEmail, setInviteEmail] = useState("")
  const [inviteRole, setInviteRole]   = useState("MEMBER")
  const [inviting, setInviting]       = useState(false)
  const [inviteMsg, setInviteMsg]     = useState("")
  const [inviteError, setInviteError] = useState("")

  async function loadOrg() {
    try {
      const res = await fetch("/api/org")
      const data = await res.json()
      if (!data.org) {
        router.push("/org/create")
        return
      }
      setOrg(data.org)
      setUserRole(data.userOrgRole)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { loadOrg() }, [])

  async function handleInvite(e: React.FormEvent) {
    e.preventDefault()
    setInviting(true)
    setInviteMsg("")
    setInviteError("")

    const res = await fetch("/api/org/invite", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: inviteEmail, role: inviteRole }),
    })
    const data = await res.json()

    if (!res.ok) {
      setInviteError(data.error ?? "Failed to send invite")
    } else {
      setInviteMsg(`Invite sent to ${inviteEmail}`)
      setInviteEmail("")
      loadOrg()
    }
    setInviting(false)
  }

  async function handleRemove(memberId: string) {
    if (!confirm("Remove this member from the organization?")) return
    await fetch(`/api/org/members/${memberId}`, { method: "DELETE" })
    loadOrg()
  }

  async function handleRoleChange(memberId: string, role: string) {
    await fetch(`/api/org/members/${memberId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ role }),
    })
    loadOrg()
  }

  if (loading) return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
    </div>
  )

  if (!org) return null

  const canManage = ["OWNER", "ADMIN"].includes(userRole ?? "")
  const usagePct  = Math.min(Math.round((org.analysesUsed / org.analysesLimit) * 100), 100)

  return (
    <div className="max-w-5xl mx-auto space-y-6">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="h-12 w-12 rounded-xl bg-blue-100 flex items-center justify-center flex-shrink-0">
            <Building2 className="h-6 w-6 text-blue-600" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">{org.name}</h1>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="text-xs bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded-full font-medium">
                {org.plan}
              </span>
              {userRole && (
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ring-1 ${ROLE_COLORS[userRole]}`}>
                  {userRole}
                </span>
              )}
            </div>
          </div>
        </div>
        <button
          onClick={loadOrg}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          title="Refresh"
        >
          <RefreshCw className="h-4 w-4 text-gray-400" />
        </button>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">Members</p>
          <p className="text-3xl font-bold text-gray-900">{org.members.length}</p>
          <p className="text-xs text-gray-400 mt-1">
            {org.invites.length} pending invite{org.invites.length !== 1 ? "s" : ""}
          </p>
        </div>
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">Analyses Used</p>
          <p className="text-3xl font-bold text-gray-900">
            {org.analysesUsed}
            <span className="text-lg text-gray-400">/{org.analysesLimit}</span>
          </p>
          <div className="mt-2 bg-gray-100 rounded-full h-1.5">
            <div
              className={`h-1.5 rounded-full transition-all ${
                usagePct >= 90 ? "bg-red-500" :
                usagePct >= 70 ? "bg-amber-500" : "bg-blue-500"
              }`}
              style={{ width: `${usagePct}%` }}
            />
          </div>
          <p className="text-xs text-gray-400 mt-1">{usagePct}% used</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-xl p-5">
          <p className="text-xs text-gray-400 uppercase tracking-wide mb-1">Plan</p>
          <p className="text-3xl font-bold text-gray-900">{org.plan}</p>
          <p className="text-xs text-blue-500 mt-1 cursor-pointer hover:text-blue-700">
            Upgrade plan →
          </p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-5">

        {/* Members list */}
        <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
            <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
              <Users className="h-4 w-4 text-gray-400" />
              Team Members
            </h3>
            <span className="text-xs text-gray-400">{org.members.length} total</span>
          </div>

          <div className="divide-y divide-gray-50">
            {org.members.map(member => {
              const Icon = ROLE_ICONS[member.orgRole] ?? Users
              return (
                <div key={member.id} className="px-5 py-3 flex items-center justify-between gap-3">
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="h-8 w-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
                      {member.name?.[0]?.toUpperCase() ?? "?"}
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">{member.name}</p>
                      <p className="text-xs text-gray-400 truncate">{member.email}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    {canManage && member.orgRole !== "OWNER" ? (
                      <select
                        value={member.orgRole}
                        onChange={e => handleRoleChange(member.id, e.target.value)}
                        className="text-xs border border-gray-200 rounded-lg px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500"
                      >
                        {["ADMIN","MEMBER","VIEWER"].map(r => (
                          <option key={r} value={r}>{r}</option>
                        ))}
                      </select>
                    ) : (
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ring-1 ${ROLE_COLORS[member.orgRole]}`}>
                        <Icon className="h-3 w-3 inline mr-0.5" />
                        {member.orgRole}
                      </span>
                    )}
                    {canManage && member.orgRole !== "OWNER" && (
                      <button
                        onClick={() => handleRemove(member.id)}
                        className="p-1.5 text-gray-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                        title="Remove member"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    )}
                  </div>
                </div>
              )
            })}
          </div>

          {/* Pending invites */}
          {org.invites.length > 0 && (
            <div className="border-t border-gray-100">
              <p className="px-5 py-2 text-xs font-semibold text-gray-400 uppercase tracking-wide bg-gray-50">
                Pending Invites
              </p>
              {org.invites.map(invite => (
                <div key={invite.id} className="px-5 py-3 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="h-8 w-8 rounded-full bg-gray-100 flex items-center justify-center flex-shrink-0">
                      <Mail className="h-3.5 w-3.5 text-gray-400" />
                    </div>
                    <div>
                      <p className="text-sm text-gray-700">{invite.email}</p>
                      <p className="text-xs text-gray-400">Invited as {invite.role}</p>
                    </div>
                  </div>
                  <span className="text-xs bg-amber-50 text-amber-600 px-2 py-0.5 rounded-full ring-1 ring-amber-200 font-medium">
                    Pending
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right column */}
        <div className="space-y-5">

          {/* Invite form */}
          {canManage && (
            <div className="bg-white border border-gray-200 rounded-xl p-5">
              <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2 mb-4">
                <UserPlus className="h-4 w-4 text-gray-400" />
                Invite Team Member
              </h3>
              <form onSubmit={handleInvite} className="space-y-3">
                {inviteMsg && (
                  <div className="bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-2 text-xs text-emerald-800 flex items-center gap-1.5">
                    <CheckCircle className="h-3.5 w-3.5" />
                    {inviteMsg}
                  </div>
                )}
                {inviteError && (
                  <div className="bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-xs text-red-700">
                    {inviteError}
                  </div>
                )}
                <input
                  type="email"
                  value={inviteEmail}
                  onChange={e => setInviteEmail(e.target.value)}
                  required
                  placeholder="colleague@company.com"
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <div className="flex gap-2">
                  <select
                    value={inviteRole}
                    onChange={e => setInviteRole(e.target.value)}
                    className="flex-1 px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="ADMIN">Admin</option>
                    <option value="MEMBER">Member</option>
                    <option value="VIEWER">Viewer</option>
                  </select>
                  <button
                    type="submit"
                    disabled={inviting || !inviteEmail.trim()}
                    className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white text-sm font-semibold rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                  >
                    {inviting
                      ? <Loader2 className="h-3.5 w-3.5 animate-spin" />
                      : <Mail className="h-3.5 w-3.5" />}
                    {inviting ? "..." : "Invite"}
                  </button>
                </div>

                {/* Role legend */}
                <div className="grid grid-cols-3 gap-2 pt-1">
                  {[
                    { role:"Admin",  desc:"Full access + invite" },
                    { role:"Member", desc:"Run analyses" },
                    { role:"Viewer", desc:"Read only" },
                  ].map(({ role, desc }) => (
                    <div key={role} className="bg-gray-50 rounded-lg p-2 text-center">
                      <p className="text-xs font-semibold text-gray-700">{role}</p>
                      <p className="text-[10px] text-gray-400 mt-0.5">{desc}</p>
                    </div>
                  ))}
                </div>
              </form>
            </div>
          )}

          {/* Recent shared analyses */}
          <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
            <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-gray-900 flex items-center gap-2">
                <FlaskConical className="h-4 w-4 text-gray-400" />
                Recent Analyses
              </h3>
              <Link href="/history" className="text-xs text-blue-500 hover:text-blue-700">
              View all →
              </Link>
            </div>
            <div className="divide-y divide-gray-50">
              {org.analyses.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-sm text-gray-400">No analyses yet</p>
                  <Link href="/analysis" className="text-xs text-blue-500 hover:text-blue-700 mt-1 block">
                    Run first analysis →
                  </Link>
                </div>
              ) : org.analyses.map(a => {
                const decColor =
                  a.decision === "GO"          ? "text-emerald-700 bg-emerald-50 ring-emerald-200" :
                  a.decision === "NO-GO"       ? "text-red-700 bg-red-50 ring-red-200" :
                  a.decision === "INVESTIGATE" ? "text-amber-700 bg-amber-50 ring-amber-200" :
                  "text-gray-600 bg-gray-50 ring-gray-200"
                return (
                  <div key={a.id} className="px-5 py-3 flex items-center justify-between gap-3">
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">{a.diseaseName}</p>
                      <p className="text-xs text-gray-400">
                        by {a.user?.name} · {new Date(a.createdAt).toLocaleDateString()}
                      </p>
                    </div>
                    {a.decision && (
                      <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ring-1 flex-shrink-0 ${decColor}`}>
                        {a.decision}
                      </span>
                    )}
                  </div>
                )
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Quick links */}
      <div className="flex items-center gap-3 pt-2">
        <Link href="/analysis"
          className="text-xs bg-blue-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-blue-700 transition-colors flex items-center gap-1.5">
          <FlaskConical className="h-3.5 w-3.5" />
          Run Analysis
        </Link>
        <Link href="/"
          className="text-xs border border-gray-200 text-gray-600 px-4 py-2 rounded-lg font-medium hover:bg-gray-50 transition-colors">
          ← Dashboard
        </Link>
      </div>
    </div>
  )
}