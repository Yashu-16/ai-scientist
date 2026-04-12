// lib/plans.ts
export type PlanId = "FREE" | "ACADEMIC" | "PRO" | "ENTERPRISE"

export interface PlanConfig {
  id:            PlanId
  name:          string
  price:         number      // monthly in USD
  priceInCents:  number      // price × 100
  analysesLimit: number      // -1 = unlimited
  memberLimit:   number
  features:      string[]
  cta:           string
  highlighted:   boolean
  badge?:        string
}

export const PLANS: PlanConfig[] = [
  {
    id:            "FREE",
    name:          "Free",
    price:         0,
    priceInCents:  0,
    analysesLimit: 3,
    memberLimit:   1,
    cta:           "Current Plan",
    highlighted:   false,
    features: [
      "3 analyses per month",
      "All 10 analysis tabs",
      "PDF export",
      "AI chat assistant",
      "GO/NO-GO decision engine",
      "ClinicalTrials.gov integration",
    ],
  },
  {
    id:            "ACADEMIC",
    name:          "Academic",
    price:         25,
    priceInCents:  1900,
    analysesLimit: 50,
    memberLimit:   3,
    cta:           "Start Free Trial",
    highlighted:   false,
    badge:         "For researchers",
    features: [
      "50 analyses per month",
      "Up to 3 team members",
      "Priority API access",
      "All Free features",
      "Email support",
      "Research citation export",
    ],
  },
  {
    id:            "PRO",
    name:          "Professional",
    price:         99,
    priceInCents:  9900,
    analysesLimit: -1,
    memberLimit:   10,
    cta:           "Start Free Trial",
    highlighted:   true,
    badge:         "Most Popular",
    features: [
      "Unlimited analyses",
      "Up to 10 team members",
      "Drug repurposing mode",
      "Trend detection engine",
      "Knowledge graph access",
      "Priority support",
      "API access",
      "Invoice & receipts",
    ],
  },
  {
    id:            "ENTERPRISE",
    name:          "Enterprise",
    price:         0,
    priceInCents:  0,
    analysesLimit: -1,
    memberLimit:   -1,
    cta:           "Contact Sales",
    highlighted:   false,
    badge:         "Custom",
    features: [
      "Unlimited analyses",
      "Unlimited team members",
      "Dedicated account manager",
      "Custom integrations",
      "On-premise deployment option",
      "SLA guarantee",
      "Custom contract & invoicing",
      "Training & onboarding",
    ],
  },
]

export function getPlan(id: PlanId): PlanConfig {
  return PLANS.find(p => p.id === id) ?? PLANS[0]
}

export function getAnalysesLimit(plan: PlanId): number {
  return getPlan(plan).analysesLimit
}