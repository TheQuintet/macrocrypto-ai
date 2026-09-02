import type {
  EconomicEventType,
  EventImpactLevel,
} from '@/types/economicCalendar'

/**
 * A user's standing subscription to one macro event category, from
 * GET /api/v1/macro/subscriptions/{user_id} on the alert service.
 */
export type MacroEventSubscription = {
  id: string
  user_id: string
  event_type: EconomicEventType
  subscribed: boolean
  /**
   * Lowest impact that still alerts — a floor, not an exact match. `low`
   * receives every event, `high` only high-impact ones. Mirrors
   * `MacroAlertEngine._impact_matches`.
   */
  impact_filter: EventImpactLevel
  created_at: string | null
  updated_at: string | null
}

/** Response body of GET /api/v1/macro/subscriptions/{user_id}. */
export type MacroSubscriptionsResponse = {
  user_id: string
  subscriptions: MacroEventSubscription[]
}
