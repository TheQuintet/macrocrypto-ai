import { formatConfidencePercent } from '@/components/dashboard/lib/predictionChart'
import { cn } from '@/lib/utils'

type PredictionChartLegendProps = {
  confidence: number
  hasHistory: boolean
}

/**
 * Wide enough that a dash pattern reads as dashes. At the 16px these started
 * at, `border-dashed` renders about one dash and the forecast swatch was
 * indistinguishable from the solid one beside it.
 */
const SWATCH_BASE = 'inline-block w-7 shrink-0 rounded-[2px]'

/**
 * Names every mark on the plot and says what the shaded area means.
 *
 * Swatches carry the same colour and dash as the plot, so the legend can be
 * matched to the chart by eye rather than by reading the labels.
 */
export function PredictionChartLegend({
  confidence,
  hasHistory,
}: PredictionChartLegendProps) {
  const percent = formatConfidencePercent(confidence)

  return (
    <div className="flex flex-col gap-2" role="group" aria-label="Chart legend">
      <ul className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-muted-foreground">
        {hasHistory ? (
          <li className="flex items-center gap-1.5">
            <span aria-hidden="true" className="inline-flex items-center gap-0.5">
              <span className="inline-block h-3 w-1 rounded-[2px] bg-positive" />
              <span className="inline-block h-3 w-1 rounded-[2px] bg-negative" />
            </span>
            Actual price
          </li>
        ) : null}
        <li className="flex items-center gap-1.5">
          <span
            aria-hidden="true"
            className={cn(
              SWATCH_BASE,
              'h-0 border-t-2 border-dashed border-chart-1',
            )}
          />
          Forecast
        </li>
        <li className="flex items-center gap-1.5">
          <span
            aria-hidden="true"
            className={cn(SWATCH_BASE, 'h-3 bg-chart-1/25')}
          />
          {percent} confidence band
        </li>
      </ul>
      <p className="text-xs text-muted-foreground">
        {percent} confidence: price is expected to fall within this shaded
        range.
      </p>
    </div>
  )
}
