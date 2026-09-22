import { useQuery } from '@tanstack/react-query';
import {
  fetchMacroAlertHistory,
  macroAlertHistoryQueryKey,
} from '@/api/alerts/macroAlertHistory';
import type { MacroAlertHistoryResponse } from '@/types/alerts/macroAlertHistory';

export { macroAlertHistoryQueryKey };

/** Sent alerts only grow at the pace of the release calendar, so cache generously. */
export function useMacroAlertHistoryQuery(userId: string) {
  return useQuery<MacroAlertHistoryResponse, Error>({
    queryKey: macroAlertHistoryQueryKey(userId),
    queryFn: () => fetchMacroAlertHistory(userId),
    enabled: Boolean(userId),
    staleTime: 1000 * 60 * 5,
  });
}
