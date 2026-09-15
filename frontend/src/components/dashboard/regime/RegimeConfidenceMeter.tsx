import { clampConfidence, formatConfidence } from '@/lib/regimeDisplay'
import { cn } from '@/lib/utils'
import type { RegimeDisplay } from '@/types/regime'

type RegimeConfidenceMeterProps = {
  confidence: number
  display: RegimeDisplay
}

/** How sure the classifier is, as a figure and a bar in the regime's colour. */
export function RegimeConfidenceMeter({
  confidence,
  display,
}: RegimeConfidenceMeterProps) {
  const value = clampConfidence(confidence)

  return (
    <div className="flex min-w-0 flex-col gap-1.5">
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-xs text-muted-foreground">Confidence</span>
        <span
          className={cn('text-sm font-medium tabular-nums', display.toneClass)}
        >
          {formatConfidence(confidence)}
        </span>
      </div>
      <div
        role="meter"
        aria-label="Regime classification confidence"
        aria-valuenow={Math.round(value)}
        aria-valuemin={0}
        aria-valuemax={100}
        className="h-1.5 w-full overflow-hidden rounded-full bg-muted"
      >
        <div
          className={cn('h-full rounded-full', display.barClass)}
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  )
}
