"use client"
// components/AppShell.tsx
// Renders sidebar+navbar for app routes, plain layout for landing page

import { usePathname } from "next/navigation"
import { Sidebar } from "./Sidebar"
import { Navbar }  from "./Navbar"

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const isLanding = pathname === "/landing"
  const isAuth    = pathname.startsWith("/auth")

  if (isLanding || isAuth) {
    return <>{children}</>
  }

  // App pages: sidebar + navbar + content area
  return (
    <div className="bg-gray-50 min-h-screen">
      <Sidebar />
      <Navbar />
      <main className="ml-56 pt-14 min-h-screen">
        <div className="p-6">
          {children}
        </div>
      </main>
    </div>
  )
}