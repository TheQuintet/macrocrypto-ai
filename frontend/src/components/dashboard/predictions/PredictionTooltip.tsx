import { CHART_TOOLTIP_STYLE } from '@/components/dashboard/lib/chartTheme'
import { formatPredictionTime } from '@/components/dashboard/lib/predictionChart'
import { PredictionForecastDetails } from '@/components/dashboard/predictions/PredictionForecastDetails'
import { PriceCandleDetails } from '@/components/dashboard/price/PriceCandleDetails'
import type { ChartCandle } from '@/types/chart'
import type { PredictionChartRow } from '@/types/predictions'

type PredictionTooltipProps = {
  active?: boolean
  payload?: { payload?: PredictionChartRow }[]
  confidence: number
  currentPrice: number | null
}

/** A history row read back as the candle the shared OHLC readout expects. */
function toCandle(row: PredictionChartRow): ChartCandle | null {
  if (row.open == null || row.close == null) {
    return null
  }

  return {
    time: formatPredictionTime(row.timeMs),
    timeMs: row.timeMs,
    open: row.open,
    high: row.high ?? row.open,
    low: row.low ?? row.close,
    close: row.close,
  }
}

/**
 * Point detail for whichever half of the plot is under the cursor.
 *
 * The history half reuses the dashboard's OHLC readout so a candle reads the
 * same on both screens; the forecast half gets bounds and confidence instead,
 * which a candle has no equivalent of.
 */
export function PredictionTooltip({
  active,
  payload,
  confidence,
  currentPrice,
}: PredictionTooltipProps) {
  const row = payload?.find((entry) => entry.payload)?.payload

  if (!active || !row) {
    return null
  }

  const candle = row.kind === 'history' ? toCandle(row) : null

  return (
    <div
      role="tooltip"
      className="flex min-w-52 flex-col gap-1 px-2.5 py-2 text-xs"
      style={CHART_TOOLTIP_STYLE}
    >
      {candle ? (
        <PriceCandleDetails candle={candle} />
      ) : (
        <PredictionForecastDetails
          row={row}
          confidence={confidence}
          currentPrice={currentPrice}
        />
      )}
    </div>
  )
}
