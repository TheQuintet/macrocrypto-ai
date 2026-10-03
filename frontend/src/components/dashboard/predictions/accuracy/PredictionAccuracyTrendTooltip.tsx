import { CHART_TOOLTIP_STYLE } from '@/components/dashboard/lib/chartTheme'
import {
  accuracyTrendLineLabel,
  formatAccuracyDay,
  formatAccuracyPercent,
} from '@/lib/predictionAccuracy'
import { cn } from '@/lib/utils'
import type { AccuracyTrendRow } from '@/types/predictionAccuracy'
import type { PredictionHorizon } from '@/types/predictions'

type TrendTooltipLine = {
  horizon: PredictionHorizon
  swatchClass: string
}

type PredictionAccuracyTrendTooltipProps = {
  active?: boolean
  payload?: { payload?: AccuracyTrendRow }[]
  /** Lines in legend order, with the swatch each is drawn in. */
  lines: TrendTooltipLine[]
}

/** Each horizon's accuracy on the hovered day; a day one skipped says so. */
export function PredictionAccuracyTrendTooltip({
  active,
  payload,
  lines,
}: PredictionAccuracyTrendTooltipProps) {
  const row = payload?.find((entry) => entry.payload)?.payload

  if (!active || !row) {
    return null
  }

  return (
    <div
      role="tooltip"
      className="flex min-w-40 flex-col gap-1 px-2.5 py-2 text-xs"
      style={CHART_TOOLTIP_STYLE}
    >
      <p className="font-medium">{formatAccuracyDay(row.timeMs)}</p>
      {lines.map((line) => (
        <p
          key={line.horizon}
          className="flex items-center justify-between gap-4"
        >
          <span className="flex items-center gap-1.5 text-muted-foreground">
            <span
              aria-hidden="true"
              className={cn('size-2 shrink-0 rounded-full', line.swatchClass)}
            />
            {accuracyTrendLineLabel(line.horizon)}
          </span>
          <span className="font-mono tabular-nums">
            {formatAccuracyPercent(row[line.horizon])}
          </span>
        </p>
      ))}
    </div>
  )
}
