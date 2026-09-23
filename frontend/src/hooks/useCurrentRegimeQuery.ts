import { useQuery } from '@tanstack/react-query'
import {
  currentRegimeQueryKey,
  fetchCurrentRegime,
} from '@/api/regimes/currentRegime'
import type { CurrentRegime } from '@/types/regime'

export { currentRegimeQueryKey }

/**
 * The service reclassifies once a day, so this is polled on the hour rather
 * than on the price cadence.
 */
export function useCurrentRegimeQuery() {
  return useQuery<CurrentRegime | null, Error>({
    queryKey: currentRegimeQueryKey(),
    queryFn: () => fetchCurrentRegime(),
    staleTime: 1000 * 60 * 30,
    refetchInterval: 1000 * 60 * 60,
  })
}
