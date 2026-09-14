import { parseInstant } from '@/lib/economicCalendarGrid'
import { formatEventTypeLabel } from '@/lib/economicEventFilters'
import { isWithinDateRange, matchesSearch } from '@/lib/tableFilters'
import type { DateRange } from '@/lib/tableFilters'
import type { EconomicEvent } from '@/types/economicCalendar'

/**
 * Releases that have already happened, most recent first.
 *
 * An event whose date cannot be read is left out rather than guessed into one
 * side or the other — the calendar grid already surfaces those separately.
 */
export function pastEvents(
  events: EconomicEvent[],
  now: Date = new Date(),
): EconomicEvent[] {
  return events
    .filter((event) => {
      const instant = parseInstant(event.event_date)

      return instant ? instant.getTime() < now.getTime() : false
    })
    .sort((a, b) => b.event_date.localeCompare(a.event_date))
}

/** Free text plus an inclusive range over the event's own date. */
export type EventHistoryQuery = {
  search: string
  dateRange: DateRange
}

export function searchEventHistory(
  events: EconomicEvent[],
  { search, dateRange }: EventHistoryQuery,
  timeZone: string,
): EconomicEvent[] {
  return events.filter(
    (event) =>
      isWithinDateRange(event.event_date, dateRange, timeZone) &&
      matchesSearch(search, [
        event.event_name,
        formatEventTypeLabel(event.event_type),
        event.description,
      ]),
  )
}
