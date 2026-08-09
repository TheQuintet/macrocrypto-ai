export const DEFAULT_CHART_POINT_WIDTH = 28
export const MIN_CHART_POINT_WIDTH = 8
export const MAX_CHART_POINT_WIDTH = 72
export const CHART_ZOOM_FACTOR = 1.25

export function clampChartPointWidth(value: number) {
  return Math.min(MAX_CHART_POINT_WIDTH, Math.max(MIN_CHART_POINT_WIDTH, value))
}

export function zoomChartPointWidth(current: number, direction: 'in' | 'out') {
  const next =
    direction === 'in'
      ? current * CHART_ZOOM_FACTOR
      : current / CHART_ZOOM_FACTOR
  return clampChartPointWidth(next)
}
