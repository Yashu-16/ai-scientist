"use client"
// app/insights/page.tsx
import { useAnalysis } from "../../lib/hooks"
import { TrendsTab }   from "../../components/tabs/TrendsTab"
import { RepurposeTab } from "../../components/tabs/RepurposeTab"
import { Spinner, Card, Badge, riskVariant } from "../../components/ui"
import { useState } from "react"

const TABS = [
  { id:"trends",    label:"🔥 Trends" },
  { id:"repurpose", label:"🔁 Drug Repurposing" },
  { id:"competition", label:"🏁 Competition Intel" },
]

export default function InsightsPage() {
  const { data, hydrated } = useAnalysis()
  const [activeTab, setActiveTab] = useState("trends")

  if (!hydrated) return <div className="flex justify-center py-16"><Spinner size="lg" /></div>

  return (
    <div className="max-w-5xl mx-auto space-y-5">
      <div>
        <h1 className="text-xl font-bold text-gray-900">Insights</h1>
        <p className="text-sm text-gray-500 mt-0.5">Emerging trends, drug repurposing, and competitive intelligence</p>
      </div>

      {/* Tab bar */}
      <div className="border-b border-gray-200">
        <div className="flex gap-0">
          {TABS.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-3 text-sm font-medium transition-all border-b-2 -mb-px ${
                activeTab === tab.id
                  ? "border-blue-600 text-blue-700"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      <div className="tab-content">
        {activeTab === "trends"      && <TrendsTab />}
        {activeTab === "repurpose"   && <RepurposeTab />}
        {activeTab === "competition" && <CompetitionTab data={data} />}
      </div>
    </div>
  )
}

function CompetitionTab({ data }: { data: ReturnType<typeof useAnalysis>["data"] }) {
  if (!data?.drugs?.some(d => d.competition_intel)) return (
    <div className="text-center py-16">
      <p className="text-3xl mb-3">🏁</p>
      <p className="text-sm text-gray-500">No competition data available.</p>
      <p className="text-xs text-gray-400 mt-1">Run an analysis first to see competitive intelligence.</p>
    </div>
  )

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-gray-700">🏁 Competitive Landscape</h3>
      {data!.drugs.filter(d => d.competition_intel).map(drug => {
        const comp = drug.competition_intel!
        return (
          <Card key={drug.drug_name} padding="md">
            <div className="flex items-start justify-between mb-3">
              <div>
                <p className="font-bold text-gray-900">💊 {drug.drug_name}</p>
                <p className="text-xs text-gray-400 mt-0.5">{comp.drug_class} · Phase {drug.clinical_phase}</p>
              </div>
              <div className="flex gap-2">
                <Badge
                  label={`${comp.competition_level} Competition`}
                  variant={comp.competition_level === "High" ? "red" : comp.competition_level === "Medium" ? "yellow" : "green"}
                />
                <Badge
                  label={comp.market_opportunity}
                  variant={comp.market_opportunity === "Strong" ? "green" : comp.market_opportunity === "Crowded" ? "red" : "yellow"}
                />
              </div>
            </div>
            <p className="text-sm text-gray-600 mb-3">{comp.strategic_note}</p>
            {comp.similar_drug_names?.length > 0 && (
              <div>
                <p className="text-xs font-medium text-gray-500 mb-2">Similar drugs ({comp.num_similar_drugs} total):</p>
                <div className="flex flex-wrap gap-1.5">
                  {comp.similar_drug_names.map(d => (
                    <span key={d} className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full">{d}</span>
                  ))}
                </div>
              </div>
            )}
          </Card>
        )
      })}
    </div>
  )
}