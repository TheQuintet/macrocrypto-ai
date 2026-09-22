export type EventType = 'FED' | 'CPI' | 'GDP' | 'EMPLOYMENT';
export type EventImpact = 'HIGH' | 'MEDIUM' | 'LOW';
export type EventTiming = '1D' | '12H' | '1H';

/**
 * One row of GET /api/v1/macro/subscriptions/{user_id}.
 *
 * `timing` and `one_time` are `null` because the alert service does not
 * persist them yet — it stores only event type, subscribed, and impact filter.
 */
export interface MacroSubscription {
  id: string;
  user_id: string;
  event_type: EventType;
  subscribed: boolean;
  impact_filter: EventImpact | null;
  timing: EventTiming | null;
  one_time: boolean | null;
  created_at: string | null;
  updated_at: string | null;
}

/** Status filter applied to the macro event list, mirroring price alerts. */
export type MacroEventStatusFilter = 'all' | 'active' | 'inactive';

/** Values captured by the macro alert form before a subscription is saved. */
export interface MacroAlertDraft {
  event_type: EventType;
  timing: EventTiming;
  one_time: boolean;
  notify_in_app: boolean;
  notify_email: boolean;
}