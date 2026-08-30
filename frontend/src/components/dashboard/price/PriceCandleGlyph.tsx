import { candleDirection, candleLayout } from '@/components/dashboard/lib/candleGeometry'
import type { ChartCandle } from '@/types/chart'

const GLYPH = { width: 10, height: 48, padY: 1 }

const DIRECTION_COLOR = {
  up: 'var(--positive)',
  down: 'var(--negative)',
} as const

type PriceCandleGlyphProps = {
  candle: ChartCandle
}

/**
 * Tiny OHLC candle so the tooltip can show high above the body and low
 * below it, matching the plot without needing to scan the numbers.
 */
export function PriceCandleGlyph({ candle }: PriceCandleGlyphProps) {
  const slotHeight = GLYPH.height - GLYPH.padY * 2
  const layout = candleLayout(candle, 0, GLYPH.padY, GLYPH.width, slotHeight)
  const color = DIRECTION_COLOR[candleDirection(candle)]

  return (
    <svg
      aria-hidden="true"
      viewBox={`0 0 ${GLYPH.width} ${GLYPH.height}`}
      className="h-12 w-2.5 shrink-0"
    >
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
    </svg>
  )
}
