import { describe, expect, it } from 'vitest'
import { makeIndicator } from '@/api/macroIndicators.testHelpers'
import {
  formatIndicatorTitle,
  groupIndicatorsByName,
} from '@/lib/macroIndicatorHistory'

describe('groupIndicatorsByName', () => {
  it('groups mixed observations and sorts each series by time', () => {
    const series = groupIndicatorsByName([
      makeIndicator({
        indicator_name: 'gdp',
        time: '2026-06-01T00:00:00.000Z',
        current_value: 1,
      }),
      makeIndicator({
        indicator_name: 'cpi',
        time: '2026-07-01T00:00:00.000Z',
        current_value: 3,
      }),
      makeIndicator({
        indicator_name: 'cpi',
        time: '2026-05-01T00:00:00.000Z',
        current_value: 2,
      }),
    ])

    expect(series.map((item) => item.name)).toEqual(['gdp', 'cpi'])
    expect(series[1].points.map((point) => point.current_value)).toEqual([2, 3])
    expect(series[1].latest.current_value).toBe(3)
  })

  it('returns an empty list when there are no observations', () => {
    expect(groupIndicatorsByName([])).toEqual([])
  })
})

describe('formatIndicatorTitle', () => {
  it('replaces underscores for display', () => {
    expect(formatIndicatorTitle('federal_funds_rate')).toBe('federal funds rate')
  })
})
