import { describe, expect, it } from 'vitest'
import { formatPriceAlertRule, getAlertTypeOption } from './priceAlertRule'

describe('formatPriceAlertRule', () => {
  it('asks for a price when the threshold is empty', () => {
    expect(formatPriceAlertRule('BTC/USD', 'reaches', 0)).toBe(
      'Enter a price to see when this alert will fire.',
    )
  })

  it('summarizes each condition in plain language', () => {
    expect(formatPriceAlertRule('BTC/USD', 'reaches', 85000)).toBe(
      "We'll notify you when BTC/USD hits $85,000.00.",
    )
    expect(formatPriceAlertRule('BTC/USD', 'crosses_above', 85000)).toBe(
      "We'll notify you when BTC/USD goes above $85,000.00.",
    )
    expect(formatPriceAlertRule('BTC/USD', 'crosses_below', 70000)).toBe(
      "We'll notify you when BTC/USD goes below $70,000.00.",
    )
  })
})

describe('getAlertTypeOption', () => {
  it('returns the matching condition copy', () => {
    expect(getAlertTypeOption('crosses_above').label).toBe('Goes above')
  })
})
