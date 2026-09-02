import { describe, expect, it } from 'vitest'
import { makeEconomicEvent } from '@/api/economicCalendar/economicCalendar.testHelpers'
import {
  anchorForInstant,
  buildCalendarGrid,
  calendarRangeLabel,
  civilDateFromKey,
  dayKeyInTimezone,
  displayTimezone,
  formatEventDateTime,
  formatEventTime,
  parseInstant,
  shiftAnchor,
  startOfWeek,
  weekdayLabels,
} from '@/lib/economicCalendarGrid'

const NEW_YORK = 'America/New_York'

function gridFor(
  anchorKey: string,
  options: Partial<Parameters<typeof buildCalendarGrid>[0]> = {},
) {
  return buildCalendarGrid({
    anchor: civilDateFromKey(anchorKey),
    view: 'month',
    events: [],
    timeZone: 'UTC',
    now: new Date('2026-03-18T12:00:00.000Z'),
    ...options,
  })
}

describe('buildCalendarGrid', () => {
  it('pads a month to whole weeks starting on Sunday', () => {
    // March 2026 starts on a Sunday and needs five rows for its 31 days.
    const grid = gridFor('2026-03-01')

    expect(grid.weeks).toHaveLength(5)
    expect(grid.days).toHaveLength(35)
    expect(grid.days[0].key).toBe('2026-03-01')
    expect(grid.days[34].key).toBe('2026-04-04')
  })

  it('does not trail an empty week when a month fits exactly', () => {
    // February 2026 is a Sunday-start 28-day month — exactly four rows.
    const grid = gridFor('2026-02-01')

    expect(grid.weeks).toHaveLength(4)
    expect(grid.days.at(-1)?.key).toBe('2026-02-28')
  })

  it('marks padding days as outside the month', () => {
    const grid = gridFor('2026-04-01')

    const padding = grid.days.filter((day) => !day.isCurrentPeriod)
    expect(padding.length).toBeGreaterThan(0)
    expect(padding.every((day) => !day.key.startsWith('2026-04'))).toBe(true)
  })

  it('renders a single Sunday-aligned week in week view', () => {
    const grid = gridFor('2026-03-18', { view: 'week' })

    expect(grid.days).toHaveLength(7)
    expect(grid.days[0].key).toBe('2026-03-15')
    expect(grid.days[6].key).toBe('2026-03-21')
    expect(grid.days.every((day) => day.isCurrentPeriod)).toBe(true)
  })

  it('marks today in the display timezone', () => {
    const grid = gridFor('2026-03-01', {
      now: new Date('2026-03-18T12:00:00.000Z'),
    })

    expect(grid.days.filter((day) => day.isToday).map((day) => day.key)).toEqual(
      ['2026-03-18'],
    )
  })

  it('buckets an event into the day it falls on in the display timezone', () => {
    // 00:30 UTC on the 2nd is still the evening of the 1st in New York.
    const event = makeEconomicEvent({
      event_date: '2026-03-02T00:30:00.000Z',
    })

    const utcGrid = gridFor('2026-03-01', { events: [event] })
    const newYorkGrid = gridFor('2026-03-01', {
      events: [event],
      timeZone: NEW_YORK,
    })

    expect(
      utcGrid.days.find((day) => day.key === '2026-03-02')?.events,
    ).toHaveLength(1)
    expect(
      newYorkGrid.days.find((day) => day.key === '2026-03-01')?.events,
    ).toHaveLength(1)
    expect(
      newYorkGrid.days.find((day) => day.key === '2026-03-02')?.events,
    ).toHaveLength(0)
  })

  it('orders events within a day by release time', () => {
    const grid = gridFor('2026-03-01', {
      events: [
        makeEconomicEvent({
          event_name: 'Later',
          event_date: '2026-03-12T19:00:00.000Z',
        }),
        makeEconomicEvent({
          event_name: 'Earlier',
          event_date: '2026-03-12T13:30:00.000Z',
        }),
      ],
    })

    const day = grid.days.find((candidate) => candidate.key === '2026-03-12')
    expect(day?.events.map((event) => event.event_name)).toEqual([
      'Earlier',
      'Later',
    ])
  })

  it('reports events it cannot place instead of dropping them', () => {
    const grid = gridFor('2026-03-01', {
      events: [makeEconomicEvent({ event_date: 'not-a-date' })],
    })

    expect(grid.undated).toHaveLength(1)
    expect(grid.days.every((day) => day.events.length === 0)).toBe(true)
  })
})

