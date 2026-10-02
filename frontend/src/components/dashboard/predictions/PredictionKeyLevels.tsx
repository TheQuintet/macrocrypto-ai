import { predictionKeyLevels } from '@/components/dashboard/lib/predictionChart'
import { PredictionSummaryStat } from '@/components/dashboard/predictions/PredictionSummaryStat'
import { formatPrice } from '@/components/dashboard/lib/priceFormat'
import type { PredictionHorizon, PredictionPoint } from '@/types/predictions'

type PredictionKeyLevelsProps = {
  points: PredictionPoint[]
  horizon: PredictionHorizon
}

/**
 * Point cadence the bounds are drawn from — hourly for both horizons. Worded
 * as the forecast's window rather than "the next N hours", since a batch may
 * have been made a while before it is read.
 */
const levelCaption: Record<PredictionHorizon, string> = {
  '24h': 'Widest hourly bounds across the 24-hour forecast',
  '7d': 'Widest hourly bounds across the 7-day forecast',
}

/**
 * The confidence range, as the two prices that bound it.
 *
 * These are the outermost bounds across every forecast point, so they move
 * with both the horizon and the confidence level. Printing the same pair
 * again as a single `low – high` line above only said it twice.
 */
export function PredictionKeyLevels({
  points,
  horizon,
}: PredictionKeyLevelsProps) {
  const levels = predictionKeyLevels(points)

  if (!levels) {
    return null
  }

  return (
    <div
      className="flex flex-col gap-2"
      role="group"
      aria-label="Confidence range"
    >
      <h3 className="text-sm font-medium">Confidence range</h3>
      <PredictionSummaryStat
        label="Expected high"
        value={formatPrice(levels.high)}
        className="text-positive"
      />
      <PredictionSummaryStat
        label="Expected low"
        value={formatPrice(levels.low)}
        className="text-negative"
      />
      <p className="text-xs text-muted-foreground">{levelCaption[horizon]}</p>
    </div>
  )
}
