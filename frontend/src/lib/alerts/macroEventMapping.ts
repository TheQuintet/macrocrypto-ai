import type {
  EventImpact,
  EventTiming,
  EventType,
  MacroEvent,
  MacroSubscription,
} from '@/types/alerts/macroAlert'
import type { EconomicEvent } from '@/types/economicCalendar'

export const MACRO_EVENT_TYPES: EventType[] = [
  'FED',
  'CPI',
  'GDP',
  'EMPLOYMENT',
]

const EVENT_TYPE_SET = new Set<string>(MACRO_EVENT_TYPES)
const IMPACT_SET = new Set<string>(['HIGH', 'MEDIUM', 'LOW'])
const TIMING_SET = new Set<string>(['1D', '12H', '1H'])

export function toApiEventType(eventType: EventType) {
  return eventType.toLowerCase()
}

export function toUiEventType(value: string | null | undefined): EventType | null {
  const normalized = value?.toUpperCase()
  if (!normalized || !EVENT_TYPE_SET.has(normalized)) {
    return null
  }
  return normalized as EventType
}

export function toApiImpact(impact: EventImpact) {
  return impact.toLowerCase()
}

export function toUiImpact(value: string | null | undefined): EventImpact {
  const normalized = value?.toUpperCase()
  if (normalized && IMPACT_SET.has(normalized)) {
    return normalized as EventImpact
  }
  return 'HIGH'
}

export function toUiTiming(value: string | null | undefined): EventTiming {
  const normalized = value?.toUpperCase()
  if (normalized && TIMING_SET.has(normalized)) {
    return normalized as EventTiming
  }
  return '1D'
}

export type SubscriptionPayload = {
  id?: string
  user_id?: string
  event_type?: string
  subscribed?: boolean
  impact_filter?: string | null
  timing?: string | null
  one_time?: boolean
  created_at?: string | null
  updated_at?: string | null
}

export function toUiSubscription(
  payload: SubscriptionPayload,
  fallbackUserId: string,
): MacroSubscription | null {
  const eventType = toUiEventType(payload.event_type)
  if (!eventType) {
    return null
  }

  return {
    id: payload.id ?? `subscription-${eventType}`,
    user_id: payload.user_id ?? fallbackUserId,
    event_type: eventType,
    subscribed: Boolean(payload.subscribed),
    impact_filter: toUiImpact(payload.impact_filter),
    timing: toUiTiming(payload.timing),
    one_time: payload.one_time ?? true,
    created_at: payload.created_at ?? new Date().toISOString(),
    updated_at: payload.updated_at ?? new Date().toISOString(),
  }
}

/** Keep a row for every event type the alerts UI can toggle. */
export function withDefaultSubscriptions(
  userId: string,
  subscriptions: MacroSubscription[],
): MacroSubscription[] {
  const byType = new Map(
    subscriptions.map((subscription) => [subscription.event_type, subscription]),
  )
  const timestamp = new Date().toISOString()

  return MACRO_EVENT_TYPES.map(
    (eventType) =>
      byType.get(eventType) ?? {
        id: `default-${eventType}`,
        user_id: userId,
        event_type: eventType,
        subscribed: false,
        impact_filter: 'HIGH',
        timing: '1D',
        one_time: true,
        created_at: timestamp,
        updated_at: timestamp,
      },
  )
}

export function toUiMacroEvent(event: EconomicEvent): MacroEvent | null {
  const eventType = toUiEventType(event.event_type)
  if (!eventType) {
    return null
  }

  return {
    id: String(event.id),
    event_id: String(event.id),
    event_type: eventType,
    event_name: event.event_name,
    description: event.description,
    scheduled_at: event.event_date,
    timezone: 'UTC',
    impact: toUiImpact(event.impact_level),
    subscribed: false,
    notified: false,
  }
}
