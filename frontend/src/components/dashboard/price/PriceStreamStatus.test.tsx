import { cleanup } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import {
  expectLastUpdated,
  expectStatusIndicator,
  renderPriceStreamStatus,
} from '@/components/dashboard/price/PriceStreamStatus.testHelpers'
import { usePriceStream } from '@/hooks/usePriceStream'

vi.mock('@/hooks/usePriceStream', () => ({ usePriceStream: vi.fn() }))

const priceStream = vi.mocked(usePriceStream)

function givenStream(
  status: 'connecting' | 'connected' | 'disconnected',
  lastUpdatedAt: string | null = null,
) {
  priceStream.mockReturnValue({ status, lastUpdatedAt })
}

describe('PriceStreamStatus', () => {
  beforeEach(() => {
    priceStream.mockReset()
  })

  afterEach(() => {
    cleanup()
  })

  it('shows a live indicator while connected', () => {
    givenStream('connected')
    renderPriceStreamStatus()

    expectStatusIndicator('Live', 'text-positive')
  })

  it('shows a connecting indicator before the first handshake', () => {
    givenStream('connecting')
    renderPriceStreamStatus()

    expectStatusIndicator('Connecting', 'text-muted-foreground')
  })

  it('shows a reconnecting indicator after a connection loss', () => {
    givenStream('disconnected')
    renderPriceStreamStatus()

    expectStatusIndicator('Reconnecting', 'text-negative')
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

  it('mounts the stream so the connection is owned in one place', () => {
    givenStream('connected')
    renderPriceStreamStatus()

    expect(priceStream).toHaveBeenCalled()
  })
})
