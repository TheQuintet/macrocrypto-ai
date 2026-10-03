import type { ChartCandle } from '@/types/chart'
import type {
  BtcPrediction,
  PredictionBandWidth,
  PredictionChartRow,
  PredictionHorizon,
  PredictionKeyLevels,
  PredictionPoint,
  PredictionRowKind,
} from '@/types/predictions'

const MINUTE_MS = 60 * 1000
const HOUR_MS = 60 * MINUTE_MS
const DAY_MS = 24 * HOUR_MS

/** `0.85` -> `85%` — the confidence reading shown everywhere on the screen. */
export function formatConfidencePercent(confidence: number) {
  return `${Math.round(confidence * 100)}%`
}

/**
 * Tick spacings the time axis may use, finest first. Sub-day steps divide a
 * day evenly, so every tick lands on the same clock times day after day.
 */
const TICK_STEPS_MS = [
  HOUR_MS,
  2 * HOUR_MS,
  3 * HOUR_MS,
  6 * HOUR_MS,
  12 * HOUR_MS,
  DAY_MS,
  2 * DAY_MS,
  3 * DAY_MS,
  7 * DAY_MS,
]

/**
 * Finest spacing per horizon. The 7d axis spans a fortnight or more of
 * hourly points, and clock-time ticks across that many days cannot say which
 * day they fall on, so it never ticks finer than daily.
 */
const MIN_TICK_STEP_MS: Record<PredictionHorizon, number> = {
  '24h': HOUR_MS,
  '7d': DAY_MS,
}

/** Smallest step that keeps the axis at or under `maxTicks` labels. */
export function predictionTickStepMs(
  spanMs: number,
  maxTicks: number,
  horizon: PredictionHorizon,
) {
  const target = spanMs / Math.max(maxTicks, 1)
  const floor = MIN_TICK_STEP_MS[horizon]

  return (
    TICK_STEPS_MS.find((step) => step >= floor && step >= target) ??
    TICK_STEPS_MS[TICK_STEPS_MS.length - 1]
  )
}

/**
 * Tick positions on round local times — whole hours for sub-day steps, local
 * midnights for day steps — so labels read `06:00` or `16 Jun` rather than
 * wherever evenly divided milliseconds happen to fall.
 */
export function predictionTicks(startMs: number, endMs: number, stepMs: number) {
  const ticks: number[] = []

  if (stepMs < DAY_MS) {
    const hours = Math.round(stepMs / HOUR_MS)
    const first = new Date(startMs)
    first.setMinutes(0, 0, 0)

    // Walk in real hours rather than `setHours`, so a DST change cannot stall it.
    for (let tick = first.getTime(); tick <= endMs; tick += HOUR_MS) {
      if (tick >= startMs && new Date(tick).getHours() % hours === 0) {
        ticks.push(tick)
      }
    }

    return ticks
  }

  const days = Math.round(stepMs / DAY_MS)
  const cursor = new Date(startMs)
  cursor.setHours(0, 0, 0, 0)
  if (cursor.getTime() < startMs) {
    cursor.setDate(cursor.getDate() + 1)
  }

  for (let index = 0; cursor.getTime() <= endMs; index += 1) {
    if (index % days === 0) {
      ticks.push(cursor.getTime())
    }
    cursor.setDate(cursor.getDate() + 1)
  }

  return ticks
}

/**
 * Axis label for a tick. Day steps read as dates; sub-day steps read as
 * clock times, except at midnight, where the date says the day has turned.
 */
