import type {
  PredictionHistoryInterval,
  PredictionHistoryRange,
  PredictionHorizon,
} from '@/types/predictions'

/** Spacing between forecast points: hourly for 24h, daily for 7d. */
export const PREDICTION_STEP_MS: Record<PredictionHorizon, number> = {
  '24h': 60 * 60 * 1000,
  '7d': 24 * 60 * 60 * 1000,
}

/** Forecast points the endpoint returns per horizon. */
export const PREDICTION_POINT_COUNT: Record<PredictionHorizon, number> = {
  '24h': 24,
  '7d': 7,
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
 * of now; the surplus is what the zoom control has left to reveal. Fetching
 * it up front keeps zooming instant and costs one request either way.
 *
 * Both ranges are chosen so the interval survives: asking a wider range for
 * finer candles makes the service merge them instead, so `7d`+`1h` is the
 * most hourly history available and `30d`+`1d` the most daily.
 */
export const HISTORY_WINDOW: Record<PredictionHorizon, PredictionHistoryWindow> =
  {
    '24h': { range: '7d', interval: '1h', candles: 168 },
    '7d': { range: '30d', interval: '1d', candles: 30 },
  }
