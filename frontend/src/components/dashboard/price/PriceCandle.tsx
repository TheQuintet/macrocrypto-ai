import { candleLayout } from '@/components/dashboard/lib/candleGeometry'
import type { ChartCandle } from '@/types/chart'

/** Recharts hands a custom bar shape its resolved slot plus the datum. */
type PriceCandleProps = {
  x?: number
  y?: number
  width?: number
  height?: number
  payload?: ChartCandle
}

const DIRECTION_COLOR = {
  up: 'var(--positive)',
  down: 'var(--negative)',
} as const

/** One OHLC candle: high-low wick with an open-close body. */
export function PriceCandle({
  x = 0,
  y = 0,
  width = 0,
  height = 0,
  payload,
}: PriceCandleProps) {
  if (!payload) {
    return null
  }

  const layout = candleLayout(payload, x, y, width, height)
  const color = DIRECTION_COLOR[layout.direction]

  return (
    <g>
      <line
        x1={layout.centerX}
        x2={layout.centerX}
        y1={layout.wickTopY}
        y2={layout.wickBottomY}
        stroke={color}
        strokeWidth={1}
      />
      <rect
        x={layout.bodyX}
        y={layout.bodyY}
        width={layout.bodyWidth}
        height={layout.bodyHeight}
        fill={color}
      />
    </g>
  )
}
