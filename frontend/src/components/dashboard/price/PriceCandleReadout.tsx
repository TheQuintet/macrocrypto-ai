import { PriceCandleDetails } from '@/components/dashboard/price/PriceCandleDetails'
import type { ChartCandle } from '@/types/chart'

type PriceCandleReadoutProps = {
  candle: ChartCandle | null
}

/**
 * Values for the selected candle, shown under the plot on narrow screens
 * so a floating tooltip does not cover the chart.
 */
export function PriceCandleReadout({ candle }: PriceCandleReadoutProps) {
  return (
    <div
      role="region"
      aria-label="Selected candle"
      className="rounded-lg border border-border bg-muted/40 px-3 py-2 text-xs"
    >
      {candle ? (
        <PriceCandleDetails candle={candle} />
      ) : (
        <p className="text-muted-foreground">
          Tap a candle to see open, high, low, close, and as-of indicator
          prints.
        </p>
      )}
    </div>
  )
}
