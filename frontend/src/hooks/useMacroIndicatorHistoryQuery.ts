import { keepPreviousData, useQuery } from '@tanstack/react-query'
import {
  fetchMacroIndicatorHistory,
  macroIndicatorHistoryQueryKey,
} from '@/api/macroIndicators/macroIndicatorHistory'
import type { MacroIndicator } from '@/types/macroIndicators'
import type { TimeRange } from '@/types/preferences'

export function useMacroIndicatorHistoryQuery(
  range: TimeRange,
  enabled = true,
) {
  return useQuery<MacroIndicator[], Error>({
    queryKey: macroIndicatorHistoryQueryKey(range),
    queryFn: () => fetchMacroIndicatorHistory(range),
    enabled,
    staleTime: 1000 * 60 * 5,
    placeholderData: keepPreviousData,
  })
}
