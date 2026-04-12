require("dotenv").config({ path: ".env.local" })
const { PrismaClient } = require("@prisma/client")
const prisma = new PrismaClient()
async function main() {
  const count = await prisma.analysis.count()
  const all   = await prisma.analysis.findMany({
    orderBy: { createdAt: "desc" },
    select:  { diseaseName: true, decision: true, createdAt: true }
  })
  console.log("Total in DB:", count)
  all.forEach(a => console.log(" -", a.diseaseName, "|", a.decision, "|", new Date(a.createdAt).toLocaleDateString()))
}
main().catch(console.error).finally(() => prisma.$disconnect())
