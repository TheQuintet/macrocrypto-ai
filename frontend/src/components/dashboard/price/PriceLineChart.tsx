import {
  CartesianGrid,
  Line,
  LineChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { ChartPoint } from '@/types/chart'
import {
  chartPlotMargin,
  CHART_TOOLTIP_STYLE,
  formatPriceTooltip,
} from '@/components/dashboard/lib/chartTheme'

type PriceLineChartProps = {
  data: ChartPoint[]
  width: number
  height: number
  yDomain: [number, number]
  compact?: boolean
}

export function PriceLineChart({
  data,
  width,
  height,
  yDomain,
  compact = false,
}: PriceLineChartProps) {
  return (
    <LineChart
      width={width}
      height={height}
      data={data}
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
        contentStyle={CHART_TOOLTIP_STYLE}
        formatter={formatPriceTooltip}
      />
      <Line
        type="monotone"
        dataKey="price"
        stroke="var(--chart-1)"
        strokeWidth={2}
        dot={false}
        activeDot={{ r: 4 }}
        isAnimationActive={false}
      />
    </LineChart>
  )
}
