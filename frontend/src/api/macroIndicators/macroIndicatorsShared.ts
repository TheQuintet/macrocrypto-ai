import type {
  MacroIndicator,
  MacroIndicatorDataSource,
} from '@/types/macroIndicators'

/** Names as returned by GET /api/v1/indicators (data-service / FRED collector). */
export const MAIN_INDICATOR_NAMES = [
  'cpi',
  'federal_funds_rate',
  'gdp',
] as const

const MAIN_INDICATORS = new Set<string>(MAIN_INDICATOR_NAMES)

export const MACRO_INDICATORS_MOCK_LATENCY_MS = 280

export function keepMainIndicators(indicators: MacroIndicator[]) {
  return indicators.filter((indicator) =>
    MAIN_INDICATORS.has(indicator.indicator_name.toLowerCase()),
  )
}

export function withDataSource(
  indicators: MacroIndicator[],
  dataSource: MacroIndicatorDataSource,
): MacroIndicator[] {
  return indicators.map((indicator) => ({ ...indicator, dataSource }))
}

export function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export const mockLatestIndicators: MacroIndicator[] = [
  {
    indicator_name: 'cpi',
    time: '2026-07-15T00:00:00.000Z',
    current_value: 322.13,
    previous_value: 321.47,
    change_percent: 0.21,
    trend: '↑',
    source: 'fred',
    dataSource: 'simulated',
  },
  {
    indicator_name: 'federal_funds_rate',
    time: '2026-08-01T00:00:00.000Z',
    current_value: 4.33,
    previous_value: 4.33,
    change_percent: 0,
    trend: '→',
    source: 'fred',
    dataSource: 'simulated',
  },
  {
    indicator_name: 'gdp',
    time: '2026-06-30T00:00:00.000Z',
    current_value: 30353.9,
    previous_value: 30111.2,
    change_percent: 0.81,
    trend: '↑',
    source: 'fred',
    dataSource: 'simulated',
  },
]
