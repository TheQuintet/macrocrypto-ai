import {
  accuracyTrendLineLabel,
  formatTrendTarget,
} from '@/lib/predictionAccuracy'
import { cn } from '@/lib/utils'
import type { TrendTarget } from '@/types/predictionAccuracy'
import type { PredictionHorizon } from '@/types/predictions'

type TrendLegendLine = {
  horizon: PredictionHorizon
  swatchClass: string
}

type PredictionAccuracyTrendLegendProps = {
  lines: TrendLegendLine[]
  targets: TrendTarget[]
}

/** Wide enough that the target's dash pattern reads as dashes. */
const SWATCH_BASE = 'inline-block w-7 shrink-0 rounded-[2px]'

/** Names both lines by horizon and says what the dashed target is. */
export function PredictionAccuracyTrendLegend({
  lines,
  targets,
}: PredictionAccuracyTrendLegendProps) {
  return (
    <div role="group" aria-label="Accuracy trend legend">
      <ul className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-muted-foreground">
        {lines.map((line) => (
          <li key={line.horizon} className="flex items-center gap-1.5">
            <span
              aria-hidden="true"
              className={cn(SWATCH_BASE, 'h-0.5', line.swatchClass)}
            />
            {accuracyTrendLineLabel(line.horizon)}
          </li>
        ))}
        {targets.map((target) => (
          <li key={target.value} className="flex items-center gap-1.5">
            <span
              aria-hidden="true"
              className={cn(
                SWATCH_BASE,
                'h-0 border-t-2 border-dashed border-warning',
              )}
            />
            {formatTrendTarget(target)}
          </li>
        ))}
      </ul>
    </div>
  )
}
