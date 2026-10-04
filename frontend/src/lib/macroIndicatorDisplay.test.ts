import { describe, expect, it } from 'vitest'
import {
  formatIndicatorCardTitle,
  formatIndicatorValue,
  normalizeMacroIndicatorsFromApi,
} from '@/lib/macroIndicatorDisplay'
import { makeIndicator } from '@/api/macroIndicators/macroIndicators.testHelpers'

describe('normalizeMacroIndicatorsFromApi', () => {
  it('normalizes names and sorts alphabetically', () => {
    const rows = normalizeMacroIndicatorsFromApi([
      makeIndicator({ indicator_name: 'GDP', current_value: 1 }),
      makeIndicator({ indicator_name: 'cpi', current_value: 2 }),
      makeIndicator({ indicator_name: 'VIX', current_value: 3 }),
    ])

    expect(rows.map((row) => row.indicator_name)).toEqual([
      'cpi',
      'gdp',
      'vix',
    ])
  })
})

describe('formatIndicatorValue', () => {
  it('formats large counts without decimals', () => {
    expect(formatIndicatorValue(534_413, 'active_addresses')).toBe('534,413')
  })

  it('formats rate-like indicators with two decimals', () => {
    expect(formatIndicatorValue(4.67, 'ten_year_treasury')).toBe('4.67')
  })

  it('formats large macro levels with grouping', () => {
    expect(formatIndicatorValue(23_218, 'm2_money_supply')).toBe('23,218')
    expect(formatIndicatorValue(32_475.21, 'gdp')).toBe('32,475.21')
  })
})

describe('formatIndicatorCardTitle', () => {
  it('turns snake_case API names into readable titles', () => {
    expect(formatIndicatorCardTitle('high_yield_spread')).toBe(
      'HIGH YIELD SPREAD',
    )
  })
})
