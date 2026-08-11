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
  CHART_PLOT_MARGIN,
  CHART_TOOLTIP_STYLE,
  formatPriceTooltip,
} from '@/components/dashboard/lib/chartTheme'

type PriceLineChartProps = {
  data: ChartPoint[]
  width: number
  height: number
  yDomain: [number, number]
}

export function PriceLineChart({
  data,
  width,
  height,
  yDomain,
}: PriceLineChartProps) {
  return (
    <LineChart
      width={width}
      height={height}
      data={data}
      margin={CHART_PLOT_MARGIN}
    >
      <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" />
      <XAxis
        dataKey="time"
        tick={{ fill: 'var(--muted-foreground)', fontSize: 11 }}
        tickLine={false}
        axisLine={{ stroke: 'var(--border)' }}
        minTickGap={28}
        angle={-25}
        textAnchor="end"
        height={56}
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
