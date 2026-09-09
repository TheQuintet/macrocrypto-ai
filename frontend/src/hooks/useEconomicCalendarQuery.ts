import { useQuery } from '@tanstack/react-query'
import {
  economicCalendarQueryKey,
  fetchEconomicCalendar,
} from '@/api/economicCalendar/economicCalendar'
import type { EconomicEvent } from '@/types/economicCalendar'

export { economicCalendarQueryKey }

/**
 * The release schedule changes on the order of days, so this is cached
 * generously — paging between months must never refetch.
 */
export function useEconomicCalendarQuery() {
  return useQuery<EconomicEvent[], Error>({
    queryKey: economicCalendarQueryKey(),
    queryFn: () => fetchEconomicCalendar(),
    staleTime: 1000 * 60 * 30,
    refetchInterval: 1000 * 60 * 60,
  })
}
