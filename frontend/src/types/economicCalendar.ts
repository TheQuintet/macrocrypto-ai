/**
 * Where calendar events came from. Simulated events must be labelled in the UI
 * the same way macro indicators and BTC snapshots are.
 */
export type EconomicEventDataSource = 'live' | 'simulated'

/**
 * Event categories shared by data-service (`VALID_EVENT_TYPES`) and
 * alert-service (`MacroSubscriptionCreate.event_type`).
 *
 * Only alert-service accepts `other`, so an event never carries it — but a
 * subscription can, which is why it lives on the shared union.
 */
export type EconomicEventType =
  | 'fed'
  | 'cpi'
  | 'employment'
  | 'gdp'
  | 'other'

/** Expected market impact of an event. */
export type EventImpactLevel = 'high' | 'medium' | 'low'

/** One event as it arrives from GET /api/v1/economic-calendar. */
export type EconomicEventPayload = {
  id: number
  event_name: string
  event_type: EconomicEventType
  /** ISO-8601 instant. Requested in UTC; the display timezone is applied client-side. */
  event_date: string
  impact_level: EventImpactLevel
  description: string
}

/** An event once the fetcher has recorded where it came from. */
export type EconomicEvent = EconomicEventPayload & {
  /** Live API vs frontend stand-in — set by the fetcher, not the UI. */
  dataSource: EconomicEventDataSource
}

/** Response body of GET /api/v1/economic-calendar. */
export type EconomicCalendarResponse = {
  count: number
  events: EconomicEventPayload[]
}

/** Month grid or single week. */
export type CalendarViewMode = 'month' | 'week'

/** Grid (month/week) or a flat table of the same period. */
export type CalendarLayout = 'calendar' | 'list'

/** Render events in the reader's own IANA zone, or in UTC. */
export type CalendarTimezoneMode = 'local' | 'utc'

/** `'all'` keeps every category; otherwise only that one. */
export type EventTypeFilter = 'all' | EconomicEventType

/** `'all'` keeps every impact level; otherwise only that one. */
export type ImpactLevelFilter = 'all' | EventImpactLevel

/** One cell of the grid, already bucketed into the display timezone. */
export type CalendarDay = {
  /** `YYYY-MM-DD` in the display timezone — also the bucketing key. */
  key: string
  dayOfMonth: number
  /** False for the leading/trailing days that pad a month grid. */
  isCurrentPeriod: boolean
  isToday: boolean
  events: EconomicEvent[]
}

/** A row of the grid — always seven days, Sunday first. */
export type CalendarWeek = {
  key: string
  days: CalendarDay[]
}

/** Everything the grid needs for one visible period. */
export type CalendarGrid = {
  weeks: CalendarWeek[]
  /** Flattened cells, for the mobile agenda that shares this bucketing. */
  days: CalendarDay[]
  /**
   * Events whose `event_date` could not be parsed, so they belong to no cell.
   * Surfaced rather than dropped silently — an empty grid should never be the
   * only sign that the feed sent something unreadable.
   */
  undated: EconomicEvent[]
  /** Human range, e.g. `March 2026` or `Mar 2 – Mar 8, 2026`. */
  label: string
}
