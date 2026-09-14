import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { EventImpactBadge } from '@/components/calendar/EventImpactBadge';
import { formatEventDateTime } from '@/lib/economicCalendarGrid';
import { formatAlertTiming } from '@/lib/alerts/macroAlertHistoryFilters';
import { formatEventTypeLabel } from '@/lib/economicEventFilters';
import type { MacroAlertHistoryEntry } from '@/types/alerts/macroAlertHistory';

type MacroAlertHistoryTableProps = {
  entries: MacroAlertHistoryEntry[];
  /** IANA zone every date in the table is rendered in. */
  timeZone: string;
};

function formatOrMissing(value: string | null, timeZone: string): string {
  return value ? formatEventDateTime(value, timeZone) : 'Date unavailable';
}

/**
 * Sent macro alerts, newest first.
 *
 * The type and impact columns drop out below `sm` — their information is
 * already in the event name and the row stays readable on a phone without
 * pushing the table into a horizontal scroll.
 */
export function MacroAlertHistoryTable({
  entries,
  timeZone,
}: MacroAlertHistoryTableProps) {
  return (
    <div className="overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Event</TableHead>
            <TableHead className="hidden sm:table-cell">Type</TableHead>
            <TableHead className="hidden sm:table-cell">Impact</TableHead>
            <TableHead>Alert timing</TableHead>
            <TableHead className="hidden md:table-cell">Event date</TableHead>
            <TableHead>Sent</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {entries.map((entry) => (
            <TableRow key={entry.id}>
              <TableCell className="font-medium">
                {entry.event_name}
              </TableCell>
              <TableCell className="hidden sm:table-cell">
                {formatEventTypeLabel(entry.event_type)}
              </TableCell>
              <TableCell className="hidden sm:table-cell">
                <EventImpactBadge impact={entry.impact} size="sm" />
              </TableCell>
              <TableCell className="text-sm">
                {formatAlertTiming(entry.timing)}
              </TableCell>
              <TableCell className="hidden text-sm text-muted-foreground md:table-cell">
                {formatOrMissing(entry.event_date, timeZone)}
              </TableCell>
              <TableCell className="text-sm text-muted-foreground">
                {formatOrMissing(entry.sent_at, timeZone)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
