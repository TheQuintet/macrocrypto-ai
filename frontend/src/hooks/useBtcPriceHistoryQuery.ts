import { keepPreviousData, useQuery } from '@tanstack/react-query'
import {
  btcPriceHistoryQueryKey,
  fetchBtcPriceHistory,
} from '@/api/btcPriceHistory'
import type {
  BtcPriceHistoryParams,
  BtcPriceHistoryResponse,
} from '@/types/btcPriceHistory'

/** Fetch chart-ready BTC history for a range + interval (cached per combo). */
export function useBtcPriceHistoryQuery(params: BtcPriceHistoryParams) {
  return useQuery<BtcPriceHistoryResponse, Error>({
    queryKey: btcPriceHistoryQueryKey(params),
    queryFn: () => fetchBtcPriceHistory(params),
    placeholderData: keepPreviousData,
  })
}
