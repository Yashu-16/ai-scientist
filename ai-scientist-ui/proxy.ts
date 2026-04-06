import { auth } from "@/auth"
import { NextResponse } from "next/server"

const PUBLIC_PATHS = [
  "/",              
  "/landing",      
  "/auth/login",
  "/auth/register",
  "/auth/forgot-password",
  "/auth/reset-password",
  "/auth/verify",
  "/auth/error",
  "/api/auth",
  "/terms",
  "/privacy",
]

export default auth((req) => {
  const { pathname } = req.nextUrl
  const isPublic  = PUBLIC_PATHS.some(p => pathname.startsWith(p))
  const isLoggedIn = !!req.auth

  if (isPublic) return NextResponse.next()

  if (!isLoggedIn) {
    const loginUrl = new URL("/auth/login", req.nextUrl.origin)
    loginUrl.searchParams.set("callbackUrl", pathname)
    return NextResponse.redirect(loginUrl)
  }

  return NextResponse.next()
})

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\.png$).*)"],
}