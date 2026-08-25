import { useEffect, useMemo, useRef, useState } from 'react'
import {
  CartesianGrid,
  Line,
  LineChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import {
  CHART_TOOLTIP_STYLE,
  isChartCompact,
} from '@/components/dashboard/lib/chartTheme'
import { formatIndicatorChartLabel } from '@/lib/macroIndicatorHistory'
import type { MacroIndicator } from '@/types/macroIndicators'

const DEFAULT_CHART_WIDTH = 320
const CHART_HEIGHT = 160
const CHART_HEIGHT_COMPACT = 144

type MacroIndicatorHistoryChartProps = {
  points: MacroIndicator[]
  indicatorName: string
}

function formatValueTooltip(value: unknown) {
  const numeric = typeof value === 'number' ? value : Number(value)
  return [numeric.toFixed(2), 'Value'] as [string, string]
}

/** Responsive Recharts line for one indicator series. */
export function MacroIndicatorHistoryChart({
  points,
  indicatorName,
}: MacroIndicatorHistoryChartProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [width, setWidth] = useState(DEFAULT_CHART_WIDTH)

  useEffect(() => {
    const node = containerRef.current
    if (!node) return

    const syncWidth = () => {
      const nextWidth = node.clientWidth
      if (nextWidth > 0) setWidth(nextWidth)
    }

    syncWidth()
    const observer = new ResizeObserver(syncWidth)
    observer.observe(node)
    return () => observer.disconnect()
  }, [])

  const data = useMemo(
    () =>
      points.map((point) => ({
        time: formatIndicatorChartLabel(point.time),
        value: point.current_value,
      })),
    [points],
  )

  const compact = isChartCompact(width)
  const height = compact ? CHART_HEIGHT_COMPACT : CHART_HEIGHT

  return (
    <div
      ref={containerRef}
      className="h-36 w-full min-w-0 sm:h-40"
      role="img"
      aria-label={`${indicatorName} history`}
    >
      <LineChart
        width={width}
        height={height}
        data={data}
        margin={{ top: 8, right: 8, left: 4, bottom: 8 }}
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
          minTickGap={compact ? 28 : 20}
        />
        <YAxis
          domain={['auto', 'auto']}
          tick={{
            fill: 'var(--muted-foreground)',
            fontSize: compact ? 10 : 11,
          }}
          tickLine={false}
          axisLine={false}
          width={compact ? 40 : 48}
        />
        <Tooltip
          contentStyle={CHART_TOOLTIP_STYLE}
          formatter={formatValueTooltip}
        />
        <Line
          type="monotone"
          dataKey="value"
          stroke="var(--chart-1)"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4 }}
          isAnimationActive={false}
        />
      </LineChart>
    </div>
  )
}
