import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

type PredictionSummaryStatProps = {
  label: string
  value: ReactNode
  className?: string
}

/** One label/value row in the forecast summary. */
export function PredictionSummaryStat({
  label,
  value,
  className,
}: PredictionSummaryStatProps) {
  return (
    <div
      className="flex items-center justify-between gap-4"
      role="group"
      aria-label={label}
    >
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className={cn('font-mono text-sm tabular-nums', className)}>
        {value}
      </span>
    </div>
  )
}
