import { describe, expect, it } from 'vitest'
import {
  formatPrice,
  formatSignedPercent,
  formatSignedPrice,
  priceDirection,
} from '@/components/dashboard/lib/priceFormat'

describe('formatPrice', () => {
  it('uses a currency label, thousands separators and 2 decimals', () => {
    expect(formatPrice(64213.5)).toBe('$64,213.50')
    expect(formatPrice(1000000)).toBe('$1,000,000.00')
  })

  it('rounds to cents', () => {
    expect(formatPrice(64213.456)).toBe('$64,213.46')
  })
})

describe('formatSignedPrice', () => {
  it('signs the absolute change', () => {
    expect(formatSignedPrice(1204.3)).toBe('+$1,204.30')
    expect(formatSignedPrice(-820.1)).toBe('-$820.10')
  })

  it('leaves a flat change unsigned', () => {
    expect(formatSignedPrice(0)).toBe('$0.00')
  })
})

describe('formatSignedPercent', () => {
  it('signs the percentage to 2 decimals', () => {
    expect(formatSignedPercent(1.876)).toBe('+1.88%')
    expect(formatSignedPercent(-0.42)).toBe('-0.42%')
    expect(formatSignedPercent(0)).toBe('0.00%')
  })
})

describe('priceDirection', () => {
  it('maps sign to direction', () => {
    expect(priceDirection(12)).toBe('up')
    expect(priceDirection(-12)).toBe('down')
    expect(priceDirection(0)).toBe('flat')
  })

  it('treats missing or non-finite values as flat', () => {
    expect(priceDirection(null)).toBe('flat')
    expect(priceDirection(undefined)).toBe('flat')
    expect(priceDirection(Number.NaN)).toBe('flat')
  })
})
