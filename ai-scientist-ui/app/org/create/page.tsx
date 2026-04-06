"use client"
import { useState } from "react"
import { useRouter } from "next/navigation"
import { Building2, Loader2 } from "lucide-react"
import Link from "next/link"

export default function CreateOrgPage() {
  const router = useRouter()
  const [name, setName]                 = useState("")
  const [billingEmail, setBillingEmail] = useState("")
  const [loading, setLoading]           = useState(false)
  const [error, setError]               = useState("")

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError("")

    const res = await fetch("/api/org/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, billingEmail }),
    })

    const data = await res.json()

    if (!res.ok) {
      setError(data.error ?? "Failed to create organization")
      setLoading(false)
      return
    }

    router.push("/org/dashboard")
    router.refresh()
  }

  const slug = name.toLowerCase().replace(/[^a-z0-9]/g, "-").replace(/-+/g, "-")

  return (
    <div className="max-w-lg mx-auto space-y-6">
      <div>
        <h1 className="text-xl font-bold text-gray-900">Create Organization</h1>
        <p className="text-sm text-gray-500 mt-1">
          Set up a team workspace to share analyses and collaborate
        </p>
      </div>

      <div className="bg-white border border-gray-200 rounded-2xl p-8">
        <form onSubmit={handleSubmit} className="space-y-5">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Organization Name
            </label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              required
              placeholder="e.g. Biocon Research Lab"
              className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {name && (
              <p className="text-xs text-gray-400 mt-1">
                Slug: <code className="bg-gray-100 px-1 rounded">{slug}</code>
              </p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Billing Email{" "}
              <span className="text-gray-400 font-normal">(optional)</span>
            </label>
            <input
              type="email"
              value={billingEmail}
              onChange={e => setBillingEmail(e.target.value)}
              placeholder="billing@yourcompany.com"
              className="w-full px-4 py-2.5 border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Plan info */}
          <div className="bg-blue-50 border border-blue-100 rounded-xl p-4">
            <p className="text-sm font-semibold text-blue-800 mb-2">
              Free Organization Plan — included
            </p>
            <ul className="space-y-1.5">
              {[
                "10 shared analyses per month",
                "Up to 5 team members",
                "Shared analysis history",
                "All 10 analysis tabs",
                "Role-based access control",
              ].map(f => (
                <li key={f} className="text-xs text-blue-700 flex items-center gap-1.5">
                  <span className="text-emerald-500 font-bold">✓</span> {f}
                </li>
              ))}
            </ul>
          </div>

          <button
            type="submit"
            disabled={loading || !name.trim()}
            className="w-full flex items-center justify-center gap-2 py-3 bg-blue-600 text-white text-sm font-bold rounded-xl hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {loading
              ? <Loader2 className="h-4 w-4 animate-spin" />
              : <Building2 className="h-4 w-4" />}
            {loading ? "Creating..." : "Create Organization"}
          </button>
        </form>
      </div>

      <p className="text-center text-sm text-gray-500">
        <Link href="/" className="text-blue-600 hover:text-blue-800">
          ← Back to dashboard
        </Link>
      </p>
    </div>
  )
}