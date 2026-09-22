import { EventImpactBadge } from '@/components/calendar/EventImpactBadge'
import { SubscriptionStatusBadge } from '@/components/calendar/SubscriptionStatusBadge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { formatEventDateTime } from '@/lib/economicCalendarGrid'
import { formatEventTypeLabel } from '@/lib/economicEventFilters'
import type { EconomicEvent } from '@/types/economicCalendar'

type EconomicEventListProps = {
  events: EconomicEvent[]
  periodLabel: string
  timeZone: string
  isSubscribed: (event: EconomicEvent) => boolean | null
  onSelectEvent: (event: EconomicEvent) => void
}

/** Same period as the grid, as a date-sorted table. */
export function EconomicEventList({
  events,
  periodLabel,
  timeZone,
  isSubscribed,
  onSelectEvent,
}: EconomicEventListProps) {
  if (events.length === 0) {
    return (
      <p className="rounded-lg border border-border bg-card px-3 py-6 text-center text-sm text-muted-foreground">
        No events in {periodLabel}.
      </p>
    )
  }

  return (
    <div
      className="overflow-hidden rounded-lg border border-border bg-card"
      aria-label={`Economic calendar list, ${periodLabel}`}
    >
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>When</TableHead>
            <TableHead>Event</TableHead>
            <TableHead className="hidden sm:table-cell">Type</TableHead>
            <TableHead className="hidden sm:table-cell">Impact</TableHead>
            <TableHead className="hidden md:table-cell">Alerts</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {events.map((event) => (
            <TableRow key={event.id}>
              <TableCell className="whitespace-nowrap text-muted-foreground">
                {formatEventDateTime(event.event_date, timeZone)}
              </TableCell>
              <TableCell>
                <button
                  type="button"
                  className="text-left font-medium hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  onClick={() => onSelectEvent(event)}
                >
                  {event.event_name}
                </button>
              </TableCell>
              <TableCell className="hidden sm:table-cell">
                {formatEventTypeLabel(event.event_type)}
              </TableCell>
              <TableCell className="hidden sm:table-cell">
                <EventImpactBadge impact={event.impact_level} size="sm" />
              </TableCell>
              <TableCell className="hidden md:table-cell">
                <SubscriptionStatusBadge subscribed={isSubscribed(event)} />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
