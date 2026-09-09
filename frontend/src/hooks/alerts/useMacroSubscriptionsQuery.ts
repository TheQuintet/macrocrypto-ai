import { useQuery } from '@tanstack/react-query'
import {
  fetchMacroSubscriptions,
  macroSubscriptionsQueryKey,
} from '@/api/alerts/macroSubscriptions'
import type { MacroEventSubscription } from '@/types/alerts/macroSubscription'

export { macroSubscriptionsQueryKey }

export function useMacroSubscriptionsQuery(userId: string) {
  return useQuery<MacroEventSubscription[], Error>({
    queryKey: macroSubscriptionsQueryKey(userId),
    queryFn: () => fetchMacroSubscriptions(userId),
    enabled: Boolean(userId),
    staleTime: 1000 * 60 * 5,
  })
}
