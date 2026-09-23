import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { RegimePerformanceTooltip } from '@/components/dashboard/regime/RegimePerformanceTooltip'
import { isChartCompact } from '@/components/dashboard/lib/chartTheme'
import { useContainerWidth } from '@/hooks/useContainerWidth'
import { regimeDisplay } from '@/lib/regimeDisplay'
import { regimeSeriesColor } from '@/lib/regimeSeriesColor'
import { sortRegimesByStart } from '@/lib/regimePerformance'
import type { RegimePerformanceRow } from '@/types/regime'

const DEFAULT_CHART_WIDTH = 320
const CHART_HEIGHT = 260
const CHART_HEIGHT_COMPACT = 200

type RegimePerformanceChartProps = {
  rows: RegimePerformanceRow[]
}

type ChartRow = {
  label: string
  avgReturn: number
  row: RegimePerformanceRow
}

function toChartRows(rows: RegimePerformanceRow[]): ChartRow[] {
  return sortRegimesByStart(rows)
    .filter((row) => row.performance.avgReturn != null)
    .map((row) => ({
      label: regimeDisplay(row.regimeType, 'neutral').label,
      avgReturn: row.performance.avgReturn as number,
      row,
    }))
}

function formatPercentTick(value: number) {
  return `${value > 0 ? '+' : ''}${Math.round(value)}%`
}

/** Average BTC return per regime, one bar per regime in its own colour. */
export function RegimePerformanceChart({ rows }: RegimePerformanceChartProps) {
  const { ref, width } = useContainerWidth(DEFAULT_CHART_WIDTH)
  const compact = isChartCompact(width)
  const data = toChartRows(rows)

  return (
    <div ref={ref} className="min-w-0">
      {data.length === 0 ? (
        <p className="py-8 text-center text-xs text-muted-foreground">
          No regime has a measured return yet.
        </p>
      ) : (
        <BarChart
          width={width}
          height={compact ? CHART_HEIGHT_COMPACT : CHART_HEIGHT}
          data={data}
          margin={{ top: 8, right: 8, left: 0, bottom: compact ? 4 : 8 }}
        >
          <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" />
          <XAxis
            dataKey="label"
            tick={{ fontSize: compact ? 9 : 11, fill: 'var(--muted-foreground)' }}
            interval={0}
            angle={compact ? -35 : 0}
            textAnchor={compact ? 'end' : 'middle'}
            height={compact ? 56 : 28}
            stroke="var(--border)"
          />
          <YAxis
            tickFormatter={formatPercentTick}
            tick={{ fontSize: compact ? 9 : 11, fill: 'var(--muted-foreground)' }}
            width={compact ? 40 : 52}
            stroke="var(--border)"
          />
          <ReferenceLine y={0} stroke="var(--muted-foreground)" />
          <Tooltip
            cursor={{ fill: 'var(--muted)', opacity: 0.35 }}
            content={({ active, payload }) => {
              const entry = payload?.[0]?.payload as ChartRow | undefined

              if (!active || !entry) {
                return null
              }

              return <RegimePerformanceTooltip row={entry.row} />
            }}
          />
          <Bar dataKey="avgReturn" radius={[3, 3, 0, 0]}>
            {data.map((entry) => (
              <Cell
                key={entry.row.regimeId}
                fill={regimeSeriesColor(entry.row.regimeType)}
                // The open regime is the one the reader is living in; outline
                // it rather than relying on its position in the row.
                stroke={
                  entry.row.status === 'active'
                    ? 'var(--foreground)'
                    : undefined
                }
                strokeWidth={entry.row.status === 'active' ? 1.5 : 0}
              />
            ))}
          </Bar>
        </BarChart>
      )}
    </div>
  )
}
