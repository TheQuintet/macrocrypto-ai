import type {
  CalendarDay,
  CalendarGrid,
  CalendarTimezoneMode,
  CalendarViewMode,
  CalendarWeek,
  EconomicEvent,
} from '@/types/economicCalendar'

/** Rows start on Sunday, the way economic calendars are usually printed. */
const WEEK_START_DAY = 0
const DAYS_IN_WEEK = 7

/**
 * The IANA zone events are rendered in.
 *
 * `local` resolves the reader's own zone so the grid, the times, and "today"
 * all agree. A runtime with no resolvable zone falls back to UTC rather than
 * guessing an offset.
 */
export function displayTimezone(mode: CalendarTimezoneMode): string {
  if (mode === 'utc') {
    return 'UTC'
  }

  return Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC'
}

/**
 * Civil dates (the cells of the grid) are held as UTC-midnight `Date`s, so
 * stepping between days, weeks, and months never lands in a DST gap. The
 * display timezone is applied only where an *instant* is involved — bucketing
 * an event, formatting a time, resolving "today".
 */
function civilDate(year: number, monthIndex: number, day: number): Date {
  return new Date(Date.UTC(year, monthIndex, day))
}

/** `YYYY-MM-DD` for a civil date. */
export function dayKey(date: Date): string {
  return date.toISOString().slice(0, 10)
}

/** Inverse of {@link dayKey}. */
export function civilDateFromKey(key: string): Date {
  const [year, month, day] = key.split('-').map(Number)
  return civilDate(year, month - 1, day)
}

function addDays(date: Date, days: number): Date {
  return civilDate(
    date.getUTCFullYear(),
    date.getUTCMonth(),
    date.getUTCDate() + days,
  )
}

/** The day of the month is not preserved — month anchors are always the 1st. */
export function addMonths(date: Date, months: number): Date {
  return civilDate(date.getUTCFullYear(), date.getUTCMonth() + months, 1)
}

export function addWeeks(date: Date, weeks: number): Date {
  return addDays(date, weeks * DAYS_IN_WEEK)
}

export function startOfMonth(date: Date): Date {
  return civilDate(date.getUTCFullYear(), date.getUTCMonth(), 1)
}

export function startOfWeek(date: Date): Date {
  const offset =
    (date.getUTCDay() - WEEK_START_DAY + DAYS_IN_WEEK) % DAYS_IN_WEEK
  return addDays(date, -offset)
}

/** Day 0 of the next month is the last day of this one. */
function daysInMonth(monthStart: Date): number {
  return civilDate(
    monthStart.getUTCFullYear(),
    monthStart.getUTCMonth() + 1,
    0,
  ).getUTCDate()
}

/** Step the anchor one period in either direction. */
export function shiftAnchor(
  anchor: Date,
  view: CalendarViewMode,
  delta: number,
): Date {
  return view === 'month'
    ? addMonths(anchor, delta)
    : addWeeks(startOfWeek(anchor), delta)
}

/** The anchor that brings `instant` into view, as seen from `timeZone`. */
export function anchorForInstant(
  instant: Date,
  view: CalendarViewMode,
  timeZone: string,
): Date {
  const today = civilDateFromKey(dayKeyInTimezone(instant, timeZone))
  return view === 'month' ? startOfMonth(today) : startOfWeek(today)
}

const dayKeyFormatters = new Map<string, Intl.DateTimeFormat>()

function dayKeyFormatter(timeZone: string): Intl.DateTimeFormat {
  const cached = dayKeyFormatters.get(timeZone)
  if (cached) {
    return cached
  }

  const formatter = new Intl.DateTimeFormat('en-CA', {
    timeZone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  })
  dayKeyFormatters.set(timeZone, formatter)
  return formatter
}

/** Which calendar day an instant falls on, as seen from `timeZone`. */
export function dayKeyInTimezone(instant: Date, timeZone: string): string {
  const parts = dayKeyFormatter(timeZone).formatToParts(instant)
  const part = (type: Intl.DateTimeFormatPartTypes) =>
    parts.find((candidate) => candidate.type === type)?.value ?? ''

  return `${part('year')}-${part('month')}-${part('day')}`
}

/** `null` for a date the feed sent in a shape we cannot read. */
export function parseInstant(value: string): Date | null {
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? null : parsed
}

/** Clock time of an event in the display timezone, 24-hour. */
export function formatEventTime(isoInstant: string, timeZone: string): string {
  const instant = parseInstant(isoInstant)
  if (!instant) {
    return '--:--'
  }

  return new Intl.DateTimeFormat('en-GB', {
    timeZone,
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
  }).format(instant)
}

/** Full date, time, and zone — for the event detail panel. */
export function formatEventDateTime(
  isoInstant: string,
  timeZone: string,
): string {
  const instant = parseInstant(isoInstant)
  if (!instant) {
    return 'Date unavailable'
  }

  return new Intl.DateTimeFormat('en-GB', {
    timeZone,
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
    timeZoneName: 'short',
  }).format(instant)
}

