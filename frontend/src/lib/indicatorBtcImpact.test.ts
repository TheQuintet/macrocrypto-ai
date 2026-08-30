import { describe, expect, it } from 'vitest'
import {
  formatChangePercent,
  getChangeSymbol,
  getIndicatorBtcImpact,
  getIndicatorChangeDisplay,
  indicatorFamily,
} from '@/lib/indicatorBtcImpact'

describe('indicatorFamily', () => {
  it('maps FRED names onto the regime-engine families', () => {
    expect(indicatorFamily('cpi')).toBe('inflation')
    expect(indicatorFamily('CPI')).toBe('inflation')
    expect(indicatorFamily('federal_funds_rate')).toBe('rates')
    expect(indicatorFamily('FEDFUNDS')).toBe('rates')
    expect(indicatorFamily('ten_year_treasury')).toBe('rates')
    expect(indicatorFamily('unemployment')).toBe('unemployment')
    expect(indicatorFamily('gdp')).toBe('growth')
    expect(indicatorFamily('m2_money_supply')).toBe('liquidity')
    expect(indicatorFamily('dxy')).toBe('dollar')
  })
})

describe('getIndicatorBtcImpact', () => {
  it('treats rising inflation, rates, and unemployment as negative for BTC', () => {
    for (const name of ['cpi', 'federal_funds_rate', 'unemployment']) {
      const impact = getIndicatorBtcImpact(name, 0.5)
      expect(impact.polarity).toBe('negative')
      expect(impact.toneClass).toBe('text-negative')
      expect(impact.label).toBe('Negative for BTC')
      expect(impact.reason.length).toBeGreaterThan(0)
    }
  })

  it('treats falling inflation, rates, and unemployment as positive for BTC', () => {
    for (const name of ['cpi', 'federal_funds_rate', 'unemployment']) {
      const impact = getIndicatorBtcImpact(name, -0.5)
      expect(impact.polarity).toBe('positive')
      expect(impact.toneClass).toBe('text-positive')
      expect(impact.label).toBe('Positive for BTC')
    }
  })

  it('treats stronger GDP as positive and weaker GDP as negative for BTC', () => {
    expect(getIndicatorBtcImpact('gdp', 1.91).polarity).toBe('positive')
    expect(getIndicatorBtcImpact('gdp', -0.4).polarity).toBe('negative')
  })

  it('treats a stronger dollar as negative and rising M2 as positive', () => {
    expect(getIndicatorBtcImpact('dxy', 0.3).polarity).toBe('negative')
    expect(getIndicatorBtcImpact('m2_money_supply', 0.4).polarity).toBe(
      'positive',
    )
  })

  it('returns a neutral reading when the print is unchanged or missing', () => {
    expect(getIndicatorBtcImpact('cpi', 0).polarity).toBe('neutral')
    expect(getIndicatorBtcImpact('gdp', null).polarity).toBe('neutral')
    expect(getIndicatorBtcImpact('cpi', 0).toneClass).toBe(
      'text-muted-foreground',
    )
  })
})

describe('change formatters', () => {
  it('formats the signed percent and arrow', () => {
    expect(formatChangePercent(0.23)).toBe('+0.23%')
    expect(formatChangePercent(-2.38)).toBe('-2.38%')
    expect(formatChangePercent(0)).toBe('0.00%')
    expect(formatChangePercent(null)).toBe('--')
    expect(getChangeSymbol(0.23)).toBe('↑')
    expect(getChangeSymbol(-2.38)).toBe('↓')
    expect(getChangeSymbol(0)).toBe('→')
    expect(getChangeSymbol(null)).toBe('→')
  })
})

describe('getIndicatorChangeDisplay', () => {
  it('keeps the numeric arrow and colors by BTC impact', () => {
    const risingCpi = getIndicatorChangeDisplay('cpi', 0.21)
    expect(risingCpi.symbol).toBe('↑')
    expect(risingCpi.text).toBe('↑ +0.21%')
    expect(risingCpi.toneClass).toBe('text-negative')

    const fallingGdp = getIndicatorChangeDisplay('gdp', -0.5)
    expect(fallingGdp.symbol).toBe('↓')
    expect(fallingGdp.text).toBe('↓ -0.50%')
    expect(fallingGdp.toneClass).toBe('text-negative')

    const risingGdp = getIndicatorChangeDisplay('gdp', 1.91)
    expect(risingGdp.symbol).toBe('↑')
    expect(risingGdp.toneClass).toBe('text-positive')
  })
})
