import { keepPreviousData, useQuery } from '@tanstack/react-query'
import {
  fetchMacroIndicators,
  macroIndicatorsQueryKey,
} from '@/api/macroIndicators'
import type {
  MacroIndicator,
  MacroIndicatorPeriod,
} from '@/types/macroIndicators'

export function useMacroIndicatorHistoryQuery(
  period: MacroIndicatorPeriod,
  enabled = true,
) {
  return useQuery<MacroIndicator[], Error>({
    queryKey: macroIndicatorsQueryKey(period),
    queryFn: () => fetchMacroIndicators(period),
    enabled,
    staleTime: 1000 * 60 * 5,
    placeholderData: keepPreviousData,
  })
}
