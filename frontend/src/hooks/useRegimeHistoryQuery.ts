import { useQuery } from '@tanstack/react-query'
import {
  fetchRegimeHistory,
  regimeHistoryQueryKey,
} from '@/api/regimes/regimeHistory'
import type { RegimeHistory } from '@/types/regime'

export { regimeHistoryQueryKey }

/** Regime boundaries move on the daily job, so this is not polled tightly. */
export function useRegimeHistoryQuery() {
  return useQuery<RegimeHistory, Error>({
    queryKey: regimeHistoryQueryKey(),
    queryFn: () => fetchRegimeHistory(),
    staleTime: 1000 * 60 * 30,
    refetchInterval: 1000 * 60 * 60,
  })
}
