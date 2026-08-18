import { cleanup } from '@testing-library/react'
import { afterEach, beforeEach, describe, it, vi } from 'vitest'
import { fetchBtcPriceSnapshot } from '@/api/btcPrice'
import { SNAPSHOT } from '@/components/dashboard/price/BtcPriceCard.testHelpers'
import {
  expectLoadingSkeletons,
  expectWindowValues,
  renderPriceChangeCard,
} from '@/components/dashboard/price/PriceChangeCard.testHelpers'

vi.mock('@/api/btcPrice', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/api/btcPrice')>()
  return { ...actual, fetchBtcPriceSnapshot: vi.fn() }
})

const fetchSnapshot = vi.mocked(fetchBtcPriceSnapshot)

describe('PriceChangeCard', () => {
  beforeEach(() => {
    fetchSnapshot.mockReset()
  })

  afterEach(() => {
    cleanup()
    vi.restoreAllMocks()
  })

  it('renders the 24h and 7d windows with their own values', async () => {
    fetchSnapshot.mockResolvedValue(SNAPSHOT)
    renderPriceChangeCard()

    await expectWindowValues('24h change', '+1.76%', '+$1,113.50')
    await expectWindowValues('7d change', '+4.58%', '+$2,813.50')
  })

  it('shows a loading state before the first snapshot arrives', () => {
    fetchSnapshot.mockReturnValue(new Promise(() => undefined))
    renderPriceChangeCard()

    expectLoadingSkeletons()
  })
})
