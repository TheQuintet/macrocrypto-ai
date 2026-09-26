import axios from 'axios'
import {
  generateMockMacroSubscriptions,
  upsertMockMacroSubscription,
} from '@/api/alerts/simulatedMacroAlerts'
import {
  MACRO_SUBSCRIBE_PATH,
  MACRO_SUBSCRIPTIONS_PATH,
} from '@/constants/apiUrls'
import { apiUrl } from '@/lib/apiConfig'
import {
  toApiEventType,
  toApiImpact,
  toApiTiming,
  toUiSubscription,
  type SubscriptionPayload,
} from '@/lib/alerts/macroEventMapping'
import type {
  MacroSubscription,
  MacroSubscriptionWrite,
} from '@/types/alerts/macroAlert'

const JSON_HEADERS = { Accept: 'application/json' }

function subscribePayload(userId: string, write: MacroSubscriptionWrite) {
  return {
    user_id: userId,
    event_type: toApiEventType(write.event_type),
    subscribed: write.subscribed,
    impact_filter: toApiImpact('HIGH'),
    timing: toApiTiming(write.timing),
    one_time: write.one_time,
    notify_in_app: write.notify_in_app,
    notify_email: write.notify_email,
  }
}

async function fromApiOrSimulate<T>(
  path: string,
  simulate: () => Promise<T>,
  live: (url: string) => Promise<T>,
): Promise<T> {
  const url = apiUrl(path)
  if (!url) {
    return simulate()
  }

  return live(url)
}

export const macroAlertApi = {
  /** Exactly the rows the alert service holds for this user — nothing added. */
  getSubscriptions: async (userId: string): Promise<MacroSubscription[]> =>
    fromApiOrSimulate(
      `${MACRO_SUBSCRIPTIONS_PATH}/${userId}`,
      async () => generateMockMacroSubscriptions(userId),
      async (url) => {
        const response = await axios.get<{ subscriptions?: unknown[] }>(url, {
          headers: JSON_HEADERS,
        })

        return (response.data.subscriptions ?? [])
          .map((row) =>
            toUiSubscription(row as SubscriptionPayload, userId),
          )
          .filter((row): row is MacroSubscription => row !== null)
      },
    ),

  updateSubscription: async (
    userId: string,
    write: MacroSubscriptionWrite,
  ): Promise<MacroSubscription> =>
    fromApiOrSimulate(
      MACRO_SUBSCRIBE_PATH,
      async () => upsertMockMacroSubscription(userId, write),
      async (url) => {
        const response = await axios.post<SubscriptionPayload>(
          url,
          subscribePayload(userId, write),
          {
            headers: JSON_HEADERS,
          },
        )

        return (
          toUiSubscription(response.data, userId) ?? {
            id: crypto.randomUUID(),
            user_id: userId,
            event_type: write.event_type,
            subscribed: write.subscribed,
            impact_filter: 'HIGH',
            timing: write.timing,
            one_time: write.one_time,
            notify_in_app: write.notify_in_app,
            notify_email: write.notify_email,
            created_at: null,
            updated_at: null,
          }
        )
      },
    ),
}

export default macroAlertApi
