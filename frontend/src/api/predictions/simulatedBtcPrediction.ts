import {
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

/**
 * Matches the ai-service neutral band (`prediction/trend.py`): a change must
 * clear this, exclusively, to read as up or down. A week is allowed twice the
 * drift of a day before it counts as a move.
 */
const NEUTRAL_TREND_THRESHOLD_PCT: Record<PredictionHorizon, number> = {
  '24h': 0.5,
  '7d': 1,
}

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

function trendOf(
  changePct: number,
  horizon: PredictionHorizon,
): PredictionTrend {
  const threshold = NEUTRAL_TREND_THRESHOLD_PCT[horizon]

  if (changePct > threshold) {
    return 'up'
  }

  return changePct < -threshold ? 'down' : 'neutral'
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
     * Straight off the shared curve — the same one the simulated candles
     * sample behind now, so the projection continues them rather than
     * restarting.
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
 *
 * Forward points only, like the real endpoint: its frame starts an hour past
 * the last training row and never includes in-sample fitted values.
 */
export function buildSimulatedPrediction(
  params: PredictionParams,
  nowMs: number,
): PredictionResponse {
  const currentPrice = simulatedCurrentPrice(nowMs)
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
    trend: trendOf(priceChangePct, params.horizon),
    predictions: forecast,
  }
}
