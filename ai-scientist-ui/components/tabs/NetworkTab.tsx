"use client"
// components/tabs/NetworkTab.tsx
import { useEffect, useRef, useState } from "react"
import { getNetworkData } from "@/lib/api"
import type { NetworkData } from "@/types"
import { Card, Spinner, StatCard } from "@/components/ui"

export function NetworkTab({ diseaseName }: { diseaseName: string }) {
  const [network, setNetwork] = useState<NetworkData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    getNetworkData(diseaseName)
      .then(r => setNetwork(r.network))
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [diseaseName])

  useEffect(() => {
    if (!network || !containerRef.current) return

    // vis.js via CDN loaded in the HTML
    const script = document.createElement("script")
    script.src = "https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.js"
    script.onload = () => {
      const win = window as any
      if (!win.vis || !containerRef.current) return
      const nodes = new win.vis.DataSet(network.nodes)
      const edges = new win.vis.DataSet(network.edges)
      new win.vis.Network(containerRef.current, { nodes, edges }, {
        nodes: { shape:"dot", borderWidth:2, shadow:true, font:{ face:"monospace", size:13 } },
        edges: { smooth:{ type:"continuous", roundness:0.3 }, shadow:false },
        physics: {
          enabled:true,
          forceAtlas2Based:{ gravitationalConstant:-50, centralGravity:0.01, springLength:120, springConstant:0.08, damping:0.4 },
          solver:"forceAtlas2Based",
          stabilization:{ enabled:true, iterations:200, fit:true }
        },
        interaction:{ hover:true, tooltipDelay:100, navigationButtons:true, keyboard:true }
      })
    }
    document.head.appendChild(script)

    const css = document.createElement("link")
    css.rel = "stylesheet"
    css.href = "https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.css"
    document.head.appendChild(css)
  }, [network])

  if (loading) return <div className="flex justify-center py-16"><Spinner size="lg" /></div>
  if (error) return <div className="text-red-500 text-sm text-center py-8">{error}</div>
  if (!network) return null

  const stats = network.stats ?? {}

  return (
    <div className="space-y-4 tab-content">
      <h3 className="text-sm font-semibold text-gray-700">🕸️ Protein-Drug Interaction Network</h3>
      <p className="text-xs text-gray-400">Interactive network showing proteins, drugs, pathways and their relationships</p>

      <div className="grid grid-cols-4 gap-3">
        <StatCard label="🔵 Total Nodes" value={stats.total_nodes ?? 0} />
        <StatCard label="🧬 Proteins"    value={stats.proteins ?? 0}    color="blue" />
        <StatCard label="💊 Drugs"       value={stats.drugs ?? 0}       color="green" />
        <StatCard label="🔮 Pathways"    value={stats.pathways ?? 0}    color="purple" />
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-4">
        {[
          { color:"#ef4444", label:"Disease" },
          { color:"#3b82f6", label:"Protein" },
          { color:"#10b981", label:"Drug (Low Risk)" },
          { color:"#f59e0b", label:"Drug (Med Risk)" },
          { color:"#8b5cf6", label:"Pathway" },
        ].map(({ color, label }) => (
          <div key={label} className="flex items-center gap-1.5">
            <div className="h-3 w-3 rounded-full flex-shrink-0" style={{ backgroundColor: color }} />
            <span className="text-xs text-gray-500">{label}</span>
          </div>
        ))}
      </div>

      <Card padding="none">
        <div ref={containerRef} style={{ width:"100%", height:520, backgroundColor:"#0e1117", borderRadius:8 }} />
      </Card>
      <p className="text-xs text-gray-400 text-center">💡 Click nodes to see details | Scroll to zoom | Drag to pan</p>
    </div>
  )
}