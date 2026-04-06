"use client"
import Link from "next/link"
import { useSearchParams } from "next/navigation"
import { Suspense } from "react"

function ErrorContent() {
  const params = useSearchParams()
  const error  = params.get("error")

  const messages: Record<string, string> = {
    "Configuration":   "Server configuration error. Please contact support.",
    "AccessDenied":    "You do not have permission to sign in.",
    "Verification":    "The verification link has expired or already been used.",
    "Default":         "An error occurred during sign in.",
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md text-center">
        <div className="text-5xl mb-4">⚠️</div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Authentication Error</h2>
        <p className="text-gray-500 mb-6">
          {messages[error ?? "Default"] ?? messages["Default"]}
        </p>
        <Link href="/auth/login"
          className="inline-flex items-center gap-2 bg-blue-600 text-white px-6 py-2.5 rounded-xl text-sm font-semibold hover:bg-blue-700 transition-colors">
          Back to Sign In
        </Link>
      </div>
    </div>
  )
}

export default function ErrorPage() {
  return <Suspense><ErrorContent /></Suspense>
}