import type { MacroIndicator } from '@/types/macroIndicators'
import { formatIndicatorTitle } from '@/lib/macroIndicatorHistory'

export const MACRO_INDICATOR_SKELETON_COUNT = 6

export function normalizeIndicatorName(raw: string): string {
  return raw.trim().toLowerCase().replace(/[\s-]+/g, '_')
}

/** Stable sort for cards and filters — one card per API series. */
export function sortMacroIndicators(
  indicators: MacroIndicator[],
): MacroIndicator[] {
  return [...indicators].sort((left, right) =>
    normalizeIndicatorName(left.indicator_name).localeCompare(
      normalizeIndicatorName(right.indicator_name),
    ),
  )
}

export function uniqueIndicatorNames(indicators: MacroIndicator[]): string[] {
  const names = new Set<string>()
  for (const row of indicators) {
    names.add(normalizeIndicatorName(row.indicator_name))
  }
  return [...names].sort((a, b) => a.localeCompare(b))
}

export function normalizeMacroIndicatorsFromApi(
  indicators: MacroIndicator[],
): MacroIndicator[] {
  return sortMacroIndicators(
    indicators.map((indicator) => ({
      ...indicator,
      indicator_name: normalizeIndicatorName(indicator.indicator_name),
    })),
  )
}

type IndicatorValueKind =
  | 'integer'
  | 'percent_like'
  | 'large_number'
  | 'default'

function indicatorValueKind(name: string): IndicatorValueKind {
  const key = normalizeIndicatorName(name)

  if (key === 'active_addresses') {
    return 'integer'
  }

  if (
    key.includes('rate') ||
    key === 'unemployment' ||
    key.includes('treasury') ||
    key === 'vix' ||
    key.includes('spread') ||
    key === 'equity_corr'
  ) {
    return 'percent_like'
  }

  if (
    key === 'gdp' ||
    key === 'm2_money_supply' ||
    key === 'nasdaq_composite' ||
    key === 'gold_spot'
  ) {
    return 'large_number'
  }

  return 'default'
}

/** Human-readable card label from API snake_case names. */
export function formatIndicatorCardTitle(name: string): string {
  return formatIndicatorTitle(normalizeIndicatorName(name)).toUpperCase()
}

/** Format a print for cards and tables based on indicator semantics. */
export function formatIndicatorValue(
  value: number | null | undefined,
  indicatorName: string,
): string {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return '--'
  }

  const kind = indicatorValueKind(indicatorName)

  if (kind === 'integer') {
    return new Intl.NumberFormat('en-US', {
      maximumFractionDigits: 0,
    }).format(value)
  }

  if (kind === 'percent_like') {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value)
  }

  if (kind === 'large_number') {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    }).format(value)
  }

  if (Math.abs(value) >= 100) {
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value)
  }

  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  }).format(value)
}

export function formatIndicatorFilterLabel(name: string): string {
  const normalized = normalizeIndicatorName(name)
  const titled = formatIndicatorTitle(normalized)
  return titled
    .split(' ')
    .map((word) =>
      word.length <= 3 ? word.toUpperCase() : word[0].toUpperCase() + word.slice(1),
    )
    .join(' ')
}