export function formatPredictionTick(timeMs: number, stepMs: number) {
  const date = new Date(timeMs)
  const isMidnight = date.getHours() === 0 && date.getMinutes() === 0

  if (stepMs < DAY_MS && !isMidnight) {
    return date.toLocaleTimeString('en-GB', {
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return date.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })
}

/**
 * Full point label for the tooltip. The weekday is there for the 7d view,
 * where a point is one of 168 hourly ones and the date alone is slow to
 * place within the week.
 */
export function formatPredictionTime(timeMs: number) {
  return new Date(timeMs).toLocaleString('en-GB', {
    weekday: 'short',
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/**
 * How long ago a batch was generated, e.g. `12 min ago`.
 *
 * Batches are produced on a schedule, so a 7d one can be most of a day old
 * when it is read; this is what stops it passing for a forecast made just now.
 */
export function formatForecastAge(predictionTimeMs: number, nowMs: number) {
  const elapsed = Math.max(0, nowMs - predictionTimeMs)

  if (elapsed < MINUTE_MS) {
    return 'just now'
  }

  if (elapsed < HOUR_MS) {
    return `${Math.floor(elapsed / MINUTE_MS)} min ago`
  }

  if (elapsed < 2 * DAY_MS) {
    return `${Math.floor(elapsed / HOUR_MS)} h ago`
  }

  return `${Math.floor(elapsed / DAY_MS)} d ago`
}

/**
 * The cadence of *one* evenly spaced series, as its smallest gap.
 *
 * Inferred rather than passed in so it holds whatever interval the services
 * actually return. Never mix two series into it: the smallest gap would then
 * be how far apart they are misaligned, not how often either one samples.
 */
export function inferStepMs(timestamps: number[]) {
  const sorted = [...new Set(timestamps)].sort((a, b) => a - b)
  let smallest = Infinity

  for (let index = 1; index < sorted.length; index += 1) {
    const gap = sorted[index] - sorted[index - 1]
    if (gap > 0 && gap < smallest) {
      smallest = gap
    }
  }

  return Number.isFinite(smallest) ? smallest : 0
}

function emptyRow(
  timeMs: number,
  kind: PredictionRowKind,
): PredictionChartRow {
  return { kind, time: new Date(timeMs).toISOString(), timeMs }
}

/**
 * The plot's rows, keyed by moment.
 *
 * A candle and a forecast point for the same hour merge into one row, and
 * rows are emitted in time order, so a candle with no forecast beside it
 * still plots.
 *
 * Every point the endpoint returns is a forecast — its frame starts an hour
 * past the last training row and it never sends in-sample fitted values — so
 * every point is drawn as one, whatever its timestamp. Points at or before
 * `prediction_time` (the frame can start before the batch timestamp, and an
 * older batch has more of them) are drawn rather than dropped: dropping them
 * would cut the horizon short and leave the line disagreeing with the end
 * price, trend and key levels, which the service computed over every point.
 * Where candles already exist for those hours the two overlap, which shows
 * how that stretch of the forecast has done so far.
 */
export function predictionChartRows(
  prediction: BtcPrediction,
  candles: ChartCandle[] = [],
): PredictionChartRow[] {
  const points = prediction.points
  /**
   * Buckets are counted *from* the first forecast point, not from the epoch.
   * An absolute grid assumes every timestamp sits on a step boundary, which a
   * forecast generated at an arbitrary moment need not; anchoring here makes
   * bucket 0 the forecast start and everything else a whole number of steps
   * either side of it.
   */
  const anchorMs =
    points.length > 0
      ? Math.min(...points.map((point) => point.timeMs))
      : new Date(prediction.predictionTime).getTime()
  const byBucket = new Map<number, PredictionChartRow>()

  /**
   * Bucket by cadence, not by exact instant. A candle and a forecast point
   * for the same hour come from separate services, so their timestamps agree
   * on the hour but need not agree on the millisecond. Keying on the raw
   * value would leave them in neighbouring rows of their own.
   */
  const stepMs =
    inferStepMs(points.map((point) => point.timeMs)) ||
    inferStepMs(candles.map((candle) => candle.timeMs))
  const bucketOf = (timeMs: number) =>
    stepMs > 0
      ? Math.round((timeMs - anchorMs) / stepMs)
      : // No cadence to infer from a lone point: fall back to the raw offset,
        // which still puts bucket 0 at the forecast start.
        timeMs - anchorMs

  const rowAt = (timeMs: number) => {
    const bucket = bucketOf(timeMs)
    const existing = byBucket.get(bucket)
    if (existing) {
      return existing
    }

    const created = emptyRow(timeMs, 'history')
    byBucket.set(bucket, created)
    return created
  }

  for (const candle of candles) {
    const row = rowAt(candle.timeMs)
    row.open = candle.open
    row.high = candle.high
    row.low = candle.low
    row.close = candle.close
    row.candle = [candle.low, candle.high]
  }

  /**
   * A forecast point is what makes a row part of the forecast; a candle only
   * says what actually traded. So a candle sharing an hour with a point sits
   * in a forecast row, and the band covers every forecast hour.
   */
  for (const point of points) {
    const row = rowAt(point.timeMs)
    row.kind = 'forecast'
    row.predicted = point.predictedPrice
    row.lower = point.lowerBound
    row.upper = point.upperBound
    row.band = [point.lowerBound, point.upperBound]
  }

  const rows = [...byBucket.values()].sort((a, b) => a.timeMs - b.timeMs)

  return joinAtBoundary(rows)
}

/**
 * Carry the last actual close before the forecast into `predicted`, so the
 * projected line starts from where price was instead of floating free a
 * step later. The zero-width band on the same row is what makes the cone
 * open from a point instead of starting already wide.
 */
function joinAtBoundary(rows: PredictionChartRow[]): PredictionChartRow[] {
  const startIndex = rows.findIndex((row) => row.kind === 'forecast')
  // Rows before the forecast exist only because a candle put them there.
  const join = startIndex > 0 ? rows[startIndex - 1] : undefined

  if (!join || join.close == null) {
    return rows
  }

  join.predicted = join.close
  join.band = [join.close, join.close]

  return rows
}

/**
 * Where the forecast starts: its first point. Not the current time — for a
 * batch made a while ago, the candles carry on past it.
 */
export function forecastStartMs(rows: PredictionChartRow[]) {
  return rows.find((row) => row.kind === 'forecast')?.timeMs ?? null
}

/** Widest bounds across the batch — the window's expected high and low. */
export function predictionKeyLevels(
  points: PredictionPoint[],
): PredictionKeyLevels | null {
  if (points.length === 0) {
    return null
  }

  return {
    high: Math.max(...points.map((point) => point.upperBound)),
    low: Math.min(...points.map((point) => point.lowerBound)),
  }
}

/** Y domain padded past the band so it never touches the plot edges. */
const DOMAIN_PADDING_RATIO = 0.04

/** Roughly how many gridlines to aim for when rounding the domain. */
const TARGET_TICK_COUNT = 4

/**
 * A round step near `span / TARGET_TICK_COUNT` — 1, 2 or 5 times a power of
 * ten. Snapping the domain to a multiple of it keeps every gridline evenly
 * spaced, instead of a last tick sitting wherever the data happened to end.
 */
export function niceStep(span: number) {
  if (span <= 0) {
    return 1
  }

  const raw = span / TARGET_TICK_COUNT
  const magnitude = 10 ** Math.floor(Math.log10(raw))
  const normalized = raw / magnitude

  if (normalized <= 1) return magnitude
  if (normalized <= 2) return 2 * magnitude
  if (normalized <= 5) return 5 * magnitude

  return 10 * magnitude
}

export function predictionYDomain(
  points: PredictionPoint[],
  currentPrice: number | null,
  candles: ChartCandle[] = [],
): [number, number] | undefined {
  const levels = predictionKeyLevels(points)
  const highs = candles.map((candle) => candle.high)
  const lows = candles.map((candle) => candle.low)

  if (levels) {
    highs.push(levels.high)
    lows.push(levels.low)
  }

  // Nothing to plot: let Recharts pick rather than centring on a lone price.
  if (highs.length === 0) {
    return undefined
  }

  if (currentPrice != null) {
    highs.push(currentPrice)
    lows.push(currentPrice)
  }

  const high = Math.max(...highs)
  const low = Math.min(...lows)
  const padding = Math.max((high - low) * DOMAIN_PADDING_RATIO, 1)
  const step = niceStep(high - low + padding * 2)

  return [
    Math.floor((low - padding) / step) * step,
    Math.ceil((high + padding) / step) * step,
  ]
}

/**
 * Narrowest price span that survives k-rounded axis ticks.
 *
 * A forecast window can be only a few thousand dollars wide, and at that
 * span `$66k` lands on two neighbouring ticks at once — so those axes get
 * full dollar amounts instead.
 */
export const COMPACT_TICK_MIN_SPAN = 5_000

export function usesCompactTicks(domain: [number, number] | undefined) {
  if (!domain) {
    return true
  }

  return domain[1] - domain[0] >= COMPACT_TICK_MIN_SPAN
}

/** Mean band width across the batch, as a percentage of the predicted price. */
export function predictionBandWidthPercent(points: PredictionPoint[]) {
  if (points.length === 0) {
    return 0
  }

  const total = points.reduce((sum, point) => {
    if (point.predictedPrice === 0) {
      return sum
    }

    return (
      sum +
      ((point.upperBound - point.lowerBound) / point.predictedPrice) * 100
    )
  }, 0)

  return total / points.length
}

/**
 * Band width, bucketed for a glance: how far either side of the forecast line
 * price is projected to range at the selected coverage level. It describes
 * the spread, not how good the model is — any band widens as coverage rises.
 */
export const NARROW_BAND_MAX_PERCENT = 2
export const MEDIUM_BAND_MAX_PERCENT = 5

export function predictionBandWidth(
  widthPercent: number,
): PredictionBandWidth {
  if (widthPercent < NARROW_BAND_MAX_PERCENT) {
    return 'narrow'
  }

  return widthPercent < MEDIUM_BAND_MAX_PERCENT ? 'medium' : 'wide'
}

/** Percent change from the batch's anchor price to an arbitrary point. */
export function changeFromCurrentPercent(
  prediction: BtcPrediction,
  price: number,
) {
  const current = prediction.currentPrice

  if (current == null || current === 0) {
    return null
  }

  return ((price - current) / current) * 100
}
