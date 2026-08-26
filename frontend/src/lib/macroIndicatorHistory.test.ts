import { describe, expect, it } from 'vitest'
import { makeIndicator } from '@/api/macroIndicators.testHelpers'
import {
  asOfIndexedYDomain,
  attachAsOfIndicators,
  filterIndicatorsByName,
  filterIndicatorsToTimeRange,
  formatIndicatorTitle,
  groupIndicatorsByName,
  indexSeriesToBase100,
  indexedRowsFromCandles,
  indicatorApiPeriod,
  mergeIndexedIndicatorSeries,
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

describe('indexSeriesToBase100', () => {
  it('rebases the first observation to 100', () => {
    const indexed = indexSeriesToBase100([
      makeIndicator({
        indicator_name: 'cpi',
        time: '2026-05-01T00:00:00.000Z',
        current_value: 200,
      }),
      makeIndicator({
        indicator_name: 'cpi',
        time: '2026-06-01T00:00:00.000Z',
        current_value: 220,
      }),
    ])

    expect(indexed.map((point) => point.value)).toEqual([100, 110])
  })
})

describe('mergeIndexedIndicatorSeries', () => {
  it('aligns irregular calendars onto one time axis', () => {
    const series = groupIndicatorsByName([
      makeIndicator({
        indicator_name: 'cpi',
        time: '2026-05-01T00:00:00.000Z',
        current_value: 200,
      }),
      makeIndicator({
        indicator_name: 'gdp',
        time: '2026-06-01T00:00:00.000Z',
        current_value: 30000,
      }),
    ])

    const rows = mergeIndexedIndicatorSeries(series)

    expect(rows).toHaveLength(2)
    expect(rows[0].values.cpi).toBe(100)
    expect(rows[0].values.gdp).toBeUndefined()
    expect(rows[1].values.gdp).toBe(100)
  })
})

describe('formatIndicatorTitle', () => {
  it('replaces underscores for display', () => {
    expect(formatIndicatorTitle('federal_funds_rate')).toBe('federal funds rate')
  })
})

describe('indicatorApiPeriod', () => {
  it('sends the selected window to the backend', () => {
    expect(indicatorApiPeriod('30d')).toBe('30d')
    expect(indicatorApiPeriod('90d')).toBe('90d')
    expect(indicatorApiPeriod('1y')).toBe('1y')
    expect(indicatorApiPeriod('5y')).toBe('5y')
  })
})

describe('filterIndicatorsByName', () => {
  it('keeps every series when the filter is all', () => {
    const cpi = makeIndicator({ indicator_name: 'cpi' })
    const gdp = makeIndicator({ indicator_name: 'gdp' })

    expect(filterIndicatorsByName([cpi, gdp], 'all')).toEqual([cpi, gdp])
  })

  it('keeps only the chosen series', () => {
    const cpi = makeIndicator({ indicator_name: 'cpi' })
    const gdp = makeIndicator({ indicator_name: 'gdp' })

    expect(filterIndicatorsByName([cpi, gdp], 'cpi')).toEqual([cpi])
  })
})

describe('filterIndicatorsToTimeRange', () => {
  it('keeps observations inside the shared lookback window', () => {
    const nowMs = Date.parse('2026-08-25T12:00:00.000Z')
    const kept = makeIndicator({
      indicator_name: 'cpi',
      time: '2026-08-24T12:00:00.000Z',
      current_value: 1,
    })
    const dropped = makeIndicator({
      indicator_name: 'cpi',
      time: '2026-07-01T12:00:00.000Z',
      current_value: 2,
    })

    expect(
      filterIndicatorsToTimeRange([kept, dropped], '30d', nowMs),
    ).toEqual([kept])
  })
})

describe('attachAsOfIndicators', () => {
  const series = groupIndicatorsByName([
    makeIndicator({
      indicator_name: 'cpi',
      time: '2026-06-01T00:00:00.000Z',
      current_value: 200,
      change_percent: 0.1,
    }),
    makeIndicator({
      indicator_name: 'cpi',
      time: '2026-07-01T00:00:00.000Z',
      current_value: 220,
      change_percent: 10,
    }),
    makeIndicator({
      indicator_name: 'gdp',
      time: '2026-07-01T00:00:00.000Z',
      current_value: 30000,
      change_percent: 1.5,
    }),
  ])

  it('carries the last print forward onto later candles', () => {
    const [before, between, after] = attachAsOfIndicators(
      [
        {
          time: 'May',
          timeMs: Date.parse('2026-05-15T00:00:00.000Z'),
          open: 1,
          high: 1,
          low: 1,
          close: 1,
        },
        {
          time: 'Jun',
          timeMs: Date.parse('2026-06-15T00:00:00.000Z'),
          open: 1,
          high: 1,
          low: 1,
          close: 1,
        },
        {
          time: 'Jul',
          timeMs: Date.parse('2026-07-15T00:00:00.000Z'),
          open: 1,
          high: 1,
          low: 1,
          close: 1,
        },
      ],
      series,
    )

    expect(before.asOfIndicators).toEqual({})
    expect(between.asOfIndicators?.cpi).toEqual({
      value: 200,
      indexed: 100,
      changePercent: 0.1,
    })
    expect(between.asOfIndicators?.gdp).toBeUndefined()
    expect(after.asOfIndicators?.cpi).toEqual({
      value: 220,
      indexed: 110,
      changePercent: 10,
    })
    expect(after.asOfIndicators?.gdp).toEqual({
      value: 30000,
      indexed: 100,
      changePercent: 1.5,
    })
  })
})

describe('indexedRowsFromCandles', () => {
  it('keeps candle labels and splits indexed vs raw prints', () => {
    const [row] = indexedRowsFromCandles([
      {
        time: 'Tue, Jul 15',
        timeMs: 1,
        open: 1,
        high: 1,
        low: 1,
        close: 1,
        asOfIndicators: {
          cpi: { value: 220, indexed: 110, changePercent: 10 },
        },
      },
    ])

    expect(row.time).toBe('Tue, Jul 15')
    expect(row.values.cpi).toBe(110)
    expect(row.prints?.cpi).toBe(220)
  })
})

describe('asOfIndexedYDomain', () => {
  it('pads the visible indexed range', () => {
    const [min, max] = asOfIndexedYDomain([
      {
        time: 'a',
        timeMs: 1,
        open: 1,
        high: 1,
        low: 1,
        close: 1,
        asOfIndicators: { cpi: { value: 1, indexed: 100, changePercent: 0 } },
      },
      {
        time: 'b',
        timeMs: 2,
        open: 1,
        high: 1,
        low: 1,
        close: 1,
        asOfIndicators: { cpi: { value: 1, indexed: 120, changePercent: 2 } },
      },
    ])

    expect(min).toBeLessThan(100)
    expect(max).toBeGreaterThan(120)
  })
})

