import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import type { PriceStreamStatus } from '@/types/priceStream'

type PriceStreamState = {
  status: PriceStreamStatus
  /** Consecutive reconnect attempts; reset to 0 once connected. */
  reconnectAttempts: number
  setStatus: (status: PriceStreamStatus) => void
  setReconnectAttempts: (reconnectAttempts: number) => void
}

/** Live-connection state: transport status, not server data. */
export const usePriceStreamStore = create<PriceStreamState>()(
  devtools(
    (set) => ({
      status: 'connecting',
      reconnectAttempts: 0,
      setStatus: (status) =>
        set({ status }, undefined, 'priceStream/setStatus'),
      setReconnectAttempts: (reconnectAttempts) =>
        set(
          { reconnectAttempts },
          undefined,
          'priceStream/setReconnectAttempts',
        ),
    }),
    { name: 'PriceStreamStore' },
  ),
)
