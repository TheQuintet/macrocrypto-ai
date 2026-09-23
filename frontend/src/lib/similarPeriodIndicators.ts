import { formatIndicatorTitle } from '@/lib/macroIndicatorHistory'
import type { SimilarPeriod, SimilarPeriodIndicatorName } from '@/types/regime'

/** Same set the data service uses to measure distance from today. */
export const SIMILAR_PERIOD_INDICATORS: readonly SimilarPeriodIndicatorName[] = [
  'cpi',
  'federal_funds_rate',
  'm2_money_supply',
  'dxy',
  'ten_year_treasury',
  'gdp',
  'unemployment',
]

const SHORT_LABELS: Record<SimilarPeriodIndicatorName, string> = {
  cpi: 'CPI',
  federal_funds_rate: 'Fed funds',
  m2_money_supply: 'M2',
  dxy: 'DXY',
  ten_year_treasury: '10y',
  gdp: 'GDP',
  unemployment: 'Unemp',
}

export function similarPeriodIndicatorLabel(name: string) {
  return (
    SHORT_LABELS[name as SimilarPeriodIndicatorName] ??
    formatIndicatorTitle(name)
  )
}

export function formatConditionValue(value: number | undefined) {
  if (value == null || !Number.isFinite(value)) {
    return '—'
  }

  return value.toFixed(2)
}

/** The engine's set first, then any extra keys the payload still sent. */
export function similarPeriodIndicatorKeys(
  current: Record<string, number>,
  periods: SimilarPeriod[] = [],
) {
  const extras = new Set<string>()

  for (const key of Object.keys(current)) {
    extras.add(key)
  }

  for (const period of periods) {
    for (const key of Object.keys(period.macroConditions)) {
      extras.add(key)
    }
  }

  const known = new Set<string>(SIMILAR_PERIOD_INDICATORS)
  const extraKeys = [...extras]
    .filter((key) => !known.has(key))
    .sort((left, right) => left.localeCompare(right))

  return [...SIMILAR_PERIOD_INDICATORS, ...extraKeys]
}
