import { describe, expect, it } from 'vitest'
import {
  DEFAULT_CHART_POINT_WIDTH,
  MAX_CHART_POINT_WIDTH,
  MIN_CHART_POINT_WIDTH,
  clampChartPointWidth,
  fitChartPointWidth,
  initialChartPointWidth,
  minChartPointWidth,
  zoomChartPointWidth,
} from '@/components/dashboard/lib/chartZoom'

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

describe('fitChartPointWidth', () => {
  it('divides the plot evenly between the points', () => {
    expect(fitChartPointWidth(1_200, 100)).toBe(12)
  })

  it('has no answer before the plot has been measured', () => {
    expect(fitChartPointWidth(0, 100)).toBeNull()
  })

  it('has no answer with nothing to plot', () => {
    expect(fitChartPointWidth(1_200, 0)).toBeNull()
  })
})

describe('initialChartPointWidth', () => {
  it('fits the whole range when it is denser than the default', () => {
    // 500 buckets in 1200px is the 90d case the range picker felt inert on.
    expect(initialChartPointWidth(1_200, 500)).toBeCloseTo(2.4, 5)
  })

  it('does not stretch a short range past the normal density', () => {
    expect(initialChartPointWidth(1_200, 10)).toBe(DEFAULT_CHART_POINT_WIDTH)
  })

  it('falls back to the default before the plot is measured', () => {
    expect(initialChartPointWidth(0, 500)).toBe(DEFAULT_CHART_POINT_WIDTH)
  })
})

describe('minChartPointWidth', () => {
  it('lets the user zoom out to the whole range, below the fixed floor', () => {
    expect(minChartPointWidth(1_200, 500)).toBeCloseTo(2.4, 5)
  })

  it('keeps the fixed floor when the range already fits', () => {
    expect(minChartPointWidth(1_200, 10)).toBe(MIN_CHART_POINT_WIDTH)
  })

  it('falls back to the fixed floor before the plot is measured', () => {
    expect(minChartPointWidth(0, 500)).toBe(MIN_CHART_POINT_WIDTH)
  })
})

describe('zooming out to the fitted floor', () => {
  it('stops at the whole range rather than adding empty space', () => {
    const fit = minChartPointWidth(1_200, 500)

    expect(zoomChartPointWidth(fit, 'out', fit)).toBeCloseTo(fit, 5)
  })

  it('still zooms back in from the fitted floor', () => {
    const fit = minChartPointWidth(1_200, 500)

    expect(zoomChartPointWidth(fit, 'in', fit)).toBeGreaterThan(fit)
  })

  it('never lets a caller raise the floor above the fixed minimum', () => {
    // A bad `minWidth` must not trap the user above the normal zoom range.
    expect(clampChartPointWidth(8, 40)).toBe(MIN_CHART_POINT_WIDTH)
  })
})
