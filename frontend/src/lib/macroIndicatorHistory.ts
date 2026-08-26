import type { ChartCandle } from '@/types/chart'
import type {
  IndexedIndicatorChartRow,
  IndicatorHistoryFilter,
  MacroIndicator,
  MacroIndicatorApiPeriod,
  MacroIndicatorSeries,
} from '@/types/macroIndicators'
import type { TimeRange } from '@/types/preferences'
import { TIME_RANGE_LOOKBACK_MS } from '@/lib/timeRange'

/** UI time ranges match GET /api/v1/indicators `period` values. */
export function indicatorApiPeriod(range: TimeRange): MacroIndicatorApiPeriod {
  return range
}

/** Keep observations that fall inside the same lookback as the BTC chart. */
export function filterIndicatorsToTimeRange(
  indicators: MacroIndicator[],
  range: TimeRange,
  nowMs: number,
): MacroIndicator[] {
  const startMs = nowMs - TIME_RANGE_LOOKBACK_MS[range]
  return indicators.filter((row) => Date.parse(row.time) >= startMs)
}

/** Limit history to one series, or keep every series when the filter is `all`. */
export function filterIndicatorsByName(
  indicators: MacroIndicator[],
  name: IndicatorHistoryFilter,
): MacroIndicator[] {
  if (name === 'all') return indicators
  return indicators.filter(
    (row) => row.indicator_name.toLowerCase() === name,
  )
}

export function formatIndicatorTitle(name: string) {
  return name.replace(/_/g, ' ')
}

export function formatIndicatorTimestamp(timeString: string) {
  return new Date(timeString).toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZone: 'UTC',
  })
}

export function formatIndicatorChartLabel(timeString: string) {
  return new Date(timeString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: '2-digit',
    timeZone: 'UTC',
  })
}

/** Group mixed API rows into per-indicator series, oldest → newest. */
export function groupIndicatorsByName(
  indicators: MacroIndicator[],
): MacroIndicatorSeries[] {
  const grouped = new Map<string, MacroIndicator[]>()

  for (const indicator of indicators) {
    const key = indicator.indicator_name
    const existing = grouped.get(key)
    if (existing) {
      existing.push(indicator)
    } else {
      grouped.set(key, [indicator])
    }
  }

  return [...grouped.entries()].map(([name, points]) => {
    const sorted = [...points].sort(
      (left, right) => Date.parse(left.time) - Date.parse(right.time),
    )
    return {
      name,
      points: sorted,
      latest: sorted[sorted.length - 1],
    }
  })
}

/**
 * Rebase a series to 100 at its first observation so CPI, rates, and GDP
 * can share one Y-axis without GDP flattening the rest.
 */
export function indexSeriesToBase100(points: MacroIndicator[]) {
  const baseline = points[0]?.current_value
  if (!baseline) return []

  return points.map((point) => ({
    time: point.time,
    timeMs: Date.parse(point.time),
    value: Math.round((point.current_value / baseline) * 10_000) / 100,
  }))
}

/** Merge irregular FRED calendars onto one time axis for a combined chart. */
export function mergeIndexedIndicatorSeries(
  series: MacroIndicatorSeries[],
): IndexedIndicatorChartRow[] {
  const byTime = new Map<number, IndexedIndicatorChartRow>()

  for (const item of series) {
    for (const point of indexSeriesToBase100(item.points)) {
      const existing = byTime.get(point.timeMs)
      if (existing) {
        existing.values[item.name] = point.value
        continue
      }

      byTime.set(point.timeMs, {
        time: formatIndicatorChartLabel(point.time),
        timeMs: point.timeMs,
        values: { [item.name]: point.value },
      })
    }
  }

  return [...byTime.values()].sort((left, right) => left.timeMs - right.timeMs)
}

const INDEXED_Y_PADDING_RATIO = 0.06

/**
 * Carry each series' last print forward onto BTC candle times so both
 * plots share one X axis. A candle before the first print has no value yet.
 */
export function attachAsOfIndicators(
  candles: ChartCandle[],
  series: MacroIndicatorSeries[],
): ChartCandle[] {
  const cursors = series.map((item) => ({
    name: item.name,
    points: item.points,
    indexed: indexSeriesToBase100(item.points),
    index: -1,
  }))

  return candles.map((candle) => {
    const asOfIndicators: NonNullable<ChartCandle['asOfIndicators']> = {}

    for (const cursor of cursors) {
      while (
        cursor.index + 1 < cursor.indexed.length &&
        cursor.indexed[cursor.index + 1].timeMs <= candle.timeMs
      ) {
        cursor.index += 1
      }

      if (cursor.index < 0) continue

      asOfIndicators[cursor.name] = {
        value: cursor.points[cursor.index].current_value,
        indexed: cursor.indexed[cursor.index].value,
        changePercent: cursor.points[cursor.index].change_percent,
      }
    }

    return { ...candle, asOfIndicators }
  })
}

/** Indexed series keyed like the standalone history chart, one row per candle. */
export function indexedRowsFromCandles(
  candles: ChartCandle[],
): IndexedIndicatorChartRow[] {
  return candles.map((candle) => {
    const values: Record<string, number> = {}
    const prints: Record<string, number> = {}

    for (const [name, print] of Object.entries(candle.asOfIndicators ?? {})) {
      values[name] = print.indexed
      prints[name] = print.value
    }

    return {
      time: candle.time,
      timeMs: candle.timeMs,
      values,
      prints,
    }
  })
}

/** Y range for the indicator pane, from visible as-of indexed prints. */
export function asOfIndexedYDomain(candles: ChartCandle[]): [number, number] {
  let min = Infinity
  let max = -Infinity

  for (const candle of candles) {
    for (const print of Object.values(candle.asOfIndicators ?? {})) {
      min = Math.min(min, print.indexed)
      max = Math.max(max, print.indexed)
    }
  }

  if (!Number.isFinite(min) || !Number.isFinite(max)) {
    return [90, 110]
  }

  const span = max - min
  const padding = span > 0 ? span * INDEXED_Y_PADDING_RATIO : 5
  return [min - padding, max + padding]
}
