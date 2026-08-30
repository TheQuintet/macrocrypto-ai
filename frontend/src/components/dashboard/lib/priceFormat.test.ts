import { describe, expect, it } from 'vitest'
import {
  formatPrice,
  formatSignedPercent,
  formatSignedPrice,
  formatUpdatedAt,
  formatVolume,
  percentChange,
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

describe('formatVolume', () => {
  it('labels traded volume in the base asset', () => {
    expect(formatVolume(24_180.42)).toBe('24,180.42 BTC')
  })

  it('keeps 2 decimals for small and large volumes alike', () => {
    expect(formatVolume(0.5)).toBe('0.50 BTC')
    expect(formatVolume(1_234_567.891)).toBe('1,234,567.89 BTC')
  })
})

describe('formatUpdatedAt', () => {
  it('shows the wall-clock time of the update', () => {
    const updatedAt = new Date('2024-06-15T12:34:56.000Z')

    expect(formatUpdatedAt(updatedAt.toISOString())).toBe(
      updatedAt.toLocaleTimeString('en-GB', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      }),
    )
  })

  it('formats as zero-padded hh:mm:ss', () => {
    expect(formatUpdatedAt('2024-06-15T01:02:03.000Z')).toMatch(
      /^\d{2}:\d{2}:\d{2}$/,
    )
  })

  it('placeholders a missing or unparseable timestamp', () => {
    expect(formatUpdatedAt(null)).toBe('--')
    expect(formatUpdatedAt(undefined)).toBe('--')
    expect(formatUpdatedAt('')).toBe('--')
    expect(formatUpdatedAt('not a date')).toBe('--')
  })
})

describe('percentChange', () => {
  it('measures the move from a base value', () => {
    expect(percentChange(64_000, 64_400)).toBeCloseTo(0.625)
    expect(percentChange(64_100.5, 63_900)).toBeCloseTo(-0.3126, 3)
  })

  it('is flat when the base cannot be used', () => {
    expect(percentChange(0, 100)).toBe(0)
    expect(percentChange(Number.NaN, 100)).toBe(0)
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
