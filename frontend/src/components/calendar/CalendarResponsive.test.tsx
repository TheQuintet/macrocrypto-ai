import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'
import { makeEconomicEvent } from '@/api/economicCalendar/economicCalendar.testHelpers'
import { CalendarAgenda } from '@/components/calendar/CalendarAgenda'
import { CalendarGrid } from '@/components/calendar/CalendarGrid'
import {
  buildCalendarGrid,
  civilDateFromKey,
} from '@/lib/economicCalendarGrid'

const EVENTS = [
  makeEconomicEvent({
    event_name: 'CPI release',
    event_date: '2026-03-12T13:30:00.000Z',
  }),
  makeEconomicEvent({
    event_name: 'FOMC rate decision',
    event_date: '2026-03-18T19:00:00.000Z',
  }),
]

function marchGrid() {
  return buildCalendarGrid({
    anchor: civilDateFromKey('2026-03-01'),
    view: 'month',
    events: EVENTS,
    timeZone: 'UTC',
    now: new Date('2026-03-18T12:00:00.000Z'),
  })
}

function renderGrid() {
  return render(
    <CalendarGrid
      grid={marchGrid()}
      timeZone="UTC"
      isSubscribed={() => false}
      onSelectEvent={() => {}}
    />,
  )
}

function renderAgenda() {
  return render(
    <CalendarAgenda
      grid={marchGrid()}
      timeZone="UTC"
      isSubscribed={() => false}
      onSelectEvent={() => {}}
    />,
  )
}

function eventNames() {
  return screen
    .getAllByRole('button')
    .map((button) => button.getAttribute('aria-label')?.split(',')[0])
}

/**
 * jsdom has no layout engine, so a media query cannot be evaluated here. What
 * can be asserted is the contract the two views are built on: the breakpoint
 * classes are complementary, and the narrow view shows the same releases as
 * the wide one — a phone must not silently lose events.
 */
describe('calendar responsive behaviour', () => {
  afterEach(() => {
    cleanup()
  })

  it('hides the seven-column grid below md', () => {
    renderGrid()
    const grid = screen.getByRole('grid')

    expect(grid).toHaveClass('hidden')
    expect(grid).toHaveClass('md:block')
  })

  it('hides the agenda from md upwards, so exactly one view shows', () => {
    renderAgenda()

    expect(
      screen.getByLabelText('Economic calendar agenda, March 2026'),
    ).toHaveClass('md:hidden')
  })

  it('shows the same events in the agenda as in the grid', () => {
    renderGrid()
    const wide = eventNames()

    cleanup()

    renderAgenda()
    const narrow = eventNames()

    expect(narrow.sort()).toEqual(wide.sort())
    expect(narrow).toContain('CPI release')
  })
})
