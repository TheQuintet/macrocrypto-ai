import { forecastPoints } from '@/components/dashboard/lib/predictionChart'
import {
  formatPrice,
  formatSignedPercent,
  PRICE_PLACEHOLDER,
} from '@/components/dashboard/lib/priceFormat'
import { ConfidenceWidthIndicator } from '@/components/dashboard/predictions/ConfidenceWidthIndicator'
import { PredictionConfidenceMeter } from '@/components/dashboard/predictions/PredictionConfidenceMeter'
import { PredictionKeyLevels } from '@/components/dashboard/predictions/PredictionKeyLevels'
import { PredictionSummaryStat } from '@/components/dashboard/predictions/PredictionSummaryStat'
import { PredictionTrendBadge } from '@/components/dashboard/predictions/PredictionTrendBadge'
import { Separator } from '@/components/ui/separator'
import { cn } from '@/lib/utils'
import type { BtcPrediction } from '@/types/predictions'

type PredictionSummaryProps = {
  prediction: BtcPrediction
}

const horizonLabel: Record<BtcPrediction['horizon'], string> = {
  '24h': 'in 24 hours',
  '7d': 'in 7 days',
}

function changeClassName(changePct: number | null) {
  if (changePct == null || changePct === 0) {
    return 'text-muted-foreground'
  }

  return changePct > 0 ? 'text-positive' : 'text-negative'
}

/**
 * The read on the selected window: where price is now, where the model puts
 * it at the end of the horizon, and how much of a range that carries.
 *
 * One box serves both horizons — only the labels change.
 */
export function PredictionSummary({ prediction }: PredictionSummaryProps) {
  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex min-w-0 flex-col gap-0.5">
          <span className="text-xs text-muted-foreground">
            Predicted {horizonLabel[prediction.horizon]}
          </span>
          <span
            className={cn(
              'font-mono text-2xl tabular-nums sm:text-3xl',
              changeClassName(prediction.priceChangePct),
            )}
          >
            {formatPrice(prediction.predictedEndPrice)}
          </span>
        </div>
        <PredictionTrendBadge trend={prediction.trend} />
      </div>

      <div className="flex flex-col gap-2">
        <PredictionSummaryStat
          label="Current price"
          value={
            prediction.currentPrice == null
              ? PRICE_PLACEHOLDER
              : formatPrice(prediction.currentPrice)
          }
        />
        <PredictionSummaryStat
          label="Expected change"
          value={
            prediction.priceChangePct == null
              ? PRICE_PLACEHOLDER
              : formatSignedPercent(prediction.priceChangePct)
          }
          className={cn(changeClassName(prediction.priceChangePct))}
        />
      </div>

      <PredictionConfidenceMeter confidence={prediction.confidence} />

      <Separator />

      <PredictionKeyLevels
        points={forecastPoints(prediction)}
        horizon={prediction.horizon}
      />

      <Separator />

      <ConfidenceWidthIndicator points={forecastPoints(prediction)} />
    </div>
  )
}
