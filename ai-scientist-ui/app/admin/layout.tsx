// app/admin/layout.tsx
"use client"
import { useEffect, useState } from "react"
import { useRouter, usePathname } from "next/navigation"
import Link from "next/link"
import {
  LayoutDashboard, Users, Building2,
  CreditCard, FlaskConical, Shield,
  LogOut, ChevronRight
} from "lucide-react"

const adminNav = [
  { href:"/admin",          label:"Overview",  icon:LayoutDashboard },
  { href:"/admin/users",    label:"Users",     icon:Users           },
  { href:"/admin/orgs",     label:"Orgs",      icon:Building2       },
  { href:"/admin/revenue",  label:"Revenue",   icon:CreditCard      },
  { href:"/admin/analyses", label:"Analyses",  icon:FlaskConical    },
]

export default function AdminLayout({
  children
}: {
  children: React.ReactNode
}) {
  const router   = useRouter()
  const pathname = usePathname()
  const [checking, setChecking] = useState(true)

  useEffect(() => {
    // Verify admin access
    fetch("/api/admin/stats")
      .then(r => {
        if (r.status === 401) router.push("/auth/login")
        if (r.status === 403) router.push("/")
        setChecking(false)
      })
      .catch(() => router.push("/"))
  }, [router])

  if (checking) return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="animate-spin rounded-full h-8 w-8 border-2 border-gray-200 border-t-blue-600" />
    </div>
  )

  return (
    <div className="min-h-screen bg-gray-950 flex">

      {/* Admin sidebar */}
      <aside className="w-52 bg-gray-900 border-r border-gray-800 flex flex-col flex-shrink-0">
        <div className="px-4 py-5 border-b border-gray-800">
          <div className="flex items-center gap-2">
            <div className="h-7 w-7 rounded-lg bg-red-600 flex items-center justify-center">
              <Shield className="h-3.5 w-3.5 text-white" />
            </div>
            <div>
              <p className="text-xs font-bold text-white leading-none">Admin</p>
              <p className="text-[10px] text-gray-500 mt-0.5">Causyn AI</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 px-2 py-3 space-y-0.5">
          {adminNav.map(({ href, label, icon: Icon }) => {
            const active = pathname === href
            return (
              <Link
                key={href}
                href={href}
                className={`flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors ${
                  active
                    ? "bg-gray-800 text-white"
                    : "text-gray-400 hover:bg-gray-800 hover:text-white"
                }`}
              >
                <Icon className="h-4 w-4 flex-shrink-0" />
                {label}
                {active && (
                  <ChevronRight className="h-3 w-3 ml-auto text-gray-500" />
                )}
              </Link>
            )
          })}
        </nav>

        <div className="px-4 py-3 border-t border-gray-800 space-y-2">
          <Link
            href="/"
            className="flex items-center gap-2 text-xs text-gray-500 hover:text-gray-300 transition-colors"
          >
            <LogOut className="h-3.5 w-3.5" />
            Back to App
          </Link>
        </div>
      </aside>

      {/* Content */}
      <main className="flex-1 overflow-auto">
        <div className="p-6 max-w-screen-xl">
          {children}
        </div>
      </main>
    </div>
  )
}