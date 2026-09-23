import { RegimeConfidenceScale } from '@/components/dashboard/regime/RegimeConfidenceScale'
import {
  clampConfidence,
  confidenceDisplay,
  formatConfidence,
  formatConfidenceBand,
} from '@/lib/regimeDisplay'
import { cn } from '@/lib/utils'

type RegimeConfidenceMeterProps = {
  confidence: number
}

/** How sure the classifier is, coloured by that figure rather than by stance. */
export function RegimeConfidenceMeter({
  confidence,
}: RegimeConfidenceMeterProps) {
  const value = clampConfidence(confidence)
  const tone = confidenceDisplay(value)

  return (
    <div className="flex min-w-0 flex-col gap-1.5">
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-xs text-muted-foreground">Confidence</span>
        <span className={cn('text-sm font-medium tabular-nums', tone.toneClass)}>
          {`${formatConfidence(confidence)} ${formatConfidenceBand(tone.band)}`}
        </span>
      </div>
      <div
        role="meter"
        aria-label="Regime classification confidence"
        aria-valuenow={Math.round(value)}
        aria-valuemin={0}
        aria-valuemax={100}
        data-confidence-band={tone.band}
        className="h-1.5 w-full overflow-hidden rounded-full bg-muted"
      >
        <div
          className={cn('h-full rounded-full', tone.barClass)}
          style={{ width: `${value}%` }}
        />
      </div>
      <RegimeConfidenceScale />
    </div>
  )
}
