import { MarketConditionIcon } from '@/components/dashboard/predictions/accuracy/MarketConditionIcon'
import { CHART_TOOLTIP_STYLE } from '@/components/dashboard/lib/chartTheme'
import {
  formatAccuracyMoment,
  formatPriceGap,
  formatUsdPrice,
  marketConditionLabel,
} from '@/lib/predictionAccuracy'
import type { PredictionAccuracyPoint } from '@/types/predictionAccuracy'

type PredictionAccuracyComparisonTooltipProps = {
  active?: boolean
  payload?: { payload?: PredictionAccuracyPoint }[]
}

/** One scored forecast: what the model said, what happened, and the gap. */
export function PredictionAccuracyComparisonTooltip({
  active,
  payload,
}: PredictionAccuracyComparisonTooltipProps) {
  const point = payload?.find((entry) => entry.payload)?.payload

  if (!active || !point) {
    return null
  }

  return (
    <div
      role="tooltip"
      className="flex min-w-48 flex-col gap-1 px-2.5 py-2 text-xs"
      style={CHART_TOOLTIP_STYLE}
    >
      <p className="font-medium">{formatAccuracyMoment(point.timeMs)}</p>
      <p className="flex items-center justify-between gap-4">
        <span className="flex items-center gap-1.5 text-muted-foreground">
          <span
            aria-hidden="true"
            className="inline-block h-0 w-3 border-t-2 border-dashed border-chart-1"
          />
          Predicted
        </span>
        <span className="font-mono tabular-nums">
          {formatUsdPrice(point.predicted)}
        </span>
      </p>
      <p className="flex items-center justify-between gap-4">
        <span className="flex items-center gap-1.5 text-muted-foreground">
          <span
            aria-hidden="true"
            className="inline-block h-0.5 w-3 bg-foreground"
          />
          Actual
        </span>
        <span className="font-mono tabular-nums">
          {formatUsdPrice(point.actual)}
        </span>
      </p>
      <p className="flex items-center justify-between gap-4">
        <span className="text-muted-foreground">Gap</span>
        <span className="font-mono tabular-nums">
          {formatPriceGap(point.predicted, point.actual)}
        </span>
      </p>
      {point.marketCondition ? (
        <p className="flex items-center gap-1.5 text-muted-foreground">
          <MarketConditionIcon condition={point.marketCondition} />
          {marketConditionLabel(point.marketCondition)}
        </p>
      ) : null}
    </div>
  )
}
