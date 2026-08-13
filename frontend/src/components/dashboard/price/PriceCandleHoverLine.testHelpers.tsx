import { render } from '@testing-library/react'
import { expect } from 'vitest'
import { PriceCandleHoverLine } from '@/components/dashboard/price/PriceCandleHoverLine'

/** The band box Recharts hands the cursor for a hovered candle. */
export const BAND = { x: 100, y: 8, width: 27, height: 220 }

export function renderHoverLine(band = BAND) {
  return render(
    <svg>
      <PriceCandleHoverLine
        x={band.x}
        y={band.y}
        width={band.width}
        height={band.height}
      />
    </svg>,
  )
}

export function getHoverLine(container: HTMLElement) {
  const line = container.querySelector('[data-slot="candle-hover-line"]')
  expect(line).not.toBeNull()
  return line as SVGLineElement
}

export function attr(line: SVGLineElement, name: string) {
  return Number(line.getAttribute(name))
}
