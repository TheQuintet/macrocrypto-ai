import { useQuery } from '@tanstack/react-query'
import {
  fetchRegimePerformance,
  regimePerformanceQueryKey,
} from '@/api/regimes/regimePerformance'
import type { RegimePerformance } from '@/types/regime'

export { regimePerformanceQueryKey }

/** Regime boundaries move on the daily job, so this is not polled tightly. */
export function useRegimePerformanceQuery() {
  return useQuery<RegimePerformance, Error>({
    queryKey: regimePerformanceQueryKey(),
    queryFn: () => fetchRegimePerformance(),
    staleTime: 1000 * 60 * 30,
    refetchInterval: 1000 * 60 * 60,
  })
}
