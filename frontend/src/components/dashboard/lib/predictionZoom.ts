/**
 * How much actual price sits behind the forecast, and how far that can be
 * pulled back.
 *
 * Zero is the resting state: exactly as much history as forecast, so a view
 * labelled "7d" shows seven days either side of now and the toggle describes
 * what is on screen. Zooming out asks for more context deliberately, rather
 * than the chart quietly showing a month under a seven-day label.
 */
export const PREDICTION_ZOOM_MIN = 0
export const PREDICTION_ZOOM_MAX = 4

/** Each step widens the history window by this much. */
export const PREDICTION_ZOOM_FACTOR = 1.6

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
 * Never fewer than the forecast covers, and never more than were fetched —
 * so the two halves stay comparable and the control stops where the data does.
 */
export function visibleHistoryCount(
  zoom: number,
  forecastCount: number,
  availableCount: number,
) {
  const wanted = Math.round(
    forecastCount * PREDICTION_ZOOM_FACTOR ** clampPredictionZoom(zoom),
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
