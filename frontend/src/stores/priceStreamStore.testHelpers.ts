import { usePriceStreamStore } from '@/stores/priceStreamStore'
import type { PriceStreamStatus } from '@/types/priceStream'

/** Reset shared Zustand state between tests. */
export function resetPriceStreamStore(
  status: PriceStreamStatus = 'connecting',
  lastUpdatedAt: string | null = null,
): void {
  usePriceStreamStore.setState({ status, lastUpdatedAt })
}
