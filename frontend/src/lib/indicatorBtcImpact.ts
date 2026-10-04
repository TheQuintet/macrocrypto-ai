import type { BtcImpact } from '@/types/macroIndicators'

/**
 * Indicator families whose *rise* is bearish for BTC.
 *
 * Mirrors data-service `RegimeService.VISUAL_INDICATORS`:
 * high inflation / rising rates → bear; low inflation / falling rates → bull.
 * Unemployment follows the same risk-off mapping (issue #270).
 */
type IndicatorFamily =
  | 'inflation'
  | 'rates'
  | 'unemployment'
  | 'growth'
  | 'liquidity'
  | 'dollar'
  | 'volatility'
  | 'credit_stress'
  | 'on_chain'
  | 'other'

const RISE_IS_NEGATIVE_FOR_BTC: ReadonlySet<IndicatorFamily> = new Set([
  'inflation',
  'rates',
  'unemployment',
  'dollar',
  'volatility',
  'credit_stress',
])

const FAMILY_REASONS: Record<
  IndicatorFamily,
  { up: string; down: string }
> = {
  inflation: {
    up: 'Rising inflation is typically negative for BTC (risk-off / tighter policy).',
    down: 'Falling inflation is typically positive for BTC (easing policy pressure).',
  },
  rates: {
    up: 'Rising rates are typically negative for BTC (risk-off / tighter liquidity).',
    down: 'Falling rates are typically positive for BTC (risk-on / easier liquidity).',
  },
  unemployment: {
    up: 'Rising unemployment is typically negative for BTC (weaker demand / risk-off).',
    down: 'Falling unemployment is typically positive for BTC (stronger growth / risk-on).',
  },
  growth: {
    up: 'Stronger GDP is typically positive for BTC (growth / risk-on).',
    down: 'Weaker GDP is typically negative for BTC (recession risk / risk-off).',
  },
  liquidity: {
    up: 'Rising M2 is typically positive for BTC (more liquidity).',
    down: 'Falling M2 is typically negative for BTC (tighter liquidity).',
  },
  dollar: {
    up: 'A stronger dollar (DXY) is typically negative for BTC.',
    down: 'A weaker dollar (DXY) is typically positive for BTC.',
  },
  volatility: {
    up: 'Rising volatility (VIX) is typically negative for BTC (risk-off).',
    down: 'Falling volatility is typically positive for BTC (risk-on).',
  },
  credit_stress: {
    up: 'Wider credit spreads are typically negative for BTC (stress / risk-off).',
    down: 'Tighter credit spreads are typically positive for BTC (risk-on).',
  },
  on_chain: {
    up: 'More active addresses are typically positive for BTC (network usage).',
    down: 'Fewer active addresses are typically negative for BTC (weaker usage).',
  },
  other: {
    up: 'This increase is treated as positive for BTC.',
    down: 'This decrease is treated as negative for BTC.',
  },
}

const NEUTRAL_IMPACT: BtcImpact = {
  polarity: 'neutral',
  toneClass: 'text-muted-foreground',
  label: 'Neutral',
  reason: 'Unchanged — no clear BTC impact from this print.',
}

function normalizeIndicatorName(indicatorName: string) {
  return indicatorName.toLowerCase().replace(/[\s-]+/g, '_')
}

export function indicatorFamily(indicatorName: string): IndicatorFamily {
  const name = normalizeIndicatorName(indicatorName)

  if (name === 'cpi' || name.includes('inflation')) return 'inflation'
  if (
    name === 'federal_funds_rate' ||
    name === 'fedfunds' ||
    name.includes('fed_funds') ||
    name.includes('interest') ||
    name === 'ten_year_treasury' ||
    name.includes('treasury') ||
    name === 'dgs10'
  ) {
    return 'rates'
  }
  if (name.includes('unemployment') || name.includes('unrate')) {
    return 'unemployment'
  }
  if (name === 'gdp' || name.includes('gdp')) return 'growth'
  if (name.includes('m2') || name.includes('money_supply')) return 'liquidity'
  if (name === 'dxy' || name.includes('dollar')) return 'dollar'
  if (name === 'vix' || name.includes('volatility')) return 'volatility'
  if (name.includes('high_yield') || name.includes('spread')) {
    return 'credit_stress'
  }
  if (name === 'nasdaq_composite' || name.includes('nasdaq')) return 'growth'
  if (name === 'gold_spot' || name.includes('gold')) return 'dollar'
  if (name === 'active_addresses' || name.includes('active_address')) {
    return 'on_chain'
  }
  return 'other'
}

/**
 * Classify a print as positive/negative for BTC from the latest % change.
 *
 * Latest snapshots only include period-over-period change (not CPI YoY or
 * 3-month rate trend), so direction is the frontend equivalent of the
 * regime engine's rising/falling and high/low conditions.
 */
export function getIndicatorBtcImpact(
  indicatorName: string,
  changePercent: number | null,
): BtcImpact {
  if (changePercent === null || changePercent === 0) {
    return NEUTRAL_IMPACT
  }

  const family = indicatorFamily(indicatorName)
  const isUp = changePercent > 0
  const isPositive = RISE_IS_NEGATIVE_FOR_BTC.has(family) ? !isUp : isUp

  return {
    polarity: isPositive ? 'positive' : 'negative',
    toneClass: isPositive ? 'text-positive' : 'text-negative',
    label: isPositive ? 'Positive for BTC' : 'Negative for BTC',
    reason: isUp ? FAMILY_REASONS[family].up : FAMILY_REASONS[family].down,
  }
}

export function getChangeSymbol(changePercent: number | null): string {
  if (changePercent === null || changePercent === 0) return '→'
  return changePercent > 0 ? '↑' : '↓'
}

export function formatChangePercent(changePercent: number | null): string {
  if (changePercent === null) return '--'
  return `${changePercent > 0 ? '+' : ''}${changePercent.toFixed(2)}%`
}

/**
 * Arrow follows the print (up/down). Color follows BTC impact — same
 * pairing the cards and history table use.
 */
export function getIndicatorChangeDisplay(
  indicatorName: string,
  changePercent: number | null,
) {
  const impact = getIndicatorBtcImpact(indicatorName, changePercent)
  const symbol = getChangeSymbol(changePercent)
  const formatted = formatChangePercent(changePercent)

  return {
    ...impact,
    symbol,
    formatted,
    text: `${symbol} ${formatted}`,
  }
}
