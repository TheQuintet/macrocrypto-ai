import { useMemo } from 'react'
import { Bar, BarChart, CartesianGrid, Tooltip, XAxis, YAxis } from 'recharts'
import type { ChartCandle } from '@/types/chart'
import { chartPlotMargin } from '@/components/dashboard/lib/chartTheme'
import { PriceCandle } from '@/components/dashboard/price/PriceCandle'
import { PriceCandleHoverLine } from '@/components/dashboard/price/PriceCandleHoverLine'
import { PriceCandleTooltip } from '@/components/dashboard/price/PriceCandleTooltip'

type PriceCandlestickChartProps = {
  data: ChartCandle[]
  width: number
  height: number
  yDomain: [number, number]
  compact?: boolean
  hideXAxis?: boolean
  syncId?: string
  overlayTooltip?: boolean
  onInspect?: (candle: ChartCandle) => void
}

/**
 * OHLC candles.
 *
 * Recharts has no candlestick primitive, so each bucket is a floating bar
 * spanning [low, high] with a custom shape: the bar resolves the high/low
 * pixels, and the shape interpolates the open/close body between them.
 */
export function PriceCandlestickChart({
  data,
  width,
  height,
  yDomain,
  compact = false,
  hideXAxis = false,
  syncId,
  overlayTooltip = true,
  onInspect,
}: PriceCandlestickChartProps) {
  const series = useMemo(
    () => data.map((candle) => ({ ...candle, range: [candle.low, candle.high] })),
    [data],
  )
  const margin = chartPlotMargin(compact, hideXAxis)

  return (
    <BarChart
      width={width}
      height={height}
      data={series}
      margin={margin}
      syncId={syncId}
      onMouseMove={(state) => {
        if (!state.isTooltipActive) return
        const index = Number(state.activeIndex)
        const candle = Number.isInteger(index) ? series[index] : undefined
        if (candle) onInspect?.(candle)
      }}
    >
      <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" />
      <XAxis
        dataKey="time"
        hide={hideXAxis}
        tick={{
          fill: 'var(--muted-foreground)',
          fontSize: compact ? 10 : 11,
        }}
        tickLine={false}
        axisLine={{ stroke: 'var(--border)' }}
        minTickGap={compact ? 40 : 28}
        angle={compact ? 0 : -25}
        textAnchor={compact ? 'middle' : 'end'}
        height={hideXAxis ? 1 : compact ? 32 : 56}
      />
      <YAxis domain={yDomain} hide width={0} />
      <Tooltip
        content={overlayTooltip ? <PriceCandleTooltip /> : () => null}
        cursor={<PriceCandleHoverLine />}
        wrapperStyle={overlayTooltip ? undefined : { display: 'none' }}
      />
      <Bar dataKey="range" shape={<PriceCandle />} isAnimationActive={false} />
    </BarChart>
  )
}
