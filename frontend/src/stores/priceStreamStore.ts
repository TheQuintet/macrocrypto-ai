import { create } from 'zustand'
import { devtools } from 'zustand/middleware'
import type { PriceStreamStatus } from '@/types/priceStream'

type PriceStreamState = {
  status: PriceStreamStatus
  /** ISO timestamp of the last frame received, or `null` before the first. */
  lastUpdatedAt: string | null
  setStatus: (status: PriceStreamStatus) => void
  setLastUpdatedAt: (lastUpdatedAt: string | null) => void
}

/** Live-connection state: transport status, not server data. */
export const usePriceStreamStore = create<PriceStreamState>()(
  devtools(
    (set) => ({
      status: 'connecting',
      lastUpdatedAt: null,
      setStatus: (status) =>
        set({ status }, undefined, 'priceStream/setStatus'),
      setLastUpdatedAt: (lastUpdatedAt) =>
        set({ lastUpdatedAt }, undefined, 'priceStream/setLastUpdatedAt'),
    }),
    { name: 'PriceStreamStore' },
  ),
)
