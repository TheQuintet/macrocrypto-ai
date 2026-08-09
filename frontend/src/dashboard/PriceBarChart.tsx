import {
  Bar,
  BarChart,
  CartesianGrid,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { ChartPoint } from '@/dashboard/chart-point'
import {
  CHART_PLOT_MARGIN,
  CHART_TOOLTIP_STYLE,
  formatPriceTooltip,
} from '@/dashboard/chart-theme'

type PriceBarChartProps = {
  data: ChartPoint[]
  width: number
  height: number
  yDomain: [number, number]
}

export function PriceBarChart({
  data,
  width,
  height,
  yDomain,
}: PriceBarChartProps) {
  return (
    <BarChart
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
      <Bar
        dataKey="price"
        fill="var(--chart-2)"
        radius={[6, 6, 0, 0]}
        isAnimationActive={false}
      />
    </BarChart>
  )
}
