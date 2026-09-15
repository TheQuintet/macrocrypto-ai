import { clampConfidence, formatConfidence } from '@/lib/regimeDisplay'
import { cn } from '@/lib/utils'

type SimilarPeriodConfidenceProps = {
  score: number
  className?: string
}

/**
 * How close the match is, as a figure and a bar.
 *
 * Neutral-coloured on purpose: a strong match to a period BTC fell through is
 * not good news, so tinting confidence green would read as a recommendation.
 */
export function SimilarPeriodConfidence({
  score,
  className,
}: SimilarPeriodConfidenceProps) {
  const value = clampConfidence(score)

  return (
    <div className={cn('flex min-w-0 flex-col gap-1', className)}>
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-xs text-muted-foreground">Match</span>
        <span className="text-sm font-medium tabular-nums">
          {formatConfidence(score)}
        </span>
      </div>
      <div
        role="meter"
        aria-label="Similarity to the current environment"
        aria-valuenow={Math.round(value)}
        aria-valuemin={0}
        aria-valuemax={100}
        className="h-1.5 w-full overflow-hidden rounded-full bg-muted"
      >
        <div
          className="h-full rounded-full bg-foreground/60"
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  )
}
