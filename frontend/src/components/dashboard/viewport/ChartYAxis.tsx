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
}

/** Fixed price axis that stays visible while the plot pans. */
export function ChartYAxis({
  yDomain,
  height,
  compact = false,
}: ChartYAxisProps) {
  const axisWidth = chartYAxisWidth(compact)

  return (
    <LineChart
      width={axisWidth}
      height={height}
      data={[{ price: yDomain[0] }, { price: yDomain[1] }]}
      margin={chartYAxisMargin(compact)}
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
        tickFormatter={(value: number) => formatPriceTick(value, compact)}
      />
    </LineChart>
  )
}
