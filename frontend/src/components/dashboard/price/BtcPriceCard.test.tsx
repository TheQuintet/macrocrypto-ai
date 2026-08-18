import { cleanup } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { fetchBtcPriceSnapshot } from '@/api/btcPrice'
import {
  expect24hRangeShown,
  expectLoadingSkeleton,
  expectPriceShown,
  expectPriceUnavailable,
  renderBtcPriceCard,
  silenceQueryErrors,
  snapshotWith,
  SNAPSHOT,
} from '@/components/dashboard/price/BtcPriceCard.testHelpers'

vi.mock('@/api/btcPrice', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/api/btcPrice')>()
  return { ...actual, fetchBtcPriceSnapshot: vi.fn() }
})

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

  it('renders the 24h high and low alongside the price', async () => {
    fetchSnapshot.mockResolvedValue(SNAPSHOT)
    renderBtcPriceCard()

    await expect24hRangeShown()
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
