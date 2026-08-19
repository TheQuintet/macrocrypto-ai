import { formatPrice } from '@/components/dashboard/lib/priceFormat'
import { CHART_TOOLTIP_STYLE } from '@/components/dashboard/lib/chartTheme'
import type { ChartCandle } from '@/types/chart'

type PriceCandleTooltipProps = {
  active?: boolean
  payload?: { payload?: ChartCandle }[]
}

const OHLC_ROWS = [
  { key: 'open', label: 'Open' },
  { key: 'high', label: 'High' },
  { key: 'low', label: 'Low' },
  { key: 'close', label: 'Close' },
] as const

/** OHLC breakdown for the hovered candle. */
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
      <p className="mb-1 font-medium">{candle.time}</p>
      <dl className="grid grid-cols-[auto_auto] gap-x-3 gap-y-0.5">
        {OHLC_ROWS.map((row) => (
          <div key={row.key} className="contents">
            <dt className="text-muted-foreground">{row.label}</dt>
            <dd className="text-right font-mono tabular-nums">
              {formatPrice(candle[row.key])}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  )
}
