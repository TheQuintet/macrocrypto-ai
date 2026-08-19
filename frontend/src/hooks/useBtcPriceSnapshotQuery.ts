import { useQuery } from '@tanstack/react-query'
import {
  btcPriceSnapshotQueryKey,
  fetchBtcPriceSnapshot,
  PRICE_SNAPSHOT_TICK_MS,
} from '@/api/btcPrice'
import { usePriceStreamStore } from '@/stores/priceStreamStore'
import type { BtcPriceSnapshot } from '@/types/btcPrice'

/**
 * Current BTC snapshot (price + 24h/7d change windows).
 *
 * The live stream is the primary transport and writes straight into this
 * cache entry; polling is the fallback and stands down while the socket is
 * connected, so the two never fight over the same key.
 */
export function useBtcPriceSnapshotQuery() {
  const isStreamConnected = usePriceStreamStore(
    (state) => state.status === 'connected',
  )

  return useQuery<BtcPriceSnapshot, Error>({
    queryKey: btcPriceSnapshotQueryKey(),
    queryFn: () => fetchBtcPriceSnapshot(),
    refetchInterval: isStreamConnected ? false : PRICE_SNAPSHOT_TICK_MS,
    staleTime: PRICE_SNAPSHOT_TICK_MS,
  })
}
