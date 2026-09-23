import { formatConfidencePercent } from '@/components/dashboard/lib/predictionChart'
import {
  formatPredictionConfidenceBand,
  predictionConfidenceDisplay,
  predictionConfidencePercent,
} from '@/components/dashboard/lib/predictionConfidence'
import { PredictionConfidenceScale } from '@/components/dashboard/predictions/PredictionConfidenceScale'
import { cn } from '@/lib/utils'

type PredictionConfidenceMeterProps = {
  confidence: number
}

/** The selected interval as a named band, so 70 / 85 / 95 is glanceable. */
export function PredictionConfidenceMeter({
  confidence,
}: PredictionConfidenceMeterProps) {
  const percent = predictionConfidencePercent(confidence)
  const tone = predictionConfidenceDisplay(confidence)

  return (
    <div className="flex min-w-0 flex-col gap-1.5">
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-xs text-muted-foreground">Confidence</span>
        <span className={cn('text-sm font-medium tabular-nums', tone.toneClass)}>
          {`${formatConfidencePercent(confidence)} ${formatPredictionConfidenceBand(tone.band)}`}
        </span>
      </div>
      <div
        role="meter"
        aria-label="Forecast confidence"
        aria-valuenow={percent}
        aria-valuemin={0}
        aria-valuemax={100}
        data-confidence-band={tone.band}
        className="h-1.5 w-full overflow-hidden rounded-full bg-muted"
      >
        <div
          className={cn('h-full rounded-full', tone.barClass)}
          style={{ width: `${percent}%` }}
        />
      </div>
      <PredictionConfidenceScale />
    </div>
  )
}
