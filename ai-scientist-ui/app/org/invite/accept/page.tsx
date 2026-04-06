"use client"
import { useEffect, useState, Suspense } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import { Loader2, CheckCircle, XCircle } from "lucide-react"
import Link from "next/link"

function AcceptInviteContent() {
  const params  = useSearchParams()
  const router  = useRouter()
  const token   = params.get("token")

  const [status, setStatus]   = useState<"loading" | "success" | "error">("loading")
  const [message, setMessage] = useState("")
  const [orgName, setOrgName] = useState("")

  useEffect(() => {
    if (!token) {
      setStatus("error")
      setMessage("Invalid invite link — token is missing.")
      return
    }

    fetch("/api/org/invite/accept", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token }),
    })
      .then(async res => {
        const data = await res.json()
        if (res.ok) {
          setOrgName(data.orgName ?? "your organization")
          setStatus("success")
          setTimeout(() => router.push("/org/dashboard"), 2500)
        } else {
          setStatus("error")
          setMessage(data.error ?? "Failed to accept invite. The link may have expired.")
        }
      })
      .catch(() => {
        setStatus("error")
        setMessage("Something went wrong. Please try again.")
      })
  }, [token, router])

  return (
    <div className="min-h-[60vh] flex items-center justify-center px-4">
      <div className="text-center max-w-sm w-full">

        {status === "loading" && (
          <div className="space-y-4">
            <div className="flex justify-center">
              <Loader2 className="h-14 w-14 animate-spin text-blue-600" />
            </div>
            <h2 className="text-xl font-bold text-gray-900">Accepting invitation...</h2>
            <p className="text-sm text-gray-500">Please wait a moment.</p>
          </div>
        )}

        {status === "success" && (
          <div className="space-y-4">
            <div className="flex justify-center">
              <CheckCircle className="h-16 w-16 text-emerald-500" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900">Welcome to the team!</h2>
            <p className="text-sm text-gray-500">
              You've joined <strong>{orgName}</strong>. Redirecting to your
              organization dashboard...
            </p>
            <div className="flex justify-center">
              <Loader2 className="h-4 w-4 animate-spin text-gray-400" />
            </div>
          </div>
        )}

        {status === "error" && (
          <div className="space-y-4">
            <div className="flex justify-center">
              <XCircle className="h-16 w-16 text-red-500" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900">Invite Error</h2>
            <p className="text-sm text-gray-500 leading-relaxed">{message}</p>
            <div className="flex flex-col gap-2">
              <Link
                href="/auth/login"
                className="inline-flex items-center justify-center gap-2 bg-blue-600 text-white px-6 py-2.5 rounded-xl text-sm font-semibold hover:bg-blue-700 transition-colors"
              >
                Sign in and try again
              </Link>
              <Link
                href="/"
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Go to dashboard
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default function AcceptInvitePage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-[60vh] flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
        </div>
      }
    >
      <AcceptInviteContent />
    </Suspense>
  )
}