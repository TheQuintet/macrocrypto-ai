import { cleanup } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import {
  attr,
  BAND,
  getHoverLine,
  renderHoverLine,
} from '@/components/dashboard/price/PriceCandleHoverLine.testHelpers'

describe('PriceCandleHoverLine', () => {
  afterEach(() => {
    cleanup()
  })

  it('draws a vertical line', () => {
    const line = getHoverLine(renderHoverLine().container)

    expect(attr(line, 'x1')).toBe(attr(line, 'x2'))
  })

  it('centres the line on the hovered candle', () => {
    const line = getHoverLine(renderHoverLine().container)

    expect(attr(line, 'x1')).toBe(BAND.x + BAND.width / 2)
  })

  it('spans the full height of the band', () => {
    const line = getHoverLine(renderHoverLine().container)

    expect(attr(line, 'y1')).toBe(BAND.y)
    expect(attr(line, 'y2')).toBe(BAND.y + BAND.height)
  })

  it('stays a hairline so it never competes with the candles', () => {
    const line = getHoverLine(renderHoverLine().container)

    expect(attr(line, 'stroke-width')).toBe(1)
    expect(line).toHaveAttribute('stroke-dasharray', '3 3')
  })

  it('degrades to the origin when Recharts passes no box', () => {
    const { container } = renderHoverLine({ x: 0, y: 0, width: 0, height: 0 })
    const line = getHoverLine(container)

    expect(attr(line, 'x1')).toBe(0)
    expect(attr(line, 'y2')).toBe(0)
  })
})
