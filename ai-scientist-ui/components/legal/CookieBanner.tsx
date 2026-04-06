"use client"
// components/legal/CookieBanner.tsx
import { useState, useEffect } from "react"
import Link from "next/link"
import { Cookie, X, Check } from "lucide-react"

const COOKIE_KEY = "ais_cookie_consent"

export function CookieBanner() {
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    // Show only if no consent recorded
    const consent = localStorage.getItem(COOKIE_KEY)
    if (!consent) setVisible(true)
  }, [])

  function accept() {
    localStorage.setItem(COOKIE_KEY, "accepted")
    setVisible(false)
  }

  function decline() {
    localStorage.setItem(COOKIE_KEY, "declined")
    setVisible(false)
  }

  if (!visible) return null

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 p-4 sm:p-6">
      <div className="max-w-4xl mx-auto bg-white border border-gray-200 rounded-2xl shadow-lg p-5 flex flex-col sm:flex-row items-start sm:items-center gap-4">

        {/* Icon */}
        <div className="flex-shrink-0 h-10 w-10 rounded-xl bg-amber-50 border border-amber-100 flex items-center justify-center">
          <Cookie className="h-5 w-5 text-amber-600" />
        </div>

        {/* Text */}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold text-gray-900">
            We use essential cookies
          </p>
          <p className="text-xs text-gray-500 mt-0.5 leading-relaxed">
            We use only essential cookies for authentication and security.
            No advertising or tracking cookies. See our{" "}
            <Link href="/privacy" className="text-blue-500 hover:text-blue-700 underline">
              Privacy Policy
            </Link>{" "}
            for details.
          </p>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 flex-shrink-0">
          <button
            onClick={decline}
            className="flex items-center gap-1.5 px-4 py-2 border border-gray-200 text-gray-500 text-xs font-medium rounded-xl hover:bg-gray-50 transition-colors"
          >
            <X className="h-3.5 w-3.5" />
            Decline
          </button>
          <button
            onClick={accept}
            className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 text-white text-xs font-semibold rounded-xl hover:bg-blue-700 transition-colors"
          >
            <Check className="h-3.5 w-3.5" />
            Accept
          </button>
        </div>
      </div>
    </div>
  )
}