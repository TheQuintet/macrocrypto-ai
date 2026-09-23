import axios from 'axios';
import { MACRO_ALERT_HISTORY_PATH } from '@/constants/apiUrls';
import { apiUrl } from '@/lib/apiConfig';
import { simulateMacroAlertHistory } from '@/api/alerts/simulatedMacroAlertHistory';
import type { MacroAlertHistoryResponse } from '@/types/alerts/macroAlertHistory';

/**
 * The endpoint caps `limit` at 100. The view filters, searches, and paginates
 * the rows it holds, so it takes one full page rather than paging the server —
 * otherwise a search would only ever look inside the page it happened to be
 * on. When the user has more sent alerts than this, the view says so instead
 * of quietly searching a subset.
 */
export const MACRO_ALERT_HISTORY_LIMIT = 100;

export function macroAlertHistoryQueryKey(userId: string) {
  return ['macroAlertHistory', userId] as const;
}

/**
 * Macro alerts that were actually sent to this user.
 *
 * Follows the API gateway like the rest of the alert surface: unset →
 * simulated history, set → a failed request throws rather than showing an
 * empty history the user might read as "I was never alerted".
 */
export async function fetchMacroAlertHistory(
  userId: string,
): Promise<MacroAlertHistoryResponse> {
  const url = apiUrl(`${MACRO_ALERT_HISTORY_PATH}/${userId}`);

  if (!url) {
    return simulateMacroAlertHistory(userId);
  }

  const response = await axios.get<MacroAlertHistoryResponse>(url, {
    params: { limit: MACRO_ALERT_HISTORY_LIMIT },
    headers: { Accept: 'application/json' },
  });

  return {
    total: response.data.total ?? 0,
    limit: response.data.limit ?? MACRO_ALERT_HISTORY_LIMIT,
    offset: response.data.offset ?? 0,
    notifications: response.data.notifications ?? [],
  };
}
