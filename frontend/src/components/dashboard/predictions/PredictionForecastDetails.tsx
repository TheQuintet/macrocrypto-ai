import {
  formatConfidencePercent,
  formatPredictionTime,
} from '@/components/dashboard/lib/predictionChart'
import {
  formatPrice,
  formatSignedPercent,
} from '@/components/dashboard/lib/priceFormat'
import { PredictionTooltipRow } from '@/components/dashboard/predictions/PredictionTooltipRow'
import type { PredictionChartRow } from '@/types/predictions'

type PredictionForecastDetailsProps = {
  row: PredictionChartRow
  confidence: number
  currentPrice: number | null
}

/**
 * Model detail for a point: the value, its bounds where it has them, and its
 * drift from now.
 *
 * A row over the history carries a fitted value and no band — only the
 * forecast half has one — so the bound rows are omitted rather than printed
 * as zeroes.
 */
export function PredictionForecastDetails({
  row,
  confidence,
  currentPrice,
}: PredictionForecastDetailsProps) {
  const predicted = row.predicted ?? row.fit ?? null
  const hasBounds = row.lower != null && row.upper != null
  const changePercent =
    predicted != null && currentPrice != null && currentPrice !== 0
      ? ((predicted - currentPrice) / currentPrice) * 100
      : null

  return (
    <>
      <p className="mb-1 font-medium">{formatPredictionTime(row.timeMs)}</p>
      {predicted == null ? null : (
        <PredictionTooltipRow
          label={row.kind === 'forecast' ? 'Predicted' : 'Model fit'}
          value={formatPrice(predicted)}
        />
      )}
      {hasBounds ? (
        <>
          <PredictionTooltipRow
            label="Upper bound"
            value={formatPrice(row.upper!)}
          />
          <PredictionTooltipRow
            label="Lower bound"
            value={formatPrice(row.lower!)}
          />
          <PredictionTooltipRow
            label="Range width"
            value={formatPrice(row.upper! - row.lower!)}
          />
        </>
      ) : null}
      {changePercent == null ? null : (
        <PredictionTooltipRow
          label="vs current"
          value={formatSignedPercent(changePercent)}
        />
      )}
      {hasBounds ? (
        <p className="pt-0.5 text-muted-foreground">
          {formatConfidencePercent(confidence)} confidence
        </p>
      ) : null}
    </>
  )
}
