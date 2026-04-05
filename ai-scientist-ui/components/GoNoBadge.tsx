import { clsx } from "clsx"

interface GoNoBadgeProps {
  decision: "GO" | "NO-GO" | "INVESTIGATE"
  confidence?: number
  size?: "sm" | "lg"
}

const config = {
  "GO":          { bg: "bg-emerald-50", border: "border-emerald-200", text: "text-emerald-700", dot: "bg-emerald-500", label: "GO" },
  "NO-GO":       { bg: "bg-red-50",     border: "border-red-200",     text: "text-red-700",     dot: "bg-red-500",     label: "NO-GO" },
  "INVESTIGATE": { bg: "bg-amber-50",   border: "border-amber-200",   text: "text-amber-700",   dot: "bg-amber-500",   label: "INVESTIGATE" },
}

export function GoNoBadge({ decision, confidence, size = "sm" }: GoNoBadgeProps) {
  const c = config[decision] ?? config["INVESTIGATE"]
  return (
    <div className={clsx(
      "inline-flex items-center gap-2 rounded-full border font-semibold",
      c.bg, c.border, c.text,
      size === "sm" ? "px-3 py-1 text-sm" : "px-5 py-2.5 text-lg"
    )}>
      <span className={clsx("rounded-full", c.dot, size === "sm" ? "h-2 w-2" : "h-3 w-3")} />
      {c.label}
      {confidence !== undefined && (
        <span className="opacity-60 text-xs font-normal ml-1">
          {Math.round(confidence * 100)}%
        </span>
      )}
    </div>
  )
}