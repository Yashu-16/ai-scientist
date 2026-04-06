import { defineConfig } from "prisma/config"
import { loadEnvConfig } from "@next/env"

const { combinedEnv } = loadEnvConfig(process.cwd())

export default defineConfig({
  earlyAccess: true,
  schema: "prisma/schema.prisma",
  datasource: {
    url: combinedEnv.DATABASE_URL ?? "",
  },
})
