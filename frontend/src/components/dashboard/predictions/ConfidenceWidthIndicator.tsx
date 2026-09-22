import {
  predictionBandWidth,
  predictionBandWidthPercent,
} from '@/components/dashboard/lib/predictionChart'
import { getPredictionBandWidthConfig } from '@/components/dashboard/predictions/predictionBandWidthConfig'
import { cn } from '@/lib/utils'
import type { PredictionPoint } from '@/types/predictions'

type ConfidenceWidthIndicatorProps = {
  points: PredictionPoint[]
}

/**
 * How wide the confidence band runs, as a reliability signal: a narrow band
 * pins the forecast down, a wide one says the model is unsure.
 */
export function ConfidenceWidthIndicator({
  points,
}: ConfidenceWidthIndicatorProps) {
  const widthPercent = predictionBandWidthPercent(points)
  const width = predictionBandWidth(widthPercent)
  const config = getPredictionBandWidthConfig(width)

  return (
    <div
      className="flex flex-col gap-1.5"
      role="group"
      aria-label="Confidence range width"
    >
      <div className="flex items-center justify-between gap-4">
        <span className="text-sm text-muted-foreground">Range width</span>
        <span
          className={cn(
            'inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium',
            config.className,
          )}
        >
          <span
            aria-hidden="true"
            className={cn('size-1.5 rounded-full', config.dot)}
          />
          {config.label}
          <span className="font-mono tabular-nums">
            ±{(widthPercent / 2).toFixed(2)}%
          </span>
        </span>
      </div>
      <p className="text-xs text-muted-foreground">{config.description}</p>
    </div>
  )
}
