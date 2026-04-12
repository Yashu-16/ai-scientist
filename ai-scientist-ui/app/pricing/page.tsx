"use client"
// app/pricing/page.tsx — Global market, USD pricing
import { useState } from "react"
import { Check, Zap, Building2, GraduationCap, Globe, Shield, Clock, Users } from "lucide-react"
import { PLANS, PlanConfig } from "@/lib/plans"
import Link from "next/link"

const PLAN_ICONS: Record<string, React.ElementType> = {
  FREE:       Zap,
  ACADEMIC:   GraduationCap,
  PRO:        Zap,
  ENTERPRISE: Building2,
}

export default function PricingPage() {
  const [billingCycle, setBillingCycle] = useState<"monthly" | "annual">("monthly")

  function getPrice(plan: PlanConfig): string {
    if (plan.price === 0 && plan.id === "FREE")       return "Free"
    if (plan.price === 0 && plan.id === "ENTERPRISE") return "Custom"
    const price = billingCycle === "annual"
      ? Math.round(plan.price * 0.8)   // 20% annual discount
      : plan.price
    return `$${price}`
  }

  function handleUpgrade(plan: PlanConfig) {
    if (plan.id === "FREE")       return
    if (plan.id === "ENTERPRISE") {
      window.location.href = "mailto:sales@causyn.ai?subject=Enterprise Plan Inquiry"
      return
    }
    // Direct to billing page — Stripe integration
    window.location.href = `/billing?plan=${plan.id}&cycle=${billingCycle}`
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 py-16 space-y-12">

        {/* Header */}
        <div className="text-center">
          <div className="inline-flex items-center gap-2 bg-blue-50 border border-blue-100 text-blue-700 text-xs font-semibold px-4 py-1.5 rounded-full mb-6">
            <Globe className="h-3.5 w-3.5" />
            Available Worldwide · All prices in USD
          </div>
          <h1 className="text-4xl font-black text-gray-900 mb-3">
            Simple, transparent pricing
          </h1>
          <p className="text-gray-500 text-lg max-w-xl mx-auto">
            Start free. Upgrade when you need more. Cancel anytime.
            No hidden fees, no lock-in contracts.
          </p>
        </div>

        {/* Billing toggle */}
        <div className="flex items-center justify-center gap-3">
          <span className={`text-sm font-medium ${billingCycle === "monthly" ? "text-gray-900" : "text-gray-400"}`}>
            Monthly
          </span>
          <button
            onClick={() => setBillingCycle(c => c === "monthly" ? "annual" : "monthly")}
            className={`relative w-12 h-6 rounded-full transition-colors ${
              billingCycle === "annual" ? "bg-blue-600" : "bg-gray-300"
            }`}
          >
            <span className={`absolute top-1 left-1 h-4 w-4 bg-white rounded-full shadow transition-transform ${
              billingCycle === "annual" ? "translate-x-6" : ""
            }`} />
          </button>
          <span className={`text-sm font-medium ${billingCycle === "annual" ? "text-gray-900" : "text-gray-400"}`}>
            Annual
            <span className="ml-1.5 text-xs bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full font-bold">
              Save 20%
            </span>
          </span>
        </div>

        {/* Plans grid */}
        <div className="grid grid-cols-4 gap-5">
          {PLANS.map(plan => {
            const Icon = PLAN_ICONS[plan.id] ?? Zap

            return (
              <div
                key={plan.id}
                className={`relative bg-white rounded-2xl border flex flex-col ${
                  plan.highlighted
                    ? "border-blue-500 shadow-xl shadow-blue-100 ring-2 ring-blue-500"
                    : "border-gray-200 shadow-sm"
                }`}
              >
                {/* Badge */}
                {plan.badge && (
                  <div className={`absolute -top-3 left-1/2 -translate-x-1/2 text-xs font-bold px-3 py-1 rounded-full whitespace-nowrap ${
                    plan.highlighted ? "bg-blue-600 text-white" : "bg-gray-800 text-white"
                  }`}>
                    {plan.badge}
                  </div>
                )}

                <div className="p-6 flex-1">
                  {/* Icon + name */}
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center mb-4 ${
                    plan.highlighted ? "bg-blue-100" : "bg-gray-100"
                  }`}>
                    <Icon className={`h-5 w-5 ${plan.highlighted ? "text-blue-600" : "text-gray-500"}`} />
                  </div>

                  <h3 className="text-base font-bold text-gray-900">{plan.name}</h3>

                  {/* Price */}
                  <div className="mt-3 mb-1">
                    <div className="flex items-baseline gap-1">
                      <span className="text-4xl font-black text-gray-900">
                        {getPrice(plan)}
                      </span>
                      {plan.price > 0 && (
                        <span className="text-sm text-gray-400">/mo</span>
                      )}
                    </div>
                    {billingCycle === "annual" && plan.price > 0 && plan.id !== "ENTERPRISE" && (
                      <p className="text-xs text-emerald-600 font-medium mt-0.5">
                        Billed ${Math.round(plan.price * 0.8 * 12)}/year
                      </p>
                    )}
                  </div>

                  <p className="text-xs text-gray-400 mb-5">
                    {plan.analysesLimit === -1
                      ? "Unlimited analyses"
                      : plan.analysesLimit === 0
                      ? "Custom limit"
                      : `${plan.analysesLimit} analyses/month`}
                  </p>

                  {/* Features */}
                  <ul className="space-y-2.5">
                    {plan.features.map(f => (
                      <li key={f} className="flex items-start gap-2 text-sm text-gray-600">
                        <Check className={`h-4 w-4 flex-shrink-0 mt-0.5 ${
                          plan.highlighted ? "text-blue-500" : "text-emerald-500"
                        }`} />
                        {f}
                      </li>
                    ))}
                  </ul>
                </div>

                {/* CTA */}
                <div className="p-6 pt-0">
                  <button
                    onClick={() => handleUpgrade(plan)}
                    disabled={plan.id === "FREE"}
                    className={`w-full py-2.5 rounded-xl text-sm font-bold transition-all ${
                      plan.id === "FREE"
                        ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                        : plan.highlighted
                        ? "bg-blue-600 text-white hover:bg-blue-700 shadow-md"
                        : "bg-gray-900 text-white hover:bg-gray-800"
                    }`}
                  >
                    {plan.cta}
                  </button>
                  {plan.id !== "FREE" && plan.id !== "ENTERPRISE" && (
                    <p className="text-xs text-center text-gray-400 mt-2">
                      14-day free trial · No credit card required
                    </p>
                  )}
                </div>
              </div>
            )
          })}
        </div>

        {/* Trust badges */}
        <div className="grid grid-cols-4 gap-4">
          {[
            { icon: Shield,  title: "Secure Payments",      desc: "256-bit SSL encryption. PCI-DSS compliant." },
            { icon: Globe,   title: "Global Access",         desc: "Available in 150+ countries. All major currencies." },
            { icon: Clock,   title: "Cancel Anytime",        desc: "No lock-in. Cancel or downgrade at any time." },
            { icon: Users,   title: "Team Collaboration",    desc: "Invite team members and share analyses instantly." },
          ].map(({ icon: Icon, title, desc }) => (
            <div key={title} className="bg-white border border-gray-200 rounded-xl p-4 text-center">
              <div className="h-9 w-9 rounded-xl bg-blue-50 flex items-center justify-center mx-auto mb-3">
                <Icon className="h-4.5 w-4.5 text-blue-600" />
              </div>
              <p className="text-sm font-semibold text-gray-900 mb-1">{title}</p>
              <p className="text-xs text-gray-400 leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>

        {/* FAQ */}
        <div className="bg-white border border-gray-200 rounded-2xl p-8">
          <h3 className="text-lg font-bold text-gray-900 mb-6">Frequently asked questions</h3>
          <div className="grid grid-cols-2 gap-6">
            {[
              {
                q: "What counts as one analysis?",
                a: "Each time you run the full 9-stage pipeline for a disease. Cached results and reopened analyses don't count toward your limit."
              },
              {
                q: "Can I upgrade or downgrade anytime?",
                a: "Yes. Upgrades take effect immediately. Downgrades apply at the end of your current billing period."
              },
              {
                q: "What payment methods do you accept?",
                a: "All major credit and debit cards (Visa, Mastercard, Amex), PayPal, and bank transfers for Enterprise plans."
              },
              {
                q: "Do you offer academic or non-profit discounts?",
                a: "Yes. Contact us at sales@causyn.ai with your institutional email for special pricing."
              },
              {
                q: "Is my data secure?",
                a: "Yes. All data is encrypted at rest and in transit. We never share your research data with third parties."
              },
              {
                q: "Is this platform suitable for clinical decisions?",
                a: "No. Causyn AI is for exploratory research only. All outputs require independent validation by qualified researchers."
              },
              {
                q: "Do you provide invoices?",
                a: "Yes. Automatic invoices are generated for every payment and can be downloaded from your billing dashboard."
              },
              {
                q: "What is your refund policy?",
                a: "We offer a 14-day money-back guarantee on all paid plans. Contact support@causyn.ai to request a refund."
              },
            ].map(({ q, a }) => (
              <div key={q} className="border-b border-gray-100 pb-4 last:border-0 last:pb-0">
                <p className="text-sm font-semibold text-gray-900 mb-1">{q}</p>
                <p className="text-sm text-gray-500 leading-relaxed">{a}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Enterprise CTA */}
        <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl p-8 text-center">
          <h3 className="text-xl font-bold text-white mb-2">
            Need a custom solution for your organization?
          </h3>
          <p className="text-slate-400 text-sm mb-6 max-w-lg mx-auto">
            We work with pharmaceutical companies, CROs, biotech firms, and academic institutions
            to build custom drug discovery intelligence workflows.
          </p>
          <div className="flex items-center justify-center gap-3">
            <a
              href="mailto:sales@causyn.ai?subject=Enterprise Plan Inquiry"
              className="bg-blue-600 text-white px-6 py-2.5 rounded-xl text-sm font-bold hover:bg-blue-700 transition-colors"
            >
              Contact Sales
            </a>
            <a
              href="mailto:sales@causyn.ai?subject=Demo Request"
              className="border border-slate-600 text-slate-300 px-6 py-2.5 rounded-xl text-sm font-medium hover:bg-slate-700 transition-colors"
            >
              Request Demo
            </a>
          </div>
        </div>

        {/* Footer links */}
        <div className="text-center space-x-6">
          <Link href="/terms"   className="text-sm text-gray-400 hover:text-gray-600">Terms of Service</Link>
          <Link href="/privacy" className="text-sm text-gray-400 hover:text-gray-600">Privacy Policy</Link>
          <Link href="/"        className="text-sm text-gray-400 hover:text-gray-600">← Back to Dashboard</Link>
        </div>

      </div>
    </div>
  )
}