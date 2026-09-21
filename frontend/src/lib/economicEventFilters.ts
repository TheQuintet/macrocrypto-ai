import type { MacroEventSubscription } from '@/types/alerts/macroSubscription'
import type {
  EconomicEvent,
  EconomicEventType,
  EventImpactLevel,
  EventTypeFilter,
  ImpactLevelFilter,
} from '@/types/economicCalendar'

/**
 * Impact ranking, mirroring `impact_priority` in `MacroAlertEngine`. A
 * subscription's `impact_filter` is a *floor*, not an exact match: `low`
 * receives everything, `high` only high-impact events.
 */
const IMPACT_PRIORITY: Record<EventImpactLevel, number> = {
  low: 1,
  medium: 2,
  high: 3,
}

export type EconomicEventFilters = {
  eventType: EventTypeFilter
  impactLevel: ImpactLevelFilter
}

/** Narrow the feed to the chosen category and impact level. */
export function filterEconomicEvents(
  events: EconomicEvent[],
  { eventType, impactLevel }: EconomicEventFilters,
): EconomicEvent[] {
  return events.filter((event) => {
    const typeMatches = eventType === 'all' || event.event_type === eventType
    const impactMatches =
      impactLevel === 'all' || event.impact_level === impactLevel

    return typeMatches && impactMatches
  })
}

/**
 * Index a user's subscriptions by category, keeping only the ones actually
 * switched on. A row with `subscribed: false` is a record of an unsubscribe,
 * not a live subscription.
 */
export function activeSubscriptionsByType(
  subscriptions: MacroEventSubscription[],
): Map<EconomicEventType, MacroEventSubscription> {
  const byType = new Map<EconomicEventType, MacroEventSubscription>()

  for (const subscription of subscriptions) {
    if (subscription.subscribed) {
      byType.set(subscription.event_type, subscription)
    }
  }

  return byType
}

/**
 * Whether this event would actually alert the user — the event's category is
 * subscribed *and* its impact clears that subscription's floor. Anything
 * looser would badge events the alert engine will never send.
 */
export function isEventSubscribed(
  event: EconomicEvent,
  subscriptionsByType: Map<EconomicEventType, MacroEventSubscription>,
): boolean {
  const subscription = subscriptionsByType.get(event.event_type)
  if (!subscription) {
    return false
  }

  const floor = IMPACT_PRIORITY[subscription.impact_filter]
  const impact = IMPACT_PRIORITY[event.impact_level]
  if (floor === undefined || impact === undefined) {
    return false
  }

  return floor <= impact
}
