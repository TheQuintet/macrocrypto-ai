import { describe, expect, it } from 'vitest'
import {
  formatAlertPriceInput,
  formatPriceAlertHeadline,
  getAlertTypeOption,
  parseAlertPriceInput,
  proposedAlertThreshold,
  resolveAlertThresholdPrice,
} from './priceAlertRule'

describe('formatPriceAlertHeadline', () => {
  it('formats a short rule for the alerts list', () => {
    expect(formatPriceAlertHeadline('BTC/USD', 'reaches', 85000)).toBe(
      'BTC/USD hits $85,000.00',
    )
    expect(formatPriceAlertHeadline('BTC/USD', 'crosses_above', 85000)).toBe(
      'BTC/USD goes above $85,000.00',
    )
    expect(formatPriceAlertHeadline('BTC/USD', 'crosses_below', 70000)).toBe(
      'BTC/USD goes below $70,000.00',
    )
  })
})

describe('formatAlertPriceInput', () => {
  it('uses thousands and decimal separators', () => {
    expect(formatAlertPriceInput(13123)).toBe('13,123.00')
    expect(formatAlertPriceInput(85000)).toBe('85,000.00')
    expect(formatAlertPriceInput(85000.5)).toBe('85,000.50')
  })
})

describe('parseAlertPriceInput', () => {
  it('reads a delimited price back to a number', () => {
    expect(parseAlertPriceInput('13,123.00')).toBe(13123)
    expect(parseAlertPriceInput('85000')).toBe(85000)
    expect(parseAlertPriceInput('')).toBe(0)
  })
})

describe('proposedAlertThreshold', () => {
  it('returns the last received price when it is usable', () => {
    expect(proposedAlertThreshold(64_213.5)).toBe(64_213.5)
  })

  it('returns 0 when no price has arrived yet', () => {
    expect(proposedAlertThreshold(null)).toBe(0)
    expect(proposedAlertThreshold(undefined)).toBe(0)
    expect(proposedAlertThreshold(0)).toBe(0)
    expect(proposedAlertThreshold(-1)).toBe(0)
  })
})

describe('resolveAlertThresholdPrice', () => {
  it('proposes the last received price until the user types', () => {
    expect(
      resolveAlertThresholdPrice({
        isEditing: false,
        priceTouched: false,
        typedPrice: 0,
        lastReceivedPrice: 64_213.5,
      }),
    ).toBe(64_213.5)
  })

  it('keeps a typed or edited threshold', () => {
    expect(
      resolveAlertThresholdPrice({
        isEditing: false,
        priceTouched: true,
        typedPrice: 70_000,
        lastReceivedPrice: 64_213.5,
      }),
    ).toBe(70_000)
    expect(
      resolveAlertThresholdPrice({
        isEditing: true,
        priceTouched: false,
        typedPrice: 85_000,
        lastReceivedPrice: 64_213.5,
      }),
    ).toBe(85_000)
  })
})

describe('getAlertTypeOption', () => {
  it('returns the matching condition copy', () => {
    expect(getAlertTypeOption('crosses_above').label).toBe('Goes above')
  })
})

