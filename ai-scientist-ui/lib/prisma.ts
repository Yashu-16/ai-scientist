// lib/prisma.ts
import { PrismaClient } from "@prisma/client"
import { PrismaNeon } from "@prisma/adapter-neon"
import { neonConfig } from "@neondatabase/serverless"
import ws from "ws"

// Required for Neon serverless WebSockets in Node.js
neonConfig.webSocketConstructor = ws

function createPrismaClient(): PrismaClient {
  const connectionString = process.env.DATABASE_URL
  if (!connectionString) {
    throw new Error("DATABASE_URL is not set")
  }
  const adapter = new PrismaNeon({ connectionString })
  // Driver adapter narrows PrismaClient's type and can omit model delegates; runtime API is unchanged.
  return new PrismaClient({ adapter }) as PrismaClient
}

const globalForPrisma = globalThis as unknown as { prisma: PrismaClient | undefined }

export const prisma: PrismaClient =
  globalForPrisma.prisma ?? createPrismaClient()

if (process.env.NODE_ENV !== "production") globalForPrisma.prisma = prisma
