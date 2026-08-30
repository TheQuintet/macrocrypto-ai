import { QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook } from '@testing-library/react'
import type { ReactNode } from 'react'
import { expect, vi } from 'vitest'
import { btcPriceSnapshotQueryKey } from '@/api/btcPrice/btcPrice'
import { usePriceStream } from '@/hooks/usePriceStream'
import { createTestQueryClient } from '@/test/renderWithQuery'
import type { BtcPriceSnapshot } from '@/types/btcPrice'
import type { PriceSocketEvent, PriceSocketFactory } from '@/types/priceStream'

export const PRICE_FRAME = {
  current_price: 64_213.5,
  change_24h: 1_113.5,
  change_24h_percent: 1.76,
  high_24h: 64_993.5,
  low_24h: 63_573.5,
  volume_24h: 24_180.42,
  change_7d: 2_813.5,
  change_7d_percent: 4.58,
  updated_at: '2024-06-15T12:00:00.000Z',
}

/** A socket whose lifecycle the test drives by hand. */
export function createControllableSocket() {
  let emit: ((event: PriceSocketEvent) => void) | undefined
  let connectCount = 0
  let closeCount = 0

  const factory: PriceSocketFactory = (onEvent) => {
    connectCount += 1
    emit = onEvent
    return {
      close: () => {
        closeCount += 1
      },
    }
  }

  const send = (event: PriceSocketEvent) => {
    act(() => {
      emit?.(event)
    })
  }

  return {
    factory,
    connectCount: () => connectCount,
    closeCount: () => closeCount,
    open: () => send({ type: 'open' }),
    sendFrame: (frame: unknown = PRICE_FRAME) =>
      send({ type: 'message', data: JSON.stringify(frame) }),
    sendRaw: (data: string) => send({ type: 'message', data }),
    drop: () => send({ type: 'close' }),
    fail: () => send({ type: 'error' }),
  }
}

export function renderPriceStream(socketFactory: PriceSocketFactory | null) {
  const queryClient = createTestQueryClient()

  const view = renderHook(() => usePriceStream({ socketFactory: socketFactory ?? undefined }), {
    wrapper: ({ children }: { children: ReactNode }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    ),
  })

  return { view, queryClient }
}

export function getCachedSnapshot(
  queryClient: ReturnType<typeof createTestQueryClient>,
) {
  return queryClient.getQueryData<BtcPriceSnapshot>(btcPriceSnapshotQueryKey())
}

export function advanceBy(ms: number) {
  act(() => {
    vi.advanceTimersByTime(ms)
  })
}

export function expectStatus(
  view: ReturnType<typeof renderPriceStream>['view'],
  status: string,
) {
  expect(view.result.current.status).toBe(status)
}
