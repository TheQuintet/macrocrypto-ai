import { useQuery } from '@tanstack/react-query'
import {
  btcPriceSnapshotQueryKey,
  fetchBtcPriceSnapshot,
  PRICE_SNAPSHOT_TICK_MS,
} from '@/api/btcPrice'
import type { BtcPriceSnapshot } from '@/types/btcPrice'

/**
 * Current BTC snapshot (price + 24h/7d change windows).
 *
 * Refetches on the snapshot cadence so the display stays current; the live
 * stream replaces this as the primary transport and leaves it as the fallback.
 */
export function useBtcPriceSnapshotQuery() {
  return useQuery<BtcPriceSnapshot, Error>({
    queryKey: btcPriceSnapshotQueryKey(),
    queryFn: () => fetchBtcPriceSnapshot(),
    refetchInterval: PRICE_SNAPSHOT_TICK_MS,
    staleTime: PRICE_SNAPSHOT_TICK_MS,
  })
}
