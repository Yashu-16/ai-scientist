"use client"
// components/ui/GoNoBadge.tsx

const cfg = {
  "GO":          { bg:"bg-emerald-50", border:"border-emerald-200", text:"text-emerald-700", dot:"bg-emerald-500", hero:"from-emerald-900/20 to-emerald-800/10 border-emerald-500/30" },
  "NO-GO":       { bg:"bg-red-50",     border:"border-red-200",     text:"text-red-700",     dot:"bg-red-500",     hero:"from-red-900/20 to-red-800/10 border-red-500/30" },
  "INVESTIGATE": { bg:"bg-amber-50",   border:"border-amber-200",   text:"text-amber-700",   dot:"bg-amber-500",   hero:"from-amber-900/20 to-amber-800/10 border-amber-500/30" },
}

export function GoNoBadge({
  decision, confidence, size="sm"
}: {
  decision: "GO"|"NO-GO"|"INVESTIGATE"; confidence?: number; size?: "sm"|"lg"
}) {
  const c = cfg[decision] ?? cfg["INVESTIGATE"]
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border font-semibold ${c.bg} ${c.border} ${c.text} ${size==="sm" ? "px-2.5 py-1 text-xs" : "px-4 py-2 text-sm"}`}>
      <span className={`rounded-full ${c.dot} ${size==="sm" ? "h-1.5 w-1.5" : "h-2 w-2"}`} />
      {decision}
      {confidence !== undefined && (
        <span className="opacity-60 font-normal ml-0.5">{Math.round(confidence * 100)}%</span>
      )}
    </span>
  )
}

export function GoNoGoCard({ gng }: { gng: { decision: "GO"|"NO-GO"|"INVESTIGATE"; confidence_in_decision: number; primary_reason: string; supporting_reasons: string[]; blocking_reasons: string[]; recommended_action: string; conditions_to_flip: string } }) {
  const c = cfg[gng.decision] ?? cfg["INVESTIGATE"]
  const emoji = { "GO":"✅", "NO-GO":"❌", "INVESTIGATE":"🔍" }[gng.decision] ?? "❓"

  return (
    <div className={`rounded-xl border bg-gradient-to-br p-5 ${c.hero}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <span className="text-3xl">{emoji}</span>
          <div>
            <p className="text-xs text-gray-400 uppercase tracking-wider">Final Decision</p>
            <p className={`text-2xl font-black tracking-wide ${c.text}`}>{gng.decision}</p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-xs text-gray-400">Confidence</p>
          <p className={`text-xl font-bold ${c.text}`}>{Math.round(gng.confidence_in_decision * 100)}%</p>
        </div>
      </div>

      {/* Primary reason */}
      <div className="bg-white/60 rounded-lg p-3 mb-3 text-sm text-gray-700">
        <span className="font-medium">📋 Decision Basis: </span>{gng.primary_reason}
      </div>

      {/* Supporting / blocking */}
      {(gng.supporting_reasons?.length > 0 || gng.blocking_reasons?.length > 0) && (
        <div className="grid grid-cols-2 gap-3 mb-3">
          {gng.supporting_reasons?.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-emerald-600 mb-1.5">✅ Supporting</p>
              {gng.supporting_reasons.map((r, i) => (
                <p key={i} className="text-xs text-gray-600 mb-1 bg-emerald-50/50 rounded px-2 py-1">• {r}</p>
              ))}
            </div>
          )}
          {gng.blocking_reasons?.length > 0 && (
            <div>
              <p className="text-xs font-semibold text-red-600 mb-1.5">❌ Blocking</p>
              {gng.blocking_reasons.map((r, i) => (
                <p key={i} className="text-xs text-gray-600 mb-1 bg-red-50/50 rounded px-2 py-1">• {r}</p>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Action */}
      {gng.recommended_action && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-2 text-xs text-emerald-800">
          🚀 <strong>Recommended Action:</strong> {gng.recommended_action}
        </div>
      )}

      {/* Flip condition */}
      {gng.conditions_to_flip && (
        <p className="text-xs text-gray-400 mt-2 italic">🔄 {gng.conditions_to_flip}</p>
      )}
    </div>
  )
}