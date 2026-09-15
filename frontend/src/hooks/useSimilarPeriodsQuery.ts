import { useQuery } from '@tanstack/react-query'
import {
  fetchSimilarPeriods,
  similarPeriodsQueryKey,
} from '@/api/regimes/similarPeriods'
import type { SimilarPeriods } from '@/types/regime'

export { similarPeriodsQueryKey }

/**
 * Matches are recomputed from the latest indicator prints, which move on the
 * daily job, so this is not polled tightly.
 */
export function useSimilarPeriodsQuery() {
  return useQuery<SimilarPeriods, Error>({
    queryKey: similarPeriodsQueryKey(),
    queryFn: () => fetchSimilarPeriods(),
    staleTime: 1000 * 60 * 30,
    refetchInterval: 1000 * 60 * 60,
  })
}
