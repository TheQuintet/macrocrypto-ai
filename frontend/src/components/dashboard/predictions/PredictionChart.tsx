import { useEffect, useMemo, useRef, useState } from 'react'
import {
  Area,
  Bar,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceLine,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import {
  chartPlotMargin,
  chartYAxisWidth,
  formatPriceTick,
  isChartCompact,
} from '@/components/dashboard/lib/chartTheme'
import { visiblePredictionRows } from '@/components/dashboard/lib/predictionZoom'
import {
  forecastStartMs,
  formatPredictionTick,
  predictionChartRows,
  predictionTickStepMs,
  predictionTicks,
  predictionYDomain,
  usesCompactTicks,
} from '@/components/dashboard/lib/predictionChart'
import { PriceCandle } from '@/components/dashboard/price/PriceCandle'
import { PredictionTooltip } from '@/components/dashboard/predictions/PredictionTooltip'
import type { ChartCandle } from '@/types/chart'
import type { BtcPrediction } from '@/types/predictions'

const DEFAULT_CHART_WIDTH = 320
const DEFAULT_CHART_HEIGHT = 224

/** Room each x-axis label gets — enough for `16 Jun` or `06:00` plus a gap. */
const TICK_SLOT_PX = 80
const TICK_SLOT_PX_COMPACT = 64

type PredictionChartProps = {
  prediction: BtcPrediction
  candles?: ChartCandle[]
  /** Steps of history beyond the forecast's own window; 0 shows a matching one. */
  historyZoom?: number
}

/**
 * One chart for both horizons: the actual candles behind the window, then the
 * projected path and its confidence band from where the forecast starts.
 *
 * The 24h and 7d views differ only in the batch and candles handed to it — a
 * second chart component for the weekly case would be the same plot with
 * different ticks.
 */
export function PredictionChart({
  prediction,
  candles = [],
  historyZoom = 0,
}: PredictionChartProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const [size, setSize] = useState({
    width: DEFAULT_CHART_WIDTH,
    height: DEFAULT_CHART_HEIGHT,
  })

  /**
   * Both dimensions come from the box, not from constants: the plot's own
   * width decides whether its chrome is compact, and that width tracks the
   * card rather than the viewport — so a height picked from a Tailwind
   * breakpoint would leave the SVG short of its container on a wide screen.
   */
  useEffect(() => {
    const node = containerRef.current
    if (!node) return

    const syncSize = () => {
      const { clientWidth, clientHeight } = node
      if (clientWidth > 0 && clientHeight > 0) {
        setSize({ width: clientWidth, height: clientHeight })
      }
    }

    syncSize()
    const observer = new ResizeObserver(syncSize)
    observer.observe(node)
    return () => observer.disconnect()
  }, [])

  /**
   * Trim to the visible window before anything is measured or scaled: the Y
   * domain and the candle width both have to describe what is on screen, not
   * the wider history held in reserve for zooming out.
   */
  const rows = useMemo(
    () =>
      visiblePredictionRows(
        predictionChartRows(prediction, candles),
        historyZoom,
      ),
    [prediction, candles, historyZoom],
  )

  const visibleCandles = useMemo(
    () =>
      rows
        .filter((row) => row.candle)
        .map((row) => ({
          time: row.time,
          timeMs: row.timeMs,
          open: row.open!,
          high: row.high!,
          low: row.low!,
          close: row.close!,
        })),
    [rows],
  )
  const visiblePoints = useMemo(
    () =>
      rows
        .filter((row) => row.lower != null && row.upper != null)
        .map((row) => ({
          time: row.time,
          timeMs: row.timeMs,
          predictedPrice: row.predicted ?? 0,
          lowerBound: row.lower!,
          upperBound: row.upper!,
        })),
    [rows],
  )
  const yDomain = useMemo(
    () =>
      predictionYDomain(visiblePoints, prediction.currentPrice, visibleCandles),
    [visiblePoints, prediction.currentPrice, visibleCandles],
  )
  const candleCount = visibleCandles.length

  const compact = isChartCompact(size.width)
  const compactTicks = usesCompactTicks(yDomain)
  const startMs = forecastStartMs(rows)

  /**
   * Ticks placed on round times rather than left to Recharts, which spaces a
   * numeric axis by evenly divided milliseconds. A 7d view is 300+ hourly
   * rows; the step is chosen from the span and the width, so the axis keeps
   * to a readable number of labels at every zoom level.
   */
  const firstMs = rows[0]?.timeMs ?? 0
  const lastMs = rows[rows.length - 1]?.timeMs ?? 0
  const maxTicks = Math.max(
    2,
    Math.floor(size.width / (compact ? TICK_SLOT_PX_COMPACT : TICK_SLOT_PX)),
  )
  const tickStepMs = predictionTickStepMs(
    lastMs - firstMs,
    maxTicks,
    prediction.horizon,
  )
  const ticks = useMemo(
    () => predictionTicks(firstMs, lastMs, tickStepMs),
    [firstMs, lastMs, tickStepMs],
  )
  /**
   * Size candles against the slots they actually occupy, not every row: the
   * forecast half holds no candles, so dividing by the full row count would
   * halve them for no reason.
   */
  const barSize = Math.max(
    2,
    Math.round(
      ((size.width / Math.max(rows.length, 1)) * rows.length) /
        Math.max(candleCount, 1) /
        2,
    ),
  )

  return (
    <div
      ref={containerRef}
      className="h-56 w-full min-w-0 sm:h-[280px] md:h-[340px]"
      role="img"
      aria-label={`BTC ${prediction.horizon} price forecast`}
    >
      <ComposedChart
        width={size.width}
        height={size.height}
        data={rows}
        margin={chartPlotMargin(compact, true)}
      >
        <CartesianGrid stroke="var(--border)" strokeDasharray="3 3" />
        <XAxis
          dataKey="timeMs"
          type="number"
          scale="time"
          domain={['dataMin', 'dataMax']}
          ticks={ticks.length > 0 ? ticks : undefined}
          tickFormatter={(value: number) =>
            formatPredictionTick(value, tickStepMs)
          }
          tick={{
            fill: 'var(--muted-foreground)',
            fontSize: compact ? 10 : 11,
          }}
          tickLine={false}
          axisLine={{ stroke: 'var(--border)' }}
          minTickGap={compact ? 32 : 24}
        />
        <YAxis
          domain={yDomain ?? ['auto', 'auto']}
          tickFormatter={(value: number) =>
            formatPriceTick(value, compactTicks)
          }
          tick={{
            fill: 'var(--muted-foreground)',
            fontSize: compact ? 10 : 11,
          }}
          tickLine={false}
          axisLine={false}
          width={chartYAxisWidth(compactTicks)}
        />
        <Tooltip
          content={
            <PredictionTooltip
              confidence={prediction.confidence}
              currentPrice={prediction.currentPrice}
            />
          }
          cursor={{ stroke: 'var(--muted-foreground)', strokeDasharray: '3 3' }}
        />
        <Bar
          dataKey="candle"
          name="Historical"
          barSize={barSize}
          shape={<PriceCandle />}
          isAnimationActive={false}
        />
        <Area
          dataKey="band"
          name="Confidence band"
          stroke="none"
          fill="var(--chart-1)"
          fillOpacity={0.22}
          isAnimationActive={false}
          activeDot={false}
          connectNulls={false}
        />
        <Line
          dataKey="predicted"
          name="Predicted price"
          type="monotone"
          stroke="var(--chart-1)"
          strokeWidth={2}
          strokeDasharray="5 4"
          dot={false}
          activeDot={{ r: 4 }}
          isAnimationActive={false}
          connectNulls={false}
        />
        {/*
          Marks the first forecast point, not the current time: a batch is
          served until the next one is made, so the present can be well to
          the right of this line. The label says which it is.
        */}
        {startMs == null ? null : (
          <ReferenceLine
            x={startMs}
            stroke="var(--muted-foreground)"
            strokeDasharray="4 4"
            label={{
              value: 'forecast start',
              position: 'insideTopRight',
              fill: 'var(--muted-foreground)',
              fontSize: compact ? 9 : 10,
            }}
          />
        )}
      </ComposedChart>
    </div>
  )
}
