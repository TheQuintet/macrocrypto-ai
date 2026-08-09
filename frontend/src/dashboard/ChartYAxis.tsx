import { LineChart, YAxis } from 'recharts'
import {
  CHART_Y_AXIS_MARGIN,
  CHART_Y_AXIS_WIDTH,
  formatPriceTick,
} from '@/dashboard/chartTheme'

type ChartYAxisProps = {
  yDomain: [number, number]
  height: number
}

/** Fixed price axis that stays visible while the plot pans. */
export function ChartYAxis({ yDomain, height }: ChartYAxisProps) {
  return (
    <LineChart
      width={CHART_Y_AXIS_WIDTH}
      height={height}
      data={[{ price: yDomain[0] }, { price: yDomain[1] }]}
      margin={CHART_Y_AXIS_MARGIN}
    >
      <YAxis
        dataKey="price"
        domain={yDomain}
        width={CHART_Y_AXIS_WIDTH}
        tick={{ fill: 'var(--muted-foreground)', fontSize: 12 }}
        tickLine={false}
        axisLine={false}
        tickFormatter={formatPriceTick}
      />
    </LineChart>
  )
}
