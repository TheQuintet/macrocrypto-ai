import { apiUrl } from '@/lib/apiConfig'
import { simulateEconomicCalendar } from '@/api/economicCalendar/simulatedEconomicCalendar'
import type {
  EconomicCalendarResponse,
  EconomicEvent,
} from '@/types/economicCalendar'

/** Real endpoint on the data service (see `app/api/economic_calendar.py`). */
export const ECONOMIC_CALENDAR_PATH = '/api/v1/economic-calendar'

export function economicCalendarQueryKey() {
  return ['economicCalendar', 'events'] as const
}

/**
 * Events from the data service.
 *
 * The endpoint takes `event_type` and `impact_level` filters, but the grid
 * needs the whole period regardless of what is filtered — so this fetches once
 * and the filtering happens client-side, which also makes the filters
 * instant. It has no date-range parameter either, so this is the full feed.
 *
 * Dates are requested in UTC (the endpoint's default) and converted for
 * display with `Intl`, so the timezone is applied in exactly one place rather
 * than once on the wire and again in the UI.
 *
 * With no backend configured the app runs on simulated events so it still
 * works standalone. When a backend *is* configured a failed request throws
 * rather than quietly substituting a fake schedule.
 */
export async function fetchEconomicCalendar(): Promise<EconomicEvent[]> {
  const url = apiUrl(ECONOMIC_CALENDAR_PATH)

  if (!url) {
    return simulateEconomicCalendar()
  }

  const response = await fetch(url, {
    headers: { Accept: 'application/json' },
  })

  if (!response.ok) {
    throw new Error(
      `Economic calendar request failed with ${response.status}`,
    )
  }

  const data: EconomicCalendarResponse = await response.json()

  return (data.events ?? []).map((event) => ({
    ...event,
    dataSource: 'live' as const,
  }))
}
