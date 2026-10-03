import {
  describePredictionCoverage,
  formatPredictionCoverage,
  predictionConfidencePercent,
} from '@/components/dashboard/lib/predictionConfidence'
import { PredictionConfidenceScale } from '@/components/dashboard/predictions/PredictionConfidenceScale'

type PredictionConfidenceMeterProps = {
  confidence: number
}

/**
 * The selected interval's coverage, read neutrally.
 *
 * One colour at every level, matching the band it describes: a green 95% and
 * a red 70% read as a good and a bad forecast, when all they differ in is how
 * wide a range was asked for.
 */
export function PredictionConfidenceMeter({
  confidence,
}: PredictionConfidenceMeterProps) {
  const percent = predictionConfidencePercent(confidence)
  const description = describePredictionCoverage(confidence)

  return (
    <div className="flex min-w-0 flex-col gap-1.5">
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-xs text-muted-foreground">Range coverage</span>
        <span className="text-sm font-medium tabular-nums">
          {formatPredictionCoverage(confidence)}
        </span>
      </div>
      <div
        role="meter"
        aria-label="Range coverage"
        aria-valuenow={percent}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuetext={description}
        className="h-1.5 w-full overflow-hidden rounded-full bg-muted"
      >
        <div
          className="h-full rounded-full bg-chart-1"
          style={{ width: `${percent}%` }}
        />
      </div>
      <PredictionConfidenceScale confidence={confidence} />
      <p className="text-xs text-muted-foreground">
        {description}. A coverage level, not a rating of the model.
      </p>
    </div>
  )
}
