process.env.DATABASE_URL = "postgresql://neondb_owner:npg_Q8caYBSwf9be@ep-blue-unit-a4g77awd.us-east-1.aws.neon.tech/neondb?sslmode=require"
const { PrismaClient } = require("@prisma/client")
const prisma = new PrismaClient()
async function main() {
  const users = await prisma.user.findMany({
    select: {
      email: true,
      plan: true,
      analysesUsed: true,
      analysesLimit: true,
      _count: { select: { analyses: true } }
    }
  })
  console.log("Users:")
  users.forEach(u => console.log(
    " -", u.email,
    "| plan:", u.plan,
    "| used:", u.analysesUsed,
    "| limit:", u.analysesLimit,
    "| total saved:", u._count.analyses
  ))
}
main().catch(console.error).finally(() => prisma.$disconnect())
