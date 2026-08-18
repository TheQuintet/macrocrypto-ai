import { render, screen } from '@testing-library/react'
import { expect } from 'vitest'
import type { PriceFlashDirection } from '@/components/dashboard/lib/priceFlash'
import { PriceValue } from '@/components/dashboard/price/PriceValue'

export function renderPriceValue(
  price: number | null,
  flashDirection: PriceFlashDirection = null,
) {
  return render(<PriceValue price={price} flashDirection={flashDirection} />)
}

export function getPriceValue() {
  const element = document.querySelector('[data-flash]')
  if (!element) {
    throw new Error('PriceValue not rendered')
  }

  return element
}

export function expectPriceText(text: string) {
  expect(screen.getByText(text)).toBeInTheDocument()
}

export function expectLargeBoldPrice() {
  expect(getPriceValue()).toHaveClass('font-bold', 'text-2xl', 'font-mono')
}

export function expectFlash(direction: 'up' | 'down' | 'none') {
  const element = getPriceValue()
  expect(element).toHaveAttribute('data-flash', direction)

  if (direction === 'none') {
    expect(element.className).not.toMatch(/animate-price-flash/)
    return
  }

  expect(element).toHaveClass(`animate-price-flash-${direction}`)
}
