import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { EventImpactBadge } from '@/components/calendar/EventImpactBadge'
import { formatEventDateTime } from '@/lib/economicCalendarGrid'
import { formatEventTypeLabel } from '@/lib/economicEventFilters'
import type { EconomicEvent } from '@/types/economicCalendar'

type EventHistoryTableProps = {
  events: EconomicEvent[]
  timeZone: string
  onSelectEvent: (event: EconomicEvent) => void
}

/**
 * Past releases, most recent first.
 *
 * The type column drops out below `sm`; impact stays, since it is the reason
 * most readers are scanning the list at all.
 */
export function EventHistoryTable({
  events,
  timeZone,
  onSelectEvent,
}: EventHistoryTableProps) {
  return (
    <div className="overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Event</TableHead>
            <TableHead className="hidden sm:table-cell">Type</TableHead>
            <TableHead>Impact</TableHead>
            <TableHead>Date</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {events.map((event) => (
            <TableRow key={event.id}>
              <TableCell className="font-medium">
                <button
                  type="button"
                  onClick={() => onSelectEvent(event)}
                  className="touch-manipulation text-left underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                >
                  {event.event_name}
                </button>
              </TableCell>
              <TableCell className="hidden sm:table-cell">
                {formatEventTypeLabel(event.event_type)}
              </TableCell>
              <TableCell>
                <EventImpactBadge impact={event.impact_level} size="sm" />
              </TableCell>
              <TableCell className="text-sm text-muted-foreground">
                {formatEventDateTime(event.event_date, timeZone)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
