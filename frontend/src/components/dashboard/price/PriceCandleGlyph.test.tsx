import { cleanup, render } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { PriceCandleGlyph } from '@/components/dashboard/price/PriceCandleGlyph'
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

describe('PriceCandleGlyph', () => {
  afterEach(() => {
    cleanup()
  })

  it('draws a wick that extends beyond the body', () => {
    const { container } = render(<PriceCandleGlyph candle={candle()} />)
    const wick = container.querySelector('line')
    const body = container.querySelector('rect')

    expect(wick).not.toBeNull()
    expect(body).not.toBeNull()

    const wickTop = Number(wick?.getAttribute('y1'))
    const wickBottom = Number(wick?.getAttribute('y2'))
    const bodyTop = Number(body?.getAttribute('y'))
    const bodyBottom = bodyTop + Number(body?.getAttribute('height'))

    expect(wickTop).toBeLessThan(bodyTop)
    expect(wickBottom).toBeGreaterThan(bodyBottom)
  })

  it('colours a rising candle positive', () => {
    const { container } = render(
      <PriceCandleGlyph candle={candle({ open: 120, close: 180 })} />,
    )

    expect(container.querySelector('rect')).toHaveAttribute(
      'fill',
      'var(--positive)',
    )
  })
})
