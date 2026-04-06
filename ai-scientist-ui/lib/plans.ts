// lib/plans.ts

export type PlanId = "FREE" | "ACADEMIC" | "PRO" | "ENTERPRISE"

export interface PlanConfig {
  id:             PlanId
  name:           string
  price:          number      // monthly in ₹
  priceInPaise:   number      // price × 100
  analysesLimit:  number      // -1 = unlimited
  memberLimit:    number
  features:       string[]
  cta:            string
  highlighted:    boolean
  badge?:         string
}

export const PLANS: PlanConfig[] = [
  {
    id:            "FREE",
    name:          "Free",
    price:         0,
    priceInPaise:  0,
    analysesLimit: 3,
    memberLimit:   1,
    cta:           "Current Plan",
    highlighted:   false,
    features: [
      "3 analyses per month",
      "All 10 analysis tabs",
      "PDF export",
      "AI chat",
      "GO/NO-GO decision engine",
    ],
  },
  {
    id:            "ACADEMIC",
    name:          "Academic",
    price:         999,
    priceInPaise:  99900,
    analysesLimit: 50,
    memberLimit:   3,
    cta:           "Upgrade to Academic",
    highlighted:   false,
    badge:         "For researchers",
    features: [
      "50 analyses per month",
      "Up to 3 team members",
      "Priority API access",
      "All Free features",
      "Email support",
    ],
  },
  {
    id:            "PRO",
    name:          "Professional",
    price:         4999,
    priceInPaise:  499900,
    analysesLimit: -1,
    memberLimit:   10,
    cta:           "Upgrade to Pro",
    highlighted:   true,
    badge:         "Most Popular",
    features: [
      "Unlimited analyses",
      "Up to 10 team members",
      "Drug repurposing mode",
      "Trend detection",
      "Knowledge graph access",
      "Priority support",
      "GST invoice",
    ],
  },
  {
    id:            "ENTERPRISE",
    name:          "Enterprise",
    price:         0,
    priceInPaise:  0,
    analysesLimit: -1,
    memberLimit:   -1,
    cta:           "Contact Sales",
    highlighted:   false,
    badge:         "Custom",
    features: [
      "Unlimited analyses",
      "Unlimited team members",
      "Dedicated support",
      "Custom integrations",
      "On-premise option",
      "SLA guarantee",
      "Custom contract",
    ],
  },
]

export function getPlan(id: PlanId): PlanConfig {
  return PLANS.find(p => p.id === id) ?? PLANS[0]
}

export function getAnalysesLimit(plan: PlanId): number {
  return getPlan(plan).analysesLimit
}