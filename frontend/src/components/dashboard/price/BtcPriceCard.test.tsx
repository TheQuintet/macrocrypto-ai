import { cleanup, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { fetchBtcPriceSnapshot } from '@/api/btcPrice/btcPrice'
import {
  expect24hSessionShown,
  expectLoadingSkeleton,
  expectPriceShown,
  expectPriceUnavailable,
  renderBtcPriceCard,
  silenceQueryErrors,
  snapshotWith,
  SNAPSHOT,
} from '@/components/dashboard/price/BtcPriceCard.testHelpers'

vi.mock('@/api/btcPrice/btcPrice', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/api/btcPrice/btcPrice')>()
  return { ...actual, fetchBtcPriceSnapshot: vi.fn() }
})

vi.mock('@/stores/priceStreamStore', () => ({
  usePriceStreamStore: (selector: (state: unknown) => unknown) =>
    selector({
      status: 'connecting',
      reconnectAttempts: 0,
      setStatus: vi.fn(),
      setReconnectAttempts: vi.fn(),
    }),
}))

const fetchSnapshot = vi.mocked(fetchBtcPriceSnapshot)

describe('BtcPriceCard', () => {
  beforeEach(() => {
    fetchSnapshot.mockReset()
  })

  afterEach(() => {
    cleanup()
    vi.restoreAllMocks()
  })

  it('renders the BTC price in USD once loaded', async () => {
    fetchSnapshot.mockResolvedValue(SNAPSHOT)
    renderBtcPriceCard()

    await expectPriceShown('$64,213.50')
  })

  it('renders the 24h high, low and volume alongside the price', async () => {
    fetchSnapshot.mockResolvedValue(SNAPSHOT)
    renderBtcPriceCard()

    await expect24hSessionShown()
  })

  it('labels simulated data so it cannot pass as the real market', async () => {
    fetchSnapshot.mockResolvedValue(snapshotWith({ source: 'simulated' }))
    renderBtcPriceCard()

    await expectPriceShown('$64,213.50')
    expect(screen.getByText('Simulated')).toBeInTheDocument()
  })

  it('shows no such label for live data', async () => {
    fetchSnapshot.mockResolvedValue(SNAPSHOT)
    renderBtcPriceCard()

    await expectPriceShown('$64,213.50')
    expect(screen.queryByText('Simulated')).not.toBeInTheDocument()
  })

  it('shows a loading state while the price is in flight', () => {
    fetchSnapshot.mockReturnValue(new Promise(() => undefined))
    renderBtcPriceCard()

    expectLoadingSkeleton()
  })

  it('shows an error state when the price request fails', async () => {
    silenceQueryErrors()
    fetchSnapshot.mockRejectedValue(new Error('service unavailable'))
    renderBtcPriceCard()

    await expectPriceUnavailable()
  })

  it('shows an error state when the service reports no price', async () => {
    fetchSnapshot.mockResolvedValue(snapshotWith({ currentPrice: null }))
    renderBtcPriceCard()

    await expectPriceUnavailable()
    expect(fetchSnapshot).toHaveBeenCalled()
  })
})
