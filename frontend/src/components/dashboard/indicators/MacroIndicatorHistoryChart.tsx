import { useEffect, useMemo, useRef, useState } from 'react'
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import {
  CHART_TOOLTIP_STYLE,
  chartPlotMargin,
  isChartCompact,
} from '@/components/dashboard/lib/chartTheme'
import {
  formatIndicatorTitle,
  indexedRowsFromCandles,
  mergeIndexedIndicatorSeries,
} from '@/lib/macroIndicatorHistory'
import { indicatorSeriesColor } from '@/lib/indicatorSeriesColor'
import type { ChartCandle } from '@/types/chart'
import type {
  IndexedIndicatorChartRow,
  MacroIndicatorSeries,
} from '@/types/macroIndicators'

const DEFAULT_CHART_WIDTH = 320
const CHART_HEIGHT = 288
const CHART_HEIGHT_COMPACT = 220

type MacroIndicatorHistoryChartProps = {
  series: MacroIndicatorSeries[]
  candles?: ChartCandle[]
  width?: number
  height?: number
  yDomain?: [number, number]
  compact?: boolean
  syncId?: string
  overlayTooltip?: boolean
  onInspect?: (candle: ChartCandle) => void
}

function formatIndexedTick(value: number) {
  return value.toFixed(0)
}

function formatIndexedTooltip(
  value: unknown,
  name: unknown,
  item: unknown,
) {
  const numeric = typeof value === 'number' ? value : Number(value)
  const key = typeof name === 'string' ? name : String(name)
  const label = formatIndicatorTitle(key)
  const payload =
    item && typeof item === 'object' && 'payload' in item
      ? (item as { payload?: IndexedIndicatorChartRow }).payload
      : undefined
  const print = payload?.prints?.[key]
  if (typeof print === 'number') {
    return [`${print.toFixed(2)} (index ${numeric.toFixed(1)})`, label] as [
      string,
      string,
    ]
  }
  return [`${numeric.toFixed(1)}`, label] as [string, string]
}

function rowsToChartData(rows: IndexedIndicatorChartRow[]) {
  return rows.map((row) => ({
    time: row.time,
    timeMs: row.timeMs,
    prints: row.prints,
    ...row.values,
  }))
}

/** Combined history: one line per indicator, rebased to 100 at window start. */
export function MacroIndicatorHistoryChart({
  series,
  candles,
  width: widthProp,
  height: heightProp,
  yDomain,
  compact: compactProp,
  syncId,
  overlayTooltip = true,
  onInspect,
}: MacroIndicatorHistoryChartProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [measuredWidth, setMeasuredWidth] = useState(DEFAULT_CHART_WIDTH)
  const embedded = widthProp != null && heightProp != null

  useEffect(() => {
    if (embedded) return
    const node = containerRef.current
    if (!node) return

    const syncWidth = () => {
      const nextWidth = node.clientWidth
      if (nextWidth > 0) setMeasuredWidth(nextWidth)
    }

    syncWidth()
    const observer = new ResizeObserver(syncWidth)
    observer.observe(node)
    return () => observer.disconnect()
  }, [embedded])

  const data = useMemo(() => {
    if (candles) {
      return rowsToChartData(indexedRowsFromCandles(candles))
    }
    return rowsToChartData(mergeIndexedIndicatorSeries(series))
  }, [candles, series])

  const width = widthProp ?? measuredWidth
  const compact = compactProp ?? isChartCompact(width)
  const height =
    heightProp ?? (compact ? CHART_HEIGHT_COMPACT : CHART_HEIGHT)
  const margin = embedded
    ? chartPlotMargin(compact, false)
    : {
        top: compact ? 8 : 12,
        right: 12,
        left: 4,
        bottom: compact ? 28 : 8,
      }

  return (
    <div
      ref={containerRef}
      className={
        embedded ? 'h-full w-full min-w-0' : 'h-56 w-full min-w-0 sm:h-72'
      }
      role="img"
      aria-label="Macro indicator history"
    >
      <LineChart
        width={width}
        height={height}
        data={data}
        margin={margin}
        syncId={syncId}
        onMouseMove={(state) => {
          if (!state.isTooltipActive || !candles) return
          const index = Number(state.activeIndex)
          const candle = Number.isInteger(index) ? candles[index] : undefined
          if (candle) onInspect?.(candle)
        }}
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
        {embedded ? (
          <YAxis domain={yDomain ?? ['auto', 'auto']} hide width={0} />
        ) : (
          <YAxis
            domain={['auto', 'auto']}
            tickFormatter={formatIndexedTick}
            tick={{
              fill: 'var(--muted-foreground)',
              fontSize: compact ? 10 : 11,
            }}
            tickLine={false}
            axisLine={false}
            width={compact ? 36 : 44}
          />
        )}
        <Tooltip
          contentStyle={CHART_TOOLTIP_STYLE}
          formatter={formatIndexedTooltip}
          content={overlayTooltip ? undefined : () => null}
          wrapperStyle={overlayTooltip ? undefined : { display: 'none' }}
        />
        {embedded ? null : (
          <Legend
            formatter={(value) =>
              formatIndicatorTitle(String(value)).toUpperCase()
            }
            wrapperStyle={{
              fontSize: compact ? 11 : 12,
              color: 'var(--muted-foreground)',
            }}
          />
        )}
        {series.map((item) => {
          const isCpi = item.name.toLowerCase() === 'cpi'
          return (
            <Line
              key={item.name}
              type={candles ? 'stepAfter' : 'monotone'}
              dataKey={item.name}
              stroke={indicatorSeriesColor(item.name)}
              strokeWidth={isCpi ? 2.5 : 2}
              dot={false}
              connectNulls
              activeDot={{ r: 4 }}
              isAnimationActive={false}
            />
          )
        })}
      </LineChart>
    </div>
  )
}
