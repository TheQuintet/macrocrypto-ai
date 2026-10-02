import {
  HISTORY_INTERVAL_MS,
  HISTORY_WINDOW,
} from '@/api/predictions/predictionWindow'
import { marketPriceAt } from '@/api/predictions/simulatedMarket'
import type {
  PredictionHistoryInterval,
  PredictionHistoryParams,
  PredictionHistoryResponse,
} from '@/types/predictions'

type PredictionHistoryPoint = PredictionHistoryResponse['points'][number]

type HistoryVolatility = {
  /** Candle-to-candle noise around the curve — what sets the body height. */
  body: number
  /** How far the wicks reach past the body. */
  wick: number
}

/**
 * Noise per candle, as a fraction of price.
 *
 * Scaled to the interval, not the horizon: a daily candle covers roughly an
 * order of magnitude more movement than an hourly one, and both horizons now
 * sit on hourly candles. The window's overall shape comes from the shared
 * market curve, not from here.
 */
const HISTORY_VOLATILITY: Record<PredictionHistoryInterval, HistoryVolatility> =
  {
    '1h': { body: 0.0018, wick: 0.0012 },
    '1d': { body: 0.0075, wick: 0.005 },
  }

function roundCents(value: number) {
  return Math.round(value * 100) / 100
}

/**
 * Deterministic walk landing on the same anchor the simulated forecast
 * departs from, so the candles and the projection meet at one price rather
 * than showing a step at "now".
 *
 * Each candle is stamped at its *open* time, as the data service stamps
 * Binance klines: the newest one opened a step before `endMs` and closed on
 * the anchor at `endMs`.
 */
export function buildSimulatedHistoryPoints(
  params: PredictionHistoryParams,
  endMs: number,
  anchorPrice: number,
): PredictionHistoryPoint[] {
  const stepMs = HISTORY_INTERVAL_MS[params.interval]
  const count = HISTORY_WINDOW[params.horizon].candles
  const volatility = HISTORY_VOLATILITY[params.interval]
  const startMs = endMs - count * stepMs

  const closes = Array.from({ length: count + 1 }, (_, index) => {
    const curve = marketPriceAt(startMs + index * stepMs)
    const jitter =
      (Math.sin(index * 2.1) * 0.6 + Math.sin(index * 0.9) * 0.4) *
      volatility.body

    return curve * (1 + jitter)
  })

  // Land the final close exactly on the anchor the forecast starts from.
  const correction = anchorPrice - closes[count]

  return Array.from({ length: count }, (_, index) => {
    const open = closes[index] + correction * (index / count)
    const close = closes[index + 1] + correction * ((index + 1) / count)
    const extent = ((open + close) / 2) * volatility.wick
    const wickUp = extent * (0.5 + Math.abs(Math.cos(index / 3)))
    const wickDown = extent * (0.5 + Math.abs(Math.sin(index / 4)))

    return {
      timestamp: new Date(startMs + index * stepMs).toISOString(),
      open: roundCents(open),
      high: roundCents(Math.max(open, close) + wickUp),
      low: roundCents(Math.max(1, Math.min(open, close) - wickDown)),
      close: roundCents(close),
    }
  })
}
