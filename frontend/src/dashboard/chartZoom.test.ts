import { describe, expect, it } from 'vitest'
import {
  DEFAULT_CHART_POINT_WIDTH,
  MAX_CHART_POINT_WIDTH,
  MIN_CHART_POINT_WIDTH,
  clampChartPointWidth,
  zoomChartPointWidth,
} from '@/dashboard/chart-zoom'

describe('clampChartPointWidth', () => {
  it('leaves values inside the allowed range unchanged', () => {
    expect(clampChartPointWidth(DEFAULT_CHART_POINT_WIDTH)).toBe(
      DEFAULT_CHART_POINT_WIDTH,
    )
  })

  it('clamps below the minimum', () => {
    expect(clampChartPointWidth(1)).toBe(MIN_CHART_POINT_WIDTH)
  })

  it('clamps above the maximum', () => {
    expect(clampChartPointWidth(1_000)).toBe(MAX_CHART_POINT_WIDTH)
  })
})

describe('zoomChartPointWidth', () => {
  it('zooms in by the chart zoom factor', () => {
    expect(zoomChartPointWidth(20, 'in')).toBe(25)
  })

  it('zooms out by the chart zoom factor', () => {
    expect(zoomChartPointWidth(25, 'out')).toBe(20)
  })

  it('does not zoom in past the maximum', () => {
    expect(zoomChartPointWidth(MAX_CHART_POINT_WIDTH, 'in')).toBe(
      MAX_CHART_POINT_WIDTH,
    )
  })

  it('does not zoom out past the minimum', () => {
    expect(zoomChartPointWidth(MIN_CHART_POINT_WIDTH, 'out')).toBe(
      MIN_CHART_POINT_WIDTH,
    )
  })
})
