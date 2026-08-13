import { cleanup, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  expectLastUpdated,
  expectStatusIndicator,
  expectTooltipDetail,
  openStatusTooltip,
  renderPriceStreamStatus,
} from '@/components/dashboard/price/PriceStreamStatus.testHelpers'
import { useBtcPriceSnapshotQuery } from '@/hooks/useBtcPriceSnapshotQuery'
import { usePriceStream } from '@/hooks/usePriceStream'
import type { PriceStreamStatus as StreamStatus } from '@/types/priceStream'

vi.mock('@/hooks/usePriceStream', () => ({ usePriceStream: vi.fn() }))
vi.mock('@/hooks/useBtcPriceSnapshotQuery', () => ({
  useBtcPriceSnapshotQuery: vi.fn(),
}))

const priceStream = vi.mocked(usePriceStream)
const snapshotQuery = vi.mocked(useBtcPriceSnapshotQuery)

function givenStream(
  status: StreamStatus,
  lastUpdatedAt: string | null = null,
  reconnectAttempts = 0,
) {
  priceStream.mockReturnValue({ status, reconnectAttempts })
  snapshotQuery.mockReturnValue({
    data: lastUpdatedAt ? { updatedAt: lastUpdatedAt } : undefined,
  } as ReturnType<typeof useBtcPriceSnapshotQuery>)
}

describe('PriceStreamStatus', () => {
  beforeEach(() => {
    priceStream.mockReset()
    snapshotQuery.mockReset()
  })

  afterEach(() => {
    cleanup()
  })

  it('shows a green live indicator while connected', () => {
    givenStream('connected')
    renderPriceStreamStatus()

    expectStatusIndicator('Live', 'text-positive')
  })

  it('shows an orange indicator while connecting', () => {
    givenStream('connecting')
    renderPriceStreamStatus()

    expectStatusIndicator('Connecting', 'text-warning')
  })

  it('shows a red indicator once disconnected', () => {
    givenStream('disconnected')
    renderPriceStreamStatus()

    expectStatusIndicator('Disconnected', 'text-negative')
  })

  it('shows the time of the last update', () => {
    const updatedAt = new Date('2024-06-15T12:34:56.000Z')
    givenStream('connected', updatedAt.toISOString())
    renderPriceStreamStatus()

    expectLastUpdated(
      updatedAt.toLocaleTimeString('en-GB', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      }),
    )
  })

  it('placeholders the timestamp until the first frame arrives', () => {
    givenStream('connecting', null)
    renderPriceStreamStatus()

    expectLastUpdated('--')
  })

  it('explains the connection in a tooltip', async () => {
    const user = userEvent.setup()
    givenStream('connected', '2024-06-15T12:34:56.000Z')
    renderPriceStreamStatus()

    await openStatusTooltip(user)

    expectTooltipDetail('Receiving live price updates')
    expectTooltipDetail(/^Last update /)
  })

  it('reports retry attempts in the tooltip while disconnected', async () => {
    const user = userEvent.setup()
    givenStream('disconnected', null, 3)
    renderPriceStreamStatus()

    await openStatusTooltip(user)

    expectTooltipDetail('Price feed lost — retrying automatically')
    expectTooltipDetail('Reconnect attempts 3')
  })

  it('omits the attempt count when there have been none', async () => {
    const user = userEvent.setup()
    givenStream('connected', null, 0)
    renderPriceStreamStatus()

    await openStatusTooltip(user)

    expect(screen.queryByText(/reconnect attempts/i)).not.toBeInTheDocument()
  })
})
