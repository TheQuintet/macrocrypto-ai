import { keepPreviousData, useQuery } from '@tanstack/react-query'
import {
  fetchMacroIndicators,
  macroIndicatorsQueryKey,
} from '@/api/macroIndicators'
import type { MacroIndicator } from '@/types/macroIndicators'
import type { TimeRange } from '@/types/preferences'

export function useMacroIndicatorHistoryQuery(
  range: TimeRange,
  enabled = true,
) {
  return useQuery<MacroIndicator[], Error>({
    queryKey: macroIndicatorsQueryKey(range),
    queryFn: () => fetchMacroIndicators(range),
    enabled,
    staleTime: 1000 * 60 * 5,
    placeholderData: keepPreviousData,
  })
}
