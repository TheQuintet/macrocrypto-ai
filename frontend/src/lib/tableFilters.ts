import { dayKeyInTimezone, parseInstant } from '@/lib/economicCalendarGrid';

/** Inclusive `YYYY-MM-DD` bounds, as produced by a native date input. */
export type DateRange = {
  start: string;
  end: string;
};

export const EMPTY_DATE_RANGE: DateRange = { start: '', end: '' };

/**
 * Whether an instant falls inside an inclusive day range, judged in the zone
 * the rows are displayed in.
 *
 * The zone matters: a row that reads "3 March" to the reader must not be
 * filtered out by a range starting on 3 March just because it is still
 * 2 March in UTC.
 *
 * A row whose date cannot be read is kept while no range is set, and dropped
 * once one is — an unreadable date cannot be shown to be inside it.
 */
export function isWithinDateRange(
  isoInstant: string | null | undefined,
  { start, end }: DateRange,
  timeZone: string,
): boolean {
  if (!start && !end) {
    return true;
  }

  const instant = isoInstant ? parseInstant(isoInstant) : null;
  if (!instant) {
    return false;
  }

  const day = dayKeyInTimezone(instant, timeZone);

  return (!start || day >= start) && (!end || day <= end);
}

/** Case-insensitive substring match across several fields. Blank query matches all. */
export function matchesSearch(
  query: string,
  fields: (string | null | undefined)[],
): boolean {
  const needle = query.trim().toLowerCase();
  if (!needle) {
    return true;
  }

  return fields.some((field) => field?.toLowerCase().includes(needle));
}

/** Always at least one page, so an empty table still reads as "page 1 of 1". */
export function pageCount(total: number, pageSize: number): number {
  if (pageSize <= 0) {
    return 1;
  }

  return Math.max(1, Math.ceil(total / pageSize));
}

export function clampPage(page: number, totalPages: number): number {
  return Math.min(Math.max(page, 1), Math.max(totalPages, 1));
}

/**
 * One page of rows. The page is clamped rather than trusted, so filtering down
 * to fewer pages while on the last one shows rows instead of a blank table.
 */
export function paginate<T>(rows: T[], page: number, pageSize: number): T[] {
  const safePage = clampPage(page, pageCount(rows.length, pageSize));
  const start = (safePage - 1) * pageSize;

  return rows.slice(start, start + pageSize);
}

function escapeCsvField(value: string): string {
  return `"${value.replace(/"/g, '""')}"`;
}

/**
 * RFC 4180-style CSV. Every field is quoted, so commas, quotes, and newlines
 * inside an event name cannot shift the columns.
 */
export function toCsv(headers: string[], rows: string[][]): string {
  return [headers, ...rows]
    .map((row) => row.map(escapeCsvField).join(','))
    .join('\r\n');
}
