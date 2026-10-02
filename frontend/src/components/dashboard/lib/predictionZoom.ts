import type { PredictionChartRow } from '@/types/predictions'

/**
 * How much actual price sits behind the forecast, and how far that can be
 * pulled back.
 *
 * Zero is the resting state: exactly as much history as forecast, so a view
 * labelled "7d" shows seven days either side of the forecast start and the
 * toggle describes what is on screen. Zooming out asks for more context
 * deliberately, rather than the chart quietly showing a month under a
 * seven-day label.
 */
export const PREDICTION_ZOOM_MIN = 0
export const PREDICTION_ZOOM_MAX = 4

export function clampPredictionZoom(value: number) {
  return Math.min(PREDICTION_ZOOM_MAX, Math.max(PREDICTION_ZOOM_MIN, value))
}

/** Zooming *in* narrows the window back toward the forecast. */
export function zoomPredictionStep(current: number, direction: 'in' | 'out') {
  return clampPredictionZoom(direction === 'in' ? current - 1 : current + 1)
}

/**
 * Candles to show at this zoom level.
 *
 * Steps are spaced geometrically from the forecast's own length at rest to
 * everything fetched at the last step, so each click widens the window by
 * the same ratio whatever the horizon. A fixed ratio suited one horizon only:
 * it stopped the 24h view short of its week of candles, and spent the 7d
 * view's last step on a sliver of its month.
 *
 * Never fewer than the forecast covers, and never more than were fetched —
 * so the two halves stay comparable and the control stops where the data does.
 */
export function visibleHistoryCount(
  zoom: number,
  forecastCount: number,
  availableCount: number,
) {
  if (availableCount <= forecastCount) {
    return availableCount
  }

  const reach = availableCount / Math.max(forecastCount, 1)
  const wanted = Math.round(
    forecastCount *
      reach ** (clampPredictionZoom(zoom) / PREDICTION_ZOOM_MAX),
  )

  return Math.min(Math.max(wanted, forecastCount), availableCount)
}

/** True when zooming out further would show nothing new. */
export function isFullyZoomedOut(
  zoom: number,
  forecastCount: number,
  availableCount: number,
) {
  return (
    visibleHistoryCount(zoom, forecastCount, availableCount) >= availableCount
  )
}

/**
 * The rows on screen at this zoom level: everything from the forecast start
 * on, plus as much of the history before it as the zoom allows.
 *
 * Sliced by position, not by kind, so rows stay in time order even when a
 * batch is old enough for candles to run on past the forecast start.
 */
export function visiblePredictionRows(
  rows: PredictionChartRow[],
  zoom: number,
) {
  const startIndex = rows.findIndex((row) => row.kind === 'forecast')

  if (startIndex < 0) {
    return rows
  }

  const shown = visibleHistoryCount(zoom, rows.length - startIndex, startIndex)

  return rows.slice(startIndex - shown)
}
