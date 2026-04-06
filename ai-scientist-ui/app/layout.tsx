// app/layout.tsx
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { AppShell } from "@/components/AppShell"
import { CookieBanner } from "@/components/legal/CookieBanner"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "AI Scientist — Drug Discovery Platform",
  description: "V5 Decision & Risk Intelligence Platform for Drug Discovery",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${inter.className} antialiased`}>
        <AppShell>{children}</AppShell>
        <CookieBanner />
      </body>
    </html>
  )
}