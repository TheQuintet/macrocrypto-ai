import { cleanup } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  advancePastFlash,
  observePrice,
  renderPriceFlash,
} from '@/hooks/usePriceFlash.testHelpers'

describe('usePriceFlash', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    cleanup()
    vi.useRealTimers()
  })

  it('does not flash on the first observed price', () => {
    const view = renderPriceFlash(64_000)

    expect(view.result.current).toBeNull()
  })

  it('flashes up on a rise over 1% and clears after 500ms', () => {
    const view = renderPriceFlash(64_000)

    observePrice(view, 65_000)
    expect(view.result.current).toBe('up')

    advancePastFlash()
    expect(view.result.current).toBeNull()
  })

  it('flashes down on a drop over 1%', () => {
    const view = renderPriceFlash(64_000)

    observePrice(view, 63_000)

    expect(view.result.current).toBe('down')
  })

  it('stays quiet on an insignificant move', () => {
    const view = renderPriceFlash(64_000)

    observePrice(view, 64_100)

    expect(view.result.current).toBeNull()
  })

  it('compares against the previous price, not a running total', () => {
    const view = renderPriceFlash(64_000)

    // Each step is under 1%, even though 64k -> 65k is over it.
    observePrice(view, 64_500)
    expect(view.result.current).toBeNull()

    observePrice(view, 65_000)
    expect(view.result.current).toBeNull()
  })

  it('ignores missing prices while waiting for the first tick', () => {
    const view = renderPriceFlash(null)
    expect(view.result.current).toBeNull()

    observePrice(view, 64_000)
    expect(view.result.current).toBeNull()

    observePrice(view, 66_000)
    expect(view.result.current).toBe('up')
  })
})
