import { CHART_TOOLTIP_STYLE } from '@/components/dashboard/lib/chartTheme'
import { PriceCandleDetails } from '@/components/dashboard/price/PriceCandleDetails'
import type { ChartCandle } from '@/types/chart'

type PriceCandleTooltipProps = {
  active?: boolean
  payload?: { payload?: ChartCandle }[]
}

/** Floating OHLC overlay for wide charts. */
export function PriceCandleTooltip({
  active,
  payload,
}: PriceCandleTooltipProps) {
  const candle = payload?.[0]?.payload

  if (!active || !candle) {
    return null
  }

  return (
    <div
      role="tooltip"
      className="px-2.5 py-1.5 text-xs"
      style={CHART_TOOLTIP_STYLE}
    >
      <PriceCandleDetails candle={candle} />
    </div>
  )
}
