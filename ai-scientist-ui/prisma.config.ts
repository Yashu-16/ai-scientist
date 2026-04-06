import { defineConfig } from "prisma/config"

export default defineConfig({
  earlyAccess: true,
  schema: "prisma/schema.prisma",
  datasource: {
    url: "postgresql://neondb_owner:npg_Q8caYBSwf9be@ep-blue-unit-a4g77awd.us-east-1.aws.neon.tech/neondb?sslmode=require",
  },
})
