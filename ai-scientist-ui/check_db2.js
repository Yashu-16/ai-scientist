process.env.DATABASE_URL = "postgresql://neondb_owner:npg_Q8caYBSwf9be@ep-blue-unit-a4g77awd.us-east-1.aws.neon.tech/neondb?sslmode=require"
const { PrismaClient } = require("@prisma/client")
const prisma = new PrismaClient()
async function main() {
  const result = await prisma.analysis.findMany({
    orderBy: { createdAt: "desc" },
    take: 20,
    select: { diseaseName: true, decision: true, createdAt: true }
  })
  console.log("Total in DB:", result.length)
  result.forEach(a => console.log(" -", a.diseaseName, "|", a.decision, "|", a.createdAt.toLocaleDateString()))
}
main().catch(console.error).finally(() => prisma.$disconnect())
