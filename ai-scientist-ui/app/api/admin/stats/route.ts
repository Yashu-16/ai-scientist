// app/api/admin/stats/route.ts
import { NextResponse } from "next/server"
import { requireAdmin } from "@/lib/adminGuard"
import { prisma } from "@/lib/prisma"

export async function GET() {
  const { error } = await requireAdmin()
  if (error) return error

  const now       = new Date()
  const today     = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const thisMonth = new Date(now.getFullYear(), now.getMonth(), 1)
  const lastMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1)

  const [
    totalUsers,
    newUsersToday,
    newUsersThisMonth,
    totalOrgs,
    totalAnalyses,
    analysesToday,
    analysesThisMonth,
    planCounts,
    revenueThisMonth,
    revenueLastMonth,
    totalRevenue,
    recentUsers,
    recentAnalyses,
  ] = await Promise.all([
    prisma.user.count(),
    prisma.user.count({ where: { createdAt: { gte: today } } }),
    prisma.user.count({ where: { createdAt: { gte: thisMonth } } }),
    prisma.organization.count(),
    prisma.analysis.count(),
    prisma.analysis.count({ where: { createdAt: { gte: today } } }),
    prisma.analysis.count({ where: { createdAt: { gte: thisMonth } } }),
    prisma.user.groupBy({
      by:     ["plan"],
      _count: { plan: true },
    }),
    prisma.payment.aggregate({
      where:  { status: "CAPTURED", createdAt: { gte: thisMonth } },
      _sum:   { amount: true },
    }),
    prisma.payment.aggregate({
      where:  { status: "CAPTURED", createdAt: { gte: lastMonth, lt: thisMonth } },
      _sum:   { amount: true },
    }),
    prisma.payment.aggregate({
      where: { status: "CAPTURED" },
      _sum:  { amount: true },
    }),
    prisma.user.findMany({
      orderBy: { createdAt: "desc" },
      take:    5,
      select:  {
        id: true, name: true, email: true,
        plan: true, createdAt: true
      },
    }),
    prisma.analysis.findMany({
      orderBy: { createdAt: "desc" },
      take:    5,
      select:  {
        id: true, diseaseName: true, decision: true,
        createdAt: true,
        user: { select: { name: true, email: true } },
      },
    }),
  ])

  const mrrThisMonth = (revenueThisMonth._sum.amount ?? 0) / 100
  const mrrLastMonth = (revenueLastMonth._sum.amount ?? 0) / 100
  const mrrGrowth    = mrrLastMonth > 0
    ? Math.round(((mrrThisMonth - mrrLastMonth) / mrrLastMonth) * 100)
    : 0

  return NextResponse.json({
    users: {
      total:        totalUsers,
      newToday:     newUsersToday,
      newThisMonth: newUsersThisMonth,
    },
    orgs: { total: totalOrgs },
    analyses: {
      total:        totalAnalyses,
      today:        analysesToday,
      thisMonth:    analysesThisMonth,
    },
    revenue: {
      mrr:       mrrThisMonth,
      lastMonth: mrrLastMonth,
      growth:    mrrGrowth,
      total:     (totalRevenue._sum.amount ?? 0) / 100,
    },
    planCounts,
    recentUsers,
    recentAnalyses,
  })
}