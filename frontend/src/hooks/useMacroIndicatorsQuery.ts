import { useQuery } from '@tanstack/react-query'
import {
  fetchMacroIndicators,
  macroIndicatorsQueryKey,
} from '@/api/macroIndicators'
import type { MacroIndicator } from '@/types/macroIndicators'

export { macroIndicatorsQueryKey }

export function useMacroIndicatorsQuery() {
  return useQuery<MacroIndicator[], Error>({
    queryKey: macroIndicatorsQueryKey(),
    queryFn: () => fetchMacroIndicators(),
    staleTime: 1000 * 60 * 5,
    refetchInterval: 1000 * 60 * 30,
  })
}
