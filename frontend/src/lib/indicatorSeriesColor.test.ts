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

  it('gives the similar-period indicators their own series colors', () => {
    expect(indicatorSeriesColor('m2_money_supply')).toBe('var(--indicator-m2)')
    expect(indicatorSeriesColor('dxy')).toBe('var(--indicator-dxy)')
    expect(indicatorSeriesColor('ten_year_treasury')).toBe(
      'var(--indicator-ten-year)',
    )
    expect(indicatorSeriesColor('unemployment')).toBe(
      'var(--indicator-unemployment)',
    )
  })

  it('falls back for unknown series', () => {
    expect(indicatorSeriesColor('unknown_print')).toBe(
      'var(--muted-foreground)',
    )
  })
})
