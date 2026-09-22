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

/** `0.85` -> `85%` — the confidence reading shown everywhere on the screen. */
export function formatConfidencePercent(confidence: number) {
  return `${Math.round(confidence * 100)}%`
}

/** 24h steps hourly, 7d steps daily; each axis reads in its own unit. */
export function formatPredictionTick(
  timeMs: number,
  horizon: PredictionHorizon,
) {
  const date = new Date(timeMs)

  if (horizon === '24h') {
    return date.toLocaleTimeString('en-GB', {
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return date.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' })
}

/** Full point label for the tooltip — date and time, whatever the horizon. */
export function formatPredictionTime(timeMs: number) {
  return new Date(timeMs).toLocaleString('en-GB', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/**
 * The model's values for moments that have already happened.
 *
 * Today's endpoint returns only forward points, so this is empty and the
 * chart draws a forward-only forecast. When the ai-service adds its in-sample
 * fit to `predictions[]`, those rows land here and the line extends back over
 * the candles with no frontend change.
 */
export function fitPoints(prediction: BtcPrediction) {
  const boundaryMs = new Date(prediction.predictionTime).getTime()

  return prediction.points.filter((point) => point.timeMs <= boundaryMs)
}

/**
 * The model's values for moments still ahead.
 *
 * Everything the summary reports reads from these: an expected high that
 * counted the in-sample fit would be describing the past.
 */
export function forecastPoints(prediction: BtcPrediction) {
  const boundaryMs = new Date(prediction.predictionTime).getTime()

  return prediction.points.filter((point) => point.timeMs > boundaryMs)
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
 * A candle and the model's value for the same hour merge into one row, which
 * is what puts the fitted line *through* the history rather than beside it.
 * Rows are emitted in time order, so a candle whose timestamp the model has
 * no value for still plots.
 */
export function predictionChartRows(
  prediction: BtcPrediction,
  candles: ChartCandle[] = [],
): PredictionChartRow[] {
  const boundaryMs = new Date(prediction.predictionTime).getTime()
  const byBucket = new Map<number, PredictionChartRow>()

  /**
   * Bucket by cadence, not by exact instant. A candle and the model's value
   * for the same hour are generated from separate clock reads, and a real
   * candle is stamped with its bucket start, so their timestamps agree on the
   * hour but rarely on the millisecond. Keying on the raw value would leave
   * every candle in a row of its own, next to an empty row for the fit.
   */
  const stepMs =
    inferStepMs(prediction.points.map((point) => point.timeMs)) ||
    inferStepMs(candles.map((candle) => candle.timeMs))
  /**
   * Buckets are counted *from* `prediction_time`, not from the epoch. An
   * absolute grid assumes every timestamp sits on a step boundary, which a
   * forecast generated at an arbitrary moment does not; anchoring here makes
   * bucket 0 the moment the forecast was made and everything else a whole
   * number of steps either side of it.
   */
  const bucketOf = (timeMs: number) =>
    stepMs > 0
      ? Math.round((timeMs - boundaryMs) / stepMs)
      : // No cadence to infer from a lone point: fall back to the raw offset,
        // which still puts bucket 0 at the boundary so the split holds.
        timeMs - boundaryMs

  /**
   * Split on the bucket, not the instant. The two queries read the clock a
   * moment apart, so the newest candle can be stamped just *after*
   * `prediction_time` — and comparing raw timestamps then files an actual
   * traded candle as a forecast, which also inflates the count the visible
   * window is sized from.
   */
  const rowAt = (timeMs: number) => {
    const bucket = bucketOf(timeMs)
    const existing = byBucket.get(bucket)
    if (existing) {
      return existing
    }

    const created = emptyRow(timeMs, bucket > 0 ? 'forecast' : 'history')
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

  for (const point of prediction.points) {
    const row = rowAt(point.timeMs)

    /**
     * Only the forecast half carries a band. The legend's promise — that
     * price is expected to fall inside the shaded range — is about what has
     * not happened yet; over the history the same shading would stand for
     * in-sample residual, a different quantity rendered as a sliver.
     */
    if (row.kind === 'forecast') {
      row.predicted = point.predictedPrice
      row.lower = point.lowerBound
      row.upper = point.upperBound
      row.band = [point.lowerBound, point.upperBound]
    } else {
      row.fit = point.predictedPrice
    }
  }

  const rows = [...byBucket.values()].sort((a, b) => a.timeMs - b.timeMs)

  return joinAtBoundary(rows)
}

/**
 * Carry the last history value into `predicted` so the fit and the forecast
 * meet. Without it the two lines break apart at now, which reads as a gap in
 * the model rather than the moment it stops knowing. The zero-width band on
 * the same row is what makes the cone open from a point instead of starting
 * already wide.
 */
function joinAtBoundary(rows: PredictionChartRow[]): PredictionChartRow[] {
  if (!rows.some((row) => row.kind === 'forecast')) {
    return rows
  }

  const history = [...rows].reverse().filter((row) => row.kind === 'history')
  /**
   * Hand over from the last bucket the model actually fitted, not simply the
   * last one with a candle. A feed whose fit stops short of now would
   * otherwise leave the fitted line ending in mid-air while the forecast
   * began a bucket later, with a gap between them.
   */
  const join = history.find((row) => row.fit != null) ?? history[0]
  const joinValue = join?.fit ?? join?.close

  if (!join || joinValue == null) {
    return rows
  }

  join.predicted = joinValue
  join.band = [joinValue, joinValue]

  return rows
}

/** Where the model stops describing the past and starts projecting. */
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
 * Band width read as a reliability signal: a narrow band means the model is
 * confident about where price lands, a wide one means it is not.
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
