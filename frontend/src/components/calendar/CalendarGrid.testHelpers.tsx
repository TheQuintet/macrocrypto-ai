import { render, screen } from '@testing-library/react'
import type { UserEvent } from '@testing-library/user-event'
import { expect } from 'vitest'
import { CalendarGrid } from '@/components/calendar/CalendarGrid'
import {
  buildCalendarGrid,
  civilDateFromKey,
} from '@/lib/economicCalendarGrid'
import type { EconomicEvent } from '@/types/economicCalendar'

/** March 2026 with "today" pinned, so cells and headings never drift. */
const ANCHOR_KEY = '2026-03-01'
const NOW = new Date('2026-03-18T12:00:00.000Z')

type RenderCalendarGridOptions = {
  events?: EconomicEvent[]
  isSubscribed?: (event: EconomicEvent) => boolean | null
  onSelectEvent?: (event: EconomicEvent) => void
}

export function renderCalendarGrid({
  events = [],
  isSubscribed = () => false,
  onSelectEvent = () => {},
}: RenderCalendarGridOptions = {}) {
  const grid = buildCalendarGrid({
    anchor: civilDateFromKey(ANCHOR_KEY),
    view: 'month',
    events,
    timeZone: 'UTC',
    now: NOW,
  })

  return render(
    <CalendarGrid
      grid={grid}
      timeZone="UTC"
      isSubscribed={isSubscribed}
      onSelectEvent={onSelectEvent}
    />,
  )
}

export function getEventChip(eventName: string) {
  return screen.getByRole('button', { name: new RegExp(`^${eventName},`) })
}

export async function clickEventChip(user: UserEvent, eventName: string) {
  await user.click(getEventChip(eventName))
}

export function expectChipAnnounces(eventName: string, fragment: string) {
  expect(getEventChip(eventName).getAttribute('aria-label')).toContain(
    fragment,
  )
}

export function expectDayCellRendered(label: string) {
  expect(screen.getByRole('gridcell', { name: label })).toBeInTheDocument()
}

export function expectWeekdayHeadings() {
  expect(screen.getAllByRole('columnheader')).toHaveLength(7)
}

export function expectDayCellCount(count: number) {
  expect(screen.getAllByRole('gridcell')).toHaveLength(count)
}
