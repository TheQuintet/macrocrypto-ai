import type {
  EventImpact,
  EventTiming,
  EventType,
  MacroSubscription,
} from '@/types/alerts/macroAlert'

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

export function toUiImpact(value: string | null | undefined): EventImpact | null {
  const normalized = value?.toUpperCase()
  if (normalized && IMPACT_SET.has(normalized)) {
    return normalized as EventImpact
  }
  return null
}

export function toUiTiming(value: string | null | undefined): EventTiming | null {
  const normalized = value?.toUpperCase()
  if (normalized && TIMING_SET.has(normalized)) {
    return normalized as EventTiming
  }
  return null
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

/**
 * Maps one subscription record as the alert service returns it. Fields the
 * service does not send stay `null` rather than being invented here.
 */
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
    one_time: payload.one_time ?? null,
    created_at: payload.created_at ?? null,
    updated_at: payload.updated_at ?? null,
  }
}
