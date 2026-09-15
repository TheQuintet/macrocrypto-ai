import { describe, expect, it } from 'vitest'
import {
  formatPercent,
  formatRatio,
  formatRegimePrice,
  formatRegimeRange,
  returnToneClass,
  sortRegimesByStart,
} from '@/lib/regimePerformance'
import type { RegimePerformanceRow } from '@/types/regime'

function row(
  regimeId: number,
  startDate: string,
  endDate: string | null,
): RegimePerformanceRow {
  return {
    regimeId,
    regimeType: 'growth',
    startDate,
    endDate,
    status: endDate ? 'completed' : 'active',
    performance: {
      avgReturn: null,
      maxDrawdown: null,
      volatility: null,
      sharpeRatio: null,
      btcPriceStart: null,
      btcPriceEnd: null,
    },
  }
}

describe('sortRegimesByStart', () => {
  it('puts the oldest regime first, wherever the endpoint placed it', () => {
    // The endpoint sends completed regimes newest-first, then appends the
    // active one — so the open regime arrives last despite being the newest.
    const rows = [
      row(3, '2023-08-01', '2024-02-29'),
      row(2, '2022-02-01', '2022-10-31'),
      row(4, '2024-03-01', null),
    ]

    expect(sortRegimesByStart(rows).map((r) => r.regimeId)).toEqual([2, 3, 4])
  })

  it('does not mutate the array it was given', () => {
    const rows = [row(2, '2024-01-01', null), row(1, '2020-01-01', null)]
    sortRegimesByStart(rows)

    expect(rows.map((r) => r.regimeId)).toEqual([2, 1])
  })
})

describe('formatPercent', () => {
  it('signs a gain and leaves a loss with its own minus', () => {
    expect(formatPercent(28.4)).toBe('+28.4%')
    expect(formatPercent(-12.7)).toBe('-12.7%')
  })

  it('does not sign zero', () => {
    expect(formatPercent(0)).toBe('0.0%')
  })

  it('shows a dash rather than inventing a figure', () => {
    expect(formatPercent(null)).toBe('—')
    expect(formatPercent(Number.NaN)).toBe('—')
  })
})

describe('formatRatio and formatRegimePrice', () => {
  it('formats a Sharpe ratio to two places', () => {
    expect(formatRatio(1.4237)).toBe('1.42')
    expect(formatRatio(-0.21)).toBe('-0.21')
  })

  it('formats BTC prices as whole dollars with separators', () => {
    expect(formatRegimePrice(61_400)).toBe('$61,400')
  })

  it('shows a dash for a missing metric', () => {
    expect(formatRatio(null)).toBe('—')
    expect(formatRegimePrice(null)).toBe('—')
  })
})

describe('formatRegimeRange', () => {
  it('reads as a month span', () => {
    expect(formatRegimeRange('2023-08-01', '2024-02-29')).toBe(
      'Aug 2023 – Feb 2024',
    )
  })

  it('says "now" while the regime is still open', () => {
    expect(formatRegimeRange('2024-03-01', null)).toBe('Mar 2024 – now')
  })

  it('reads the date in UTC, not the reader’s zone', () => {
    // 1 Mar UTC is still 29 Feb in the Americas; the label must not slip.
    expect(formatRegimeRange('2024-03-01', null)).toContain('Mar 2024')
  })

  it('falls back to the raw value for an unreadable date', () => {
    expect(formatRegimeRange('not-a-date', null)).toBe('not-a-date – now')
  })
})

describe('returnToneClass', () => {
  it('colours gains green and losses red', () => {
    expect(returnToneClass(12)).toBe('text-positive')
    expect(returnToneClass(-12)).toBe('text-negative')
  })

  it('stays neutral for zero and for a missing figure', () => {
    expect(returnToneClass(0)).toBe('text-muted-foreground')
    expect(returnToneClass(null)).toBe('text-muted-foreground')
  })
})
