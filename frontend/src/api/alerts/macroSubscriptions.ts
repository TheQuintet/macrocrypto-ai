import axios from 'axios'
import { MACRO_SUBSCRIPTIONS_PATH } from '@/constants/apiUrls'
import { apiUrl } from '@/lib/apiConfig'
import { simulateMacroSubscriptions } from '@/api/alerts/simulatedMacroSubscriptions'
import type {
  MacroEventSubscription,
  MacroSubscriptionsResponse,
} from '@/types/alerts/macroSubscription'

export function macroSubscriptionsQueryKey(userId: string) {
  return ['macroSubscriptions', userId] as const
}

/**
 * A user's macro event subscriptions, used to show which calendar events would
 * actually alert them.
 *
 * Follows the API gateway like price-alert CRUD: unset → simulated
 * subscriptions, set → a failed request throws rather than implying the user
 * is subscribed to nothing.
 */
export async function fetchMacroSubscriptions(
  userId: string,
): Promise<MacroEventSubscription[]> {
  const url = apiUrl(`${MACRO_SUBSCRIPTIONS_PATH}/${userId}`)

  if (!url) {
    return simulateMacroSubscriptions(userId)
  }

  const response = await axios.get<MacroSubscriptionsResponse>(url, {
    headers: { Accept: 'application/json' },
  })

  return response.data.subscriptions ?? []
}
