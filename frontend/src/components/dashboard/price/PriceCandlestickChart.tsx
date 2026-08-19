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
}: PriceCandlestickChartProps) {
  const series = useMemo(
    () => data.map((candle) => ({ ...candle, range: [candle.low, candle.high] })),
    [data],
  )

  return (
    <BarChart
      width={width}
      height={height}
      data={series}
      margin={chartPlotMargin(compact)}
    >
      <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" />
      <XAxis
        dataKey="time"
        tick={{
          fill: 'var(--muted-foreground)',
          fontSize: compact ? 10 : 11,
        }}
        tickLine={false}
        axisLine={{ stroke: 'var(--border)' }}
        minTickGap={compact ? 40 : 28}
        angle={compact ? 0 : -25}
        textAnchor={compact ? 'middle' : 'end'}
        height={compact ? 32 : 56}
      />
      <YAxis domain={yDomain} hide width={0} />
      <Tooltip
        content={<PriceCandleTooltip />}
        cursor={<PriceCandleHoverLine />}
      />
      <Bar dataKey="range" shape={<PriceCandle />} isAnimationActive={false} />
    </BarChart>
  )
}
