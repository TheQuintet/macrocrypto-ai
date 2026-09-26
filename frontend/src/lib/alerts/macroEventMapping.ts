import type {
  EventImpact,
  EventTiming,
  EventType,
  MacroAlertDraft,
  MacroSubscription,
  MacroSubscriptionWrite,
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

export function toApiTiming(timing: EventTiming) {
  return timing.toLowerCase()
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
  notify_in_app?: boolean
  notify_email?: boolean
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
    notify_in_app: payload.notify_in_app ?? null,
    notify_email: payload.notify_email ?? null,
    created_at: payload.created_at ?? null,
    updated_at: payload.updated_at ?? null,
  }
}

export function subscriptionToWrite(
  subscription: MacroSubscription,
  subscribed: boolean,
): MacroSubscriptionWrite {
  return {
    event_type: subscription.event_type,
    subscribed,
    timing: subscription.timing ?? '1D',
    one_time: subscription.one_time ?? true,
    notify_in_app: subscription.notify_in_app ?? true,
    notify_email: subscription.notify_email ?? false,
  }
}

export function draftToWrite(draft: MacroAlertDraft): MacroSubscriptionWrite {
  return {
    event_type: draft.event_type,
    subscribed: true,
    timing: draft.timing,
    one_time: draft.one_time,
    notify_in_app: draft.notify_in_app,
    notify_email: draft.notify_email,
  }
}
