import type {
  EconomicEventType,
  EventImpactLevel,
  EventTypeFilter,
} from '@/types/economicCalendar';
import type { DateRange } from '@/lib/tableFilters';

/** How far ahead of the event the alert was sent (alert-service `timing`). */
export type MacroAlertTiming = '1d' | '12h' | '1h';

/**
 * One alert the engine actually sent, from
 * GET /api/v1/macro/notifications/{user_id} on the alert service.
 *
 * `event_type`, `impact`, and `timing` are plain strings on the wire rather
 * than enums, so the UI widens them and falls back gracefully instead of
 * assuming the feed only ever sends values it knows.
 */
export type MacroAlertHistoryEntry = {
  id: string;
  user_id: string;
  alert_id: string | null;
  event_name: string;
  event_type: EconomicEventType | string;
  /** When the event itself takes place. */
  event_date: string | null;
  timing: MacroAlertTiming | string;
  impact: EventImpactLevel | string;
  description: string | null;
  read: boolean;
  /** When the alert was sent. */
  sent_at: string | null;
};

/** Response body of GET /api/v1/macro/notifications/{user_id}. */
export type MacroAlertHistoryResponse = {
  total: number;
  limit: number;
  offset: number;
  notifications: MacroAlertHistoryEntry[];
};

/** Everything the history view narrows by. */
export type MacroAlertHistoryFilters = {
  search: string;
  eventType: EventTypeFilter;
  dateRange: DateRange;
};
