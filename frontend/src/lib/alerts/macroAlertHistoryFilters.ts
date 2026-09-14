import { formatEventDateTime } from '@/lib/economicCalendarGrid';
import { formatEventTypeLabel } from '@/lib/economicEventFilters';
import {
  isWithinDateRange,
  matchesSearch,
  toCsv,
} from '@/lib/tableFilters';
import type {
  MacroAlertHistoryEntry,
  MacroAlertHistoryFilters,
  MacroAlertTiming,
} from '@/types/alerts/macroAlertHistory';

const TIMING_LABELS: Record<MacroAlertTiming, string> = {
  '1d': '1 day before',
  '12h': '12 hours before',
  '1h': '1 hour before',
};

/** Falls back to the raw value for a lead time the backend added later. */
export function formatAlertTiming(timing: string): string {
  return TIMING_LABELS[timing as MacroAlertTiming] ?? timing;
}

/** Most recently sent first; entries with no sent date sink to the bottom. */
export function sortMacroAlertHistory(
  entries: MacroAlertHistoryEntry[],
): MacroAlertHistoryEntry[] {
  return [...entries].sort((a, b) => {
    if (!a.sent_at) return 1;
    if (!b.sent_at) return -1;

    return b.sent_at.localeCompare(a.sent_at);
  });
}

/**
 * Narrow the history to what the reader asked for.
 *
 * The date range applies to when the alert was *sent*, which is what the
 * reader is looking back over — not when the event itself happened.
 */
export function filterMacroAlertHistory(
  entries: MacroAlertHistoryEntry[],
  { search, eventType, dateRange }: MacroAlertHistoryFilters,
  timeZone: string,
): MacroAlertHistoryEntry[] {
  return entries.filter((entry) => {
    if (eventType !== 'all' && entry.event_type !== eventType) {
      return false;
    }

    if (!isWithinDateRange(entry.sent_at, dateRange, timeZone)) {
      return false;
    }

    return matchesSearch(search, [
      entry.event_name,
      formatEventTypeLabel(entry.event_type),
      entry.description,
    ]);
  });
}

const CSV_HEADERS = [
  'Event',
  'Event type',
  'Event date',
  'Impact',
  'Alert timing',
  'Sent',
];

/** Exported rows read exactly as they do on screen, including the timezone. */
export function macroAlertHistoryToCsv(
  entries: MacroAlertHistoryEntry[],
  timeZone: string,
): string {
  const rows = entries.map((entry) => [
    entry.event_name,
    formatEventTypeLabel(entry.event_type),
    entry.event_date
      ? formatEventDateTime(entry.event_date, timeZone)
      : 'Date unavailable',
    entry.impact,
    formatAlertTiming(entry.timing),
    entry.sent_at
      ? formatEventDateTime(entry.sent_at, timeZone)
      : 'Date unavailable',
  ]);

  return toCsv(CSV_HEADERS, rows);
}
