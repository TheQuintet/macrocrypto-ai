import { useMemo } from 'react'
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import {
  CHART_TOOLTIP_STYLE,
  isChartCompact,
} from '@/components/dashboard/lib/chartTheme'
import { useContainerWidth } from '@/hooks/useContainerWidth'
import {
  formatAccuracyDay,
  formatAccuracyPercent,
  historyScore,
  scoreTarget,
  scoreThreshold,
  thresholdTone,
} from '@/lib/predictionAccuracy'
import type {
  AccuracyHistoryPoint,
  AccuracyScoreKind,
  AccuracyThreshold,
} from '@/types/predictionAccuracy'

const DEFAULT_CHART_WIDTH = 320
const CHART_HEIGHT = 200
const CHART_HEIGHT_COMPACT = 160

type PredictionAccuracyTrendChartProps = {
  history: AccuracyHistoryPoint[]
  kind: AccuracyScoreKind
  thresholds: AccuracyThreshold[]
}

type TrendRow = { timeMs: number; score: number | null }

function formatTooltipValue(value: unknown) {
  return [formatAccuracyPercent(Number(value)), 'Accuracy'] as [string, string]
}

function formatTooltipLabel(label: unknown) {
  return formatAccuracyDay(Number(label))
}

/**
 * The headline score day by day, with the service's bound drawn as a
 * dashed target so a slide towards it is visible before it warns.
 */
export function PredictionAccuracyTrendChart({
  history,
  kind,
  thresholds,
}: PredictionAccuracyTrendChartProps) {
  const { ref, width } = useContainerWidth(DEFAULT_CHART_WIDTH)
  const compact = isChartCompact(width)
  const height = compact ? CHART_HEIGHT_COMPACT : CHART_HEIGHT
  const target = scoreTarget(kind, thresholds)
  // Same tone as the headline score: green while healthy, amber on a warning.
  const tone = thresholdTone(scoreThreshold(kind, thresholds))
  const lineColor = tone ? `var(--${tone})` : 'var(--primary)'

  const data = useMemo<TrendRow[]>(
    () =>
      history.map((point) => ({
        timeMs: point.timeMs,
        score: historyScore(point, kind),
      })),
    [history, kind],
  )

  // The measured wrapper always mounts, so the width is known by the time
  // enough history arrives to draw.
  return (
    <div ref={ref} className="w-full min-w-0">
      {data.length < 2 ? (
        <p className="text-sm text-muted-foreground">
          The trend appears once the model has been scored on two or more days.
        </p>
      ) : (
        <div role="img" aria-label="Forecast accuracy trend">
          <LineChart
            width={width}
            height={height}
            data={data}
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
            <YAxis
              domain={['auto', 'auto']}
              tickFormatter={(value: number) => formatAccuracyPercent(value)}
              tick={{
                fill: 'var(--muted-foreground)',
                fontSize: compact ? 10 : 11,
              }}
              tickLine={false}
              axisLine={false}
              width={compact ? 36 : 44}
            />
            <Tooltip
              contentStyle={CHART_TOOLTIP_STYLE}
              formatter={formatTooltipValue}
              labelFormatter={formatTooltipLabel}
            />
            {target != null ? (
              <ReferenceLine
                y={target}
                stroke="var(--warning)"
                strokeDasharray="4 4"
                ifOverflow="extendDomain"
                label={{
                  value: `Target ${formatAccuracyPercent(target)}`,
                  position: 'insideBottomRight',
                  fill: 'var(--muted-foreground)',
                  fontSize: 11,
                }}
              />
            ) : null}
            <Line
              type="monotone"
              dataKey="score"
              stroke={lineColor}
              strokeWidth={2}
              dot={false}
              connectNulls
              activeDot={{ r: 4 }}
              isAnimationActive={false}
            />
          </LineChart>
        </div>
      )}
    </div>
  )
}