describe('shiftAnchor', () => {
  it('steps whole months across a year boundary', () => {
    const next = shiftAnchor(civilDateFromKey('2026-12-01'), 'month', 1)
    expect(next.toISOString().slice(0, 10)).toBe('2027-01-01')
  })

  it('steps whole weeks from the start of the week', () => {
    const next = shiftAnchor(civilDateFromKey('2026-03-18'), 'week', -1)
    expect(next.toISOString().slice(0, 10)).toBe('2026-03-08')
  })
})

describe('anchorForInstant', () => {
  it('anchors to the month or week containing the instant', () => {
    const instant = new Date('2026-03-18T12:00:00.000Z')

    expect(
      anchorForInstant(instant, 'month', 'UTC').toISOString().slice(0, 10),
    ).toBe('2026-03-01')
    expect(
      anchorForInstant(instant, 'week', 'UTC').toISOString().slice(0, 10),
    ).toBe('2026-03-15')
  })

  it('follows the display timezone across a date boundary', () => {
    // 01:00 UTC on 1 March is still 28 February in New York.
    const instant = new Date('2026-03-01T01:00:00.000Z')

    expect(
      anchorForInstant(instant, 'month', NEW_YORK).toISOString().slice(0, 10),
    ).toBe('2026-02-01')
  })
})

describe('formatting', () => {
  it('renders event times in the display timezone, 24-hour', () => {
    expect(formatEventTime('2026-03-12T13:30:00.000Z', 'UTC')).toBe('13:30')
    expect(formatEventTime('2026-03-12T13:30:00.000Z', NEW_YORK)).toBe('09:30')
  })

  it('names the zone in the full date, so a time is never ambiguous', () => {
    const formatted = formatEventDateTime('2026-03-12T13:30:00.000Z', 'UTC')

    expect(formatted).toContain('12 Mar 2026')
    expect(formatted).toContain('13:30')
    expect(formatted).toContain('UTC')
  })

  it('degrades to a placeholder for an unreadable date', () => {
    expect(formatEventTime('not-a-date', 'UTC')).toBe('--:--')
    expect(formatEventDateTime('not-a-date', 'UTC')).toBe('Date unavailable')
  })

  it('labels a month and a week range', () => {
    expect(calendarRangeLabel(civilDateFromKey('2026-03-01'), 'month')).toBe(
      'March 2026',
    )
    expect(calendarRangeLabel(civilDateFromKey('2026-03-18'), 'week')).toBe(
      '15 Mar – 21 Mar 2026',
    )
  })

  it('spells out both years for a week that straddles one', () => {
    expect(calendarRangeLabel(civilDateFromKey('2026-12-31'), 'week')).toBe(
      '27 Dec 2026 – 2 Jan 2027',
    )
  })

  it('starts the weekday headings on Sunday', () => {
    expect(weekdayLabels()).toEqual([
      'Sun',
      'Mon',
      'Tue',
      'Wed',
      'Thu',
      'Fri',
      'Sat',
    ])
  })
})

describe('timezone helpers', () => {
  it('pins UTC for the UTC mode and resolves a real zone for local', () => {
    expect(displayTimezone('utc')).toBe('UTC')
    expect(displayTimezone('local')).toBeTruthy()
  })

  it('reads the calendar day an instant lands on', () => {
    const instant = new Date('2026-03-02T00:30:00.000Z')

    expect(dayKeyInTimezone(instant, 'UTC')).toBe('2026-03-02')
    expect(dayKeyInTimezone(instant, NEW_YORK)).toBe('2026-03-01')
  })

  it('rejects a date it cannot parse', () => {
    expect(parseInstant('not-a-date')).toBeNull()
    expect(parseInstant('2026-03-02T00:30:00.000Z')).toBeInstanceOf(Date)
  })

  it('walks back to Sunday from any day of the week', () => {
    expect(
      startOfWeek(civilDateFromKey('2026-03-21')).toISOString().slice(0, 10),
    ).toBe('2026-03-15')
    expect(
      startOfWeek(civilDateFromKey('2026-03-15')).toISOString().slice(0, 10),
    ).toBe('2026-03-15')
  })
})
