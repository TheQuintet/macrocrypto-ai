import { render } from '@testing-library/react'
import { expect } from 'vitest'
import { PriceCandle } from '@/components/dashboard/price/PriceCandle'
import type { ChartCandle } from '@/types/chart'

export const SLOT = { x: 10, y: 0, width: 20, height: 100 }

export function renderPriceCandle(candle?: ChartCandle) {
  return render(
    <svg>
      <PriceCandle
        x={SLOT.x}
        y={SLOT.y}
        width={SLOT.width}
        height={SLOT.height}
        payload={candle}
      />
    </svg>,
  )
}

export function getCandleBody(container: HTMLElement) {
  const body = container.querySelector('rect')
  expect(body).not.toBeNull()
  return body as SVGRectElement
}

export function getCandleWick(container: HTMLElement) {
  const wick = container.querySelector('line')
  expect(wick).not.toBeNull()
  return wick as SVGLineElement
}

export function expectCandleColor(container: HTMLElement, color: string) {
  expect(getCandleBody(container)).toHaveAttribute('fill', color)
  expect(getCandleWick(container)).toHaveAttribute('stroke', color)
}
