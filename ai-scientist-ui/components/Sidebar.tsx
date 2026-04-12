"use client"
// components/Sidebar.tsx
import Link from "next/link"
import { Building2 } from "lucide-react"
import { usePathname } from "next/navigation"
import {
  LayoutDashboard, FlaskConical, Lightbulb,
  TrendingUp, FileText, Dna, Activity, CreditCard, History, UserCircle, Shield  
} from "lucide-react"

const nav = [
  { href: "/dashboard", label: "Dashboard",    icon: LayoutDashboard },
  { href: "/analysis",  label: "Analysis",     icon: FlaskConical    },
  { href: "/hypotheses",label: "All 10 Tabs",  icon: Lightbulb       },
  { href: "/insights",  label: "Insights",     icon: TrendingUp      },
  { href: "/report",    label: "Report & Chat",icon: FileText        },
  { href: "/org/dashboard", label: "Organization", icon: Building2   },
  { href: "/pricing",   label: "Pricing",      icon: CreditCard      },
  { href: "/billing",   label: "Billing",      icon: CreditCard      },
  { href: "/history",   label: "History",      icon: History         },
  { href: "/profile",   label: "Profile",      icon: UserCircle      },
]

export function Sidebar() {
  const pathname = usePathname()
  return (
    <aside className="fixed left-0 top-0 h-full w-56 bg-white border-r border-gray-100 flex flex-col z-40 shadow-sm">
      {/* Logo */}
      <div className="flex items-center gap-2.5 px-5 py-4 border-b border-gray-100">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 shadow-sm flex-shrink-0">
          <Dna className="h-4 w-4 text-white" />
        </div>
        <div>
          <p className="text-sm font-bold text-gray-900 leading-none">Causyn AI</p>
          <p className="text-[11px] text-gray-400 mt-0.5">Drug Discovery V5</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-3 space-y-0.5 overflow-y-auto">
        {nav.map(({ href, label, icon:Icon }) => {
          const active = pathname === href
          return (
            <Link key={href} href={href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
                active
                  ? "bg-blue-50 text-blue-700 shadow-sm"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              }`}>
              <Icon className={`h-4 w-4 flex-shrink-0 ${active ? "text-blue-600" : "text-gray-400"}`} />
              {label}
            </Link>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-gray-100 space-y-1">
        <div className="flex items-center gap-1.5">
          <Activity className="h-3 w-3 text-emerald-500" />
          <p className="text-[11px] text-gray-500">FastAPI + GPT-4o-mini</p>
        </div>
        <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer"
           className="text-[11px] text-blue-500 hover:text-blue-700 block">
          API Docs →
        </a>
      </div>
    </aside>
  )
}