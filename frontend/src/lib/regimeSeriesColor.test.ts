import { describe, expect, it } from 'vitest'
import { regimeSeriesColor } from '@/lib/regimeSeriesColor'

const ALL_REGIMES = [
  'growth',
  'low_inflation',
  'falling_rates',
  'rising_rates',
  'high_inflation',
  'recession',
]

describe('regimeSeriesColor', () => {
  it('gives every regime class its own color', () => {
    const colors = ALL_REGIMES.map(regimeSeriesColor)

    expect(new Set(colors).size).toBe(ALL_REGIMES.length)
  })

  it('reads the tokens defined in index.css', () => {
    expect(regimeSeriesColor('growth')).toBe('var(--regime-growth)')
    expect(regimeSeriesColor('high_inflation')).toBe(
      'var(--regime-high-inflation)',
    )
  })

  it('matches names case-insensitively', () => {
    expect(regimeSeriesColor('GROWTH')).toBe(regimeSeriesColor('growth'))
  })

  it('falls back for a regime class this build does not know', () => {
    expect(regimeSeriesColor('stagflation_shock')).toBe(
      'var(--muted-foreground)',
    )
  })
})
