import type { MacroIndicator } from '@/types/macroIndicators'

export const FIXED_INDICATOR_TIME = '2024-06-15T12:00:00.000Z'

export function makeIndicator(
  overrides: Partial<MacroIndicator> & Pick<MacroIndicator, 'indicator_name'>,
): MacroIndicator {
  return {
    time: FIXED_INDICATOR_TIME,
    current_value: 1,
    previous_value: 1,
    change_percent: 0,
    trend: '→',
    source: 'fred',
    dataSource: 'live',
    ...overrides,
  }
}

/** Shape of GET /api/v1/indicators, including names the UI should drop. */
export const mockIndicatorsApiResponse = {
  period: 'latest',
  count: 5,
  indicators: [
    makeIndicator({
      indicator_name: 'cpi',
      current_value: 307.2,
      previous_value: 306.5,
      change_percent: 0.23,
      trend: '↑',
    }),
    makeIndicator({
      indicator_name: 'federal_funds_rate',
      current_value: 5.5,
      previous_value: 5.5,
      change_percent: 0,
      trend: '→',
    }),
    makeIndicator({
      indicator_name: 'gdp',
      current_value: 32475.21,
      previous_value: 31865.721,
      change_percent: 1.91,
      trend: '↑',
    }),
    makeIndicator({
      indicator_name: 'unemployment',
      current_value: 4.1,
      previous_value: 4.2,
      change_percent: -2.38,
      trend: '↓',
    }),
    makeIndicator({
      indicator_name: 'm2_money_supply',
      current_value: 21000,
      previous_value: 20900,
      change_percent: 0.48,
      trend: '↑',
    }),
  ],
}
