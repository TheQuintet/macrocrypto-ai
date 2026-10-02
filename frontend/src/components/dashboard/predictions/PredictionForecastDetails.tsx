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
 * Forecast detail for a point: the value, its bounds where it has them, and
 * its drift from the batch's current price.
 *
 * A row without bounds leaves the bound rows out rather than printing them
 * as zeroes. A forecast hour that has since traded — an older batch — also
 * shows the actual close beside the forecast.
 */
export function PredictionForecastDetails({
  row,
  confidence,
  currentPrice,
}: PredictionForecastDetailsProps) {
  const predicted = row.predicted ?? null
  const hasBounds = row.lower != null && row.upper != null
  const changePercent =
    predicted != null && currentPrice != null && currentPrice !== 0
      ? ((predicted - currentPrice) / currentPrice) * 100
      : null

  return (
    <>
      <p className="mb-1 font-medium">{formatPredictionTime(row.timeMs)}</p>
      {predicted == null ? null : (
        <PredictionTooltipRow label="Predicted" value={formatPrice(predicted)} />
      )}
      {row.close == null ? null : (
        <PredictionTooltipRow label="Actual close" value={formatPrice(row.close)} />
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
