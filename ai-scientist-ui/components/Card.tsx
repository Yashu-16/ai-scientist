import { clsx } from "clsx"

interface CardProps {
  children: React.ReactNode
  className?: string
  padding?: "sm" | "md" | "lg"
}

export function Card({ children, className, padding = "md" }: CardProps) {
  return (
    <div className={clsx(
      "bg-white rounded-xl border border-gray-200 shadow-sm",
      padding === "sm" && "p-4",
      padding === "md" && "p-6",
      padding === "lg" && "p-8",
      className
    )}>
      {children}
    </div>
  )
}

export function CardTitle({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <h3 className={clsx("text-sm font-medium text-gray-500 uppercase tracking-wide mb-1", className)}>
      {children}
    </h3>
  )
}

export function CardValue({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <p className={clsx("text-2xl font-semibold text-gray-900", className)}>
      {children}
    </p>
  )
}