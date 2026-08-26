import { describe, expect, it } from 'vitest'
import {
  CHART_COMPACT_MAX_WIDTH,
  CHART_Y_AXIS_WIDTH,
  CHART_Y_AXIS_WIDTH_COMPACT,
  chartPlotMargin,
  chartYAxisMargin,
  chartYAxisWidth,
  formatPriceTick,
  isChartCompact,
} from '@/components/dashboard/lib/chartTheme'

describe('formatPriceTick', () => {
  it('formats full prices with thousands separators', () => {
    expect(formatPriceTick(67_450)).toBe('$67,450')
  })

  it('formats compact prices for narrow screens', () => {
    expect(formatPriceTick(67_450, true)).toBe('$67k')
    expect(formatPriceTick(1_250_000, true)).toBe('$1.3M')
    expect(formatPriceTick(850, true)).toBe('$850')
  })
})

describe('isChartCompact', () => {
  it('is compact below the sm breakpoint once measured', () => {
    expect(isChartCompact(0)).toBe(false)
    expect(isChartCompact(CHART_COMPACT_MAX_WIDTH - 1)).toBe(true)
    expect(isChartCompact(CHART_COMPACT_MAX_WIDTH)).toBe(false)
  })
})

describe('chart theme layout helpers', () => {
  it('shrinks the Y-axis and bottom margin when compact', () => {
    expect(chartYAxisWidth(true)).toBe(CHART_Y_AXIS_WIDTH_COMPACT)
    expect(chartYAxisWidth(false)).toBe(CHART_Y_AXIS_WIDTH)
    expect(chartPlotMargin(true).bottom).toBeLessThan(chartPlotMargin(false).bottom)
    expect(chartYAxisMargin(true).bottom).toBe(chartPlotMargin(true).bottom)
    expect(chartPlotMargin(false, true).bottom).toBe(8)
    expect(chartYAxisMargin(false, true).bottom).toBe(8)
  })
})
