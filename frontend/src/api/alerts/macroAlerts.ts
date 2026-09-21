import axios from 'axios'
import { fetchEconomicCalendar } from '@/api/economicCalendar/economicCalendar'
import {
  generateMockMacroEvents,
  generateMockMacroSubscriptions,
} from '@/api/alerts/simulatedMacroAlerts'
import { alertApiUrl, isApiConfigured } from '@/lib/apiConfig'
import {
  toApiEventType,
  toApiImpact,
  toUiMacroEvent,
  toUiSubscription,
  withDefaultSubscriptions,
  type SubscriptionPayload,
} from '@/lib/alerts/macroEventMapping'
import type {
  EventType,
  MacroAlertHistory,
  MacroEvent,
  MacroSubscription,
} from '@/types/alerts/macroAlert'

const JSON_HEADERS = { Accept: 'application/json' }

export const MACRO_SUBSCRIPTIONS_PATH = '/api/v1/macro/subscriptions'
export const MACRO_SUBSCRIBE_PATH = '/api/v1/macro/subscribe'

async function fromApiOrSimulate<T>(
  path: string,
  simulate: () => Promise<T>,
  live: (url: string) => Promise<T>,
): Promise<T> {
  const url = alertApiUrl(path)
  if (!url) {
    return simulate()
  }

  return live(url)
}

export const macroAlertApi = {
  getSubscriptions: async (userId: string): Promise<MacroSubscription[]> =>
    fromApiOrSimulate(
      `${MACRO_SUBSCRIPTIONS_PATH}/${userId}`,
      async () => generateMockMacroSubscriptions(userId),
      async (url) => {
        const response = await axios.get<{ subscriptions?: unknown[] }>(url, {
          headers: JSON_HEADERS,
        })
        const mapped = (response.data.subscriptions ?? [])
          .map((row) =>
            toUiSubscription(row as SubscriptionPayload, userId),
          )
          .filter((row): row is MacroSubscription => row !== null)

        return withDefaultSubscriptions(userId, mapped)
      },
    ),

  updateSubscription: async (
    userId: string,
    eventType: EventType,
    subscribed: boolean,
    oneTime: boolean = true,
  ): Promise<MacroSubscription> =>
    fromApiOrSimulate(
      MACRO_SUBSCRIBE_PATH,
      async () => ({
        id: crypto.randomUUID(),
        user_id: userId,
        event_type: eventType,
        subscribed,
        impact_filter: 'HIGH',
        timing: '1D',
        one_time: oneTime,
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
            impact_filter: 'HIGH',
            timing: '1D',
            one_time: oneTime,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          }
        )
      },
    ),

  updateImpactFilter: async (): Promise<{ success: boolean }> => {
    return { success: true }
  },

  getUpcomingEvents: async (): Promise<MacroEvent[]> => {
    if (isApiConfigured()) {
      const events = await fetchEconomicCalendar()
      const mapped = events
        .map(toUiMacroEvent)
        .filter((event): event is MacroEvent => event !== null)
      const now = Date.now()
      const upcoming = mapped
        .filter((event) => Date.parse(event.scheduled_at) >= now)
        .sort(
          (left, right) =>
            Date.parse(left.scheduled_at) - Date.parse(right.scheduled_at),
        )

      if (upcoming.length > 0) {
        return upcoming.slice(0, 50)
      }

      return [...mapped]
        .sort(
          (left, right) =>
            Date.parse(right.scheduled_at) - Date.parse(left.scheduled_at),
        )
        .slice(0, 50)
    }

    return generateMockMacroEvents()
  },

  getHistory: async (): Promise<MacroAlertHistory[]> => {
    return []
  },
}

export default macroAlertApi
