"use client"
import { usePathname } from "next/navigation"
import { Sidebar } from "./Sidebar"
import { Navbar }  from "./Navbar"

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()

  // Full-page routes — no sidebar, no navbar
  const isPublicPage =
    pathname === "/" ||
    pathname === "/landing" ||
    pathname.startsWith("/auth")

  if (isPublicPage) {
    return <>{children}</>
  }

  // App routes — show sidebar + navbar
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