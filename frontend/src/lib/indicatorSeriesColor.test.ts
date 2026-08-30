import { describe, expect, it } from 'vitest'
import { indicatorSeriesColor } from '@/lib/indicatorSeriesColor'

describe('indicatorSeriesColor', () => {
  it('gives CPI, Fed funds, and GDP distinct series colors', () => {
    const cpi = indicatorSeriesColor('cpi')
    const fed = indicatorSeriesColor('federal_funds_rate')
    const gdp = indicatorSeriesColor('gdp')

    expect(cpi).toBe('var(--indicator-cpi)')
    expect(fed).toBe('var(--indicator-federal-funds-rate)')
    expect(gdp).toBe('var(--indicator-gdp)')
    expect(new Set([cpi, fed, gdp]).size).toBe(3)
  })

  it('matches names case-insensitively', () => {
    expect(indicatorSeriesColor('CPI')).toBe(indicatorSeriesColor('cpi'))
  })

  it('falls back for unknown series', () => {
    expect(indicatorSeriesColor('m2_money_supply')).toBe(
      'var(--muted-foreground)',
    )
  })
})
