// types/next-auth.d.ts
import { DefaultSession } from "next-auth"

declare module "next-auth" {
  interface Session {
    user: {
      id:   string
      role: string
      plan: string
    } & DefaultSession["user"]
  }
}