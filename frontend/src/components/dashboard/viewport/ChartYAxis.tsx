import { LineChart, YAxis } from 'recharts'
import {
  chartYAxisMargin,
  chartYAxisWidth,
  formatPriceTick,
} from '@/components/dashboard/lib/chartTheme'

type ChartYAxisProps = {
  yDomain: [number, number]
  height: number
  compact?: boolean
  hideXAxis?: boolean
  tickFormatter?: (value: number, compact?: boolean) => string
}

/** Fixed axis that stays visible while the plot pans. */
export function ChartYAxis({
  yDomain,
  height,
  compact = false,
  hideXAxis = false,
  tickFormatter = formatPriceTick,
}: ChartYAxisProps) {
  const axisWidth = chartYAxisWidth(compact)

  return (
    <LineChart
      width={axisWidth}
      height={height}
      data={[{ price: yDomain[0] }, { price: yDomain[1] }]}
      margin={chartYAxisMargin(compact, hideXAxis)}
    >
      <YAxis
        dataKey="price"
        domain={yDomain}
        width={axisWidth}
        tick={{
          fill: 'var(--muted-foreground)',
          fontSize: compact ? 10 : 12,
        }}
        tickLine={false}
        axisLine={false}
        tickFormatter={(value: number) => tickFormatter(value, compact)}
      />
    </LineChart>
  )
}
