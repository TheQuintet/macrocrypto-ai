import { describe, expect, it } from 'vitest'
import {
  flashDirectionFor,
  percentChange,
  priceFlashClass,
  PRICE_FLASH_DURATION_MS,
  PRICE_FLASH_THRESHOLD_PERCENT,
} from '@/components/dashboard/lib/priceFlash'

describe('price flash constants', () => {
  it('flashes for 500ms on moves over 1%', () => {
    expect(PRICE_FLASH_THRESHOLD_PERCENT).toBe(1)
    expect(PRICE_FLASH_DURATION_MS).toBe(500)
  })
})

describe('percentChange', () => {
  it('measures the move against the previous price', () => {
    expect(percentChange(100, 102)).toBeCloseTo(2)
    expect(percentChange(100, 98)).toBeCloseTo(-2)
  })

  it('avoids dividing by zero', () => {
    expect(percentChange(0, 500)).toBe(0)
  })
})

describe('flashDirectionFor', () => {
  it('flashes green on a rise over the threshold', () => {
    expect(flashDirectionFor(64000, 64800)).toBe('up')
  })

  it('flashes red on a drop over the threshold', () => {
    expect(flashDirectionFor(64000, 63200)).toBe('down')
  })

  it('stays quiet on insignificant moves', () => {
    expect(flashDirectionFor(64000, 64100)).toBeNull()
    expect(flashDirectionFor(64000, 63900)).toBeNull()
    expect(flashDirectionFor(64000, 64000)).toBeNull()
  })

  it('stays quiet on an exactly-threshold move', () => {
    expect(flashDirectionFor(64000, 64640)).toBeNull()
    expect(flashDirectionFor(64000, 63360)).toBeNull()
  })
})

describe('priceFlashClass', () => {
  it('maps direction to an animation utility', () => {
    expect(priceFlashClass('up')).toBe('animate-price-flash-up')
    expect(priceFlashClass('down')).toBe('animate-price-flash-down')
    expect(priceFlashClass(null)).toBeUndefined()
  })
})
