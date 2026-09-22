import {
  HISTORY_WINDOW,
  PREDICTION_POINT_COUNT,
  PREDICTION_STEP_MS,
} from '@/api/predictions/predictionWindow'
import { marketPriceAt } from '@/api/predictions/simulatedMarket'
import type {
  PredictionHorizon,
  PredictionParams,
  PredictionPointResponse,
  PredictionResponse,
  PredictionTrend,
} from '@/types/predictions'

/** The model the endpoint defaults to, echoed back in its response. */
export const DEFAULT_PREDICTION_MODEL = 'prophet'

/** Matches the ai-service neutral band: |change| under this reads as flat. */
const NEUTRAL_TREND_THRESHOLD_PCT = 0.5

/**
 * Band half-width at the end of the horizon, as a fraction of price.
 *
 * Set per horizon as well as per confidence: a week of uncertainty is worth
 * several times a day of it, and a higher confidence level has to widen the
 * band visibly, or the selector changes a number and nothing else.
 */
const TERMINAL_SPREAD: Record<PredictionHorizon, Record<number, number>> = {
  '24h': { 0.7: 0.012, 0.85: 0.02, 0.95: 0.03 },
  '7d': { 0.7: 0.03, 0.85: 0.05, 0.95: 0.075 },
}


function roundCents(value: number) {
  return Math.round(value * 100) / 100
}

/** Deterministic anchor price, so a fixed `nowMs` always yields one batch. */
export function simulatedCurrentPrice(nowMs: number) {
  return roundCents(marketPriceAt(nowMs))
}

function trendOf(changePct: number): PredictionTrend {
  if (changePct > NEUTRAL_TREND_THRESHOLD_PCT) {
    return 'up'
  }

  return changePct < -NEUTRAL_TREND_THRESHOLD_PCT ? 'down' : 'neutral'
}

/**
 * In-sample band half-width, as a fraction of price.
 *
 * Flat across the history and much tighter than the forecast's: over a window
 * that already happened the model is fitting known prices, so its uncertainty
 * is residual error rather than a cone.
 */
const FIT_SPREAD: Record<number, number> = {
  0.7: 0.0016,
  0.85: 0.0026,
  0.95: 0.004,
}

/**
 * Bounds fan out with the square root of elapsed horizon, the way a forecast's
 * uncertainty actually grows — a constant-width band would misrepresent what
 * the shaded area means.
 */
function spreadAt(
  price: number,
  progress: number,
  params: PredictionParams,
) {
  const horizonSpread = TERMINAL_SPREAD[params.horizon]
  const terminal = horizonSpread[params.confidence] ?? horizonSpread[0.85]

  return price * terminal * Math.sqrt(progress)
}

/**
 * The model's in-sample fit: what it would have said over the window that
 * already happened. Stands in for the `predictions[]` rows the ai-service
 * will carry once it returns its fit alongside the forecast.
 */
function buildFitPoints(
  params: PredictionParams,
  nowMs: number,
): PredictionPointResponse[] {
  const stepMs = PREDICTION_STEP_MS[params.horizon]
  const count = HISTORY_WINDOW[params.horizon].candles
  const spread = FIT_SPREAD[params.confidence] ?? FIT_SPREAD[0.85]

  return Array.from({ length: count }, (_, index) => {
    // Ends *at* now, the bucket the newest candle occupies. Stopping a step
    // short leaves that candle with no fitted value and breaks the line.
    const timeMs = nowMs - (count - 1 - index) * stepMs
    const fitted = marketPriceAt(timeMs)
    const halfWidth = fitted * spread

    return {
      time: new Date(timeMs).toISOString(),
      predicted_price: roundCents(fitted),
      lower_bound: roundCents(fitted - halfWidth),
      upper_bound: roundCents(fitted + halfWidth),
    }
  })
}

function buildPoints(
  params: PredictionParams,
  startMs: number,
): PredictionPointResponse[] {
  const stepMs = PREDICTION_STEP_MS[params.horizon]
  const count = PREDICTION_POINT_COUNT[params.horizon]

  return Array.from({ length: count }, (_, index) => {
    const step = index + 1
    const progress = step / count
    const timeMs = startMs + step * stepMs
    /**
     * Straight off the shared curve — the same one the fit traces behind now,
     * so the projection continues it rather than restarting.
     *
     * Nothing is eased onto the anchor here: the anchor already *is* this
     * curve at `now`, so there is no step to smooth over, and easing one in
     * flattened the first several points into a straight run before the line
     * caught up with itself.
     */
    const predicted = marketPriceAt(timeMs)
    const spread = spreadAt(predicted, progress, params)

    return {
      time: new Date(timeMs).toISOString(),
      predicted_price: roundCents(predicted),
      lower_bound: roundCents(predicted - spread),
      upper_bound: roundCents(predicted + spread),
    }
  })
}

/**
 * Stand-in prediction batch in the ai-service's own wire shape, so the
 * mapper the live response goes through is the one under test here too.
 */
export function buildSimulatedPrediction(
  params: PredictionParams,
  nowMs: number,
): PredictionResponse {
  const currentPrice = simulatedCurrentPrice(nowMs)
  const fit = buildFitPoints(params, nowMs)
  const forecast = buildPoints(params, nowMs)
  const predictedEndPrice = forecast[forecast.length - 1].predicted_price
  const priceChangePct = roundCents(
    ((predictedEndPrice - currentPrice) / currentPrice) * 100,
  )

  return {
    horizon: params.horizon,
    model_name: DEFAULT_PREDICTION_MODEL,
    confidence: params.confidence,
    prediction_time: new Date(nowMs).toISOString(),
    current_price: currentPrice,
    predicted_end_price: predictedEndPrice,
    price_change_pct: priceChangePct,
    trend: trendOf(priceChangePct),
    predictions: [...fit, ...forecast],
  }
}
