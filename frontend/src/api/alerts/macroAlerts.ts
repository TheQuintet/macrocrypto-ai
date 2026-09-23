import axios from 'axios'
import { generateMockMacroSubscriptions } from '@/api/alerts/simulatedMacroAlerts'
import {
  MACRO_SUBSCRIBE_PATH,
  MACRO_SUBSCRIPTIONS_PATH,
} from '@/constants/apiUrls'
import { apiUrl } from '@/lib/apiConfig'
import {
  toApiEventType,
  toApiImpact,
  toUiSubscription,
  type SubscriptionPayload,
} from '@/lib/alerts/macroEventMapping'
import type {
  EventType,
  MacroSubscription,
} from '@/types/alerts/macroAlert'

const JSON_HEADERS = { Accept: 'application/json' }

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
    eventType: EventType,
    subscribed: boolean,
  ): Promise<MacroSubscription> =>
    fromApiOrSimulate(
      MACRO_SUBSCRIBE_PATH,
      async () => ({
        id: crypto.randomUUID(),
        user_id: userId,
        event_type: eventType,
        subscribed,
        impact_filter: 'HIGH',
        timing: null,
        one_time: null,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }),
      async (url) => {
        const response = await axios.post<SubscriptionPayload>(url, {
          user_id: userId,
          event_type: toApiEventType(eventType),
          subscribed,
          impact_filter: toApiImpact('HIGH'),
        }, {
          headers: JSON_HEADERS,
        })

        return (
          toUiSubscription(response.data, userId) ?? {
            id: crypto.randomUUID(),
            user_id: userId,
            event_type: eventType,
            subscribed,
            impact_filter: null,
            timing: null,
            one_time: null,
            created_at: null,
            updated_at: null,
          }
        )
      },
    ),
}

export default macroAlertApi
