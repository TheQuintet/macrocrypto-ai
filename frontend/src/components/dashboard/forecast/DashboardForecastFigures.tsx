import { formatPredictionCoverage } from '@/components/dashboard/lib/predictionConfidence'
import {
  formatPrice,
  formatSignedPercent,
  PRICE_PLACEHOLDER,
  priceDirection,
  type PriceDirection,
} from '@/components/dashboard/lib/priceFormat'
import { PredictionKeyLevels } from '@/components/dashboard/predictions/PredictionKeyLevels'
import { PredictionMadeAt } from '@/components/dashboard/predictions/PredictionMadeAt'
import { PredictionSummaryStat } from '@/components/dashboard/predictions/PredictionSummaryStat'
import { PredictionTrendBadge } from '@/components/dashboard/predictions/PredictionTrendBadge'
import { Separator } from '@/components/ui/separator'
import { cn } from '@/lib/utils'
import type { BtcPrediction } from '@/types/predictions'

type DashboardForecastFiguresProps = {
  prediction: BtcPrediction
}

const CHANGE_TONE: Record<PriceDirection, string> = {
  up: 'text-positive',
  down: 'text-negative',
  flat: 'text-muted-foreground',
}

/**
 * The numbers beside the dashboard's forecast chart: where the model puts
 * price in a day, how far that is from now, and the range around it.
 *
 * Coverage is shown as the range it describes ("85% range"), not graded:
 * it is the level the band was asked for, not a score the model earned.
 */
export function DashboardForecastFigures({
  prediction,
}: DashboardForecastFiguresProps) {
  const tone = CHANGE_TONE[priceDirection(prediction.priceChangePct)]

  return (
    <div className="flex min-w-0 flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div
          className="flex min-w-0 flex-col gap-0.5"
          role="group"
          aria-label="Predicted in 24 hours"
        >
          <span className="text-xs text-muted-foreground">
            Predicted in 24 hours
          </span>
          <span className={cn('font-mono text-2xl tabular-nums', tone)}>
            {formatPrice(prediction.predictedEndPrice)}
          </span>
        </div>
        <PredictionTrendBadge trend={prediction.trend} />
      </div>

      <div className="flex flex-col gap-2">
        <PredictionSummaryStat
          label="Expected change"
          value={
            prediction.priceChangePct == null
              ? PRICE_PLACEHOLDER
              : formatSignedPercent(prediction.priceChangePct)
          }
          className={tone}
        />
        <PredictionSummaryStat
          label="Range coverage"
          value={formatPredictionCoverage(prediction.confidence)}
        />
      </div>

      <Separator />

      <PredictionKeyLevels
        points={prediction.points}
        horizon={prediction.horizon}
      />

      <PredictionMadeAt predictionTime={prediction.predictionTime} />
    </div>
  )
}
