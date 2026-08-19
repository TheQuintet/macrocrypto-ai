import { useQuery } from '@tanstack/react-query';
import { fetchMacroIndicators } from '@/api/macroIndicators';
import type { MacroIndicator } from '@/types/macroIndicators';

export const macroIndicatorsQueryKey = ['macroIndicators'];

export function useMacroIndicatorsQuery() {
  return useQuery<MacroIndicator[]>({
    queryKey: macroIndicatorsQueryKey,
    queryFn: fetchMacroIndicators,
    staleTime: 1000 * 60 * 5, // 5 minutes
    refetchInterval: 1000 * 60 * 30, // 30 minutes
  });
}