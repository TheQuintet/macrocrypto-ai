import { describe, expect, it } from 'vitest'
import {
  candleDirection,
  candleLayout,
  MAX_CANDLE_BODY_WIDTH,
  MIN_CANDLE_BODY_HEIGHT,
} from '@/components/dashboard/lib/candleGeometry'
import type { ChartCandle } from '@/types/chart'

/** Slot spanning [low, high] = [100, 200] over 100px starting at y=0. */
const SLOT = { x: 10, y: 0, width: 20, height: 100 }

function candle(overrides: Partial<ChartCandle> = {}): ChartCandle {
  return {
    time: 'Mar 5 14:00',
    timeMs: 0,
    open: 120,
    high: 200,
    low: 100,
    close: 180,
    ...overrides,
  }
}

function layoutFor(overrides: Partial<ChartCandle> = {}) {
  return candleLayout(
    candle(overrides),
    SLOT.x,
    SLOT.y,
    SLOT.width,
    SLOT.height,
  )
}

describe('candleDirection', () => {
  it('reads a close above the open as up', () => {
    expect(candleDirection(candle({ open: 100, close: 110 }))).toBe('up')
  })

  it('reads a close below the open as down', () => {
    expect(candleDirection(candle({ open: 110, close: 100 }))).toBe('down')
  })

  it('treats an unchanged close as up', () => {
    expect(candleDirection(candle({ open: 100, close: 100 }))).toBe('up')
  })
})

describe('candleLayout', () => {
  it('draws the wick across the full high-low slot', () => {
    const layout = layoutFor()

    expect(layout.wickTopY).toBe(SLOT.y)
    expect(layout.wickBottomY).toBe(SLOT.y + SLOT.height)
  })

  it('centres the wick and body in the slot', () => {
    const layout = layoutFor()

    expect(layout.centerX).toBe(20)
    expect(layout.bodyX + layout.bodyWidth / 2).toBe(layout.centerX)
  })

  it('places the body between open and close, inverted for pixels', () => {
    // high=200 at y=0, low=100 at y=100 -> close 180 sits at y=20, open 120 at y=80.
    const layout = layoutFor()

    expect(layout.bodyY).toBe(20)
    expect(layout.bodyHeight).toBe(60)
  })

  it('places the body identically whichever way the candle closed', () => {
    const up = layoutFor({ open: 120, close: 180 })
    const down = layoutFor({ open: 180, close: 120 })

    expect(down.bodyY).toBe(up.bodyY)
    expect(down.bodyHeight).toBe(up.bodyHeight)
    expect(down.direction).toBe('down')
  })

  it('keeps a doji visible with a minimum body height', () => {
    const layout = layoutFor({ open: 150, close: 150 })

    expect(layout.bodyHeight).toBe(MIN_CANDLE_BODY_HEIGHT)
  })

  it('survives a flat bucket without dividing by zero', () => {
    const layout = layoutFor({ open: 150, high: 150, low: 150, close: 150 })

    expect(Number.isFinite(layout.bodyY)).toBe(true)
    expect(layout.bodyY).toBe(SLOT.y)
    expect(layout.bodyHeight).toBe(MIN_CANDLE_BODY_HEIGHT)
  })

  it('caps body width so sparse series stay readable', () => {
    const layout = candleLayout(candle(), 0, 0, 400, 100)

    expect(layout.bodyWidth).toBe(MAX_CANDLE_BODY_WIDTH)
  })

  it('keeps a visible body in a very narrow slot', () => {
    const layout = candleLayout(candle(), 0, 0, 1, 100)

    expect(layout.bodyWidth).toBeGreaterThanOrEqual(1)
  })

  it('never draws the body outside the wick', () => {
    const layout = layoutFor({ open: 105, close: 195 })

    expect(layout.bodyY).toBeGreaterThanOrEqual(layout.wickTopY)
    expect(layout.bodyY + layout.bodyHeight).toBeLessThanOrEqual(
      layout.wickBottomY,
    )
  })
})
