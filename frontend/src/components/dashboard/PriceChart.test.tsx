import userEvent from '@testing-library/user-event'
import { cleanup, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  expectNoChartTypeSwitcher,
  renderPriceChart,
} from '@/components/dashboard/PriceChart.testHelpers'
import { resetPreferencesStore } from '@/stores/preferencesStore.testHelpers'
import { usePreferencesStore } from '@/stores/preferencesStore'

vi.mock('@/hooks/useBtcPriceHistoryQuery', () => ({
  useBtcPriceHistoryQuery: () => ({
    data: undefined,
    isPending: true,
    isFetching: false,
    isError: false,
    error: null,
  }),
}))

describe('PriceChart', () => {
  beforeEach(() => {
    resetPreferencesStore()
  })

  afterEach(() => {
    cleanup()
    resetPreferencesStore()
  })

  it('does not offer a line-chart switcher', () => {
    renderPriceChart()
    expectNoChartTypeSwitcher()
  })

  it('places the time range on the left and candle size on the right', () => {
    renderPriceChart()

    const heading = screen.getByRole('heading', { name: 'BTC price' })
    const range = screen.getByRole('group', { name: 'Time range' })
    const interval = screen.getByRole('group', { name: 'Chart interval' })

    expect(
      heading.compareDocumentPosition(range) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy()
    expect(
      range.compareDocumentPosition(interval) & Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy()
  })

  it('opens on daily candles', () => {
    renderPriceChart()

    expect(screen.getByRole('button', { name: 'Daily' })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
    expect(screen.getByRole('heading', { name: 'BTC price' }).parentElement)
      .toHaveTextContent(/daily candles/i)
  })

  it('switches to weekly candles', async () => {
    const user = userEvent.setup()
    renderPriceChart()

    await user.click(screen.getByRole('button', { name: 'Weekly' }))

    expect(screen.getByRole('button', { name: 'Weekly' })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
    expect(usePreferencesStore.getState().candleInterval).toBe('1w')
    expect(screen.getByRole('heading', { name: 'BTC price' }).parentElement)
      .toHaveTextContent(/weekly candles/i)
  })

  it('uses weekly candles when the range is 1y', async () => {
    const user = userEvent.setup()
    renderPriceChart()

    await user.click(screen.getByRole('button', { name: '1y' }))

    expect(usePreferencesStore.getState().candleInterval).toBe('1w')
    expect(screen.getByRole('button', { name: 'Weekly' })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
    expect(screen.getByRole('button', { name: 'Daily' })).toBeDisabled()
    expect(screen.getByRole('heading', { name: 'BTC price' }).parentElement)
      .toHaveTextContent(/weekly candles/i)
  })
})
