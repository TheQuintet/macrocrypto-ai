import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { isChartCompact } from '@/components/dashboard/lib/chartTheme'
import { PredictionAccuracyTrendLegend } from '@/components/dashboard/predictions/accuracy/PredictionAccuracyTrendLegend'
import { PredictionAccuracyTrendTooltip } from '@/components/dashboard/predictions/accuracy/PredictionAccuracyTrendTooltip'
import { useContainerWidth } from '@/hooks/useContainerWidth'
import {
  accuracyTrendCaption,
  accuracyTrendLineLabel,
  buildAccuracyTrend,
  formatAccuracyDay,
  formatAccuracyPercent,
  trendLineStyle,
  trendScoreKind,
  trendTargets,
} from '@/lib/predictionAccuracy'
import type { PredictionAccuracy } from '@/types/predictionAccuracy'
import type { PredictionHorizon } from '@/types/predictions'

const DEFAULT_CHART_WIDTH = 320
const CHART_HEIGHT = 200
const CHART_HEIGHT_COMPACT = 160

/** Line, legend and tooltip order. */
const HORIZON_ORDER: PredictionHorizon[] = ['24h', '7d']

/** The full percentage scale, so a dip reads at its true size. */
const Y_DOMAIN: [number, number] = [0, 100]
const Y_TICKS = [0, 25, 50, 75, 100]

type PredictionAccuracyTrendChartProps = {
  /** Every horizon scored so far; each gets its own line. */
  accuracies: PredictionAccuracy[]
  /** Why a horizon's line is missing, one note per missing horizon. */
  gapNotes?: string[]
}

/**
 * 24h and 7d accuracy day by day on one 0–100% scale. Always both, so the
 * horizons can be compared: unlike the rest of the card, it does not follow
 * the chart toggle. The service's bound is drawn as a dashed target, so a
 * slide towards it is visible before it warns.
 */
export function PredictionAccuracyTrendChart({
  accuracies,
  gapNotes = [],
}: PredictionAccuracyTrendChartProps) {
  const { ref, width } = useContainerWidth(DEFAULT_CHART_WIDTH)
  const compact = isChartCompact(width)
  const height = compact ? CHART_HEIGHT_COMPACT : CHART_HEIGHT
  // Lines sharing an axis plot the same figure: price accuracy for both
  // unless both horizons report direction.
  const kind = trendScoreKind(accuracies)
  const rows = buildAccuracyTrend(accuracies, kind)
  const targets = trendTargets(accuracies, kind)
  const lines = HORIZON_ORDER.filter((horizon) =>
    accuracies.some((accuracy) => accuracy.horizon === horizon),
  ).map((horizon) => ({ horizon, ...trendLineStyle(horizon) }))

  // The measured wrapper always mounts, so the width is known by the time
  // enough history arrives to draw.
  return (
    <div ref={ref} className="flex w-full min-w-0 flex-col gap-2">
      <div className="flex flex-col gap-0.5 text-xs text-muted-foreground">
        <p>{accuracyTrendCaption(kind)}</p>
        <p>Both horizons, for comparison: this chart doesn't change with the 24h/7d toggle.</p>
      </div>
      {rows.length < 2 ? (
        <p className="text-sm text-muted-foreground">
          The trend appears once the model has been scored on two or more days.
        </p>
      ) : (
        <>
          <div role="img" aria-label="Forecast accuracy trend">
            <LineChart
              width={width}
              height={height}
              data={rows}
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
                domain={Y_DOMAIN}
                ticks={Y_TICKS}
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
                content={<PredictionAccuracyTrendTooltip lines={lines} />}
                cursor={{
                  stroke: 'var(--muted-foreground)',
                  strokeDasharray: '3 3',
                }}
              />
              {targets.map((target) => (
                <ReferenceLine
                  key={target.value}
                  y={target.value}
                  stroke="var(--warning)"
                  strokeDasharray="4 4"
                />
              ))}
              {lines.map((line) => (
                <Line
                  key={line.horizon}
                  type="monotone"
                  dataKey={line.horizon}
                  name={accuracyTrendLineLabel(line.horizon)}
                  stroke={line.stroke}
                  strokeWidth={2}
                  dot={false}
                  connectNulls
                  activeDot={{ r: 4 }}
                  isAnimationActive={false}
                />
              ))}
            </LineChart>
          </div>
          <PredictionAccuracyTrendLegend lines={lines} targets={targets} />
        </>
      )}
      {gapNotes.map((note) => (
        <p key={note} className="text-xs text-muted-foreground">
          {note}
        </p>
      ))}
    </div>
  )
}
