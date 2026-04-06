// auth.ts
import NextAuth from "next-auth"
import Credentials from "next-auth/providers/credentials"
import bcrypt from "bcryptjs"
import { prisma } from "@/lib/prisma"

export const { handlers, auth, signIn, signOut } = NextAuth({
  secret: process.env.NEXTAUTH_SECRET,
  session: { strategy: "jwt" },
  pages: {
    signIn:  "/auth/login",
    error:   "/auth/error",
  },
  providers: [
    Credentials({
      name: "credentials",
      credentials: {
        email:    { label: "Email",    type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        try {
          if (!credentials?.email || !credentials?.password) return null

          const user = await prisma.user.findUnique({
            where: { email: credentials.email as string },
          })

          if (!user || !user.password) return null

          const valid = await bcrypt.compare(
            credentials.password as string,
            user.password
          )
          if (!valid) return null

          if (!user.emailVerified) return null

          return {
            id:    user.id,
            email: user.email ?? "",
            name:  user.name  ?? "",
            role:  user.role,
            plan:  user.plan,
          }
        } catch (error) {
          console.error("Auth error:", error)
          return null
        }
      },
    }),
  ],
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.id   = user.id
        token.role = (user as any).role
        token.plan = (user as any).plan
      }
  
      // Always refresh role from DB (catches role changes)
      if (token.id) {
        const dbUser = await prisma.user.findUnique({
          where:  { id: token.id as string },
          select: { role: true, plan: true }
        })
        if (dbUser) {
          token.role = dbUser.role
          token.plan = dbUser.plan
        }
      }
  
      return token
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.id   = token.id   as string
        session.user.role = token.role as string
        session.user.plan = token.plan as string
      }
      return session
    },
  },
})
