import type {
  PredictionHistoryInterval,
  PredictionHistoryRange,
  PredictionHorizon,
} from '@/types/predictions'

const HOUR_MS = 60 * 60 * 1000

/**
 * Spacing between forecast points. The ai-service forecasts hourly for both
 * horizons (`horizon_hours=168` for 7d), so a week is 168 points, not 7.
 */
export const PREDICTION_STEP_MS: Record<PredictionHorizon, number> = {
  '24h': HOUR_MS,
  '7d': HOUR_MS,
}

/** Forecast points the endpoint returns per horizon. */
export const PREDICTION_POINT_COUNT: Record<PredictionHorizon, number> = {
  '24h': 24,
  '7d': 168,
}

/** Width of one history candle; a candle is stamped at its open time. */
export const HISTORY_INTERVAL_MS: Record<PredictionHistoryInterval, number> = {
  '1h': HOUR_MS,
  '1d': 24 * HOUR_MS,
}

export type PredictionHistoryWindow = {
  range: PredictionHistoryRange
  interval: PredictionHistoryInterval
  /** Candles that range yields at that interval — what zooming out can reach. */
  candles: number
}

/**
 * How much actual price is *fetched* behind each forecast.
 *
 * Deliberately more than is shown at rest. The chart opens with as much
 * history as forecast, so a view labelled "7d" shows seven days either side
 * of the forecast start; the surplus is what the zoom control has left to
 * reveal. Fetching it up front keeps zooming instant and costs one request
 * either way.
 *
 * Both horizons use hourly candles so they share the forecast's own cadence
 * and merge with it bucket for bucket. The data service would otherwise
 * merge anything over its default point cap (500) into coarser candles, so
 * the fetcher asks for the series uncapped — see `fetchPredictionHistory`.
 * `30d` is the smallest range the service offers that still leaves the 7d
 * view something to zoom out to past its resting week.
 */
export const HISTORY_WINDOW: Record<PredictionHorizon, PredictionHistoryWindow> =
  {
    '24h': { range: '7d', interval: '1h', candles: 168 },
    '7d': { range: '30d', interval: '1h', candles: 720 },
  }
