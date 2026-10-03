import { useState } from 'react'
import {
  CartesianGrid,
  Line,
  LineChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import {
  chartYAxisWidth,
  formatPriceTick,
  isChartCompact,
} from '@/components/dashboard/lib/chartTheme'
import { ChartZoomControls } from '@/components/dashboard/controls/ChartZoomControls'
import { PredictionAccuracyComparisonLegend } from '@/components/dashboard/predictions/accuracy/PredictionAccuracyComparisonLegend'
import { PredictionAccuracyComparisonTooltip } from '@/components/dashboard/predictions/accuracy/PredictionAccuracyComparisonTooltip'
import { useContainerWidth } from '@/hooks/useContainerWidth'
import {
  comparisonMaxZoom,
  comparisonZoomPoints,
  formatAccuracyDay,
  formatComparisonSpan,
} from '@/lib/predictionAccuracy'
import type { PredictionAccuracyPoint } from '@/types/predictionAccuracy'
import type { PredictionHorizon } from '@/types/predictions'

const DEFAULT_CHART_WIDTH = 320
const CHART_HEIGHT = 200
const CHART_HEIGHT_COMPACT = 160

/** Past this many forecasts, per-point dots crowd into a solid band. */
const MAX_DOTTED_POINTS = 60

type PredictionAccuracyComparisonChartProps = {
  points: PredictionAccuracyPoint[]
  horizon: PredictionHorizon
}

/**
 * Each scored forecast against the price it was for. Where the dashed line
 * leaves the solid one is where the model missed, and by how much.
 *
 * Zooming in keeps the most recent stretch and zooming out gives history
 * back, the same +/- as the forecast chart; there is no panning.
 */
export function PredictionAccuracyComparisonChart({
  points,
  horizon,
}: PredictionAccuracyComparisonChartProps) {
  const { ref, width } = useContainerWidth(DEFAULT_CHART_WIDTH)
  const compact = isChartCompact(width)
  const height = compact ? CHART_HEIGHT_COMPACT : CHART_HEIGHT
  const [zoom, setZoom] = useState(0)
  const maxZoom = comparisonMaxZoom(points)
  const visible = comparisonZoomPoints(points, Math.min(zoom, maxZoom))
  const dot = visible.length > MAX_DOTTED_POINTS ? false : { r: 2 }

  return (
    <div ref={ref} className="flex w-full min-w-0 flex-col gap-2">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="text-xs text-muted-foreground">
          {formatComparisonSpan(visible)}
        </span>
        <ChartZoomControls
          label="Comparison zoom"
          value={zoom}
          min={0}
          max={maxZoom}
          onZoomIn={() => setZoom((level) => Math.min(maxZoom, level + 1))}
          onZoomOut={() => setZoom((level) => Math.max(0, level - 1))}
        />
      </div>
      <div
        role="img"
        aria-label={`Predicted vs actual BTC price, ${horizon} forecasts`}
      >
        <LineChart
          width={width}
          height={height}
          data={visible}
          margin={{ top: 8, right: 12, left: 0, bottom: 0 }}
        >
          <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" />
          <XAxis
            dataKey="timeMs"
            type="number"
            scale="time"
            domain={['dataMin', 'dataMax']}
            tickFormatter={formatAccuracyDay}
            tick={{
              fill: 'var(--muted-foreground)',
              fontSize: compact ? 10 : 11,
            }}
            tickLine={false}
            axisLine={{ stroke: 'var(--border)' }}
            minTickGap={compact ? 32 : 24}
          />
          {/* `$64k` ticks: the card column is narrow at every width. */}
          <YAxis
            domain={['auto', 'auto']}
            tickFormatter={(value: number) => formatPriceTick(value, true)}
            tick={{
              fill: 'var(--muted-foreground)',
              fontSize: compact ? 10 : 11,
            }}
            tickLine={false}
            axisLine={false}
            width={chartYAxisWidth(true)}
          />
          <Tooltip
            content={<PredictionAccuracyComparisonTooltip />}
            cursor={{
              stroke: 'var(--muted-foreground)',
              strokeDasharray: '3 3',
            }}
          />
          <Line
            type="monotone"
            dataKey="actual"
            name="Actual price"
            stroke="var(--foreground)"
            strokeWidth={1.5}
            dot={dot}
            activeDot={{ r: 4 }}
            isAnimationActive={false}
          />
          <Line
            type="monotone"
            dataKey="predicted"
            name="Predicted price"
            stroke="var(--chart-1)"
            strokeWidth={2}
            strokeDasharray="5 4"
            dot={dot}
            activeDot={{ r: 4 }}
            isAnimationActive={false}
          />
        </LineChart>
      </div>
      <PredictionAccuracyComparisonLegend />
    </div>
  )
}
