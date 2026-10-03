import { cn } from '@/lib/utils'

/** Wide enough that the forecast's dash pattern reads as dashes. */
const SWATCH_BASE = 'inline-block w-7 shrink-0 rounded-[2px]'

/**
 * Names both lines. The forecast is dashed teal as on the chart above, so
 * it reads as the same thing; the real price is a solid neutral line.
 */
export function PredictionAccuracyComparisonLegend() {
  return (
    <div role="group" aria-label="Predicted vs actual legend">
      <ul className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-muted-foreground">
        <li className="flex items-center gap-1.5">
          <span
            aria-hidden="true"
            className={cn(
              SWATCH_BASE,
              'h-0 border-t-2 border-dashed border-chart-1',
            )}
          />
          Predicted price
        </li>
        <li className="flex items-center gap-1.5">
          <span
            aria-hidden="true"
            className={cn(SWATCH_BASE, 'h-0.5 bg-foreground')}
          />
          Actual price
        </li>
      </ul>
    </div>
  )
}