/** Heading for one day, e.g. `Mon 2 Mar`. */
export function formatDayHeading(key: string): string {
  return new Intl.DateTimeFormat('en-GB', {
    timeZone: 'UTC',
    weekday: 'short',
    day: 'numeric',
    month: 'short',
  }).format(civilDateFromKey(key))
}

/** Column headings, Sunday first. */
export function weekdayLabels(): string[] {
  const formatter = new Intl.DateTimeFormat('en-GB', {
    timeZone: 'UTC',
    weekday: 'short',
  })

  // 2024-01-07 was a Sunday, so this walks one full week from the start day.
  return Array.from({ length: DAYS_IN_WEEK }, (_, index) =>
    formatter.format(civilDate(2024, 0, 7 + index)),
  )
}

function formatMonthLabel(anchor: Date): string {
  return new Intl.DateTimeFormat('en-GB', {
    timeZone: 'UTC',
    month: 'long',
    year: 'numeric',
  }).format(anchor)
}

function formatWeekLabel(start: Date): string {
  const end = addDays(start, DAYS_IN_WEEK - 1)
  const dayMonth = new Intl.DateTimeFormat('en-GB', {
    timeZone: 'UTC',
    day: 'numeric',
    month: 'short',
  })

  if (start.getUTCFullYear() !== end.getUTCFullYear()) {
    return `${dayMonth.format(start)} ${start.getUTCFullYear()} – ${dayMonth.format(end)} ${end.getUTCFullYear()}`
  }

  return `${dayMonth.format(start)} – ${dayMonth.format(end)} ${end.getUTCFullYear()}`
}

/** Human label for the visible period. */
export function calendarRangeLabel(
  anchor: Date,
  view: CalendarViewMode,
): string {
  return view === 'month'
    ? formatMonthLabel(startOfMonth(anchor))
    : formatWeekLabel(startOfWeek(anchor))
}

type GroupedEvents = {
  byDay: Map<string, EconomicEvent[]>
  undated: EconomicEvent[]
}

/** Bucket events by the day they fall on in `timeZone`, earliest first. */
function groupEventsByDay(
  events: EconomicEvent[],
  timeZone: string,
): GroupedEvents {
  const byDay = new Map<string, EconomicEvent[]>()
  const undated: EconomicEvent[] = []

  for (const event of events) {
    const instant = parseInstant(event.event_date)
    if (!instant) {
      undated.push(event)
      continue
    }

    const key = dayKeyInTimezone(instant, timeZone)
    const bucket = byDay.get(key)
    if (bucket) {
      bucket.push(event)
    } else {
      byDay.set(key, [event])
    }
  }

  for (const bucket of byDay.values()) {
    bucket.sort((a, b) => a.event_date.localeCompare(b.event_date))
  }

  return { byDay, undated }
}

type BuildCalendarGridOptions = {
  anchor: Date
  view: CalendarViewMode
  events: EconomicEvent[]
  timeZone: string
  /** Injectable so tests can pin "today" without faking timers. */
  now?: Date
}

/**
 * Lay out one visible period.
 *
 * A month renders whole weeks, padded with the neighbouring months' days so
 * every row has seven cells — and only as many rows as that month needs, so
 * February starting on a Sunday does not trail an empty week.
 */
export function buildCalendarGrid({
  anchor,
  view,
  events,
  timeZone,
  now = new Date(),
}: BuildCalendarGridOptions): CalendarGrid {
  const { byDay, undated } = groupEventsByDay(events, timeZone)
  const todayKey = dayKeyInTimezone(now, timeZone)

  const monthStart = startOfMonth(anchor)
  const gridStart =
    view === 'month' ? startOfWeek(monthStart) : startOfWeek(anchor)

  const leadingDays =
    (monthStart.getUTCDay() - WEEK_START_DAY + DAYS_IN_WEEK) % DAYS_IN_WEEK
  const cellCount =
    view === 'week'
      ? DAYS_IN_WEEK
      : Math.ceil((leadingDays + daysInMonth(monthStart)) / DAYS_IN_WEEK) *
        DAYS_IN_WEEK

  const days: CalendarDay[] = Array.from({ length: cellCount }, (_, index) => {
    const date = addDays(gridStart, index)
    const key = dayKey(date)

    return {
      key,
      dayOfMonth: date.getUTCDate(),
      isCurrentPeriod:
        view === 'week' || date.getUTCMonth() === monthStart.getUTCMonth(),
      isToday: key === todayKey,
      events: byDay.get(key) ?? [],
    }
  })

  const weeks: CalendarWeek[] = []
  for (let index = 0; index < days.length; index += DAYS_IN_WEEK) {
    const weekDays = days.slice(index, index + DAYS_IN_WEEK)
    weeks.push({ key: weekDays[0].key, days: weekDays })
  }

  return {
    weeks,
    days,
    undated,
    label: calendarRangeLabel(anchor, view),
  }
}

/**
 * Releases that land on a cell of the current period, in the order the
 * grid already bucketed them. Padding days from the neighbouring month
 * stay off the list so both layouts show the same window.
 */
export function eventsInCurrentPeriod(grid: CalendarGrid): EconomicEvent[] {
  return grid.days
    .filter((day) => day.isCurrentPeriod)
    .flatMap((day) => day.events)
}
