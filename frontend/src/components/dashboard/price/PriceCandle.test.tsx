import { cleanup } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import {
  expectCandleColor,
  getCandleWick,
  renderPriceCandle,
  SLOT,
} from '@/components/dashboard/price/PriceCandle.testHelpers'
import type { ChartCandle } from '@/types/chart'

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

describe('PriceCandle', () => {
  afterEach(() => {
    cleanup()
  })

  it('draws a body and a wick for a candle', () => {
    const { container } = renderPriceCandle(candle())

    expect(container.querySelector('rect')).toBeInTheDocument()
    expect(container.querySelector('line')).toBeInTheDocument()
  })

  it('colours a rising candle positive', () => {
    const { container } = renderPriceCandle(candle({ open: 120, close: 180 }))

    expectCandleColor(container, 'var(--positive)')
  })

  it('colours a falling candle negative', () => {
    const { container } = renderPriceCandle(candle({ open: 180, close: 120 }))

    expectCandleColor(container, 'var(--negative)')
  })

  it('spans the wick across the whole high-low slot', () => {
    const { container } = renderPriceCandle(candle())
    const wick = getCandleWick(container)

    expect(wick).toHaveAttribute('y1', String(SLOT.y))
    expect(wick).toHaveAttribute('y2', String(SLOT.y + SLOT.height))
  })

  it('renders nothing without a datum', () => {
    const { container } = renderPriceCandle(undefined)

    expect(container.querySelector('rect')).not.toBeInTheDocument()
    expect(container.querySelector('line')).not.toBeInTheDocument()
  })
})
