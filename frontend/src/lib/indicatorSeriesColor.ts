import { normalizeIndicatorName } from '@/lib/macroIndicatorDisplay'

/** Canonical series colors live in `src/index.css` as `--indicator-*` tokens. */
const INDICATOR_SERIES_COLOR: Record<string, string> = {
  cpi: 'var(--indicator-cpi)',
  federal_funds_rate: 'var(--indicator-federal-funds-rate)',
  gdp: 'var(--indicator-gdp)',
  m2_money_supply: 'var(--indicator-m2)',
  dxy: 'var(--indicator-dxy)',
  ten_year_treasury: 'var(--indicator-ten-year)',
  unemployment: 'var(--indicator-unemployment)',
  vix: 'var(--indicator-vix)',
  gold_spot: 'var(--indicator-gold-spot)',
  active_addresses: 'var(--indicator-active-addresses)',
  nasdaq_composite: 'var(--indicator-nasdaq)',
  high_yield_spread: 'var(--indicator-high-yield-spread)',
  equity_corr: 'var(--indicator-equity-corr)',
}

const FALLBACK_CHART_COLORS = [
  'var(--chart-2)',
  'var(--chart-3)',
  'var(--chart-4)',
  'var(--chart-5)',
] as const

function hashIndicatorName(name: string): number {
  let hash = 0
  for (let index = 0; index < name.length; index += 1) {
    hash = (hash * 31 + name.charCodeAt(index)) | 0
  }
  return Math.abs(hash)
}

export function indicatorSeriesColor(name: string): string {
  const key = normalizeIndicatorName(name)
  const known = INDICATOR_SERIES_COLOR[key]
  if (known) {
    return known
  }

  const fallbackIndex = hashIndicatorName(key) % FALLBACK_CHART_COLORS.length
  return FALLBACK_CHART_COLORS[fallbackIndex]
}
