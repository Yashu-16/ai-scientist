import { clsx } from "clsx"

interface BadgeProps {
  label: string
  variant?: "green" | "yellow" | "red" | "blue" | "gray"
  size?: "sm" | "md"
}

const variants = {
  green:  "bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200",
  yellow: "bg-amber-50 text-amber-700 ring-1 ring-amber-200",
  red:    "bg-red-50 text-red-700 ring-1 ring-red-200",
  blue:   "bg-blue-50 text-blue-700 ring-1 ring-blue-200",
  gray:   "bg-gray-50 text-gray-600 ring-1 ring-gray-200",
}

export function Badge({ label, variant = "gray", size = "md" }: BadgeProps) {
  return (
    <span className={clsx(
      "inline-flex items-center rounded-full font-medium",
      size === "sm" ? "px-2 py-0.5 text-xs" : "px-3 py-1 text-sm",
      variants[variant]
    )}>
      {label}
    </span>
  )
}

export function riskVariant(risk: string): BadgeProps["variant"] {
  return risk === "High" ? "red" : risk === "Medium" ? "yellow" : risk === "Low" ? "green" : "gray"
}

export function evidenceVariant(label: string): BadgeProps["variant"] {
  return label === "Strong" ? "green" : label === "Moderate" ? "yellow" : "red"
}