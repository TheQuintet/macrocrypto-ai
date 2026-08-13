import { cleanup } from '@testing-library/react'
import { afterEach, describe, it } from 'vitest'
import {
  expectChangeArrow,
  expectChangeTone,
  expectChangeUnavailable,
  expectChangeValues,
  renderPriceChangeStat,
} from '@/components/dashboard/price/PriceChangeStat.testHelpers'

describe('PriceChangeStat', () => {
  afterEach(() => {
    cleanup()
  })

  it('shows a 24h rise as percentage and absolute value', () => {
    renderPriceChangeStat('24h', 1_113.5, 1.76)

    expectChangeValues('24h change', '+1.76%', '+$1,113.50')
  })

  it('shows a 7d rise as percentage and absolute value', () => {
    renderPriceChangeStat('7d', 2_813.5, 4.58)

    expectChangeValues('7d change', '+4.58%', '+$2,813.50')
  })

  it('colours a rise positive and points the arrow up', () => {
    renderPriceChangeStat('24h', 1_113.5, 1.76)

    expectChangeTone('24h change', 'positive')
    expectChangeArrow('24h change', 'up')
  })

  it('colours a drop negative and points the arrow down', () => {
    renderPriceChangeStat('24h', -820.1, -1.28)

    expectChangeValues('24h change', '-1.28%', '-$820.10')
    expectChangeTone('24h change', 'negative')
    expectChangeArrow('24h change', 'down')
  })

  it('stays neutral when the price is flat', () => {
    renderPriceChangeStat('24h', 0, 0)

    expectChangeTone('24h change', 'muted')
    expectChangeArrow('24h change', 'flat')
  })

  it('falls back to placeholders when the window is unavailable', () => {
    renderPriceChangeStat('7d', null, null)

    expectChangeUnavailable('7d change')
  })
})
