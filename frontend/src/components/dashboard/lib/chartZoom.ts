export const DEFAULT_CHART_POINT_WIDTH = 28
export const MIN_CHART_POINT_WIDTH = 8
export const MAX_CHART_POINT_WIDTH = 72
export const CHART_ZOOM_FACTOR = 1.25

/**
 * Below this, a candle body is too thin to read an open/close from, so the
 * plot draws a close line instead. Chosen rather than discovered: a 4px
 * body with a 1px wick is already a smear at any realistic density.
 */
export const CANDLE_LEGIBLE_MIN_WIDTH = 5

export function clampChartPointWidth(
  value: number,
  minWidth = MIN_CHART_POINT_WIDTH,
) {
  const floor = Math.min(minWidth, MIN_CHART_POINT_WIDTH)

  return Math.min(MAX_CHART_POINT_WIDTH, Math.max(floor, value))
}

export function zoomChartPointWidth(
  current: number,
  direction: 'in' | 'out',
  minWidth = MIN_CHART_POINT_WIDTH,
) {
  const next =
    direction === 'in'
      ? current * CHART_ZOOM_FACTOR
      : current / CHART_ZOOM_FACTOR

  return clampChartPointWidth(next, minWidth)
}

/**
 * Point width at which `count` points exactly fill `plotWidth`.
 *
 * This is what makes the time range picker mean something: selecting 90d has
 * to show 90 days, not one screen of candles out of 90 days' worth of data.
 * Returns `null` before the plot has been measured, when there is no width to
 * divide up yet.
 */
export function fitChartPointWidth(plotWidth: number, count: number) {
  if (plotWidth <= 0 || count <= 0) {
    return null
  }

  return plotWidth / count
}

/**
 * Starting density for a freshly selected range: the whole range on screen,
 * but never blown up past the normal default just because the range is short.
 *
 * A 24h range of a few dozen candles would otherwise stretch each one to the
 * maximum width, which looks broken next to the same chart at 90d.
 */
export function initialChartPointWidth(plotWidth: number, count: number) {
  const fit = fitChartPointWidth(plotWidth, count)

  if (fit == null) {
    return DEFAULT_CHART_POINT_WIDTH
  }

  return Math.min(DEFAULT_CHART_POINT_WIDTH, fit)
}

/**
 * How far out the user may zoom: to the whole range, and no further.
 *
 * The fixed 8px floor is what made fitting impossible — 500 buckets at 8px is
 * 4000px of strip against a ~1200px plot. Zooming out past the full range
 * only adds empty space, so the fit width is the honest limit.
 */
export function minChartPointWidth(plotWidth: number, count: number) {
  const fit = fitChartPointWidth(plotWidth, count)

  if (fit == null) {
    return MIN_CHART_POINT_WIDTH
  }

  return Math.min(MIN_CHART_POINT_WIDTH, fit)
}

/** Candles this thin cannot be read; the plot switches to a close line. */
export function shouldRenderAsLine(pointWidth: number) {
  return pointWidth < CANDLE_LEGIBLE_MIN_WIDTH
}
