import { cleanup } from '@testing-library/react'
import { afterEach, describe, it } from 'vitest'
import {
  expectFlash,
  expectLargeBoldPrice,
  expectPriceText,
  renderPriceValue,
} from '@/components/dashboard/price/PriceValue.testHelpers'

describe('PriceValue', () => {
  afterEach(() => {
    cleanup()
  })

  it('renders the price with a currency label and 2 decimals', () => {
    renderPriceValue(64_213.5)

    expectPriceText('$64,213.50')
  })

  it('renders the price in large bold type', () => {
    renderPriceValue(64_213.5)

    expectLargeBoldPrice()
  })

  it('falls back to a placeholder when there is no price', () => {
    renderPriceValue(null)

    expectPriceText('--')
  })

  it('applies no animation by default', () => {
    renderPriceValue(64_213.5)

    expectFlash('none')
  })

  it('applies the green flash on a significant rise', () => {
    renderPriceValue(64_213.5, 'up')

    expectFlash('up')
  })

  it('applies the red flash on a significant drop', () => {
    renderPriceValue(64_213.5, 'down')

    expectFlash('down')
  })
})
